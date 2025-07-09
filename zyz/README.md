# Git University Stats

This tool analyzes Git commit contributions from university domains.

## Installation
```bash
pip install .
```

## Usage
```bash
git-uni-stats --path /path/to/repo --branch master
```

## Output
- `result.json`: Contains the aggregated statistics
- `detail/`: HTML files listing patch details

## Development
```bash
pip install -e .
```

## Build Package
```bash
python setup.py sdist bdist_wheel
```
