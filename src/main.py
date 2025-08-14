#!/usr/bin/env python3
"""Generate ranked contributions of university-affiliated commits from a Git repo."""

import json
import os
import shutil
from argparse import ArgumentParser
from datetime import datetime

import git
import requests
from tqdm import tqdm

import pytz

shanghai_tz = pytz.timezone("Asia/Shanghai")

parser = ArgumentParser()
parser.add_argument("--branch", type=str, default="master")
parser.add_argument("--path", type=str, default="./linux")
parser.add_argument("--repo", type=str, default="Linux Mainline")

args = parser.parse_args()
branch = args.branch
path = args.path
repo_name = args.repo

repo = git.Repo(path)

print("Getting university list...")
university_list: list = requests.get(
    "https://github.com/Hipo/university-domains-list/raw/master/world_universities_and_domains.json",
    timeout=(5, 10)
).json()

# assemble all domains into one set
all_domains = set(d for u in university_list for d in u["domains"])
# speed up domain check by caching
non_university_domain_cache = set()

print("Getting commits list...")
commits = list(repo.iter_commits(branch))

meta = {
    "update": datetime.now(shanghai_tz).isoformat(),
    "repo": repo_name,
    "branch": branch,
    "commit": repo.commit("master").hexsha,
}

# exec command and turn pipe to iterator
result_patches = {}
result_lines = {}
result_detail = {}
result_authors = {}
print("Total commits: ", len(commits))
for commit in tqdm(commits):
    email = commit.author.email
    if not email:
        continue
    # get email domain
    email_domain = email.split("@")[-1]
    # check if the domain is in the non_university_domain cache
    if email_domain in non_university_domain_cache:
        continue
    if email_domain not in all_domains:
        # check if its parent domains belong to a university
        parts = email_domain.split(".")
        parent_domains = [".".join(parts[i:]) for i in range(0, len(parts))]
        if all(parent not in all_domains for parent in parent_domains):
            non_university_domain_cache.add(email_domain)
            continue

    # cache commit stats
    commit_stats = commit.stats.total

    # initialize result for this domain if not exists
    if email_domain not in result_patches:
        result_patches[email_domain] = 0
        result_lines[email_domain] = 0
        result_detail[email_domain] = []
        result_authors[email_domain] = {}

    result_patches[email_domain] += 1
    result_lines[email_domain] += commit_stats["lines"]
    result_detail[email_domain].append(repo.git.show(commit.hexsha))

    # update author information
    if email not in result_authors[email_domain]:
        result_authors[email_domain][email] = [commit.author.name, 0, []]
    result_authors[email_domain][email][1] += 1
    result_authors[email_domain][email][2].append(
        {
            "commit": commit.hexsha,
            "summary": commit.summary,
            "date": commit.authored_datetime.isoformat(),
            "files": commit_stats["files"],
            "lines": f'-{commit_stats["deletions"]}/+{commit_stats["insertions"]}'
        }
    )


def get_university(domain_name, uni_list):
    """Get the university information for a given domain."""
    # Check exact domain match first
    for university in uni_list:
        if domain_name in university["domains"]:
            return university

    # Check parent domains
    domain_parts = domain_name.split(".")
    parent_domains_list = [".".join(domain_parts[i:]) for i in range(0, len(domain_parts))]
    for university in uni_list:
        if any(parent in university["domains"] for parent in parent_domains_list):
            return university

    return None


def transform_author_data(authors_map, target_domain):
    """Transform author data for a specific domain into a structured format."""
    authors = []
    for author_email, author_info in authors_map.get(target_domain, {}).items():
        authors.append({
            "email": author_email,
            "name": author_info[0],
            "count": author_info[1],
            "commits": author_info[2],
        })
    return sorted(authors, key=lambda x: x["count"], reverse=True)


def create_domain_result(domain_name, patches_count, lines_count, university, authors_map):
    """Create a result entry for a domain."""
    authors = transform_author_data(authors_map, domain_name)

    if university is None:
        return {
            "name": f"Unknown ({domain_name})",
            "domains": [domain_name],
            "university": None,
            "count": patches_count,
            "lines": lines_count,
            "authors": authors,
        }

    return {
        "name": university["name"],
        "domains": [domain_name],
        "university": university,
        "count": patches_count,
        "lines": lines_count,
        "authors": authors,
    }


def merge_university_results(results):
    """Merge results from the same university."""
    merged_results = {}

    for item in results:
        university_name = item["name"]
        domain_name = item["domains"][0]  # Each item has exactly one domain at this point

        if university_name not in merged_results:
            merged_results[university_name] = item.copy()
        else:
            # Merge with existing entry
            existing = merged_results[university_name]
            if domain_name not in existing["domains"]:
                existing["domains"].append(domain_name)
                existing["authors"].extend(item["authors"])
                existing["count"] += item["count"]
                existing["lines"] += item["lines"]
                existing["authors"].sort(key=lambda x: x["count"], reverse=True)

    return list(merged_results.values())


