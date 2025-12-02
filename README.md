# GitDoctor

A powerful Python CLI tool that maps Git commit SHAs to GitLab repositories. It discovers which repositories contain specific commits and outputs detailed metadata including commit information, branches, and tags.

## Features

- 🔍 **Smart Discovery**: Auto-discover all repositories in GitLab groups or explicitly specify projects to search
- 🚀 **Rich Metadata**: Extract commit details, author info, branches, and tags
- 📊 **CSV/JSON Export**: Generate comprehensive reports for easy analysis
- 🔄 **Delta Discovery**: Compare two releases/tags/branches and find all commits between them
- ⚙️ **Flexible Configuration**: YAML-based configuration with multiple scan modes
- 🔒 **Enterprise Ready**: Supports self-hosted GitLab instances with SSL verification options
- 🧪 **Well Tested**: Comprehensive test suite with pytest

## What It Does

Given a list of Git commit SHAs, this tool:

1. Connects to your GitLab instance (self-hosted or gitlab.com)
2. Searches for each commit across configured repositories
3. For each commit found, collects:
   - Repository information (name, path, URL)
   - Commit metadata (author, title, date)
   - All branches containing the commit
   - All tags containing the commit
4. Outputs a CSV file with all findings

This is particularly useful for:
- **DevOps Teams**: Track which commits made it into which environments
- **QA Teams**: Verify commit presence across multiple repositories
- **Release Management**: Identify branch and tag relationships for commits, discover deltas between releases
- **Audit & Compliance**: Generate reports on code deployment across repositories

## 🔄 Delta Discovery

GitDoctor now supports **delta discovery** - comparing two releases, tags, or branches to find all commits between them across all your microservices:

```bash
# Compare two releases across all services
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.csv
```

This automates the tedious manual process of cloning each repository and running `git log BASE..TARGET`. See [DELTA_GUIDE.md](DELTA_GUIDE.md) for complete documentation.

## Installation

### Prerequisites

- Python >= 3.10
- GitLab Personal Access Token (PAT) with `api`, `read_api`, and `read_repository` scopes

### Setup

1. Clone or download this repository:

```bash
cd /path/to/gitdoctor
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in editable mode:

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

4. Verify installation:

```bash
gitdoctor --version
```

## Configuration

### Creating Your Configuration File

1. Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` with your GitLab details:

```yaml
gitlab:
  base_url: "https://your-gitlab-instance.com"
  private_token: "your-gitlab-personal-access-token"
  verify_ssl: true
  timeout_seconds: 15

scan:
  mode: "auto_discover"  # or "explicit"

groups:
  include_subgroups: true
  by_path:
    - "your-group-name"

# Optional: explicitly specify projects
projects:
  by_path:
    - "group/specific-project"

# Optional: filter which projects to search
filters:
  exclude_project_paths:
    - "group/very-large-repo"
```

### Configuration Reference

#### GitLab Section

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `base_url` | Yes | - | Your GitLab instance URL (no trailing slash) |
| `private_token` | Yes | - | GitLab Personal Access Token |
| `api_version` | No | `v4` | GitLab API version |
| `verify_ssl` | No | `true` | Verify SSL certificates |
| `timeout_seconds` | No | `15` | API request timeout |

**Generating a Personal Access Token:**
1. Go to your GitLab instance
2. Navigate to User Settings → Access Tokens
3. Create a token with scopes: `api`, `read_api`, `read_repository`
4. Copy the token and add it to your config (keep it secure!)

#### Scan Modes

The tool supports two scan modes controlled by `scan.mode`:

**1. Auto-Discover Mode** (`auto_discover`)
- Automatically discovers all projects from configured GitLab groups
- Searches all repositories in the group (and subgroups if enabled)
- Best for: Comprehensive searches across an entire organization or team

**2. Explicit Mode** (`explicit`)
- Only searches explicitly configured projects
- Much faster when you know exactly which repositories to search
- Best for: Targeted searches with known repositories

