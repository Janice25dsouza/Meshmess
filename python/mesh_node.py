# python/mesh_node.py
import asyncio
import json
import platform
import random
import websockets

from bleak import BleakScanner
from connection_manager import handshake

MESH_ID = "MESH1234"
NODE_ID = "NODE_A1"

connection_table = {
    "self": NODE_ID,
    "neighbors": []
}


# WebSocket client to send data to the server
async def send_to_dashboard_server():
    uri = "ws://localhost:8000/ws/mesh_node"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to dashboard server.")
                while True:
                    await websocket.send(json.dumps({
                        "type": "topology_update",
                        "payload": connection_table
                    }))
                    await asyncio.sleep(5)  # Send update every 5 seconds
        except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError):
            print("Connection to dashboard server failed. Retrying in 5 seconds...")
            await asyncio.sleep(5)

# -------- Advertiser --------
async def advertise():
    # ... (no change to this function)
    payload = json.dumps({
        "mesh_id": MESH_ID,
        "node_id": NODE_ID,
        "hello": "mesh"
    })
    system = platform.system().lower()
    if system == "linux":
        print(f"[Advertiser] Linux stub. Would broadcast: {payload}")
    elif system == "darwin":
        print(f"[Advertiser] macOS stub. Would broadcast: {payload}")
    elif system == "windows":
        print(f"[Advertiser] Windows stub. Would broadcast: {payload}")
    else:
        print("Unsupported platform for advertising")
    while True:
        await asyncio.sleep(5)

# -------- Scanner --------
async def scan_and_update():
    # ... (no change to this function)
    # This section is already well-implemented to update `connection_table`
    scanner = BleakScanner()
    def callback(device, advertisement_data):
        global connection_table
        manufacturer_data = advertisement_data.manufacturer_data
        for key, value in manufacturer_data.items():
            try:
                payload = json.loads(value.decode('utf-8'))
                if payload.get("mesh_id") == MESH_ID:
                    node_id = payload.get("node_id")
                    neighbor = {"id": node_id, "rssi": advertisement_data.rssi}
                    exists = next((n for n in connection_table["neighbors"] if n["id"] == node_id), None)
                    if exists:
                        exists["rssi"] = advertisement_data.rssi
                    else:
                        connection_table["neighbors"].append(neighbor)
                        asyncio.create_task(handshake(device.address, NODE_ID))
            except Exception:
                continue

    scanner.register_detection_callback(callback)
    await scanner.start()
    print("[Scanner] Scanning for neighbors...")
    while True:
        await asyncio.sleep(10)
        print("[Scanner] Current connection table:")
        print(json.dumps(connection_table, indent=2))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(scan_and_update())
    loop.create_task(advertise())
    loop.create_task(send_to_dashboard_server()) # NEW: Start the client to send data to the server
    loop.run_forever()