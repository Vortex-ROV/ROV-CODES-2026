import pygame
import platform
from PySide6.QtCore import QThread
from gui_mappings import *
from pcb_class import PCB
from pixhawk_class import Pixhawk

class Joystick(QThread):

    def __init__(self):
        if __name__ != "__main__": super().__init__() # qthread inheritance initialization
        self.__running = False
        self.platform = platform.system()
        
        # pygame initialization for controller
        pygame.init()
        pygame.joystick.init()

        # initial joystick data
        self.__controller_buttons_count = 0
        self.__controller_axes_count = 0
        self.__controller_buttons_data = []
        self.__controller_last_buttons_data = [] # this is to keep track of what button got pressed and what button got released
        self.__controller_raw_axes_data = []
        self.__controller_mapped_axes_data = []
        self.__controller_hat_data = [0, 0]
        self.__controller_last_hats_data = 0 # this is to keep track of what button in the hat got pressed and what button got released
        self.__controller_connected = False
        self.__controller_name = ""
        self.__controllers_count = 0
        self.__gain = 100

        # initialize pcb control class and pixhawk control class
        self.pcb = PCB()
        self.pixhawk = Pixhawk()
        self.pixhawk.start()

        # initila controller function mapping
        self.__rov_actions = {
            GUIControllerButtonActions.GRIPPER_A: self.pcb.control_gripper_a,
            GUIControllerButtonActions.GRIPPER_B: self.pcb.control_gripper_b,
            GUIControllerButtonActions.GRIPPER_C: self.pcb.control_gripper_c,
            GUIControllerButtonActions.FINGERS: self.pcb.control_fingers,
            GUIControllerButtonActions.ROTATE_TOOL: self.pcb.control_rotating_tool,
            GUIControllerButtonActions.SERVO_UP: self.pcb.control_raise_camera,
            GUIControllerButtonActions.SERVO_DOWN: self.pcb.control_lower_camera,
            GUIControllerButtonActions.GAIN_INCREASE: self.increase_gain,
            GUIControllerButtonActions.GAIN_DECREASE: self.decrease_gain,
            GUIControllerButtonActions.ARM_DISARM: self.pixhawk.control_arm_disarm,
            GUIControllerButtonActions.MANUAL_MODE: self.pixhawk.control_manual_mode,
            GUIControllerButtonActions.STABILIZE_MODE: self.pixhawk.control_stabilize_mode,
            GUIControllerButtonActions.DEPTH_HOLD_MODE: self.pixhawk.control_depth_hold_mode,
            GUIControllerButtonActions.NONE: "none"
        }

        self.__rov_movements = {
            GUIControllerMovementActions.THROTTLE: self.pixhawk.set_throttle_value,
            GUIControllerMovementActions.YAW: self.pixhawk.set_yaw_value,
            GUIControllerMovementActions.FORWARD: self.pixhawk.set_forward_value,
            GUIControllerMovementActions.LATERAL: self.pixhawk.set_lateral_value,
            GUIControllerMovementActions.NONE: ""
        }

        self.__button_action_mapping = {
            JoystickButtons.A.value: self.__rov_actions[GUIControllerButtonActions.GRIPPER_A],
            JoystickButtons.B.value: self.__rov_actions[GUIControllerButtonActions.GRIPPER_B],
            JoystickButtons.X.value: self.__rov_actions[GUIControllerButtonActions.GRIPPER_C],
            JoystickButtons.Y.value: self.__rov_actions[GUIControllerButtonActions.FINGERS],
            JoystickButtons.LT.value: self.__rov_actions[GUIControllerButtonActions.NONE],
            JoystickButtons.RT.value: self.__rov_actions[GUIControllerButtonActions.ARM_DISARM],
            JoystickButtons.BACK.value: self.__rov_actions[GUIControllerButtonActions.STABILIZE_MODE],
            JoystickButtons.START.value: self.__rov_actions[GUIControllerButtonActions.NONE],
            JoystickButtons.XBOX.value: self.__rov_actions[GUIControllerButtonActions.MANUAL_MODE],
            JoystickButtons.LSTCIK.value: self.__rov_actions[GUIControllerButtonActions.NONE], 
            JoystickButtons.RSTCIK.value: self.__rov_actions[GUIControllerButtonActions.NONE],
            JoystickHats.HATUP: self.__rov_actions[GUIControllerButtonActions.SERVO_UP],
            JoystickHats.HATDOWN: self.__rov_actions[GUIControllerButtonActions.SERVO_DOWN],
            JoystickHats.HATRIGHT: self.__rov_actions[GUIControllerButtonActions.GAIN_INCREASE],
            JoystickHats.HATLEFT: self.__rov_actions[GUIControllerButtonActions.GAIN_DECREASE]
        }

        self.__button_name_mapping = {
            "A": JoystickButtons.A.value, 
            "B": JoystickButtons.B.value,
            "X": JoystickButtons.X.value,
            "Y": JoystickButtons.Y.value,
            "LT": JoystickButtons.LT.value,
            "RT": JoystickButtons.RT.value,
            "BACK": JoystickButtons.BACK.value,
            "START": JoystickButtons.START.value,
            "XBOX": JoystickButtons.XBOX.value,
            "LSTICK": JoystickButtons.LSTCIK.value,
            "RSTICK": JoystickButtons.RSTCIK.value
        }

        self.__axis_action_mapping = {
            JoystickAxes.LEFTVERTICAL.value: self.__rov_movements[GUIControllerMovementActions.FORWARD],
            JoystickAxes.LEFTHORIZONTAL.value: self.__rov_movements[GUIControllerMovementActions.LATERAL],
            JoystickAxes.RIGHTVERTICAL.value: self.__rov_movements[GUIControllerMovementActions.THROTTLE],
            JoystickAxes.RIGHTHORIZONTAL.value: self.__rov_movements[GUIControllerMovementActions.NONE],
            JoystickAxes.TRIGGERS.value: self.__rov_movements[GUIControllerMovementActions.YAW]
        }

        print("initialized class")

        """ 
        This is an explaination of how the axes work in this code in the xbox controller, 
        there are 6 axes, 2 in each stick and 1 on the left (below left trigger) and 1 on the right (below riht trigger),
        the axes on the sticks begin in the middle (which is zero) and go from -1 to 1, while the two below the riggers start from -1 not like the other, and the go to 1,
        the 4 axes on the sticks will all map from 1100 to 1900 with them beginning on and being neutral at 1500,
        the two under the triggers work a bit differently, there is a standard value of 1500, and the
        left axis makes a change from -400 to 0, and this change is added to the 1500,
        and the right axis makes a change from 0 to 400, and this change is also added to the 1500.
        """
    
    def get_gain(self): return self.__gain
    def increase_gain(self): # increases gain by 20 %
        if self.__gain < 100:
            self.__gain += 20
            if self.__gain > 100: self.__gain = 100
        else: print("gain is maximum")

    def decrease_gain(self): # decreases gain by 20 %
        if self.__gain > 20:
            self.__gain -= 20
            if self.__gain < 20: self.__gain = 20
        else: print("gain is minimum")

    def set_gain(self, value):
        if value > 100: self.__gain = 100
        elif value < 20: self.__gain = 20
        else: self.__gain = value

    def get_name(self): return self.__controller_name

    def get_mapped_outputs(self): return self.__controller_mapped_axes_data

    def __map_value(self, value, from_low, from_high, to_low, to_high): # similar to arduino's map() function
        return round(((value - from_low) * (to_high - to_low) / (from_high - from_low) + to_low), 2)
    
    def get_button_mapping(self, button: str): # know what button does what, example: self.get_button_mapping("A")
        if button not in self.__button_name_mapping: print("Button not available")
        else: return self.__button_action_mapping[self.__button_name_mapping[button]].__name__

    def set_button_mapping(self, button, mapping):# chane what button does what, example: self.set_button_mapping("A", self.pcb.control_gripper_c)
        if button not in self.__button_name_mapping: print("Button not available")
        else: self.__button_action_mapping[self.__button_name_mapping[button]] = mapping


    def run(self):
        self.__running = True
        while self.__running:
            pygame.event.pump() # send all 
            self.__controllers_count = pygame.joystick.get_count() # get number of connected controllers
            if self.__controllers_count:
                self.__controller_connected = True
                self.__controller = pygame.joystick.Joystick(0)
                self.__controller.init()
                self.__controller_name = self.__controller.get_name()
                if "Xbox 360 Controller" not in self.__controller_name:
                    print("please plug in only a single xbox 360 controller.")
                    self.__controller.quit()
                    pygame.time.Clock.tick(10)
                    continue
                self.__controller_buttons_count = self.__controller.get_numbuttons()
                self.__controller_axes_count = self.__controller.get_numaxes()
                self.__controller_last_buttons_data.clear()
                self.__controller_last_buttons_data = [0] * self.__controller_buttons_count
                self.__controller_last_hats_data = [0, 0]
                self.__controller_mapped_axes_data = [0, 0, 0, 0, 0]
                print(self.__controller_name)
                

            while self.__controller_connected:
                pygame.event.pump()
                self.__controllers_count = pygame.joystick.get_count()
                if self.__controllers_count == 0: # joystick disconnected
                    self.__controller_connected = False
                    print("joystick disconnected")
                    break
                
                """ Reading data """

                # read buttons data
                for i in range(self.__controller_buttons_count):
                    self.__controller_buttons_data.append(self.__controller.get_button(i))
                
                # read axes data
                for i in range(self.__controller_axes_count):
                    self.__controller_raw_axes_data.append(self.__controller.get_axis(i))
                
                # read hat data
                self.__controller_hat_data = self.__controller.get_hat(0)


                """ Processing data """
                
                # compare buttons with previous state to know which button got pressed and which got released
                for i in range(self.__controller_buttons_count):
                    if self.__controller_buttons_data[i] == 1 and self.__controller_last_buttons_data[i] == 0:
                        if self.__button_action_mapping[i] != "none":
                            self.__press_event(self.__button_action_mapping[i])
                        else: print("mapping is none")
                    elif self.__controller_buttons_data[i] == 0 and self.__controller_last_buttons_data[i] == 1:
                        pass
                    else: pass

                
                # compare hat buttons with previous state to know which hat button got pressed and which got released

                # hat up
                if self.__controller_hat_data[1] == 1 and self.__controller_last_hats_data[1] == 0: # press
                    if self.__button_action_mapping[JoystickHats.HATUP] != "":
                        self.__press_event(self.__button_action_mapping[JoystickHats.HATUP])                        
                elif self.__controller_hat_data[1] == 0 and self.__controller_last_hats_data[1] == 1: # release
                    pass
                else: pass

                # hat down
                if self.__controller_hat_data[1] == -1 and self.__controller_last_hats_data[1] == 0: # press
                    if self.__button_action_mapping[JoystickHats.HATDOWN] != "":
                        self.__press_event(self.__button_action_mapping[JoystickHats.HATDOWN])
                elif self.__controller_hat_data[1] == 0 and self.__controller_last_hats_data[1] == -1: # release
                    pass
                else: pass

                # hat right                
                if self.__controller_hat_data[0] == 1 and self.__controller_last_hats_data[0] == 0: # press
                    if self.__button_action_mapping[JoystickHats.HATRIGHT] != "":
                        self.__press_event(self.__button_action_mapping[JoystickHats.HATRIGHT])
                elif self.__controller_hat_data[0] == 0 and self.__controller_last_hats_data[0] == 1: # release
                    pass
                else: pass

                # hat left
                if self.__controller_hat_data[0] == -1 and self.__controller_last_hats_data[0] == 0: # press
                    if self.__button_action_mapping[JoystickHats.HATLEFT] != "":
                        self.__press_event(self.__button_action_mapping[JoystickHats.HATLEFT])
                elif self.__controller_hat_data[0] == 0 and self.__controller_last_hats_data[0] == -1: # release
                    pass
                else: pass


                # remap joystick values (OS dependent)

                if self.platform == "Linux":
                    self.__controller_raw_axes_data[2] = self.__map_value(self.__controller_raw_axes_data[2], -1, 1, 0, 1)
                    self.__controller_raw_axes_data[5] = self.__map_value(self.__controller_raw_axes_data[5], -1, 1, 0, 1)
                    self.__controller_mapped_axes_data[0] += int(-400*self.__controller_raw_axes_data[1]*(self.__gain/100))
                    self.__controller_mapped_axes_data[1] += int(400*self.__controller_raw_axes_data[0]*(self.__gain/100))
                    self.__controller_mapped_axes_data[2] += int(-400*self.__controller_raw_axes_data[4]*(self.__gain/100))
                    self.__controller_mapped_axes_data[3] += int(400*self.__controller_raw_axes_data[3]*(self.__gain/100))
                    self.__controller_mapped_axes_data[4] += int(400*self.__controller_raw_axes_data[5]*(self.__gain/100) + -400*self.__controller_raw_axes_data[2]*(self.__gain/100))
                
                elif self.platform == "Windows":
                    self.__controller_raw_axes_data[4] = self.__map_value(self.__controller_raw_axes_data[4], -1, 1, 0, 1)
                    self.__controller_raw_axes_data[5] = self.__map_value(self.__controller_raw_axes_data[5], -1, 1, 0, 1)
                    self.__controller_mapped_axes_data[0] += int(-400*self.__controller_raw_axes_data[1]*(self.__gain/100))
                    self.__controller_mapped_axes_data[1] += int(400*self.__controller_raw_axes_data[0]*(self.__gain/100))
                    self.__controller_mapped_axes_data[2] += int(-400*self.__controller_raw_axes_data[3]*(self.__gain/100))
                    self.__controller_mapped_axes_data[3] += int(400*self.__controller_raw_axes_data[2]*(self.__gain/100))
                    self.__controller_mapped_axes_data[4] += int(-400*self.__controller_raw_axes_data[4]*(self.__gain/100) + 400*self.__controller_raw_axes_data[5]*(self.__gain/100))
                
                # set the movements values in the pixhawk and move the ROV according to these values, then reset the value for a fresh read
                for i in range(5):
                    if self.__axis_action_mapping[i] == "": pass
                    else: self.__axis_event(self.__axis_action_mapping[i], self.__controller_mapped_axes_data[i])
                
                self.pixhawk.move_rov()

             
                # prepare variables for a fresh read
                self.__controller_last_buttons_data = self.__controller_buttons_data.copy()
                self.__controller_last_hats_data[0] = self.__controller_hat_data[0]
                self.__controller_last_hats_data[1] = self.__controller_hat_data[1]
                self.__controller_buttons_data.clear()
                self.__controller_raw_axes_data.clear()
                self.__controller_mapped_axes_data = [0, 0, 0, 0, 0]

            
                pygame.time.Clock().tick(200)
        
    def __press_event(self, method): method()
    def __release_event(self, method): method()

    def __axis_event(self, method, args): method(args)

    def stop(self):
        if self.__controller_connected:
            self.__controller.quit()
            self.__controller_connected = False
        pygame.joystick.quit()
        pygame.quit()
        self.pixhawk.stop()
        self.__running = False
    
if __name__ == "__main__":
    try:
        controller = Joystick()
        controller.run()

    except KeyboardInterrupt:
        print("quitting...")
        controller.stop()
