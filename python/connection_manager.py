# connection_manager.py
import asyncio
import json
import time
from bleak import BleakClient

HANDSHAKE_UUID = "0000abcd-0000-1000-8000-00805f9b34fb"  # Example UUID

async def handshake(device_address, node_id):
    async with BleakClient(device_address) as client:
        try:
            await client.connect()
            handshake_data = {
                "node_id": node_id,
                "status": "ready",
                "timestamp": int(time.time())
            }
            await client.write_gatt_char(HANDSHAKE_UUID, json.dumps(handshake_data).encode())
            print(f"Handshake sent to {device_address}")
        except Exception as e:
            print(f"Failed to handshake with {device_address}: {e}")

# Example usage
if __name__ == "__main__":
    address = "AA:BB:CC:DD:EE:FF"  # Replace with actual device address
    node_id = "NODE_A1"
    asyncio.run(handshake(address, node_id))
