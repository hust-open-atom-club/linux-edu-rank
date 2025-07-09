import requests

def load_university_list():
    print("Getting university list...")
    return requests.get(
        "https://github.com/Hipo/university-domains-list/raw/master/world_universities_and_domains.json"
    ).json()

def _find_university_by_domain(domain, uni_list):
    for university in uni_list:
        if domain in university["domains"]:
            return university
    for university in uni_list:
        for raw_domain in university["domains"]:
            if domain.endswith(raw_domain) or raw_domain.endswith(domain):
                return university
    return None

def is_university_domain(domain, uni_list):
    return _find_university_by_domain(domain, uni_list) is not None

def get_university(domain, uni_list):
    return _find_university_by_domain(domain, uni_list)
