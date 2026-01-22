# GitDoctor - Comviva Internal Setup

## 🔒 Internal Use Only

This is the internal Comviva configuration and documentation for GitDoctor.

---

## Quick Start for Comviva Team

### 1. Clone from Internal GitLab

```bash
git clone http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor.git
cd gitdoctor
```

### 2. Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install GitDoctor
pip install -e .
```

### 3. Configure

```bash
# Copy the Comviva config template
cp config.comviva.yaml config.yaml

# Edit with your GitLab token
nano config.yaml
```

**Get your GitLab token:**
- Go to: http://blrgitlab.comviva.com/-/profile/personal_access_tokens
- Create token with scopes: `api`, `read_api`, `read_repository`
- Copy token to `config.yaml`

### 4. Test

```bash
# Verify installation
gitdoctor --version

# Test with sample tags
gitdoctor delta \
  --base MobiquityPay_vX.10.15.8_L4Patch_19Jan26 \
  --target MobiquityPay_vX.10.15.8_PVG.B1 \
  --format html \
  -o delta-report.html
```

---

## Comviva-Specific Configuration

### GitLab Instance

- **URL:** http://blrgitlab.comviva.com
- **Main Group:** dfs-core
- **Sub-groups:** product-domains, orchestration, platform, devops, etc.

### JIRA Integration

- **URL:** https://comviva.atlassian.net
- **Common Projects:** MON, DFS, etc.

### Common Project IDs

| Project | ID | Path |
|---------|----|----|
| Shulka | 127 | dfs-core/product-domains/transaction/shulka |
| SOE | TBD | dfs-core/mobiquity-one-issuing/microservices/soe |
| SOE Core | TBD | dfs-core/orchestration/soe-core |
| SDUI Screens | TBD | dfs-core/sdui/projects/mobiquity/mobiquity-sdui-screens |
| Multinode Deploy | TBD | dfs-core/devops/multinode_mobiquity_deployment |
| Platform Config | TBD | dfs-core/platform/config |
| Ansible Configs | TBD | dfs-core/devops/ansible_configs |

---

## Common Use Cases

### 1. Release Delta Discovery

Compare two MobiquityPay releases:

```bash
gitdoctor delta \
  --base MobiquityPay_vX.10.15.8_L4Patch_19Jan26 \
  --target MobiquityPay_vX.10.15.8_PVG.B1 \
  --format html \
  -o delta-mobiquitypay.html
```

### 2. MR Changes for Test Selection

Get complete changeset from an MR:

```bash
gitdoctor mr-changes \
  --project "dfs-core/product-domains/transaction/shulka" \
  --mr 123 \
  --format test-selection \
  -o mr-changes.json
```

### 3. Track MRs to Master

Find all MRs merged to master in date range:

```bash
gitdoctor mr \
  --target master \
  --after 2026-01-01 \
  --format html \
  -o master-mrs.html
```

---

## Configuration Template

See `config.comviva.yaml` for pre-configured settings:

```yaml
gitlab:
  base_url: "http://blrgitlab.comviva.com"
  private_token: "YOUR_TOKEN_HERE"
  verify_ssl: false

scan:
  mode: "auto_discover"

groups:
  by_path:
    - "dfs-core"

jira:
  base_url: "https://comviva.atlassian.net"
  project_key: "MON"
```

---

## Support

- **Repository:** http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor
- **Issues:** Create issue in internal GitLab
- **Team Chat:** Ask in automation team channel

---

## Public Documentation

For generic documentation (sanitized), see:
- https://github.com/javedansari-foundry/gitdoctor

⚠️ **Note:** Public repo has generic examples. Use this internal README for Comviva-specific information.

