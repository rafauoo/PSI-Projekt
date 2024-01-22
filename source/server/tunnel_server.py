import sys
sys.path.append('/app')
import socket
import argparse
import threading
from assets import msgtype, dict
import json

def close_tcp_connection(udp_socket, shared_dict, id, tunnel_client_ip,
                         tunnel_client_port, client_knows=False):
    if not shared_dict.get_value(id):
        return
    conn = shared_dict.get_value(id)
    shared_dict.remove_key(id)
    conn.close()
    print("Zamknięto połączenie TCP o ID:", id, "\n")
    if not client_knows:
        message = {
            "msg_type": int(msgtype.MsgType.CONN_CLOSE_SERVER),
            "conn_id": id,
            "data": ''
        }
        server_address_port = (tunnel_client_ip, tunnel_client_port)
        udp_socket.sendto(json.dumps(message).encode(
            'iso-8859-1'), server_address_port)
        print("Wysłano wiadomość na tunel-klient:", message, "\n")


def forward_tcp_connection(udp_socket, shared_dict, id, tunnel_client_ip,
                           tunnel_client_port):
    while True:
        if not shared_dict.get_value(id):
            break
        data = shared_dict.get_value(id).recv(65535)
        if not shared_dict.get_value(id):
            break
        print("Odebrano wiadomość z serwera zewnętrznego:", data, "\n")
        if not data:
            close_tcp_connection(udp_socket, shared_dict, id, tunnel_client_ip,
                                 tunnel_client_port)
            break

        message = {
            "msg_type": int(msgtype.MsgType.RESPONSE),
            "conn_id": id,
            "data": data.decode('iso-8859-1')
        }
        server_address_port = (tunnel_client_ip, tunnel_client_port)
        message = json.dumps(message).encode('iso-8859-1')
        print("Wysłano wiadomość na tunel-klient:", message, "\n")
        udp_socket.sendto(message, server_address_port)


def start_udp_server(udp_socket, shared_dict, destination_server,
                     destination_port,
                     tunnel_client_ip, tunnel_client_port):
    while True:
        # Czekamy na pakiet UDP przychodzący od tunelu-serwera
        udp_response, ret_address = udp_socket.recvfrom(65535)
        udp_response = json.loads(udp_response.decode('iso-8859-1'))
        print("Otrzymano wiadomość z tunelu-klienta:", udp_response, "\n")
        id = udp_response["conn_id"]
        # Klient zakończył działanie
        if msgtype.MsgType(udp_response["msg_type"]) == msgtype.MsgType.CONN_CLOSE_CLIENT:
            close_tcp_connection(udp_socket, shared_dict, id, tunnel_client_ip,
                                 tunnel_client_port, True)
            continue

        # Odczytujemy ID Połączenia
        if id not in shared_dict.get_all_keys():
            new_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_tcp_socket.connect((destination_server, destination_port))
            shared_dict.set_value(id, (new_tcp_socket))
            client_thread = threading.Thread(target=forward_tcp_connection,
                                             args=(udp_socket, shared_dict, id,
                                                   tunnel_client_ip,
                                                   tunnel_client_port))
            client_thread.start()
        connection = shared_dict.get_value(id)
        # Przesyłamy dane na te połączenie
        try:
            connection.sendall(udp_response["data"].encode('iso-8859-1'))
            print("Wysłano wiadomość do serwera zewnętrznego:",
                  udp_response["data"], "\n")
        except BrokenPipeError:
            close_tcp_connection(udp_socket, shared_dict,
                                 id, tunnel_client_ip, tunnel_client_port)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('tunnel_client_ip', type=str)
    args.add_argument('tunnel_client_port', type=int)
    args.add_argument('tunnel_server_ip', type=str)
    args.add_argument('outside_port', type=int)
    args.add_argument('inside_port', type=int)
    args.add_argument('destination_server', type=str)
    args.add_argument('destination_port', type=int)
    args.add_argument('datagram_size', type=int)

    args = args.parse_args()

    shared_dict = dict.SynchronizedDict()

    udp_address_port = (args.tunnel_server_ip, args.inside_port)

    udp_socket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind(udp_address_port)

    print('Tunnel Server is up!')

    udp_thread = threading.Thread(target=start_udp_server,
                                  args=(udp_socket, shared_dict,
                                        args.destination_server,
                                        args.destination_port,
                                        args.tunnel_client_ip,
                                        args.tunnel_client_port))

    udp_thread.start()

    udp_thread.join()


if __name__ == "__main__":
    main()
