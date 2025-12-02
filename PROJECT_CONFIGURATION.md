# Project Configuration Guide

## 📍 Where Projects Are Configured

Projects for delta discovery are configured in **two places**:

### 1. **Config File (`config.yaml`)** - Default

Projects are configured in `config.yaml` under the `projects` section:

```yaml
projects:
  by_id: []  # Project IDs (e.g., [123, 456])
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/order-service"
    - "myorg/frontend/web-app"
```

**How it works:**
- In **explicit mode**: Only projects listed here are used
- In **auto_discover mode**: Projects from groups + explicitly listed projects

### 2. **CLI Arguments** - Override Config

You can now override config projects using CLI arguments:

```bash
# Filter by project paths
--projects "path1,path2,path3"

# Filter by project IDs
--project-ids "123,456,789"
```

**How it works:**
- CLI arguments **filter** the projects from config
- Only projects matching CLI args are used
- If no match, command fails with clear error

---

## 🚀 Usage Examples

### Example 1: Use All Projects from Config

```bash
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o delta.csv
```

**Result:** Uses all 3 projects from `config.yaml`

---

### Example 2: Filter to Specific Projects by Path

```bash
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  --projects "myorg/backend/user-service,myorg/backend/order-service" \
  -o delta.csv
```

**Result:** Only compares the 2 specified projects (filters from config)

---

### Example 3: Filter by Project IDs

```bash
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  --project-ids "123,456" \
  -o delta.csv
```

**Result:** Only compares projects with IDs 123 and 456

---

### Example 4: Single Project Quick Test

```bash
gitdoctor delta \
  --base TAG1 \
  --target TAG2 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  --projects "myorg/backend/order-service" \
  -o test-single.csv \
  -v
```

**Result:** Quick test with just one project

---

## 🔍 How to Find Project IDs

### Method 1: From GitLab Web UI

1. Go to your project in GitLab
2. Look at the URL: `https://gitlab.com/group/project/-/settings/general`
3. Project ID is shown in the project settings page

### Method 2: From GitDoctor Output

Run with verbose mode to see project IDs:

```bash
gitdoctor delta \
  --base TAG1 \
  --target TAG2 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o delta.csv \
  -v
```

**Output:**
```
Resolving projects to compare...
  Will compare across 3 project(s)
    - myorg/backend/user-service (ID: 123)
    - myorg/backend/order-service (ID: 456)
    - myorg/frontend/web-app (ID: 1234)
```

### Method 3: From Config File

If you have project IDs in config:

```yaml
projects:
  by_id:
    - 123
    - 456
```

---

## ⚙️ Configuration Modes

### Explicit Mode

```yaml
scan:
  mode: "explicit"

projects:
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/api-gateway"
```

**Behavior:**
- Uses ONLY projects listed in `projects.by_path` or `projects.by_id`
- CLI `--projects` filters from this list
- Fastest mode (no group discovery)

### Auto Discover Mode

```yaml
scan:
  mode: "auto_discover"

groups:
  by_path:
    - "myorg"
  include_subgroups: true

projects:
  by_path:
    - "myorg/backend/user-service"  # Additional explicit projects
```

**Behavior:**
- Discovers ALL projects from `groups.by_path`
- Also includes projects from `projects.by_path`
- CLI `--projects` filters from the combined list
- Slower but comprehensive

---

## 🎯 Best Practices

### 1. **Use Config for Default Projects**

Keep your most-used projects in `config.yaml`:

```yaml
projects:
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/api-gateway"
    - "myorg/frontend/web-app"
```

### 2. **Use CLI for Ad-Hoc Filtering**

For one-off comparisons, use CLI args:

```bash
# Test with just one project
--projects "myorg/backend/user-service"

# Compare specific subset
--projects "myorg/backend/user-service,myorg/backend/api-gateway"
```

### 3. **Use Project IDs for Stability**

Project paths can change, but IDs are stable:

```bash
# More stable (IDs don't change)
--project-ids "123,456"

# Less stable (paths can be renamed)
--projects "myorg/backend/user-service,myorg/backend/api-gateway"
```

### 4. **Combine with Date Ranges**

Always use date ranges with project filtering:

```bash
gitdoctor delta \
  --base TAG1 \
  --target TAG2 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  --projects "myorg/backend/user-service" \
  -o delta.csv
```

---

## ❌ Error Handling

### Error 1: No Projects Found After Filtering

```bash
$ gitdoctor delta --base TAG1 --target TAG2 \
                  --after 2025-09-01 --before 2025-11-01 \
                  --projects "nonexistent/project" \
                  -o delta.csv

ERROR: No projects found after filtering. Check your --projects or --project-ids arguments.
```

**Solution:** Verify project paths/IDs exist in your config

### Error 2: Invalid Project IDs Format

```bash
$ gitdoctor delta --base TAG1 --target TAG2 \
                  --after 2025-09-01 --before 2025-11-01 \
                  --project-ids "abc,def" \
                  -o delta.csv

ERROR: Invalid project IDs format. Expected comma-separated numbers.
```

**Solution:** Use numeric IDs only: `--project-ids "123,456"`

---

## 📊 Summary

| Method | Use Case | Example |
|--------|----------|---------|
| **Config file** | Default projects for all runs | `config.yaml` |
| **`--projects`** | Filter by project paths | `--projects "path1,path2"` |
| **`--project-ids`** | Filter by project IDs | `--project-ids "123,456"` |

**Key Points:**
- ✅ Config file sets default projects
- ✅ CLI args filter/override config projects
- ✅ Use `-v` to see which projects are being compared
- ✅ Project IDs are more stable than paths

---

## 🔗 Related Documentation

- **[DELTA_GUIDE.md](DELTA_GUIDE.md)** - Complete delta discovery guide
- **[config.yaml](config.yaml)** - Your configuration file
- **[README.md](README.md)** - Main documentation

---

**Ready to use!** You can now specify projects via CLI without editing config. 🎉

