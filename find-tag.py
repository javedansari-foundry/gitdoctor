#!/usr/bin/env python3
import requests
import sys
import warnings
warnings.filterwarnings('ignore')

# Config
GITLAB_URL = "http://blrgitlab.comviva.com"
TOKEN = "Rwd98qeB9LyUChkyzs6i"
TAG_NAME = "PE_MobiquityPay_v11.0.0_20250908_PVG.B1"
GROUP_ID = 1  # dfs-core group ID

headers = {"PRIVATE-TOKEN": TOKEN}

# Get all projects in dfs-core group (with subgroups)
print(f"Searching for TAG '{TAG_NAME}' in dfs-core projects...")
print("=" * 80)

url = f"{GITLAB_URL}/api/v4/groups/{GROUP_ID}/projects"
params = {"include_subgroups": "true", "per_page": "100"}

page = 1
found_repos = []

while True:
    params["page"] = page
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        if response.status_code != 200:
            break
        
        projects = response.json()
        if not projects:
            break
        
        for project in projects:
            project_id = project["id"]
            project_path = project["path_with_namespace"]
            
            # Check if tag exists
            tag_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tags/{TAG_NAME}"
            tag_response = requests.get(tag_url, headers=headers, verify=False, timeout=10)
            
            if tag_response.status_code == 200:
                found_repos.append(project_path)
                print(f"✓ FOUND TAG in: {project_path} (ID: {project_id})")
        
        page += 1
        if page > 15:  # Search up to 1500 projects
            break
    except Exception as e:
        print(f"Error: {e}")
        break

print("=" * 80)
print(f"\nTotal repositories with this TAG: {len(found_repos)}")
if found_repos:
    print("\nRepositories found:")
    for repo in found_repos:
        print(f"  - {repo}")
