import type { Bill } from '../types/bill';

/**
 * Converts an array of bills to CSV format
 */
export function convertBillsToCSV(bills: Bill[]): string {
  if (bills.length === 0) {
    return '';
  }

  // Define CSV headers
  const headers = [
    'Bill Number',
    'Title',
    'State',
    'Year',
    'Session',
    'Status',
    'Legislation Type',
    'Categories',
    'Tags',
    'Summary',
    'Key Provisions',
    'Palliative Care Impact',
    'Special Flags',
    'Status Date',
    'Last Action',
    'URL',
  ];

  // Helper function to escape CSV fields
  const escapeCSVField = (field: any): string => {
    if (field === null || field === undefined) {
      return '';
    }

    const stringField = String(field);

    // If field contains comma, quote, or newline, wrap in quotes and escape quotes
    if (stringField.includes(',') || stringField.includes('"') || stringField.includes('\n')) {
      return `"${stringField.replace(/"/g, '""')}"`;
    }

    return stringField;
  };

  // Helper to safely join arrays or convert values to strings
  const joinArray = (arr: any): string => {
    if (!arr) return '';
    if (Array.isArray(arr)) return arr.join('; ');
    // Handle objects - extract keys where value is truthy
    if (typeof arr === 'object') {
      try {
        // If object has boolean flags, extract the true keys
        const keys = Object.keys(arr).filter(key => arr[key]);
        if (keys.length > 0) {
          return keys.join('; ');
        }
        // Otherwise return JSON string
        return JSON.stringify(arr);
      } catch (e) {
        return '';
      }
    }
    // Handle primitives (string, number, boolean)
    return String(arr);
  };

  // Convert bills to CSV rows
  const rows = bills.map(bill => {
    return [
      escapeCSVField(bill.bill_number),
      escapeCSVField(bill.title),
      escapeCSVField(bill.state),
      escapeCSVField(bill.year),
      escapeCSVField(bill.session),
      escapeCSVField(bill.bill_status),
      escapeCSVField(bill.legislation_type),
      escapeCSVField(joinArray(bill.categories)),
      escapeCSVField(joinArray(bill.tags)),
      escapeCSVField(bill.summary),
      escapeCSVField(joinArray(bill.key_provisions)),
      escapeCSVField(bill.palliative_care_impact),
      escapeCSVField(joinArray(bill.special_flags)),
      escapeCSVField(bill.status_date),
      escapeCSVField(bill.last_action),
      escapeCSVField(bill.url),
    ].join(',');
  });

  // Combine headers and rows
  return [headers.join(','), ...rows].join('\n');
}

/**
 * Downloads CSV data as a file
 */
export function downloadCSV(csvContent: string, filename: string): void {
  // Create blob with UTF-8 BOM for Excel compatibility
  const BOM = '\uFEFF';
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

  // Create download link
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up
  URL.revokeObjectURL(url);
}

/**
 * Exports filtered bills to CSV file
 */
export function exportBillsToCSV(bills: Bill[], filters: any): void {
  if (bills.length === 0) {
    alert('No bills to export. Please adjust your filters.');
    return;
  }

  const csvContent = convertBillsToCSV(bills);

  // Generate filename with timestamp
  const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const filterInfo = [];

  if (filters.states?.length > 0) {
    filterInfo.push(filters.states.join('-'));
  }
  if (filters.years?.length > 0) {
    filterInfo.push(filters.years.join('-'));
  }

  const filterSuffix = filterInfo.length > 0 ? `_${filterInfo.join('_')}` : '';
  const filename = `legislative_bills${filterSuffix}_${timestamp}.csv`;

  downloadCSV(csvContent, filename);
}
