from datetime import datetime

def generate_meta(repo_name, branch, repo):
    return {
        "update": datetime.now().isoformat(),
        "repo": repo_name,
        "branch": branch,
        "commit": repo.commit(branch).hexsha,
    }
