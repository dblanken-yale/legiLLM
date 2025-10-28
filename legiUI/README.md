# LegiUI - Legislative Analysis Dashboard

A modern React-based dashboard for visualizing and exploring palliative care legislative data across multiple states, years, and policy categories.

## Features

### 🎯 Core Functionality
- **Multi-dimensional Filtering**: Filter bills by state, category, year, status, and legislation type
- **Real-time Search**: Search across bill titles, summaries, tags, and categories
- **Interactive Visualizations**: Charts and graphs showing distribution across categories, states, years, and status
- **Detailed Bill Views**: Click any bill to see complete details including provisions, impact analysis, and tags
- **Sortable Tables**: Sort bills by number, title, state, year, or status
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### 📊 Visualizations
- **Category Distribution**: Bar chart showing bills across 8 palliative care policy categories
- **State Breakdown**: Pie chart showing distribution across states
- **Temporal Analysis**: Year-over-year bill trends
- **Status Overview**: Current status of all bills (Enacted, Pending, Failed, Vetoed)

### 🏷️ Policy Categories
1. Clinical Skill-Building
2. Patient Rights
3. Payment
4. Pediatric Palliative Care
5. Public Awareness
6. Quality/Standards
7. Telehealth
8. Workforce

## Getting Started

### Prerequisites
- Node.js 20.x or later
- npm 10.x or later

### Installation

```bash
# Navigate to the legiUI directory
cd legiUI

# Install dependencies
npm install

# Load data from analysis results
npm run load-data

# Start the development server
npm run dev
```

**Or use the shortcut:**
```bash
npm start  # Runs load-data then dev in one command
```

The application will open at `http://localhost:5173`

**Note**: The `load-data` script automatically combines all `*_relevant.json` files from `../data/analyzed/` into a single `public/bills.json` file. It extracts state information from:
1. Filenames (e.g., `analysis_alan_ct_bills_2025_relevant.json` → CT)
2. LegiScan URLs (e.g., `https://legiscan.com/IN/bill/...` → IN)

Run `npm run load-data` whenever you add new analysis results.

### Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Data Integration

### Automatic Data Loading (Default)

The dashboard automatically loads data from your analysis results:

1. **Run Analysis**: Use the parent project's analysis scripts:
   ```bash
   cd ..  # Go to parent directory
   cd scripts
   python run_analysis_pass.py
   # or
   python run_direct_analysis.py ../data/filtered/filter_results_*.json
   ```

2. **Load Data into UI**:
   ```bash
   cd ../legiUI
   npm run load-data
   ```

3. **Start Dashboard**:
   ```bash
   npm run dev
   # or use shortcut that does both:
   npm start
   ```

The `load-data` script automatically:
- Finds all `*_relevant.json` files in `../data/analyzed/`
- Extracts state codes from filenames and URLs
- Combines data from multiple states (CT, IN, NY, etc.)
- Handles both AI-filtered and vector similarity formats
- Normalizes data structure for the UI
- Outputs to `public/bills.json`

### Alternative Integration Methods

#### Option 1: Custom API Endpoint

For production deployments, update `src/utils/dataLoader.ts`:

```typescript
async loadData(_dataPath: string = '../data/analyzed'): Promise<Bill[]> {
  const response = await fetch('https://your-api.com/bills');
  const data = await response.json();
  this.bills = this.normalizeBills(data);
  return this.bills;
}
```

#### Option 2: Custom Data Script

Modify `scripts/load-data.js` to load from different sources:
- Add more state mappings
- Include additional data fields
- Filter by date ranges
- Apply custom transformations

### Data Format

The dashboard expects bills in the following format:

```typescript
interface Bill {
  bill_id: string;
  bill_number: string;
  title: string;
  url: string;
  state?: string;
  year?: string | number;
  session?: string;
  is_relevant: boolean;
  relevance_reasoning?: string;
  summary?: string;
  bill_status?: string;
  legislation_type?: string;
  categories?: string[];
  tags?: string[];
  key_provisions?: string[];
  palliative_care_impact?: string;
  exclusion_check?: string;
  special_flags?: string[];
  status_date?: string;
  last_action?: string;
}
```

This matches the output format from the `run_analysis_pass.py` and `run_direct_analysis.py` scripts.

## Project Structure

