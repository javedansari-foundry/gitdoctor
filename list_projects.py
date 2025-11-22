#!/usr/bin/env python3
"""
Helper script to list all projects in your GitLab group.
Use this to identify which projects to add to explicit mode.
"""

import yaml
import requests
import urllib.parse

print("=" * 80)
print("GitLab Projects Lister")
print("=" * 80)

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

base_url = config['gitlab']['base_url']
token = config['gitlab']['private_token']
verify_ssl = config['gitlab']['verify_ssl']

headers = {"PRIVATE-TOKEN": token}

# Get projects from your-group (update this to your actual group name)
group_path = urllib.parse.quote("your-group", safe="")
url = f"{base_url}/api/v4/groups/{group_path}/projects"

print("\nFetching projects from your-group...")
print("(This may take a moment...)\n")

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
            print(f"Error: {response.status_code} - {response.text}")
            break
        
        projects = response.json()
        if not projects:
            break
        
        all_projects.extend(projects)
        page += 1
        
        # Check if there are more pages
        if 'x-next-page' not in response.headers or not response.headers['x-next-page']:
            break
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"Found {len(all_projects)} projects in your-group\n")
print("=" * 80)

# Group by subgroup for easier reading
from collections import defaultdict
by_group = defaultdict(list)

for proj in all_projects:
    path = proj['path_with_namespace']
    # Get the immediate parent group
    parts = path.split('/')
    if len(parts) > 1:
        parent = '/'.join(parts[:-1])
    else:
        parent = 'root'
    
    by_group[parent].append({
        'id': proj['id'],
        'name': proj['name'],
        'path': path,
        'last_activity': proj.get('last_activity_at', 'unknown')
    })

# Print organized by group
print("\nProjects organized by group:\n")
for group in sorted(by_group.keys()):
    print(f"\n📁 {group}/")
    print("-" * 80)
    for proj in sorted(by_group[group], key=lambda x: x['name']):
        print(f"  ID: {proj['id']:6d}  |  {proj['path']}")

# Save to file for reference
print("\n" + "=" * 80)
print("Saving full list to projects_list.txt...")

with open('projects_list.txt', 'w') as f:
    f.write("All Projects in Your Group\n")
    f.write("=" * 80 + "\n\n")
    f.write("Copy these paths to config.yaml under projects.by_path for explicit mode\n\n")
    
    for group in sorted(by_group.keys()):
        f.write(f"\n{group}/\n")
        f.write("-" * 80 + "\n")
        for proj in sorted(by_group[group], key=lambda x: x['name']):
            f.write(f"{proj['path']}\n")

print("✅ Saved to: projects_list.txt")

# Print YAML template for common projects
print("\n" + "=" * 80)
print("SUGGESTED CONFIG FOR EXPLICIT MODE")
print("=" * 80)
print("\nCopy this to your config.yaml:\n")
print("""
scan:
  mode: "explicit"

projects:
  by_path:""")

# Show top 10 most recently active projects
sorted_projects = sorted(all_projects, key=lambda x: x.get('last_activity_at', ''), reverse=True)
for proj in sorted_projects[:10]:
    print(f'    - "{proj["path_with_namespace"]}"  # {proj["name"]}')

print("\n# Add more projects as needed...")

print("\n" + "=" * 80)
print("TIP: Check projects_list.txt for the complete list!")
print("=" * 80)

