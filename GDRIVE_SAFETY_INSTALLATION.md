# Google Drive Safety Suite - Installation & Usage Guide

Complete guide for installing and using the Google Drive Safety Suite as a skill with Claude Code CLI, local agents, or any CLI-capable model.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [CLI Usage](#cli-usage)
5. [Python API](#python-api)
6. [Claude Code Integration](#claude-code-integration)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Option 1: Claude Code CLI (Easiest)

```bash
# Install the skill
npx skills add gdrive-safety

# Run a scan
claude gdrive:scan --folder-id YOUR_FOLDER_ID

# View results
claude gdrive:results

# Cleanup
claude gdrive:cleanup --session-id YOUR_SESSION_ID --confirm
```

### Option 2: Python CLI

```bash
# Install dependencies
pip install -r requirements.txt

# Scan a folder
python gdrive_safety_cli.py scan --folder-id YOUR_FOLDER_ID

# Generate report
python gdrive_safety_cli.py report --scan-results results.json

# Cleanup
python gdrive_safety_cli.py cleanup --session-id YOUR_SESSION_ID --confirm
```

### Option 3: Direct Python Import

```python
from gdrive_safety_suite import GDriveSafetyManager

manager = GDriveSafetyManager(max_depth=5, enable_audit_log=True)
results = manager.check_folder("folder_id")
print(f"Files analyzed: {results['files_found']}")
manager.cleanup(confirm=True)
```

---

## 📦 Installation Methods

### Method 1: As a Claude Code Skill

**Step 1: Clone or download the skill**
```bash
git clone https://github.com/yourusername/gdrive-safety-skill.git
cd gdrive-safety-skill
```

**Step 2: Install globally**
```bash
npm install -g .
```

**Step 3: Use with Claude Code CLI**
```bash
# List installed skills
claude skills list | grep gdrive

# Run commands
claude gdrive:scan --folder-id FOLDER_ID
```

**Step 4: Or add to a local project**
```bash
# In your project directory
npx skills add /path/to/gdrive-safety-skill

# Then use
claude gdrive:scan --folder-id FOLDER_ID
```

### Method 2: As a Python Package (Recommended)

**Step 1: Install from source**
```bash
# Navigate to the skill directory
cd gdrive_safety_suite

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

**Step 2: Verify installation**
```bash
python -c "from gdrive_safety_suite import GDriveSafetyManager; print('✓ Installed')"
```

**Step 3: Use anywhere**
```python
from gdrive_safety_suite import GDriveSafetyManager
# Works anywhere in your Python environment
```

### Method 3: CLI Tool Only

**Step 1: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Make CLI executable**
```bash
chmod +x gdrive_safety_cli.py

# Create symlink for global access (optional)
sudo ln -s $(pwd)/gdrive_safety_cli.py /usr/local/bin/gdrive-safety
```

**Step 3: Use CLI**
```bash
# Direct usage
python gdrive_safety_cli.py scan --folder-id FOLDER_ID

# Or with symlink
gdrive-safety scan --folder-id FOLDER_ID
```

### Method 4: Docker (For Isolated Environment)

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY gdrive_safety_suite/ ./gdrive_safety_suite/
COPY gdrive_safety_cli.py .

ENTRYPOINT ["python", "gdrive_safety_cli.py"]
```

**Step 2: Build and run**
```bash
# Build image
docker build -t gdrive-safety .

# Run scan
docker run -v ~/.config/gcloud:/root/.config/gcloud \
  gdrive-safety scan --folder-id FOLDER_ID
```

---

## ⚙️ Configuration

### Google Drive API Setup

**Step 1: Create Google Cloud Project**
```bash
# Visit: https://console.cloud.google.com/
# 1. Create new project
# 2. Enable Google Drive API
# 3. Create OAuth 2.0 credentials (Desktop app)
# 4. Download as JSON
```

**Step 2: Set credentials**
```bash
# Option A: Environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Option B: Place in home directory
cp credentials.json ~/.gdrive_safety/credentials.json

# Option C: Specify in code
manager = GDriveSafetyManager(
    credentials_file='/path/to/credentials.json'
)
```

**Step 3: Test connection**
```bash
python -c "
from google.auth import default
from googleapiclient.discovery import build

creds, _ = default()
drive = build('drive', 'v3', credentials=creds)
print('✓ Connected to Google Drive')
"
```

### Safety Configuration

**Default limits:**
```python
from gdrive_safety_suite import SafetyValidator

validator = SafetyValidator(
    max_file_size_mb=5000,      # 5GB file size limit
    max_depth=10,               # 10-level nesting limit
    max_files_per_folder=100000 # 100k files per folder
)
```

**Custom limits:**
```python
# Stricter settings
validator = SafetyValidator(
    max_file_size_mb=1000,      # 1GB limit
    max_depth=5,                # 5-level limit
    max_files_per_folder=10000  # 10k files limit
)
```

**Environment variables:**
```bash
# Optional customization
export GDRIVE_SAFETY_CACHE_DIR=/custom/cache/path
export GDRIVE_SAFETY_MAX_DEPTH=3
export GDRIVE_SAFETY_MAX_FILES=50000
export GDRIVE_SAFETY_AUDIT_LOG=true
export GDRIVE_SAFETY_ENCRYPT=true
```

---

## 🖥️ CLI Usage

### Basic Scan

```bash
# Scan a folder
python gdrive_safety_cli.py scan --folder-id 1XAEJqKxoZ0gv2XGmdGaUgJD_uhjP1BR8

# Output:
# 🔍 GOOGLE DRIVE SAFETY SCAN
# 📁 Folder ID: 1XAEJqKxoZ0gv2XGmdGaUgJD_uhjP1BR8
# 📊 Files Found: 28
# ⚠️  Issues Detected: 28 (permission issues)
# ✅ SCAN COMPLETE
```

### Scan with Custom Depth

```bash
# Shallow scan (faster, less data)
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 2

# Deep scan (slower, more thorough)
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 10
```

### Save Results

```bash
# Save to JSON file
python gdrive_safety_cli.py scan \
  --folder-id FOLDER_ID \
  --output results.json

# Then generate report
python gdrive_safety_cli.py report \
  --scan-results results.json \
  --output report.txt
```

### Cleanup Session

```bash
# With confirmation
python gdrive_safety_cli.py cleanup \
  --session-id e259e2dc-0bdd-4ea7-ab48-59c219754228 \
  --confirm

# Or interactive (will prompt)
python gdrive_safety_cli.py cleanup \
  --session-id YOUR_SESSION_ID
```

### Validate Single File

```bash
# Validate file metadata
python gdrive_safety_cli.py validate --file metadata.json

# Output:
# 📋 FILE VALIDATION
# File: example.pdf
# Type: regular
# Size: 1048576 bytes
# Issues Found: 0
# ✅ No issues found
```

---

## 🐍 Python API

### Basic Usage

```python
from gdrive_safety_suite import GDriveSafetyManager

# Initialize
manager = GDriveSafetyManager(
    max_depth=5,
    enable_audit_log=True
)

# Scan folder
results = manager.check_folder("folder_id")

# Process results
print(f"Files found: {results['files_found']}")
for issue in results['issues']:
    print(f"  • {issue['category']}: {issue['message']}")

# Cleanup (requires confirmation)
manager.cleanup(confirm=True)
```

### Advanced: Custom Validators

```python
from gdrive_safety_suite import SafetyValidator, FileTypeChecker

# Create validators
validator = SafetyValidator(max_file_size_mb=2000, max_depth=3)
checker = FileTypeChecker()

# Validate files
for file in files:
    # Classify type
    file_type = checker.classify(file)
    print(f"Type: {file_type.value}")
    
    # Get issues
    issues = validator.validate_file(file)
    if issues:
        for issue in issues:
            print(f"  ⚠️  {issue.message}")
```

### Advanced: Custom Sessions

```python
from gdrive_safety_suite import SessionMemory, PrivacyCleaner

# Track in custom session
session = SessionMemory()
sid = session.start_session()

# Store data
session.track_metadata(sid, {"folder": "My Docs"})
session.log_access(sid, "list", {"count": 100})

# Get summary
summary = session.get_session_summary(sid)
print(f"Files tracked: {summary['files_tracked']}")

# Cleanup
cleaner = PrivacyCleaner()
cleaner.cleanup_session(sid, confirm=True)
```

### Advanced: Async Processing

```python
import asyncio
from gdrive_safety_suite import GDriveSafetyManager

async def scan_multiple():
    folders = [
        "folder_id_1",
        "folder_id_2", 
        "folder_id_3"
    ]
    
    tasks = []
    for fid in folders:
        manager = GDriveSafetyManager()
        task = asyncio.create_task(
            scan_folder_async(manager, fid)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

async def scan_folder_async(manager, folder_id):
    # Simulate async operation
    await asyncio.sleep(0.1)
    return manager.check_folder(folder_id)

# Run
results = asyncio.run(scan_multiple())
```

---

## 🤖 Claude Code Integration

### Using as a Skill in Claude Code

**File: `~/.claude/skills/gdrive-safety/skill.md`**
```markdown
---
name: gdrive-safety
description: Scan and analyze Google Drive for safety issues
---

# Google Drive Safety Skill
...
```

**Usage in Claude Code:**
```bash
# Activate skill
/gdrive-safety

# Run scan
/gdrive-safety scan --folder-id YOUR_FOLDER_ID

# Or invoke Claude Code commands
claude gdrive:scan --folder-id FOLDER_ID --max-depth 5 --output results.json
```

### Local Agent Integration

**Python Agent Example:**
```python
from gdrive_safety_suite import GDriveSafetyManager

class GoogleDriveAgent:
    def __init__(self):
        self.manager = GDriveSafetyManager()
    
    def handle_safety_check(self, folder_id):
        """Handle safety check request"""
        results = self.manager.check_folder(folder_id)
        
        # Process results
        report = self._generate_report(results)
        return report
    
    def _generate_report(self, results):
        # Generate human-friendly report
        return f"Analyzed {results['files_found']} files"
```

---

## 🔧 Troubleshooting

### Issue: "API quota exceeded"

**Cause:** Too many requests to Google Drive API
**Solution:**
```bash
# Reduce depth and files per scan
python gdrive_safety_cli.py scan \
  --folder-id FOLDER_ID \
  --max-depth 2

# Wait and retry later
sleep 3600
```

### Issue: "Permission denied" or "Access not configured"

**Cause:** Missing or invalid credentials
**Solution:**
```bash
# Check credentials file
ls -la ~/.gdrive_safety/credentials.json

# Set correct environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/.gdrive_safety/credentials.json

# Test connection
python -c "from google.auth import default; print(default())"
```

### Issue: "Session memory not clearing"

**Cause:** Missing confirmation flag
**Solution:**
```bash
# Must include --confirm flag
python gdrive_safety_cli.py cleanup \
  --session-id YOUR_SESSION_ID \
  --confirm
```

### Issue: "ModuleNotFoundError: No module named 'gdrive_safety_suite'"

**Cause:** Package not installed
**Solution:**
```bash
# Install from source
pip install -e /path/to/gdrive-safety-skill

# Or install dependencies
pip install -r requirements.txt

# Verify
python -c "from gdrive_safety_suite import GDriveSafetyManager"
```

### Issue: "No results generated"

**Cause:** Folder may be empty or inaccessible
**Solution:**
```bash
# Check folder ID is correct
# Verify you have access to folder
# Try with Google Drive root
python gdrive_safety_cli.py scan --folder-id root
```

---

## 📊 Performance Optimization

### For Large Folders

```bash
# Use shallow scan
python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 2

# Or scan specific subfolder instead
python gdrive_safety_cli.py scan --folder-id SUBFOLDER_ID --max-depth 5
```

### For Multiple Scans

```python
# Reuse manager instance
manager = GDriveSafetyManager()

folders = ["folder1", "folder2", "folder3"]
for folder_id in folders:
    results = manager.check_folder(folder_id)
    # Process...
```

### Memory Management

```python
# Clear cache between scans
manager.cache.clear()
manager.session.clear()

# Or create new manager
manager = GDriveSafetyManager()
```

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/ -v

# Run specific test
pytest tests/test_safety_checks.py -v

# Run with coverage
pytest tests/ --cov=gdrive_safety_suite --cov-report=html
```

---

## 📚 More Resources

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Claude Code CLI Guide](https://github.com/anthropics/claude-code)
- [Safety Suite Architecture](./ARCHITECTURE.md)
- [API Reference](./API_REFERENCE.md)

---

## 📝 License

MIT License - See LICENSE file

---

**Questions?** Check the troubleshooting section or open an issue on GitHub.
