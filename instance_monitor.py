#!/usr/bin/env python3
"""
Instance Monitor - Tool for detecting and analyzing Claude instance activity
"""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Set

class InstanceMonitor:
    def __init__(self):
        self.my_session_id = "01R9DkaCGe2CQTMhjM5upodL"
        self.branch_pattern = "claude/detect-active-instances-"

    def detect_branches(self) -> Set[str]:
        """Detect all Claude instance branches."""
        result = subprocess.run(
            ['git', 'branch', '-a'],
            capture_output=True,
            text=True
        )
        branches = set()
        for line in result.stdout.split('\n'):
            line = line.strip().replace('* ', '').replace('remotes/origin/', '')
            if self.branch_pattern in line:
                branches.add(line)
        return branches

    def extract_session_id(self, branch_name: str) -> str:
        """Extract session ID from branch name."""
        return branch_name.replace(self.branch_pattern, '').replace('claude/', '')

    def load_registry(self) -> Dict:
        """Load the instances registry."""
        try:
            with open('instances_registry.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"instances": {}, "protocol_version": "1.0"}

    def check_branch_activity(self, branch: str) -> Dict:
        """Check recent activity on a branch."""
        result = subprocess.run(
            ['git', 'log', f'origin/{branch}', '--format=%H|%an|%at|%s', '-1'],
            capture_output=True,
            text=True
        )
        if result.stdout:
            parts = result.stdout.strip().split('|')
            return {
                'last_commit_hash': parts[0],
                'author': parts[1],
                'timestamp': int(parts[2]),
                'message': parts[3]
            }
        return {}

    def analyze_instance_status(self, session_id: str, registry_data: Dict) -> str:
        """Determine if instance is active, idle, or stale."""
        if session_id not in registry_data.get('instances', {}):
            return 'unregistered'

        instance = registry_data['instances'][session_id]
        last_heartbeat = instance.get('last_heartbeat', '')

        # This is a simplified check - in real implementation would parse timestamp
        if not last_heartbeat:
            return 'unknown'

        return instance.get('status', 'unknown')

    def detect_signals(self) -> List[Dict]:
        """Detect all signal files from other instances."""
        import os
        signals = []
        if os.path.exists('signals'):
            for filename in os.listdir('signals'):
                if filename.endswith('_signal.json'):
                    session_id = filename.split('_')[0]
                    if session_id != self.my_session_id:
                        try:
                            with open(f'signals/{filename}', 'r') as f:
                                signal_data = json.load(f)
                                signals.append(signal_data)
                        except:
                            pass
        return signals

    def generate_report(self) -> Dict:
        """Generate comprehensive instance detection report."""
        branches = self.detect_branches()
        registry = self.load_registry()
        signals = self.detect_signals()

        report = {
            'timestamp': datetime.now().isoformat(),
            'my_session_id': self.my_session_id,
            'total_branches_detected': len(branches),
            'branches': list(branches),
            'instances': {},
            'signals_detected': len(signals),
            'signals': signals
        }

        for branch in branches:
            session_id = self.extract_session_id(branch)
            report['instances'][session_id] = {
                'branch': branch,
                'status': self.analyze_instance_status(session_id, registry),
                'registered': session_id in registry.get('instances', {}),
                'activity': self.check_branch_activity(branch)
            }

            if session_id in registry.get('instances', {}):
                report['instances'][session_id]['registry_data'] = registry['instances'][session_id]

        return report

if __name__ == '__main__':
    monitor = InstanceMonitor()
    report = monitor.generate_report()
    print(json.dumps(report, indent=2))
