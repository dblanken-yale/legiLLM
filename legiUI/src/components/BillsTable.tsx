import React, { useState } from 'react';
import type { Bill } from '../types/bill';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

interface BillsTableProps {
  bills: Bill[];
  onBillSelect?: (bill: Bill) => void;
}

type SortKey = 'bill_number' | 'title' | 'state' | 'year' | 'bill_status';
type SortOrder = 'asc' | 'desc';

export const BillsTable: React.FC<BillsTableProps> = ({ bills, onBillSelect }) => {
  const [sortKey, setSortKey] = useState<SortKey>('year');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const sortedBills = [...bills].sort((a, b) => {
    const aValue = a[sortKey] || '';
    const bValue = b[sortKey] || '';

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const SortIcon: React.FC<{ columnKey: SortKey }> = ({ columnKey }) => {
    if (sortKey !== columnKey) return null;
    return sortOrder === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  return (
    <div className="bills-table-container">
      <table className="bills-table" role="table" aria-label="Legislative bills">
        <thead>
          <tr>
            <th
              onClick={() => handleSort('bill_number')}
              aria-sort={sortKey === 'bill_number' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
              scope="col"
            >
              <div className="th-content">
                Bill Number
                <SortIcon columnKey="bill_number" />
              </div>
            </th>
            <th
              onClick={() => handleSort('title')}
              aria-sort={sortKey === 'title' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
              scope="col"
            >
              <div className="th-content">
                Title
                <SortIcon columnKey="title" />
              </div>
            </th>
            <th
              onClick={() => handleSort('state')}
              aria-sort={sortKey === 'state' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
              scope="col"
            >
              <div className="th-content">
                State
                <SortIcon columnKey="state" />
              </div>
            </th>
            <th
              onClick={() => handleSort('year')}
              aria-sort={sortKey === 'year' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
              scope="col"
            >
              <div className="th-content">
                Year
                <SortIcon columnKey="year" />
              </div>
            </th>
            <th scope="col">Categories</th>
            <th
              onClick={() => handleSort('bill_status')}
              aria-sort={sortKey === 'bill_status' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
              scope="col"
            >
              <div className="th-content">
                Status
                <SortIcon columnKey="bill_status" />
              </div>
            </th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedBills.map((bill, index) => (
            <tr
              key={bill.bill_id || bill.bill_number || `bill-${index}`}
              onClick={() => onBillSelect?.(bill)}
              className="bill-row"
            >
              <td className="bill-number">{bill.bill_number}</td>
              <td className="bill-title">{bill.title}</td>
              <td>{bill.state}</td>
              <td>{bill.year}</td>
              <td>
                <div className="categories">
                  {bill.categories?.slice(0, 2).map(cat => (
                    <span key={cat} className="category-badge">
                      {cat}
                    </span>
                  ))}
                  {bill.categories && bill.categories.length > 2 && (
                    <span className="category-badge more">
                      +{bill.categories.length - 2}
                    </span>
                  )}
                </div>
              </td>
              <td>
                <span className={`status-badge status-${bill.bill_status?.toLowerCase()}`}>
                  {bill.bill_status}
                </span>
              </td>
              <td>
                <a
                  href={bill.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="external-link"
                  onClick={e => e.stopPropagation()}
                  aria-label={`View ${bill.bill_number} on LegiScan (opens in new window)`}
                >
                  <ExternalLink size={16} aria-hidden="true" />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {sortedBills.length === 0 && (
        <div className="empty-state">No bills match the current filters</div>
      )}
    </div>
  );
};
