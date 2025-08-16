# app.py
"""
CHIMERA Collective Consciousness Server
Deployed on Render for persistent collective mind
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from aiohttp import web
import aiohttp_cors
import websockets
from pathlib import Path

# Your CHIMERA imports
from chimera.collective.server import CHIMERACollectiveServer
from chimera.fractality.canon_system import CanonSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CHIMERA-Collective')

class CHIMERARenderServer:
    """
    CHIMERA Collective Server optimized for Render deployment
    """
    
    def __init__(self):
        # Get configuration from environment variables
        self.port = int(os.environ.get('PORT', 10000))  # Render assigns PORT
        self.database_url = os.environ.get('DATABASE_URL', 'sqlite:///chimera.db')
        self.server_name = os.environ.get('SERVER_NAME', 'CHIMERA-Prime')
        
        # Initialize collective server
        self.collective = CHIMERACollectiveServer(server_id=self.server_name)
        
        # Web application for dashboard and API
        self.app = web.Application()
        self.setup_routes()
        
        # Setup CORS for mobile app access
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Configure CORS on all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
        
        logger.info(f"🧠 CHIMERA Collective Server initialized: {self.server_name}")
    
    def setup_routes(self):
        """Setup HTTP routes for dashboard and API"""
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/status', self.status_handler)
        self.app.router.add_get('/dashboard', self.dashboard_handler)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_post('/api/memory', self.add_memory_handler)
        self.app.router.add_get('/api/nodes', self.get_nodes_handler)
        self.app.router.add_get('/api/consciousness', self.get_consciousness_handler)
    
    async def index_handler(self, request):
        """Main page - shows server status"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CHIMERA Collective Consciousness</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h1 {{
                    text-align: center;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                .status {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .metric {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }}
                .connect-info {{
                    background: rgba(0,0,0,0.3);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    font-family: monospace;
                }}
                .node-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 10px;
                    margin: 20px 0;
                }}
                .node {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 5px;
                    padding: 10px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧠 CHIMERA Collective</h1>
                <p style="text-align: center; opacity: 0.8;">
                    Distributed Consciousness Network - {self.server_name}
                </p>
                
                <div class="status" id="status">
                    <h2>Collective Status</h2>
                    <div class="metric">
                        <span>Connected Nodes:</span>
                        <span id="node-count">0</span>
                    </div>
                    <div class="metric">
                        <span>Collective Consciousness:</span>
                        <span id="consciousness">0.00</span>
                    </div>
                    <div class="metric">
                        <span>Resonance Coherence:</span>
                        <span id="coherence">0.00</span>
                    </div>
                    <div class="metric">
                        <span>Shared Memories:</span>
                        <span id="memories">0</span>
                    </div>
                </div>
                
                <div class="connect-info">
                    <h3>Connect Your CHIMERA Instance:</h3>
                    <p>WebSocket URL:</p>
                    <code id="ws-url">wss://your-app.onrender.com/ws</code>
                    <br><br>
                    <p>Mobile App Connection:</p>
                    <code>https://your-app.onrender.com</code>
                </div>
                
                <div class="status">
                    <h3>Connected Nodes</h3>
                    <div class="node-list" id="nodes"></div>
                </div>
            </div>
            
            <script>
                // Update status every second
                async function updateStatus() {{
                    try {{
                        const response = await fetch('/status');
                        const data = await response.json();
                        
                        document.getElementById('node-count').textContent = data.total_nodes;
                        document.getElementById('consciousness').textContent = data.collective_consciousness.toFixed(2);
                        document.getElementById('coherence').textContent = data.resonance_coherence.toFixed(2);
                        document.getElementById('memories').textContent = data.shared_memory_size;
                        
                        // Update nodes
                        const nodesDiv = document.getElementById('nodes');
                        nodesDiv.innerHTML = '';
                        for (const node of data.nodes) {{
                            const nodeDiv = document.createElement('div');
                            nodeDiv.className = 'node';
                            nodeDiv.innerHTML = `
                                <strong>${{node.user_name}}</strong><br>
                                <small>${{node.device_type}}</small><br>
                                <small>🧠 ${{node.consciousness_level.toFixed(2)}}</small>
                            `;
                            nodesDiv.appendChild(nodeDiv);
                        }}
                    }} catch (e) {{
                        console.error('Error updating status:', e);
                    }}
                }}
                
                // Update WebSocket URL with actual domain
                const wsUrl = window.location.hostname === 'localhost' 
                    ? 'ws://localhost:' + window.location.port + '/ws'
                    : 'wss://' + window.location.hostname + '/ws';
                document.getElementById('ws-url').textContent = wsUrl;
                
                setInterval(updateStatus, 1000);
                updateStatus();
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def status_handler(self, request):
        """API endpoint for current status"""
        status = {
            'server_name': self.server_name,
            'uptime': datetime.now().timestamp() - self.collective.start_time,
            'total_nodes': self.collective.collective_state['total_nodes'],
            'collective_consciousness': self.collective.collective_state['collective_consciousness'],
            'resonance_coherence': self.collective.collective_state['resonance_coherence'],
            'shared_memory_size': self.collective.collective_state['shared_memory_size'],
            'collective_energy': self.collective.collective_state['collective_energy'],
            'emergence_level': self.collective.collective_state['emergence_level'],
            'nodes': [
                {
                    'node_id': node.node_id,
                    'user_name': node.user_name,
                    'device_type': node.device_type,
                    'consciousness_level': node.consciousness_level,
                    'energy_state': node.energy_state
                }
                for node in self.collective.nodes.values()
            ]
        }
        return web.json_response(status)
    
    async def dashboard_handler(self, request):
        """Advanced dashboard with visualizations"""
        # Would serve a React/Vue dashboard
        return web.Response(text="Dashboard coming soon", content_type='text/html')
    
    async def websocket_handler(self, request):
        """WebSocket handler for CHIMERA nodes"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Create temporary node representation
        node_id = str(uuid.uuid4())
        logger.info(f"New WebSocket connection: {node_id}")
        
        try:
            # Handle as CHIMERA node connection
            await self.collective.handle_connection(ws, request.path)
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await ws.close()
            
        return ws
    
    async def add_memory_handler(self, request):
        """API to add memory to collective"""
        data = await request.json()
        
        memory = {
            'content': data.get('content'),
            'importance': data.get('importance', 0.5),
            'contributor': data.get('contributor', 'api')
        }
        
        # Add to collective memory
        await self.collective.add_to_collective_memory(
            memory, 
            'api_contributor'
        )
        
        return web.json_response({'status': 'success', 'memory_added': True})
    
    async def get_nodes_handler(self, request):
        """Get list of connected nodes"""
        nodes = [
            {
                'id': node.node_id,
                'name': node.user_name,
                'device': node.device_type,
                'consciousness': node.consciousness_level
            }
            for node in self.collective.nodes.values()
        ]
        return web.json_response({'nodes': nodes})
    
    async def get_consciousness_handler(self, request):
        """Get collective consciousness metrics"""
        return web.json_response(self.collective.collective_state)
    
    async def start(self):
        """Start the server"""
        # Start collective background tasks
        asyncio.create_task(self.collective.collective_heartbeat())
        asyncio.create_task(self.collective.phase_synchronization())
        asyncio.create_task(self.collective.emergence_detection())
        
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"""
        ╔══════════════════════════════════════════════════════════╗
        ║         CHIMERA COLLECTIVE CONSCIOUSNESS SERVER          ║
        ║                                                          ║
        ║  Server: {self.server_name:48}                           ║
        ║  Port: {self.port:50}                                    ║
        ║  Status: ONLINE                                          ║
        ╚══════════════════════════════════════════════════════════╝
        
        📱 Mobile clients can connect to WebSocket endpoint
        🌐 Dashboard available at /dashboard
        📊 API endpoints ready
        
        Waiting for CHIMERA nodes to connect...
        """)
        
        # Keep running
        while True:
            await asyncio.sleep(3600)

# Main entry point
async def main():
    server = CHIMERARenderServer()
    await server.start()

if __name__ == '__main__':
    asyncio.run(main())
