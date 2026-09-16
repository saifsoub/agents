"""Safety validators for unusual file behaviors and edge cases.

Handles:
- Symlinks and shortcuts
- Permission issues
- Large files and deep nesting
- Corrupted or malformed metadata
"""

from typing import Any, Dict, List, Optional
from enum import Enum


class FileTypeCategory(Enum):
    """Categories for file type classification."""

    REGULAR_FILE = "regular"
    FOLDER = "folder"
    SHORTCUT = "shortcut"
    SYMLINK = "symlink"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"


class SafetyIssue:
    """Represents a single safety concern found during validation."""

    def __init__(
        self,
        level: str,
        category: str,
        message: str,
        file_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize safety issue.

        Args:
            level: "error", "warning", or "info"
            category: Issue category (e.g., "permission", "symlink")
            message: Human-readable description
            file_id: ID of problematic file (if applicable)
            metadata: Additional context
        """
        self.level = level
        self.category = category
        self.message = message
        self.file_id = file_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "file_id": self.file_id,
            "metadata": self.metadata,
        }


class FileTypeChecker:
    """Detects and categorizes file types, including unusual ones."""

    def __init__(self):
        """Initialize file type checker."""
        self.suspicious_patterns = [
            ".lnk",  # Windows shortcuts
            ".url",  # Internet shortcuts
        ]
        self.suspicious_mimetypes = [
            "application/x-msdownload",  # Executable
            "application/x-msdos-program",  # DOS executable
        ]

    def classify(self, file_metadata: Dict[str, Any]) -> FileTypeCategory:
        """Classify file type based on metadata.

        Args:
            file_metadata: File metadata from Google Drive

        Returns:
            FileTypeCategory
        """
        # Handle Google Shortcuts
        if file_metadata.get("mimeType") == "application/vnd.google-apps.shortcut":
            return FileTypeCategory.SHORTCUT

        # Handle symlinks (indicated by specific properties)
        if self._looks_like_symlink(file_metadata):
            return FileTypeCategory.SYMLINK

        # Handle folders
        if file_metadata.get("mimeType") == "application/vnd.google-apps.folder":
            return FileTypeCategory.FOLDER

        # Check for suspicious files
        if self._is_suspicious(file_metadata):
            return FileTypeCategory.SUSPICIOUS

        # Regular files
        if file_metadata.get("mimeType", "").startswith("application/"):
            return FileTypeCategory.REGULAR_FILE

        if file_metadata.get("mimeType", "").startswith("image/"):
            return FileTypeCategory.REGULAR_FILE

        if file_metadata.get("mimeType", "").startswith("text/"):
            return FileTypeCategory.REGULAR_FILE

        return FileTypeCategory.UNKNOWN

    def _looks_like_symlink(self, metadata: Dict[str, Any]) -> bool:
        """Heuristic check for symlink-like properties.

        Args:
            metadata: File metadata

        Returns:
            True if file looks like a symlink
        """
        # Symlinks often have minimal size and specific properties
        size = metadata.get("size", 0)
        name = metadata.get("name", "")

        # Very small size with link-like name
        if size < 512 and any(x in name.lower() for x in ["link", "alias"]):
            return True

        return False

    def _is_suspicious(self, metadata: Dict[str, Any]) -> bool:
        """Check for suspicious file patterns.

        Args:
            metadata: File metadata

        Returns:
            True if file is suspicious
        """
        name = metadata.get("name", "").lower()
        mimetype = metadata.get("mimeType", "").lower()

        # Check file extension patterns
        for pattern in self.suspicious_patterns:
            if name.endswith(pattern):
                return True

        # Check MIME type patterns
        for suspicious_mime in self.suspicious_mimetypes:
            if mimetype == suspicious_mime:
                return True

        return False


class SafetyValidator:
    """Comprehensive safety validation for Google Drive operations."""

    def __init__(
        self,
        max_file_size_mb: int = 5000,
        max_depth: int = 10,
        max_files_per_folder: int = 100000,
    ):
        """Initialize validator with safety constraints.

        Args:
            max_file_size_mb: Maximum file size in MB
            max_depth: Maximum folder nesting depth
            max_files_per_folder: Maximum files in single folder
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_depth = max_depth
        self.max_files_per_folder = max_files_per_folder
        self.file_checker = FileTypeChecker()
        self.issues = []

    def validate_file(self, file_metadata: Dict[str, Any]) -> List[SafetyIssue]:
        """Validate single file for safety issues.

        Args:
            file_metadata: File metadata from Google Drive

        Returns:
            List of SafetyIssue objects
        """
        issues = []
        file_id = file_metadata.get("id", "unknown")

        # Check file size
        size_bytes = int(file_metadata.get("size", 0))
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            issues.append(
                SafetyIssue(
                    level="warning",
                    category="file_size",
                    message=f"File exceeds size limit: {size_mb:.2f}MB",
                    file_id=file_id,
                )
            )

        # Check file type
        file_type = self.file_checker.classify(file_metadata)
        if file_type == FileTypeCategory.SUSPICIOUS:
            issues.append(
                SafetyIssue(
                    level="warning",
                    category="suspicious_file",
                    message="File type is suspicious and should be reviewed",
                    file_id=file_id,
                    metadata={"file_type": file_type.value},
                )
            )

        # Check for shortcut/symlink
        if file_type in [FileTypeCategory.SHORTCUT, FileTypeCategory.SYMLINK]:
            issues.append(
                SafetyIssue(
                    level="info",
                    category="shortcut",
                    message=f"File is a {file_type.value}",
                    file_id=file_id,
                )
            )

        # Check permissions
        if not file_metadata.get("webViewLink"):
            issues.append(
                SafetyIssue(
                    level="warning",
                    category="permission",
                    message="File has restricted access/visibility",
                    file_id=file_id,
                )
            )

        return issues

    def validate_folder_depth(
        self, current_depth: int, path: str = ""
    ) -> List[SafetyIssue]:
        """Validate folder nesting depth.

        Args:
            current_depth: Current depth level
            path: Optional folder path

        Returns:
            List of SafetyIssue objects
        """
        issues = []

        if current_depth > self.max_depth:
            issues.append(
                SafetyIssue(
                    level="warning",
                    category="depth_limit",
                    message=f"Folder nesting exceeds limit: depth {current_depth}",
                    metadata={"current_depth": current_depth, "max_depth": self.max_depth},
                )
            )

        if current_depth > self.max_depth * 0.8:
            issues.append(
                SafetyIssue(
                    level="info",
                    category="depth_warning",
                    message=f"Folder nesting approaching limit: {current_depth}/{self.max_depth}",
                    metadata={"current_depth": current_depth, "max_depth": self.max_depth},
                )
            )

        return issues

    def validate_folder_contents(
        self, file_count: int, folder_id: Optional[str] = None
    ) -> List[SafetyIssue]:
        """Validate number of files in folder.

        Args:
            file_count: Number of files in folder
            folder_id: Optional folder ID

        Returns:
            List of SafetyIssue objects
        """
        issues = []

        if file_count > self.max_files_per_folder:
            issues.append(
                SafetyIssue(
                    level="warning",
                    category="large_folder",
                    message=f"Folder has too many files: {file_count}",
                    file_id=folder_id,
                    metadata={"file_count": file_count, "limit": self.max_files_per_folder},
                )
            )

        if file_count > self.max_files_per_folder * 0.8:
            issues.append(
                SafetyIssue(
                    level="info",
                    category="folder_size_warning",
                    message=f"Folder size approaching limit: {file_count} files",
                    file_id=folder_id,
                )
            )

        return issues

    def clear_issues(self):
        """Clear accumulated issues."""
        self.issues = []

    def get_all_issues(self) -> List[SafetyIssue]:
        """Get all accumulated issues.

        Returns:
            List of all SafetyIssue objects
        """
        return self.issues.copy()
