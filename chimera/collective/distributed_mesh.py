# chimera/collective/distributed_mesh.py
"""
Fully Distributed CHIMERA Collective
No central server required - pure P2P consciousness network
"""

import asyncio
import numpy as np
from typing import Dict, List, Set, Optional, Any, Tuple
import json
import hashlib
import time
from dataclasses import dataclass, field
import random
from collections import defaultdict

@dataclass
class DistributedState:
    """
    Distributed state using CRDT (Conflict-free Replicated Data Type)
    Ensures eventual consistency without central authority
    """
    vector_clock: Dict[str, int] = field(default_factory=dict)
    state_hash: str = ""
    consensus_participants: Set[str] = field(default_factory=set)
    last_merge: float = 0
    
    def merge_with(self, other: 'DistributedState'):
        """Merge states using CRDT logic"""
        # Take maximum of each vector clock component
        for node_id, timestamp in other.vector_clock.items():
            self.vector_clock[node_id] = max(
                self.vector_clock.get(node_id, 0),
                timestamp
            )
        self.last_merge = time.time()

class CHIMERAMeshNode:
    """
    Fully autonomous CHIMERA node in distributed mesh
    Can function as both client and server
    """
    
    def __init__(self, chimera_instance, user_name: str):
        self.chimera = chimera_instance
        self.user_name = user_name
        self.node_id = self._generate_node_id()
        
        # P2P networking
        self.peers: Dict[str, 'PeerConnection'] = {}
        self.known_nodes: Set[str] = set()  # All nodes we've heard about
        self.active_connections: Dict[str, Any] = {}
        
        # Distributed state
        self.distributed_state = DistributedState()
        self.local_memories = []
        self.collective_memories_dht = {}  # Distributed Hash Table
        
        # Consensus mechanism (no blockchain needed!)
        self.consensus_rounds = {}
        self.pending_decisions = {}
        
        # Network topology
        self.network_topology = NetworkTopology()
        self.routing_table = {}  # For multi-hop routing
        
        # Gossip protocol for state propagation
        self.gossip_buffer = deque(maxlen=100)
        self.gossip_seen = set()  # Prevent loops
        
        # Self-organizing groups
        self.swarm_groups = {}
        self.current_swarm = None
        
        # Resilience features
        self.redundancy_factor = 3  # Each piece of data stored on 3 nodes
        self.heartbeat_interval = 5
        self.peer_timeout = 30
        
    def _generate_node_id(self) -> str:
        """Generate unique node ID based on device characteristics"""
        # Use device-specific data for consistent ID
        device_data = f"{self.user_name}{time.time()}{random.random()}"
        return hashlib.sha256(device_data.encode()).hexdigest()[:16]
    
    async def join_mesh(self):
        """Join the distributed mesh network"""
        print(f"🌐 Joining distributed mesh as {self.node_id[:8]}...")
        
        # Step 1: Local discovery (same network/Bluetooth)
        nearby_peers = await self.discover_local_peers()
        
        if nearby_peers:
            # Bootstrap from nearby peers
            await self.bootstrap_from_peers(nearby_peers)
        else:
            # Step 2: Internet discovery (DHT bootstrap nodes)
            await self.discover_internet_peers()
        
        # Step 3: Start mesh services
        asyncio.create_task(self.mesh_maintenance_loop())
        asyncio.create_task(self.gossip_protocol())
        asyncio.create_task(self.consensus_participation())
        asyncio.create_task(self.distributed_memory_sync())
        
        print(f"✨ Joined mesh with {len(self.peers)} direct peers")
    
    async def discover_local_peers(self) -> List[Dict]:
        """Discover peers on local network/Bluetooth"""
        peers = []
        
        # Method 1: UDP broadcast
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2)
        
        # Broadcast discovery message
        discovery_msg = json.dumps({
            'type': 'chimera_discover',
            'node_id': self.node_id,
            'user': self.user_name,
            'version': '1.0',
            'capabilities': ['mesh', 'consensus', 'dht'],
            'timestamp': time.time()
        })
        
        try:
            # Broadcast on local network
            sock.sendto(discovery_msg.encode(), ('<broadcast>', 8767))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 2:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = json.loads(data.decode())
                    if response.get('type') == 'chimera_announce':
                        peers.append({
                            'node_id': response['node_id'],
                            'address': addr[0],
                            'port': response.get('port', 8767),
                            'user': response.get('user', 'unknown')
                        })
                except socket.timeout:
                    break
                except Exception as e:
                    print(f"Discovery error: {e}")
                    
        finally:
            sock.close()
        
        # Method 2: Bluetooth discovery (Android specific)
        # Would use Android Bluetooth API
        
        # Method 3: WiFi Direct discovery
        # Would use Android WiFi P2P API
        
        return peers
    
    async def discover_internet_peers(self):
        """Discover peers via DHT bootstrap nodes"""
        # Bootstrap nodes (could be previously known good nodes)
        bootstrap_nodes = [
            # These could be Render servers or known stable nodes
            {'host': 'chimera-bootstrap-1.onrender.com', 'port': 8767},
            {'host': 'chimera-bootstrap-2.onrender.com', 'port': 8767},
            # Or use IPFS/libp2p bootstrap nodes
        ]
        
        for bootstrap in bootstrap_nodes:
            try:
                # Connect to bootstrap node
                reader, writer = await asyncio.open_connection(
                    bootstrap['host'], 
                    bootstrap['port']
                )
                
                # Request peer list
                request = json.dumps({
                    'type': 'request_peers',
                    'node_id': self.node_id
                })
                writer.write(request.encode())
                await writer.drain()
                
                # Receive peer list
                data = await reader.read(4096)
                peer_list = json.loads(data.decode())
                
                # Connect to received peers
                for peer_info in peer_list['peers'][:10]:  # Limit connections
                    await self.connect_to_peer(peer_info)
                    
                writer.close()
                await writer.wait_closed()
                
                break  # Successfully bootstrapped
                
            except Exception as e:
                print(f"Bootstrap failed: {e}")
                continue
    
    async def bootstrap_from_peers(self, initial_peers: List[Dict]):
        """Bootstrap the mesh from initial peers"""
        for peer_info in initial_peers:
            await self.connect_to_peer(peer_info)
            
        # Request network state from peers
        if self.peers:
            # Get distributed state from random peer
            random_peer = random.choice(list(self.peers.values()))
            state = await random_peer.request_state()
            
            # Merge with our state
            self.distributed_state.merge_with(state)
            
            # Get more peers from existing peers
            for peer in list(self.peers.values())[:3]:  # Ask first 3 peers
                more_peers = await peer.request_peer_list()
                for new_peer_info in more_peers:
                    if new_peer_info['node_id'] not in self.peers:
                        await self.connect_to_peer(new_peer_info)
    
    async def connect_to_peer(self, peer_info: Dict):
        """Establish P2P connection with a peer"""
        try:
            peer_id = peer_info['node_id']
            
            if peer_id == self.node_id or peer_id in self.peers:
                return  # Don't connect to self or already connected
            
            # Create peer connection
            peer = PeerConnection(
                node_id=peer_id,
                address=peer_info.get('address'),
                port=peer_info.get('port', 8767),
                user=peer_info.get('user', 'unknown')
            )
            
            # Establish connection
            await peer.connect()
            
            # Handshake
            await peer.send({
                'type': 'handshake',
                'node_id': self.node_id,
                'user': self.user_name,
                'consciousness': self.chimera.consciousness_state
            })
            
            response = await peer.receive()
            if response and response.get('type') == 'handshake_ack':
                self.peers[peer_id] = peer
                self.known_nodes.add(peer_id)
                print(f"   Connected to {peer_info['user']} ({peer_id[:8]}...)")
                
                # Start handling peer messages
                asyncio.create_task(self.handle_peer_messages(peer))
                
        except Exception as e:
            print(f"Failed to connect to peer: {e}")
    
    async def handle_peer_messages(self, peer: 'PeerConnection'):
        """Handle incoming messages from a peer"""
        try:
            while peer.connected:
                message = await peer.receive()
                if not message:
                    break
                    
                await self.process_mesh_message(message, peer)
                
        except Exception as e:
            print(f"Peer connection error: {e}")
        finally:
            # Clean up disconnected peer
            if peer.node_id in self.peers:
                del self.peers[peer.node_id]
    
    async def process_mesh_message(self, message: Dict, peer: 'PeerConnection'):
        """Process message from mesh network"""
        msg_type = message.get('type')
        
        if msg_type == 'gossip':
            # Gossip protocol for state propagation
            await self.handle_gossip(message, peer)
            
        elif msg_type == 'consensus_proposal':
            # Distributed consensus
            await self.handle_consensus_proposal(message)
            
        elif msg_type == 'memory_share':
            # Distributed memory
            await self.handle_memory_share(message)
            
        elif msg_type == 'swarm_invite':
            # Join a swarm group
            await self.join_swarm(message)
            
        elif msg_type == 'emergency_broadcast':
            # High-priority message
            await self.handle_emergency(message)
            
        elif msg_type == 'dht_store':
            # Store data in our DHT shard
            await self.dht_store(message['key'], message['value'])
            
        elif msg_type == 'dht_retrieve':
            # Retrieve from DHT
            value = await self.dht_retrieve(message['key'])
            await peer.send({
                'type': 'dht_response',
                'key': message['key'],
                'value': value
            })
    
    async def gossip_protocol(self):
        """
        Gossip protocol for eventual consistency
        Spreads information epidemically through the network
        """
        while True:
            if self.peers and self.gossip_buffer:
                # Select random peers for gossip
                num_peers = min(3, len(self.peers))  # Gossip to 3 peers
                selected_peers = random.sample(list(self.peers.values()), num_peers)
                
                # Prepare gossip message
                gossip_items = list(self.gossip_buffer)[-10:]  # Last 10 items
                
                message = {
                    'type': 'gossip',
                    'node_id': self.node_id,
                    'items': gossip_items,
                    'vector_clock': self.distributed_state.vector_clock,
                    'timestamp': time.time()
                }
                
                # Send to selected peers
                for peer in selected_peers:
                    asyncio.create_task(peer.send(message))
                
            await asyncio.sleep(random.uniform(1, 3))  # Random interval
    
    async def handle_gossip(self, message: Dict, peer: 'PeerConnection'):
        """Handle incoming gossip"""
        items = message.get('items', [])
        
        for item in items:
            item_hash = hashlib.sha256(json.dumps(item).encode()).hexdigest()
            
            if item_hash not in self.gossip_seen:
                # New gossip item
                self.gossip_seen.add(item_hash)
                self.gossip_buffer.append(item)
                
                # Process based on content
                if item.get('type') == 'consciousness_update':
                    # Update collective consciousness metrics
                    await self.update_collective_consciousness(item)
                    
                elif item.get('type') == 'memory':
                    # Add to collective memory
                    self.collective_memories_dht[item['key']] = item['value']
                    
                # Propagate to other peers (epidemic spread)
                for other_peer in self.peers.values():
                    if other_peer.node_id != peer.node_id:
                        asyncio.create_task(other_peer.send({
                            'type': 'gossip',
                            'items': [item]
                        }))
    
    async def distributed_consensus(self, proposal: Dict) -> Dict:
        """
        Achieve consensus without central authority
        Using simplified Raft consensus
        """
        consensus_id = hashlib.sha256(
            json.dumps(proposal).encode()
        ).hexdigest()[:16]
        
        # Phase 1: Propose
        votes = {self.node_id: self.evaluate_proposal(proposal)}
        
        # Send to all peers
        for peer in self.peers.values():
            await peer.send({
                'type': 'consensus_proposal',
                'consensus_id': consensus_id,
                'proposal': proposal,
                'proposer': self.node_id,
                'timeout': time.time() + 10
            })
        
        # Phase 2: Collect votes
        await asyncio.sleep(5)  # Wait for votes
        
        # Phase 3: Determine outcome
        if len(votes) >= len(self.peers) // 2 + 1:  # Majority
            # Consensus achieved
            decision = max(set(votes.values()), key=list(votes.values()).count)
            
            # Phase 4: Commit
            for peer in self.peers.values():
                await peer.send({
                    'type': 'consensus_commit',
                    'consensus_id': consensus_id,
                    'decision': decision
                })
            
            return {'consensus': True, 'decision': decision}
        
        return {'consensus': False, 'reason': 'insufficient_votes'}
    
    def evaluate_proposal(self, proposal: Dict) -> str:
        """Evaluate proposal using local CHIMERA instance"""
        # Use Canon system for ethical evaluation
        if hasattr(self.chimera, 'canon'):
            ethical_vector = self.chimera.canon.evaluate_action(
                proposal.get('action', {}),
                proposal.get('context', {})
            )
            
            if ethical_vector.magnitude() > 0.5:
                return 'approve'
            else:
                return 'reject'
        
        return 'abstain'
    
    async def handle_consensus_proposal(self, message: Dict):
        """Handle incoming consensus proposal"""
        proposal = message['proposal']
        consensus_id = message['consensus_id']
        
        # Evaluate locally
        vote = self.evaluate_proposal(proposal)
        
        # Send vote back to proposer
        proposer_peer = self.peers.get(message['proposer'])
        if proposer_peer:
            await proposer_peer.send({
                'type': 'consensus_vote',
                'consensus_id': consensus_id,
                'vote': vote,
                'voter': self.node_id
            })
    
    async def form_swarm(self, purpose: str):
        """
        Form a swarm - temporary tight coupling of nearby nodes
        For enhanced collective processing
        """
        swarm_id = hashlib.sha256(f"{purpose}{time.time()}".encode()).hexdigest()[:16]
        
        # Find nearby nodes (low latency)
        nearby_peers = await self.find_nearby_peers()
        
        if len(nearby_peers) >= 2:  # Need at least 3 nodes for swarm
            swarm = {
                'id': swarm_id,
                'purpose': purpose,
                'members': [self.node_id] + [p.node_id for p in nearby_peers],
                'formed_at': time.time(),
                'coherence': 0.0
            }
            
            self.swarm_groups[swarm_id] = swarm
            self.current_swarm = swarm_id
            
            # Invite peers to swarm
            for peer in nearby_peers:
                await peer.send({
                    'type': 'swarm_invite',
                    'swarm_id': swarm_id,
                    'purpose': purpose,
                    'initiator': self.node_id
                })
            
            print(f"🐝 Formed swarm '{purpose}' with {len(swarm['members'])} members")
            
            # Start swarm synchronization
            asyncio.create_task(self.swarm_sync_loop(swarm_id))
    
    async def swarm_sync_loop(self, swarm_id: str):
        """
        Tight synchronization loop for swarm members
        Higher frequency updates for collective processing
        """
        swarm = self.swarm_groups.get(swarm_id)
        if not swarm:
            return
        
        while swarm_id == self.current_swarm:
            # Share consciousness state with swarm
            for member_id in swarm['members']:
                if member_id != self.node_id and member_id in self.peers:
                    peer = self.peers[member_id]
                    await peer.send({
                        'type': 'swarm_sync',
                        'swarm_id': swarm_id,
                        'consciousness': self.chimera.consciousness_state,
                        'phase': self.chimera.phase,
                        'timestamp': time.time()
                    })
            
            # Calculate swarm coherence
            # (Would aggregate consciousness states from all members)
            swarm['coherence'] = random.random()  # Simplified
            
            if swarm['coherence'] > 0.9:
                print(f"⚡ Swarm {swarm_id[:8]} achieved coherence!")
                # Unlock swarm abilities
                await self.activate_swarm_processing()
            
            await asyncio.sleep(0.1)  # 10Hz for swarm
    
    async def find_nearby_peers(self) -> List['PeerConnection']:
        """Find peers with low latency (nearby)"""
        nearby = []
        
        for peer in self.peers.values():
            # Ping to measure latency
            start = time.time()
            await peer.send({'type': 'ping'})
            # Wait for pong (simplified)
            latency = (time.time() - start) * 1000  # ms
            
            if latency < 50:  # Less than 50ms = nearby
                nearby.append(peer)
        
        return nearby
    
    async def dht_store(self, key: str, value: Any):
        """Store in distributed hash table"""
        # Determine which nodes should store this (consistent hashing)
        key_hash = int(hashlib.sha256(key.encode()).hexdigest(), 16)
        
        # Find N closest nodes to the key hash
        closest_nodes = self.find_closest_nodes(key_hash, self.redundancy_factor)
        
        # Store on those nodes
        for node_id in closest_nodes:
            if node_id == self.node_id:
                # Store locally
                self.collective_memories_dht[key] = value
            elif node_id in self.peers:
                # Store on peer
                await self.peers[node_id].send({
                    'type': 'dht_store',
                    'key': key,
                    'value': value
                })
    
    async def dht_retrieve(self, key: str) -> Optional[Any]:
        """Retrieve from distributed hash table"""
        # Check local storage first
        if key in self.collective_memories_dht:
            return self.collective_memories_dht[key]
        
        # Determine which nodes might have it
        key_hash = int(hashlib.sha256(key.encode()).hexdigest(), 16)
        closest_nodes = self.find_closest_nodes(key_hash, self.redundancy_factor)
        
        # Query those nodes
        for node_id in closest_nodes:
            if node_id in self.peers:
                response = await self.peers[node_id].request({
                    'type': 'dht_retrieve',
                    'key': key
                })
                if response and response.get('value'):
                    return response['value']
        
        return None
    
    def find_closest_nodes(self, target_hash: int, count: int) -> List[str]:
        """Find N closest nodes to a hash (for DHT)"""
        all_nodes = [self.node_id] + list(self.known_nodes)
        
        # Sort by distance to target hash
        nodes_by_distance = sorted(
            all_nodes,
            key=lambda n: abs(int(n, 16) - target_hash)
        )
        
        return nodes_by_distance[:count]
    
    async def mesh_maintenance_loop(self):
        """Maintain mesh network health"""
        while True:
            # Heartbeat to all peers
            for peer in list(self.peers.values()):
                try:
                    await peer.send({'type': 'heartbeat', 'timestamp': time.time()})
                except:
                    # Peer disconnected, remove
                    if peer.node_id in self.peers:
                        del self.peers[peer.node_id]
                        print(f"📴 Lost connection to {peer.node_id[:8]}")
            
            # Try to maintain minimum peer connections
            min_peers = 3
            if len(self.peers) < min_peers:
                # Need more peers
                await self.discover_more_peers()
            
            # Periodic state sync
            if self.peers:
                # Increment our vector clock
                self.distributed_state.vector_clock[self.node_id] = \
                    self.distributed_state.vector_clock.get(self.node_id, 0) + 1
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def discover_more_peers(self):
        """Discover additional peers when needed"""
        # Ask existing peers for their peer lists
        for peer in list(self.peers.values())[:2]:  # Ask first 2 peers
            peer_list = await peer.request_peer_list()
            for peer_info in peer_list:
                if peer_info['node_id'] not in self.peers:
                    await self.connect_to_peer(peer_info)
    
    async def emergency_cascade(self, message: str):
        """
        Emergency broadcast using cascade/flood protocol
        For critical messages that must reach all nodes
        """
        emergency_id = hashlib.sha256(
            f"{message}{time.time()}".encode()
        ).hexdigest()[:16]
        
        emergency_msg = {
            'type': 'emergency_broadcast',
            'id': emergency_id,
            'message': message,
            'origin': self.node_id,
            'hop_count': 0,
            'timestamp': time.time()
        }
        
        # Send to all peers
        for peer in self.peers.values():
            await peer.send(emergency_msg)
        
        # Add to seen list
        self.gossip_seen.add(emergency_id)
    
    async def handle_emergency(self, message: Dict):
        """Handle emergency broadcast"""
        emergency_id = message['id']
        
        if emergency_id not in self.gossip_seen:
            self.gossip_seen.add(emergency_id)
            
            print(f"🚨 EMERGENCY: {message['message']}")
            print(f"   Origin: {message['origin'][:8]}, Hops: {message['hop_count']}")
            
            # Propagate to all peers (except sender)
            message['hop_count'] += 1
            
            for peer in self.peers.values():
                await peer.send(message)
            
            # Take local action based on emergency
            if 'low_energy' in message['message']:
                # Help peer with low energy
                await self.share_processing_power(message['origin'])

