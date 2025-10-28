# LegiUI Setup Guide

## Quick Start

```bash
# 1. Install dependencies
cd legiUI
npm install

# 2. Load data from analysis results
npm run load-data

# 3. Start the dashboard
npm run dev

# Or use the all-in-one command:
npm start
```

Visit `http://localhost:5173` to view the dashboard.

## How It Works

### Data Flow

```
Parent Project Analysis
  ↓
../data/analyzed/*.json
  ↓
scripts/load-data.js (combines & deduplicates)
  ↓
public/bills.json
  ↓
React UI loads and displays
```

### The load-data Script

**Location**: `scripts/load-data.js`

**What it does:**
1. Scans `../data/analyzed/` for all `*_relevant.json` files
2. Loads each file and normalizes the data format
3. Extracts state codes from:
   - Filenames: `analysis_alan_ct_bills_2025_relevant.json` → `CT`
   - URLs: `https://legiscan.com/IN/bill/SB0473/2025` → `IN`
4. Deduplicates bills by `bill_id` (or `bill_number` as fallback)
5. Outputs combined data to `public/bills.json`

**Supported Formats:**
- ✅ AI-filtered format (from `run_filter_pass.py`)
- ✅ Vector similarity format (Alan's format)
- ✅ Nested format with `{bill: {...}, analysis: {...}}`
- ✅ Flat format with all fields at top level

### Data Updates

**When to run `npm run load-data`:**
- After running analysis scripts in the parent project
- When you add new states
- When you re-analyze existing bills
- Before starting the dev server with `npm run dev`

**Or just use:**
```bash
npm start  # Automatically loads data then starts dev server
```

## Current Data

Run `npm run load-data` to see:
- Total bills loaded
- Number of unique bills (after deduplication)
- Bills per state

Example output:
```
✅ Success! Loaded 77 bills, 77 unique from 6 files
📊 Output written to: public/bills.json

📍 Bills by State:
  CT: 76
  IN: 1
```

## Customization

### Adding New States

The script automatically handles new states:
1. Run analysis in parent project for new state
2. Results saved to `../data/analyzed/analysis_*_STATE_*_relevant.json`
3. Run `npm run load-data`
4. New state appears in the UI

### Adding State Mappings

Edit `scripts/load-data.js`:

```javascript
const stateMap = {
  'ct': 'CT',
  'in': 'IN',
  'ny': 'NY',
  'ca': 'CA',
  // Add more states here
};
```

### Filtering Data

Modify `scripts/load-data.js` to filter bills:

```javascript
// After loading bills, before deduplication:
const filteredBills = allBills.filter(bill => {
  // Example: Only include enacted bills
  return bill.bill_status === 'Enacted';

  // Example: Only include bills from specific years
  // return bill.year >= 2024;

  // Example: Only include specific categories
  // return bill.categories?.includes('Workforce');
});
```

## Troubleshooting

### "Using mock data" message in console

**Problem**: UI can't find `public/bills.json`

**Solution**: Run `npm run load-data` before starting dev server

### Bills showing as "Unknown" state

**Problem**: State extraction failed

**Causes:**
1. Filename doesn't match pattern `*_XX_bills_*`
2. URL doesn't match LegiScan format
3. Bill data missing state field

**Solution**:
- Check filename format
- Verify URLs contain state code
- Manually add state field to data

### Duplicate bills appearing

**Problem**: Same bill appearing multiple times

**Cause**: Bills missing `bill_id` or `bill_number`

**Solution**: Ensure all bills have unique identifier. Script will log warnings for bills without IDs.

### No data loading

**Check:**
1. Parent directory has `data/analyzed/` folder
2. Folder contains `*_relevant.json` files
3. Files are valid JSON
4. Run script with `npm run load-data` and check for errors

## Production Deployment

### Build for Production

```bash
# 1. Load latest data
npm run load-data

# 2. Build
npm run build

# 3. Deploy dist/ folder
# The public/bills.json file is included in the build
```

### Alternative: API Integration

For dynamic data, update `src/utils/dataLoader.ts`:

```typescript
async loadData(_dataPath: string = '../data/analyzed'): Promise<Bill[]> {
  try {
    // Fetch from your API instead of static file
    const response = await fetch('https://your-api.com/bills');
    const data = await response.json();
    this.bills = this.normalizeBills(data);
    return this.bills;
  } catch (error) {
    console.error('Error loading bills:', error);
    return this.loadMockData();
  }
}
```

## File Structure

```
legiUI/
├── scripts/
│   └── load-data.js          # Data loading & combination script
├── public/
│   └── bills.json            # Combined data (generated)
├── src/
│   ├── utils/
│   │   └── dataLoader.ts     # Data loading utility
│   └── ...
└── package.json
```

## npm Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run load-data` - Load data from analysis results
- `npm start` - Load data + start dev server
- `npm run lint` - Run ESLint
