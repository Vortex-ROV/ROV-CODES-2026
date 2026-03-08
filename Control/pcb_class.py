from PySide6.QtCore import QThread
import json
import socket

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
        self.__jetson_ip = "192.168.33.1"
        self.__jetson_port = 12345
        self.connected = False

        self.__arduino_control = {"Mosfet1": 0, 
                                  "Mosfet2": 0, 
                                  "Mosfet3": 0, 
                                  "Mosfet4": 0, 
                                  "Mosfet5": 0, 
                                  "Mosfet6": 0, 
                                  "Mosfet7": 0, 
                                  "bilge": 0, 
                                  "angle": 1500, 
                                  "servo_direction": 0 }
        print(json.dumps(self.__arduino_control))
    
    def control_gripper_a(self):
        self.__gripper_a = not self.__gripper_a
        self.__arduino_control["Mosfet1"] = not self.__arduino_control["Mosfet1"]
        if self.__gripper_a: self.__arduino_control["Mosfet1"] = 1
        elif self.__gripper_a == 0: self.__arduino_control["Mosfet1"] = 0
        print("Gripper A:", self.__gripper_a)

    def control_gripper_b(self):
        self.__gripper_b = not self.__gripper_b
        self.__arduino_control["Mosfet2"] = not self.__arduino_control["Mosfet2"]
        if self.__gripper_b: self.__arduino_control["Mosfet2"] = 1
        elif self.__gripper_b == 0: self.__arduino_control["Mosfet2"] = 0
        print("Gripper B:", self.__gripper_b)

    def control_gripper_c(self):
        self.__gripper_c = not self.__gripper_c
        self.__arduino_control["Mosfet6"] = not self.__arduino_control["Mosfet6"]
        if self.__gripper_c: self.__arduino_control["Mosfet6"] = 1
        elif self.__gripper_c == 0: self.__arduino_control["Mosfet6"] = 0
        print("Gripper C:", self.__gripper_c)

    def control_gripper_d(self):
        self.__gripper_d = not self.__gripper_d
        self.__arduino_control["Mosfet7"] = not self.__arduino_control["Mosfet7"]
        if self.__gripper_d: self.__arduino_control["Mosfet7"] = 1
        elif self.__gripper_d == 0: self.__arduino_control["Mosfet7"] = 0
        
        print("Gripper D:", self.__gripper_d)

    def control_rotating_tool(self):
        self.__rotate_tool = not self.__rotate_tool
        if self.__arduino_control["bilge"] == 0: self.__arduino_control["bilge"] = 40  
        else: self.__arduino_control["bilge"] = 0
        print("Rotating Tool:", "rotating" if self.__rotate_tool else "not rotating")
    
    def control_raise_camera(self):
        self.__arduino_control["servo_direction"] = 1
        print("Raising camera")
        
    def control_lower_camera(self):
        self.__arduino_control["servo_direction"] = -1
        print("Lowering camera")
    
    def control_camera_stop(self):
        self.__arduino_control["servo_direction"] = 0

    def run(self):
        while True:
            try:
                self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__socket.connect((self.__jetson_ip, self.__jetson_port))
                self.connected = True
                print("Connected to Jetson")
                while self.connected:
                    control_string = json.dumps(self.__arduino_control)
                    print(control_string)
                    control_string += '\n'
                    self.__socket.sendall(control_string.encode())
                    self.msleep(50)
                break
            except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
                self.connected = False
                print("Error in connection, retrying....")
                try:
                    self.__socket.close()
                    self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.__socket.connect((self.__jetson_ip, self.__jetson_port))
                except Exception:
                    pass
                self.msleep(500)

    def stop(self):
        self.connected = False
        self.exit()