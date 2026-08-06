#!/usr/bin/env python3
import requests
import warnings
warnings.filterwarnings('ignore')

GITLAB_URL = "http://blrgitlab.comviva.com"
TOKEN = "Rwd98qeB9LyUChkyzs6i"
headers = {"PRIVATE-TOKEN": TOKEN}

# Check key project
project_id = 128  # jigsaw

branches_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/branches"
response = requests.get(branches_url, headers=headers, params={"per_page": "50"}, verify=False, timeout=10)

if response.status_code == 200:
    branches = response.json()
    print("🌿 ACTIVE BRANCHES in dfs-core/platform/jigsaw:\n")
    print("=" * 80)
    
    # Look for main branches
    main_branches = []
    dev_branches = []
    v11_branches = []
    
    for branch in branches:
        name = branch["name"]
        last_commit = branch["commit"]["created_at"]
        
        if any(x in name.lower() for x in ["main", "master", "develop"]):
            main_branches.append((name, last_commit))
        elif "v11" in name.lower() or "_11." in name:
            v11_branches.append((name, last_commit))
        elif "dev" in name.lower() or "release" in name.lower():
            dev_branches.append((name, last_commit))
    
    if main_branches:
        print("\n📍 Main branches:")
        for name, date in main_branches[:5]:
            print(f"  - {name} (last commit: {date})")
    
    if v11_branches:
        print("\n📍 v11-related branches:")
        for name, date in v11_branches[:5]:
            print(f"  - {name} (last commit: {date})")
    
    if dev_branches:
        print("\n📍 Development branches:")
        for name, date in dev_branches[:5]:
            print(f"  - {name} (last commit: {date})")
    
    print("\n" + "=" * 80)
    print(f"\nTotal branches: {len(branches)}")
    
    print("\n💡 To check recent commits on a branch, use:")
    print("   gitdoctor delta --base <branch>~50 --target <branch> --after 2026-01-18")
