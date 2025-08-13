# Linux Kernel Patch Statistic among Universities

## Introduction

This project is to do some data statistics about Linux kernel patches contributed by universities.

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
pdm start
```
3. If you make changes, run the following command to lint your code
```bash
pdm lint
```
4. The result will be saved in `result.json` file and html files in `detail`
5. Use web server to serve `index.html`, `result.json` and `detail` to view the result
