import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const analysisDir = path.join(__dirname, '../../data/analyzed');
const outputFile = path.join(__dirname, '../public/bills.json');

console.log('Loading data from:', analysisDir);

// Find all relevant analysis files (exclude "not_relevant")
const files = fs.readdirSync(analysisDir)
  .filter(f => f.endsWith('_relevant.json') && !f.includes('not_relevant'));

console.log(`Found ${files.length} analysis files:`, files);

const allBills = [];
const stateMap = {
  'ct': 'CT',
  'in': 'IN',
  'ny': 'NY',
  'ca': 'CA',
  // Add more state mappings as needed
};

// Extract state from filename (e.g., "analysis_alan_ct_bills_2025_relevant.json" -> "CT")
function extractStateFromFilename(filename) {
  const match = filename.match(/_([a-z]{2})_bills_/i);
  if (match) {
    const stateCode = match[1].toLowerCase();
    return stateMap[stateCode] || stateCode.toUpperCase();
  }
  return null; // Return null instead of 'Unknown' so we can try URL extraction
}

// Extract state from LegiScan URL (e.g., "https://legiscan.com/CT/bill/..." -> "CT")
function extractStateFromUrl(url) {
  if (!url) return null;
  const match = url.match(/legiscan\.com\/([A-Z]{2})\//);
  return match ? match[1] : null;
}

// Process each file
for (const file of files) {
  const filePath = path.join(analysisDir, file);
  const content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  const filenameState = extractStateFromFilename(file);

  console.log(`Processing ${file}${filenameState ? ` (State from filename: ${filenameState})` : ''}`);

  // Handle different data formats
  let bills = [];

  if (Array.isArray(content)) {
    // Format: Array of bills (like analysis_alan_in_bills_2025_relevant.json)
    bills = content.map(item => {
      // Check if it has nested structure with "bill" and "analysis"
      if (item.bill && item.analysis) {
        const urlState = extractStateFromUrl(item.bill.url);
        const state = filenameState || urlState || 'Unknown';
        const merged = {
          ...item.bill,
          // Flatten extra_metadata FIRST so analysis fields can override
          ...(item.bill.extra_metadata || {}),
          ...item.analysis,
          state: state,
        };
        // Ensure bill_id exists (use bill_number as fallback)
        if (!merged.bill_id && merged.bill_number) {
          merged.bill_id = merged.bill_number;
        }
        return merged;
      }
      // Otherwise assume it's already flat
      const urlState = extractStateFromUrl(item.url);
      const state = item.state || filenameState || urlState || 'Unknown';
      const bill = {
        ...item,
        state: state,
      };
      // Ensure bill_id exists
      if (!bill.bill_id && bill.bill_number) {
        bill.bill_id = bill.bill_number;
      }
      return bill;
    });
  } else if (content.relevant_bills) {
    // Format: Object with relevant_bills array (AI-filtered format)
    bills = content.relevant_bills.map(bill => {
      const urlState = extractStateFromUrl(bill.url);
      const state = bill.state || filenameState || urlState || 'Unknown';
      const processed = {
        ...bill,
        state: state,
      };
      // Ensure bill_id exists
      if (!processed.bill_id && processed.bill_number) {
        processed.bill_id = processed.bill_number;
      }
      return processed;
    });
  }

  console.log(`  Loaded ${bills.length} bills`);
  allBills.push(...bills);
}

// Ensure public directory exists
const publicDir = path.join(__dirname, '../public');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

// Deduplicate bills by bill_id, keeping the latest version
// Use bill_number as fallback if bill_id is missing
const billMap = new Map();
const duplicates = [];

allBills.forEach(bill => {
  const id = bill.bill_id || bill.bill_number || bill.number;
  if (!id) {
    console.warn('Warning: Bill without ID found:', bill.title?.substring(0, 50));
    return;
  }

  if (billMap.has(id)) {
    duplicates.push(id);
    // Keep the existing one (assuming later files in the array are newer)
    // You could add more sophisticated logic here based on timestamps
  } else {
    billMap.set(id, bill);
  }
});

const uniqueBills = Array.from(billMap.values());

if (duplicates.length > 0) {
  console.log(`\n⚠️  Found ${duplicates.length} duplicate bills (kept latest version)`);
  console.log('Duplicate IDs:', [...new Set(duplicates)].slice(0, 10).join(', '));
}

// Write combined data
fs.writeFileSync(outputFile, JSON.stringify(uniqueBills, null, 2));

console.log(`\n✅ Success! Loaded ${allBills.length} bills, ${uniqueBills.length} unique from ${files.length} files`);
console.log(`📊 Output written to: ${outputFile}`);

// Print summary by state
const byState = {};
uniqueBills.forEach(bill => {
  const state = bill.state || 'Unknown';
  byState[state] = (byState[state] || 0) + 1;
});

console.log('\n📍 Bills by State:');
Object.entries(byState)
  .sort((a, b) => b[1] - a[1])
  .forEach(([state, count]) => {
    console.log(`  ${state}: ${count}`);
  });
