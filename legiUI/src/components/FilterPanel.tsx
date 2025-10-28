import React from 'react';
import type { FilterState, Bill } from '../types/bill';
import { X, Download } from 'lucide-react';

interface FilterPanelProps {
  filters: FilterState;
  availableFilters: {
    states: string[];
    categories: string[];
    years: string[];
    statuses: string[];
    legislationTypes: string[];
  };
  onFilterChange: (filters: FilterState) => void;
  filteredBills: Bill[];
  onExportCSV: () => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  availableFilters,
  onFilterChange,
  filteredBills,
  onExportCSV,
}) => {
  const handleMultiSelect = (key: keyof FilterState, value: string) => {
    const currentValues = filters[key] as string[];
    const newValues = currentValues.includes(value)
      ? currentValues.filter(v => v !== value)
      : [...currentValues, value];

    onFilterChange({ ...filters, [key]: newValues });
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, searchQuery: e.target.value });
  };

  const clearFilters = () => {
    onFilterChange({
      states: [],
      categories: [],
      years: [],
      statuses: [],
      legislationTypes: [],
      searchQuery: '',
    });
  };

  const hasActiveFilters =
    filters.states.length > 0 ||
    filters.categories.length > 0 ||
    filters.years.length > 0 ||
    filters.statuses.length > 0 ||
    filters.legislationTypes.length > 0 ||
    filters.searchQuery !== '';

  return (
    <div className="filter-panel" role="search" aria-label="Filter legislative bills">
      <div className="filter-header">
        <h2 id="filter-heading">Filters</h2>
        <div className="filter-actions">
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="clear-filters-btn"
              aria-label="Clear all filters"
            >
              <X size={16} aria-hidden="true" />
              Clear All
            </button>
          )}
        </div>
      </div>

      <div className="export-section">
        <button
          onClick={onExportCSV}
          className="export-csv-btn"
          aria-label={`Export ${filteredBills.length} filtered bills to CSV`}
          disabled={filteredBills.length === 0}
        >
          <Download size={16} aria-hidden="true" />
          Export CSV ({filteredBills.length})
        </button>
      </div>

      <div className="filter-section">
        <label htmlFor="search-input">Search</label>
        <input
          id="search-input"
          type="text"
          placeholder="Search bills..."
          value={filters.searchQuery}
          onChange={handleSearchChange}
          className="search-input"
          aria-describedby="search-help"
        />
        <span id="search-help" className="visually-hidden">
          Search by bill number, title, summary, or tags
        </span>
      </div>

      <fieldset className="filter-section">
        <legend>States ({filters.states.length} selected)</legend>
        <div className="filter-options" role="group" aria-label="State filters">
          {availableFilters.states.length === 0 && (
            <div style={{ padding: '0.5rem', color: '#999', fontStyle: 'italic' }}>
              No states available (check console)
            </div>
          )}
          {availableFilters.states.map(state => (
            <label key={state || 'empty'} className="checkbox-label" title={`State: ${state || 'EMPTY'}`}>
              <input
                type="checkbox"
                checked={filters.states.includes(state)}
                onChange={() => handleMultiSelect('states', state)}
                aria-label={`Filter by state: ${state || 'empty'}`}
              />
              <span>{state || '(empty)'}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="filter-section">
        <legend>Categories ({filters.categories.length} selected)</legend>
        <div className="filter-options" role="group" aria-label="Category filters">
          {availableFilters.categories.map(category => (
            <label key={category} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.categories.includes(category)}
                onChange={() => handleMultiSelect('categories', category)}
                aria-label={`Filter by category: ${category}`}
              />
              <span>{category}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="filter-section">
        <legend>Years ({filters.years.length} selected)</legend>
        <div className="filter-options" role="group" aria-label="Year filters">
          {availableFilters.years.map(year => (
            <label key={year} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.years.includes(year)}
                onChange={() => handleMultiSelect('years', year)}
                aria-label={`Filter by year: ${year}`}
              />
              <span>{year}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="filter-section">
        <legend>Status ({filters.statuses.length} selected)</legend>
        <div className="filter-options" role="group" aria-label="Status filters">
          {availableFilters.statuses.map(status => (
            <label key={status} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.statuses.includes(status)}
                onChange={() => handleMultiSelect('statuses', status)}
                aria-label={`Filter by status: ${status}`}
              />
              <span>{status}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="filter-section">
        <legend>Legislation Type ({filters.legislationTypes.length} selected)</legend>
        <div className="filter-options" role="group" aria-label="Legislation type filters">
          {availableFilters.legislationTypes.map(type => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.legislationTypes.includes(type)}
                onChange={() => handleMultiSelect('legislationTypes', type)}
                aria-label={`Filter by legislation type: ${type}`}
              />
              <span>{type}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  );
};
