# LegiUI Deployment Guide

Complete guide for deploying the LegiUI dashboard in all environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Production Build](#production-build)
3. [GitHub Pages Deployment](#github-pages-deployment)
4. [Static Hosting Options](#static-hosting-options)
5. [Docker Deployment](#docker-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Data Integration](#data-integration)

---

## Local Development

### Quick Start

```bash
# Navigate to LegiUI directory
cd legiUI

# Install dependencies
npm install

# Load data from analysis results
npm run load-data

# Start development server
npm run dev

# Or use shortcut (load-data + dev)
npm start
```

The app will be available at `http://localhost:5173`

### Step-by-Step Setup

```bash
# ========================================
# STEP 1: Prerequisites Check
# ========================================
node --version
# Expected: v20.x or higher

npm --version
# Expected: v10.x or higher

# ========================================
# STEP 2: Install Dependencies
# ========================================
cd legiUI
npm install

# Expected output:
# added 250 packages in 15s

# ========================================
# STEP 3: Verify Analysis Data Exists
# ========================================
ls -lh ../data/analyzed/
# Expected: analysis_results_relevant.json and other analysis files

# If no data exists, run the pipeline first:
# cd ../scripts
# python run_analysis_pass.py
# cd ../legiUI

# ========================================
# STEP 4: Load Data
# ========================================
npm run load-data

# Expected output:
# Loading analysis data from ../data/analyzed/
# Found 2 result files:
#   - analysis_results_relevant.json
#   - analysis_alan_ct_bills_2025_relevant.json
# Loaded 68 bills from analysis_results_relevant.json
# Loaded 8 bills from analysis_alan_ct_bills_2025_relevant.json
# Combined 76 bills total
# Saved to public/bills.json (357 KB)

# Verify bills.json was created
ls -lh public/bills.json
# Expected: bills.json (~350 KB)

# ========================================
# STEP 5: Start Development Server
# ========================================
npm run dev

# Expected output:
#   VITE v5.0.0  ready in 500 ms
#
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose
#   ➜  press h to show help

# ========================================
# STEP 6: Open in Browser
# ========================================
# Automatically opens, or manually navigate to:
open http://localhost:5173

# ========================================
# STEP 7: Verify Dashboard Works
# ========================================
# You should see:
# ✅ Total bill count displayed
# ✅ Filters working (state, category, year, status)
# ✅ Search box functional
# ✅ Charts showing data distribution
# ✅ Table with bills
# ✅ Click bill to see modal with details

# ========================================
# DONE! 🎉
# ========================================
# Dashboard is running locally
# Press Ctrl+C in terminal to stop server
```

### Development Workflow

```bash
# Make code changes
# Vite auto-reloads on file changes

# If you add new analysis data:
npm run load-data  # Reload data
# Browser auto-refreshes

# Type checking
npm run tsc

# Linting
npm run lint

# Fix linting issues
npm run lint -- --fix
```

---

## Production Build

### Build for Static Hosting

```bash
# ========================================
# STEP 1: Ensure Data is Loaded
# ========================================
npm run load-data

# Verify bills.json exists
ls -lh public/bills.json

# ========================================
# STEP 2: Build Production Assets
# ========================================
npm run build

# Expected output:
# vite v5.0.0 building for production...
# ✓ 234 modules transformed.
# dist/index.html                   0.45 kB │ gzip:  0.30 kB
# dist/assets/index-BwN8kYVz.css   12.34 kB │ gzip:  3.21 kB
# dist/assets/index-D4KJh9fL.js   145.67 kB │ gzip: 48.92 kB
# ✓ built in 3.45s

# ========================================
# STEP 3: Verify Build Output
# ========================================
ls -lh dist/
# Expected:
# index.html
# assets/
# bills.json (copied from public/)
# vite.svg

tree dist/
# dist/
# ├── assets/
# │   ├── index-BwN8kYVz.css
# │   └── index-D4KJh9fL.js
# ├── bills.json
# ├── index.html
# └── vite.svg

# ========================================
# STEP 4: Preview Production Build Locally
# ========================================
npm run preview

# Expected output:
#   ➜  Local:   http://localhost:4173/
#   ➜  Network: use --host to expose

# Open and test
open http://localhost:4173

# ========================================
# STEP 5: Production Build is Ready!
# ========================================
# The dist/ directory contains everything needed
# Upload to any static hosting service
```

### Optimize Build Size

```bash
# Check bundle size
npm run build -- --mode production

# Analyze bundle (requires plugin)
npm install -D rollup-plugin-visualizer

# Add to vite.config.ts:
# import { visualizer } from 'rollup-plugin-visualizer'
# plugins: [react(), visualizer()]

npm run build
open stats.html  # Shows bundle composition
```

---

## GitHub Pages Deployment

### Automated Deployment via GitHub Actions

The repository includes a GitHub Actions workflow for automatic deployment.

#### Step 1: Update bills.json

```bash
cd legiUI

# Load latest analysis data
npm run load-data

# Verify file size is reasonable
ls -lh public/bills.json
# Expected: ~350 KB (acceptable for git)

# Commit the data file
git add public/bills.json
git commit -m "feat(data): update bills.json with latest analysis results"
git push origin main
```

#### Step 2: Trigger Deployment

**Option A: Via GitHub Actions UI**

```
1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "Deploy LegiUI to GitHub Pages" workflow
4. Click "Run workflow" button
5. Select branch: main
6. Click green "Run workflow" button
7. Wait ~2 minutes for build and deployment
```

**Option B: Via Git Tag (Automatic)**

```bash
# Create and push a tag
git tag -a legiui-v1.0.1 -m "Deploy updated analysis data"
git push origin legiui-v1.0.1

# GitHub Actions automatically deploys on tag push
```

#### Step 3: Access Deployed Site

```
URL: https://dblanken-yale.github.io/legiLLM/

Wait 1-2 minutes for deployment
Refresh browser if needed (Ctrl+Shift+R to bypass cache)
```

#### Step 4: Verify Deployment

```bash
# Check deployment status
# Visit: https://github.com/your-org/ai-scraper-ideas/actions

# Test live site
curl https://dblanken-yale.github.io/legiLLM/bills.json | jq '. | length'
# Expected: Number of bills in dataset

# Open in browser
open https://dblanken-yale.github.io/legiLLM/
```

### Manual GitHub Pages Setup (First Time)

If workflow doesn't exist, set up manually:

```bash
# ========================================
# STEP 1: Create GitHub Actions Workflow
# ========================================
mkdir -p .github/workflows

cat > .github/workflows/deploy-legiui.yml << 'EOF'
name: Deploy LegiUI to GitHub Pages

on:
  push:
    branches:
      - main
    paths:
      - 'legiUI/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        working-directory: ./legiUI
        run: npm ci

      - name: Build
        working-directory: ./legiUI
        run: npm run build

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './legiUI/dist'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
EOF

# ========================================
# STEP 2: Enable GitHub Pages in Repository Settings
# ========================================
echo "
Manual Steps Required:
1. Go to: https://github.com/your-org/ai-scraper-ideas/settings/pages
2. Under 'Source', select: GitHub Actions
3. Click 'Save'
"

# ========================================
# STEP 3: Commit and Push Workflow
# ========================================
git add .github/workflows/deploy-legiui.yml
git commit -m "ci: add GitHub Pages deployment workflow"
git push origin main

# ========================================
# STEP 4: Trigger First Deployment
# ========================================
# Go to Actions tab and manually run workflow
# Or push any change to legiUI/

# ========================================
# DONE! 🎉
# ========================================
# Site will be available at:
# https://your-org.github.io/your-repo/
```

---

## Static Hosting Options

### Netlify

```bash
# ========================================
# STEP 1: Build Production Assets
# ========================================
cd legiUI
npm run build

# ========================================
# STEP 2: Deploy via Netlify CLI
# ========================================
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
netlify deploy --prod --dir=dist

# Expected output:
# Deploying to main site URL...
# ✔ Finished hashing
# ✔ CDN requesting 4 files
# ✔ Finished uploading 4 assets
# ✔ Deploy is live!
#
# Unique Deploy URL: https://random-name.netlify.app

# ========================================
# STEP 3: Access Site
# ========================================
open https://your-site-name.netlify.app

# ========================================
# Continuous Deployment (Optional)
# ========================================
# Create netlify.toml in project root
cat > netlify.toml << 'EOF'
[build]
  base = "legiUI"
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
EOF

# Connect to Git repository
netlify init

# Now auto-deploys on git push!
```

### Vercel

```bash
# ========================================
# STEP 1: Install Vercel CLI
# ========================================
npm install -g vercel

# ========================================
# STEP 2: Login
# ========================================
vercel login

# ========================================
# STEP 3: Deploy
# ========================================
cd legiUI
vercel

# Follow prompts:
# Set up and deploy "~/ai-scraper-ideas/legiUI"? Y
# Which scope? (select your account)
# Link to existing project? N
# What's your project's name? legiui
# In which directory is your code located? ./
# Override settings? N

# ========================================
# STEP 4: Deploy to Production
# ========================================
vercel --prod

# Expected output:
# ✔ Production: https://legiui.vercel.app [copied]

# ========================================
# DONE! 🎉
# ========================================
open https://legiui.vercel.app
```

### AWS S3 + CloudFront

```bash
# ========================================
# STEP 1: Build
# ========================================
cd legiUI
npm run build

# ========================================
# STEP 2: Create S3 Bucket
# ========================================
aws s3 mb s3://legiui-dashboard --region us-east-1

# Enable static website hosting
aws s3 website s3://legiui-dashboard \
  --index-document index.html \
  --error-document index.html

# ========================================
# STEP 3: Upload Files
# ========================================
aws s3 sync dist/ s3://legiui-dashboard --delete

# Expected output:
# upload: dist/index.html to s3://legiui-dashboard/index.html
# upload: dist/bills.json to s3://legiui-dashboard/bills.json
# upload: dist/assets/index-xxx.js to s3://legiui-dashboard/assets/index-xxx.js

# ========================================
# STEP 4: Make Public
# ========================================
aws s3api put-bucket-policy \
  --bucket legiui-dashboard \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::legiui-dashboard/*"
    }]
  }'

# ========================================
# STEP 5: Access Site
# ========================================
# URL: http://legiui-dashboard.s3-website-us-east-1.amazonaws.com

# ========================================
# STEP 6: Add CloudFront (Optional, for HTTPS)
# ========================================
# Create CloudFront distribution via AWS Console
# Point origin to S3 bucket
# Enable HTTPS
# Add custom domain (optional)
```

### Azure Static Web Apps

```bash
# ========================================
# STEP 1: Create Static Web App
# ========================================
az staticwebapp create \
  --name legiui \
  --resource-group rg-legiscan-prod \
  --location eastus2 \
  --sku Free

# ========================================
# STEP 2: Get Deployment Token
# ========================================
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name legiui \
  --resource-group rg-legiscan-prod \
  --query "properties.apiKey" -o tsv)

# ========================================
# STEP 3: Install SWA CLI
# ========================================
npm install -g @azure/static-web-apps-cli

# ========================================
# STEP 4: Deploy
# ========================================
cd legiUI
npm run build

swa deploy \
  --app-location . \
  --output-location dist \
  --deployment-token "$DEPLOYMENT_TOKEN"

# ========================================
# STEP 5: Access Site
# ========================================
# Get URL
az staticwebapp show \
  --name legiui \
  --resource-group rg-legiscan-prod \
  --query "defaultHostname" -o tsv

# Open
open https://legiui.azurestaticapps.net
```

---

## Docker Deployment

### Development with Docker

```bash
# ========================================
# STEP 1: Create Dockerfile for LegiUI
# ========================================
cat > Dockerfile.ui << 'EOF'
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application files
COPY . .

# Load data (if available)
RUN if [ -d "../data/analyzed" ]; then npm run load-data; fi

# Expose port
EXPOSE 5173

# Start dev server
CMD ["npm", "run", "dev", "--", "--host"]
EOF

# ========================================
# STEP 2: Build Image
# ========================================
docker build -f Dockerfile.ui -t legiui:dev .

# ========================================
# STEP 3: Run Container
# ========================================
docker run -d \
  -p 5173:5173 \
  -v $(pwd)/../data:/app/data \
  -v $(pwd)/src:/app/src \
  --name legiui-dev \
  legiui:dev

# ========================================
# STEP 4: Access Dashboard
# ========================================
open http://localhost:5173

# ========================================
# STEP 5: View Logs
# ========================================
docker logs -f legiui-dev

# ========================================
# STEP 6: Stop Container
# ========================================
docker stop legiui-dev
docker rm legiui-dev
```

### Production with Docker + Nginx

```bash
# ========================================
# STEP 1: Create Production Dockerfile
# ========================================
cat > Dockerfile.prod << 'EOF'
# Build stage
FROM node:20-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run load-data || echo "No data to load"
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config (optional)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

# ========================================
# STEP 2: Create Nginx Config
# ========================================
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Don't cache index.html
    location = /index.html {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
EOF

# ========================================
# STEP 3: Build Production Image
# ========================================
docker build -f Dockerfile.prod -t legiui:prod .

# ========================================
# STEP 4: Run Production Container
# ========================================
docker run -d \
  -p 8080:80 \
  --name legiui-prod \
  legiui:prod

# ========================================
# STEP 5: Access Production Site
# ========================================
open http://localhost:8080

# ========================================
# STEP 6: Push to Registry (Optional)
# ========================================
docker tag legiui:prod yourregistry.azurecr.io/legiui:latest
docker push yourregistry.azurecr.io/legiui:latest
```

### Add to Main docker-compose.yml

```bash
# ========================================
# Add LegiUI Service to Existing docker-compose.yml
# ========================================
cat >> ../docker-compose.yml << 'EOF'

  legiui:
    build:
      context: ./legiUI
      dockerfile: Dockerfile.ui
    container_name: legiui
    ports:
      - "5173:5173"
    volumes:
      - ./legiUI:/app
      - /app/node_modules
      - ./data:/app/data:ro  # Read-only access to data
    environment:
      - NODE_ENV=development
    depends_on:
      - legiscan-pipeline
    networks:
      - legiscan-network
    command: npm run dev -- --host
EOF

# ========================================
# Start All Services
# ========================================
cd ..
docker-compose up -d

# Access LegiUI at http://localhost:5173
```

---

## Environment Configuration

### Environment Variables

Create `.env` file in `legiUI/` for environment-specific settings:

```bash
# .env
VITE_API_URL=https://api.example.com
VITE_ANALYTICS_ID=UA-XXXXXXXXX-X
VITE_ENV=production
```

Access in code:

```typescript
// src/config.ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:3000',
  analyticsId: import.meta.env.VITE_ANALYTICS_ID,
  environment: import.meta.env.VITE_ENV || 'development',
}
```

### Build-Time Configuration

Different configs for different environments:

```bash
# .env.development
VITE_API_URL=http://localhost:3000

# .env.production
VITE_API_URL=https://api.production.com

# .env.staging
VITE_API_URL=https://api.staging.com
```

Build for specific environment:

```bash
# Development
npm run dev

# Production
npm run build  # Uses .env.production

# Staging
npm run build -- --mode staging  # Uses .env.staging
```

---

## Data Integration

### Loading Data from Analysis Results

The default setup loads from local files:

```bash
# Load data from ../data/analyzed/
npm run load-data

# This runs: node scripts/load-data.js
# - Finds all *_relevant.json files in ../data/analyzed/
# - Extracts state codes from filenames and URLs
# - Combines all bills into single array
# - Outputs to public/bills.json
```

### Custom Data Source

Modify `scripts/load-data.js` for custom sources:

```javascript
// scripts/load-data.js
import fs from 'fs';
import path from 'path';

// Example: Load from API
async function loadFromAPI() {
  const response = await fetch('https://api.example.com/bills');
  const bills = await response.json();

  // Transform if needed
  const transformed = bills.map(bill => ({
    ...bill,
    state: extractState(bill),
    year: bill.year || 2025,
  }));

  // Save to public/bills.json
  fs.writeFileSync(
    'public/bills.json',
    JSON.stringify(transformed, null, 2)
  );

  console.log(`Loaded ${bills.length} bills from API`);
}

// Example: Load from database
async function loadFromDatabase() {
  const { Pool } = await import('pg');
  const pool = new Pool({
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
  });

  const result = await pool.query('SELECT * FROM bills WHERE is_relevant = true');
  const bills = result.rows;

  fs.writeFileSync(
    'public/bills.json',
    JSON.stringify(bills, null, 2)
  );

  console.log(`Loaded ${bills.length} bills from database`);
  await pool.end();
}

// Choose your data source
loadFromAPI();
// or loadFromDatabase();
// or default file-based loading
```

### Dynamic Data Loading

For production with live API:

```typescript
// src/utils/dataLoader.ts
export class DataLoader {
  private apiUrl = import.meta.env.VITE_API_URL;

  async loadData(): Promise<Bill[]> {
    if (this.apiUrl) {
      // Load from API
      const response = await fetch(`${this.apiUrl}/bills`);
      return await response.json();
    } else {
      // Load from static file
      const response = await fetch('/bills.json');
      return await response.json();
    }
  }
}
```

---

## Troubleshooting

### Build Fails

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Data Not Loading

```bash
# Verify bills.json exists
ls -lh public/bills.json

# Check file is valid JSON
cat public/bills.json | jq '.' > /dev/null
echo "JSON is valid"

# Re-run load-data
npm run load-data

# Check browser console for errors
# Open http://localhost:5173 and check DevTools Console
```

### Port Already in Use

```bash
# Find process using port 5173
lsof -i :5173

# Kill process
kill -9 <PID>

# Or use different port
npm run dev -- --port 3000
```

### GitHub Pages 404

```bash
# Check base URL in vite.config.ts
# For GitHub Pages at https://user.github.io/repo/
export default defineConfig({
  base: '/repo/',  # Must match repository name
  // ...
})

# Rebuild
npm run build

# Commit and redeploy
git add dist
git commit -m "fix: update base URL for GitHub Pages"
git push
```

---

## Performance Optimization

### Lazy Loading Routes

```typescript
// src/App.tsx
import { lazy, Suspense } from 'react';

const BillDetailModal = lazy(() => import('./components/BillDetailModal'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <BillDetailModal />
    </Suspense>
  );
}
```

### Code Splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'charts': ['recharts'],
          'utils': ['date-fns'],
        }
      }
    }
  }
})
```

### Compression

```bash
# Install compression plugin
npm install -D vite-plugin-compression

