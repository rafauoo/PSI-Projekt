import socket
import argparse
import threading
import struct
import enum
from ..assets.msgtype import MsgType
TUNNEL_CLIENT_IP = '172.21.23.9'
OUTSIDE_PORT = 54321
INSIDE_PORT = 12345
TUNNEL_SERVER_IP = '172.21.23.10'
TUNNEL_SERVER_PORT = 12345

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
            if key in self._data:
                del self._data[key]

    def get_all_items(self):
        with self._lock:
            return dict(self._data)

def forward_tcp_connection(udp_socket, shared_dict, id):
    while True:
        data = shared_dict.get_value(id).recv()
        if not data:
            # Tu będzie trzeba zrobić obsługę jak user zamknie połączenie TCP
            message = {
                "msg_type": MsgType.CONN_CLOSE_CLIENT,
                "conn_id": id,
                "data": data
            }
            conn = shared_dict.get_value(id)
            shared_dict.remove_key(id)
            conn.close()
            return
        
        print(data)
        
        message = {
            "msg_type": MsgType.REQUEST,
            "conn_id": id,
            "data": data
        }
        server_address_port = (TUNNEL_SERVER_IP, TUNNEL_SERVER_PORT)
        
        udp_socket.sendto(message, server_address_port)

def start_tcp_server(udp_socket, tcp_socket, shared_dict):
    id = 0
    while True:
        connection, address = tcp_socket.accept()
        shared_dict.set_value(id, (connection, address))
        client_thread = threading.Thread(target=forward_tcp_connection, args=(udp_socket, shared_dict, id))
        client_thread.start()
        id += 1

def start_udp_server(udp_socket, shared_dict):
    while True:
        # Czekamy na pakiet UDP przychodzący od tunelu-serwera
        udp_response, ret_address = udp_socket.recvfrom(65535)
        # Odczytujemy ID Połączenia
        connection = shared_dict.get_value(udp_response["conn_id"])
        # Przesyłamy dane na te połączenie
        connection.sendall(udp_response["data"])
        

def main():
    shared_dict = SynchronizedDict()
    tcp_address_port = (TUNNEL_CLIENT_IP, OUTSIDE_PORT)
    udp_address_port = (TUNNEL_CLIENT_IP, INSIDE_PORT)

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

    tcp_thread = threading.Thread(target=start_tcp_server, args=(udp_socket, tcp_socket, shared_dict))
    udp_thread = threading.Thread(target=start_udp_server, args=(udp_socket, shared_dict))

    tcp_thread.start()
    udp_thread.start()


if __name__ == "__main__":
    main()
