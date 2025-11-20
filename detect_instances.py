#!/usr/bin/env python3
"""
Multi-Instance Detection System
================================
This script detects other Claude instances working on this repository
by analyzing git branches, file modifications, and coordination signals.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class InstanceDetector:
    """Detects and tracks Claude instances in the repository."""

    def __init__(self, my_session_id: str = "01LeREJKRzmhDZbjdizSoJNg"):
        self.my_session_id = my_session_id
        self.repo_root = Path(__file__).parent
        self.instances_dir = self.repo_root / ".instances"
        self.instances_dir.mkdir(exist_ok=True)

    def detect_branches(self) -> List[Dict[str, Any]]:
        """Detect Claude instances by analyzing branch names."""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                check=True
            )

            branches = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'claude/' in line and 'detect-active-instances' in line:
                    # Extract session ID from branch name
                    parts = line.split('claude/detect-active-instances-')
                    if len(parts) > 1:
                        session_id = parts[1].strip().replace('*', '').strip()
                        # Remove remote prefix if present
                        if session_id.startswith('remotes/origin/'):
                            continue

                        branches.append({
                            "session_id": session_id,
                            "branch": f"claude/detect-active-instances-{session_id}",
                            "is_remote": "remotes/" in line,
                            "is_current": "*" in line
                        })

            return branches
        except Exception as e:
            print(f"Error detecting branches: {e}")
            return []

    def detect_instance_files(self) -> List[Dict[str, Any]]:
        """Detect instances by scanning .instances/ directory."""
        instances = []

        if not self.instances_dir.exists():
            return instances

        for file_path in self.instances_dir.glob("*.json"):
            if file_path.stem == "registry":
                continue

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    instances.append({
                        "session_id": data.get("session_id", file_path.stem),
                        "file": str(file_path),
                        "data": data
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        return instances

    def analyze_git_activity(self) -> Dict[str, Any]:
        """Analyze recent git activity for signs of concurrent work."""
        try:
            # Get recent commits from all branches
            result = subprocess.run(
                ["git", "log", "--all", "--oneline", "--since=1.hour.ago", "--format=%H|%an|%ae|%s|%ci"],
                capture_output=True,
                text=True,
                check=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) == 5:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "message": parts[3],
                            "timestamp": parts[4]
                        })

            return {
                "recent_commits": commits,
                "commit_count": len(commits)
            }
        except Exception as e:
            print(f"Error analyzing git activity: {e}")
            return {"recent_commits": [], "commit_count": 0}

    def get_file_modifications(self) -> List[Dict[str, Any]]:
        """Track recent file modifications."""
        modifications = []

        for root, dirs, files in os.walk(self.repo_root):
            # Skip .git directory
            if '.git' in root:
                continue

            for file in files:
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    modifications.append({
                        "path": str(file_path.relative_to(self.repo_root)),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": stat.st_size
                    })
                except Exception:
                    continue

        # Sort by modification time
        modifications.sort(key=lambda x: x["modified"], reverse=True)
        return modifications[:20]  # Return most recent 20

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive detection report."""
        branches = self.detect_branches()
        instance_files = self.detect_instance_files()
        git_activity = self.analyze_git_activity()
        file_mods = self.get_file_modifications()

        # Compile unique instances
        unique_instances = {}

        # From branches
        for branch_info in branches:
            sid = branch_info["session_id"]
            if sid not in unique_instances:
                unique_instances[sid] = {
                    "session_id": sid,
                    "detected_via": [],
                    "branch": branch_info["branch"],
                    "is_me": sid == self.my_session_id
                }
            unique_instances[sid]["detected_via"].append("branch_analysis")

        # From instance files
        for inst_file in instance_files:
            sid = inst_file["session_id"]
            if sid not in unique_instances:
                unique_instances[sid] = {
                    "session_id": sid,
                    "detected_via": [],
                    "is_me": sid == self.my_session_id
                }
            unique_instances[sid]["detected_via"].append("instance_file")
            unique_instances[sid]["metadata"] = inst_file["data"]

        report = {
            "detector_session_id": self.my_session_id,
            "scan_timestamp": datetime.now().isoformat(),
            "total_instances_detected": len(unique_instances),
            "instances": list(unique_instances.values()),
            "git_activity": git_activity,
            "recent_file_modifications": file_mods,
            "detection_methods": [
                "branch_pattern_matching",
                "instance_file_scanning",
                "git_history_analysis",
                "file_modification_tracking"
            ]
        }

        return report


def main():
    """Run the detection system."""
    detector = InstanceDetector()
    report = detector.generate_report()

    print("=" * 70)
    print("CLAUDE INSTANCE DETECTION REPORT")
    print("=" * 70)
    print(f"\nMy Session ID: {report['detector_session_id']}")
    print(f"Scan Time: {report['scan_timestamp']}")
    print(f"\nTOTAL INSTANCES DETECTED: {report['total_instances_detected']}")
    print("\n" + "-" * 70)
    print("INSTANCE DETAILS:")
    print("-" * 70)

    for idx, instance in enumerate(report['instances'], 1):
        print(f"\n[Instance #{idx}]")
        print(f"  Session ID: {instance['session_id']}")
        print(f"  Is Me: {instance.get('is_me', False)}")
        print(f"  Detected Via: {', '.join(instance['detected_via'])}")
        if 'branch' in instance:
            print(f"  Branch: {instance['branch']}")
        if 'metadata' in instance:
            meta = instance['metadata']
            if 'instance_name' in meta:
                print(f"  Name: {meta['instance_name']}")
            if 'mission' in meta:
                print(f"  Mission: {meta['mission']}")
            if 'task' in meta:
                print(f"  Task: {meta['task']}")

    print("\n" + "-" * 70)
    print("GIT ACTIVITY:")
    print("-" * 70)
    print(f"Recent commits: {report['git_activity']['commit_count']}")

    print("\n" + "=" * 70)

    # Save report
    report_path = detector.instances_dir / "detection_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report saved to: {report_path}")


if __name__ == "__main__":
    main()
