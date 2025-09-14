# scanner.py
import asyncio
import json
from bleak import BleakScanner

MESH_ID = "MESH1234"

async def scan():
    def callback(device, advertisement_data):
        manufacturer_data = advertisement_data.manufacturer_data
        for key, value in manufacturer_data.items():
            try:
                payload = json.loads(value.decode('utf-8'))
                if payload.get("mesh_id") == MESH_ID:
                    print(f"Discovered node {payload.get('node_id')} at {device.address}")
            except Exception:
                continue

    scanner = BleakScanner()
    scanner.register_detection_callback(callback)
    await scanner.start()
    print("Scanning for mesh nodes...")
    await asyncio.sleep(60)  # scan for 60 seconds
    await scanner.stop()

if __name__ == "__main__":
    asyncio.run(scan())