def add_rankings(sorted_results):
    """Add ID and rank fields to sorted results."""
    # Add sequential IDs
    results_with_ids = []
    for index, item in enumerate(sorted_results):
        item_with_id = item.copy()
        item_with_id["id"] = index + 1
        results_with_ids.append(item_with_id)

    # Add rankings (same count gets same rank)
    results_with_ranks = []
    for item in results_with_ids:
        if not results_with_ranks or item["count"] != results_with_ranks[-1]["count"]:
            rank = item["id"]
        else:
            rank = results_with_ranks[-1]["rank"]

        item_with_rank = item.copy()
        item_with_rank["rank"] = rank
        item_with_rank["contributor_count"] = len(item_with_rank["authors"])
        results_with_ranks.append(item_with_rank)

    return results_with_ranks


def process_results(patches_map, lines_map, authors_map, uni_list):
    """Process raw results into final ranked format."""
    # Create initial results with university information
    initial_results = []
    for domain_name, patches_count in patches_map.items():
        lines_count = lines_map[domain_name]
        university = get_university(domain_name, uni_list)
        result_item = create_domain_result(domain_name, patches_count, lines_count, university, authors_map)
        initial_results.append(result_item)

    # Merge results by university
    merged_results = merge_university_results(initial_results)

    # Sort by patch count (descending)
    sorted_results = sorted(merged_results, key=lambda x: (x["count"], x["lines"]), reverse=True)

    # Add rankings
    final_results = add_rankings(sorted_results)

    return final_results


def create_pagination_html(page, page_num, get_href_func):
    """Create pagination HTML for a given page."""
    pagination = ""

    if page > 1:
        pagination += f"<a href='{get_href_func(page - 1)}'>&lt;&lt;Prev</a>"

    for i in range(1, page_num + 1):
        if i == page:
            pagination += f"<span>[{i}]</span>"
        else:
            pagination += f"<a href='{get_href_func(i)}'>{i}</a>"

    if page < page_num:
        pagination += f"<a href='{get_href_func(page + 1)}'>Next&gt;&gt;</a>"

    return pagination


def escape_html_content(content):
    """Escape HTML special characters in content."""
    return (content.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


def generate_html_page(item_id, title, patches, page, page_size=10):
    """Generate HTML pages for patches with pagination."""
    total = len(patches)
    page_num = (total + page_size - 1) // page_size  # Ceiling division

    def get_href(page_num_local):
        return f"{item_id}.html" if page_num_local == 1 else f"{item_id}_{page_num_local}.html"

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    page_patches = patches[start_idx:end_idx]

    pagination = create_pagination_html(page, page_num, get_href)

    # Create content
    content_parts = []
    for patch in page_patches:
        escaped_patch = escape_html_content(patch)
        content_parts.append(f"<pre>{escaped_patch}</pre>")
    content = "<hr>".join(content_parts)

    template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
    .pagination {{
        border-top: 1px solid #ddd;
        border-bottom: 1px solid #ddd;
        overflow-wrap: break-word;
    }}
    .pagination a, .pagination span {{
        margin: 0 4px;
    }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="pagination">
        {pagination}
    </div>
    <hr>
    {content}
    <div class="pagination">
        {pagination}
    </div>
</body>
</html>"""

    html_content = template.format(
        title=title,
        pagination=pagination,
        content=content
    )

    return html_content, get_href(page)


def generate_all_html_files(processed_result, result_detailed):
    """Generate all HTML files for the results."""
    for item in processed_result:
        domains = item["domains"]
        item_id = item["id"]
        title = f"Patches contributed by {item['name']}"

        # Collect all patches for this item
        patches = []
        for domain_name in domains:
            patches.extend(result_detailed[domain_name])

        # Generate paginated HTML files
        page_size = 10
        total_patches = len(patches)
        page_num = (total_patches + page_size - 1) // page_size

        for page in range(1, page_num + 1):
            html_content, filename = generate_html_page(item_id, title, patches, page, page_size)

            with open(f"detail/{filename}", "w", encoding="utf-8") as file:
                try:
                    file.write(html_content)
                except UnicodeEncodeError:
                    safe_content = html_content.encode("utf-8", "replace").decode("utf-8")
                    file.write(safe_content)


# Run the processing
result = process_results(result_patches, result_lines, result_authors, university_list)

with open("result.json", "w", encoding="utf-8") as f:
    f.write(json.dumps({"meta": meta, "data": result}, indent=2))
print("Result saved to result.json")

print("Save patches to detail dir...")
shutil.rmtree("detail", ignore_errors=True)
os.mkdir("detail")

generate_all_html_files(result, result_detail)
