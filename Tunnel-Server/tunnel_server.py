import socket
import argparse
import threading
import json
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

    def __str__(self):
        return str(self.value)

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

def close_tcp_connection(udp_socket, shared_dict, id, client_knows=False):
    if not shared_dict.get_value(id):
        return
    conn = shared_dict.get_value(id)
    shared_dict.remove_key(id)
    conn.close()
    print("Zamknięto połączenie TCP o ID:", id, "\n")
    if not client_knows:
        message = {
            "msg_type": 5,
            "conn_id": id,
            "data": ''
        }
        server_address_port = (TUNNEL_CLIENT_IP, TUNNEL_CLIENT_PORT)
        udp_socket.sendto(json.dumps(message).encode('utf-8'), server_address_port)
        print("Wysłano wiadomość na tunel-klient:", message, "\n")

def forward_tcp_connection(udp_socket, shared_dict, id):
    while True:
        if not shared_dict.get_value(id):
            return
        data = shared_dict.get_value(id).recv(65535)
        print("Odebrano wiadomość z serwera zewnętrznego:", data, "\n")
        if not data:
            # Tu będzie trzeba zrobić obsługę jak user zamknie połączenie TCP
            close_tcp_connection(udp_socket, shared_dict, id)
            return
        
        message = {
            "msg_type": 2,
            "conn_id": id,
            "data": data.decode('utf-8')
        }
        server_address_port = (TUNNEL_CLIENT_IP, TUNNEL_CLIENT_PORT)
        message = json.dumps(message).encode('utf-8')
        print("Wysłano wiadomość na tunel-klient:", message, "\n")
        udp_socket.sendto(message, server_address_port)

def start_udp_server(udp_socket, shared_dict):
    while True:
        # Czekamy na pakiet UDP przychodzący od tunelu-serwera
        udp_response, ret_address = udp_socket.recvfrom(65535)
        udp_response = json.loads(udp_response.decode('utf-8'))
        print("Otrzymano wiadomość z tunelu-klienta:", udp_response, "\n")
        id = udp_response["conn_id"]
        # Klient zakończył działanie
        if udp_response["msg_type"] == 4:
            close_tcp_connection(udp_socket, shared_dict, id, True)
            continue
        # Odczytujemy ID Połączenia
        if not id in shared_dict.get_all_keys():
            new_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_tcp_socket.connect((DESTINATION_SERVER, DESTINATION_PORT))
            shared_dict.set_value(id, (new_tcp_socket))
            client_thread = threading.Thread(target=forward_tcp_connection, args=(udp_socket, shared_dict, id))
            client_thread.start()
        connection = shared_dict.get_value(id)
        # Przesyłamy dane na te połączenie
        try:
            connection.sendall(udp_response["data"].encode('utf-8'))
            print("Wysłano wiadomość do serwera zewnętrznego:", udp_response["data"], "\n")
        except BrokenPipeError as e:
            close_tcp_connection(udp_socket, shared_dict, id)

def main():
    shared_dict = SynchronizedDict()

    udp_address_port = (TUNNEL_SERVER_IP, INSIDE_PORT)

    udp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind(udp_address_port)

    print(f'Tunnel Server is up!')

    udp_thread = threading.Thread(target=start_udp_server, args=(udp_socket, shared_dict))

    udp_thread.start()

    udp_thread.join()


if __name__ == "__main__":
    main()