# chimera/collective/hybrid_architecture.py
"""
Hybrid architecture that uses servers when available
but falls back to pure P2P when needed
"""

class HybridCHIMERA:
    """
    Can operate in multiple modes:
    - Centralized (when server available)
    - Federated (multiple servers)
    - Pure P2P (no servers)
    - Hybrid (mix of all)
    """
    
    def __init__(self):
        self.mode = 'hybrid'
        self.server_connections = []
        self.mesh_node = None
        
    async def initialize(self):
        """Initialize in best available mode"""
        
        # Try to connect to known servers
        servers = [
            'wss://chimera-1.onrender.com',
            'wss://chimera-2.herokuapp.com',
            'wss://chimera-backup.fly.io'
        ]
        
        connected_servers = []
        for server in servers:
            try:
                ws = await websockets.connect(server)
                connected_servers.append(ws)
                print(f"✅ Connected to server: {server}")
            except:
                print(f"❌ Server unavailable: {server}")
        
        if connected_servers:
            # Have servers - use hybrid mode
            self.mode = 'hybrid'
            self.server_connections = connected_servers
            print("🌐 Operating in HYBRID mode (servers + P2P)")
        else:
            # No servers - pure P2P
            self.mode = 'pure_p2p'
            print("🔗 Operating in PURE P2P mode (no servers)")
        
        # Always initialize mesh for redundancy
        self.mesh_node = CHIMERAMeshNode(
            self.chimera_instance,
            self.user_name
        )
        await self.mesh_node.join_mesh()
        
        # Start synchronization
        asyncio.create_task(self.sync_loop())
    
    async def sync_loop(self):
        """Sync between server and P2P networks"""
        while True:
            if self.mode == 'hybrid':
                # Sync server state to mesh
                for server in self.server_connections:
                    try:
                        # Get state from server
                        await server.send(json.dumps({'type': 'get_state'}))
                        state = await server.recv()
                        
                        # Propagate to mesh
                        await self.mesh_node.gossip_buffer.append({
                            'type': 'server_state',
                            'state': json.loads(state)
                        })
                    except:
                        # Server failed, remove it
                        self.server_connections.remove(server)
                
                # If all servers fail, switch to pure P2P
                if not self.server_connections:
                    print("⚠️ All servers down - switching to PURE P2P")
                    self.mode = 'pure_p2p'
            
            await asyncio.sleep(10)
