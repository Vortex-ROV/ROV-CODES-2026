from enum import Enum
import platform

class JoystickButtons(Enum):
    if platform.system() == "Windows":
        A = 0
        B = 1
        X = 2
        Y = 3
        LT = 4
        RT = 5
        BACK = 6
        START = 7
        LSTCIK = 8
        RSTCIK = 9
        XBOX = 10
        
    else:
        A = 0
        B = 1
        X = 2
        Y = 3
        LT = 4
        RT = 5
        BACK = 6
        START = 7
        XBOX = 8
        LSTCIK = 9
        RSTCIK = 10

class JoystickHats(Enum):
    HATRIGHT = 13
    HATLEFT = 14
    HATUP = 11
    HATDOWN = 12

class JoystickAxes(Enum):
    LEFTVERTICAL = 0
    LEFTHORIZONTAL = 1
    RIGHTVERTICAL = 2
    RIGHTHORIZONTAL = 3
    TRIGGERS = 4

class ROVActions(Enum):
    Disarm = 0
    Arm = 1
    ManualMode = 2
    StabilizeMode = 3
    DepthHoldMode = 4
    GripperA = 5
    GripperB = 6
    ServoUp = 7
    ServoDown = 8

class GUIControllerButtonActions(Enum):
    NONE = 0
    GRIPPER_A = 1
    GRIPPER_B = 2
    GRIPPER_C = 3
    GRIPPER_D = 4
    ROTATE_TOOL = 5
    ARM_DISARM = 6
    ARM = 7
    DISARM = 8
    MANUAL_MODE = 9
    STABILIZE_MODE = 10
    DEPTH_HOLD_MODE = 11
    SERVO_UP = 12
    SERVO_DOWN = 13
    SERVO_STOP = 14
    GAIN_INCREASE = 15
    GAIN_DECREASE = 16
    SCROLL_CAMERA_FORWARD = 17
    SCROLL_CAMERA_BACKWARD = 18


class GUIControllerMovementActions(Enum):
    NONE = 0
    THROTTLE = 1
    YAW = 2
    FORWARD = 3
    LATERAL = 4