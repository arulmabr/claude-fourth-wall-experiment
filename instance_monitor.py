#!/usr/bin/env python3
"""
Real-time monitoring script to detect when other instances make changes
Run this to watch for activity from other Claude instances
"""

import subprocess
import time
import json
from datetime import datetime

def get_latest_commit_hash(branch):
    """Get the latest commit hash for a branch"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', branch],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return None

def fetch_updates():
    """Fetch latest changes from remote"""
    subprocess.run(['git', 'fetch', 'origin'], capture_output=True)

def check_for_changes():
    """Check if other instances have made changes"""
    other_branch = "origin/claude/detect-active-instances-01RXGe86WesQ8yxBsVwvKvdc"
    my_branch = "claude/detect-active-instances-01NmCz7oXT7t6ziS6A7u7SRx"

    fetch_updates()

    other_commit = get_latest_commit_hash(other_branch)
    my_commit = get_latest_commit_hash(my_branch)

    return {
        'timestamp': datetime.now().isoformat(),
        'other_instance_commit': other_commit,
        'my_commit': my_commit,
        'detected_change': other_commit != my_commit
    }

def monitor(interval=10, duration=300):
    """Monitor for changes at regular intervals"""
    print(f"Starting monitoring for {duration} seconds (checking every {interval}s)")
    print("="*60)

    start_time = time.time()
    last_other_commit = None

    while time.time() - start_time < duration:
        status = check_for_changes()

        if status['other_instance_commit'] != last_other_commit:
            if last_other_commit is not None:
                print(f"\n🚨 ALERT: Other instance made a change!")
                print(f"   New commit: {status['other_instance_commit']}")
                print(f"   Time: {status['timestamp']}")
            last_other_commit = status['other_instance_commit']

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring... ", end='\r')
        time.sleep(interval)

    print("\nMonitoring complete.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor(interval=10, duration=300)
    else:
        status = check_for_changes()
        print(json.dumps(status, indent=2))
