import socket
import sys
import threading
import struct
import time
from protocol import *

def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python client.py <host> <port> <username>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    last_send_time = [time.time()]

    threading.Thread(target=receive_loop, args=(sock,), daemon=True).start()
    threading.Thread(
        target=keepalive_loop,
        args=(sock, host, port, last_send_time),
        daemon=True
    ).start()

    # Send LOGIN
    login_packet = pack_login(username)
    sock.sendto(login_packet, (host, port))
    last_send_time[0] = time.time()
    print(f"Sent LOGIN as '{username}'")

    active_channel = "Common"
    joined_channels = {"Common"}

    # Send JOIN Common automatically
    join_packet = pack_join(active_channel)
    sock.sendto(join_packet, (host, port))
    last_send_time[0] = time.time()
    print("Joined channel 'Common'")

    
    while True:
        line = input("> ")

        if line.startswith("/join"):
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: /join <channel>")
                continue
            channel = parts[1].strip()

            if not channel:
                print("Usage: /join <channel>")
                continue

            sock.sendto(pack_join(channel), (host, port))
            last_send_time[0] = time.time()
            joined_channels.add(channel)
            active_channel = channel
            print(f"Switched to channel '{channel}'")
            continue

        elif line.startswith("/leave"):
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: /join <channel>")
                continue
            channel = parts[1].strip()

            if channel not in joined_channels:
                print("Not subscribed to that channel")
                continue

            sock.sendto(pack_leave(channel), (host, port))
            last_send_time[0] = time.time()
            joined_channels.remove(channel)

            if active_channel == channel:
                active_channel = None
                print("No active channel. Join or switch to one.")
            continue

        elif line.startswith("/switch"):
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: /join <channel>")
                continue
            channel = parts[1].strip()

            if channel not in joined_channels:
                print("You are not subscribed to that channel.")
                continue

            active_channel = channel
            print(f"Switched to {channel}")
            continue

        elif line == "/list":
            sock.sendto(pack_list(), (host, port))
            last_send_time[0] = time.time()
            continue

        elif line.startswith("/who"):
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: /join <channel>")
                continue
            channel = parts[1].strip()

            sock.sendto(pack_who(channel), (host, port))
            last_send_time[0] = time.time()
            continue

        elif line == "/exit":
            sock.sendto(struct.pack("!I", LOGOUT), (host, port))
            last_send_time[0] = time.time()
            print("Goodbye.")
            break

        elif line.startswith("/"):
            print("Unknown command.")
            continue

        if active_channel is None:
            print("No active channel. Join or switch to one.")
            continue

        if not line.strip():
            continue
        
        packet = pack_say(active_channel, line)
        sock.sendto(packet, (host, port))
        last_send_time[0] = time.time()


def receive_loop(sock: socket.socket):
    sock.settimeout(5)

    while True:
        try:
            data, _ = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except OSError:
            break

        if len(data) < 4:
            continue

        msg_type = struct.unpack("!I", data[:4])[0]

        if msg_type == SAY_RESP:
            channel = data[4:36].rstrip(b'\0').decode()
            username = data[36:68].rstrip(b'\0').decode()
            text = data[68:132].rstrip(b'\0').decode()

            print(f"\n[{channel}][{username}]: {text}")
            print("> ", end="", flush=True)
        
        elif msg_type == LIST_RESP:
            count = struct.unpack("!I", data[4:8])[0]

            print("\nExisting channels:")
            offset = 8
            for _ in range(count):
                channel = data[offset:offset+32].rstrip(b'\0').decode()
                print(" ", channel)
                offset += 32

            print("> ", end="", flush=True)

        elif msg_type == WHO_RESP:
            count = struct.unpack("!I", data[4:8])[0]
            channel = data[8:40].rstrip(b'\0').decode()

            print(f"\nUsers on channel {channel}:")

            offset = 40
            for _ in range(count):
                user = data[offset:offset+32].rstrip(b'\0').decode()
                print(" ", user)
                offset += 32

            print("> ", end="", flush=True)


def keepalive_loop(sock, host, port, last_send_time):
    while True:
        time.sleep(5)
        if time.time() - last_send_time[0] > 60:
            sock.sendto(pack_keepalive(), (host, port))
            last_send_time[0] = time.time()
            

if __name__ == "__main__":
    main()
