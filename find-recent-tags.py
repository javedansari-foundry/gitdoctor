#!/usr/bin/env python3
import requests
import warnings
warnings.filterwarnings('ignore')

GITLAB_URL = "http://blrgitlab.comviva.com"
TOKEN = "Rwd98qeB9LyUChkyzs6i"

headers = {"PRIVATE-TOKEN": TOKEN}

# Check a few known projects from your config
projects_to_check = [
    ("dfs-core/platform/jigsaw", 128),
    ("dfs-core/product-domains/transaction/shulka", 127),
    ("dfs-core/platform/liquibase-common-schema", 1880),
    ("dfs-core/devops/multinode_mobiquity_deployment", 3051)
]

print("Recent tags in your configured repositories:")
print("=" * 80)

all_tags = set()

for project_path, project_id in projects_to_check:
    tags_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tags"
    try:
        response = requests.get(tags_url, headers=headers, params={"per_page": "20"}, verify=False, timeout=10)
        
        if response.status_code == 200:
            tags = response.json()
            print(f"\n{project_path}:")
            if tags:
                for tag in tags[:10]:  # Show first 10
                    tag_name = tag["name"]
                    all_tags.add(tag_name)
                    print(f"  - {tag_name}")
            else:
                print("  (no tags)")
    except:
        print(f"  (error accessing)")

print("\n" + "=" * 80)
print(f"\nTotal unique tags found: {len(all_tags)}")

# Show MobiquityPay tags
mobiquity_tags = sorted([t for t in all_tags if "Mobiquity" in t or "mobiquity" in t])
if mobiquity_tags:
    print("\nMobiquityPay tags found:")
    for tag in mobiquity_tags[:20]:
        print(f"  - {tag}")
