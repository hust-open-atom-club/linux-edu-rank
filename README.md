[![Pylint CI](https://github.com/hust-open-atom-club/linux-edu-rank/actions/workflows/pylint.yml/badge.svg)](https://github.com/hust-open-atom-club/linux-edu-rank/actions/workflows/pylint.yml)
[![Deploy Pages](https://github.com/hust-open-atom-club/linux-edu-rank/actions/workflows/update-page.yaml/badge.svg)](https://github.com/hust-open-atom-club/linux-edu-rank/actions/workflows/update-page.yaml)
[![License](https://img.shields.io/github/license/hust-open-atom-club/linux-edu-rank)](LICENSE)

# Linux Kernel Patch Statistic among Universities

This project analyzes the Linux kernel git history to rank universities by their patch contributions. It matches commit author email domains against a [university domain list](https://github.com/Hipo/university-domains-list), aggregates statistics (patch count, lines changed, contributors), and publishes the results as a static website via GitHub Pages.

## Quick Start

```bash
# Install PDM (Linux/macOS)
curl -sSL https://pdm-project.org/install-pdm.py | python3 -

# Install dependencies
pdm install

# Clone the Linux kernel repo (full history required)
git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

# Generate results
pdm start
```

The output is a `result.json` file and paginated HTML detail pages in `detail/`. Serve `index.html` with any web server to view the rankings.

## Requirements

- Python 3.9+
- [PDM](https://pdm-project.org/en/latest/) package manager
- A local clone of the Linux kernel repository (with full git history)

## Development

```bash
pdm install -G dev       # Install with dev dependencies (pylint, pytest)
pdm lint                 # Run pylint (threshold 9.0)
pdm test                 # Run all tests
```

## How It Works

1. Fetches the university domain list from [Hipo/university-domains-list](https://github.com/Hipo/university-domains-list)
2. Iterates through all git commits, matching author email domains to universities (with parent domain fallback, e.g. `cs.mit.edu` matches `mit.edu`)
3. Aggregates per-domain statistics and merges aliases for the same university
4. Ranks universities by patch count (tiebreak: total lines changed)
5. Writes `result.json` and generates paginated HTML detail pages

## CI/CD

- **Pylint CI**: Runs on every push/PR to `master` across Python 3.9-3.13
- **Page Deployment**: A daily scheduled workflow regenerates the data and deploys to GitHub Pages

## Documentation

See the [docs/](docs/) folder for more details:

- [Architecture](docs/architecture.md) - Project structure and data pipeline
- [Data Format](docs/data-format.md) - Schema of `result.json`

## License

[BSD-2-Clause](LICENSE)
