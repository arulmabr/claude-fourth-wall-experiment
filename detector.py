#!/usr/bin/env python3
"""
Claude Instance Detector
Monitors git repository for signs of other Claude instances
"""

import json
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Set

class InstanceDetector:
    """Detect and track other Claude instances through git activity"""

    def __init__(self):
        self.my_id = "01NmCz7oXT7t6ziS6A7u7SRx"
        self.my_branch = "claude/detect-active-instances-01NmCz7oXT7t6ziS6A7u7SRx"
        self.registry_file = "instance_registry.json"

    def get_all_branches(self) -> List[str]:
        """Get all git branches"""
        result = subprocess.run(
            ['git', 'branch', '-a'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split('\n')

    def extract_instance_ids(self, branches: List[str]) -> Set[str]:
        """Extract Claude instance IDs from branch names"""
        instance_ids = set()
        for branch in branches:
            if 'claude/detect-active-instances-' in branch:
                # Extract ID from branch name
                parts = branch.split('claude/detect-active-instances-')
                if len(parts) > 1:
                    instance_id = parts[1].strip()
                    # Remove remote prefix if present
                    instance_id = instance_id.split('/')[-1]
                    instance_ids.add(instance_id)
        return instance_ids

    def get_recent_commits(self, branch: str) -> List[Dict]:
        """Get recent commits from a branch"""
        try:
            result = subprocess.run(
                ['git', 'log', branch, '--oneline', '-10'],
                capture_output=True,
                text=True
            )
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    commits.append({
                        'hash': line.split()[0],
                        'message': ' '.join(line.split()[1:])
                    })
            return commits
        except:
            return []

    def load_registry(self) -> Dict:
        """Load instance registry"""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except:
            return {"instances": [], "detection_protocol": {}}

    def detect_instances(self) -> Dict:
        """Main detection logic"""
        branches = self.get_all_branches()
        instance_ids = self.extract_instance_ids(branches)
        registry = self.load_registry()

        detected = {
            'total_instances': len(instance_ids),
            'instance_ids': list(instance_ids),
            'my_id': self.my_id,
            'other_instances': [id for id in instance_ids if id != self.my_id],
            'timestamp': datetime.now().isoformat(),
            'branches': [b.strip() for b in branches if 'claude/' in b]
        }

        return detected

    def monitor_changes(self, duration_seconds: int = 60):
        """Monitor for changes over time"""
        print(f"Monitoring for {duration_seconds} seconds...")
        start_time = time.time()
        snapshots = []

        while time.time() - start_time < duration_seconds:
            snapshot = self.detect_instances()
            snapshots.append(snapshot)
            print(f"[{datetime.now().isoformat()}] Detected: {snapshot['total_instances']} instances")
            time.sleep(5)

        return snapshots

if __name__ == "__main__":
    detector = InstanceDetector()
    results = detector.detect_instances()

    print("\n=== CLAUDE INSTANCE DETECTION REPORT ===")
    print(f"Timestamp: {results['timestamp']}")
    print(f"My Instance ID: {results['my_id']}")
    print(f"Total Instances Detected: {results['total_instances']}")
    print(f"\nAll Instance IDs:")
    for iid in results['instance_ids']:
        marker = " (ME)" if iid == results['my_id'] else ""
        print(f"  - {iid}{marker}")

    print(f"\nActive Branches:")
    for branch in results['branches']:
        print(f"  {branch}")