#### Projects Section

Configure specific projects to search (used in `explicit` mode, or as additions in `auto_discover` mode):

```yaml
projects:
  by_id:
    - 123      # GitLab project ID
    - 456
  by_path:
    - "group/subgroup/project-name"
    - "another-group/project"
```

#### Groups Section

Configure groups for auto-discovery (used in `auto_discover` mode):

```yaml
groups:
  include_subgroups: true  # Also search projects in subgroups
  by_id:
    - 42      # GitLab group ID
  by_path:
    - "myorg"
    - "myorg/backend"
```

#### Filters Section

Optional filters to restrict which projects are searched:

```yaml
filters:
  # Whitelist: ONLY search these projects (if specified)
  include_project_paths:
    - "group/project1"
    - "group/project2"
  
  # Blacklist: SKIP these projects
  exclude_project_paths:
    - "group/archived-project"
    - "group/very-large-monorepo"
```

**Note:** Filters apply AFTER project discovery. Include filter creates a whitelist; exclude filter creates a blacklist.

## Usage

GitDoctor provides two main commands:
- `search` - Find specific commits across repositories (original functionality)
- `delta` - Compare two releases/tags/branches across repositories

### Command 1: Search for Specific Commits

#### Preparing Your Input

Create a text file with commit SHAs (one per line):

```bash
cat > commits.txt << EOF
abc123def456789
fed321cba987654
1234567890abcdef
EOF
```

#### Running Search Command

Basic usage:

```bash
gitdoctor search -i commits.txt -o results.csv

# Or use the old syntax (backward compatible)
gitdoctor -i commits.txt -o results.csv
```

With custom config and verbose logging:

```bash
gitdoctor search -c my-config.yaml -i commits.txt -o output.csv -v
```

#### Search Command Options

```
usage: gitdoctor search [-h] -i COMMITS_FILE [-o OUTPUT] [-c CONFIG] [-v]

Options:
  -h, --help            Show help message
  -i, --commits-file    Path to file with commit SHAs (required)
  -o, --output          Path to output CSV (default: gitlab_commit_mapping.csv)
  -c, --config          Path to YAML config file (default: config.yaml)
  -v, --verbose         Enable verbose logging
```

### Command 2: Discover Delta Between Releases

#### Running Delta Command

Compare two tags:

```bash
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.csv
```

With date filtering:

```bash
gitdoctor delta --base v1.0.0 --target v2.0.0 \
                --after 2025-09-01 \
                -o delta.csv -v
```

Export as JSON:

```bash
gitdoctor delta --base TAG1 --target TAG2 \
                -o delta.json --format json
```

#### Delta Command Options

```
usage: gitdoctor delta [-h] --base BASE --target TARGET [-o OUTPUT] 
                       [--format {csv,json}] [--after AFTER] [--before BEFORE]
                       [-c CONFIG] [-v]

Options:
  -h, --help            Show help message
  --base BASE           Base reference (tag/branch/commit) - starting point
  --target TARGET       Target reference (tag/branch/commit) - ending point
  -o, --output          Path to output file (default: delta.csv)
  --format              Output format: csv or json (default: csv)
  --after AFTER         Only commits after this date (ISO 8601: YYYY-MM-DD)
  --before BEFORE       Only commits before this date (ISO 8601: YYYY-MM-DD)
  -c, --config          Path to YAML config file (default: config.yaml)
  -v, --verbose         Enable verbose logging
```

**📖 For complete delta documentation, see [DELTA_GUIDE.md](DELTA_GUIDE.md)**

### Output Format

The tool generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `commit_sha` | The commit SHA searched for |
| `project_id` | GitLab project ID |
| `project_name` | Repository name |
| `project_path` | Full path (group/subgroup/repo) |
| `project_web_url` | URL to the repository |
| `commit_web_url` | URL to view the commit |
| `author_name` | Commit author name |
| `author_email` | Commit author email |
| `title` | Commit message title |
| `created_at` | Commit timestamp (ISO 8601) |
| `branches` | Pipe-separated list of branches containing this commit |
| `tags` | Pipe-separated list of tags containing this commit |
| `found` | Boolean: whether commit was found |
| `error` | Error message if any |

