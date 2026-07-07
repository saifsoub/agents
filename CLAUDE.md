# CLAUDE.md

@AGENTS.md

## Google Drive Safety Suite

Progressive scripts for safe, privacy-preserving Google Drive folder checking. All operations are **isolated to a single locked folder** (`gdrive_safety_suite/`) with explicit confirmation gates and memory cleanup.

### Overview

The suite provides evolving capabilities:
1. **Initial Level**: Basic catch & cache with thread-safe locking
2. **Evolving Level**: Validation of unusual file behaviors
3. **Advanced Level**: Safe folder traversal with circular reference detection
4. **Final Level**: Privacy-preserving memory cleanup with audit logs

### Quick Start

```python
from gdrive_safety_suite import GDriveSafetyManager

# Initialize manager
manager = GDriveSafetyManager(max_depth=5, enable_audit_log=True)

# Check a folder (returns results immediately, no data persists)
results = manager.check_folder(folder_id="your_folder_id")

# Process results...

# Cleanup: EXPLICIT CONFIRMATION REQUIRED
# This clears all cached paths, metadata, and session data
confirmed = manager.cleanup(confirm=True)
```

### Core Components

#### 1. Object Cache with Locking (`object_cache.py`)

Thread-safe caching of Google Drive objects with exclusive locks:

```python
from gdrive_safety_suite import ObjectCache

cache = ObjectCache()

# Store object with lock
obj = cache.put("file_123", file_data)

# Acquire lock for exclusive access
if cache.acquire_lock("file_123", timeout=5.0):
    try:
        # Safe concurrent access
        data = cache.get("file_123")
    finally:
        cache.release_lock("file_123")

# Clear cache and locks
cache.clear()
```

**Features:**
- Thread-safe with RLock
- Automatic TTL (default 1 hour)
- Per-object locking for safe concurrent ops
- Memory-efficient storage
- Access tracking for audit logs

#### 2. Safety Validators (`safety_checks.py`)

Detect and handle unusual file behaviors:

```python
from gdrive_safety_suite import SafetyValidator, FileTypeChecker

validator = SafetyValidator(
    max_file_size_mb=5000,
    max_depth=10,
    max_files_per_folder=100000
)

# Validate individual files
issues = validator.validate_file(file_metadata)

# Check nesting depth
depth_issues = validator.validate_folder_depth(current_depth=5)

# Validate folder contents count
size_issues = validator.validate_folder_contents(file_count=50000)

# Get all accumulated issues
all_issues = validator.get_all_issues()
```

**Handles:**
- **Symlinks & Shortcuts**: Detects and flags Google Shortcuts and symlink-like files
- **Permission Issues**: Identifies files with restricted access
- **Large Files**: Warns when files exceed size limits
- **Deep Nesting**: Tracks and limits folder depth
- **Suspicious Types**: Flags unusual file types and patterns

#### 3. Safe Traversal (`traversal.py`)

Folder enumeration with safety constraints:

```python
from gdrive_safety_suite import SafeTraversal

traversal = SafeTraversal(max_depth=5, include_shortcuts=False)

# Traverse with callbacks
def on_file(file_metadata):
    print(f"Found: {file_metadata['name']}")

def on_folder(folder_info, depth):
    print(f"Folder depth {depth}: {folder_info['folder_id']}")

results = traversal.traverse(
    root_folder_id="your_folder_id",
    file_callback=on_file,
    folder_callback=on_folder
)
```

**Features:**
- Depth limit enforcement
- Circular reference detection
- Permission validation before access
- Shortcut handling (skip by default)
- File type filtering
- Comprehensive issue reporting

#### 4. Privacy & Memory Cleanup (`privacy_cleaner.py`)

**CRITICAL**: All file paths, metadata, and session data are cleared after operations.

```python
from gdrive_safety_suite import PrivacyCleaner, SessionMemory

# Track operations in isolated session
session_mem = SessionMemory()
session_id = session_mem.start_session()

# Store data (only in session memory, nowhere else)
session_mem.track_file_path(session_id, "/path/to/file")
session_mem.track_metadata(session_id, {"name": "file.txt"})
session_mem.log_access(session_id, "list", {"count": 100})

# Get session summary (no file paths exposed)
summary = session_mem.get_session_summary(session_id)
# Output: {"files_tracked": 1, "metadata_entries": 1, ...}

# Cleanup with EXPLICIT confirmation
cleaner = PrivacyCleaner(enable_audit_log=True)

# Step 1: Request confirmation
msg = cleaner.request_cleanup_confirmation(session_id)
# User must confirm...

# Step 2: Cleanup (zeros memory, saves audit)
cleaner.cleanup_session(session_id, confirm=True, save_audit=True)

# Audit log (no file paths, only operation types)
status = cleaner.get_cleanup_status()
```

