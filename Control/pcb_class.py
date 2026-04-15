from PySide6.QtCore import QThread
import grpc
import queue
import pcb_service_pb2 as pb2
import pcb_service_pb2_grpc as pb2_grpc


class PCB(QThread):
    def __init__(self):
        if __name__ != "__main__":
            super().__init__()

        self.__gripper_a = False
        self.__gripper_b = False
        self.__gripper_c = False
        self.__gripper_d = False
        self.__rotate_tool = False
        self.armed = False

        self.__jetson_address = "192.168.33.1:12345"
        self.connected = False
        self.__running = False

        self.__queue: queue.Queue[pb2.ClientMessage] = queue.Queue()

        self.__mosfets = {
            "mosfet_1": False, "mosfet_2": False, "mosfet_3": False,
            "mosfet_4": False, "mosfet_5": False, "mosfet_6": False,
            "mosfet_7": False,
        }
        self.__bilge_speed = 0
        self.__servo_angle = 1500
        self.__servo_direction = 0

    def control_gripper_a(self):
        self.__gripper_a = not self.__gripper_a
        self.__mosfets["mosfet_3"] = self.__gripper_a
        print("Gripper A:", self.__gripper_a)

    def control_gripper_b(self):
        self.__gripper_b = not self.__gripper_b
        self.__mosfets["mosfet_2"] = self.__gripper_b
        print("Gripper B:", self.__gripper_b)

    def control_gripper_c(self):
        self.__gripper_c = not self.__gripper_c
        self.__mosfets["mosfet_6"] = self.__gripper_c
        print("Gripper C:", self.__gripper_c)

    def control_gripper_d(self):
        self.__gripper_d = not self.__gripper_d
        self.__mosfets["mosfet_7"] = self.__gripper_d
        print("Gripper D:", self.__gripper_d)

    def control_rotating_tool(self):
        self.__rotate_tool = not self.__rotate_tool
        self.__bilge_speed = 100 if self.__rotate_tool else 0
        print("Rotating Tool:", "rotating" if self.__rotate_tool else "not rotating")

    def control_raise_camera(self):
        self.__servo_direction = 1
        print("Raising camera")

    def control_lower_camera(self):
        self.__servo_direction = -1
        print("Lowering camera")

    def control_camera_stop(self):
        self.__servo_direction = 0

    def send_control(self):
        if not self.connected:
            return

        self.msleep(100)

        self.__queue.put(pb2.ClientMessage(heartbeat=pb2.Heartbeat()))
        self.__queue.put(pb2.ClientMessage(
            mosfet_control=pb2.MosfetControl(**self.__mosfets)
        ))
        self.__queue.put(pb2.ClientMessage(
            servo_control=pb2.ServoControl(
                angle=self.__servo_angle,
                raise_lower=self.__servo_direction,
            )
        ))
        self.__queue.put(pb2.ClientMessage(
            bilge_control=pb2.BilgeControl(speed=self.__bilge_speed)
        ))


    def __message_stream(self):
        while self.__running:
            try:
                yield self.__queue.get(timeout=1.0)
            except queue.Empty:
                yield pb2.ClientMessage(heartbeat=pb2.Heartbeat())

    def run(self):
        self.__running = True

        while self.__running:
            try:
                with grpc.insecure_channel(self.__jetson_address) as channel:
                    stub = pb2_grpc.PCBServiceStub(channel)
                    self.connected = True
                    print("Connected to Jetson via gRPC")
                    stub.Session(self.__message_stream())

            except grpc.RpcError as e:
                self.connected = False
                print(f"gRPC error [{e.code()}]: {e.details()}")
                self.msleep(500)
            except Exception as e:
                self.connected = False
                print(f"Unexpected error: {e}")
                self.msleep(500)

    def stop(self):
        self.__running = False
        self.connected = False
        self.exit()