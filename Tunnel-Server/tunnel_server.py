import socket
import argparse
import threading
import struct
import enum
TUNNEL_CLIENT_IP = '172.21.23.9'
TUNNEL_CLIENT_PORT = 12345
TUNNEL_SERVER_IP = '172.21.23.10'
OUTSIDE_PORT = 54321
INSIDE_PORT = 12345
DESTINATION_SERVER = '142.250.189.206' #google
DESTINATION_PORT = 80
DATAGRAM_SIZE = 128

class MsgType(enum.Enum):
    REQUEST = 1
    RESPONSE = 2
    INIT = 3
    CONN_CLOSE_CLIENT = 4
    CONN_CLOSE_SERVER = 5

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
    
    def get_all_keys(self):
        with self._lock:
            return self._data.keys()

def forward_tcp_connection(udp_socket, shared_dict, id):
    while True:
        data = shared_dict.get_value(id).recv()
        if not data:
            # Tu będzie trzeba zrobić obsługę jak user zamknie połączenie TCP
            message = {
                "msg_type": MsgType.CONN_CLOSE_SERVER,
                "conn_id": id,
                "data": data
            }
            conn = shared_dict.get_value(id)
            shared_dict.remove_key(id)
            conn.close()
            return
        
        print(data)
        
        message = {
            "msg_type": MsgType.RESPONSE,
            "conn_id": id,
            "data": data
        }
        server_address_port = (TUNNEL_CLIENT_IP, TUNNEL_CLIENT_PORT)
        
        udp_socket.sendto(message, server_address_port)

def start_udp_server(udp_socket, tcp_socket, shared_dict):
    while True:
        # Czekamy na pakiet UDP przychodzący od tunelu-serwera
        udp_response, ret_address = udp_socket.recvfrom(65535)
        # Odczytujemy ID Połączenia
        if not udp_response["conn_id"] in shared_dict.get_all_keys():
            connection, address = tcp_socket.connect((DESTINATION_SERVER, DESTINATION_PORT))
            shared_dict.set_value(id, (connection, address))
            client_thread = threading.Thread(target=forward_tcp_connection, args=(udp_socket, shared_dict, id))
            client_thread.start()
        connection = shared_dict.get_value(udp_response["conn_id"])
        # Przesyłamy dane na te połączenie
        connection.sendall(udp_response["data"])

def main():
    shared_dict = SynchronizedDict()
    tcp_address_port = (TUNNEL_SERVER_IP, OUTSIDE_PORT)

    tcp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcp_socket.bind(tcp_address_port)

    udp_address_port = (TUNNEL_SERVER_IP, INSIDE_PORT)

    udp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind(udp_address_port)

    print(f'Tunnel Server is up!')
    
    tcp_socket.listen()

    udp_thread = threading.Thread(target=start_udp_server, args=(udp_socket, tcp_socket, shared_dict))

    udp_thread.start()

    udp_thread.join()


if __name__ == "__main__":
    main()