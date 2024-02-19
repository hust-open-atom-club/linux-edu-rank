# Linux Kernel Contribution Ranking among Universities

## Introduction

This project is to rank the contribution of universities to the Linux kernel.

The result is displayed in a web page with a table.

## Pre-requisites

- Python 3.9 or higher
- GitPython
- tqdm
- requests

## How to run

1. Clone linux kernel repository
2. Run the following command to get the result json file
```bash
./linux-statistic.py --path /path/to/linux-kernel-repo --branch BRANCH_NAME --repo DISPLAY_REPO_NAME
```
3. The result will be saved in `result.json` file and html files in `detail`
4. Use web server to serve `index.html`, `result.json` and `detail` to view the result
