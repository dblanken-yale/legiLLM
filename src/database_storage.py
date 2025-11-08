"""
Database Storage Provider

Implements PostgreSQL-based storage for team collaboration and queryable data.
Supports optional dual-write mode to maintain file compatibility during migration.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import SimpleConnectionPool

from src.storage_provider import StorageProvider


class DatabaseStorage(StorageProvider):
    """PostgreSQL database storage provider"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database storage provider

        Args:
            config: Configuration dictionary with:
                - connection_string_env: Environment variable name for connection string
                - enable_file_fallback: If True, also writes to files (dual-write mode)
                - pool_size: Connection pool size (default: 5)
                - pool_max_overflow: Max pool overflow (default: 10)
        """
        # Get connection string from environment
        connection_string_env = config.get('connection_string_env', 'DATABASE_CONNECTION_STRING')
        self.connection_string = os.getenv(connection_string_env)

        if not self.connection_string:
            raise ValueError(f"Database connection string not found in environment variable: {connection_string_env}")

        # Configuration options
        self.enable_file_fallback = config.get('enable_file_fallback', False)
        pool_size = config.get('pool_size', 5)
        pool_max_overflow = config.get('pool_max_overflow', 10)

        # Initialize connection pool
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=pool_size + pool_max_overflow,
                dsn=self.connection_string
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database connection pool: {e}")

        # If file fallback is enabled, initialize local file storage
        if self.enable_file_fallback:
            from src.local_file_storage import LocalFileStorage
            self.file_storage = LocalFileStorage()

    def _get_connection(self):
        """Get a connection from the pool"""
        return self.pool.getconn()

    def _return_connection(self, conn):
        """Return a connection to the pool"""
        self.pool.putconn(conn)

    def _execute_query(self, query: str, params: tuple = None, fetch: str = None):
        """
        Execute a query and optionally fetch results

        Args:
            query: SQL query string
            params: Query parameters
            fetch: 'one', 'all', or None

        Returns:
            Query results if fetch is specified, None otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)

                if fetch == 'one':
                    result = cursor.fetchone()
                elif fetch == 'all':
                    result = cursor.fetchall()
                else:
                    result = None

                conn.commit()
                return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._return_connection(conn)

    def save_raw_data(self, filename: str, data: Dict[str, Any]) -> None:
        """Save raw bill data to bills table"""
        if filename.endswith('.json'):
            filename = filename[:-5]

        # Extract bills from data structure
        if isinstance(data, dict) and 'summary' in data and 'masterlist' in data['summary']:
            bills = data['summary']['masterlist']
        elif isinstance(data, dict) and 'bills' in data:
            bills = data['bills']
        elif isinstance(data, list):
            bills = data
        else:
            bills = []

        # Insert bills into database
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                for bill in bills:
                    if not isinstance(bill, dict):
                        continue

                    # Prepare bill data
                    bill_id = bill.get('bill_id')
                    if not bill_id:
                        continue

                    # Insert or update bill
                    query = """
                        INSERT INTO bills (
                            bill_id, bill_number, state, session, title, description,
                            status, status_desc, year, change_hash, last_action,
                            last_action_date, url, state_url, raw_data, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bill_id) DO UPDATE SET
                            bill_number = EXCLUDED.bill_number,
                            state = EXCLUDED.state,
                            session = EXCLUDED.session,
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            status = EXCLUDED.status,
                            status_desc = EXCLUDED.status_desc,
                            year = EXCLUDED.year,
                            change_hash = EXCLUDED.change_hash,
                            last_action = EXCLUDED.last_action,
                            last_action_date = EXCLUDED.last_action_date,
                            url = EXCLUDED.url,
                            state_url = EXCLUDED.state_url,
                            raw_data = EXCLUDED.raw_data,
                            updated_at = EXCLUDED.updated_at
                    """

                    # Parse last_action_date
                    last_action_date = bill.get('last_action_date')
                    if last_action_date and isinstance(last_action_date, str):
                        try:
                            last_action_date = datetime.strptime(last_action_date, '%Y-%m-%d').date()
                        except ValueError:
                            last_action_date = None

                    cursor.execute(query, (
                        bill_id,
                        bill.get('bill_number'),
                        bill.get('state'),
                        bill.get('session'),
                        bill.get('title'),
                        bill.get('description'),
                        bill.get('status'),
                        bill.get('status_desc'),
                        bill.get('year'),
                        bill.get('change_hash'),
                        bill.get('last_action'),
                        last_action_date,
                        bill.get('url'),
                        bill.get('state_url'),
                        json.dumps(bill),
                        datetime.now()
                    ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._return_connection(conn)

        # File fallback
        if self.enable_file_fallback:
            self.file_storage.save_raw_data(filename, data)

    def load_raw_data(self, filename: str) -> Dict[str, Any]:
        """Load raw bill data from bills table"""
        if filename.endswith('.json'):
            filename = filename[:-5]

        # Extract state and year from filename (e.g., "ct_bills_2025")
        parts = filename.split('_')
        state = parts[0].upper() if parts else None
        year = int(parts[-1]) if parts and parts[-1].isdigit() else None

        query = """
            SELECT raw_data
            FROM bills
            WHERE 1=1
        """
        params = []

        if state:
            query += " AND state = %s"
            params.append(state)

        if year:
            query += " AND year = %s"
            params.append(year)

        query += " ORDER BY bill_number"

        results = self._execute_query(query, tuple(params) if params else None, fetch='all')

        if not results:
            raise FileNotFoundError(f"No bills found for: {filename}")

        # Reconstruct data structure
        bills = [json.loads(row['raw_data']) for row in results]

        return {
            'summary': {
                'masterlist': bills,
                'total': len(bills)
            }
        }

    def save_filtered_results(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save filter results to filter_results table"""
        # Extract relevant bills from data
        relevant_bills = data.get('relevant_bills', [])
        summary = data.get('summary', {})
        total_analyzed = summary.get('total_analyzed', 0)
        relevant_count = summary.get('relevant_count', 0)
        not_relevant_count = summary.get('not_relevant_count', 0)

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Insert filter results for each bill
                for bill_data in relevant_bills:
                    bill_number = bill_data.get('bill_number')
                    if not bill_number:
                        continue

                    # Get bill_id from bills table
                    cursor.execute(
                        "SELECT bill_id FROM bills WHERE bill_number = %s",
                        (bill_number,)
                    )
                    bill_row = cursor.fetchone()

                    if not bill_row:
                        continue

                    bill_id = bill_row[0]

                    # Insert filter result
                    query = """
                        INSERT INTO filter_results (bill_id, run_id, is_relevant, reason)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (bill_id, run_id) DO UPDATE SET
                            is_relevant = EXCLUDED.is_relevant,
                            reason = EXCLUDED.reason,
                            filtered_at = CURRENT_TIMESTAMP
                    """

                    cursor.execute(query, (
                        bill_id,
                        run_id,
                        True,
                        bill_data.get('reason', '')
                    ))

                # Record pipeline run
                cursor.execute("""
                    INSERT INTO pipeline_runs (
                        run_id, stage, status, bills_processed, bills_relevant, completed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        bills_processed = EXCLUDED.bills_processed,
                        bills_relevant = EXCLUDED.bills_relevant,
                        completed_at = EXCLUDED.completed_at,
                        status = EXCLUDED.status
                """, (
                    run_id,
                    'filter',
                    'completed',
                    total_analyzed,
                    relevant_count,
                    datetime.now()
                ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._return_connection(conn)

        # File fallback
        if self.enable_file_fallback:
            self.file_storage.save_filtered_results(run_id, data)

    def load_filtered_results(self, run_id: str) -> Dict[str, Any]:
        """Load filter results from filter_results table"""
        query = """
            SELECT
                b.bill_number,
                b.title,
                b.url,
                f.reason,
                f.filtered_at
            FROM filter_results f
            JOIN bills b ON f.bill_id = b.bill_id
            WHERE f.run_id = %s AND f.is_relevant = TRUE
            ORDER BY b.bill_number
        """

        results = self._execute_query(query, (run_id,), fetch='all')

        if not results:
            raise FileNotFoundError(f"Filter results not found for run_id: {run_id}")

        # Get summary from pipeline_runs
        summary_query = """
            SELECT bills_processed, bills_relevant
            FROM pipeline_runs
            WHERE run_id = %s AND stage = 'filter'
        """
        summary_row = self._execute_query(summary_query, (run_id,), fetch='one')

        relevant_bills = [
            {
                'bill_number': row['bill_number'],
                'title': row['title'],
                'url': row['url'],
                'reason': row['reason']
            }
            for row in results
        ]

        return {
            'summary': {
                'total_analyzed': summary_row['bills_processed'] if summary_row else 0,
                'relevant_count': summary_row['bills_relevant'] if summary_row else len(relevant_bills),
                'not_relevant_count': (summary_row['bills_processed'] if summary_row else 0) - len(relevant_bills),
                'source_file': run_id
            },
            'relevant_bills': relevant_bills
        }

    def save_analysis_results(
        self,
        run_id: str,
        relevant: Union[List[Dict[str, Any]], Dict[str, Any]],
        not_relevant: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Save analysis results to analysis_results table

        Accepts either:
        - List format (legacy): [{"bill": {...}, "analysis": {...}}, ...]
        - Dict format (with stats): {"summary": {...}, "timing_stats": {...}, "results": [...]}
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Extract results list from either format
                relevant_list = relevant if isinstance(relevant, list) else relevant.get('results', [])
                not_relevant_list = not_relevant if isinstance(not_relevant, list) else not_relevant.get('results', [])

                # Process both relevant and not relevant bills
                all_bills = [(bill, True) for bill in relevant_list] + [(bill, False) for bill in not_relevant_list]

                for bill_data, is_relevant in all_bills:
                    bill_number = bill_data.get('bill_number')
                    if not bill_number:
                        continue

                    # Get bill_id from bills table
                    cursor.execute(
                        "SELECT bill_id FROM bills WHERE bill_number = %s",
                        (bill_number,)
                    )
                    bill_row = cursor.fetchone()

                    if not bill_row:
                        continue

                    bill_id = bill_row[0]

                    # Insert analysis result
                    query = """
                        INSERT INTO analysis_results (
                            bill_id, run_id, is_relevant, relevance_reasoning, summary,
                            bill_status, legislation_type, categories, tags, key_provisions,
                            palliative_care_impact, exclusion_check, special_flags
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (bill_id, run_id) DO UPDATE SET
                            is_relevant = EXCLUDED.is_relevant,
                            relevance_reasoning = EXCLUDED.relevance_reasoning,
                            summary = EXCLUDED.summary,
                            bill_status = EXCLUDED.bill_status,
                            legislation_type = EXCLUDED.legislation_type,
                            categories = EXCLUDED.categories,
                            tags = EXCLUDED.tags,
                            key_provisions = EXCLUDED.key_provisions,
                            palliative_care_impact = EXCLUDED.palliative_care_impact,
                            exclusion_check = EXCLUDED.exclusion_check,
                            special_flags = EXCLUDED.special_flags,
                            analyzed_at = CURRENT_TIMESTAMP
                    """

                    cursor.execute(query, (
                        bill_id,
                        run_id,
                        is_relevant,
                        bill_data.get('relevance_reasoning', ''),
                        bill_data.get('summary', ''),
                        bill_data.get('bill_status', ''),
                        bill_data.get('legislation_type', ''),
                        json.dumps(bill_data.get('categories', [])),
                        json.dumps(bill_data.get('tags', [])),
                        json.dumps(bill_data.get('key_provisions', [])),
                        bill_data.get('palliative_care_impact', ''),
                        json.dumps(bill_data.get('exclusion_check', {})),
                        json.dumps(bill_data.get('special_flags', {}))
                    ))

                # Update pipeline run
                cursor.execute("""
                    INSERT INTO pipeline_runs (
                        run_id, stage, status, bills_processed, bills_relevant, completed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        bills_processed = EXCLUDED.bills_processed,
                        bills_relevant = EXCLUDED.bills_relevant,
                        completed_at = EXCLUDED.completed_at,
                        status = EXCLUDED.status
                """, (
                    run_id,
                    'analysis',
                    'completed',
                    len(relevant) + len(not_relevant),
                    len(relevant),
                    datetime.now()
                ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._return_connection(conn)

        # File fallback
        if self.enable_file_fallback:
            self.file_storage.save_analysis_results(run_id, relevant, not_relevant)

    def load_analysis_results(self, run_id: str) -> Tuple[List[Dict], List[Dict]]:
        """Load analysis results from analysis_results table"""
        query = """
            SELECT
                b.bill_number,
                b.title,
                b.url,
                a.is_relevant,
                a.relevance_reasoning,
                a.summary,
                a.bill_status,
                a.legislation_type,
                a.categories,
                a.tags,
                a.key_provisions,
                a.palliative_care_impact,
                a.exclusion_check,
                a.special_flags
            FROM analysis_results a
            JOIN bills b ON a.bill_id = b.bill_id
            WHERE a.run_id = %s
            ORDER BY b.bill_number
        """

        results = self._execute_query(query, (run_id,), fetch='all')

        if not results:
            raise FileNotFoundError(f"Analysis results not found for run_id: {run_id}")

        relevant = []
        not_relevant = []

        for row in results:
            bill_data = {
                'bill_number': row['bill_number'],
                'title': row['title'],
                'url': row['url'],
                'relevance_reasoning': row['relevance_reasoning'],
                'summary': row['summary'],
                'bill_status': row['bill_status'],
                'legislation_type': row['legislation_type'],
                'categories': json.loads(row['categories']) if row['categories'] else [],
                'tags': json.loads(row['tags']) if row['tags'] else [],
                'key_provisions': json.loads(row['key_provisions']) if row['key_provisions'] else [],
                'palliative_care_impact': row['palliative_care_impact'],
                'exclusion_check': json.loads(row['exclusion_check']) if row['exclusion_check'] else {},
                'special_flags': json.loads(row['special_flags']) if row['special_flags'] else {}
            }

            if row['is_relevant']:
                relevant.append(bill_data)
            else:
                not_relevant.append(bill_data)

        return relevant, not_relevant

    def get_bill_from_cache(self, bill_id: int) -> Optional[Dict[str, Any]]:
        """Get cached bill from legiscan_cache table"""
        query = "SELECT response_data FROM legiscan_cache WHERE bill_id = %s"
        result = self._execute_query(query, (bill_id,), fetch='one')

        if result:
            return json.loads(result['response_data'])

        return None

    def save_bill_to_cache(self, bill_id: int, data: Dict[str, Any]) -> None:
        """Save bill to legiscan_cache table"""
        query = """
            INSERT INTO legiscan_cache (bill_id, response_data)
            VALUES (%s, %s)
            ON CONFLICT (bill_id) DO UPDATE SET
                response_data = EXCLUDED.response_data,
                cached_at = CURRENT_TIMESTAMP
        """

        self._execute_query(query, (bill_id, json.dumps(data)))

        # File fallback
        if self.enable_file_fallback:
            self.file_storage.save_bill_to_cache(bill_id, data)

    def list_raw_files(self) -> List[str]:
        """List available states/years in bills table"""
        query = """
            SELECT DISTINCT LOWER(state) || '_bills_' || year::text as identifier
            FROM bills
            ORDER BY identifier
        """

        results = self._execute_query(query, fetch='all')
        return [row['identifier'] for row in results]

    def list_filtered_results(self) -> List[str]:
        """List available filter run IDs"""
        query = """
            SELECT DISTINCT run_id
            FROM filter_results
            ORDER BY run_id
        """

        results = self._execute_query(query, fetch='all')
        return [row['run_id'] for row in results]

    def bill_exists_in_raw(self, bill_number: str, filename: str) -> bool:
        """Check if a bill exists in bills table"""
        query = "SELECT 1 FROM bills WHERE bill_number = %s LIMIT 1"
        result = self._execute_query(query, (bill_number,), fetch='one')
        return result is not None

    def get_bill_by_number(self, bill_number: str, filename: str) -> Optional[Dict[str, Any]]:
        """Get a specific bill from bills table by bill number"""
        query = "SELECT raw_data FROM bills WHERE bill_number = %s"
        result = self._execute_query(query, (bill_number,), fetch='one')

        if result:
            return json.loads(result['raw_data'])

        return None

    def close(self):
        """Close all database connections"""
        if hasattr(self, 'pool'):
            self.pool.closeall()
