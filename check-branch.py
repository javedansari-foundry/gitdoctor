#!/usr/bin/env python3
import requests
import warnings
warnings.filterwarnings('ignore')

GITLAB_URL = "http://blrgitlab.comviva.com"
TOKEN = "Rwd98qeB9LyUChkyzs6i"
REF_NAME = "MobiquityPay_v11.1.0_20251229_PVG.B1"

headers = {"PRIVATE-TOKEN": TOKEN}

# Check a few key projects
projects = [128, 127, 1880, 3051]  # jigsaw, shulka, liquibase, multinode

print(f"Checking if '{REF_NAME}' is a TAG or BRANCH:\n")
print("=" * 80)

for project_id in projects:
    # Get project name
    proj_url = f"{GITLAB_URL}/api/v4/projects/{project_id}"
    proj_resp = requests.get(proj_url, headers=headers, verify=False, timeout=10)
    if proj_resp.status_code == 200:
        project_name = proj_resp.json()["path_with_namespace"]
        
        # Check if it's a tag
        tag_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tags/{REF_NAME}"
        tag_resp = requests.get(tag_url, headers=headers, verify=False, timeout=10)
        
        # Check if it's a branch
        branch_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/branches/{REF_NAME}"
        branch_resp = requests.get(branch_url, headers=headers, verify=False, timeout=10)
        
        if tag_resp.status_code == 200:
            tag_data = tag_resp.json()
            tag_date = tag_data.get("commit", {}).get("created_at", "N/A")
            print(f"{project_name}:")
            print(f"  ✓ TAG found (created: {tag_date})")
        
        if branch_resp.status_code == 200:
            branch_data = branch_resp.json()
            last_commit_date = branch_data.get("commit", {}).get("created_at", "N/A")
            print(f"  ✓ BRANCH found (last commit: {last_commit_date})")
        
        if tag_resp.status_code != 200 and branch_resp.status_code != 200:
            print(f"{project_name}: ✗ Not found")

print("\n" + "=" * 80)
print("\n💡 EXPLANATION:")
print("- TAG = Fixed snapshot from December 29, 2025")
print("- BRANCH = Active development line that can have recent commits")
