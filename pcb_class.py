from PySide6.QtCore import QThread

class PCB():
    def __init__(self):
        if __name__ != "__main__":
            super().__init__()
        
        self.__gripper_a = False
        self.__gripper_b = False
        self.__gripper_c = False
        self.__fingers = False
        self.__rotate_tool = False

        self.armed = False
    
    def control_gripper_a(self):
        self.__gripper_a = not self.__gripper_a
        print("Gripper A:", self.__gripper_a)

    def control_gripper_b(self):
        self.__gripper_b = not self.__gripper_b
        print("Gripper B:", self.__gripper_b)

    def control_gripper_c(self):
        self.__gripper_c = not self.__gripper_c
        print("Gripper C:", self.__gripper_c)

    def control_fingers(self):
        self.__fingers= not self.__fingers
        print("Fingers:", self.__fingers)

    def control_rotating_tool(self):
        self.__rotate_tool = not self.__rotate_tool
        print("Rotating Tool:", "rotating" if self.__rotate_tool else "not rotating")
    
    def control_raise_camera(self):
        print("Raising camera")
        
    def control_lower_camera(self):
        print("Lowering camera")
        