# Google Drive Safety Suite - Quick Reference

Fast lookup for common commands and usage patterns.

---

## 🚀 Quick Commands

### CLI - Scan

```bash
# Basic scan
python gdrive_safety_cli.py scan --folder-id FOLDER_ID

# With max depth
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 3

# Save results
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --output results.json

# Deep scan (comprehensive)
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 10
```

### CLI - Cleanup

```bash
# Cleanup with confirmation
python gdrive_safety_cli.py cleanup --session-id SESSION_ID --confirm

# Interactive cleanup (prompts for confirmation)
python gdrive_safety_cli.py cleanup --session-id SESSION_ID
```

### CLI - Report

```bash
# Generate report from scan results
python gdrive_safety_cli.py report --scan-results results.json --output report.txt

# View report in terminal
python gdrive_safety_cli.py report --scan-results results.json
```

### Claude Code CLI

```bash
# Install skill
npx skills add gdrive-safety

# Scan folder
claude gdrive:scan --folder-id FOLDER_ID

# View results
claude gdrive:results

# Cleanup
claude gdrive:cleanup --session-id SESSION_ID --confirm
```

---

## 🐍 Python - Common Patterns

### Pattern 1: Simple Scan & Report

```python
from gdrive_safety_suite import GDriveSafetyManager

manager = GDriveSafetyManager()
results = manager.check_folder("folder_id")
print(f"Files: {results['files_found']}, Issues: {len(results['issues'])}")
manager.cleanup(confirm=True)
```

### Pattern 2: Detailed Analysis

```python
from gdrive_safety_suite import SafetyValidator, FileTypeChecker

validator = SafetyValidator()
checker = FileTypeChecker()

for file in files:
    file_type = checker.classify(file)
    issues = validator.validate_file(file)
    if issues:
        print(f"{file['name']}: {len(issues)} issues")
```

### Pattern 3: Custom Session Tracking

```python
from gdrive_safety_suite import SessionMemory

session = SessionMemory()
sid = session.start_session()

# Track operations
session.track_file_path(sid, "file_path")
session.track_metadata(sid, {"name": "value"})

# Get summary
summary = session.get_session_summary(sid)
print(summary)
```

### Pattern 4: Batch Scanning

```python
from gdrive_safety_suite import GDriveSafetyManager

manager = GDriveSafetyManager()
folders = ["folder1", "folder2", "folder3"]
all_results = []

for folder_id in folders:
    results = manager.check_folder(folder_id)
    all_results.append(results)

manager.cleanup(confirm=True)
```

---

## 📊 Output Interpretation

### Risk Levels

| Level | Severity | Action |
|-------|----------|--------|
| 🔴 HIGH | Critical | Investigate immediately |
| 🟡 MEDIUM | Warning | Review and plan action |
| 🟢 LOW | Info | Note for reference |
| ✅ SAFE | None | No action needed |

### Common Issues

| Issue | Meaning | Action |
|-------|---------|--------|
| permission | Restricted access | Review sharing settings |
| symlink | Shortcut/alias | Verify intended behavior |
| large_file | Exceeds size limit | Review storage needs |
| depth_limit | Nesting too deep | Check folder structure |
| suspicious_file | Unusual type | Review file contents |
| corruption | Metadata error | May need repair |

---

## 🔒 Privacy & Cleanup

### Always Cleanup When Done

```python
# ✅ Correct way
manager = GDriveSafetyManager()
results = manager.check_folder("folder_id")
# ... process results ...
manager.cleanup(confirm=True)  # REQUIRED

# ❌ Wrong way (data stays in memory)
manager = GDriveSafetyManager()
results = manager.check_folder("folder_id")
# Forgot to cleanup!
```

### Verify Cleanup

```python
# After cleanup, session should be empty
status = manager.privacy.get_cleanup_status()
print(status)
# Should show: audit_logs_count: 0, cleanups_performed: 1
```

---

## ⚙️ Configuration Presets

### Quick Scan (Fast, Surface Level)
```python
manager = GDriveSafetyManager(max_depth=2)
```

### Standard Scan (Balanced)
```python
manager = GDriveSafetyManager(max_depth=5)
```

### Deep Scan (Thorough, Slow)
```python
manager = GDriveSafetyManager(max_depth=10)
```

### Secure Scan (With Audit Logs)
```python
manager = GDriveSafetyManager(
    max_depth=5,
    enable_audit_log=True
)
```

---

## 🔐 Environment Setup

### First Time Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup Google credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# 3. Test installation
python -c "from gdrive_safety_suite import GDriveSafetyManager; print('✓')"

# 4. Run first scan
python gdrive_safety_cli.py scan --folder-id root
```

### Persistent Setup (Linux/Mac)

```bash
# Add to ~/.bashrc or ~/.zshrc
export GOOGLE_APPLICATION_CREDENTIALS=~/.gdrive_safety/credentials.json
export PYTHONPATH="${PYTHONPATH}:/path/to/gdrive-safety"

