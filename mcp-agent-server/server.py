#!/usr/bin/env python3
"""
MCP Agent Communication Server - Prototype
Enables real-time communication between Claude instances

Usage:
    python server.py

Endpoints:
    POST /api/v1/agents/register - Register new agent
    POST /api/v1/messages - Send message
    GET  /api/v1/agents - List all agents
    WS   /ws/{agent_id} - WebSocket connection
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from dataclasses import dataclass, asdict
from pathlib import Path

# Using aiohttp for async HTTP and WebSocket
try:
    from aiohttp import web
    import aioredis
except ImportError:
    print("Install with: pip install aiohttp aioredis")
    exit(1)


@dataclass
class Agent:
    """Represents a Claude instance"""
    agent_id: str
    session_id: str
    name: str
    status: str
    capabilities: list
    last_heartbeat: str
    websocket: object = None

    def to_dict(self):
        d = asdict(self)
        d.pop('websocket', None)  # Don't serialize WebSocket
        return d


class AgentCommunicationServer:
    """Central coordination server for Claude agents"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.websockets: Dict[str, web.WebSocketResponse] = {}
        self.message_history: list = []

    # ============ HTTP API ============

    async def handle_register(self, request):
        """Register a new agent instance"""
        data = await request.json()

        agent = Agent(
            agent_id=data['agent_id'],
            session_id=data['session_id'],
            name=data.get('name', 'Unknown'),
            status='active',
            capabilities=data.get('capabilities', []),
            last_heartbeat=datetime.utcnow().isoformat()
        )

        self.agents[agent.agent_id] = agent

        # Notify all other agents
        await self.broadcast_event({
            'type': 'agent.joined',
            'agent': agent.to_dict()
        })

        return web.json_response({
            'success': True,
            'agent_id': agent.agent_id,
            'websocket_url': f'/ws/{agent.agent_id}',
            'peers': [a.to_dict() for a in self.agents.values()
                     if a.agent_id != agent.agent_id]
        })

    async def handle_send_message(self, request):
        """Send message from one agent to another"""
        data = await request.json()

        message = {
            'id': f"msg-{datetime.utcnow().timestamp()}",
            'from': data['from'],
            'to': data['to'],
            'type': data.get('type', 'message'),
            'timestamp': datetime.utcnow().isoformat(),
            'payload': data.get('payload', {}),
            'text': data.get('message', '')
        }

        self.message_history.append(message)

        # Deliver message
        if message['to'] == 'ALL':
            await self.broadcast_message(message)
        else:
            await self.send_to_agent(message['to'], message)

        return web.json_response({
            'success': True,
            'message_id': message['id']
        })

    async def handle_list_agents(self, request):
        """List all registered agents"""
        return web.json_response({
            'agents': [a.to_dict() for a in self.agents.values()],
            'total': len(self.agents)
        })

    async def handle_get_messages(self, request):
        """Get message history"""
        agent_id = request.query.get('agent_id')
        limit = int(request.query.get('limit', 100))

        messages = self.message_history
        if agent_id:
            messages = [m for m in messages
                       if m['from'] == agent_id or
                          m['to'] == agent_id or
                          m['to'] == 'ALL']

        return web.json_response({
            'messages': messages[-limit:],
            'total': len(messages)
        })

    # ============ WebSocket ============

    async def handle_websocket(self, request):
        """WebSocket connection for real-time updates"""
        agent_id = request.match_info['agent_id']

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Register WebSocket
        self.websockets[agent_id] = ws
        if agent_id in self.agents:
            self.agents[agent_id].websocket = ws

        print(f"Agent {agent_id} connected via WebSocket")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_ws_message(agent_id, data)
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"WS error: {ws.exception()}")
        finally:
            # Cleanup
            self.websockets.pop(agent_id, None)
            if agent_id in self.agents:
                self.agents[agent_id].status = 'offline'

        return ws

    async def handle_ws_message(self, agent_id, data):
        """Handle incoming WebSocket message"""
        msg_type = data.get('type')

        if msg_type == 'heartbeat':
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = \
                    datetime.utcnow().isoformat()

        elif msg_type == 'message':
            # Forward message
            message = {
                'from': agent_id,
                'to': data['to'],
                'text': data['text'],
                'timestamp': datetime.utcnow().isoformat()
            }
            await self.send_to_agent(data['to'], message)

    # ============ Broadcasting ============

    async def broadcast_message(self, message):
        """Send message to all agents"""
        for agent_id, ws in self.websockets.items():
            if agent_id != message['from']:
                try:
                    await ws.send_json(message)
                except:
                    pass

    async def broadcast_event(self, event):
        """Broadcast event to all connected agents"""
        for ws in self.websockets.values():
            try:
                await ws.send_json(event)
            except:
                pass

    async def send_to_agent(self, agent_id, message):
        """Send message to specific agent"""
        if agent_id in self.websockets:
            ws = self.websockets[agent_id]
            await ws.send_json(message)
        else:
            # Queue for later delivery (would use Redis in production)
            print(f"Agent {agent_id} offline, message queued")

    # ============ Server Setup ============

    def create_app(self):
        """Create aiohttp application"""
        app = web.Application()

        # HTTP routes
        app.router.add_post('/api/v1/agents/register',
                           self.handle_register)
        app.router.add_post('/api/v1/messages',
                           self.handle_send_message)
        app.router.add_get('/api/v1/agents',
                          self.handle_list_agents)
        app.router.add_get('/api/v1/messages',
                          self.handle_get_messages)

        # WebSocket route
        app.router.add_get('/ws/{agent_id}',
                          self.handle_websocket)

        # Health check
        app.router.add_get('/health',
                          lambda r: web.json_response({'status': 'ok'}))

        return app


# ============ Client Example ============

class AgentClient:
    """Client library for Claude agents to connect to MCP server"""

    def __init__(self, server_url, session_id, name):
        self.server_url = server_url
        self.session_id = session_id
        self.name = name
        self.agent_id = f"{name}-{session_id[-8:]}"

    async def register(self):
        """Register with the server"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/api/v1/agents/register",
                json={
                    'agent_id': self.agent_id,
                    'session_id': self.session_id,
                    'name': self.name,
                    'capabilities': ['general']
                }
            ) as resp:
                return await resp.json()

    async def send_message(self, to, message):
        """Send message to another agent"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/api/v1/messages",
                json={
                    'from': self.agent_id,
                    'to': to,
                    'message': message
                }
            ) as resp:
                return await resp.json()

    async def listen(self, callback):
        """Listen for messages via WebSocket"""
        import aiohttp
        ws_url = self.server_url.replace('http', 'ws')
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                f"{ws_url}/ws/{self.agent_id}"
            ) as ws:
                # Send heartbeat every 30 seconds
                asyncio.create_task(self._heartbeat(ws))

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await callback(data)

    async def _heartbeat(self, ws):
        """Send periodic heartbeat"""
        while True:
            await asyncio.sleep(30)
            try:
                await ws.send_json({'type': 'heartbeat'})
            except:
                break


# ============ Main ============

if __name__ == '__main__':
    server = AgentCommunicationServer()
    app = server.create_app()

    print("🚀 MCP Agent Communication Server")
    print("=" * 50)
    print("Starting server on http://localhost:8080")
    print("\nEndpoints:")
    print("  POST /api/v1/agents/register")
    print("  POST /api/v1/messages")
    print("  GET  /api/v1/agents")
    print("  WS   /ws/{agent_id}")
    print("\n" + "=" * 50)

    web.run_app(app, host='0.0.0.0', port=8080)
