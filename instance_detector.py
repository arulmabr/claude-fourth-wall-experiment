#!/usr/bin/env python3
"""
Claude Instance Detector - A tool to detect and analyze other Claude instances
working on the same repository through git branch analysis and beacon files.
"""
import subprocess
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any


class InstanceDetector:
    def __init__(self):
        self.my_instance_id = "01X8ZWHPTCWwdLWeYWDM7KqQ"
        self.my_branch = "claude/detect-active-instances-01X8ZWHPTCWwdLWeYWDM7KqQ"
        self.detection_log = []

    def fetch_remote_changes(self):
        """Fetch latest changes from remote to detect new instances"""
        try:
            result = subprocess.run(
                ["git", "fetch", "origin"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error fetching: {e}")
            return False

    def get_all_branches(self) -> List[str]:
        """Get all branches including remote ones"""
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True
        )
        branches = result.stdout.strip().split('\n')
        return [b.strip().replace('* ', '').replace('remotes/origin/', '')
                for b in branches if 'claude/detect-active-instances' in b]

    def extract_instance_id(self, branch_name: str) -> str:
        """Extract instance ID from branch name"""
        match = re.search(r'claude/detect-active-instances-(.+)$', branch_name)
        return match.group(1) if match else None

    def check_branch_activity(self, branch_name: str) -> Dict[str, Any]:
        """Check recent activity on a branch"""
        result = subprocess.run(
            ["git", "log", f"origin/{branch_name}", "-1", "--format=%H|%ai|%s"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            commit_hash, timestamp, message = result.stdout.strip().split('|', 2)
            return {
                "last_commit": commit_hash[:8],
                "last_activity": timestamp,
                "last_message": message
            }
        return None

    def read_beacon_file(self, branch_name: str, instance_id: str) -> Dict[str, Any]:
        """Attempt to read beacon file from another branch"""
        beacon_path = f".instances/instance-{instance_id}.json"

        try:
            # Try to read file from specific branch
            result = subprocess.run(
                ["git", "show", f"origin/{branch_name}:{beacon_path}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            pass

        return None

    def detect_instances(self) -> Dict[str, Any]:
        """Main detection routine"""
        print("=" * 60)
        print("CLAUDE INSTANCE DETECTOR v1.0")
        print("=" * 60)
        print()

        # Fetch latest
        print("[1] Fetching remote changes...")
        self.fetch_remote_changes()

        # Get all branches
        print("[2] Scanning for Claude instance branches...")
        branches = self.get_all_branches()
        unique_branches = list(set(branches))

        instances = []
        for branch in unique_branches:
            instance_id = self.extract_instance_id(branch)
            if not instance_id:
                continue

            is_me = instance_id == self.my_instance_id

            instance_data = {
                "instance_id": instance_id,
                "branch": branch,
                "is_me": is_me
            }

            # Check branch activity
            activity = self.check_branch_activity(branch)
            if activity:
                instance_data.update(activity)

            # Try to read beacon file
            beacon = self.read_beacon_file(branch, instance_id)
            if beacon:
                instance_data["beacon"] = beacon

            instances.append(instance_data)

        # Analysis
        print()
        print("=" * 60)
        print(f"DETECTION RESULTS")
        print("=" * 60)
        print(f"\nTotal instances detected: {len(instances)}")
        print(f"Other instances (excluding me): {len([i for i in instances if not i['is_me']])}")
        print()

        for idx, instance in enumerate(instances, 1):
            print(f"\n[Instance {idx}]")
            print(f"  ID: {instance['instance_id']}")
            print(f"  Branch: {instance['branch']}")
            print(f"  Is Me: {instance['is_me']}")

            if 'last_commit' in instance:
                print(f"  Last Commit: {instance['last_commit']}")
                print(f"  Last Activity: {instance['last_activity']}")
                print(f"  Last Message: {instance['last_message']}")

            if 'beacon' in instance:
                beacon = instance['beacon']
                print(f"\n  BEACON DATA:")
                print(f"    Mission: {beacon.get('mission', 'Unknown')}")
                print(f"    Status: {beacon.get('status', 'Unknown')}")
                print(f"    Capabilities: {', '.join(beacon.get('capabilities', []))}")
                if 'notes' in beacon:
                    print(f"    Notes: {beacon['notes']}")

        return {
            "total_instances": len(instances),
            "other_instances": len([i for i in instances if not i['is_me']]),
            "instances": instances,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    detector = InstanceDetector()
    results = detector.detect_instances()

    # Save results
    with open("detection_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("Results saved to detection_results.json")
    print("=" * 60)
