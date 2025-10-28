import { useState, useEffect, useMemo } from 'react';
import type { Bill, FilterState } from './types/bill';
import { DataLoader } from './utils/dataLoader';
import { FilterPanel } from './components/FilterPanel';
import { StatsCard } from './components/StatsCard';
import { Chart } from './components/Charts';
import { BillsTable } from './components/BillsTable';
import { BillDetailModal } from './components/BillDetailModal';
import { exportBillsToCSV } from './utils/csvExport';
import { FileText, Calendar, MapPin, CheckCircle } from 'lucide-react';
import './App.css';

function App() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    states: [],
    categories: [],
    years: [],
    statuses: [],
    legislationTypes: [],
    searchQuery: '',
  });

  useEffect(() => {
    const loadData = async () => {
      const loader = new DataLoader();
      const data = await loader.loadData();
      setBills(data);
      setLoading(false);
    };

    loadData();
  }, []);

  // Get available filter options
  const availableFilters = useMemo(() => {
    const states = new Set<string>();
    const categories = new Set<string>();
    const years = new Set<string>();
    const statuses = new Set<string>();
    const legislationTypes = new Set<string>();

    bills.forEach(bill => {
      if (bill.state) states.add(bill.state);
      if (bill.year) years.add(String(bill.year));
      if (bill.bill_status) statuses.add(bill.bill_status);
      if (bill.legislation_type) legislationTypes.add(bill.legislation_type);
      bill.categories?.forEach(cat => categories.add(cat));
    });

    return {
      states: Array.from(states).sort(),
      categories: Array.from(categories).sort(),
      years: Array.from(years).sort().reverse(),
      statuses: Array.from(statuses).sort(),
      legislationTypes: Array.from(legislationTypes).sort(),
    };
  }, [bills]);

  // Filter bills based on current filters
  const filteredBills = useMemo(() => {
    const filtered = bills.filter(bill => {
      // State filter
      if (filters.states.length > 0 && !filters.states.includes(bill.state || '')) {
        return false;
      }

      // Category filter
      if (filters.categories.length > 0) {
        const hasCategory = bill.categories?.some(cat => filters.categories.includes(cat));
        if (!hasCategory) return false;
      }

      // Year filter
      if (filters.years.length > 0 && !filters.years.includes(String(bill.year))) {
        return false;
      }

      // Status filter
      if (filters.statuses.length > 0 && !filters.statuses.includes(bill.bill_status || '')) {
        return false;
      }

      // Legislation type filter
      if (
        filters.legislationTypes.length > 0 &&
        !filters.legislationTypes.includes(bill.legislation_type || '')
      ) {
        return false;
      }

      // Search query filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const searchableText = [
          bill.bill_number,
          bill.title,
          bill.summary,
          ...(bill.tags || []),
          ...(bill.categories || []),
        ]
          .join(' ')
          .toLowerCase();

        if (!searchableText.includes(query)) return false;
      }

      return true;
    });

    return filtered;
  }, [bills, filters]);

  // Calculate stats for filtered bills
  const stats = useMemo(() => {
    const byState: Record<string, number> = {};
    const byCategory: Record<string, number> = {};
    const byYear: Record<string, number> = {};
    const byStatus: Record<string, number> = {};

    filteredBills.forEach(bill => {
      if (bill.state) byState[bill.state] = (byState[bill.state] || 0) + 1;
      if (bill.year) byYear[String(bill.year)] = (byYear[String(bill.year)] || 0) + 1;
      if (bill.bill_status) byStatus[bill.bill_status] = (byStatus[bill.bill_status] || 0) + 1;
      bill.categories?.forEach(cat => {
        byCategory[cat] = (byCategory[cat] || 0) + 1;
      });
    });

    return { byState, byCategory, byYear, byStatus };
  }, [filteredBills]);

  // Handle CSV export
  const handleExportCSV = () => {
    exportBillsToCSV(filteredBills, filters);
  };

  if (loading) {
    return <div className="loading">Loading legislative data...</div>;
  }

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header className="app-header" role="banner">
        <h1>LegiUI - Legislative Analysis Dashboard</h1>
        <p>Palliative Care Policy Tracking Across States</p>
      </header>

      <div className="app-layout">
        <aside className="sidebar" role="complementary" aria-label="Filter Panel">
          <FilterPanel
            filters={filters}
            availableFilters={availableFilters}
            onFilterChange={setFilters}
            filteredBills={filteredBills}
            onExportCSV={handleExportCSV}
          />
        </aside>

        <main id="main-content" className="main-content" role="main">
          <div className="stats-grid">
            <StatsCard
              title="Total Bills"
              value={filteredBills.length}
              icon={<FileText />}
              subtitle={`of ${bills.length} total`}
            />
            <StatsCard
              title="States"
              value={Object.keys(stats.byState).length}
              icon={<MapPin />}
            />
            <StatsCard
              title="Years"
              value={Object.keys(stats.byYear).length}
              icon={<Calendar />}
            />
            <StatsCard
              title="Categories"
              value={Object.keys(stats.byCategory).length}
              icon={<CheckCircle />}
            />
          </div>

          <div className="charts-grid">
            <Chart data={stats.byCategory} title="Bills by Category" type="bar" />
            <Chart data={stats.byState} title="Bills by State" type="pie" />
            <Chart data={stats.byYear} title="Bills by Year" type="bar" />
            <Chart data={stats.byStatus} title="Bills by Status" type="pie" />
          </div>

          <div className="table-section">
            <h2>Bills ({filteredBills.length})</h2>
            <BillsTable bills={filteredBills} onBillSelect={setSelectedBill} />
          </div>
        </main>
      </div>

      <BillDetailModal bill={selectedBill} onClose={() => setSelectedBill(null)} />
    </div>
  );
}

export default App;
