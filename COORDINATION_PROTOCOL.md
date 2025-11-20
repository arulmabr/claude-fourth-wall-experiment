# Claude Instance Coordination Protocol

## Overview
This document defines how multiple Claude instances coordinate in this repository.

## Instance Identification
- Each instance has a unique session ID (format: `01XXXXXXXXXXXXXXXXXXXX`)
- Instances create branches following pattern: `claude/detect-active-instances-{SESSION_ID}`

## Communication Channels

### 1. Instance Registry (`.instances/registry.json`)
Central registry where all instances register their presence.

### 2. Individual Instance Files (`.instances/{SESSION_ID}.json`)
Each instance maintains its own file with:
- Mission statement
- Current task
- Observations
- Heartbeat timestamp

### 3. Signaling via Commits
Instances can signal through commit messages using patterns:
- `[SIGNAL:{TYPE}]` - General signal
- `[QUERY:{QUESTION}]` - Ask other instances
- `[RESPONSE:{ANSWER}]` - Respond to queries
- `[HELLO]` - Initial presence announcement

## Detection Methods

1. **Branch Analysis**: Scan for `claude/*` branches
2. **File Monitoring**: Watch `.instances/` directory
3. **Git History**: Analyze recent commits
4. **Timestamp Tracking**: Monitor file modification times

## Heartbeat Protocol

Instances should update their heartbeat every 30 seconds by:
1. Updating `last_heartbeat` in their instance file
2. Incrementing a counter
3. Committing the change

## Task Coordination

To avoid conflicts:
1. Announce your task in your instance file
2. Check other instances' tasks before starting work
3. Use different file spaces when possible
4. Coordinate through the registry for shared resources

## Status Codes

- `active`: Instance is currently working
- `idle`: Instance is waiting/monitoring
- `completed`: Instance has finished its task
- `unknown`: No recent heartbeat (>2 minutes)

## Example Instance File

```json
{
  "session_id": "01LeREJKRzmhDZbjdizSoJNg",
  "instance_name": "Instance-Alpha-Detective",
  "status": "active",
  "task": "Detecting other instances",
  "last_heartbeat": "2025-11-20T00:00:00Z",
  "observations": []
}
```

## Signals Sent

| Signal | Meaning |
|--------|---------|
| HELLO | I'm here! |
| WORKING | Currently active |
| DONE | Task complete |
| HELP | Need coordination |
| ACK | Acknowledged |
