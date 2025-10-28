# Yale Branding & Design Tokens

This UI uses Yale's official design tokens from the [YaleSites tokens repository](https://github.com/yalesites-org/tokens).

## Typography

**Primary Font**: Mallory Compact
- Loaded from Yale's webfont CDN: `yale-webfonts.yalespace.org`
- Used throughout the application
- Fallback: sans-serif
- Applied to body and all text elements

**Available Weights:**
- Book (400) - Regular text
- Book Italic (400 italic)
- Medium (600) - Headings and emphasis
- Bold (700) - Strong emphasis

```css
@font-face {
  font-family: 'Mallory Compact';
  src: url('https://yale-webfonts.yalespace.org/MalloryCompact-Book.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}

/* Usage */
font-family: 'Mallory Compact', sans-serif;
```

## Color Palette

### Primary Colors
- **Yale Blue** (#00356b) - Primary brand color
- **Medium Blue** (#286dc0) - Secondary brand color
- **Light Blue** (#63aaff) - Accent highlights
- **Royal Blue** (#375597) - Supporting color

### Secondary Colors
- **Horizon** (#3E75AD) - Charts and data visualization
- **Shale** (#779FB1) - Subtle accents
- **Oceanic** (#346F6A) - Accent color for interactive elements
- **Soft Blue** (#E4EEF8) - Light backgrounds and hover states

### Accent Colors
- **Peach** (#D6A760) - Warm accent
- **Coral** (#FF6654) - Error/warning states

### Neutral Colors
- **Gray 100** (#f7f7f7) - Surface backgrounds
- **Gray 200** (#d9d9d9) - Borders
- **Gray 300** (#bababa) - Subtle borders
- **Gray 500** (#757575) - Secondary text
- **Gray 700** (#404040) - Supporting text
- **Gray 800** (#222222) - Primary text
- **Hale Gray** (#444C57) - Neutral text

## Usage

### Application Theme Mapping

```css
--primary-color: var(--yale-blue);
--secondary-color: var(--medium-blue);
--accent-color: var(--oceanic);
--background: var(--white);
--surface: var(--gray-100);
--text-primary: var(--gray-800);
--text-secondary: var(--gray-500);
--border: var(--gray-200);
--shadow: rgba(0, 53, 107, 0.1);
--hover-bg: var(--soft-blue);
```

### Component-Specific Usage

**Header Gradient**
- Uses Yale Blue → Medium Blue gradient

**Charts**
- Bar charts: Yale Blue primary
- Pie charts: Yale color palette rotation (Yale Blue, Medium Blue, Royal Blue, Horizon, Oceanic, Shale, Peach, Light Blue, Coral)

**Status Badges**
- Enacted: Soft Blue background with Yale Blue text
- Pending: Yellow warning
- Failed: Light red background with Coral text
- Vetoed: Gray 200 background with Hale Gray text

**Interactive States**
- Hover: Soft Blue background
- Links: Yale Blue
- Category badges: Yale Blue background

## References

- [YaleSites Tokens Repository](https://github.com/yalesites-org/tokens)
- [YaleSites Design System](https://yalesites.yale.edu)
