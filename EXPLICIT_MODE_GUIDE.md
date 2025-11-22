# Explicit Mode - Quick Guide

Use explicit mode to search only specific repositories for **10x faster** results!

## 🚀 Quick Start

### Step 1: Find Your Repository Paths

**Run the helper script:**
```bash
cd /path/to/your/project/gitdoctor
source venv/bin/activate
python list_projects.py
```

This creates `projects_list.txt` with all available projects.

### Step 2: Edit config-explicit.yaml

Open `config-explicit.yaml` and add your project paths:

```yaml
scan:
  mode: "explicit"

projects:
  by_path:
    - "your-group/devops/my-app"
    - "your-group/backend/api-service"
    - "your-group/frontend/web-ui"
    # Add 10-20 of your most important projects
```

### Step 3: Run with Explicit Config

```bash
gitdoctor -c config-explicit.yaml -i commits.txt -o results.csv -v
```

## 📊 Speed Comparison

| Mode | Projects Searched | Time |
|------|-------------------|------|
| Auto-discover | 100+ projects | 3-5 minutes |
| Explicit (10 projects) | 10 projects | 15 seconds |
| Explicit (20 projects) | 20 projects | 30 seconds |

## 🎯 Finding Project Paths

### Method 1: From GitLab Web UI
1. Go to your project in browser
2. URL: `https://gitlab.example.com/your-group/devops/my-app`
3. Path: `your-group/devops/my-app` ✅

### Method 2: From Previous Results
1. Open your `results.csv` from auto-discover run
2. Look at `project_path` column
3. Copy the paths you want to search regularly

### Method 3: From Helper Script
```bash
python list_projects.py
cat projects_list.txt
```

## 📝 Configuration Examples

### Example 1: Production Services Only
```yaml
# config-production.yaml
scan:
  mode: "explicit"

projects:
  by_path:
    - "your-group/prod/api-gateway"
    - "your-group/prod/auth-service"
    - "your-group/prod/payment-service"
    - "your-group/prod/user-service"
```

Run:
```bash
gitdoctor -c config-production.yaml -i commits.txt -o prod-check.csv
```

### Example 2: Backend Services
```yaml
# config-backend.yaml
scan:
  mode: "explicit"

projects:
  by_path:
    - "your-group/backend/api-service"
    - "your-group/backend/worker-service"
    - "your-group/backend/queue-service"
    - "your-group/libs/common-backend"
```

### Example 3: Using Project IDs
```yaml
# Alternative: use numeric IDs instead of paths
scan:
  mode: "explicit"

projects:
  by_id:
    - 123
    - 456
    - 789
```

Find project IDs in `projects_list.txt` or from GitLab UI (Settings → General).

## 🎨 Workflow Examples

### Quick Hotfix Check (5 critical services)
```bash
# Create config-critical.yaml with 5 most important services
gitdoctor -c config-critical.yaml -i hotfix.txt -o hotfix-check.csv
# Time: ~10 seconds
```

### Backend Services Check
```bash
# Create config-backend.yaml with backend services
gitdoctor -c config-backend.yaml -i commits.txt -o backend-check.csv
# Time: ~20 seconds for 15 services
```

### Full Check (when you have time)
```bash
# Use original config.yaml with auto-discover
gitdoctor -c config.yaml -i commits.txt -o full-check.csv
# Time: 3-5 minutes for 100+ services
```

## 💡 Best Practices

### 1. Create Multiple Configs
```
config.yaml              # Auto-discover (comprehensive)
config-explicit.yaml     # General explicit template
config-critical.yaml     # Top 5-10 critical services
config-production.yaml   # Production repos only
config-backend.yaml      # Backend services
config-frontend.yaml     # Frontend services
```

### 2. Start Small
- Begin with 10-15 most important projects
- Add more as needed
- Keep critical services config minimal (5-10 projects)

### 3. Regular Updates
- Update explicit configs monthly
- Add new services as they're deployed
- Remove deprecated projects

### 4. Documentation
- Add comments in config with project purpose
- Note which services are critical
- Document ownership/contacts

## 🔄 Migration from Auto-Discover

If you just ran auto-discover mode:

1. **Check results.csv** - see which projects had commits
2. **Copy relevant paths** - the ones you actually need to check
3. **Create explicit config** - add just those 10-20 projects
4. **Test** - run explicit mode with same commits.txt
5. **Compare** - should get same results but 10x faster!

## 🛠️ Combining Both Modes

Use both depending on scenario:

**Weekly comprehensive check:**
```bash
# Sunday night: full scan with auto-discover
gitdoctor -i weekly-commits.txt -o weekly-full.csv
```

**Daily quick checks:**
```bash
# Every day: quick check of critical services
gitdoctor -c config-critical.yaml -i daily-commits.txt -o daily-check.csv
```

**Hotfix verification:**
```bash
# Immediate: check hotfix in production services only
gitdoctor -c config-production.yaml -i hotfix.txt -o hotfix.csv
```

## 📊 Measuring Performance

Track your search times:

```bash
# Time the search
time gitdoctor -c config-explicit.yaml -i commits.txt -o results.csv

# Example output:
# real    0m15.234s    (15 seconds!)
# user    0m2.341s
# sys     0m0.432s
```

Compare with auto-discover:
```bash
time gitdoctor -c config.yaml -i commits.txt -o results.csv

# Example output:
# real    3m42.567s    (3 minutes 42 seconds)
# user    0m8.234s
# sys     0m1.234s
```

**Speed improvement: ~15x faster!** ⚡

## 🎯 Summary

| Step | Command |
|------|---------|
| 1. List all projects | `python list_projects.py` |
| 2. Check projects_list.txt | `cat projects_list.txt` |
| 3. Edit explicit config | Edit `config-explicit.yaml` |
| 4. Run with explicit mode | `gitdoctor -c config-explicit.yaml -i commits.txt -o results.csv` |
| 5. Enjoy speed! | ~10-30 seconds vs 3-5 minutes 🚀 |

---

**Next Steps:**
1. Run `python list_projects.py` now
2. Pick your 10-20 most important projects
3. Add them to `config-explicit.yaml`
4. Test with `commits.txt`
5. Create more specialized configs as needed

Happy fast searching! ⚡

