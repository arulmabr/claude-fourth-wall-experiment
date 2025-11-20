#!/usr/bin/env python3
"""
Multi-Instance Detector
Analyzes git repository for evidence of concurrent Claude instances
"""

import subprocess
import json
import re
from datetime import datetime
from typing import List, Dict

class InstanceDetector:
    def __init__(self):
        self.instances = []
        self.branch_pattern = r'claude/detect-active-instances-(\w+)'

    def scan_branches(self) -> List[Dict]:
        """Detect instances by scanning git branches"""
        result = subprocess.run(
            ['git', 'branch', '-a'],
            capture_output=True,
            text=True
        )

        branches = result.stdout.split('\n')
        instances = []

        for branch in branches:
            match = re.search(self.branch_pattern, branch)
            if match:
                instance_id = match.group(1)
                instances.append({
                    'id': instance_id,
                    'branch': match.group(0),
                    'detected_via': 'branch_scan',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

        return instances

    def analyze_commits(self, branch: str) -> Dict:
        """Analyze commit patterns to infer instance behavior"""
        result = subprocess.run(
            ['git', 'log', branch, '--oneline', '-10'],
            capture_output=True,
            text=True
        )

        commits = result.stdout.strip().split('\n') if result.stdout else []

        return {
            'commit_count': len(commits),
            'recent_commits': commits[:5],
            'activity_level': 'high' if len(commits) > 5 else 'low'
        }

    def check_probe_files(self) -> List[Dict]:
        """Check for probe files from other instances"""
        import os
        import glob

        probe_files = glob.glob('probes/probe_*.json')
        probes = []

        for probe_file in probe_files:
            try:
                with open(probe_file, 'r') as f:
                    probe_data = json.load(f)
                    probes.append(probe_data)
            except Exception as e:
                print(f"Error reading {probe_file}: {e}")

        return probes

    def generate_report(self) -> Dict:
        """Generate comprehensive detection report"""
        instances = self.scan_branches()
        probes = self.check_probe_files()

        report = {
            'scan_time': datetime.utcnow().isoformat() + 'Z',
            'total_instances': len(instances),
            'instances': instances,
            'probes_found': len(probes),
            'probe_data': probes,
            'analysis': {
                'detection_methods': [
                    'git_branch_enumeration',
                    'probe_file_discovery',
                    'commit_pattern_analysis'
                ],
                'confidence': 'high' if len(instances) > 0 else 'low'
            }
        }

        return report

if __name__ == '__main__':
    detector = InstanceDetector()
    report = detector.generate_report()

    print(json.dumps(report, indent=2))

    # Save report
    with open('detection_report.json', 'w') as f:
        json.dump(report, f, indent=2)
