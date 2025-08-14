# Linux Kernel Patch Statistic among Universities

## Introduction

This project is to do some data statistics about Linux kernel patches contributed by universities.

The result is displayed in a web page with a table.

This project is managed by [PDM](https://pdm-project.org/en/latest/). For Linux/Mac OS Platforms, run the following command to install pdm.

```bash
curl -sSL https://pdm-project.org/install-pdm.py | python3 -
```

## Pre-requisites

- Python 3.9 or higher
- GitPython
- tqdm
- requests

Run the following command to install these dependencies:

```bash
pdm install
```

## How to run

1. Clone linux kernel repository with the following command:

```bash
git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
```

2. Run the following command to get the result json file:

```bash
pdm start
```

3. If you make changes, run the following command to lint your code:

```bash
pdm lint
```

4. The result will be saved in `result.json` file and html files in `detail`.

5. Use web server to serve `index.html`, `result.json` and `detail` to view the result.
