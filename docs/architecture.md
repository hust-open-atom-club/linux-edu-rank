# Architecture

## Project Structure

```
linux-edu-rank/
├── src/
│   └── main.py            # Single-file data pipeline
├── tests/
│   ├── conftest.py         # Adds src/ to sys.path for test imports
│   └── test_functions.py   # Unit tests for core functions
├── index.html              # Frontend SPA (React 18 + Ant Design)
├── result.json             # Generated output (not committed)
├── detail/                 # Generated HTML detail pages (not committed)
├── .github/workflows/
│   ├── pylint.yml          # CI: lint on push/PR across Python 3.9-3.13
│   └── update-page.yaml    # CD: daily data generation + GitHub Pages deploy
├── pyproject.toml          # PDM project config and scripts
└── .pylintrc               # Pylint config (Google Python style)
```

## Data Pipeline (`src/main.py`)

The entire pipeline runs as a single script with these stages:

```
Fetch university domain list (GitHub)
        │
        ▼
Iterate all git commits
        │
        ▼
Match author email domain → university
  (exact match, then parent domain fallback)
        │
        ▼
Aggregate per-domain stats
  (patch count, line count, author details)
        │
        ▼
Merge aliases for same university
  (e.g. cs.mit.edu + math.mit.edu → MIT)
        │
        ▼
Sort by (patch count, lines) descending
        │
        ▼
Assign ranks (same count → same rank)
        │
        ▼
Write result.json + paginated HTML detail pages
```

## Key Functions

All functions live in `src/main.py`:

| Function | Purpose |
|---|---|
| `main()` | Entry point: parses args, drives the pipeline |
| `get_university()` | Looks up university info by email domain (exact + parent fallback) |
| `transform_author_data()` | Converts raw author map into sorted structured list |
| `create_domain_result()` | Builds a result entry for a single domain |
| `merge_university_results()` | Merges entries that belong to the same university |
| `add_rankings()` | Assigns sequential IDs and tied ranks |
| `process_results()` | Orchestrates the above into the final ranked list |
| `generate_html_page()` | Renders a single paginated HTML detail page |
| `generate_all_html_files()` | Generates all detail pages for every university |

## Frontend

`index.html` is a self-contained SPA using:

- **React 18** (via CDN)
- **Ant Design** (via CDN)

It fetches `result.json` at runtime and renders the ranking table with search, sorting, and links to the detail pages.

## CI/CD Workflows

### Pylint CI (`pylint.yml`)

- **Trigger**: push or PR to `master`, manual dispatch
- **Matrix**: Python 3.9, 3.10, 3.11, 3.12, 3.13 on Ubuntu
- **Steps**: install deps with PDM, run `pdm lint`

### Page Deployment (`update-page.yaml`)

- **Trigger**: push to `master`, daily at 00:00 UTC, manual dispatch
- **Steps**:
  1. Checkout this repo and the full Linux kernel repo
  2. Install Python 3.12 + PDM + dependencies
  3. Run `pdm start` to generate `result.json` and `detail/`
  4. Copy artifacts to `dist/` and deploy to GitHub Pages
