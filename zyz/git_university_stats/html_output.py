import os
import json
import shutil

def generate_html(id, title, patches):
    PAGE_SIZE = 10
    total = len(patches)
    page_num = total // PAGE_SIZE + 1

    def get_href(page):
        return f"{id}.html" if page == 1 else f"{id}_{page}.html"

    def get_pagination(page):
        nav = ""
        if page > 1:
            nav += f"<a href='{get_href(page-1)}'>&lt;&lt;Prev</a>"
        for i in range(1, page_num + 1):
            nav += f"<span>[{i}]</span>" if i == page else f"<a href='{get_href(i)}'>{i}</a>"
        if page < page_num:
            nav += f"<a href='{get_href(page+1)}'>Next&gt;&gt;</a>"
        return nav

    template = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title>
<style>.pagination{{border-top:1px solid #ddd;border-bottom:1px solid #ddd;}}.pagination a,.pagination span{{margin:0 4px;}}</style></head>
<body>
<h1>{title}</h1>
<div class="pagination">{pagination}</div><hr>
{content}
<div class="pagination">{pagination}</div>
</body></html>"""

    for i in range(1, page_num + 1):
        page_patches = patches[(i - 1) * PAGE_SIZE : i * PAGE_SIZE]
        safe_html = "<hr>".join(
            f"<pre>{x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</pre>"
            for x in page_patches
        )
        with open(f"detail/{get_href(i)}", "w") as f:
            f.write(template.format(
                title=title,
                pagination=get_pagination(i),
                content=safe_html,
            ))

def save_results(meta, result, details):
    with open("result.json", "w") as f:
        f.write(json.dumps({"meta": meta, "data": result}, indent=2))
    print("Result saved to result.json")

    shutil.rmtree("detail", ignore_errors=True)
    os.mkdir("detail")

    for item in result:
        patches = []
        for domain in item["domains"]:
            patches.extend(details[domain])
        generate_html(item["id"], "Patches contributed by " + item["name"], patches)

    print("HTML patches saved to 'detail/'.")
