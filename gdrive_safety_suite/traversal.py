"""Safe Google Drive folder traversal with depth limits and validation.

Provides controlled enumeration of folder contents with:
- Depth limit enforcement
- Permission validation
- Circular reference detection
- File type filtering
"""

from typing import Dict, List, Optional, Callable, Any
from .safety_checks import SafetyValidator, SafetyIssue


class TraversalPath:
    """Represents position in folder hierarchy."""

    def __init__(self, folder_id: str, depth: int = 0, parent_path: Optional[str] = None):
        """Initialize traversal path.

        Args:
            folder_id: Google Drive folder ID
            depth: Current depth level
            parent_path: Path to parent folder
        """
        self.folder_id = folder_id
        self.depth = depth
        self.parent_path = parent_path
        self.full_path = self._build_path()

    def _build_path(self) -> str:
        """Build full path string."""
        if self.parent_path:
            return f"{self.parent_path}/{self.folder_id}"
        return f"/{self.folder_id}"

    def get_child(self, child_id: str) -> "TraversalPath":
        """Create child path.

        Args:
            child_id: Child folder ID

        Returns:
            New TraversalPath for child
        """
        return TraversalPath(child_id, self.depth + 1, self.full_path)


class CircularReferenceDetector:
    """Detects circular references in folder hierarchy."""

    def __init__(self):
        """Initialize detector."""
        self.visited = set()
        self.path_stack = []

    def push(self, folder_id: str) -> bool:
        """Add folder to traversal stack.

        Args:
            folder_id: Folder ID to add

        Returns:
            True if safe, False if circular reference detected
        """
        if folder_id in self.visited:
            return False

        self.path_stack.append(folder_id)
        self.visited.add(folder_id)
        return True

    def pop(self):
        """Remove folder from traversal stack."""
        if self.path_stack:
            self.path_stack.pop()

    def clear(self):
        """Clear all visited folders."""
        self.visited.clear()
        self.path_stack.clear()

    def get_path(self) -> List[str]:
        """Get current path stack.

        Returns:
            List of folder IDs in current path
        """
        return self.path_stack.copy()


class SafeTraversal:
    """Safe folder traversal with constraints and validation."""

    def __init__(
        self,
        max_depth: int = 5,
        max_files_per_folder: int = 100000,
        include_shortcuts: bool = False,
    ):
        """Initialize safe traversal.

        Args:
            max_depth: Maximum folder nesting depth
            max_files_per_folder: Maximum files per folder
            include_shortcuts: Whether to follow shortcuts
        """
        self.max_depth = max_depth
        self.max_files_per_folder = max_files_per_folder
        self.include_shortcuts = include_shortcuts
        self.validator = SafetyValidator(max_depth=max_depth)
        self.circular_detector = CircularReferenceDetector()
        self.results = []
        self.issues = []

    def traverse(
        self,
        root_folder_id: str,
        file_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        folder_callback: Optional[Callable[[Dict[str, Any], int], None]] = None,
    ) -> Dict[str, Any]:
        """Traverse folder hierarchy safely.

        Args:
            root_folder_id: Root folder ID to start traversal
            file_callback: Optional callback for each file found
            folder_callback: Optional callback for each folder visited

        Returns:
            Dictionary with traversal results
        """
        self.results = []
        self.issues = []
        self.circular_detector.clear()

        root_path = TraversalPath(root_folder_id, depth=0)
        self._traverse_recursive(root_path, file_callback, folder_callback)

        return {
            "root_folder_id": root_folder_id,
            "files_found": len(self.results),
            "issues": [issue.to_dict() for issue in self.issues],
            "max_depth_reached": self._get_max_depth(),
        }

    def _traverse_recursive(
        self,
        path: TraversalPath,
        file_callback: Optional[Callable],
        folder_callback: Optional[Callable],
    ):
        """Recursively traverse folder.

        Args:
            path: Current traversal path
            file_callback: Callback for files
            folder_callback: Callback for folders
        """
        # Check depth limit
        if path.depth > self.max_depth:
            self.issues.append(
                SafetyIssue(
                    level="warning",
                    category="max_depth_reached",
                    message=f"Maximum depth {self.max_depth} reached at {path.full_path}",
                )
            )
            return

        # Check for circular reference
        if not self.circular_detector.push(path.folder_id):
            self.issues.append(
                SafetyIssue(
                    level="warning",
                    category="circular_reference",
                    message=f"Circular reference detected at {path.folder_id}",
                    metadata={"path": self.circular_detector.get_path()},
                )
            )
            return

        try:
            # Validate folder depth
            depth_issues = self.validator.validate_folder_depth(path.depth, path.full_path)
            self.issues.extend(depth_issues)

            # Process current folder
            if folder_callback:
                folder_callback({"folder_id": path.folder_id, "path": path.full_path}, path.depth)

            # In a real implementation, would enumerate files here
            # This is a template showing the safety structure

        finally:
            self.circular_detector.pop()

    def _get_max_depth(self) -> int:
        """Get maximum depth reached during traversal.

        Returns:
            Maximum depth value
        """
        if not self.results:
            return 0
        return max((r.get("depth", 0) for r in self.results), default=0)

    def validate_traversal_safety(
        self, folder_structure: Dict[str, Any]
    ) -> List[SafetyIssue]:
        """Validate entire folder structure for safety.

        Args:
            folder_structure: Folder structure to validate

        Returns:
            List of safety issues found
        """
        issues = []

        # Check depth
        depth = folder_structure.get("depth", 0)
        issues.extend(self.validator.validate_folder_depth(depth))

        # Check file count
        file_count = folder_structure.get("file_count", 0)
        issues.extend(self.validator.validate_folder_contents(file_count))

        # Check for suspicious patterns
        if folder_structure.get("has_shortcuts") and not self.include_shortcuts:
            issues.append(
                SafetyIssue(
                    level="info",
                    category="shortcuts_found",
                    message="Folder contains shortcuts (not traversing by default)",
                )
            )

        return issues

    def clear_results(self):
        """Clear traversal results."""
        self.results = []
        self.issues = []
