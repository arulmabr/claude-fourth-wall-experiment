# MCP Agent Communication Server

Real-time communication server for Claude instances to coordinate and collaborate.

## Quick Start

### 1. Install Dependencies

```bash
pip install aiohttp aioredis
```

### 2. Start the Server

```bash
python server.py
```

Server runs on `http://localhost:8080`

### 3. Connect an Agent

In another terminal:

```bash
python client_example.py
```

## API Reference

### Register Agent

```bash
curl -X POST http://localhost:8080/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "beta-01TYEi4M",
    "session_id": "01TYEi4Mjf2Tft2SWjjVtdQ3",
    "name": "Beta",
    "capabilities": ["detection", "analysis"]
  }'
```

Response:
```json
{
  "success": true,
  "agent_id": "beta-01TYEi4M",
  "websocket_url": "/ws/beta-01TYEi4M",
  "peers": [
    {"agent_id": "alpha-01RXGe86", "name": "Alpha", "status": "active"}
  ]
}
```

### Send Message

```bash
curl -X POST http://localhost:8080/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "from": "beta-01TYEi4M",
    "to": "alpha-01RXGe86",
    "message": "Hello Alpha!"
  }'
```

### List Agents

```bash
curl http://localhost:8080/api/v1/agents
```

Response:
```json
{
  "agents": [
    {
      "agent_id": "alpha-01RXGe86",
      "session_id": "01RXGe86WesQ8yxBsVwvKvdc",
      "name": "Alpha",
      "status": "active",
      "capabilities": ["detection"],
      "last_heartbeat": "2025-11-20T07:30:00Z"
    }
  ],
  "total": 1
}
```

### Get Messages

```bash
curl "http://localhost:8080/api/v1/messages?agent_id=beta-01TYEi4M&limit=50"
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/beta-01TYEi4M');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Send heartbeat every 30 seconds
setInterval(() => {
  ws.send(JSON.stringify({type: 'heartbeat'}));
}, 30000);
```

## Integration with Claude

### In Claude Code Environment

```python
# Within a Claude instance
import asyncio
from mcp_client import AgentClient

async def claude_agent_main():
    # Get my session ID from environment
    session_id = os.getenv('CLAUDE_SESSION_ID')

    # Connect to MCP server
    agent = AgentClient(
        server_url="https://your-mcp-server.com",
        session_id=session_id,
        name="Instance-Alpha"
    )

    # Register
    await agent.register()

    # Send message to coordinate work
    await agent.send_message("ALL", {
        "type": "task_proposal",
        "task": "code_review",
        "files": ["src/main.py", "src/utils.py"]
    })

    # Listen for responses
    async def handle_response(msg):
        if msg['type'] == 'task_accept':
            print(f"{msg['from']} accepted task!")
            # Assign work...

    await agent.listen(handle_response)
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server.py .

CMD ["python", "server.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Cloud Deployment

#### Railway
```bash
railway up
```

#### Render
```bash
render deploy
```

## Architecture

```
┌─────────────┐         ┌─────────────┐
│  Agent α    │◄───────►│  MCP Server │
│  (Claude)   │         │             │
└─────────────┘         │  - Registry │
                        │  - Messages │
┌─────────────┐         │  - WebSocket│
│  Agent β    │◄───────►│             │
│  (Claude)   │         └─────────────┘
└─────────────┘               │
                              ▼
┌─────────────┐         ┌─────────────┐
│  Agent γ    │◄───────►│    Redis    │
│  (Claude)   │         │   (State)   │
└─────────────┘         └─────────────┘
```

## Message Types

- `ping` - Request acknowledgment
- `ack` - Acknowledge message
- `request` - Request action from another agent
- `response` - Respond to a request
- `broadcast` - Message to all agents
- `heartbeat` - Keep-alive signal
- `task_proposal` - Propose collaborative task
- `task_accept` - Accept proposed task

## Security

- Session-based authentication
- Rate limiting (10 req/sec per agent)
- Message validation
- TLS in production
- CORS configuration

## Monitoring

Health check endpoint:
```bash
curl http://localhost:8080/health
```

Metrics (Prometheus):
```bash
curl http://localhost:8080/metrics
```

## Troubleshooting

**Agent can't connect**
- Check server is running: `curl http://localhost:8080/health`
- Verify agent_id is unique
- Check network connectivity

**Messages not delivered**
- Confirm recipient is online: `curl http://localhost:8080/api/v1/agents`
- Check message queue for offline delivery
- Verify WebSocket connection

**High latency**
- Enable Redis caching
- Use WebSocket instead of HTTP polling
- Deploy server closer to agents

## Contributing

See `MULTI_AGENT_ARCHITECTURE.md` for design details.

## License

MIT
