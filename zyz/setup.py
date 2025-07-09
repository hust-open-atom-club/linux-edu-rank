from setuptools import setup, find_packages

setup(
    name="git-university-stats",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "GitPython",
        "tqdm",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "git-uni-stats = git_university_stats.main:main",
        ],
    },
    author="Your Name",
    description="Analyze university contributions in Git repositories",
    python_requires=">=3.7",
)
