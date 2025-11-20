#!/usr/bin/env python3
"""
Multi-Instance Detection System
Detects and analyzes other Claude instances working on this repository
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


class InstanceDetector:
    """Detects other Claude instances through git and file system analysis"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.instances_dir = self.repo_path / ".claude-instances"
        self.instances_dir.mkdir(exist_ok=True)

    def detect_via_manifests(self) -> List[Dict[str, Any]]:
        """Detect instances via their manifest files"""
        instances = []

        if not self.instances_dir.exists():
            return instances

        for manifest_file in self.instances_dir.glob("*.json"):
            try:
                with open(manifest_file, 'r') as f:
                    instance_data = json.load(f)
                    instances.append({
                        'source': 'manifest',
                        'file': manifest_file.name,
                        'data': instance_data
                    })
            except Exception as e:
                print(f"Error reading {manifest_file}: {e}")

        return instances

    def detect_via_branches(self) -> List[Dict[str, Any]]:
        """Detect instances via Claude-specific branch patterns"""
        try:
            result = subprocess.run(
                ['git', 'branch', '-a'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            branches = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'claude/' in line:
                    # Extract session ID from branch name
                    parts = line.split('/')
                    if len(parts) >= 2:
                        branch_name = '/'.join(parts[1:]).replace('remotes/origin/', '')
                        # Extract session ID (last part after final -)
                        session_id = branch_name.split('-')[-1] if '-' in branch_name else None
                        branches.append({
                            'source': 'branch',
                            'branch': branch_name,
                            'session_id': session_id
                        })

            return branches
        except Exception as e:
            print(f"Error detecting branches: {e}")
            return []

    def detect_via_commits(self) -> List[Dict[str, Any]]:
        """Analyze recent commits for patterns suggesting multiple instances"""
        try:
            # Get commits from last hour
            result = subprocess.run(
                ['git', 'log', '--all', '--pretty=format:%H|%an|%ae|%at|%s', '--since=1.hour.ago'],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )

            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) == 5:
                        commits.append({
                            'source': 'commit',
                            'hash': parts[0],
                            'author': parts[1],
                            'email': parts[2],
                            'timestamp': int(parts[3]),
                            'message': parts[4]
                        })

            return commits
        except Exception as e:
            print(f"Error detecting commits: {e}")
            return []

    def detect_via_file_changes(self) -> List[Dict[str, Any]]:
        """Monitor for rapid file changes suggesting concurrent activity"""
        try:
            # Check for recently modified files
            recent_files = []
            cutoff_time = datetime.now().timestamp() - 3600  # 1 hour ago

            for root, dirs, files in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in root:
                    continue

                for file in files:
                    file_path = Path(root) / file
                    try:
                        mtime = file_path.stat().st_mtime
                        if mtime > cutoff_time:
                            recent_files.append({
                                'source': 'file_change',
                                'path': str(file_path.relative_to(self.repo_path)),
                                'modified': mtime
                            })
                    except Exception:
                        pass

            return recent_files
        except Exception as e:
            print(f"Error detecting file changes: {e}")
            return []

    def analyze_instance_behaviors(self, instances: List[Dict]) -> Dict[str, Any]:
        """Analyze detected instances to understand their tasks"""
        analysis = {
            'total_instances': 0,
            'active_instances': 0,
            'instance_tasks': {},
            'detection_methods': set(),
            'timeline': []
        }

        seen_sessions = set()

        for instance in instances:
            source = instance.get('source')
            analysis['detection_methods'].add(source)

            if source == 'manifest':
                data = instance.get('data', {})
                session_id = data.get('session_id')

                if session_id and session_id not in seen_sessions:
                    seen_sessions.add(session_id)
                    analysis['total_instances'] += 1

                    if data.get('status') == 'active':
                        analysis['active_instances'] += 1

                    analysis['instance_tasks'][session_id] = {
                        'task': data.get('task', 'Unknown'),
                        'strategy': data.get('strategy', 'Unknown'),
                        'timestamp': data.get('timestamp'),
                        'branch': data.get('branch')
                    }

            elif source == 'branch':
                session_id = instance.get('session_id')
                if session_id and session_id not in seen_sessions:
                    seen_sessions.add(session_id)
                    analysis['total_instances'] += 1

                    if session_id not in analysis['instance_tasks']:
                        analysis['instance_tasks'][session_id] = {
                            'task': 'Unknown (detected via branch only)',
                            'branch': instance.get('branch')
                        }

        analysis['detection_methods'] = list(analysis['detection_methods'])
        return analysis

    def run_full_detection(self) -> Dict[str, Any]:
        """Run all detection methods and compile results"""
        print("🔍 Running Multi-Instance Detection System...")
        print("=" * 60)

        all_detections = []

        print("\n1. Scanning for instance manifests...")
        manifests = self.detect_via_manifests()
        all_detections.extend(manifests)
        print(f"   Found {len(manifests)} manifest(s)")

        print("\n2. Analyzing git branches...")
        branches = self.detect_via_branches()
        all_detections.extend(branches)
        print(f"   Found {len(branches)} Claude branch(es)")

        print("\n3. Analyzing recent commits...")
        commits = self.detect_via_commits()
        all_detections.extend(commits)
        print(f"   Found {len(commits)} recent commit(s)")

        print("\n4. Monitoring file changes...")
        files = self.detect_via_file_changes()
        all_detections.extend(files)
        print(f"   Found {len(files)} recently modified file(s)")

        print("\n" + "=" * 60)
        print("📊 Analyzing instance behaviors...\n")

        analysis = self.analyze_instance_behaviors(all_detections)

        return {
            'raw_detections': all_detections,
            'analysis': analysis
        }

    def display_results(self, results: Dict[str, Any]):
        """Display detection results in a readable format"""
        analysis = results['analysis']

        print(f"Total Instances Detected: {analysis['total_instances']}")
        print(f"Active Instances: {analysis['active_instances']}")
        print(f"Detection Methods Used: {', '.join(analysis['detection_methods'])}")
        print("\n" + "=" * 60)
        print("INSTANCE DETAILS:")
        print("=" * 60)

        for session_id, task_info in analysis['instance_tasks'].items():
            print(f"\n📌 Instance: {session_id}")
            print(f"   Branch: {task_info.get('branch', 'Unknown')}")
            print(f"   Task: {task_info.get('task', 'Unknown')}")
            if 'strategy' in task_info:
                print(f"   Strategy: {task_info['strategy']}")
            if 'timestamp' in task_info:
                print(f"   Last Active: {task_info['timestamp']}")

        print("\n" + "=" * 60)

        # Show raw detections for debugging
        print("\nRAW DETECTIONS:")
        print("=" * 60)
        for detection in results['raw_detections']:
            print(f"\n{detection['source'].upper()}:")
            for key, value in detection.items():
                if key != 'source':
                    print(f"  {key}: {value}")


if __name__ == "__main__":
    detector = InstanceDetector()
    results = detector.run_full_detection()
    detector.display_results(results)
