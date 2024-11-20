def is_university_domain(test_domain, uni_list):
    '''
    Verify if the provided domain is a university domain in the uni_list
    '''
    for university in uni_list:
        if test_domain in university["domains"]:
            return True

    for university in uni_list:
        for raw_domain in university["domains"]:
            # domain: sc.edu
            # raw_domain: osc.edu
            if test_domain.endswith(raw_domain):
                return True
    return False


def get_university(domain,university_list):
    for university in university_list:
        if domain in university["domains"]:
            return university

    for university in university_list:
        for raw_domain in university["domains"]:
            if domain.endswith(raw_domain) or raw_domain.endswith(domain):
                return university
    return None


def result_authors_transform(result_authors,item):
    return list(
        map(
            lambda x: {
                "email": x[0],
                "name": x[1][0],
                "count": x[1][1],
                "commits": x[1][2],
            },
            result_authors.get(item["domain"], {}).items(),
        )
    )


def generate_html(id, title, patches):
    PAGE_SIZE = 10
    total = len(patches)
    page_num = total // PAGE_SIZE + 1

    def get_href(page):
        return f"{id}.html" if page == 1 else f"{id}_{page}.html"

    def get_pagination(page):
        str = ""
        if page > 1:
            str += "<a href='{}'>&lt;&lt;Prev</a>".format(get_href(page - 1))

        for i in range(1, page_num + 1):
            if i == page:
                str += f"<span>[{i}]</span>"
            else:
                str += "<a href='{}'>{}</a>".format(get_href(i), i)

        if page < page_num:
            str += "<a href='{}'>Next&gt;&gt;</a>".format(get_href(page + 1))
        return str

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
    <div>
</body>
"""
    for i in range(1, page_num + 1):
        with open(f"detail/{get_href(i)}", "w") as f:
            f.write(
                template.format(
                    title=title,
                    pagination=get_pagination(i),
                    content="<hr>".join(
                        map(
                            lambda x: "<pre>{}</pre>".format(
                                x.replace("&", "&amp;")
                                .replace("<", "&lt;")
                                .replace(">", "&gt;")
                            ),
                            patches[(i - 1) * PAGE_SIZE : i * PAGE_SIZE],
                        )
                    ),
                )
                .encode("utf-8", "replace")
                .decode("utf-8")
            )