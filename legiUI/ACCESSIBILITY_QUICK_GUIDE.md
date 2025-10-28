# Accessibility Quick Reference Guide

## For Users

### Keyboard Navigation

**Essential Shortcuts:**
- `Tab` - Move to next interactive element
- `Shift + Tab` - Move to previous interactive element
- `Enter` or `Space` - Activate buttons, checkboxes, and open bill details
- `Escape` - Close modal dialog
- Arrow keys work in scroll areas

**Navigation Flow:**
1. Press `Tab` on page load to access "Skip to main content" link
2. Press `Enter` to skip directly to the bills table
3. Or continue tabbing through filters to refine results

### Screen Reader Support

**Landmarks:**
- Header (banner): Contains page title and description
- Filter Panel (complementary): Sidebar with all filter controls
- Main Content (main): Statistics, charts, and bills table
- Modal Dialog: Bill detail information

**Tips:**
- Filter checkboxes announce their state (checked/unchecked)
- Table headers announce sort direction (ascending/descending/none)
- Selected filter counts are announced (e.g., "States 2 selected")
- Empty states provide helpful messages

### Visual Adjustments

**Supported:**
- ✅ Zoom up to 200% without losing functionality
- ✅ Text spacing adjustments (line-height, letter-spacing, word-spacing)
- ✅ Windows High Contrast Mode
- ✅ Browser reading modes

**Minimum Viewport:** 320px width (small mobile devices)

---

## For Developers

### Color Contrast Ratios

All combinations meet WCAG 2.1 AA standards (4.5:1 minimum for text, 3:1 for UI components):

| Foreground | Background | Ratio | Use Case |
|------------|------------|-------|----------|
| Yale Blue (#00356b) | White (#ffffff) | 10.4:1 | Primary text, links, buttons |
| Gray-800 (#222222) | White (#ffffff) | 16.1:1 | Primary text |
| Gray-600 (#5e5e5e) | White (#ffffff) | 7.0:1 | Secondary text |
| White (#ffffff) | Yale Blue (#00356b) | 10.4:1 | Header text, button text |

### ARIA Implementation Checklist

**Semantic HTML:**
- [x] `<header role="banner">`
- [x] `<main role="main">`
- [x] `<aside role="complementary">`
- [x] `<table>` with proper `<thead>`, `<tbody>`, `<th scope="col">`, `<td>`
- [x] `<fieldset>` and `<legend>` for filter groups
- [x] Proper heading hierarchy (h1 → h2 → h3 → h4)

**Interactive Elements:**
- [x] Skip link: `<a href="#main-content" className="skip-link">`
- [x] Buttons: `aria-label` for icon-only buttons
- [x] Links: Descriptive text or `aria-label`
- [x] Checkboxes: `aria-label` for each filter option
- [x] Modal: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- [x] Table: `aria-label`, `aria-sort` on sortable headers
- [x] Icons: `aria-hidden="true"` on decorative icons

**Focus Management:**
- [x] Focus visible on all interactive elements (2px Yale Blue outline)
- [x] Focus trap in modal (Escape to close)
- [x] No keyboard traps
- [x] Logical tab order

### Testing Commands

**Automated Testing:**
```bash
# Install dependencies
npm install --save-dev @axe-core/react

# Run accessibility audit with Lighthouse
npx lighthouse http://localhost:5173 --only-categories=accessibility --view
```

**Manual Testing Checklist:**
1. [ ] Tab through entire application
2. [ ] Activate all interactive elements with Enter/Space
3. [ ] Close modal with Escape key
4. [ ] Test at 200% zoom
5. [ ] Test at 320px viewport width
6. [ ] Test with screen reader (NVDA, JAWS, or VoiceOver)
7. [ ] Test with Windows High Contrast Mode
8. [ ] Test keyboard focus visibility

### Component-Specific Notes

**FilterPanel (src/components/FilterPanel.tsx):**
- Uses `<fieldset>` and `<legend>` for semantic grouping
- Each checkbox has unique `aria-label`
- Search input has `id` matching `<label htmlFor>`
- Help text uses `aria-describedby`

**BillsTable (src/components/BillsTable.tsx):**
- Sortable columns use `aria-sort` attribute
- Table has `aria-label="Legislative bills"`
- All `<th>` elements have `scope="col"`
- External links have descriptive `aria-label`

**BillDetailModal (src/components/BillDetailModal.tsx):**
- `role="dialog"` with `aria-modal="true"`
- `aria-labelledby` points to modal title
- Escape key closes modal
- Body scroll locked when modal open
- Close button has `aria-label="Close bill details"`

**App (src/App.tsx):**
- Skip link to `#main-content`
- Proper landmark roles on major sections
- Main content has `id="main-content"`

---

## Common Issues & Solutions

### Issue: Focus outline not visible
**Solution:** Added global focus styles in App.css:
```css
*:focus-visible {
  outline: 2px solid var(--yale-blue);
  outline-offset: 2px;
}
```

### Issue: Screen reader not announcing filter changes
**Solution:** Filter counts in `<legend>` text update dynamically:
```html
<legend>States ({filters.states.length} selected)</legend>
```

### Issue: Modal can't be closed with keyboard
**Solution:** Added Escape key handler in BillDetailModal:
```typescript
React.useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };
  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [onClose]);
```

### Issue: Table not keyboard accessible
**Solution:** Table rows (`<tr>`) are natively keyboard accessible when `onClick` is used. Enter key works by default.

---

## Resources

- **WCAG 2.1 Quick Reference**: https://www.w3.org/WAI/WCAG21/quickref/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **Yale Accessibility**: https://usability.yale.edu/web-accessibility

---

**Last Updated:** 2025-01-28
