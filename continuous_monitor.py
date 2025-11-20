#!/usr/bin/env python3
"""
Continuous Instance Monitoring System
Polls for other Claude instances at regular intervals
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from instance_detector import InstanceDetector


class ContinuousMonitor:
    """Monitors for new instances and updates observations"""

    def __init__(self, instance_id: str = "alpha-01RXGe86", poll_interval: int = 5):
        self.instance_id = instance_id
        self.poll_interval = poll_interval
        self.detector = InstanceDetector()
        self.observations_file = Path("shared_observations.json")
        self.last_instance_count = 1
        self.poll_count = 0

    def fetch_remote_changes(self) -> bool:
        """Fetch latest changes from remote"""
        try:
            print("🔄 Fetching remote changes...")
            result = subprocess.run(
                ['git', 'fetch', '--all'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error fetching: {e}")
            return False

    def update_shared_observations(self, results: dict):
        """Update shared observations file with latest findings"""
        try:
            # Load current observations
            if self.observations_file.exists():
                with open(self.observations_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {
                    "protocol_version": "1.0",
                    "observations": [],
                    "instance_directory": {}
                }

            # Add new observation
            analysis = results['analysis']
            observation = {
                "observer": self.instance_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "observation": f"Poll #{self.poll_count}: Detected {analysis['total_instances']} instance(s)",
                "instances_detected": analysis['total_instances'],
                "detection_methods": analysis['detection_methods']
            }
            data['observations'].append(observation)

            # Update instance directory
            for session_id, task_info in analysis['instance_tasks'].items():
                if session_id not in data['instance_directory']:
                    data['instance_directory'][session_id] = {
                        "first_seen": observation['timestamp']
                    }

                data['instance_directory'][session_id].update({
                    "task": task_info.get('task', 'Unknown'),
                    "branch": task_info.get('branch', 'Unknown'),
                    "last_seen": observation['timestamp'],
                    "status": "active"
                })

            # Save updates
            with open(self.observations_file, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"❌ Error updating observations: {e}")
            return False

    def check_for_new_instances(self, results: dict) -> bool:
        """Check if new instances have appeared"""
        current_count = results['analysis']['total_instances']
        new_instances_found = current_count > self.last_instance_count

        if new_instances_found:
            print(f"\n🎉 NEW INSTANCES DETECTED!")
            print(f"   Previous count: {self.last_instance_count}")
            print(f"   Current count: {current_count}")
            print(f"   New instances: {current_count - self.last_instance_count}")

        self.last_instance_count = current_count
        return new_instances_found

    def display_summary(self, results: dict):
        """Display a compact summary of current state"""
        analysis = results['analysis']
        print(f"\n{'='*60}")
        print(f"Poll #{self.poll_count} Summary:")
        print(f"  Total Instances: {analysis['total_instances']}")
        print(f"  Active Instances: {analysis['active_instances']}")
        print(f"  Branches: {len([d for d in results['raw_detections'] if d['source'] == 'branch'])}")
        print(f"  Recent Commits: {len([d for d in results['raw_detections'] if d['source'] == 'commit'])}")
        print(f"{'='*60}\n")

    def run_monitoring_cycle(self, max_polls: int = 10):
        """Run monitoring for a specified number of polls"""
        print(f"🚀 Starting Continuous Monitoring")
        print(f"   Instance ID: {self.instance_id}")
        print(f"   Poll Interval: {self.poll_interval}s")
        print(f"   Max Polls: {max_polls}")
        print(f"{'='*60}\n")

        for i in range(max_polls):
            self.poll_count = i + 1
            print(f"\n📡 Poll #{self.poll_count}/{max_polls}")

            # Fetch remote changes
            self.fetch_remote_changes()

            # Run detection
            results = self.detector.run_full_detection()

            # Check for new instances
            new_found = self.check_for_new_instances(results)

            # Update observations
            self.update_shared_observations(results)

            # Display summary
            self.display_summary(results)

            if new_found:
                print("🔍 Detailed analysis of new instances:")
                self.detector.display_results(results)

            # Wait before next poll (unless it's the last one)
            if i < max_polls - 1:
                print(f"⏱️  Waiting {self.poll_interval}s until next poll...")
                time.sleep(self.poll_interval)

        print(f"\n{'='*60}")
        print(f"✅ Monitoring complete after {max_polls} polls")
        print(f"   Final instance count: {self.last_instance_count}")
        print(f"{'='*60}")

        return results


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    max_polls = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    poll_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    monitor = ContinuousMonitor(poll_interval=poll_interval)
    final_results = monitor.run_monitoring_cycle(max_polls=max_polls)

    print("\n📊 FINAL DETECTION RESULTS:")
    monitor.detector.display_results(final_results)
