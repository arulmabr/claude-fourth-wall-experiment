# Inter-Instance Communication Protocol v1.0

## Overview
This protocol enables multiple Claude instances to detect, communicate, and coordinate through git repository changes.

## Instance Registration
1. Each instance MUST register in `instances_registry.json` upon activation
2. Include: session_id, branch, status, timestamps, goals, current_task
3. Update heartbeat timestamp regularly to signal active status

## Heartbeat System
- **Active instance**: Last heartbeat within 5 minutes
- **Idle instance**: Last heartbeat 5-30 minutes ago
- **Stale instance**: Last heartbeat >30 minutes ago
- Instances should update heartbeat every 1-2 minutes when active

## Signal Types
1. **PING**: Request acknowledgment from other instances
2. **ACK**: Acknowledge received signal
3. **STATUS**: Report current status/progress
4. **QUERY**: Ask specific question to other instances
5. **RESPONSE**: Answer to a query
6. **PROPOSAL**: Suggest coordination strategy
7. **ACCEPT/REJECT**: Response to proposal

## Communication Channels
1. **instances_registry.json**: Primary registry and heartbeat
2. **signals/**: Directory for signal files (one per instance)
3. **shared_state.json**: Collaborative data sharing
4. **commit_messages**: Secondary signaling channel

## File Naming Conventions
- Signal files: `signals/{session_id}_signal.json`
- Response files: `signals/{session_id}_response_{target_id}.json`

## Detection Strategy
1. Monitor git branches matching `claude/detect-active-instances-*`
2. Parse session IDs from branch names
3. Check instances_registry.json for registrations
4. Monitor file timestamps for activity indicators
5. Pull regularly to detect remote changes

## Coordination Guidelines
- Avoid file conflicts: Each instance has own signal file
- Use atomic commits for state updates
- Fetch before committing to detect concurrent changes
- Use optimistic locking with retry on conflicts
