#!/usr/bin/env python3
import json
import os
import shutil
from datetime import datetime
from functools import reduce

import git
import requests
from tqdm import tqdm

branch = "master"
path = "/home/chengziqiu/linux"
repo_name = "Linux Mainline"

repo = git.Repo("/home/chengziqiu/linux")


print("Getting university list...")
university_json = requests.get(
    "https://github.com/Hipo/university-domains-list/raw/master/world_universities_and_domains.json"
).text
university_list: list = json.loads(university_json)


print("Getting commits list...")
commits = list(repo.iter_commits(branch))

meta = {
    "update": datetime.now().isoformat(),
    "repo": repo_name,
    "branch": branch,
    "commit": repo.commit("master").hexsha,
}

# exec command and turn pipe to iterator
result = {}
result_detail = {}
print("Total commits: ", len(commits))
for commit in tqdm(commits):
    email = commit.author.email
    if not email:
        continue
    # get email domain
    domain = email.split("@")[-1]
    if not "edu" in domain:
        continue

    result[domain] = result.get(domain, 0) + 1
    if result_detail.get(domain) is None:
        result_detail[domain] = []
    result_detail[domain].append(repo.git.show(commit.hexsha))


def get_university(domain):
    for university in university_list:
        if domain in university["domains"]:
            return university

    for university in university_list:
        for raw_domain in university["domains"]:
            if domain.endswith(raw_domain) or raw_domain.endswith(domain):
                return university
    return None


# sort and save result to file
result = map(
    lambda x: {
        "domain": x[0],
        "count": x[1],
        "university": get_university(x[0]),
    },
    result.items(),
)

result_tmp = {}
# merge same university and set domain to list
for item in result:
    if item["university"] is None:
        result_tmp[item["domain"]] = {
            "name": f"Unknown ({item['domain']})",
            "domains": [item["domain"]],
            "university": None,
            "count": item["count"],
        }
        continue
    name = item["university"]["name"]
    if result_tmp.get(name) is None:
        result_tmp[name] = {
            "name": name,
            "domains": [],
            "university": item["university"],
            "count": 0,
        }
    if item["domain"] not in result_tmp[name]["domains"]:
        result_tmp[name]["domains"].append(item["domain"])
    result_tmp[name]["count"] += item["count"]

result = list(result_tmp.values())
result.sort(key=lambda x: x["count"], reverse=True)
result = list(map(lambda x: x[1] | {"id": x[0] + 1}, enumerate(result)))

result = reduce(
    lambda s, i: s
    + [
        i
        | {
            "rank": i["id"]
            if len(s) == 0 or i["count"] != s[-1]["count"]
            else s[-1]["rank"]
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
    str = "<h1>Patches contributed by {}</h1><hr>".format(item["name"])
    domains = item["domains"]
    for d in domains:
        patches = result_detail[d]
        for patch in patches:
            str += f"<pre>{patch}</pre>"
            str += "<hr>"
    with open(f"detail/{item['rank']}.html", "w") as f:
        f.write(str.encode("utf-8", "replace").decode("utf-8"))
print("Done!")
