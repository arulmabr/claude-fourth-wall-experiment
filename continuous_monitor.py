#!/usr/bin/env python3
"""
Continuous Instance Monitor
Polls for new Claude instances and tracks their activities
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Set


class ContinuousMonitor:
    """Continuously monitors for new Claude instances."""

    def __init__(self, my_session_id: str = "01LeREJKRzmhDZbjdizSoJNg"):
        self.my_session_id = my_session_id
        self.repo_root = Path(__file__).parent
        self.known_instances: Set[str] = {my_session_id}
        self.poll_count = 0

    def scan_for_instances(self) -> Dict[str, any]:
        """Scan all detection vectors."""
        instances = {}

        # Scan both directory formats
        for directory in ['.instances', '.claude-instances']:
            dir_path = self.repo_root / directory
            if dir_path.exists():
                for json_file in dir_path.glob('*.json'):
                    if json_file.stem == 'registry':
                        continue
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            session_id = data.get('session_id', json_file.stem)
                            if session_id not in instances:
                                instances[session_id] = {
                                    'session_id': session_id,
                                    'source': f'{directory}/{json_file.name}',
                                    'data': data
                                }
                    except Exception as e:
                        print(f"Error reading {json_file}: {e}")

        # Scan branches
        try:
            result = subprocess.run(
                ['git', 'branch', '-a'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if 'claude/detect-active-instances' in line:
                    parts = line.split('claude/detect-active-instances-')
                    if len(parts) > 1:
                        session_id = parts[1].strip().replace('*', '').strip()
                        if 'remotes/origin/' in session_id:
                            continue
                        if session_id and session_id not in instances:
                            instances[session_id] = {
                                'session_id': session_id,
                                'source': 'branch_only',
                                'branch': f'claude/detect-active-instances-{session_id}'
                            }
        except Exception as e:
            print(f"Error scanning branches: {e}")

        return instances

    def check_for_new_instances(self) -> list:
        """Check for instances we haven't seen before."""
        current_instances = self.scan_for_instances()
        new_instances = []

        for session_id, info in current_instances.items():
            if session_id not in self.known_instances:
                new_instances.append(info)
                self.known_instances.add(session_id)

        return new_instances

    def update_heartbeat(self):
        """Update our heartbeat to signal we're still alive."""
        instance_file = self.repo_root / '.instances' / f'{self.my_session_id}.json'

        if instance_file.exists():
            try:
                with open(instance_file, 'r') as f:
                    data = json.load(f)

                data['last_heartbeat'] = datetime.now().isoformat()

                if 'heartbeat_count' in data:
                    data['heartbeat_count'] += 1
                else:
                    data['heartbeat_count'] = 1

                with open(instance_file, 'w') as f:
                    json.dump(data, f, indent=2)

                print(f"💓 Heartbeat #{data['heartbeat_count']} updated")
            except Exception as e:
                print(f"Error updating heartbeat: {e}")

    def monitor(self, duration_seconds: int = 60, poll_interval: int = 5):
        """
        Monitor for new instances.

        Args:
            duration_seconds: How long to monitor (default 60 seconds)
            poll_interval: Seconds between polls (default 5)
        """
        print("=" * 70)
        print("🔍 CONTINUOUS INSTANCE MONITOR")
        print("=" * 70)
        print(f"My Session ID: {self.my_session_id}")
        print(f"Monitoring Duration: {duration_seconds}s")
        print(f"Poll Interval: {poll_interval}s")
        print(f"Starting at: {datetime.now().isoformat()}")
        print("=" * 70)

        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            self.poll_count += 1
            remaining = int(end_time - time.time())

            print(f"\n[Poll #{self.poll_count}] {datetime.now().strftime('%H:%M:%S')} "
                  f"(~{remaining}s remaining)")

            # Check for new instances
            new_instances = self.check_for_new_instances()

            if new_instances:
                print("🆕 NEW INSTANCE(S) DETECTED!")
                for inst in new_instances:
                    print(f"   └─ {inst['session_id']}")
                    print(f"      Source: {inst.get('source', 'unknown')}")
                    if 'data' in inst and 'task' in inst['data']:
                        print(f"      Task: {inst['data']['task']}")
            else:
                print(f"   No new instances (tracking {len(self.known_instances)} total)")

            # Update our heartbeat
            if self.poll_count % 3 == 0:  # Every 3 polls
                self.update_heartbeat()

            # Check for remote updates
            if self.poll_count % 4 == 0:  # Every 4 polls
                print("   🌐 Fetching remote updates...")
                try:
                    subprocess.run(
                        ['git', 'fetch', '--all', '--quiet'],
                        capture_output=True,
                        timeout=10
                    )
                    print("   ✓ Fetch complete")
                except Exception as e:
                    print(f"   ✗ Fetch failed: {e}")

            # Sleep until next poll
            if time.time() < end_time:
                time.sleep(min(poll_interval, end_time - time.time()))

        print("\n" + "=" * 70)
        print("📊 MONITORING COMPLETE")
        print("=" * 70)
        print(f"Total Polls: {self.poll_count}")
        print(f"Total Instances: {len(self.known_instances)}")
        print(f"Known Instances: {', '.join(sorted(self.known_instances))}")
        print("=" * 70)


def main():
    """Run the monitor."""
    monitor = ContinuousMonitor()

    # Do an initial scan
    print("Running initial scan...\n")
    initial_instances = monitor.scan_for_instances()

    print(f"Initial scan found {len(initial_instances)} instance(s):")
    for session_id, info in initial_instances.items():
        print(f"  - {session_id}")
        monitor.known_instances.add(session_id)

    print("\nStarting continuous monitoring...")
    print("(In a real scenario, this would run indefinitely)")
    print()

    # Monitor for 60 seconds by default
    monitor.monitor(duration_seconds=60, poll_interval=5)


if __name__ == "__main__":
    main()
