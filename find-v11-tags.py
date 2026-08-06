#!/usr/bin/env python3
import requests
import warnings
warnings.filterwarnings('ignore')

GITLAB_URL = "http://blrgitlab.comviva.com"
TOKEN = "Rwd98qeB9LyUChkyzs6i"
GROUP_ID = 1  

headers = {"PRIVATE-TOKEN": TOKEN}

print("Searching for v11 tags in dfs-core projects...")
print("=" * 80)

url = f"{GITLAB_URL}/api/v4/groups/{GROUP_ID}/projects"
params = {"include_subgroups": "true", "per_page": "50"}

all_v11_tags = set()

for page in range(1, 6):  # Check first 250 projects
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
            
            # Get tags for this project
            tags_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tags"
            tags_response = requests.get(tags_url, headers=headers, params={"per_page": "100"}, verify=False, timeout=10)
            
            if tags_response.status_code == 200:
                tags = tags_response.json()
                for tag in tags:
                    tag_name = tag["name"]
                    if "v11" in tag_name.lower() or "_11." in tag_name:
                        all_v11_tags.add(tag_name)
                        if len(all_v11_tags) <= 20:  # Show first 20
                            print(f"  {tag_name} (in {project_path})")
    except:
        pass

print("=" * 80)
print(f"\nFound {len(all_v11_tags)} unique v11-related tags")
print("\nUnique v11 tags found:")
for tag in sorted(list(all_v11_tags))[:30]:
    print(f"  - {tag}")
