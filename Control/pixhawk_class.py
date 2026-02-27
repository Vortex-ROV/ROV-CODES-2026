from PySide6.QtCore import QThread
from pymavlink import mavutil
import time

class Pixhawk(QThread):
    def __init__(self):
        self.__running = False
        if __name__ != "__main__":
            # pass
            super().__init__()

        self.__throttle_value = 1500
        self.__yaw_value = 1500
        self.__forward_value = 1500
        self.__lateral_value = 1500
        self.__armed = False
        self.__last_time_seen = 0
        self.__connected = False
        self.sent_armed = False
        self.sent_mode = ""

    def set_throttle_value(self, value):
        self.__throttle_value += value
        if self.__throttle_value > 1900: self.__throttle_value = 1900
        elif self.__throttle_value < 1100: self.__throttle_value = 1100

    def set_yaw_value(self, value):
        self.__yaw_value += value
        if self.__yaw_value > 1900: self.__yaw_value = 1900
        elif self.__yaw_value < 1100: self.__yaw_value = 1100

    def set_forward_value(self, value):
        self.__forward_value += value
        if self.__forward_value > 1900: self.__forward_value = 1900
        elif self.__forward_value < 1100: self.__forward_value = 1100

    def set_lateral_value(self, value):
        self.__lateral_value += value
        if self.__lateral_value > 1900: self.__lateral_value = 1900
        elif self.__lateral_value < 1100: self.__lateral_value = 1100
    
    def movements_values_reset(self):
        self.__throttle_value = 1500
        self.__yaw_value = 1500
        self.__forward_value = 1500
        self.__lateral_value = 1500
    
    def control_arm_disarm(self):
        # print("Armed" if self.__armed else "Disarmed")
        self.__pixhawk.arducopter_disarm() if self.__armed else self.__pixhawk.arducopter_arm()
    
    def control_arm(self):
        self.__pixhawk.arducopter_arm() if self.__armed == 0 else print("pixhawk already armed")
    
    def control_disarm(self):
        self.__pixhawk.arducopter_disarm() if self.__armed else print("pixhawk already disarmed")

    def control_manual_mode(self):
        mode_id = self.__pixhawk.mode_mapping()['MANUAL']
        self.__pixhawk.mav.set_mode_send(
        self.__pixhawk.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)

    def control_stabilize_mode(self):
        mode_id = self.__pixhawk.mode_mapping()['STABILIZE']
        self.__pixhawk.mav.set_mode_send(
        self.__pixhawk.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)

    def control_depth_hold_mode(self):
        mode_id = self.__pixhawk.mode_mapping()['ALT_HOLD']
        self.__pixhawk.mav.set_mode_send(
        self.__pixhawk.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)


    def run(self):
        self.__running = True
        self.__pixhawk = mavutil.mavlink_connection("udp:127.0.0.1:14561", autoreconnect=True, source_system=1)
        print("Waiting to connect to the pixhawk...")
        self.__pixhawk.wait_heartbeat()
        print("Got a heartbeat")
        self.__last_time_seen = time.time()
        while self.__running:
            msg = self.__pixhawk.recv_match()
            if msg:
                if msg.get_type() == 'HEARTBEAT':
                    if self.__connected == False:
                        self.__connected = True
                        print("connected to pixhawk")
                    
                    self.__armed = self.__pixhawk.motors_armed() # 0 if disarmed, any other value if armed
                    # print(self.__armed)
                    if self.__armed != self.sent_armed:
                        self.sent_armed = self.__armed
                        if self.__armed != 0: print("armed")
                        else: print("disarmed")

                    self.mode = mavutil.mode_string_v10(msg)
                    if self.mode != self.sent_mode:
                        self.sent_mode = self.mode
                        if self.mode == "MANUAL": print("manual mode")
                        elif self.mode == "STABILIZE": print("stabilize")
                        elif self.mode == "ALT_HOLD": print("depth hold")
                    self.__last_time_seen = time.time()
            if time.time() - self.__last_time_seen > 1.5:
                if self.__connected:
                    self.__connected = False
                    self.sent_mode = ""
                    print("Disconnected, trying to reconnect to the pixhawk...")
    
    def move_rov(self):
        rc_channel_values = [1500, 1500,self.__throttle_value, self.__yaw_value, self.__forward_value, self.__lateral_value, 65535, 65535, 65535]
        # print(self.__throttle_value, self.__yaw_value, self.__forward_value, self.__lateral_value)
        if self.__connected:
            self.__pixhawk.mav.rc_channels_override_send(
                self.__pixhawk.target_system,
                self.__pixhawk.target_component,
                *rc_channel_values)
        self.movements_values_reset()
    def stop(self):
        if self.__connected:
            self.__connected = False
            self.control_disarm()
            self.__pixhawk.close()
        self.__running = False
        