```
legiUI/
├── src/
│   ├── components/          # React components
│   │   ├── BillDetailModal.tsx
│   │   ├── BillsTable.tsx
│   │   ├── Charts.tsx
│   │   ├── FilterPanel.tsx
│   │   └── StatsCard.tsx
│   ├── types/               # TypeScript type definitions
│   │   └── bill.ts
│   ├── utils/               # Utility functions
│   │   └── dataLoader.ts
│   ├── App.tsx              # Main application component
│   ├── App.css              # Application styles
│   └── main.tsx             # Application entry point
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Technology Stack

- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Recharts**: Data visualization library
- **Lucide React**: Icon library
- **date-fns**: Date formatting utilities

## Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run tsc

# Linting
npm run lint
```

### Adding New Features

#### Add a New Filter

1. Update `FilterState` in `src/types/bill.ts`
2. Add filter UI in `src/components/FilterPanel.tsx`
3. Update filter logic in `src/App.tsx`

#### Add a New Visualization

1. Create component in `src/components/`
2. Import and use in `src/App.tsx`
3. Add corresponding styles in `src/App.css`

## Deployment

### Vite Static Hosting

The built application is a static site that can be deployed to:

- **Netlify**: Drop the `dist/` folder
- **Vercel**: Connect your git repository
- **GitHub Pages**: Use `gh-pages` package
- **AWS S3**: Upload `dist/` contents
- **Any static host**: Serve the `dist/` directory

### Environment Configuration

For API endpoints, create a `.env` file:

```env
VITE_API_URL=https://your-api-endpoint.com
```

Access in code:

```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Integration with Analysis Pipeline

This UI is designed to work seamlessly with the legislative analysis pipeline in the parent directory:

1. **Run Analysis**: Use `scripts/run_analysis_pass.py` or `scripts/run_direct_analysis.py`
2. **Output Location**: Results saved to `data/analyzed/`
3. **Load in UI**: Configure `dataLoader.ts` to load from `data/analyzed/` directory
4. **Automatic Updates**: Re-run analysis and refresh UI to see new data

### Example Integration Script

Create `legiUI/scripts/load-data.js`:

```javascript
import fs from 'fs';
import path from 'path';

const analysisDir = '../data/analyzed';
const outputFile = './public/bills.json';

// Combine all relevant analysis files
const files = fs.readdirSync(analysisDir)
  .filter(f => f.includes('relevant.json'));

const allBills = [];
for (const file of files) {
  const data = JSON.parse(
    fs.readFileSync(path.join(analysisDir, file), 'utf-8')
  );
  allBills.push(...data);
}

fs.writeFileSync(outputFile, JSON.stringify(allBills, null, 2));
console.log(`Loaded ${allBills.length} bills from ${files.length} files`);
```

Run before starting dev server:

```bash
node scripts/load-data.js && npm run dev
```

## Customization

### Theming

Update CSS variables in `src/App.css`:

```css
:root {
  --primary-color: #0088FE;
  --secondary-color: #00C49F;
  --background: #ffffff;
  --surface: #f5f5f5;
  --text-primary: #333333;
  --text-secondary: #666666;
  --border: #e0e0e0;
  --shadow: rgba(0, 0, 0, 0.1);
}
```

### Chart Colors

Modify `COLORS` array in `src/components/Charts.tsx`:

```typescript
const COLORS = [
  '#0088FE',
  '#00C49F',
  '#FFBB28',
  '#FF8042',
  // Add more colors...
];
```

## Troubleshooting

### Data Not Loading

1. Check browser console for errors
2. Verify data format matches expected structure
3. Check network tab for API request failures
4. Ensure CORS is configured if using external API

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Type Errors

```bash
# Run type checking
npm run tsc

# Fix common issues by ensuring types match
```

## Future Enhancements

- [ ] Export filtered results to CSV/Excel
- [ ] Save and share filter configurations
- [ ] Bill comparison view
- [ ] Historical trend analysis
- [ ] Email notifications for new bills
- [ ] Bulk bill operations
- [ ] Custom category definitions
- [ ] Advanced search with operators
- [ ] Bookmark favorite bills

## Contributing

This UI is part of the LegiScan State Bill Analysis Pipeline. For bugs or feature requests, please update the main project documentation.

## License

Part of the ai-scraper-ideas project.
