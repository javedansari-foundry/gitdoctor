#!/usr/bin/env python3
import requests
import sys

# Config
GITLAB_URL = "http://blrgitlab.comviva.com"
TOKEN = "Rwd98qeB9LyUChkyzs6i"
BRANCH_NAME = "PE_MobiquityPay_v11.0.0_20250908_PVG.B1"
GROUP_ID = 1  # dfs-core group ID

headers = {"PRIVATE-TOKEN": TOKEN}

# Get all projects in dfs-core group (with subgroups)
print(f"Searching for branch '{BRANCH_NAME}' in dfs-core projects...")
print("=" * 60)

url = f"{GITLAB_URL}/api/v4/groups/{GROUP_ID}/projects"
params = {"include_subgroups": "true", "per_page": "100"}

page = 1
found_count = 0

while True:
    params["page"] = page
    response = requests.get(url, headers=headers, params=params, verify=False)
    if response.status_code != 200:
        break
    
    projects = response.json()
    if not projects:
        break
    
    for project in projects:
        project_id = project["id"]
        project_path = project["path_with_namespace"]
        
        # Check if branch exists
        branch_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/branches/{BRANCH_NAME}"
        branch_response = requests.get(branch_url, headers=headers, verify=False)
        
        if branch_response.status_code == 200:
            found_count += 1
            print(f"✓ FOUND in: {project_path} (ID: {project_id})")
    
    page += 1
    if page > 10:  # Safety limit
        break

print("=" * 60)
print(f"Total repositories with this branch: {found_count}")
