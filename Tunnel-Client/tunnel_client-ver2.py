import socket
import argparse
import threading
import struct
import enum
from ..assets.msgtype import MsgType
TUNNEL_CLIENT_IP = '172.21.23.9'
TUNNEL_CLIENT_PORT = 12345
TUNNEL_SERVER_IP = '172.21.23.10'
TUNNEL_SERVER_PORT = 12345

def handle_tcp_connection(connection, address, conn_id):
    while True:
        data = connection.recv()
        if not data:
            connection.close()
            return
        print(data)
        
        message = {
            "msg_type": MsgType.REQUEST,
            "conn_id": conn_id,
            "data": data
        }
        server_address_port = (TUNNEL_SERVER_IP, TUNNEL_SERVER_PORT)

        # Create a UDP socket at client side
        udp_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        udp_socket.sendto(message, server_address_port)

        udp_response, _ = udp_socket.recvfrom(65535)

        print(udp_response)
        print(_)

def main():
    server_address_port = (TUNNEL_CLIENT_IP, TUNNEL_CLIENT_PORT)

    tcp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM)

    tcp_socket.bind(server_address_port)

    print(f'Tunnel Client is up and listening on host {server_address_port[0]}, ' +
        f'port {server_address_port[1]}')
    tcp_socket.listen()
    id = 0
    while True:
        connection, address = tcp_socket.accept()
        client_thread = threading.Thread(target=handle_tcp_connection, args=(connection, address, id))
        client_thread.start()
        id += 1


if __name__ == "__main__":
    main()
