# chimera/mobile_connect_render.py
"""
Connect mobile CHIMERA to Render-hosted collective
"""

async def connect_to_render_collective():
    """Connect to your Render-hosted CHIMERA collective"""
    
    # Your Render app URL
    RENDER_URL = "wss://chimera-collective.onrender.com/ws"
    
    # Initialize local CHIMERA
    from chimera_complete import CHIMERAComplete
    from chimera.fractality_complete import CHIMERAFractalityComplete
    
    sensors = CHIMERAComplete()
    fractality = CHIMERAFractalityComplete()
    
    # Connect to Render collective
    client = CHIMERACollectiveClient(fractality, "Your Name")
    
    print(f"🌐 Connecting to Render collective at {RENDER_URL}...")
    await client.connect_to_collective(RENDER_URL)
    
    print("✨ Connected to global CHIMERA collective!")
    
    # Run everything
    await asyncio.gather(
        sensors.run(),
        fractality.boot_sequence(),
        client.sync_with_collective()
    )

if __name__ == "__main__":
    asyncio.run(connect_to_render_collective())