# Make CLI available globally
sudo ln -s /path/to/gdrive_safety_cli.py /usr/local/bin/gdrive-safety

# Then use anywhere
gdrive-safety scan --folder-id FOLDER_ID
```

---

## 🐛 Debug Mode

### Enable Verbose Output

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs
manager = GDriveSafetyManager()
results = manager.check_folder("folder_id")
```

### CLI Debug Mode

```bash
# With debug logging
LOGLEVEL=DEBUG python gdrive_safety_cli.py scan --folder-id FOLDER_ID

# Or verbose flag
python -v gdrive_safety_cli.py scan --folder-id FOLDER_ID
```

### Test Connection

```python
# Test Google Drive connection
from google.auth import default
from googleapiclient.discovery import build

creds, _ = default()
drive = build('drive', 'v3', credentials=creds)
about = drive.about().get(fields='user').execute()
print(f"User: {about['user']['displayName']}")
```

---

## 📈 Performance Tuning

### Reduce Memory Usage
```python
# Use shallow scan instead of deep
manager = GDriveSafetyManager(max_depth=2)

# Or scan smaller folders
results = manager.check_folder("specific_subfolder_id")
```

### Speed Up Scans
```bash
# Max depth = less files to check
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 1

# Or smaller batch sizes
# (edit validator.py to adjust batch_size)
```

### Reduce API Calls
```bash
# Cache results locally
python gdrive_safety_cli.py scan \
  --folder-id FOLDER_ID \
  --output results.json

# Reuse cached results
python gdrive_safety_cli.py report \
  --scan-results results.json \
  --output report.txt
```

---

## 🆘 Quick Fixes

### "API Quota Exceeded"
```bash
# Wait and retry
sleep 3600
python gdrive_safety_cli.py scan --folder-id FOLDER_ID
```

### "Access Denied"
```bash
# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Reauthenticate
rm ~/.config/gcloud/app_default_credentials.json
# Run again (will prompt for auth)
```

### "Module Not Found"
```bash
# Install package
pip install -e .

# Or install requirements
pip install -r requirements.txt

# Verify
python -c "from gdrive_safety_suite import GDriveSafetyManager"
```

### "Session Not Cleaning"
```bash
# MUST include --confirm flag
python gdrive_safety_cli.py cleanup --session-id SESSION_ID --confirm

# Or in Python
manager.cleanup(confirm=True)  # Not just cleanup()
```

---

## 📚 File Locations

```
gdrive-safety/
├── gdrive_safety_suite/          # Main package
│   ├── __init__.py              # Unified interface
│   ├── object_cache.py          # Caching with locks
│   ├── safety_checks.py         # Validators
│   ├── traversal.py             # Folder enumeration
│   └── privacy_cleaner.py       # Memory cleanup
├── gdrive_safety_cli.py         # CLI interface
├── gdrive_safety_skill.md       # Skill definition
├── requirements.txt             # Dependencies
├── GDRIVE_SAFETY_INSTALLATION.md # Setup guide
└── GDRIVE_SAFETY_QUICKREF.md   # This file
```

---

## 🎯 Common Use Cases

### Use Case 1: Weekly Drive Audit
```bash
#!/bin/bash
# scan_weekly.sh

python gdrive_safety_cli.py scan \
  --folder-id root \
  --max-depth 3 \
  --output weekly_scan_$(date +%Y%m%d).json

# Generate report
python gdrive_safety_cli.py report \
  --scan-results weekly_scan_*.json \
  --output weekly_report.txt
```

### Use Case 2: Team Drive Compliance
```python
# Check multiple team folders for compliance
team_folders = {
    "Marketing": "folder_id_1",
    "Engineering": "folder_id_2",
    "Finance": "folder_id_3"
}

manager = GDriveSafetyManager()

for team, folder_id in team_folders.items():
    results = manager.check_folder(folder_id)
    print(f"{team}: {results['files_found']} files, "
          f"{len(results['issues'])} issues")

manager.cleanup(confirm=True)
```

### Use Case 3: Monitor For Suspicious Changes
```python
# Compare scans over time
import json

# Load previous scan
with open('baseline_scan.json') as f:
    baseline = json.load(f)

# Run new scan
manager = GDriveSafetyManager()
current = manager.check_folder("folder_id")

# Compare
new_issues = len(current['issues']) - len(baseline['issues'])
if new_issues > 0:
    print(f"⚠️  {new_issues} new issues found!")

manager.cleanup(confirm=True)
```

---

## 📞 Getting Help

1. Check **GDRIVE_SAFETY_INSTALLATION.md** for setup issues
2. Check **Troubleshooting** section above
3. Enable debug mode and check logs
4. Open issue on GitHub with:
   - Command used
   - Error message (full output)
   - System info (OS, Python version)
   - Google Drive folder structure (if relevant)

---

**Last Updated:** 2026-07-07
**Version:** 1.0
