import socket
import sys
import struct
import time
from protocol import *

def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python server.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    print(f"Server listening on {host}:{port}")

    users = {}          # username -> addr
    channels = {}       # channel -> set of usernames
    user_channels = {}  # username -> set of channels
    addr_to_user = {}   # address -> username
    last_activity = {}  

    sock.settimeout(5)
    while True:
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            now = time.time()

            for addr, t in list(last_activity.items()):
                if now - t > 120:
                    username = addr_to_user.get(addr)
                    if username:
                        print(f"Timing out {username}")

                        for ch in user_channels.get(username, []):
                            channels[ch].discard(username)

                        user_channels.pop(username, None)
                        addr_to_user.pop(addr, None)
                        last_activity.pop(addr, None)

            continue
        last_activity[addr] = time.time()

        if len(data) < 4:
            continue

        msg_type = struct.unpack("!I", data[:4])[0]

        if msg_type == LOGIN:
            if len(data) < 4 + 32:
                continue

            username = parse_login(data)
            users[username] = addr
            addr_to_user[addr] = username

            print(f"LOGIN: {username} from {addr}")

        elif msg_type == JOIN:
            if len(data) < 4 + 32:
                continue

            channel = parse_join(data)

            username = addr_to_user.get(addr)
            if username is None:
                print("JOIN from unknown user ignored")
                continue

            # Create channel if needed
            if channel not in channels:
                channels[channel] = set()

            channels[channel].add(username)

            if username not in user_channels:
                user_channels[username] = set()

            user_channels[username].add(channel)

            print(f"{username} joined channel {channel}")

        elif msg_type == LEAVE:
            if len(data) < 4 + 32:
                continue

            username = addr_to_user.get(addr)
            if username is None:
                continue

            channel = parse_leave(data)

            if channel in channels and username in channels[channel]:
                channels[channel].remove(username)

                if channel in user_channels:
                    user_channels[username].discard(channel)

                if not channels[channel]:
                    del channels[channel]

                print(f"{username} left channel {channel}")

        elif msg_type == SAY_REQ:
            if len(data) < 4 + 32 + 64:
                continue

            username = addr_to_user.get(addr)
            if username is None:
                continue

            channel, text = parse_say(data)

            if channel not in channels or username not in channels[channel]:
                print(f"Ignoring SAY from {username} to non-joined channel {channel}")
                continue

            print(f"[{channel}][{username}]: {text}")

            packet = pack_say_response(channel, username, text)

            for user in channels[channel]:
                user_addr = users[user]
                sock.sendto(packet, user_addr)

        elif msg_type == LIST_REQ:
            username = addr_to_user.get(addr)
            if username is None:
                continue

            channel_names = list(channels.keys())
            count = len(channel_names)

            packet = struct.pack("!I", LIST_RESP)
            packet += struct.pack("!I", count)

            for ch in channel_names:
                packet += pad_string(ch, 32)

            sock.sendto(packet, addr)

        elif msg_type == WHO_REQ:
            if len(data) < 4 + 32:
                continue

            username = addr_to_user.get(addr)
            if username is None:
                continue

            channel = parse_join(data)

            if channel not in channels:
                continue

            users_list = list(channels[channel])
            count = len(users_list)

            packet = struct.pack("!I", WHO_RESP)
            packet += struct.pack("!I", count)
            packet += pad_string(channel, 32)

            for u in users_list:
                packet += pad_string(u, 32)

            sock.sendto(packet, addr)

        elif msg_type == KEEPALIVE:
            continue

        elif msg_type == LOGOUT:
            username = addr_to_user.get(addr)
            if username:
                print(f"{username} logged out")
                addr_to_user.pop(addr, None)
                last_activity.pop(addr, None)

        else:
            print(f"Unknown message type {msg_type} from {addr}")


if __name__ == "__main__":
    main()
