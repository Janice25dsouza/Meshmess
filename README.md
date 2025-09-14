# Meshmess - ForestLink

**Meshmess** a peer-to-peer mesh networking app that enables communication when conventional networks fail and works through Wi-Fi Direct with multi-hop routing powered by Dijkstra’s algorithm.

**ForestLink** is a a BLE mesh system  where roadside nodes relay data to a central dashboard, with monitoring.


The project is built with Python 3, Rust, and JavaScript. Python handles the core chat logic using libraries such as `asyncio`, `socket`, `networkx`, `colorama`, and `aioconsole`. Rust powers performance-critical operations with `Tokio` and BLE integration through `Bleak`. The frontend dashboard is built with Vite and WebSockets to monitor the MeshNetwork visually.

## Technologies Used

- **Python 3** – Backend logic and peer communication  
- **Rust** – Performance and BLE management  
- **JavaScript** – Frontend dashboard  
- `asyncio`, `socket`, `networkx`, `colorama`, `aioconsole`  
- `Bleak`, `Tokio`  
- `Vite`, WebSockets  
- Bluetooth Low Energy (BLE) for mesh networking

## How to Run

**Meshmess:**

To start the P2P Chat Application, navigate to the chat folder and run the main script:
```bash
cd chat_mesh_wifi
python main.py
```
**ForestLink:**

For the MeshNetwork Monitoring system, first start the mesh node:
```bash
cd python
python mesh_node.py

Then, open a new terminal, navigate to the dashboard, and start the frontend:

cd dashboard/client
npm run dev
```
## Requirements

- **Python 3.x**  
- **Rust toolchain** with `cargo`  
- **Node.js & npm**  
- A **Bluetooth Low Energy (BLE)** supported device  
- A **web browser** to access the monitoring dashboard  

---

## ▶ Demonstration

Watch the full project walkthrough and explanation on YouTube:  
➡ [https://www.youtube.com/watch?v=9aQLiUdBN5M](https://www.youtube.com/watch?v=9aQLiUdBN5M)

---

## 📜 License

This project is open-source and released under the **MIT License**. Feel free to use, modify, and share it!
