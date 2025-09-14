import asyncio
import socket
import threading
import time
import json
import uuid
from collections import deque
import colorama
from colorama import Fore, Style
import aioconsole
import networkx as nx
from datetime import datetime

# --- Initialize Libraries & Constants ---
colorama.init(autoreset=True)
PORT = 8888
BROADCAST_PORT = 9999

# --- Global State ---
peers = set()
available_peers = {}  # Dict: {ip: name}
peer_lock = threading.Lock()
seen_message_ids = deque(maxlen=200)
connected_peers_info = {}  # Dict: {ip: name}
USER_NAME = ""  # Will be set at runtime

def get_local_ip():
    """Gets the machine's local IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
connected_peers_info[LOCAL_IP] = USER_NAME

# --- Message & UI Formatting ---
def format_message(sender_ip, message, is_self=False, color=None, hops=0, is_private=False):
    """Formats messages with timestamp, color, and optional hop info."""
    if color is None: color = Fore.CYAN
    sender_name = connected_peers_info.get(sender_ip, sender_ip)
    timestamp = datetime.now().strftime("%H:%M:%S")
    if is_self:
        sender, color = f"Me ({USER_NAME})", Fore.GREEN
    elif sender_ip == "System":
        sender, color = "System", Fore.YELLOW
    else:
        sender = sender_name
    hop_info = f" (via {hops} hop{'s' if hops != 1 else ''})" if hops > 0 else ""
    pm_info = "[Private] " if is_private else ""
    return f"{color}[{timestamp}] {pm_info}{sender}{hop_info}:{Style.RESET_ALL} {message}"

async def print_peers():
    with peer_lock:
        peer_list = sorted(list(available_peers.items()))
    if not peer_list:
        await aioconsole.aprint(format_message("System", "No peers found.", color=Fore.YELLOW))
        return
    await aioconsole.aprint(Fore.MAGENTA + "╔═ Available Peers ═════════╗")
    for i, (ip, name) in enumerate(peer_list):
        await aioconsole.aprint(f"  [{i}] {name} ({ip})")
    await aioconsole.aprint(Fore.MAGENTA + "╚═════════════════════════╝")

async def print_network_map(routing_manager):
    await aioconsole.aprint(Fore.CYAN + "╔═ Network Map ═════════╗")
    for node, neighbors in routing_manager.topology.adjacency():
        node_name = connected_peers_info.get(node, node)
        neighbor_names = [connected_peers_info.get(n, n) for n in neighbors]
        await aioconsole.aprint(f"  {node_name} -> [{', '.join(neighbor_names)}]")
    await aioconsole.aprint(Fore.CYAN + "╚═══════════════════════╝")

# --- Dijkstra Routing Manager ---
class RoutingManager:
    def __init__(self, local_ip, peers_set):
        self.local_ip, self.peers = local_ip, peers_set
        self.topology = nx.Graph()
        self.topology.add_node(local_ip)
        self.link_state_seq = 0
        self.last_lsa_seq = {}

    def get_link_state_packet(self):
        self.link_state_seq += 1
        neighbors = {w.get_extra_info('peername')[0]: 1 for w in self.peers if w.get_extra_info('peername')}
        return {"type": "lsa", "id": str(uuid.uuid4()), "source": self.local_ip, "seq": self.link_state_seq, "neighbors": neighbors}

    def update_topology(self, lsa):
        source, seq = lsa["source"], lsa["seq"]
        if seq > self.last_lsa_seq.get(source, -1):
            self.last_lsa_seq[source] = seq
            self.topology.add_node(source)
            self.topology.remove_edges_from(list(self.topology.edges(source)))
            for neighbor, weight in lsa["neighbors"].items():
                self.topology.add_edge(source, neighbor, weight=weight)
            return True
        return False

    def get_next_hop(self, destination_ip):
        try:
            path = nx.dijkstra_path(self.topology, self.local_ip, destination_ip)
            return path[1] if len(path) > 1 else None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    async def broadcast_lsa(self):
        while True:
            await asyncio.sleep(10)
            lsa_packet = self.get_link_state_packet()
            seen_message_ids.append(lsa_packet["id"])
            lsa_json = json.dumps(lsa_packet) + "\n"
            for writer in list(self.peers):
                try:
                    writer.write(lsa_json.encode())
                    await writer.drain()
                except:
                    self.peers.discard(writer)

# --- Connection Management ---
async def manage_connection(reader, writer, routing_manager):
    peer_ip = writer.get_extra_info('peername')[0]
    try:
        handshake = {"type": "handshake", "name": USER_NAME}
        writer.write((json.dumps(handshake) + "\n").encode()); await writer.drain()
        
        while True:
            line = await reader.readline()
            if not line: break
            try:
                message_data = json.loads(line.decode())
                msg_id = message_data.get("id")
                if msg_id and msg_id in seen_message_ids: continue
                if msg_id: seen_message_ids.append(msg_id)
                msg_type = message_data.get("type")

                if msg_type == "handshake":
                    peer_name = message_data.get("name", "Unknown")
                    connected_peers_info[peer_ip] = peer_name
                    peers.add(writer)
                    await aioconsole.aprint(format_message("System", f"🔗 {peer_name} ({peer_ip}) connected."))
                
                elif msg_type == "lsa":
                    if routing_manager.update_topology(message_data):
                        for p_writer in list(peers):
                            if p_writer != writer: 
                                p_writer.write(line); await p_writer.drain()
                
                elif msg_type == "chat":
                    dest = message_data.get("destination_ip")
                    if dest == routing_manager.local_ip or dest == "all":
                        await aioconsole.aprint(format_message(
                            message_data["origin_ip"], message_data["payload"],
                            hops=message_data["hops"], is_private=(dest != "all")))
                    
                    if dest != routing_manager.local_ip:
                        message_data["hops"] += 1; forward_msg = json.dumps(message_data) + "\n"
                        if dest == "all":
                            for p_writer in list(peers):
                                if p_writer != writer:
                                    p_writer.write(forward_msg.encode()); await p_writer.drain()
                        else:
                            next_hop = routing_manager.get_next_hop(dest)
                            if next_hop:
                                for p_writer in list(peers):
                                    p_info = p_writer.get_extra_info('peername')
                                    if p_info and p_info[0] == next_hop:
                                        p_writer.write(forward_msg.encode()); await p_writer.drain(); break
            except: pass
    except: pass
    finally:
        peer_name = connected_peers_info.pop(peer_ip, peer_ip)
        await aioconsole.aprint(format_message("System", f"🏃 {peer_name} disconnected."))
        peers.discard(writer)
        if routing_manager.topology.has_node(peer_ip): routing_manager.topology.remove_node(peer_ip)
        if not writer.is_closing(): writer.close(); await writer.wait_closed()

async def connect_to_peer(ip, routing_manager):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, PORT), timeout=5)
        asyncio.create_task(manage_connection(reader, writer, routing_manager))
    except Exception as e:
        await aioconsole.aprint(format_message("System", f"❌ Failed to connect to {ip}: {e}", color=Fore.RED))

async def handle_peer(reader, writer, routing_manager):
    asyncio.create_task(manage_connection(reader, writer, routing_manager))

# --- UDP Discovery Threads ---
def udp_broadcast_task():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            try:
                message = f"{USER_NAME}|{LOCAL_IP}"; sock.sendto(message.encode(), ("255.255.255.255", BROADCAST_PORT))
            except: pass
            time.sleep(5)

def udp_listen_task():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', BROADCAST_PORT))
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                name, ip = data.decode().split('|', 1)
                if ip != LOCAL_IP:
                    with peer_lock: available_peers[ip] = name
            except: pass

# --- Main UI Loop ---
async def chat_interface(routing_manager):
    await aioconsole.aprint(format_message("System", f"Welcome, {USER_NAME}! Dijkstra routing is active. Type '/h' for help."))
    await aioconsole.aprint(format_message("System", "Use '/s' to check available peers and '/connect <number>' to connect to a peer.", color=Fore.YELLOW))
    while True:
        user_input = await aioconsole.ainput(Fore.WHITE + "> ")
        if not user_input: continue
        if user_input.startswith('/'):
            parts = user_input.split(); command = parts[0].lower()
            if command == '/s': await print_peers()
            elif command == '/connect':
                if len(parts) < 2: await aioconsole.aprint(format_message("System", "Usage: /connect <id>", color=Fore.RED)); continue
                try:
                    choice = int(parts[1])
                    with peer_lock: peer_list = sorted(list(available_peers.items()))
                    if 0 <= choice < len(peer_list): asyncio.create_task(connect_to_peer(peer_list[choice][0], routing_manager))
                    else: await aioconsole.aprint(format_message("System", "That ID is not in the list.", color=Fore.RED))
                except: await aioconsole.aprint(format_message("System", "Invalid selection.", color=Fore.RED))
            elif command == '/map': await print_network_map(routing_manager)
            elif command == '/msg':
                if len(parts) < 3: await aioconsole.aprint(format_message("System", "Usage: /msg <ip_address> <message>", color=Fore.RED)); continue
                dest_ip, payload = parts[1], " ".join(parts[2:])
                next_hop = routing_manager.get_next_hop(dest_ip)
                if not next_hop: await aioconsole.aprint(format_message("System", f"No path to {dest_ip} found.", color=Fore.RED)); continue
                msg_id = str(uuid.uuid4())
                message_data = {"type": "chat", "id": msg_id, "origin_ip": LOCAL_IP, "destination_ip": dest_ip, "hops": 0, "payload": payload}
                seen_message_ids.append(msg_id)
                await aioconsole.aprint(format_message(LOCAL_IP, payload, is_self=True, is_private=True))
                for writer in list(peers):
                    p_info = writer.get_extra_info('peername')
                    if p_info and p_info[0] == next_hop: writer.write((json.dumps(message_data) + "\n").encode()); await writer.drain(); break
            elif command == '/h':
                await aioconsole.aprint(format_message("System", "Commands:\n  /s - show peers\n  /connect <id> - connect to peer\n  /map - show network map\n  /msg <ip> <message> - private message\n  /q - quit"))
            elif command == '/q': break
            else: await aioconsole.aprint(format_message("System", "Unknown command."))
        else:
            msg_id = str(uuid.uuid4())
            message_data = {"type": "chat", "id": msg_id, "origin_ip": LOCAL_IP, "destination_ip": "all", "hops": 0, "payload": user_input}
            seen_message_ids.append(msg_id)
            await aioconsole.aprint(format_message(LOCAL_IP, user_input, is_self=True))
            for writer in list(peers): writer.write((json.dumps(message_data) + "\n").encode()); await writer.drain()

# --- Main Application ---
async def main():
    global USER_NAME
    while not USER_NAME:
        USER_NAME = input("Please enter your name: ").strip()
    connected_peers_info[LOCAL_IP] = USER_NAME
    print("--- P2P Dijkstra Mesh Chat ---"); print(f"[Info] Your IP: {LOCAL_IP}")
    
    routing_manager = RoutingManager(LOCAL_IP, peers)
    
    server = await asyncio.start_server(lambda r, w: handle_peer(r, w, routing_manager), LOCAL_IP, PORT)
    
    loop = asyncio.get_running_loop()
    
    await asyncio.gather(
        server.serve_forever(),
        loop.run_in_executor(None, udp_broadcast_task),
        loop.run_in_executor(None, udp_listen_task),
        chat_interface(routing_manager),
        routing_manager.broadcast_lsa()
    )

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError): pass
    finally: print("\nExiting...")