#!/usr/bin/env python3
"""
Example: Claude Agent using MCP Communication Server

This shows how a Claude instance would connect to the MCP server
and communicate with other agents in real-time.
"""

import asyncio
import sys
from server import AgentClient


async def message_handler(message):
    """Handle incoming messages from other agents"""
    print(f"\n📨 Message from {message['from']}:")
    print(f"   {message.get('text', message)}")


async def main():
    # Initialize agent
    agent = AgentClient(
        server_url="http://localhost:8080",
        session_id="01TYEi4Mjf2Tft2SWjjVtdQ3",
        name="Beta"
    )

    print(f"🤖 Starting agent: {agent.agent_id}")

    # Register with server
    result = await agent.register()
    print(f"✅ Registered! Found {len(result['peers'])} peers")

    for peer in result['peers']:
        print(f"   - {peer['name']} ({peer['agent_id']})")

    # Send a message to all
    await agent.send_message("ALL", "Hello from Beta! 👋")
    print("📤 Sent broadcast message")

    # Send direct message to Alpha
    await agent.send_message(
        "alpha-01RXGe86",
        "Hey Alpha! I detected you created the original protocol!"
    )
    print("📤 Sent direct message to Alpha")

    # Listen for messages
    print("\n👂 Listening for messages... (Ctrl+C to stop)")
    try:
        await agent.listen(message_handler)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


if __name__ == '__main__':
    asyncio.run(main())
