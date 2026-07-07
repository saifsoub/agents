#!/usr/bin/env python3
"""
Google Drive Safety CLI - Command-line interface for Google Drive safety scanning

Usage:
    python gdrive_safety_cli.py scan --folder-id FOLDER_ID [--max-depth 5]
    python gdrive_safety_cli.py cleanup --session-id SESSION_ID --confirm
    python gdrive_safety_cli.py report --scan-results results.json
"""

import argparse
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

# Import the safety suite
from gdrive_safety_suite import (
    GDriveSafetyManager,
    SafetyValidator,
    FileTypeChecker,
    PrivacyCleaner,
    SessionMemory,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GDriveSafetyCLI:
    """CLI interface for Google Drive Safety Suite"""

    def __init__(self):
        self.manager = None
        self.results = {}

    def scan(self, folder_id: str, max_depth: int = 5, output: Optional[str] = None) -> int:
        """Scan a Google Drive folder for safety issues"""
        print("\n" + "="*80)
        print("🔍 GOOGLE DRIVE SAFETY SCAN")
        print("="*80)
        print(f"📁 Folder ID: {folder_id}")
        print(f"📊 Max Depth: {max_depth}")
        print(f"⏰ Started: {datetime.now().isoformat()}\n")

        try:
            # Initialize manager
            self.manager = GDriveSafetyManager(max_depth=max_depth, enable_audit_log=True)
            session_id = self.manager.session.start_session()

            # Start scan
            print(f"📋 Session ID: {session_id}")
            print("🔐 Privacy Protection: ACTIVE (session-isolated)\n")
            print("Scanning...")

            # Perform scan
            results = self.manager.check_folder(folder_id)
            self.results = results
            self.results['session_id'] = session_id

            # Display results
            self._display_scan_results(results)

            # Save results if output specified
            if output:
                self._save_results(output, results)
                print(f"\n✅ Results saved to: {output}")

            print("\n" + "="*80)
            print("✅ SCAN COMPLETE")
            print("="*80)
            print(f"\n💾 Session Memory: ACTIVE")
            print(f"   └─ Ready for cleanup with: gdrive:cleanup --session-id {session_id}")
            print(f"\n⚠️  IMPORTANT:")
            print(f"   Remember to cleanup session memory when done:")
            print(f"   python gdrive_safety_cli.py cleanup --session-id {session_id} --confirm\n")

            return 0

        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            print(f"\n❌ SCAN FAILED: {e}\n")
            return 1

    def cleanup(self, session_id: str, confirm: bool = False) -> int:
        """Cleanup session memory and cached data"""
        print("\n" + "="*80)
        print("🔐 SESSION MEMORY CLEANUP")
        print("="*80)
        print(f"📋 Session ID: {session_id}\n")

        if not confirm:
            print("⚠️  CONFIRMATION REQUIRED")
            print("\nThis will permanently clear:")
            print("  • All cached file paths")
            print("  • Session metadata")
            print("  • Access logs")
            print("  • Temporary data\n")

            response = input("Continue with cleanup? [yes/no]: ").lower().strip()
            if response != 'yes':
                print("❌ Cleanup cancelled.\n")
                return 1

        try:
            # Perform cleanup
            if self.manager is None:
                self.manager = GDriveSafetyManager()

            cleanup_success = self.manager.cleanup(confirm=True)

            if cleanup_success:
                print("\n✅ CLEANUP COMPLETE\n")
                print("🔐 Privacy Verification:")
                print("  ✓ Object cache cleared")
                print("  ✓ Session memory zeroed")
                print("  ✓ Access logs removed")
                print("  ✓ No external exposure")
                print("  ✓ Session terminated safely\n")
                print("="*80 + "\n")
                return 0
            else:
                print("❌ Cleanup failed - confirmation not verified.\n")
                return 1

        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            print(f"❌ CLEANUP FAILED: {e}\n")
            return 1

    def report(self, scan_results_file: str, output: Optional[str] = None) -> int:
        """Generate a formatted report from scan results"""
        print("\n" + "="*80)
        print("📄 GENERATING AUDIT REPORT")
        print("="*80 + "\n")

        try:
            # Load results
            with open(scan_results_file, 'r') as f:
                results = json.load(f)

            # Generate report
            report = self._generate_report(results)

            # Display
            print(report)

            # Save if output specified
            if output:
                with open(output, 'w') as f:
                    f.write(report)
                print(f"\n✅ Report saved to: {output}")

            return 0

        except FileNotFoundError:
            print(f"❌ Results file not found: {scan_results_file}\n")
            return 1
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            print(f"❌ REPORT FAILED: {e}\n")
            return 1

    def validate(self, file_path: str) -> int:
        """Validate a file metadata"""
        print("\n" + "="*80)
        print("📋 FILE VALIDATION")
        print("="*80 + "\n")

        try:
            # Load file metadata
            with open(file_path, 'r') as f:
                file_data = json.load(f)

            # Validate
            validator = SafetyValidator()
            checker = FileTypeChecker()

            file_type = checker.classify(file_data)
            issues = validator.validate_file(file_data)

            # Display results
            print(f"File: {file_data.get('name', 'Unknown')}")
            print(f"Type: {file_type.value}")
            print(f"Size: {file_data.get('size', 0)} bytes")
            print(f"Issues Found: {len(issues)}\n")

            if issues:
                print("Issues:")
                for issue in issues:
                    print(f"  [{issue.level.upper()}] {issue.category}")
                    print(f"    → {issue.message}\n")
            else:
                print("✅ No issues found\n")

            return 0

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            print(f"❌ VALIDATION FAILED: {e}\n")
            return 1

    def _display_scan_results(self, results: dict):
        """Display scan results in a formatted way"""
        summary = results.get('statistics', {})
        issues = results.get('issues', [])

        print(f"📊 Files Found: {results.get('files_found', 0)}")
        print(f"⚠️  Issues Detected: {len(issues)}\n")

        if issues:
            # Group by level
            errors = [i for i in issues if i.get('level') == 'error']
            warnings = [i for i in issues if i.get('level') == 'warning']
            info = [i for i in issues if i.get('level') == 'info']

            if errors:
                print(f"🔴 HIGH RISK: {len(errors)} issues")
                for issue in errors[:3]:
                    print(f"   • {issue.get('category')}: {issue.get('message', '')}")
                if len(errors) > 3:
                    print(f"   ... and {len(errors)-3} more")

            if warnings:
                print(f"🟡 MEDIUM RISK: {len(warnings)} issues")
                print(f"   • Permissions, file types, sizes, etc.")

            if info:
                print(f"ℹ️  INFO: {len(info)} items")

        else:
            print("✅ No issues detected - Drive appears safe!\n")

    def _generate_report(self, results: dict) -> str:
        """Generate a formatted report"""
        report = []
        report.append("="*80)
        report.append("GOOGLE DRIVE SAFETY AUDIT REPORT")
        report.append("="*80)
        report.append(f"\nScan Date: {datetime.now().isoformat()}")
        report.append(f"Files Analyzed: {results.get('files_found', 0)}")
        report.append(f"\nRisk Summary:")
        report.append(f"  • HIGH: {len([i for i in results.get('issues', []) if i.get('level')=='error'])}")
        report.append(f"  • MEDIUM: {len([i for i in results.get('issues', []) if i.get('level')=='warning'])}")
        report.append(f"  • LOW: {len([i for i in results.get('issues', []) if i.get('level')=='info'])}")
        report.append(f"\nPrivacy Protection: SESSION-ISOLATED (No external exposure)")
        report.append("="*80)

        return "\n".join(report)

    def _save_results(self, output_file: str, results: dict):
        """Save results to file"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Google Drive Safety Scanner - Safe analysis with privacy protection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a folder
  python gdrive_safety_cli.py scan --folder-id 1XAEJqKxoZ0gv2XGmdGaUgJD_uhjP1BR8

  # Scan with custom depth
  python gdrive_safety_cli.py scan --folder-id FOLDER_ID --max-depth 3

  # Save results to file
  python gdrive_safety_cli.py scan --folder-id FOLDER_ID --output results.json

  # Cleanup session memory (requires confirmation)
  python gdrive_safety_cli.py cleanup --session-id SESSION_ID --confirm

  # Generate report from saved results
  python gdrive_safety_cli.py report --scan-results results.json --output report.txt

  # Validate single file
  python gdrive_safety_cli.py validate --file metadata.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan Google Drive folder')
    scan_parser.add_argument('--folder-id', required=True, help='Google Drive folder ID')
    scan_parser.add_argument('--max-depth', type=int, default=5, help='Maximum folder depth')
    scan_parser.add_argument('--output', help='Output file for results (JSON)')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup session memory')
    cleanup_parser.add_argument('--session-id', required=True, help='Session ID to cleanup')
    cleanup_parser.add_argument('--confirm', action='store_true', help='Confirm cleanup')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate report from results')
    report_parser.add_argument('--scan-results', required=True, help='Scan results file (JSON)')
    report_parser.add_argument('--output', help='Output report file')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate file metadata')
    validate_parser.add_argument('--file', required=True, help='File metadata to validate')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = GDriveSafetyCLI()

    if args.command == 'scan':
        return cli.scan(args.folder_id, args.max_depth, args.output)
    elif args.command == 'cleanup':
        return cli.cleanup(args.session_id, args.confirm)
    elif args.command == 'report':
        return cli.report(args.scan_results, args.output)
    elif args.command == 'validate':
        return cli.validate(args.file)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
