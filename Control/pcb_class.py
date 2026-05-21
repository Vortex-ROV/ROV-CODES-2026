from PySide6.QtCore import QThread
import socket
import threading
import time


class PCB(QThread):
    BOTTOM_IP = "192.168.33.1"
    BOTTOM_PORT = 5000
    BIND_PORT = 5001
    HB_INTERVAL = 1
    HB_TIMEOUT = 5
    RECONNECT_INTERVAL = 3

    def __init__(self):
        if __name__ != "__main__":
            super().__init__()

        self.__gripper_a = False
        self.__gripper_b = False
        self.__gripper_c = False
        self.__gripper_d = False
        self.__rotate_tool = False
        self.armed = False
        self.connected = False

        self.__sock = None
        self.__stop_event = threading.Event()
        self.__last_hb_from_bottom = 0.0
        self.__reconnect_attempts = 0

    def __make_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.BIND_PORT))
        sock.settimeout(1.0)
        return sock

    def __send_udp(self, message: str):
        if self.__sock is None:
            return
        try:
            self.__sock.sendto(message.encode(), (self.BOTTOM_IP, self.BOTTOM_PORT))
        except OSError as e:
            print(f"[WARN] Send failed: {e}")

    def __send_command(self, cmd: str, description: str):
        if not self.connected:
            print("[WARN] Bottom-side not connected — command not sent")
            return
        self.__send_udp(cmd + "\n")
        print(f"[CMD] Sent '{cmd}' → {description}")

    def control_gripper_a(self):
        self.__gripper_a = not self.__gripper_a
        if self.__gripper_a:
            self.__send_command("C", "Gripper A OPEN  (MOSFET 3 ON)")
        else:
            self.__send_command("c", "Gripper A CLOSE (MOSFET 3 OFF)")
        print("Gripper A:", self.__gripper_a)

    def control_gripper_b(self):
        self.__gripper_b = not self.__gripper_b
        if self.__gripper_b:
            self.__send_command("B", "Gripper B OPEN  (MOSFET 2 ON)")
        else:
            self.__send_command("b", "Gripper B CLOSE (MOSFET 2 OFF)")
        print("Gripper B:", self.__gripper_b)

    def control_gripper_c(self):
        self.__gripper_c = not self.__gripper_c
        if self.__gripper_c:
            self.__send_command("F", "Gripper C OPEN  (MOSFET 6 ON)")
        else:
            self.__send_command("f", "Gripper C CLOSE (MOSFET 6 OFF)")
        print("Gripper C:", self.__gripper_c)

    def control_gripper_d(self):
        self.__gripper_d = not self.__gripper_d
        if self.__gripper_d:
            self.__send_command("D", "Gripper D OPEN  (MOSFET 4 ON)")
        else:
            self.__send_command("d", "Gripper D CLOSE (MOSFET 4 OFF)")
        print("Gripper D:", self.__gripper_d)

    def control_rotating_tool(self):
        self.__rotate_tool = not self.__rotate_tool
        if self.__rotate_tool:
            self.__send_command("E", "Rotating Tool ON  (MOSFET 5 ON)")
        else:
            self.__send_command("e", "Rotating Tool OFF (MOSFET 5 OFF)")
        print("Rotating Tool:", "rotating" if self.__rotate_tool else "not rotating")
    def control_raise_camera(self): pass
    def control_lower_camera(self): pass
    def control_camera_stop(self): pass

    def __heartbeat_sender(self):
        last_reconnect_log = 0.0

        while not self.__stop_event.is_set():
            self.__send_udp("HB_TOP\n")

            if not self.connected:
                now = time.time()
                if now - last_reconnect_log >= self.RECONNECT_INTERVAL:
                    self.__reconnect_attempts += 1
                    print(f"[RECONNECT] Attempt #{self.__reconnect_attempts} — "
                          f"waiting for bottom-side at {self.BOTTOM_IP}:{self.BOTTOM_PORT} ...")
                    last_reconnect_log = now

            time.sleep(self.HB_INTERVAL)

    def __heartbeat_receiver(self):
        while not self.__stop_event.is_set():
            try:
                data, addr = self.__sock.recvfrom(1024)
                msg = data.decode().strip()

                if msg in ("HB_BOT", "PONG"):
                    self.__last_hb_from_bottom = time.time()

                    if not self.connected:
                        self.connected = True
                        self.__reconnect_attempts = 0
                        label = " (reconnected)" if msg == "PONG" else ""
                        print(f"[INFO] Bottom-side connected from {addr[0]}{label}")

            except socket.timeout: pass
            except Exception as e: print(f"[WARN] Receiver error: {e}")
            if (self.connected and
                    (time.time() - self.__last_hb_from_bottom) > self.HB_TIMEOUT):
                self.connected = False
                print("[WARN] Bottom-side heartbeat lost — waiting to reconnect ...")
    def run(self):
        self.__stop_event.clear()
        self.__sock = self.__make_socket()

        print(f"[INFO] PCB thread started — "
              f"listening on :{self.BIND_PORT}, "
              f"target {self.BOTTOM_IP}:{self.BOTTOM_PORT}")

        sender_thread   = threading.Thread(target=self.__heartbeat_sender,
                                           daemon=True, name="pcb-hb-sender")
        receiver_thread = threading.Thread(target=self.__heartbeat_receiver,
                                           daemon=True, name="pcb-hb-receiver")

        sender_thread.start()
        receiver_thread.start()
        self.__stop_event.wait()

        sender_thread.join(timeout=2)
        receiver_thread.join(timeout=2)

    def stop(self):
        self.__stop_event.set()
        self.connected = False
        if self.__sock:
            try:
                self.__sock.close()
            except OSError:
                pass
            self.__sock = None
        self.exit()