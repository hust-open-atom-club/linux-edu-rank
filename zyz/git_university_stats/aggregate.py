from git_university_stats.university_list import get_university
from functools import reduce

def aggregate_result(patches, lines, details, authors, uni_list):
    def transform_authors(domain):
        return sorted([
            {
                "email": k,
                "name": v[0],
                "count": v[1],
                "commits": v[2],
            }
            for k, v in authors.get(domain, {}).items()
        ], key=lambda x: x["count"], reverse=True)

    temp = {}
    for domain, count in patches.items():
        university = get_university(domain, uni_list)
        author_list = transform_authors(domain)

        if university is None:
            temp[domain] = {
                "name": f"Unknown ({domain})",
                "domains": [domain],
                "university": None,
                "count": count,
                "lines": lines[domain],
                "authors": author_list,
            }
            continue

        name = university["name"]
        if name not in temp:
            temp[name] = {
                "name": name,
                "domains": [],
                "university": university,
                "count": 0,
                "lines": 0,
                "authors": [],
            }

        if domain not in temp[name]["domains"]:
            temp[name]["domains"].append(domain)
            temp[name]["authors"].extend(author_list)

        temp[name]["count"] += count
        temp[name]["lines"] += lines[domain]
        temp[name]["authors"].sort(key=lambda x: x["count"], reverse=True)

    result = list(temp.values())
    result.sort(key=lambda x: x["count"], reverse=True)
    result = list(map(lambda x: x[1] | {"id": x[0] + 1}, enumerate(result)))

    result = reduce(
        lambda s, i: s
        + [i | {
            "rank": (
                i["id"] if len(s) == 0 or i["count"] != s[-1]["count"] else s[-1]["rank"]
            )
        }],
        result,
        [],
    )

    return result
