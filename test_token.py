#!/usr/bin/env python3
"""
Quick script to test your GitLab token and diagnose issues.
"""

import requests
import yaml

print("=" * 60)
print("GitLab Token Test Utility")
print("=" * 60)

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

base_url = config['gitlab']['base_url']
token = config['gitlab']['private_token']
verify_ssl = config['gitlab']['verify_ssl']

print(f"\nConfiguration:")
print(f"  GitLab URL: {base_url}")
print(f"  Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
print(f"  Verify SSL: {verify_ssl}")
print(f"  Token length: {len(token)} characters")

# Test 1: Version endpoint
print("\n" + "=" * 60)
print("Test 1: Testing /api/v4/version endpoint")
print("=" * 60)

url = f"{base_url}/api/v4/version"
headers = {"PRIVATE-TOKEN": token}

try:
    response = requests.get(url, headers=headers, verify=verify_ssl, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS: Token is valid and working!")
    elif response.status_code == 401:
        print("\n❌ FAILED: Authentication failed (401)")
        print("Possible causes:")
        print("  1. Token is expired or invalid")
        print("  2. Token doesn't have required scopes")
        print("  3. Token format is incorrect")
        print("\nAction: Generate a new token at:")
        print(f"  {base_url}/-/profile/personal_access_tokens")
    else:
        print(f"\n⚠️  UNEXPECTED: Got status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test 2: User endpoint (more detailed)
print("\n" + "=" * 60)
print("Test 2: Testing /api/v4/user endpoint (requires authentication)")
print("=" * 60)

url = f"{base_url}/api/v4/user"
try:
    response = requests.get(url, headers=headers, verify=verify_ssl, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"\n✅ SUCCESS: Authenticated as: {user_data.get('username', 'unknown')}")
        print(f"  Name: {user_data.get('name', 'unknown')}")
        print(f"  Email: {user_data.get('email', 'unknown')}")
    elif response.status_code == 401:
        print("\n❌ FAILED: Token authentication failed")
    else:
        print(f"\n⚠️  Status: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test 3: Try to access example group
print("\n" + "=" * 60)
print("Test 3: Testing access to 'your-group' group")
print("=" * 60)

import urllib.parse
group_path = urllib.parse.quote("your-group", safe="")
url = f"{base_url}/api/v4/groups/{group_path}"

try:
    response = requests.get(url, headers=headers, verify=verify_ssl, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        group_data = response.json()
        print(f"\n✅ SUCCESS: Can access your-group group")
        print(f"  Group ID: {group_data.get('id', 'unknown')}")
        print(f"  Full Path: {group_data.get('full_path', 'unknown')}")
    elif response.status_code == 401:
        print("\n❌ FAILED: Authentication failed")
    elif response.status_code == 404:
        print("\n❌ FAILED: Group 'your-group' not found or no access")
    else:
        print(f"\n⚠️  Status: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nIf all tests passed:")
print("  ✅ Your token is working correctly")
print("  ✅ Run: gitdoctor -i commits.txt -o results.csv -v")
print("\nIf tests failed:")
print("  ❌ Generate a new token with these scopes:")
print("     - api")
print("     - read_api")
print("     - read_repository")
print(f"  ❌ URL: {base_url}/-/profile/personal_access_tokens")
print("\n" + "=" * 60)

