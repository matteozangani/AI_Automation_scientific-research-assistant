import asyncio
import websockets
import json

class MCPServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.tool_handlers = {}

    def register_tool_handler(self, tool_name, handler):
        self.tool_handlers[tool_name] = handler

    async def handler(self, websocket, path):
        async for message in websocket:
            request = json.loads(message)
            tool_name = request.get('tool')
            if tool_name in self.tool_handlers:
                response = await self.tool_handlers[tool_name](request)
                await websocket.send(json.dumps(response))
            else:
                await websocket.send(json.dumps({'error': 'Tool not found.'}))

    def run(self):
        server = websockets.serve(self.handler, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

# Example tool handler
async def example_tool_handler(request):
    return {'result': 'Hello from the MCP server!'}

# Running the server
if __name__ == '__main__':
    mcp_server = MCPServer()
    mcp_server.register_tool_handler('example_tool', example_tool_handler)
    mcp_server.run()