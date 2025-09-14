// dashboard/client/src/App.jsx
import React, { useEffect, useState, useRef } from 'react';
import { Network } from 'vis-network';
import 'vis-network/styles/vis-network.css';

function App() {
  const visRef = useRef(null);
  const networkRef = useRef(null);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');
    wsRef.current = ws;
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "topology") {
        const n = msg.payload.neighbors.map(neighbor => ({
          id: neighbor.id,
          label: neighbor.id,
          title: `RSSI: ${neighbor.rssi}`,
          color: '#00ff00'
        }));
        const e = msg.payload.neighbors.map(neighbor => ({
          from: msg.payload.self,
          to: neighbor.id,
          label: `${neighbor.rssi}`
        }));
        setNodes([{ id: msg.payload.self, label: msg.payload.self, color: '#0000ff' }, ...n]);
        setEdges(e);
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (!visRef.current) return;
    const data = { nodes, edges };
    const options = { physics: { stabilization: true }, nodes: { shape: 'dot', size: 16 } };
    if (!networkRef.current) {
      networkRef.current = new Network(visRef.current, data, options);
    } else {
      networkRef.current.setData(data);
    }
  }, [nodes, edges]);

  return <div style={{ height: '100vh' }} ref={visRef}></div>;
}

export default App;