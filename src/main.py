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

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "zh-CN", "zh-TW", "ja", "ko")
MESSAGES = {
    "en": {
        "back_to_rankings": "Back to rankings",
        "patches_contributed_by": "Patches contributed by {name}",
        "prev": "Prev",
        "next": "Next",
    },
    "zh-CN": {
        "back_to_rankings": "返回排行榜",
        "patches_contributed_by": "{name} 贡献的补丁",
        "prev": "上一页",
        "next": "下一页",
    },
    "zh-TW": {
        "back_to_rankings": "返回排行榜",
        "patches_contributed_by": "{name} 貢獻的補丁",
        "prev": "上一頁",
        "next": "下一頁",
    },
    "ja": {
        "back_to_rankings": "ランキングに戻る",
        "patches_contributed_by": "{name} によるパッチ",
        "prev": "前へ",
        "next": "次へ",
    },
    "ko": {
        "back_to_rankings": "순위로 돌아가기",
        "patches_contributed_by": "{name}의 패치",
        "prev": "이전",
        "next": "다음",
    },
}


def message(locale, key):
    """Return a localized UI message."""
    messages = MESSAGES.get(locale, MESSAGES[DEFAULT_LOCALE])
    return messages.get(key, MESSAGES[DEFAULT_LOCALE][key])


def detail_dir(locale):
    """Return the detail output directory for a locale."""
    return os.path.join("detail", locale)


def main():
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
        "commit": repo.commit(branch).hexsha[0:12],
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

    # Run the processing
    result = process_results(result_patches, result_lines, result_authors, university_list)

    write_result_files({"meta": meta, "data": result})

    print("Save patches to detail dir...")
    shutil.rmtree("detail", ignore_errors=True)

    generate_all_html_files(result, result_detail)



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


def write_result_files(result_payload):
    """Write result data as JSON and as a local-file-friendly JS payload."""
    result_json = json.dumps(result_payload, ensure_ascii=False, indent=2)
    with open("result.json", "w", encoding="utf-8") as file:
        file.write(result_json)

    with open("result.js", "w", encoding="utf-8") as file:
        file.write(f"window.__LINUX_EDU_RANK_RESULT__ = {result_json};\n")

    print("Result saved to result.json and result.js")


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


def create_pagination_html(page, page_num, get_href_func, locale=DEFAULT_LOCALE):
    """Create pagination HTML for a given page."""
    pagination = ""

    if page > 1:
        prev_text = message(locale, "prev")
        pagination += (
            f"<a class='page-btn' href='{get_href_func(page - 1)}'>&lt;&lt;{prev_text}</a>"
        )

    for i in range(1, page_num + 1):
        if i == page:
            pagination += f"<span class='page-btn current'>[{i}]</span>"
        else:
            pagination += f"<a class='page-btn' href='{get_href_func(i)}'>{i}</a>"

    if page < page_num:
        next_text = message(locale, "next")
        pagination += (
            f"<a class='page-btn' href='{get_href_func(page + 1)}'>{next_text}&gt;&gt;</a>"
        )

    return pagination


def escape_html_content(content):
    """Escape HTML special characters in content."""
    return (content.replace("&", "&amp;")
                  .replace('"', "&quot;")
                  .replace("'", "&#x27;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


def generate_html_page(item_id, title, patches, page, page_size=10, locale=DEFAULT_LOCALE):
    """Generate HTML pages for patches with pagination."""
    total = len(patches)
    page_num = (total + page_size - 1) // page_size  # Ceiling division

    def get_href(page_num_local):
        return f"{item_id}.html" if page_num_local == 1 else f"{item_id}_{page_num_local}.html"

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    page_patches = patches[start_idx:end_idx]

    pagination = create_pagination_html(page, page_num, get_href, locale)

    # Create content
    content_parts = []
    for patch in page_patches:
        escaped_patch = escape_html_content(patch)
        content_parts.append(
            f'<div class="patch-card"><pre>{escaped_patch}</pre></div>'
        )
    content = "\n".join(content_parts)

    template = """<!DOCTYPE html>
<html lang="{locale}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #f0f2f5;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                     'Helvetica Neue', Arial, sans-serif;
        color: #262626;
    }}
    .detail-header {{
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #fff;
        padding: 36px 32px 32px;
        text-align: center;
    }}
    .detail-header h1 {{
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    .back-link {{
        display: inline-block;
        color: rgba(255,255,255,0.7);
        text-decoration: none;
        font-size: 14px;
        transition: color 0.2s;
    }}
    .back-link:hover {{ color: #fff; }}
    .container {{
        max-width: 960px;
        margin: -16px auto 40px;
        padding: 0 20px;
        position: relative;
    }}
    .pagination {{
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        padding: 12px 16px;
        margin-bottom: 16px;
        overflow-wrap: break-word;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px;
    }}
    .page-btn {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 14px;
        color: #595959;
        background: #f5f5f5;
        border: 1px solid #f0f0f0;
        transition: all 0.2s;
    }}
    a.page-btn:hover {{
        color: #1677ff;
        border-color: #1677ff;
        background: #e6f4ff;
    }}
    .page-btn.current {{
        background: #1677ff;
        color: #fff;
        border-color: #1677ff;
        font-weight: 600;
    }}
    .patch-card {{
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 16px;
        overflow: hidden;
    }}
    .patch-card pre {{
        padding: 20px;
        margin: 0;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-size: 13px;
        line-height: 1.6;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        color: #333;
    }}
    @media (max-width: 576px) {{
        .detail-header {{ padding: 24px 16px 20px; }}
        .detail-header h1 {{ font-size: 18px; }}
        .container {{ padding: 0 12px; }}
        .patch-card pre {{ padding: 12px; font-size: 12px; }}
    }}
    </style>
</head>
<body>
    <div class="detail-header">
        <a class="back-link" href="../../index.html?lang={locale}">&larr; {back_to_rankings}</a>
        <h1>{title}</h1>
    </div>
    <div class="container">
        <div class="pagination">
            {pagination}
        </div>
        {content}
        <div class="pagination">
            {pagination}
        </div>
    </div>
</body>
</html>"""

    html_content = template.format(
        locale=locale,
        title=escape_html_content(title),
        pagination=pagination,
        content=content,
        back_to_rankings=message(locale, "back_to_rankings"),
    )

    return html_content, get_href(page)


def generate_all_html_files(processed_result, result_detailed, locales=SUPPORTED_LOCALES):
    """Generate all HTML files for the results."""
    for locale in locales:
        os.makedirs(detail_dir(locale), exist_ok=True)

    for item in processed_result:
        domains = item["domains"]
        item_id = item["id"]

        # Collect all patches for this item
        patches = []
        for domain_name in domains:
            patches.extend(result_detailed[domain_name])

        # Generate paginated HTML files
        page_size = 10
        total_patches = len(patches)
        page_num = (total_patches + page_size - 1) // page_size

        for locale in locales:
            title = message(locale, "patches_contributed_by").format(name=item["name"])
            for page in range(1, page_num + 1):
                html_content, filename = generate_html_page(
                    item_id, title, patches, page, page_size, locale
                )

                output_path = os.path.join(detail_dir(locale), filename)
                with open(output_path, "w", encoding="utf-8") as file:
                    try:
                        file.write(html_content)
                    except UnicodeEncodeError:
                        safe_content = html_content.encode("utf-8", "replace").decode("utf-8")
                        file.write(safe_content)


if __name__ == "__main__":
    main()
