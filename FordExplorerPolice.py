import time
import can
import random
import socket
import struct
import select 
import threading
import tkinter as tk
from datetime import datetime

bus = can.interface.Bus(channel='/dev/tty.usbmodem343E385A33351', bustype='slcan', bitrate=500000)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 44444))
    
start_time_50ms = time.time()
start_time_10ms = time.time()
start_time_5s = time.time()

leftpad_left = False
leftpad_right = False
leftpad_down = False
leftpad_up = False
leftpad_ok = False

id_counter = 0

test_mode = False

rpm = 3500
speed = 70
coolant_temp = 90
oil_temp = 90
fuel = 50
gear = 1
left_directional = False
right_directional = False
tc_active = False
tc_off = False
abs_active = False
battery = False
handbrake = False
highbeam = False

front_left_door = False
front_right_door = False
rear_right_door = False
rear_left_door = False
hood = False
trunk = False

tpms = False
cruise_control = False
cruise_control_speed = 80
foglight = False
parking_lights = False 
check_engine = False
front_left_tire = 30
front_right_tire = 30
rear_left_tire = 30
rear_right_tire = 30
airbag = False
seatbelt = False

oil_life = 200 # oil_life/2 = percentage it will show
gear_position = 0x60 #0x20 = R, 0x40 = N, 0x60 = D, 0xa0 = L
low_oil_pressure = False
handbrake_warning = False

def decode_outgauge(packet):
    global rpm
    global speed
    global oil_temp
    global fuel
    global left_directional
    global right_directional
    global highbeam
    global abs_active
    global tc_active
    global handbrake
    global throttle
    global coolant_temp
    
    rpm = int(max(min(packet[6], 8000), 0))
    speed = max(min((packet[5]*2.25), 160), 0)
    oil_temp = int(packet[11])
    coolant_temp = int(packet[8])
    fuel = int(packet[9])
    throttle = int(packet[14]*100)
    left_directional = False
    right_directional = False
    highbeam = False
    abs_active = False
    tc_active = False
    handbrake = False
    
    if (packet[13]>>1)&1:
        highbeam = True
    if (packet[13]>>2)&1:
        handbrake = True
    if (packet[13]>>4)&1:
        tc_active = True
    if (packet[13]>>10)&1:
        abs_active = True
    if (packet[13]>>5)&1:
        left_directional = True
    if (packet[13]>>6)&1:
        right_directional = True

def decode_outgauge_enhanced():
    #TBD: for a alternative outgauge lua file that exposes more info
    print("Non-stock outgauge detected")


def recv_outgauge():
    global test_mode
    #read from the socket if there is data to be read
    ready_to_read, _, _ = select.select([sock], [], [], 0)
    if sock in ready_to_read:
        data, _ = sock.recvfrom(256)
        try:
            packet = struct.unpack('I4sH2c7f2I3f16s16si', data)
        except:
            packet = struct.unpack('I4sH2c7f2I3f16s16si', data)
            decode_outgauge_enhanced(packet)
        else:
            decode_outgauge(packet)
        finally:
            test_mode = False

# Function to toggle variable values
def toggle_var(var, value):
    globals()[var] = value

# GUI setup
def gui_thread():
    root = tk.Tk()
    root.title("Ford Edge 2011")

    
    leftpad_up_button = tk.Button(root, text=f"L UP")
    leftpad_up_button.grid(row=0, column=1)
    leftpad_up_button.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up", True))
    leftpad_up_button.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up", False))

    leftpad_down_button = tk.Button(root, text=f"L DOWN")
    leftpad_down_button.grid(row=2, column=1)
    leftpad_down_button.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_down", True))
    leftpad_down_button.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_down", False))
    
    leftpad_left_button = tk.Button(root, text=f"L LEFT")
    leftpad_left_button.grid(row=1, column=0)
    leftpad_left_button.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_left", True))
    leftpad_left_button.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_left", False))
    
    leftpad_right_button = tk.Button(root, text=f"L RIGHT")
    leftpad_right_button.grid(row=1, column=2)
    leftpad_right_button.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_right", True))
    leftpad_right_button.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_right", False))
    
    leftpad_ok_button = tk.Button(root, text=f"L OK")
    leftpad_ok_button.grid(row=1, column=1)
    leftpad_ok_button.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_ok", True))
    leftpad_ok_button.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_ok", False))

    return root

root = gui_thread()