### Example Output

```csv
commit_sha,project_id,project_name,project_path,branches,tags,found
abc123,123,my-app,myorg/apps/my-app,main|develop|feature-x,v1.0.0|v1.1.0,true
abc123,124,common-lib,myorg/libs/common,master,v2.3.0,true
def456,123,my-app,myorg/apps/my-app,hotfix-branch,,true
```

## Configuration Examples

### Example 1: Search All Projects in a Group

```yaml
gitlab:
  base_url: "https://gitlab.company.com"
  private_token: "glpat-xxxxxxxxxxxx"

scan:
  mode: "auto_discover"

groups:
  include_subgroups: true
  by_path:
    - "myorg/backend"
```

This configuration will:
- Auto-discover all projects in `myorg/backend` and its subgroups
- Search each commit across all discovered projects

### Example 2: Search Only Specific Projects

```yaml
gitlab:
  base_url: "https://gitlab.company.com"
  private_token: "glpat-xxxxxxxxxxxx"

scan:
  mode: "explicit"

projects:
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/order-service"
    - "myorg/backend/api-gateway"
```

This configuration will:
- Only search the three explicitly listed projects
- Much faster for targeted searches

### Example 3: Auto-Discover with Exclusions

```yaml
gitlab:
  base_url: "https://gitlab.company.com"
  private_token: "glpat-xxxxxxxxxxxx"

scan:
  mode: "auto_discover"

groups:
  by_path:
    - "myorg"

filters:
  exclude_project_paths:
    - "myorg/archived/old-project"
    - "myorg/monorepo-with-million-commits"
```

This configuration will:
- Discover all projects in `myorg`
- Skip the two excluded projects for better performance

## Performance Considerations

### Search Speed

The tool makes API calls for each (commit × project) combination:
- 10 commits × 50 projects = 500 API calls
- At ~100ms per call = ~50 seconds

**Tips for Faster Searches:**

1. **Use Explicit Mode**: If you know which repositories to search
2. **Add Exclusions**: Skip large or irrelevant repositories
3. **Batch Your Searches**: Group related commits together
4. **Use Include Filters**: Create a whitelist for focused searches

### Rate Limiting

GitLab has rate limits on API requests:
- gitlab.com: 2,000 requests per minute per user
- Self-hosted: Configurable by admin

The tool includes retry logic for rate limit errors (429 status).

## Security Considerations

### Personal Access Token (PAT)

- **Never commit** your `config.yaml` with a real token to version control
- Add `config.yaml` to `.gitignore`
- Use a dedicated service account token for shared/CI usage
- Rotate tokens periodically
- Use minimal required scopes: `read_api`, `read_repository`

### SSL Verification

- Keep `verify_ssl: true` for production
- Only set to `false` for development with self-signed certificates
- Use proper CA certificates in production environments

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=gitlab_commit_mapper --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Project Structure

```
gitdoctor/
├── gitlab_commit_mapper/
│   ├── __init__.py           # Package initialization
│   ├── api_client.py         # GitLab API wrapper
│   ├── cli.py                # Command-line interface
│   ├── commit_finder.py      # Commit search logic
│   ├── config.py             # Configuration loading
│   └── project_resolver.py   # Project discovery logic
├── tests/
│   ├── test_api_client.py
│   ├── test_commit_finder.py
│   ├── test_config.py
│   └── test_project_resolver.py
├── config.example.yaml       # Example configuration
├── pyproject.toml            # Package metadata
├── requirements.txt          # Dependencies
├── README.md                 # This file
└── CONFLUENCE_HANDBOOK.txt   # Plain-text handbook
```

## Troubleshooting

> 📖 **For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### Installation Errors

#### Error: "Cannot declare ('project', 'optional-dependencies') twice"

