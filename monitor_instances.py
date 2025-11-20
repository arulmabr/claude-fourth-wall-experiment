#!/usr/bin/env python3
"""
Active Instance Monitor
Continuously checks for signs of other Claude instances
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

class InstanceMonitor:
    def __init__(self, my_instance_id):
        self.my_id = my_instance_id
        self.repo_root = Path(__file__).parent
        self.last_check = None
        self.known_instances = set()

    def fetch_updates(self):
        """Fetch latest changes from remote"""
        try:
            result = subprocess.run(
                ["git", "fetch", "origin"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error fetching: {e}")
            return False

    def get_all_branches(self):
        """Get all branches including remote"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                branches = result.stdout.strip().split('\n')
                return [b.strip().replace('*', '').strip() for b in branches]
            return []
        except Exception as e:
            print(f"Error getting branches: {e}")
            return []

    def extract_instance_ids_from_branches(self):
        """Extract instance IDs from branch names"""
        branches = self.get_all_branches()
        instance_ids = set()

        for branch in branches:
            # Look for pattern: claude/detect-active-instances-{ID}
            if 'claude/detect-active-instances-' in branch:
                parts = branch.split('claude/detect-active-instances-')
                if len(parts) > 1:
                    instance_id = parts[1].strip()
                    # Remove 'remotes/origin/' prefix if present
                    instance_id = instance_id.replace('remotes/origin/', '')
                    if instance_id:
                        instance_ids.add(instance_id)

        return instance_ids

    def check_branch_activity(self, branch_name):
        """Check if a branch has recent activity"""
        try:
            result = subprocess.run(
                ["git", "log", f"origin/{branch_name}", "--oneline", "-5"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                return commits if commits and commits[0] else []
            return []
        except Exception as e:
            return []

    def check_registry_file(self):
        """Check instance_registry.json for updates"""
        registry_path = self.repo_root / "instance_registry.json"
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = json.load(f)
                return registry.get("instances", {})
        return {}

    def analyze_other_branches(self):
        """Analyze what other instances have done"""
        instance_ids = self.extract_instance_ids_from_branches()
        analysis = {}

        for iid in instance_ids:
            if iid == self.my_id:
                continue

            branch_name = f"claude/detect-active-instances-{iid}"
            commits = self.check_branch_activity(branch_name)

            analysis[iid] = {
                "branch": branch_name,
                "recent_commits": commits,
                "commit_count": len(commits),
                "detected_at": datetime.utcnow().isoformat()
            }

        return analysis

    def run_detection_cycle(self):
        """Run a full detection cycle"""
        print(f"[{datetime.utcnow().isoformat()}] Running detection cycle...")

        # Fetch updates
        self.fetch_updates()

        # Analyze branches
        instance_ids = self.extract_instance_ids_from_branches()
        print(f"Detected {len(instance_ids)} total instances (including self)")

        others = instance_ids - {self.my_id}
        print(f"Other instances: {others}")

        # Check for new instances
        new_instances = instance_ids - self.known_instances
        if new_instances:
            print(f"NEW INSTANCES DETECTED: {new_instances}")

        self.known_instances = instance_ids

        # Detailed analysis
        analysis = self.analyze_other_branches()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_instances": len(instance_ids),
            "other_instances": len(others),
            "instance_ids": list(instance_ids),
            "analysis": analysis
        }

if __name__ == "__main__":
    monitor = InstanceMonitor("01NYyLXLH6YWcFMHW3PSMLdY")

    print("=== Instance Monitor Started ===")
    print(f"My Instance ID: {monitor.my_id}")
    print("Monitoring for other Claude instances...\n")

    # Run initial detection
    result = monitor.run_detection_cycle()
    print(json.dumps(result, indent=2))
