import git
import json
import os
import shutil
import requests
from tqdm import tqdm
from argparse import ArgumentParser
from datetime import datetime
from functools import reduce

from git_university_stats.meta import generate_meta
from git_university_stats.university_list import load_university_list, is_university_domain, get_university
from git_university_stats.git_commit import collect_commit_data
from git_university_stats.aggregate import aggregate_result
from git_university_stats.html_output import save_results

def main():
    parser = ArgumentParser()
    parser.add_argument("--branch", type=str, default="master")
    parser.add_argument("--path", type=str, default="/tmp/linux")
    parser.add_argument("--repo", type=str, default="Linux Mainline")
    args = parser.parse_args()

    repo = git.Repo(args.path)
    uni_list = load_university_list()

    patches, lines, details, authors = collect_commit_data(repo, args.branch, uni_list)
    meta = generate_meta(args.repo, args.branch, repo)

    result = aggregate_result(patches, lines, details, authors, uni_list)
    save_results(meta, result, details)

    print("Done!")

if __name__ == "__main__":
    main()
