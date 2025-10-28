# 🚀 START HERE - View Your Legislative Data

## You currently have 59 relevant bills analyzed (58 CT, 1 IN)

### To view them in the dashboard:

```bash
# Make sure you're in the legiUI directory
cd legiUI

# Option 1: Use the all-in-one command
npm start

# Option 2: Manual steps
npm run load-data    # Loads data from ../data/analyzed
npm run dev          # Starts dev server at http://localhost:5173
```

### Then open your browser to: `http://localhost:5173`

---

## ✅ Verify the Data Loaded

**IMPORTANT: The filters are driven by the loaded data!**

If you **don't see "IN" in the state filter**, you're viewing mock data, not real data.

Open the browser console (F12 → Console tab) and look for:

```
✅ Successfully loaded 59 bills from bills.json
📍 Bills by state: {CT: 58, IN: 1}
```

If you see:
```
⚠️  Using mock data (2 bills)
OR
⚠️  MOCK DATA LOADED - Only 2 bills found!
```

Then:
1. Stop the dev server (Ctrl+C)
2. Run `npm run load-data`
3. Run `npm run dev` again
4. Hard refresh the browser (Cmd+Shift+R or Ctrl+Shift+R)
5. Check the left sidebar - you should now see both CT and IN checkboxes

---

## 📊 What You Should See

### In the Dashboard:
- **Total Bills**: 59 (all marked as relevant)
- **States**: 2 (CT and IN visible in filters and charts)
- **Multiple categories** across your bills
- **Real bill titles** from your LegiScan analysis

### If You Only See 2 Bills (or Wrong Data):
This means the UI is showing mock data instead of your real data. Follow the steps above to fix it.

---

## 🔄 Adding More States

When you analyze more states (e.g., New York, California):

```bash
# 1. Run analysis in parent project
cd ../scripts
python run_direct_analysis.py ../data/filtered/filter_results_ny_bills_2025.json

# 2. Reload UI data
cd ../legiUI
npm run load-data

# 3. Refresh browser
# New state will appear automatically!
```

---

## 🐛 Troubleshooting

### "Cannot GET /bills.json" in console

**Problem**: Dev server not running

**Solution**: Run `npm run dev` or `npm start`

### Still seeing mock data after loading

**Solution**: Hard refresh the browser (Cmd+Shift+R or Ctrl+Shift+R)

### Port 5173 already in use

**Solution**:
```bash
# Kill the existing process
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

---

## 📁 Your Data Files

The script combines these files automatically:
```
../data/analyzed/
├── analysis_alan_ct_bills_2025_relevant.json  (7 bills)
├── analysis_alan_in_bills_2025_relevant.json  (1 bill)
└── analysis_results_relevant.json              (51 bills)

Note: Files with "not_relevant" are automatically excluded

Combined into:
./public/bills.json (59 relevant bills total)
```

---

## 🎯 Quick Reference

| Command | What It Does |
|---------|-------------|
| `npm start` | Load data + start dev server (easiest!) |
| `npm run load-data` | Combine all analysis files into bills.json |
| `npm run dev` | Start development server |
| `npm run build` | Build for production deployment |

---

**Ready?** Run `npm start` and visit `http://localhost:5173` 🎉
