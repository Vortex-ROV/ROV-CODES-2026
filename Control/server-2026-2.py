import socket
import serial
import time

HOST = "192.168.33.1"
PORT = 12345
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

{"Mosfet1": 0, "Mosfet2": 0, "Mosfet3": 0, "Mosfet4": 0, "Mosfet5": 0, "Mosfet6": 0, "Mosfet7": 0, "bilge": 0, "angle": 1500, "servo_direction": 0}

def handle_client(conn, addr, arduino):
    print(f"Client connected from {addr}")
    buffer = ""
    last_time_received = time.time()
    try:
        while True:
            if last_time_received - time.time() > 5:
                print("no heartbeat received for a while, disconnecting")
                conn.close()
                break
            data = conn.recv(1024).decode()
            if not data:
                print(f"Client {addr} disconnected.")
                break
            if "heartbeat" in data:
                print("got heartbeat")
                last_time_received = time.time()
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1) 
                line = line.strip()
                if line:
                    print(line)
                    arduino.write((line + "\n").encode())
                    last_time_received = time.time()

    except ConnectionResetError:
        print(f"Client {addr} disconnected unexpectedly.")
    finally:
        conn.close()


def main():
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print("Connected to Arduino.")

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)
    print(f"Server listening on {HOST}:{PORT}...")

    try:
        while True:
            conn, addr = server_sock.accept()
            handle_client(conn, addr, arduino)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        server_sock.close()
        arduino.close()


if __name__ == "__main__":
    main()