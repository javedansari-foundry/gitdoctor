# Quick Start Guide

Get up and running in 5 minutes!

## Installation

```bash
cd /path/to/your/project

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows

# Install the tool
pip install -e .

# Verify installation
gitdoctor --version
```

**⚠️ If you see errors during installation:**
- Make sure you're in the virtual environment (you should see `(venv)` in your terminal)
- If you see "Cannot declare...twice" error, the pyproject.toml has been fixed - try again
- See README.md → Troubleshooting → Installation Errors

## Configuration

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml and set:
# 1. Your GitLab URL (base_url)
# 2. Your Personal Access Token (private_token)
# 3. Choose mode: auto_discover or explicit
# 4. Add your groups (auto_discover) or projects (explicit)

# ⚠️ IMPORTANT - Use proper YAML list syntax:
# ✅ CORRECT:
#   by_path:
#     - "group/project1"
#     - "group/project2"
#
# ❌ WRONG (don't use commas):
#   by_path:
#     "group/project1",
#     "group/project2"
```

## Usage

```bash
# Create a file with commit SHAs (one per line)
cat > commits.txt << EOF
abc123def456
fed321cba987
EOF

# Run the tool
gitdoctor -i commits.txt -o results.csv

# Open results.csv in Excel
```

## Need Help?

- **Common issues & errors**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) ⭐
- **Installation issues**: See README.md → Installation section
- **Configuration help**: See [INTEGRATION_TESTING_GUIDE.md](INTEGRATION_TESTING_GUIDE.md)
- **Quick setup**: See [QUICKSTART.md](QUICKSTART.md)
- **Usage examples**: See CONFLUENCE_HANDBOOK.txt
- **API/technical details**: See README.md

## Test Results

All 49 tests passing ✅

```bash
# Run tests yourself
source venv/bin/activate
pytest -v
```

Enjoy! 🚀

