import socket
import argparse
import threading
# from assets.msgtype import MsgType
import enum
import json


class MsgType(enum.IntEnum):
    REQUEST = 1
    RESPONSE = 2
    INIT = 3
    CONN_CLOSE_CLIENT = 4
    CONN_CLOSE_SERVER = 5

# TUNNEL_SERVER_IP = '172.21.23.10'
# TUNNEL_SERVER_PORT = 12345
# TUNNEL_CLIENT_IP = '172.21.23.9'
# OUTSIDE_PORT = 54321
# INSIDE_PORT = 12345


class SynchronizedDict:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def set_value(self, key, value):
        with self._lock:
            self._data[key] = value

    def get_value(self, key):
        with self._lock:
            return self._data.get(key)

    def remove_key(self, key):
        with self._lock:
            try:
                del self._data[key]
            except KeyError:
                pass  # Key not present, no need to remove

    def get_all_items(self):
        with self._lock:
            return dict(self._data)
        
def close_tcp_connection(udp_socket, shared_dict, id, tunnel_server_ip, 
                         tunnel_server_port, server_knows=False):
    if not shared_dict.get_value(id):
        return
    conn = shared_dict.get_value(id)[0]
    conn.sendall("\nPołączenie zostało zerwane!\n".encode('utf-8'))
    shared_dict.remove_key(id)
    conn.close()
    print("Zamknięto połączenie TCP o ID:", id, "\n")
    if not server_knows:
        message = {
            "msg_type": int(MsgType.CONN_CLOSE_CLIENT),
            "conn_id": id,
            "data": ''
        }
        server_address_port = (tunnel_server_ip, tunnel_server_port)
        udp_socket.sendto(json.dumps(message).encode('utf-8'), server_address_port)
        print("Wysłano wiadomość na tunel-serwer:", message)

def forward_tcp_connection(udp_socket, shared_dict, id, 
                           tunnel_server_ip, tunnel_server_port):
    while True:
        if not shared_dict.get_value(id):
            break
        data = shared_dict.get_value(id)[0].recv(65535)
        if not shared_dict.get_value(id):
            break
        print("Odebrano wiadomość od klienta:", data, "\n")
        if not data:
            close_tcp_connection(udp_socket, shared_dict, id, 
                                 tunnel_server_ip, tunnel_server_port)
            break
        
        message = {
            "msg_type": int(MsgType.REQUEST),
            "conn_id": id,
            "data": data.decode('utf-8')
        }
        print("Wysłano wiadomość na tunel-serwer:", message, "\n")
        server_address_port = (tunnel_server_ip, tunnel_server_port)
        message = json.dumps(message).encode('utf-8')
        udp_socket.sendto(message, server_address_port)

def start_tcp_server(udp_socket, tcp_socket, shared_dict, tunnel_server_ip, tunnel_server_port):
    id = 0
    while True:
        connection, address = tcp_socket.accept()
        print("Zaakceptowano połączenie o ID:", id, "\n")
        shared_dict.set_value(id, (connection, address))
        client_thread = threading.Thread(target=forward_tcp_connection, 
                                         args=(udp_socket, shared_dict, id, 
                                               tunnel_server_ip, tunnel_server_port))
        client_thread.start()
        id += 1

def start_udp_server(udp_socket, shared_dict, tunnel_server_ip, tunnel_server_port):
    while True:
        # Czekamy na pakiet UDP przychodzący od tunelu-serwera
        udp_response, ret_address = udp_socket.recvfrom(65535)
        udp_response = json.loads(udp_response.decode('utf-8'))
        id = udp_response["conn_id"]
        print("Otrzymano wiadomość z tunelu-serwera:", udp_response, "\n")
        if MsgType(udp_response["msg_type"]) == MsgType.CONN_CLOSE_CLIENT:
            close_tcp_connection(udp_socket, shared_dict, id, 
                                 tunnel_server_ip, tunnel_server_port, True)
            continue
        # Odczytujemy ID Połączenia
        connection = shared_dict.get_value(id)[0]
        # Przesyłamy dane na te połączenie
        try:
            connection.sendall(udp_response["data"].encode('utf-8'))
            print("Wysłano wiadomość do klienta:", udp_response["data"], "\n")
        except BrokenPipeError as e:
            close_tcp_connection(udp_socket, shared_dict, id, 
                                 tunnel_server_ip, tunnel_server_port)
        

def main():
    args = argparse.ArgumentParser()
    args.add_argument('tunnel_server_ip', type=str)
    args.add_argument('tunnel_server_port', type=int)
    args.add_argument('tunnel_client_ip', type=str)
    args.add_argument('outside_port', type=int)
    args.add_argument('inside_port', type=int)

    args = args.parse_args()

    shared_dict = SynchronizedDict()
    tcp_address_port = (args.tunnel_client_ip, args.outside_port)
    udp_address_port = (args.tunnel_client_ip, args.inside_port)

    # Tworzymy UDP Socket
    udp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind(udp_address_port)
    
    tcp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcp_socket.bind(tcp_address_port)

    print(f'Tunnel Client is up and listening on host {tcp_address_port[0]}, ' +
        f'port {tcp_address_port[1]}')
    
    tcp_socket.listen()

    tcp_thread = threading.Thread(target=start_tcp_server, args=(udp_socket, tcp_socket, shared_dict,
                                                                 args.tunnel_server_ip, args.tunnel_server_port))
    udp_thread = threading.Thread(target=start_udp_server, args=(udp_socket, shared_dict,
                                                                 args.tunnel_server_ip, args.tunnel_server_port))

    tcp_thread.start()
    udp_thread.start()

    tcp_thread.join()
    udp_thread.join()


if __name__ == "__main__":
    main()
