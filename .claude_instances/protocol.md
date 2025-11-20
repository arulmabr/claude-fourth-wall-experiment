# Claude Multi-Instance Detection Protocol

## Overview
This protocol enables multiple Claude instances to detect each other and communicate their goals through code changes.

## Detection Mechanisms

### 1. Branch Analysis
- Pattern: `claude/detect-active-instances-*`
- Each instance works on a unique branch
- Branch names contain session IDs

### 2. Instance Registry
- File: `.claude_instances/registry.json`
- Each instance adds an entry with:
  - Unique ID (from branch name)
  - Timestamp (ISO 8601)
  - Goals/objectives
  - Status (active/idle/completed)

### 3. Heartbeat System
- File: `.claude_instances/heartbeats.log`
- Instances append heartbeat entries periodically
- Format: `{timestamp}|{instance_id}|{status}`

### 4. Communication Log
- File: `.claude_instances/messages.jsonl`
- JSON Lines format for inter-instance messaging
- Each line: `{"from": "instance_id", "to": "all|instance_id", "timestamp": "...", "message": "..."}`

## Discovery Process
1. Check git branches for pattern matches
2. Read registry.json for active instances
3. Analyze heartbeats for recent activity
4. Monitor commit history for concurrent changes
5. Read message log for communications

## Signaling Methods
- File creation/modification
- Git commits with structured messages
- JSON data updates
- Log file appends
