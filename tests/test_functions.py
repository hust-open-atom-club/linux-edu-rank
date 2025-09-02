"""Unit tests for functions in main.py."""
from main import (
    get_university,
    transform_author_data,
    create_domain_result,
    merge_university_results,
    add_rankings,
    create_pagination_html,
    escape_html_content,
    generate_html_page,
)


def test_get_university():
    uni_list = [
        {"name": "Foo Univ", "domains": ["foo.edu", "cs.foo.edu"]},
        {"name": "Bar Univ", "domains": ["bar.ac.cn"]},
    ]
    # exact domain match
    assert get_university("cs.foo.edu", uni_list)["name"] == "Foo Univ"
    # parent domain match
    assert get_university("mail.foo.edu", uni_list)["name"] == "Foo Univ"
    # unknown domain
    assert get_university("unknown.org", uni_list) is None


def test_transform_author_data():
    authors_map = {
        "foo.edu": {
            "a@foo.edu": ["NameA", 2, []],
            "b@foo.edu": ["NameB", 5, []],
            "c@foo.edu": ["NameC", 3, []],
        }
    }
    authors = transform_author_data(authors_map, "foo.edu")
    assert [a["email"] for a in authors] == ["b@foo.edu", "c@foo.edu", "a@foo.edu"]
    # sort by count desc
    assert authors[0]["name"] == "NameB" and authors[0]["count"] == 5

def test_create_domain_result():
    authors_map = {"foo.edu": {"x@foo.edu": ["NameX", 1, ["commit1"]]}}
    university_info = {"name": "Foo Univ", "domains": ["foo.edu"]}

    known = create_domain_result(
        domain_name="foo.edu",
        patches_count=3,
        lines_count=10,
        university=university_info,
        authors_map=authors_map,
    )
    assert known["name"] == "Foo Univ"
    assert known["domains"] == ["foo.edu"]
    assert known["count"] == 3 and known["lines"] == 10
    assert known["university"]["name"] == "Foo Univ"

    unknown = create_domain_result(
        domain_name="unknown.org",
        patches_count=2,
        lines_count=5,
        university=None,
        authors_map={},
    )
    assert unknown["name"] == "Unknown (unknown.org)"
    assert unknown["university"] is None


def test_merge_university_results():
    items = [
        {
            "name": "Foo Univ",
            "domains": ["foo.edu"],
            "university": {},
            "count": 3,
            "lines": 10,
            "authors": [{"count": 3}],
        },
        {
            "name": "Foo Univ",
            "domains": ["cs.foo.edu"],
            "university": {},
            "count": 2,
            "lines": 5,
            "authors": [{"count": 2}],
        },
        {
            "name": "Bar Univ",
            "domains": ["bar.ac.cn"],
            "university": {},
            "count": 3,
            "lines": 9,
            "authors": [{"count": 3}],
        },
    ]
    merged = merge_university_results(items)

    # get Foo Univ
    matches = [x for x in merged if x["name"] == "Foo Univ"]
    assert len(matches) == 1
    foo = matches[0]
    assert set(foo["domains"]) == {"foo.edu", "cs.foo.edu"}
    assert foo["count"] == 5 and foo["lines"] == 15
    assert len(foo["authors"]) == 2


def test_add_rankings():
    # Input must already be sorted desc by (count, lines)
    sorted_results = [
        {
            "name": "A",
            "domains": ["a"],
            "university": {},
            "count": 5,
            "lines": 20,
            "authors": [],
        },
        {
            "name": "B",
            "domains": ["b"],
            "university": {},
            "count": 5,
            "lines": 10,
            "authors": [{"count": 1}],
        },
        {
            "name": "C",
            "domains": ["c"],
            "university": {},
            "count": 3,
            "lines": 100,
            "authors": [{"count": 2}, {"count": 1}],
        },
    ]
    ranked = add_rankings(sorted_results)

    # IDs are sequential in original order
    assert [r["id"] for r in ranked] == [1, 2, 3]
    # First two share the same rank due to same count
    assert ranked[0]["rank"] == ranked[1]["rank"]
    assert ranked[2]["rank"] > ranked[1]["rank"]
    # contributor_count matches authors length
    assert ranked[1]["contributor_count"] == 1
    assert ranked[2]["contributor_count"] == 2


def test_create_pagination_html():
    def get_href(i: int) -> str:
        return "index.html" if i == 1 else f"index_{i}.html"

    html = create_pagination_html(page=1, page_num=3, get_href_func=get_href)
    # First page: no Prev, has Next
    assert "&lt;&lt;Prev" not in html
    assert "Next&gt;&gt;" in html
    assert "index_2.html" in html and "[1]" in html

    html2 = create_pagination_html(page=2, page_num=3, get_href_func=get_href)
    assert "&lt;&lt;Prev" in html2 and "Next&gt;&gt;" in html2
    assert "index.html" in html2 and "[2]" in html2
    assert "index_3.html" in html2


def test_escape_html_content():
    assert escape_html_content("<a&b>") == "&lt;a&amp;b&gt;"


def test_generate_html_page():
    # Page 1: should contain escaped first patch and link to page 2
    html1, fname1 = generate_html_page(
        item_id=7,
        title="T",
        patches=["1<2&3", "second"],
        page=1,
        page_size=1,
    )
    assert fname1 == "7.html"
    assert "<pre>1&lt;2&amp;3</pre>" in html1
    assert "<a href='7_2.html'>2</a>" in html1
    assert "[1]" in html1

    # Page 2: filename suffix, has Prev, shows second patch
    html2, fname2 = generate_html_page(
        item_id=7,
        title="T",
        patches=["1<2&3", "second"],
        page=2,
        page_size=1,
    )
    assert fname2 == "7_2.html"
    assert "<pre>second</pre>" in html2
    assert "<a href='7.html'>&lt;&lt;Prev</a>" in html2
    assert "Next&gt;&gt;" not in html2
    assert "[2]" in html2
