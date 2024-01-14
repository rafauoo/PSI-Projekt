import socket
import argparse
import threading
import struct
from ..assets.msgtype import MsgType
TUNNEL_CLIENT_IP = '172.21.23.9'
TUNNEL_CLIENT_PORT = 12345
TUNNEL_SERVER_IP = '172.21.23.10'
TUNNEL_SERVER_PORT = 12345
DESTINATION_SERVER = '142.250.189.206' #google
DESTINATION_PORT = 80
DATAGRAM_SIZE = 128

def handle_udp_connection(udp_response, connection, address, id):
    client_address_port = (TUNNEL_CLIENT_IP, TUNNEL_CLIENT_PORT)
    # wysyłamy zapytanie TCP do celu
    connection.sendall(udp_response["data"])
    # oczekujemy na wiadomość zwrotną TCP z celu
    data = connection.recv(65535)

    udp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    
    message = {
        "msg_type": MsgType.RESPONSE,
        "conn_id": id,
        "data": data
    }
    # przesyłamy zwrotną wiadomość do tunelu-klienta przez UDP
    udp_socket.sendto(message, client_address_port)


def main():
    server_address_port = (TUNNEL_SERVER_IP, TUNNEL_SERVER_PORT)
    open_connections = {}
    # Tworzymy UDP Socket
    udp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    while True:
        # Czekamy na pakiet UDP przychodzący od tunelu-klienta
        udp_response, ret_address = udp_socket.recvfrom(65535)

        # Jeśli jest to pierwszy pakiet o danym connection_id to
        if udp_response["conn_id"] not in open_connections.keys():
            # tworzymy połączenie tcp z danym destination
            destination_address_port = (DESTINATION_SERVER, DESTINATION_PORT)
            tcp_socket = socket.socket(
                family=socket.AF_INET, type=socket.SOCK_STREAM)
            tcp_socket.bind(destination_address_port)
            connection, address = tcp_socket.accept()

            # zapisujemy to połączenie do późniejszego wykorzystania
            open_connections[udp_response["conn_id"]] = (connection, address)

        # tworzymy wątek dla otrzymanej wiadomości UDP
        client_thread = threading.Thread(target=handle_udp_connection, args=(udp_response, connection, address, id))
        client_thread.start()

if __name__ == "__main__":
    main()