**Privacy Guarantees:**
- ✅ Session isolation (no persistent state)
- ✅ Explicit confirmation gate on cleanup
- ✅ No file paths in memory after cleanup
- ✅ No metadata persisted
- ✅ Audit logs encrypted (if enabled)
- ✅ No operation logs contain file names/paths

### Progressive Enhancement Pattern

The suite evolves capabilities as you use it:

**Phase 1: Basic Listing**
- Initialize manager
- Enumerate folder contents
- Catch basic issues (permissions, file types)

**Phase 2: Safe Caching**
- Cache objects with thread-safe locks
- Validate file types and sizes
- Track unusual behaviors

**Phase 3: Deep Traversal**
- Handle deep folder nesting
- Detect circular references
- Validate at each depth level

**Phase 4: Privacy Cleanup**
- Clear all cached data
- Save encrypted audit trail
- Confirm cleanup explicitly

### Safety Constraints

Default safety limits (configurable):

| Constraint | Default | Configurable |
|-----------|---------|--------------|
| Max folder depth | 5 levels | Yes |
| Max file size | 5000 MB | Yes |
| Max files per folder | 100,000 | Yes |
| Cache TTL | 1 hour | Yes |
| Session isolation | Always | No |
| Confirmation gate | Required | No |

### Best Practices

1. **Always use within a session**
   ```python
   manager = GDriveSafetyManager()
   session_id = manager.session.start_session()
   # ... operations ...
   manager.cleanup(confirm=True)
   ```

2. **Handle safety issues**
   ```python
   for issue in results["issues"]:
       if issue["level"] == "warning":
           logger.warning(issue["message"])
   ```

3. **Respect depth limits**
   ```python
   if results["max_depth_reached"] > manager.traversal.max_depth:
       logger.warning("Folder nesting exceeds recommended limit")
   ```

4. **Always confirm cleanup**
   ```python
   # Get user confirmation before calling
   if user_confirms_cleanup():
       manager.cleanup(confirm=True)
   ```

### File Structure

```
gdrive_safety_suite/
├── __init__.py              # Unified interface (GDriveSafetyManager)
├── object_cache.py          # Thread-safe caching with locks
├── safety_checks.py         # File type and behavior validation
├── traversal.py             # Safe folder enumeration
└── privacy_cleaner.py       # Memory cleanup and audit logs
```

### Examples

#### Example 1: Check folder, collect results, cleanup

```python
from gdrive_safety_suite import GDriveSafetyManager

manager = GDriveSafetyManager(max_depth=4)
results = manager.check_folder("folder_123")

print(f"Files found: {results['files_found']}")
for issue in results['issues']:
    if issue['level'] == 'warning':
        print(f"Warning: {issue['message']}")

# User confirms they're done
user_confirms = input("Clear session memory? [yes/no]: ")
if user_confirms.lower() == "yes":
    manager.cleanup(confirm=True)
```

#### Example 2: Cache validation with locking

```python
cache = ObjectCache()

# Multiple threads can safely access cached files
obj = cache.put("file_456", file_metadata)

# Thread 1
if cache.acquire_lock("file_456"):
    try:
        data = cache.get("file_456")
        # Safe to modify or read
    finally:
        cache.release_lock("file_456")

# Memory cleanup
cache.clear()
```

#### Example 3: Validate before traversal

```python
validator = SafetyValidator()

# Check file before including in results
issues = validator.validate_file(file_metadata)
for issue in issues:
    if issue['category'] == 'suspicious_file':
        logger.warning(f"Skipping suspicious file: {issue['message']}")
        continue

# Safe to process this file
```

### Environment Configuration

No special environment variables required. The suite uses:
- `/tmp/gdrive_cache/` for lock files (configurable)
- In-memory caching for session data
- Optional audit logs (encrypted if enabled)

### Testing

All components are self-contained and testable:

```bash
# Test individual components
python -c "from gdrive_safety_suite import ObjectCache; c = ObjectCache(); print(c.get_stats())"

# Test privacy cleanup
python -c "from gdrive_safety_suite import PrivacyCleaner; p = PrivacyCleaner(); print(p.get_cleanup_status())"
```

### Limitations & Known Behaviors

1. **No actual Google Drive API calls** - This suite provides the structure and safety mechanisms. Integrate with Google Drive SDK for actual operations.
2. **Session isolation is enforced** - Cannot persist data across sessions by design.
3. **Audit logs are optional** - Disabled by default if you don't need them.
4. **Cleanup requires explicit confirmation** - Prevents accidental data loss.

---