# Add to vite.config.ts
import compression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    react(),
    compression({ algorithm: 'gzip' }),
    compression({ algorithm: 'brotliCompress', ext: '.br' })
  ]
})
```

---

## Summary

### Quick Deploy Commands

| Platform | Command |
|----------|---------|
| **Local Dev** | `npm start` |
| **Build** | `npm run build` |
| **Preview** | `npm run preview` |
| **GitHub Pages** | Push to GitHub, run Actions workflow |
| **Netlify** | `netlify deploy --prod --dir=dist` |
| **Vercel** | `vercel --prod` |
| **AWS S3** | `aws s3 sync dist/ s3://bucket-name` |
| **Docker Dev** | `docker-compose up legiui` |

### File Locations

| File | Purpose |
|------|---------|
| `public/bills.json` | Data file (loaded from analysis results) |
| `dist/` | Production build output |
| `src/` | Source code |
| `scripts/load-data.js` | Data loading script |
| `.env` | Environment variables |
| `vite.config.ts` | Vite configuration |

---

**Next Steps:**
- Main docs: [../docs/README.md](../docs/README.md)
- Pipeline deployment: [../docs/DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md)
- Docker setup: [../docs/DOCKER_DEPLOYMENT.md](../docs/DOCKER_DEPLOYMENT.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team