while True:
    root.update()
    current_time = time.time()
    
    recv_outgauge()
            
    # Send each message every 50ms
    elapsed_time_50ms = current_time - start_time_50ms
    if elapsed_time_50ms >= 0.05:
        speedval = int(speed*160)
        messages_50ms = [
            

            can.Message(arbitration_id=0x3b3, data=[0x40, 0x48, 0x02, 0x0f, 0x10, 0x05, 0x00, 0x22], is_extended_id=False), #ignition status
            can.Message(arbitration_id=0x4c, data=[airbag*0x40,0,0,0,0,0,0,0], is_extended_id=False), #airbag/seatbelt light
            can.Message(arbitration_id=0x77, data=[random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),0,0,0,0], is_extended_id=False), #steering warnings
            can.Message(arbitration_id=0x156, data=[int(coolant_temp*1.6),50,0,0,91,0,0,0], is_extended_id=False), #coolant temp
            can.Message(arbitration_id=0x171, data=[4,gear_position,0,0,0,0,0,0], is_extended_id=False), #gear
            can.Message(arbitration_id=0x179, data=[0,0,0,0,oil_life,0,0,0], is_extended_id=False), #milage/fuel fill inlet warning/oil change warning
            can.Message(arbitration_id=0x261, data=[0,0,0,0,0,0,0,0], is_extended_id=False), #awd messages
            can.Message(arbitration_id=0x3b2, data=[0,0,0,0,right_directional*8,0,(left_directional*64)+rear_left_door+(rear_right_door*2),(trunk*4)+(hood*8)+(front_right_door*16)+(front_left_door*32)], is_extended_id=False), #doors/lights
            can.Message(arbitration_id=0x3b4, data=[tpms*4,0,0,0,0,0,0,0], is_extended_id=False), #tpms light and warnings

            can.Message(arbitration_id=0x3b5, data=[0,int(front_left_tire*6.8),0,int(front_right_tire*6.8),0,int(rear_right_tire*6.8),0,int(rear_left_tire*6.8)], is_extended_id=False), #tire pressures
            can.Message(arbitration_id=0x3c3, data=[highbeam*2,0,handbrake*0x10,handbrake_warning*4,0,0,0,0], is_extended_id=False), #highbeam, alarm
            can.Message(arbitration_id=0x416, data=[0,0,0,0,0,(tc_active*2)+(tc_off*8),abs_active*0x40,0], is_extended_id=False), #brake/tc
            can.Message(arbitration_id=0x421, data=[check_engine*4,0,low_oil_pressure*4,0,0,0,0,0], is_extended_id=False), #mil/oil press
            can.Message(arbitration_id=0x42c, data=[0,battery*2,0x80,0,0,0,0,0], is_extended_id=False), #battery, cruise control

            can.Message(arbitration_id=0x466, data=[0xff,0xff,0x00,0x22,0x50,0xff,0,0], is_extended_id=False), #compass

            can.Message(arbitration_id=0x202, data=[0,0,0,0,random.randint(0,255),0, speedval >>8,speedval & 0xff], is_extended_id=False),
            
            
        
            can.Message(arbitration_id=id_counter, data=[
                random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)], is_extended_id=False),
        ]
        
        #Update checksums and counters here

        # Send Messages
        for message in messages_50ms:
            bus.send(message)
            #if message.arbitration_id == 0x202:
            #    print(message.data)

            time.sleep(0.001)
        start_time_50ms = time.time()


    # Execute code every 10ms
    elapsed_time_10ms = current_time - start_time_10ms
    if elapsed_time_10ms >= 0.01:  # 10ms

        messages_10ms = [
            can.Message(arbitration_id=0x81, data=[(leftpad_down * 1) +(leftpad_ok * 16) +(leftpad_left * 2) + (leftpad_right * 4) + (leftpad_up * 8), 0, 0, 0, 0, 0, 0, 0], is_extended_id=False),

            can.Message(arbitration_id=0x204, data=[0,0, 0,  int(rpm/2) >> 8, int(rpm/2) & 0xff,0,0,0], is_extended_id=False),
        ]
        
        for message in messages_10ms:

            bus.send(message)
            time.sleep(0.001)
        start_time_10ms = time.time()

    # Execute code every 5s
    elapsed_time_5s = current_time - start_time_5s
    if elapsed_time_5s >= 0.5:
        id_counter += 1
        print(hex(id_counter))
        if test_mode:
            if rpm == 3500:
                rpm = 4500
            else:
                rpm = 3500
            if speed == 70:
                speed = 90
            else:
                speed = 70

            foglight = not foglight
            parking_lights = not parking_lights
            check_engine = not check_engine
            airbag = not airbag
            seatbelt = not seatbelt
            tc_off = not tc_off
            left_directional = not left_directional
            right_directional = not right_directional
            tc_active = not tc_active
            abs_active = not abs_active
            handbrake = not handbrake
            highbeam = not highbeam

        start_time_5s = time.time()

sock.close()

