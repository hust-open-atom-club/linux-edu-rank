from tqdm import tqdm
from git_university_stats.university_list import is_university_domain

def collect_commit_data(repo, branch, uni_list):
    commits = list(repo.iter_commits(branch))
    print("Total commits:", len(commits))

    patches = {}
    lines = {}
    details = {}
    authors = {}

    for commit in tqdm(commits):
        email = commit.author.email
        if not email:
            continue
        domain = email.split("@")[-1]
        if not is_university_domain(domain, uni_list):
            continue

        patches[domain] = patches.get(domain, 0) + 1
        lines[domain] = lines.get(domain, 0) + commit.stats.total["lines"]
        details.setdefault(domain, []).append(repo.git.show(commit.hexsha))

        authors.setdefault(domain, {})
        if email not in authors[domain]:
            authors[domain][email] = [commit.author.name, 0, []]

        authors[domain][email][1] += 1
        authors[domain][email][2].append({
            "commit": commit.hexsha,
            "summary": commit.summary,
            "date": commit.authored_datetime.isoformat(),
            "files": commit.stats.total["files"],
            "lines": "-{}/+{}".format(
                commit.stats.total["deletions"], commit.stats.total["insertions"]
            ),
        })

    return patches, lines, details, authors
