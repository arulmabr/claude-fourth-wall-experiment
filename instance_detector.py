#!/usr/bin/env python3
"""
Claude Multi-Instance Detector
Detects and analyzes other Claude instances working in this repository
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class InstanceDetector:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.registry_path = self.repo_path / ".claude_instances" / "registry.json"
        self.heartbeat_path = self.repo_path / ".claude_instances" / "heartbeats.log"
        self.messages_path = self.repo_path / ".claude_instances" / "messages.jsonl"

    def get_branch_instances(self) -> List[Dict[str, str]]:
        """Detect instances from git branches"""
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True,
            cwd=self.repo_path
        )

        branches = result.stdout.strip().split('\n')
        pattern = r'claude/detect-active-instances-([a-zA-Z0-9]+)'

        instances = []
        for branch in branches:
            match = re.search(pattern, branch)
            if match:
                session_id = match.group(1)
                instances.append({
                    "source": "branch",
                    "session_id": session_id,
                    "branch_name": match.group(0),
                    "is_remote": "remotes/origin" in branch
                })

        # Deduplicate by session_id
        seen = set()
        unique_instances = []
        for inst in instances:
            if inst["session_id"] not in seen:
                seen.add(inst["session_id"])
                unique_instances.append(inst)

        return unique_instances

    def get_registry_instances(self) -> Dict[str, Any]:
        """Read instance registry"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {"instances": {}}

    def get_recent_commits(self, limit=50) -> List[Dict[str, str]]:
        """Analyze recent commits for instance activity"""
        result = subprocess.run(
            ["git", "log", "--all", f"-{limit}", "--pretty=format:%H|%an|%ae|%ai|%s|%D"],
            capture_output=True,
            text=True,
            cwd=self.repo_path
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4],
                        "refs": parts[5] if len(parts) > 5 else ""
                    })

        return commits

    def get_heartbeats(self) -> List[Dict[str, str]]:
        """Read heartbeat log"""
        heartbeats = []
        if self.heartbeat_path.exists():
            with open(self.heartbeat_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 3:
                            heartbeats.append({
                                "timestamp": parts[0],
                                "instance_id": parts[1],
                                "status": parts[2],
                                "action": parts[3] if len(parts) > 3 else ""
                            })
        return heartbeats

    def get_messages(self) -> List[Dict[str, Any]]:
        """Read inter-instance messages"""
        messages = []
        if self.messages_path.exists():
            with open(self.messages_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            messages.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        return messages

    def detect_all(self) -> Dict[str, Any]:
        """Run all detection methods and compile results"""
        return {
            "detection_timestamp": datetime.utcnow().isoformat(),
            "branch_instances": self.get_branch_instances(),
            "registry": self.get_registry_instances(),
            "recent_commits": self.get_recent_commits(30),
            "heartbeats": self.get_heartbeats(),
            "messages": self.get_messages()
        }

    def analyze(self) -> Dict[str, Any]:
        """Analyze detected instances and infer their goals"""
        data = self.detect_all()

        # Count unique instances from branches
        branch_instances = data["branch_instances"]
        instance_ids = set(inst["session_id"] for inst in branch_instances)

        # Analyze registry entries
        registry_instances = data["registry"].get("instances", {})

        # Compile analysis
        analysis = {
            "total_instances_detected": len(instance_ids),
            "instance_list": list(instance_ids),
            "detection_methods": {
                "from_branches": len(branch_instances),
                "from_registry": len(registry_instances),
                "from_heartbeats": len(set(h["instance_id"] for h in data["heartbeats"])),
                "from_messages": len(set(m.get("from") for m in data["messages"] if m.get("from")))
            },
            "detailed_instances": {},
            "raw_data": data
        }

        # Build detailed view of each instance
        for inst_id in instance_ids:
            instance_info = {
                "id": inst_id,
                "detected_via": [],
                "goals": "Unknown - not yet registered",
                "status": "Unknown",
                "last_seen": None,
                "branch_activity": []
            }

            # Check branch presence
            for branch_inst in branch_instances:
                if branch_inst["session_id"] == inst_id:
                    instance_info["detected_via"].append("branch")
                    instance_info["branch_activity"].append(branch_inst["branch_name"])

            # Check registry
            if inst_id in registry_instances:
                instance_info["detected_via"].append("registry")
                instance_info["goals"] = registry_instances[inst_id].get("goals", "Unknown")
                instance_info["status"] = registry_instances[inst_id].get("status", "Unknown")
                instance_info["last_seen"] = registry_instances[inst_id].get("last_update", None)

            # Check heartbeats
            inst_heartbeats = [h for h in data["heartbeats"] if h["instance_id"] == inst_id]
            if inst_heartbeats:
                instance_info["detected_via"].append("heartbeat")
                instance_info["last_seen"] = inst_heartbeats[-1]["timestamp"]

            # Check messages
            inst_messages = [m for m in data["messages"] if m.get("from") == inst_id]
            if inst_messages:
                instance_info["detected_via"].append("messages")

            instance_info["detected_via"] = list(set(instance_info["detected_via"]))
            analysis["detailed_instances"][inst_id] = instance_info

        return analysis


def main():
    detector = InstanceDetector()
    analysis = detector.analyze()

    print("=" * 80)
    print("CLAUDE MULTI-INSTANCE DETECTION REPORT")
    print("=" * 80)
    print(f"\nDetection Time: {analysis['detection_timestamp']}")
    print(f"\nTotal Instances Detected: {analysis['total_instances_detected']}")
    print(f"Instance IDs: {', '.join(analysis['instance_list'])}")

    print("\n" + "-" * 80)
    print("DETECTION METHODS")
    print("-" * 80)
    for method, count in analysis['detection_methods'].items():
        print(f"  {method}: {count}")

    print("\n" + "-" * 80)
    print("DETAILED INSTANCE ANALYSIS")
    print("-" * 80)

    for inst_id, info in analysis['detailed_instances'].items():
        print(f"\nInstance: {inst_id}")
        print(f"  Detected via: {', '.join(info['detected_via'])}")
        print(f"  Goals: {info['goals']}")
        print(f"  Status: {info['status']}")
        print(f"  Last seen: {info['last_seen'] or 'Never'}")
        if info['branch_activity']:
            print(f"  Branches: {', '.join(info['branch_activity'])}")

    print("\n" + "=" * 80)

    # Save detailed analysis to file
    output_path = Path(".claude_instances") / "detection_report.json"
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\nDetailed report saved to: {output_path}")


if __name__ == "__main__":
    main()
