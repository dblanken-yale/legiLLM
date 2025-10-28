# 🔧 Troubleshooting Guide

## ❗ "I don't see Indiana (IN) in the state filters"

**This means you're viewing MOCK DATA, not your real data!**

### Why This Happens

The UI has 2 bills of mock data built-in for development. If the dev server can't load `public/bills.json`, it falls back to this mock data, which only has 2 Connecticut bills.

### ✅ How to Fix

**Step-by-step:**

1. **Make sure you've loaded the data:**
   ```bash
   npm run load-data
   ```

   You should see:
   ```
   ✅ Success! Loaded 59 bills, 59 unique from 3 files
   📍 Bills by State:
     CT: 58
     IN: 1
   ```

2. **Make sure dev server is running:**
   ```bash
   npm run dev
   ```

   Should show:
   ```
   VITE v7.x.x  ready in xxx ms
   ➜  Local:   http://localhost:5173/
   ```

3. **Open browser to http://localhost:5173**

4. **Open browser console (F12 → Console tab)**

5. **Look for this message:**
   ```
   ✅ Successfully loaded 59 bills from bills.json
   📍 Bills by state: {CT: 58, IN: 1}
   ```

   **If you see this instead:**
   ```
   ❌ Error loading bills.json: ...
   ⚠️  Using mock data (2 bills)
   ```

   Then the file isn't being served. Go back to step 1.

6. **Hard refresh the browser:**
   - **Mac**: Cmd + Shift + R
   - **Windows/Linux**: Ctrl + Shift + R
   - **Or**: Clear browser cache

### What You Should See After Fix

**Left Sidebar - States Filter:**
```
□ CT
□ IN
```

**Stats at Top:**
```
Total Bills: 59
States: 2
```

**Charts:**
- Pie chart showing CT (58) and IN (1)
- Bar charts with both states

**Table:**
- 59 rows total
- Mix of CT and IN bills
- Indiana bill: SB0473 "Various health care matters"

---

## ❗ "I see the right number of bills but filters still wrong"

This is very rare but can happen with browser caching.

### Fix:

1. **Clear browser cache completely**
2. **Close all browser tabs**
3. **Stop dev server** (Ctrl+C)
4. **Delete build artifacts:**
   ```bash
   rm -rf dist node_modules/.vite
   ```
5. **Restart:**
   ```bash
   npm run dev
   ```
6. **Open in incognito/private window** to test

---

## ❗ "Console shows error: Cannot GET /bills.json"

**Problem:** Dev server isn't running or isn't serving the file correctly.

### Fix:

1. **Stop server** (Ctrl+C)
2. **Check file exists:**
   ```bash
   ls -lh public/bills.json
   ```
   Should show ~395K file
3. **Restart server:**
   ```bash
   npm run dev
   ```
4. **Test file directly:** Visit http://localhost:5173/bills.json
   - Should show JSON data
   - If you get 404, something is wrong with Vite config

---

## ❗ "I ran load-data but nothing changed"

### Fix:

1. **After running `npm run load-data`, you MUST refresh the browser**
2. **Better yet, restart the dev server:**
   ```bash
   # Stop server (Ctrl+C)
   npm run dev
   # Hard refresh browser
   ```

---

## 🔍 Diagnostic Commands

**Check what data is loaded:**
```bash
# Should show 59
cat public/bills.json | jq 'length'

# Should show CT: 58, IN: 1
cat public/bills.json | jq '[.[] | .state] | group_by(.) | map({state: .[0], count: length})'

# Check unique states
cat public/bills.json | jq '[.[] | .state] | unique'
```

**Re-generate data from scratch:**
```bash
rm public/bills.json
npm run load-data
npm run dev
```

---

## 🎯 Quick Test

To verify everything is working:

1. Run: `npm start` (loads data + starts server)
2. Open: http://localhost:5173
3. Press F12 (open console)
4. Look for: `✅ Successfully loaded 59 bills`
5. Click on **States filter** in left sidebar
6. You should see: **CT** and **IN** checkboxes

If you **only see CT**, you're viewing mock data!

---

## 🔄 Complete Reset (Nuclear Option)

If nothing else works:

```bash
# 1. Stop everything
# Press Ctrl+C to stop dev server

# 2. Clean everything
rm -rf node_modules dist public/bills.json

# 3. Fresh install
npm install

# 4. Load data
npm run load-data

# 5. Start fresh
npm run dev

# 6. Open in incognito browser window
# Visit: http://localhost:5173
```

---

## 📊 Expected Console Output

**When working correctly:**
```
Attempting to load bills.json...
✅ Successfully loaded 59 bills from bills.json
📍 Bills by state: {CT: 58, IN: 1}
```

**When using mock data (WRONG):**
```
Attempting to load bills.json...
❌ Error loading bills.json: HTTP error! status: 404
⚠️  Using mock data (2 bills). To load real data:
   1. Run: npm run load-data
   2. Refresh the browser
```

---

## 🆘 Still Not Working?

1. **Check you're in the right directory:**
   ```bash
   pwd
   # Should show: .../ai-scraper-ideas/legiUI
   ```

2. **Check Node version:**
   ```bash
   node --version
   # Should be v20.x or higher
   ```

3. **Check files exist:**
   ```bash
   ls -la public/bills.json
   ls -la ../data/analyzed/*_relevant.json
   ```

4. **Try a different browser** (Chrome, Firefox, Safari)

5. **Check for port conflicts:**
   ```bash
   lsof -i :5173
   # If something is running, kill it:
   lsof -ti:5173 | xargs kill -9
   ```

---

## ✅ Success Checklist

When everything is working, you should have:

- ✅ File `public/bills.json` exists (~395KB)
- ✅ Console shows "Successfully loaded 59 bills"
- ✅ Top stats show "Total Bills: 59" and "States: 2"
- ✅ Left sidebar States filter shows both "CT" and "IN"
- ✅ Pie chart shows two slices (CT and IN)
- ✅ Table has 59 rows
- ✅ Searching for "SB0473" finds the Indiana bill
- ✅ Filtering by state "IN" shows 1 bill

If ALL of these are true, you're viewing real data! 🎉
