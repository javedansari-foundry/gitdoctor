#!/usr/bin/env python3
"""
Helper script to find which projects contain specific commits.
Useful when you don't know which repos have your commits.
"""

import yaml
import requests
import urllib.parse
import sys

print("=" * 80)
print("Find Projects Containing Commits")
print("=" * 80)

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

base_url = config['gitlab']['base_url']
token = config['gitlab']['private_token']
verify_ssl = config['gitlab']['verify_ssl']

headers = {"PRIVATE-TOKEN": token}

# Load commits
with open('commits.txt', 'r') as f:
    commits = [line.strip() for line in f if line.strip()]

print(f"\nSearching for {len(commits)} commits:")
for commit in commits:
    print(f"  - {commit[:12]}...")

# Get all projects from your group (update 'your-group' to your actual group name)
print("\nFetching all projects from your-group...")
group_path = urllib.parse.quote("your-group", safe="")
url = f"{base_url}/api/v4/groups/{group_path}/projects"

params = {
    "include_subgroups": "true",
    "per_page": 100,
    "archived": "false"
}

all_projects = []
page = 1

while True:
    params["page"] = page
    try:
        response = requests.get(url, headers=headers, params=params, verify=verify_ssl, timeout=30)
        if response.status_code != 200:
            print(f"Error fetching projects: {response.status_code}")
            sys.exit(1)
        
        projects = response.json()
        if not projects:
            break
        
        all_projects.extend(projects)
        page += 1
        
        if 'x-next-page' not in response.headers or not response.headers['x-next-page']:
            break
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

print(f"Found {len(all_projects)} projects to search")
print("\nSearching for commits (this will take a few minutes)...")
print("-" * 80)

# Search for each commit in each project
found_commits = {}

for i, commit_sha in enumerate(commits, 1):
    print(f"\n[{i}/{len(commits)}] Searching for commit {commit_sha[:12]}...")
    found_in = []
    
    for proj in all_projects:
        proj_id = proj['id']
        proj_path = proj['path_with_namespace']
        
        # Try to get commit
        commit_url = f"{base_url}/api/v4/projects/{proj_id}/repository/commits/{commit_sha}"
        try:
            resp = requests.get(commit_url, headers=headers, verify=verify_ssl, timeout=10)
            if resp.status_code == 200:
                commit_data = resp.json()
                found_in.append({
                    'path': proj_path,
                    'id': proj_id,
                    'title': commit_data.get('title', 'N/A'),
                    'author': commit_data.get('author_name', 'N/A'),
                    'date': commit_data.get('created_at', 'N/A')
                })
                print(f"  ✅ Found in: {proj_path}")
        except:
            pass
    
    found_commits[commit_sha] = found_in
    
    if not found_in:
        print(f"  ❌ Not found in any project")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for commit_sha, projects in found_commits.items():
    print(f"\nCommit: {commit_sha[:12]}...")
    if projects:
        print(f"  Found in {len(projects)} project(s):")
        for proj in projects:
            print(f"    - {proj['path']}")
            print(f"      Author: {proj['author']}")
            print(f"      Title: {proj['title']}")
    else:
        print(f"  ❌ NOT FOUND in any project in your-group")

# Generate suggested config
print("\n" + "=" * 80)
print("SUGGESTED CONFIG FOR config-explicit.yaml")
print("=" * 80)

all_project_paths = set()
for commit_sha, projects in found_commits.items():
    for proj in projects:
        all_project_paths.add(proj['path'])

if all_project_paths:
    print("\nprojects:")
    print("  by_path:")
    for path in sorted(all_project_paths):
        print(f'    - "{path}"')
    
    print("\n" + "=" * 80)
    print(f"Add these {len(all_project_paths)} projects to config-explicit.yaml")
    print("=" * 80)
else:
    print("\n❌ No projects found containing these commits!")
    print("\nPossible reasons:")
    print("  1. Commits are in repos outside your-group")
    print("  2. Commits don't exist in this GitLab instance")
    print("  3. You don't have access to the repos containing these commits")
    print("\nTry:")
    print("  - Verify commits exist in GitLab web UI")
    print("  - Check if commits are in different groups")
    print("  - Confirm you have access to the repositories")

