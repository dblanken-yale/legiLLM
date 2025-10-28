import React from 'react';
import type { Bill } from '../types/bill';
import { X, ExternalLink, Calendar, Flag, Tag } from 'lucide-react';

interface BillDetailModalProps {
  bill: Bill | null;
  onClose: () => void;
}

export const BillDetailModal: React.FC<BillDetailModalProps> = ({ bill, onClose }) => {
  // Close modal on Escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (bill) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [bill, onClose]);

  if (!bill) return null;

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 id="modal-title">{bill.bill_number}</h2>
          <button
            onClick={onClose}
            className="close-btn"
            aria-label="Close bill details"
          >
            <X size={24} aria-hidden="true" />
          </button>
        </div>

        <div className="modal-body">
          <div className="detail-section">
            <h3>{bill.title}</h3>
          </div>

          <div className="detail-grid">
            <div className="detail-item">
              <label>State</label>
              <span>{bill.state}</span>
            </div>
            <div className="detail-item">
              <label>Year</label>
              <span>{bill.year}</span>
            </div>
            <div className="detail-item">
              <label>Status</label>
              <span className={`status-badge status-${bill.bill_status?.toLowerCase()}`}>
                {bill.bill_status}
              </span>
            </div>
            <div className="detail-item">
              <label>Type</label>
              <span>{bill.legislation_type}</span>
            </div>
          </div>

          {bill.summary && (
            <div className="detail-section">
              <h4>Summary</h4>
              <p>{bill.summary}</p>
            </div>
          )}

          {bill.relevance_reasoning && (
            <div className="detail-section">
              <h4>Relevance Reasoning</h4>
              <p>{bill.relevance_reasoning}</p>
            </div>
          )}

          {bill.categories && bill.categories.length > 0 && (
            <div className="detail-section">
              <h4>
                <Tag size={18} /> Categories
              </h4>
              <div className="categories">
                {bill.categories.map(cat => (
                  <span key={cat} className="category-badge large">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          )}

          {bill.key_provisions && bill.key_provisions.length > 0 && (
            <div className="detail-section">
              <h4>Key Provisions</h4>
              <ul>
                {bill.key_provisions.map((provision, idx) => (
                  <li key={idx}>{provision}</li>
                ))}
              </ul>
            </div>
          )}

          {bill.palliative_care_impact && (
            <div className="detail-section">
              <h4>Palliative Care Impact</h4>
              <p>{bill.palliative_care_impact}</p>
            </div>
          )}

          {bill.tags && bill.tags.length > 0 && (
            <div className="detail-section">
              <h4>Tags</h4>
              <div className="tags">
                {bill.tags.map(tag => (
                  <span key={tag} className="tag-badge">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {bill.special_flags && bill.special_flags.length > 0 && (
            <div className="detail-section">
              <h4>
                <Flag size={18} /> Special Flags
              </h4>
              <div className="flags">
                {bill.special_flags.map(flag => (
                  <span key={flag} className="flag-badge">
                    {flag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {bill.last_action && (
            <div className="detail-section">
              <h4>
                <Calendar size={18} /> Last Action
              </h4>
              <p>
                {bill.status_date && <strong>{bill.status_date}:</strong>} {bill.last_action}
              </p>
            </div>
          )}

          <div className="detail-section">
            <a
              href={bill.url}
              target="_blank"
              rel="noopener noreferrer"
              className="view-full-btn"
              aria-label={`View full text of ${bill.bill_number} on LegiScan (opens in new window)`}
            >
              <ExternalLink size={18} aria-hidden="true" />
              View Full Bill on LegiScan
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
