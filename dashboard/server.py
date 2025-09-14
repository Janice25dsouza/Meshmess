# dashboard/server.py
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

connected_dashboard_clients = set()
mesh_node_client = None
current_topology = {
    "self": "NODE_A1",
    "neighbors": []
}

@app.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_dashboard_clients.add(websocket)
    try:
        # Send initial topology on connection
        await websocket.send_text(json.dumps({"type": "topology", "payload": current_topology}))
        while True:
            await websocket.receive_text() # Listen for messages but don't do anything
    except WebSocketDisconnect:
        connected_dashboard_clients.remove(websocket)

@app.websocket("/ws/mesh_node")
async def websocket_mesh_node_endpoint(websocket: WebSocket):
    global mesh_node_client
    await websocket.accept()
    mesh_node_client = websocket
    print("Mesh node connected.")
    try:
        while True:
            data = await websocket.receive_text()
            global current_topology
            msg = json.loads(data)
            if msg.get("type") == "topology_update":
                current_topology = msg.get("payload")
                print("Received topology update from mesh node:", current_topology)
                # Broadcast the new topology to all connected dashboard clients
                for client in list(connected_dashboard_clients):
                    await client.send_text(json.dumps({"type": "topology", "payload": current_topology}))
    except WebSocketDisconnect:
        print("Mesh node disconnected.")
        mesh_node_client = None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)