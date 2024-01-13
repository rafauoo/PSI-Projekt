import socket
import argparse
import struct
HOST_IP = '172.21.23.9'
DATAGRAM_SIZE = 128

def process_datagram(data):
    packet_number, data_length = struct.unpack("<iH", data[:6])
    print(packet_number, data_length)
    if data_length != len(data) - 6:
        print("Error: Data length mismatch")
        return None

    expected_data = bytes((i % 256) for i in range(data_length))
    if data[6:] != expected_data:
        print("Error: Invalid data content")
        return None

    return data_length, packet_number

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("port")
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    server_address_port = (HOST_IP, int(args.port))

    tcp_server_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM)

    tcp_server_socket.bind(server_address_port)

    print(
        f'TCP server up and listening on host {server_address_port[0]}, ' +
        f'port {server_address_port[1]}')
    expected_packet_number = 0

    tcp_server_socket.listen()
    connection, address = tcp_server_socket.accept()
    while True:
        data = connection.recv(DATAGRAM_SIZE)
        if not data:
            break
        data_len, packet_number = process_datagram(data)
        print()
        print("Message: ", data)
        print()
        if packet_number is not None:
            print(f'Received {data_len}B of data from {address}')
            if expected_packet_number != packet_number:
                print(f"Warning: Missing packet, expected {expected_packet_number}, received {packet_number}")
                break
            connection.sendall(packet_number.to_bytes(4, byteorder='little'))
            print(f"Received packet is matched with expected: {expected_packet_number}")
            expected_packet_number += 1
        print("")
        print("")
    connection.close()
