# server.py
import json
import queue
import serial
import grpc
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import pcb_service_pb2 as pb2
import pcb_service_pb2_grpc as pb2_grpc
from google.protobuf import empty_pb2

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
GRPC_HOST = "192.168.33.1"
GRPC_PORT = 12345

HEARTBEAT_TIMEOUT = 5

arduino_state = {
    "Mosfet1": 0, "Mosfet2": 0, "Mosfet3": 0, "Mosfet4": 0,
    "Mosfet5": 0, "Mosfet6": 0, "Mosfet7": 0, "bilge": 0, 
    "angle": 1500, "servo_direction": 0
}

def apply_mosfet(msg: pb2.MosfetControl):
    arduino_state["Mosfet1"] = int(msg.mosfet_1)
    arduino_state["Mosfet2"] = int(msg.mosfet_2)
    arduino_state["Mosfet3"] = int(msg.mosfet_3)
    arduino_state["Mosfet4"] = int(msg.mosfet_4)
    arduino_state["Mosfet5"] = int(msg.mosfet_5)
    arduino_state["Mosfet6"] = int(msg.mosfet_6)
    arduino_state["Mosfet7"] = int(msg.mosfet_7)

def apply_servo(msg: pb2.ServoControl):
    arduino_state["angle"] = msg.angle
    arduino_state["servo_direction"] = msg.raise_lower

def apply_bilge(msg: pb2.BilgeControl):
    arduino_state["bilge"] = msg.speed


class PCBServiceServicer(pb2_grpc.PCBServiceServicer):
    def __init__(self, arduino: serial.Serial):
        self.arduino = arduino
        self.__clients: dict = {}

        threading.Thread(target=self.__watchdog, daemon=True, name="watchdog").start()

    def __watchdog(self):
        while True:
            now = time.time()
            timed_out = [
                peer for peer, rec in self.__clients.items()
                if now - rec["last_heartbeat"] > HEARTBEAT_TIMEOUT
            ]
            for peer in timed_out:
                print(f"[WATCHDOG] {peer} timed out, evicting")
                self.__evict(peer)
            time.sleep(1.0)

    def __evict(self, peer: str):
        rec = self.__clients.pop(peer, None)
        if rec is None:
            return
        rec["context"].abort(grpc.StatusCode.DEADLINE_EXCEEDED, "Heartbeat timeout")
        print(f"[SERVER] {peer} evicted")

    def __cleanup(self, peer: str):
        with self._clients_lock:
            self._clients.pop(peer, None)
        print(f"[SERVER] Session closed for {peer}")

    def Session(self, request_iterator, context: grpc.ServicerContext):
        peer = context.peer()
        print(f"[SERVER] Client connected: {peer}")

        self.__clients[peer] = {
            "last_heartbeat": time.time(),
            "context": context,
        }

        def __reader():
            try:
                for message in request_iterator:
                    if peer in self.__clients:
                        self.__clients[peer]["last_heartbeat"] = time.time()

                    kind = message.WhichOneof("payload")

                    if kind == "mosfet_control": apply_mosfet(message.mosfet_control)
                    elif kind == "servo_control": apply_servo(message.servo_control)
                    elif kind == "bilge_control": apply_bilge(message.bilge_control)
                    else:
                        print(f"[{peer}] Unknown payload type: {kind}")
                        continue

                    payload = json.dumps(arduino_state) + "\n"
                    print(f"[{peer}] → Arduino: {payload.strip()}")
                    self.arduino.write(payload.encode())

            except grpc.RpcError:
                pass
            except Exception as exc:
                print(f"[SERVER] Reader error for {peer}: {exc}")
            finally:
                self.__cleanup(peer)

        reader_thread = threading.Thread(target=__reader, daemon=True, name=f"reader-{peer}")
        reader_thread.start()
        reader_thread.join()

        return empty_pb2.Empty()


def serve():
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Connected to Arduino on {SERIAL_PORT}.")

    server = grpc.server(
        ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.keepalive_time_ms", 5_000),
            ("grpc.keepalive_timeout_ms", 3_000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.http2.min_ping_interval_without_data_ms", 2_000),
        ],
    )
    pb2_grpc.add_PCBServiceServicer_to_server(
        PCBServiceServicer(arduino), server
    )

    listen_addr = f"{GRPC_HOST}:{GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    server.start()
    print(f"[SERVER] gRPC server listening on {listen_addr}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        server.stop(grace=2)
        arduino.close()
        print("Arduino connection closed.")


if __name__ == "__main__":
    serve()