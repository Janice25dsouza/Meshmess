# Meshmess

Meshmess is a peer-to-peer chat application that dynamically routes messages using Dijkstra’s algorithm. It is designed for local networks without a central server, providing seamless communication between devices. The project features a user-friendly terminal interface for chatting and a Dashboard for monitoring the MeshNetwork in real time. Using Bluetooth Low Energy (BLE), WebSockets, and efficient algorithms, Meshmess enables lightweight, resilient communication across devices.

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

To start the P2P Chat Application, navigate to the chat folder and run the main script:
```bash
cd chat_mesh_wifi
python main.py
```
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
