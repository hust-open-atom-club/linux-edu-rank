#!/usr/bin/env python3
import json
import os
import shutil
from argparse import ArgumentParser
from datetime import datetime
from functools import reduce

import git
import requests
from tqdm import tqdm

import function_lib

def main():
    parser = ArgumentParser()
    parser.add_argument("--branch", type=str, default="master")
    parser.add_argument("--path", type=str, default="/tmp/linux")
    parser.add_argument("--repo", type=str, default="Linux Mainline")

    args = parser.parse_args()
    branch = args.branch
    path = args.path
    repo_name = args.repo

    repo = git.Repo(path)


    print("Getting university list...")
    university_list:list = requests.get(
        "https://github.com/Hipo/university-domains-list/raw/master/world_universities_and_domains.json"
    ).json()


    print("Getting commits list...")
    commits = list(repo.iter_commits(branch))

    meta = {
        "update": datetime.now().isoformat(),
        "repo": repo_name,
        "branch": branch,
        "commit": repo.commit("master").hexsha,
    }

    # exec command and turn pipe to iterator
    result_patches = {}
    result_lines = {}
    result_detail = {}
    result_authors = {}
    print("Total commits: %d", len(commits))
    for commit in tqdm(commits):
        email = commit.author.email
        if not email:
            continue
        # get email domain
        domain = email.split("@")[-1]
        if not function_lib.is_university_domain(domain, university_list):
            continue

        result_patches[domain] = result_patches.get(domain, 0) + 1
        result_lines[domain] = result_lines.get(domain, 0) + commit.stats.total["lines"]
        if result_detail.get(domain) is None:
            result_detail[domain] = []
        result_detail[domain].append(repo.git.show(commit.hexsha))
        if result_authors.get(domain) is None:
            result_authors[domain] = {}
        if result_authors.get(domain).get(email) is None:
            result_authors[domain][email] = [commit.author.name, 0, []]
        result_authors[domain][email][1] = result_authors[domain][email][1] + 1
        result_authors[domain][email][2].append(
            {
                "commit": commit.hexsha,
                "summary": commit.summary,
                "date": commit.authored_datetime.isoformat(),
                "files": commit.stats.total["files"],
                "lines": "-{}/+{}".format(
                    commit.stats.total["deletions"], commit.stats.total["insertions"]
                ),
            }
        )


    # sort and save result to file
    result = map(
        lambda x: {
            "domain": x[0],
            "count": x[1],
            "lines": result_lines[x[0]],
            "university": function_lib.get_university(x[0], university_list),
        },
        result_patches.items(),
    )

    result_tmp = {}
    # merge same university and set domain to list
    for item in result:

        if item["university"] is None:
            authors = function_lib.result_authors_transform(result_authors, item)
            authors.sort(key=lambda x: x["count"], reverse=True)
            result_tmp[item["domain"]] = {
                "name": f"Unknown ({item['domain']})",
                "domains": [item["domain"]],
                "university": None,
                "count": item["count"],
                "lines": item["lines"],
                "authors": authors,
            }
            continue
        name = item["university"]["name"]
        if result_tmp.get(name) is None:
            result_tmp[name] = {
                "name": name,
                "domains": [],
                "university": item["university"],
                "count": 0,
                "lines": 0,
                "authors": [],
            }
        if item["domain"] not in result_tmp[name]["domains"]:
            result_tmp[name]["domains"].append(item["domain"])
            result_tmp[name]["authors"].extend(function_lib.result_authors_transform(result_authors, item))
        result_tmp[name]["authors"].sort(key=lambda x: x["count"], reverse=True)
        result_tmp[name]["count"] += item["count"]
        result_tmp[name]["lines"] += item["lines"]

    result = list(result_tmp.values())
    result.sort(key=lambda x: x["count"], reverse=True)
    result = list(map(lambda x: x[1] | {"id": x[0] + 1}, enumerate(result)))

    result = reduce(
        lambda s, i: s
        + [
            i
            | {
                "rank": (
                    i["id"]
                    if len(s) == 0 or i["count"] != s[-1]["count"]
                    else s[-1]["rank"]
                )
            }
        ],
        result,
        [],
    )

    with open("result.json", "w") as f:
        f.write(json.dumps({"meta": meta, "data": result}, indent=2))
    print("Result saved to result.json")

    print("Save patches to detail dir...")

    shutil.rmtree("detail", ignore_errors=True)
    os.mkdir("detail")


    for item in result:
        domains = item["domains"]

        patches = []
        for d in domains:
            patches.extend(result_detail[d])
        function_lib.generate_html(item["id"], "Patches contributed by " + item["name"], patches)

    print("Done!")


if __name__ == "__main__":
    main()