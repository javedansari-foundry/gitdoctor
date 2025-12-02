# Development Rules & Testing Checklist

## 🎯 Core Principles

1. **Always test before declaring "done"**
2. **Never commit secrets or tokens**
3. **Comprehensive testing for all changes**
4. **Automated checks where possible**

---

## ✅ Pre-Commit Checklist

### 1. Code Quality
- [ ] Run linter: `read_lints` on all changed files
- [ ] Fix all linting errors
- [ ] Check for unused imports
- [ ] Verify function signatures match usage

### 2. Secret Scanning
- [ ] Run secret scanner: `python scripts/check_secrets.py`
- [ ] Verify no PATs, tokens, or passwords in code
- [ ] Check config files are in `.gitignore`
- [ ] Ensure example configs use placeholders only

### 3. Functionality Testing
- [ ] Test the specific feature/change
- [ ] Test error cases (invalid input, missing files, etc.)
- [ ] Test edge cases (empty lists, None values, etc.)
- [ ] Verify backward compatibility if applicable

### 4. Integration Testing
- [ ] Test with real config file
- [ ] Test CLI commands work end-to-end
- [ ] Verify output formats (CSV, JSON, HTML)
- [ ] Check error messages are clear

### 5. Documentation
- [ ] Update relevant `.md` files
- [ ] Update help text if CLI changed
- [ ] Add examples if new feature
- [ ] Update changelog if significant

---

## 🧪 Testing Framework

### Unit Tests
```bash
# Test individual functions
python -m pytest tests/unit/ -v
```

### Integration Tests
```bash
# Test with real GitLab (requires config.yaml)
python -m pytest tests/integration/ -v
```

### Manual Testing Checklist
```bash
# 1. Test basic functionality
gitdoctor search -i commits.txt -o test.csv

# 2. Test delta command
gitdoctor delta --base TAG1 --target TAG2 \
                --after 2025-09-01 --before 2025-11-01 \
                -o test.csv

# 3. Test with invalid input
gitdoctor delta --base TAG1 --target TAG2  # Should fail (missing dates)

# 4. Test error handling
gitdoctor delta --base INVALID --target INVALID \
                --after 2025-09-01 --before 2025-11-01 \
                -o test.csv  # Should handle gracefully
```

---

## 🔒 Secret Scanning Rules

### What to Check For:
- GitLab Personal Access Tokens (PATs): `glpat-*`, `Rwd*`, etc.
- API keys: `api_key`, `apikey`, `API_KEY`
- Passwords: `password`, `passwd`, `pwd`
- Tokens: `token`, `access_token`, `private_token`
- Secrets: `secret`, `SECRET`, `secret_key`
- AWS keys: `AWS_ACCESS_KEY`, `AWS_SECRET`
- Database credentials: `db_password`, `database_password`

### Files to Always Check:
- `config.yaml` (should be in .gitignore)
- `config-*.yaml` (test configs)
- `*.py` files (code)
- `*.md` files (documentation - should use placeholders)
- `*.txt` files (logs, test data)

### Pattern Detection:
- Look for: `private_token: "actual-token-here"`
- Look for: `password: "real-password"`
- Look for: `glpat-` followed by alphanumeric string
- Look for: Long random strings (likely tokens)

---

## 🚨 Error Testing Checklist

For every new feature, test:

1. **Missing Required Arguments**
   ```bash
   gitdoctor delta --base TAG1  # Missing --target, --after
   ```

2. **Invalid Date Formats**
   ```bash
   gitdoctor delta --base TAG1 --target TAG2 \
                   --after 2025/09/01  # Wrong format
   ```

3. **Date Range > 2 Months**
   ```bash
   gitdoctor delta --base TAG1 --target TAG2 \
                   --after 2025-01-01 --before 2025-06-01  # > 2 months
   ```

4. **Invalid Project Paths**
   ```bash
   gitdoctor delta --base TAG1 --target TAG2 \
                   --after 2025-09-01 --before 2025-11-01 \
                   --projects "nonexistent/project"
   ```

5. **Missing Config File**
   ```bash
   gitdoctor delta -c nonexistent.yaml ...
   ```

6. **Network Errors** (if possible)
   - Disconnect network
   - Use invalid GitLab URL
   - Use expired token

---

## 📝 Code Review Checklist

Before submitting code:

- [ ] All tests pass
- [ ] No secrets in code
- [ ] Error messages are clear
- [ ] Logging is appropriate (not too verbose)
- [ ] Documentation updated
- [ ] Backward compatibility maintained
- [ ] Performance considered (no unnecessary API calls)

---

## 🔄 Continuous Improvement

1. **After each bug fix:**
   - Add test case for that bug
   - Update this checklist if needed
   - Document the fix

2. **After each feature:**
   - Add integration test
   - Update user documentation
   - Add example usage

3. **Regular audits:**
   - Review all config files for secrets
   - Check .gitignore is comprehensive
   - Verify all error paths are tested

---

## 🛠️ Automated Checks

### Pre-commit Hook (Recommended)
```bash
# Install pre-commit hook
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Manual Secret Check
```bash
# Before every commit
python scripts/check_secrets.py
```

### Linting Check
```bash
# Before every commit
read_lints paths/to/changed/files
```

---

## 📚 Reference

- **Secret Patterns**: See `scripts/check_secrets.py`
- **Test Examples**: See `tests/` directory
- **Config Examples**: See `config.example.yaml`
- **Error Handling**: See `gitdoctor/cli.py` error handling patterns

---

**Remember**: It's better to spend 5 minutes testing now than 30 minutes debugging later! 🎯