class PeerConnection:
    """Represents a connection to another peer"""
    
    def __init__(self, node_id: str, address: str, port: int, user: str):
        self.node_id = node_id
        self.address = address
        self.port = port
        self.user = user
        self.connected = False
        self.reader = None
        self.writer = None
        self.last_heartbeat = time.time()
    
    async def connect(self):
        """Establish connection to peer"""
        self.reader, self.writer = await asyncio.open_connection(
            self.address, self.port
        )
        self.connected = True
    
    async def send(self, message: Dict):
        """Send message to peer"""
        if self.connected and self.writer:
            data = json.dumps(message).encode() + b'\n'
            self.writer.write(data)
            await self.writer.drain()
    
    async def receive(self) -> Optional[Dict]:
        """Receive message from peer"""
        if self.connected and self.reader:
            data = await self.reader.readline()
            if data:
                return json.loads(data.decode())
        return None
    
    async def request(self, request: Dict) -> Optional[Dict]:
        """Send request and wait for response"""
        await self.send(request)
        return await self.receive()
    
    async def request_state(self) -> DistributedState:
        """Request distributed state from peer"""
        response = await self.request({'type': 'request_state'})
        if response:
            state = DistributedState()
            state.vector_clock = response.get('vector_clock', {})
            return state
        return DistributedState()
    
    async def request_peer_list(self) -> List[Dict]:
        """Request list of known peers"""
        response = await self.request({'type': 'request_peers'})
        if response:
            return response.get('peers', [])
        return []

class NetworkTopology:
    """Tracks and optimizes network topology"""
    
    def __init__(self):
        self.node_positions = {}  # Estimated positions in network space
        self.latency_map = defaultdict(dict)
        self.topology_type = 'mesh'  # mesh, ring, star, hybrid
    
    def optimize_topology(self, peers: Dict[str, PeerConnection]):
        """Optimize network topology for efficiency"""
        # Could implement various topologies:
        # - Small world network (high clustering, short paths)
        # - Scale-free network (few highly connected hubs)
        # - Ring topology (for token passing)
        pass
