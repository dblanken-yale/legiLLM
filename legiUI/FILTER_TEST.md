# 🔍 Filter Testing Guide

## How Filtering SHOULD Work

Filters should **hide** bills that don't match the criteria, reducing the list to only matching bills.

## ✅ Quick Test

1. **Start the app:**
   ```bash
   npm start
   ```

2. **Open browser console (F12)**

3. **Test State Filter:**
   - Check the "IN" checkbox under States
   - **Expected result:**
     - Console shows: `🔍 Filtering: 59 total → 1 matching`
     - Table header shows: `Bills (1)`
     - Table shows ONLY the Indiana bill (SB0473)
     - Charts update to show only IN data

4. **Uncheck IN, check CT:**
   - **Expected result:**
     - Console shows: `🔍 Filtering: 59 total → 58 matching`
     - Table shows: `Bills (58)`
     - Table shows only Connecticut bills

5. **Test Category Filter:**
   - Clear all filters
   - Check "WORKFORCE" under Categories
   - **Expected result:**
     - Console shows: `🔍 Filtering: 59 total → X matching`
     - Table shows only bills with WORKFORCE category

6. **Test Search:**
   - Clear all filters
   - Type "SB0473" in search box
   - **Expected result:**
     - Console shows: `🔍 Filtering: 59 total → 1 matching`
     - Table shows only the Indiana bill

## 🐛 If Filtering Doesn't Work

### Symptom: All bills still show when filter is applied

**Check Console:**
- Do you see the `🔍 Filtering:` message?
- What does it say for total and matching?

**If you see `59 total → 59 matching` when filter is applied:**
- The filter isn't being applied correctly
- Check that you actually checked the checkbox (should have checkmark)
- Look at the filter section header - does it show "(1 selected)" or "(0 selected)"?

**If you DON'T see the filtering message at all:**
- React isn't re-rendering with new filters
- Try hard refresh (Cmd+Shift+R)
- Check browser console for JavaScript errors

### Symptom: Filter count changes but bills don't disappear

This would be a serious bug. Please check:

1. **Table header** - does it show the filtered count?
   - Example: `Bills (1)` when filtering by IN

2. **Console message** - does it show correct filtering?
   - Example: `🔍 Filtering: 59 total → 1 matching`

3. **Bills in table** - how many rows do you actually see?
   - If table header says `Bills (1)` but you see 59 rows, that's the bug
   - Take a screenshot and note the console message

## 📊 Expected Behavior Examples

### Example 1: Filter by Indiana
```
✓ States filter: IN checked
Console: 🔍 Filtering: 59 total → 1 matching
Table header: Bills (1)
Visible bills: 1 (SB0473 - Various health care matters)
```

### Example 2: Filter by CT + Enacted
```
✓ States filter: CT checked
✓ Status filter: Enacted checked
Console: 🔍 Filtering: 59 total → X matching
Table header: Bills (X)
Visible bills: Only enacted CT bills
```

### Example 3: Multiple Filters
```
✓ States: CT
✓ Categories: WORKFORCE
✓ Year: 2025
Console: 🔍 Filtering: 59 total → Y matching
Table header: Bills (Y)
Visible bills: Only CT bills from 2025 with WORKFORCE category
```

## 🎯 What The Code Does

The filtering logic (in `src/App.tsx`):

1. **Takes all loaded bills** (59 total)
2. **Applies each active filter:**
   - State filter: `bill.state` must be in selected states
   - Category filter: `bill.categories` must include at least one selected category
   - Year filter: `bill.year` must be in selected years
   - Status filter: `bill.bill_status` must be in selected statuses
   - Search filter: bill text must contain search query
3. **Returns only matching bills** to the table
4. **Updates all components:**
   - Table shows filtered bills
   - Charts show filtered data
   - Stats cards show filtered counts

## 🔧 Debugging Tips

**Enable more detailed logging:**
Open `src/App.tsx` and the `filteredBills` useMemo shows which filters are active.

**Check filter state:**
In browser console, type:
```javascript
// This won't work directly, but the logs should show you the filter state
```

**Check the actual data:**
```javascript
// In console after page loads:
// Look for the "Successfully loaded X bills" message
// Then look for "Available states for filtering" message
```

## ✅ Working Filter Examples

When working correctly:

1. **No filters selected:**
   - Shows all 59 bills
   - No filtering message in console

2. **One state selected (IN):**
   - Shows 1 bill
   - Console: `🔍 Filtering: 59 total → 1 matching`

3. **One state selected (CT):**
   - Shows 58 bills
   - Console: `🔍 Filtering: 59 total → 58 matching`

4. **Search for "workforce":**
   - Shows bills with "workforce" in any field
   - Console shows filtered count

5. **Multiple filters combined:**
   - Shows only bills matching ALL criteria
   - Progressively narrows results
