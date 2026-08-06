# Flow validation guide

Branch-flow and release reconciliation commands are **separate from** `gitdoctor delta`. Delta reports are unchanged.

## Prerequisites

```bash
cd gitdoctor
source venv/bin/activate   # or: python3 -m venv venv && pip install -e ".[dev]"
cp config.example.yaml config.yaml   # add GitLab token + flow_validation section
```

Work from the **`gitdoctor/`** directory (this folder is the git repository root).

## Release 11.2 freeze (verify DevOps attestation)

### 1. DevOps provides CSV

Columns: `jira_ticket`, `mr_iid`, `mr_url`, `merge_commit_sha`, `source_branch`, `merged_at`.

### 2. Export Jira 11.2 scope

```bash
# CSV from Jira with column "key"
# Or configure jira.email + jira.api_token + default_jql in config.yaml
```

### 3. Run release reconciliation

```bash
gitdoctor release-check \
  --preset devops_release \
  --jira-csv /path/to/jira-11.2.csv \
  --base-ref MobiquityPay_v11.1.0 \
  --target-ref master \
  --premaster premaster-291225 \
  --after 2025-12-01 \
  -o ../11.2-release-check.html
```

Review statuses:

| Status | Meaning |
|--------|---------|
| OK_BOTH | Ticket trace on premaster and master |
| OK_PREMASTER_ONLY | On premaster only (may be in-flight) |
| MASTER_ONLY | On master but not premaster (drift) |
| MISSING_BOTH | In Jira scope, no git trace |

Exit code `2` if `MISSING_BOTH` or `MASTER_ONLY` rows exist.

### 4. Branch route audit

```bash
gitdoctor flow-report \
  --preset devops_release \
  --premaster premaster-291225 \
  --target master \
  --after 2025-12-01 \
  -o ../11.2-flow-report.html
```

Flag `VIOLATION_DIRECT_FEATURE` and `MISSING_ON_PREMASTER`.

## After premaster rebase (mandatory going forward)

### Per MR (developer / reviewer)

```bash
gitdoctor validate-mr \
  --project "dfs-core/devops/ansible_configs" \
  --mr 456 \
  --target master \
  --premaster premaster-<new-id>
```

Exit `0` = route OK (and containment OK, or exception). Exit `1` = fix before merge.

### Weekly / before promotion

```bash
gitdoctor flow-report --preset devops_release --premaster premaster-<id> --after 2026-01-01 -o flow.html
gitdoctor release-check --preset devops_release --jira-csv sprint.csv --base-ref premaster-<id> --target-ref master --premaster premaster-<id> -o release.html
```

### Exception bypass

1. Add label `flow-exception` and description block on the MR (see plan).
2. Register audit record:

```bash
gitdoctor flow-exception register \
  --project "dfs-core/devops/ansible_configs" \
  --mr 456 \
  --ticket MON-12345 \
  --reason "premaster env unstable" \
  --approved-by maintainer.user
```

3. After premaster backfill:

```bash
gitdoctor flow-exception close EX-20260403-abc123 --backfill-mr 789
```

## Commands summary

| Command | Purpose |
|---------|---------|
| `flow-report` | MR route + premaster containment |
| `release-check` | Jira scope vs git on premaster/master |
| `validate-mr` | Single MR advisory check |
| `flow-exception` | Exception registry |

## Stash note

If you had uncommitted delta work on `main`, it was stashed as:

`WIP: delta traceability and related changes (pre-flow-validation)`

Restore on `main` with: `git checkout main && git stash pop`
