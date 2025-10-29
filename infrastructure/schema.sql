-- LegiScan Bill Analysis Pipeline - PostgreSQL Database Schema
-- This schema supports the storage abstraction layer for Azure deployment
-- Version: 1.0
-- Last Updated: 2025-01-29

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Table: bills
-- Stores raw bill data from LegiScan API (replaces data/raw/*.json)
-- ============================================================================

CREATE TABLE IF NOT EXISTS bills (
    bill_id BIGINT PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL,
    state VARCHAR(2) NOT NULL,
    session VARCHAR(100),
    title TEXT,
    description TEXT,
    status INT,
    status_desc VARCHAR(100),
    year INT,
    change_hash VARCHAR(64),
    last_action TEXT,
    last_action_date DATE,
    url TEXT,
    state_url TEXT,
    raw_data JSONB NOT NULL,  -- Full LegiScan API response
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for bills table
CREATE INDEX IF NOT EXISTS idx_bills_bill_number ON bills(bill_number);
CREATE INDEX IF NOT EXISTS idx_bills_state_year ON bills(state, year);
CREATE INDEX IF NOT EXISTS idx_bills_session ON bills(session);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX IF NOT EXISTS idx_bills_last_action_date ON bills(last_action_date);

-- GIN index for JSON searching in raw_data
CREATE INDEX IF NOT EXISTS idx_bills_raw_data ON bills USING GIN(raw_data);

-- Comment on bills table
COMMENT ON TABLE bills IS 'Raw bill data from LegiScan API - replaces data/raw/*.json files';
COMMENT ON COLUMN bills.bill_id IS 'LegiScan internal bill ID (primary key)';
COMMENT ON COLUMN bills.bill_number IS 'Human-readable bill number (e.g., SB01071)';
COMMENT ON COLUMN bills.raw_data IS 'Full LegiScan API response in JSON format';

-- ============================================================================
-- Table: filter_results
-- Stores filter pass results (replaces data/filtered/*.json)
-- ============================================================================

CREATE TABLE IF NOT EXISTS filter_results (
    id SERIAL PRIMARY KEY,
    bill_id BIGINT NOT NULL REFERENCES bills(bill_id) ON DELETE CASCADE,
    run_id VARCHAR(100) NOT NULL,
    is_relevant BOOLEAN NOT NULL,
    reason TEXT,
    filtered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, run_id)
);

-- Indexes for filter_results table
CREATE INDEX IF NOT EXISTS idx_filter_results_run_id ON filter_results(run_id);
CREATE INDEX IF NOT EXISTS idx_filter_results_relevant ON filter_results(bill_id, is_relevant);
CREATE INDEX IF NOT EXISTS idx_filter_results_filtered_at ON filter_results(filtered_at);

-- Comment on filter_results table
COMMENT ON TABLE filter_results IS 'Filter pass results - replaces data/filtered/*.json files';
COMMENT ON COLUMN filter_results.run_id IS 'Unique identifier for filter run (e.g., ct_bills_2025)';
COMMENT ON COLUMN filter_results.is_relevant IS 'Whether bill passed initial relevance filter';

-- ============================================================================
-- Table: analysis_results
-- Stores analysis pass results (replaces data/analyzed/*.json)
-- ============================================================================

CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    bill_id BIGINT NOT NULL REFERENCES bills(bill_id) ON DELETE CASCADE,
    run_id VARCHAR(100) NOT NULL,
    is_relevant BOOLEAN NOT NULL,
    relevance_reasoning TEXT,
    summary TEXT,
    bill_status VARCHAR(50),
    legislation_type VARCHAR(50),
    categories JSONB,  -- Array of policy categories
    tags JSONB,  -- Array of tags
    key_provisions JSONB,  -- Array of key provisions
    palliative_care_impact TEXT,
    exclusion_check JSONB,  -- Exclusion criteria check results
    special_flags JSONB,  -- Special flags (regulations, executive orders, etc.)
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, run_id)
);

-- Indexes for analysis_results table
CREATE INDEX IF NOT EXISTS idx_analysis_results_run_id ON analysis_results(run_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_relevant ON analysis_results(is_relevant);
CREATE INDEX IF NOT EXISTS idx_analysis_results_bill_status ON analysis_results(bill_status);
CREATE INDEX IF NOT EXISTS idx_analysis_results_analyzed_at ON analysis_results(analyzed_at);

-- GIN indexes for JSON array searching
CREATE INDEX IF NOT EXISTS idx_analysis_results_categories ON analysis_results USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_analysis_results_tags ON analysis_results USING GIN(tags);

-- Comment on analysis_results table
COMMENT ON TABLE analysis_results IS 'Analysis pass results - replaces data/analyzed/*.json files';
COMMENT ON COLUMN analysis_results.run_id IS 'Unique identifier for analysis run';
COMMENT ON COLUMN analysis_results.categories IS 'Array of palliative care policy categories';
COMMENT ON COLUMN analysis_results.special_flags IS 'References to regulations, executive orders, ballot measures';

-- ============================================================================
-- Table: legiscan_cache
-- Stores cached LegiScan API responses (replaces data/cache/legiscan_cache/*.json)
-- ============================================================================

CREATE TABLE IF NOT EXISTS legiscan_cache (
    bill_id BIGINT PRIMARY KEY,
    response_data JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- Optional TTL for cache invalidation
);

-- Index for cache expiration cleanup
CREATE INDEX IF NOT EXISTS idx_legiscan_cache_expires ON legiscan_cache(expires_at);

-- Comment on legiscan_cache table
COMMENT ON TABLE legiscan_cache IS 'LegiScan API response cache - replaces data/cache/legiscan_cache/*.json files';
COMMENT ON COLUMN legiscan_cache.response_data IS 'Full LegiScan getBill API response';
COMMENT ON COLUMN legiscan_cache.expires_at IS 'Optional cache expiration timestamp';

-- ============================================================================
-- Table: pipeline_runs
-- Tracks pipeline execution history and status
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    stage VARCHAR(50) NOT NULL,  -- 'fetch', 'filter', 'analysis'
    state VARCHAR(2),
    year INT,
    status VARCHAR(20) NOT NULL,  -- 'running', 'completed', 'failed'
    bills_processed INT,
    bills_relevant INT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    CHECK (status IN ('running', 'completed', 'failed')),
    CHECK (stage IN ('fetch', 'filter', 'analysis'))
);

-- Indexes for pipeline_runs table
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_state_year ON pipeline_runs(state, year);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_stage ON pipeline_runs(stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON pipeline_runs(started_at);

-- Comment on pipeline_runs table
COMMENT ON TABLE pipeline_runs IS 'Pipeline execution history and monitoring';
COMMENT ON COLUMN pipeline_runs.run_id IS 'Unique identifier for pipeline run (e.g., ct_2025_20250129_143022)';
COMMENT ON COLUMN pipeline_runs.metadata IS 'Additional run metadata (configuration, environment, etc.)';

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- View: Relevant bills with analysis details
CREATE OR REPLACE VIEW v_relevant_bills AS
SELECT
    b.bill_id,
    b.bill_number,
    b.state,
    b.year,
    b.title,
    b.url,
    a.run_id,
    a.summary,
    a.bill_status,
    a.categories,
    a.tags,
    a.key_provisions,
    a.palliative_care_impact,
    a.analyzed_at
FROM bills b
JOIN analysis_results a ON b.bill_id = a.bill_id
WHERE a.is_relevant = TRUE
ORDER BY b.state, b.year, b.bill_number;

COMMENT ON VIEW v_relevant_bills IS 'All bills deemed relevant with their analysis details';

-- View: Pipeline run summary statistics
CREATE OR REPLACE VIEW v_pipeline_stats AS
SELECT
    run_id,
    stage,
    state,
    year,
    status,
    bills_processed,
    bills_relevant,
    CASE
        WHEN bills_processed > 0
        THEN ROUND((bills_relevant::numeric / bills_processed::numeric) * 100, 2)
        ELSE 0
    END as relevance_percentage,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
FROM pipeline_runs
WHERE completed_at IS NOT NULL
ORDER BY started_at DESC;

COMMENT ON VIEW v_pipeline_stats IS 'Pipeline execution statistics with duration and relevance rates';

-- View: Category distribution across relevant bills
CREATE OR REPLACE VIEW v_category_distribution AS
SELECT
    jsonb_array_elements_text(categories) as category,
    COUNT(*) as bill_count,
    ROUND((COUNT(*)::numeric / (SELECT COUNT(*) FROM analysis_results WHERE is_relevant = TRUE)::numeric) * 100, 2) as percentage
FROM analysis_results
WHERE is_relevant = TRUE AND categories IS NOT NULL
GROUP BY category
ORDER BY bill_count DESC;

COMMENT ON VIEW v_category_distribution IS 'Distribution of palliative care policy categories across relevant bills';

-- ============================================================================
-- Functions
-- ============================================================================

-- Function: Get bills by category
CREATE OR REPLACE FUNCTION get_bills_by_category(category_name TEXT)
RETURNS TABLE (
    bill_number VARCHAR(50),
    state VARCHAR(2),
    year INT,
    title TEXT,
    url TEXT,
    summary TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.bill_number,
        b.state,
        b.year,
        b.title,
        b.url,
        a.summary
    FROM bills b
    JOIN analysis_results a ON b.bill_id = a.bill_id
    WHERE a.is_relevant = TRUE
      AND a.categories @> to_jsonb(ARRAY[category_name])
    ORDER BY b.state, b.year, b.bill_number;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_bills_by_category IS 'Retrieve all bills tagged with a specific palliative care category';

-- Function: Clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM legiscan_cache
    WHERE expires_at IS NOT NULL AND expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clean_expired_cache IS 'Remove expired cache entries and return count of deleted rows';

-- Function: Update bill updated_at timestamp
CREATE OR REPLACE FUNCTION update_bill_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update bill timestamp on modification
CREATE TRIGGER trigger_bills_updated_at
    BEFORE UPDATE ON bills
    FOR EACH ROW
    EXECUTE FUNCTION update_bill_timestamp();

-- ============================================================================
-- Sample Queries (Commented out, for reference)
-- ============================================================================

/*
-- Get all relevant bills for Connecticut 2025
SELECT b.bill_number, b.title, a.categories
FROM bills b
JOIN analysis_results a ON b.bill_id = a.bill_id
WHERE b.state = 'CT'
  AND b.year = 2025
  AND a.is_relevant = true
ORDER BY b.bill_number;

-- Get bills by specific category
SELECT * FROM get_bills_by_category('Clinical Skill-Building');

-- Pipeline execution history
SELECT * FROM v_pipeline_stats
ORDER BY started_at DESC
LIMIT 10;

-- Category distribution
SELECT * FROM v_category_distribution;

-- Search bills by keyword in title
SELECT bill_number, title, state, year
FROM bills
WHERE title ILIKE '%palliative%' OR title ILIKE '%hospice%'
ORDER BY year DESC, state;

-- Get recent analysis activity
SELECT
    b.bill_number,
    b.title,
    a.is_relevant,
    a.summary,
    a.analyzed_at
FROM analysis_results a
JOIN bills b ON a.bill_id = b.bill_id
ORDER BY a.analyzed_at DESC
LIMIT 20;

-- Clean expired cache entries
SELECT clean_expired_cache();

-- Get bills with multiple categories
SELECT
    b.bill_number,
    b.title,
    jsonb_array_length(a.categories) as category_count,
    a.categories
FROM bills b
JOIN analysis_results a ON b.bill_id = a.bill_id
WHERE a.is_relevant = TRUE
  AND jsonb_array_length(a.categories) > 1
ORDER BY category_count DESC;
*/

-- ============================================================================
-- Permissions (adjust as needed for your environment)
-- ============================================================================

-- Grant permissions to application user (replace 'app_user' with your actual username)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_user;

-- ============================================================================
-- Maintenance
-- ============================================================================

-- Vacuum and analyze for optimal performance (run periodically)
-- VACUUM ANALYZE bills;
-- VACUUM ANALYZE filter_results;
-- VACUUM ANALYZE analysis_results;
-- VACUUM ANALYZE legiscan_cache;
-- VACUUM ANALYZE pipeline_runs;

-- ============================================================================
-- Schema Version Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('1.0', 'Initial schema for LegiScan Bill Analysis Pipeline')
ON CONFLICT (version) DO NOTHING;

COMMENT ON TABLE schema_version IS 'Tracks database schema versions and migration history';