**Problem:** Duplicate sections in `pyproject.toml`

**Solution:**
```bash
# The pyproject.toml file has been fixed, but if you see this:
pip install -e .  # Should work now
```

If you still encounter this, check `pyproject.toml` for duplicate `[project.optional-dependencies]` sections.

#### Error: "command 'gitdoctor' not found"

**Problem:** Package not installed or virtual environment not activated

**Solutions:**
```bash
# 1. Ensure virtual environment is activated
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate  # On Windows

# 2. Install the package
pip install -e .

# 3. Verify installation
which gitdoctor  # Should show path in venv/bin/
gitdoctor --version  # Should show version
```

### Configuration Errors

#### Error: "In explicit mode, at least one project must be configured"

**Problem:** YAML list syntax error in `config.yaml` - using commas instead of dashes

**Solution:**
```yaml
# ❌ WRONG - Don't use commas:
projects:
  by_path:
    "group/project1",
    "group/project2",
    "group/project3"

# ✅ CORRECT - Use dashes:
projects:
  by_path:
    - "group/project1"
    - "group/project2"
    - "group/project3"
```

**Important:** YAML lists require a dash (`-`) before each item, not commas!

#### Error: "In auto_discover mode, at least one group must be configured"

**Problem:** Similar YAML syntax error or empty groups configuration

**Solution:**
```yaml
# ✅ CORRECT format:
groups:
  by_path:
    - "your-group-name"
    - "another-group"
  by_id: []  # Empty list if not using IDs
```

### Authentication Errors (401)

**Problem:** `GitLabUnauthorized: Authentication failed`

**Solutions:**
- Verify your PAT is correct and not expired
- Ensure PAT has required scopes: `api`, `read_api`, `read_repository`
- Check if token belongs to user with access to configured projects/groups

### Access Denied (403)

**Problem:** `GitLabForbidden: Access forbidden`

**Solutions:**
- Verify your user has at least Reporter/Guest access to the projects
- Check if projects/groups are private and token has proper permissions
- Ensure group paths are correct and accessible

### Resource Not Found (404)

**Problem:** `GitLabNotFound: Resource not found`

**Solutions:**
- Verify group/project paths are correct (case-sensitive)
- Check if you have access to view the group/project
- Ensure project IDs are valid

### SSL Certificate Errors

**Problem:** `SSL verification failed`

**Solutions:**
- For self-signed certificates, set `verify_ssl: false` (not recommended for production)
- Install proper CA certificates on your system
- For corporate proxies, configure SSL_CERT_FILE environment variable

### Slow Performance

**Solutions:**
- Switch to `explicit` mode and list only needed projects
- Add exclusions for large repositories in filters
- Reduce the number of commits searched per run
- Check your network latency to GitLab instance

### Empty Results

**Problem:** No commits found in any project

**Solutions:**
- Verify commits exist in configured projects (check on GitLab web UI)
- Ensure full commit SHA is used (not abbreviated)
- Check if commits are in default branch or might be in forks
- Verify project search scope includes the right repositories

## Future Enhancements

Potential features for future versions:

- **Parallelization**: Use threading/asyncio for faster searches
- **Progress Bar**: Visual progress indicator for long-running searches
- **Resume Capability**: Save progress and resume interrupted searches
- **Multiple Output Formats**: JSON, Excel, HTML reports
- **Web UI**: Simple web interface for non-technical users
- **CI/CD Integration**: GitHub Actions / GitLab CI templates
- **Caching**: Cache project lists and commit results
- **Webhook Integration**: Real-time commit tracking

## Contributing

Contributions welcome! Areas for improvement:
- Performance optimizations
- Additional output formats
- Better error messages
- More comprehensive tests

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check the Troubleshooting section above
2. Review the documentation in this repository
3. Open an issue on GitHub for support

## Changelog

### Version 1.0.0
- Initial release
- Auto-discover and explicit scan modes
- CSV output with rich metadata
- Comprehensive test suite
- Full documentation

