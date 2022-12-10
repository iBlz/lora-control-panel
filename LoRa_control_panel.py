from tkinter import *
from datetime import datetime
import contextlib, io
import getpass
import time
import json
import sys
import os
import serial
import plotext as plt
import re
import threading
import pyglet
import win32gui, win32con

window = win32gui.GetForegroundWindow() # hide window
win32gui.ShowWindow(window, win32con.SW_HIDE)

window = Tk()
user = getpass.getuser()

ansi_escape = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)

def load_serial():
    global ser, serial_raw
    try:
        ser = serial.Serial(
            port='COM9',
            baudrate=9600,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        serial_raw = ser.readline().decode().replace("\n", "")
    except:
        pass

load_serial()

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

pyglet.font.add_file(resource_path('font.ttf'))

def update_serial_box():
    global serial_raw
    try:
        open(resource_path("log_lora.txt"), "w").write("Serial started at %s \n" % datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    except:
        pass
    while True:
        try:
            serial_box.configure(state='normal',exportselection=0)
            serial_box.insert("end","\n{} {}".format(datetime.now().strftime("%H:%M:%S"),serial_raw))
            serial_box.configure(state='disabled',exportselection=0)
            serial_box.see("end")
            serial_raw = ser.readline().decode().replace("\n", "")
            save = open(resource_path("log_lora.txt"), "a")
            save.write("\n" + serial_box.get(1.0, END).splitlines()[-1])
            save.close()
        except:
            serial_raw = "Please connect your serial connection!"
            load_serial()
            time.sleep(1)
            pass

def update_plot_box():
    global serial_raw
    while True:
        time.sleep(0.01)
        pattern = re.compile(r"\[\*].*Json ping : \{.*\}", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0):
                serial_json_raw = pattern.findall(serial_raw)
                serial_json_raw = json.loads(serial_json_raw[0].replace("[*] Json ping : ", ""))
                names = ["Rssi", "Snr", "Frequency Error"]
                info_gateway = [float(serial_json_raw["gateway_info"]["rssi"].replace("-","")),float(serial_json_raw["gateway_info"]["packetSnr"].replace("-","")),float(serial_json_raw["gateway_info"]["packetFrequencyError"].replace("-",""))]
                info_node = [float(serial_json_raw["node_info"]["rssi"].replace("-","")),float(serial_json_raw["node_info"]["packetSnr"].replace("-","")),float(serial_json_raw["node_info"]["packetFrequencyError"].replace("-",""))]
                plt.simple_multiple_bar(names,[info_gateway,info_node], labels=['Gateway info', 'Node info'], width = 118, title = 'LoRa Info Plot')
                plt.axes_color('black')
                plt.canvas_color('black')
                plot_box.configure(state='normal',exportselection=0)
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    plt.show()
                plot = f.getvalue()
                plot_box.delete("1.0", END)
                plot_box.insert("end","" + ansi_escape.sub('', plot))
                plot_box.configure(state='disabled',exportselection=0)
                plot_box.see("end")
        except:
            pass

def time_running():
    global serial_raw
    while True:
        time.sleep(0.01)
        pattern = re.compile(r"\[\*] Time running \( Minutes \) : \d+(?:-\d+)*", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0):
                minutes = pattern.findall(serial_raw)
                try:
                    time_running_text.destroy()
                except:
                    pass
                time_running_text = Label(window,text="Time Running :%s minutes" % minutes[0].replace("[*] Time running ( Minutes ) :",""),font=('Prototype',25))
                time_running_text.pack(ipadx=5, ipady=5, expand=True)
                time_running_text.config(background='#28242c', bd=0, fg='#aaaaaa')
                time_running_text.place(x=45, y=115)
            else:
                pass
        except:
            pass

def time_since_last_packet():
    global serial_raw
    time1 = time.time()
    while True:
        time.sleep(0.01)
        pattern = re.compile(r"\[\*].*Json ping : \{.*\}", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0):
                time2 = time.time()
                difference = time2 - time1
                try:
                    try:
                        time_since_last_packet_text.destroy()
                    except:
                        pass
                    time_since_last_packet_text = Label(window,text="Time since last packet : %s sec" % round(difference-count,3),font=('Prototype',20))
                    time_since_last_packet_text.pack(ipadx=5, ipady=5, expand=True)
                    time_since_last_packet_text.config(background='#28242c', bd=0, fg='#aaaaaa')
                    time_since_last_packet_text.place(x=45, y=225)
                except:
                    pass
            else:
                try:
                    count = round(difference,3)
                except:
                    pass
                pass
        except:
            pass

def packets():
    global serial_raw, count_packets
    count_packets = 0
    while True:
        time.sleep(0.01)
        pattern = re.compile(r"\[\*].*Json ping : \{.*\}", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0):
                count_packets = count_packets + 1
                time.sleep(2)
                try:
                    packets_text.destroy()
                except:
                    pass
                packets_text = Label(window,text="Packets : %s" % count_packets,font=('Prototype',25))
                packets_text.pack(ipadx=5, ipady=5, expand=True)
                packets_text.config(background='#28242c', bd=0, fg='#aaaaaa')
                packets_text.place(x=45, y=329)
        except:
            pass

def corrupted_packets():
    global serial_raw, count_corrputed_packets
    count_corrputed_packets = 0
    set_byte = 0
    while True:
        time.sleep(0.01)
        pattern = re.compile(r"\[\*].*Json ping : \{.*\}", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0 and set_byte == 0):
                corrupted_packets_text = Label(window,text="Corrupted Packets : 0",font=('Prototype',25))
                corrupted_packets_text.pack(ipadx=5, ipady=5, expand=True)
                corrupted_packets_text.config(background='#28242c', bd=0, fg='#aaaaaa')
                corrupted_packets_text.place(x=45, y=435)
                set_byte = 1
        except:
            pass
        pattern = re.compile(r"\[\*] Json status : InvalidInput", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0):
                count_corrputed_packets = count_corrputed_packets + 1
                time.sleep(2)
                try:
                    corrupted_packets_text.destroy()
                except:
                    pass
                corrupted_packets_text = Label(window,text="Corrupted Packets : %s" % count_corrputed_packets,font=('Prototype',25))
                corrupted_packets_text.pack(ipadx=5, ipady=5, expand=True)
                corrupted_packets_text.config(background='#28242c', bd=0, fg='#aaaaaa')
                corrupted_packets_text.place(x=45, y=435)
        except:
            pass

def command_status():
    global serial_raw
    command_status_text = Label(window,text="Command status",font=('Prototype',25))
    command_status_text.pack(ipadx=5, ipady=5, expand=True)
    command_status_text.config(background='#28242c', bd=0, fg='#aaaaaa')
    command_status_text.place(x=585, y=435)
    while True:
        time.sleep(0.01)
        pattern = re.compile(r"\[\*].*Json command : \{.*\}", re.IGNORECASE)
        try:
            if(len(pattern.findall(serial_raw)) > 0):
                command_json_pattern = pattern.findall(serial_raw)
                command_json = json.loads(command_json_pattern[0].replace("[*] Json command : ", ""))
                try:
                    command_status_text.destroy()
                except:
                    pass
                command_status_text = Label(window,text="Status : %s" % command_json["command_status"],font=('Prototype',25))
                command_status_text.pack(ipadx=5, ipady=5, expand=True)
                command_status_text.config(background='#28242c', bd=0, fg='#aaaaaa')
                command_status_text.place(x=500, y=435)
        except:
            pass

def fire():
    global ser
    try:
        ser.write("fire".encode())
    except:
        print("Fire error")

def relay_off():
    global ser
    try:
        ser.write("relay_off".encode())
    except:
        print("Relay off error")

def relay_on():
    global ser
    try:
        ser.write("relay_on".encode())
    except:
        print("Relay on error")

def background_threads():
    time_running_thread = threading.Thread(target=time_running)
    time_running_thread.daemon = True 
    time_running_thread.start()
    print("Started time running thread")
    find_json_thread = threading.Thread(target=update_plot_box)
    find_json_thread.daemon = True 
    find_json_thread.start()
    print("Started plot box thread")
    serial_box_thread = threading.Thread(target=update_serial_box)
    serial_box_thread.daemon = True 
    serial_box_thread.start()
    print("Started serial box thread")
    time_since_last_packet_thread = threading.Thread(target=time_since_last_packet)
    time_since_last_packet_thread.daemon = True 
    time_since_last_packet_thread.start()
    print("Started time since last packet thread")
    packets_min_thread = threading.Thread(target=packets)
    packets_min_thread.daemon = True 
    packets_min_thread.start()
    print("Started packets packet thread")
    corrupted_packets_min_thread = threading.Thread(target=corrupted_packets)
    corrupted_packets_min_thread.daemon = True 
    corrupted_packets_min_thread.start()
    print("Started corrupted packets packet thread")
    command_status_thread = threading.Thread(target=command_status)
    command_status_thread.daemon = True 
    command_status_thread.start()
    print("Started command_status thread")

print(resource_path("images\\icon.png"))
window.geometry('1500x700')
window.resizable('0', '0')
window.title("LoRa Control Panel")
icon = PhotoImage(file=resource_path("images\\icon.png"))
window.iconphoto(False, icon)
window.configure(background='#22272e')

logo_img = PhotoImage(file=resource_path("images\\logo.png"))
logo = Canvas(window, width = 915, height = 50, highlightthickness=0, bd=0)
logo.create_image(0, 0, anchor=NW, image=logo_img) 
logo.place(x=25,y=10)

serial_box = Text(window,height=42,width=65,background='#22272e',bd=0,fg='#ffffff')
serial_box.place(x=965,y=10)
serial_box.configure(state='normal',exportselection=0)
serial_box.insert("end", "Started at %s \n" % datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
serial_box.configure(state='disabled',exportselection=0)

plot_box = Text(window,height=12,width=118,background='#22272e',bd=0,fg='#ffffff')
plot_box.place(x=10,y=520)
plot_box.configure(state='disabled',exportselection=0)

main_box_img = PhotoImage(file=resource_path("images\\main_box.png"))
main_box = Canvas(window, width = 924, height = 424, highlightthickness=0, bd=0)
main_box.create_image(0, 0, anchor=NW, image=main_box_img) 
main_box.place(x=20,y=85)

box_box_img = PhotoImage(file=resource_path("images\\box.png"))
box_box = Canvas(window, width = 438, height = 85, highlightthickness=0, bd=0)
box_box.create_image(0, 0, anchor=NW, image=box_box_img) 
box_box.place(x=490,y=414)

boxes_box_img = PhotoImage(file=resource_path("images\\boxes.png"))
boxes_box = Canvas(window, width = 438, height = 404, highlightthickness=0, bd=0)
boxes_box.create_image(0, 0, anchor=NW, image=boxes_box_img) 
boxes_box.place(x=35,y=95)

fire_img=PhotoImage(file=resource_path("images\\fire.png"))
fire_button = Button(window, highlightthickness=0, borderwidth=0, bd=0, text='',image=fire_img, command=lambda: fire())
fire_button.pack(ipadx=5, ipady=5, expand=True)
fire_button.place(x=490, y=102)

off_img=PhotoImage(file=resource_path("images\\off.png"))
off_button = Button(window, highlightthickness=0, borderwidth=0, bd=0, text='',image=off_img, command=lambda: relay_off())
off_button.pack(ipadx=5, ipady=5, expand=True)
off_button.place(x=490, y=208)

on_img=PhotoImage(file=resource_path("images\\on.png"))
on_button = Button(window, highlightthickness=0, borderwidth=0, bd=0, text='',image=on_img, command=lambda: relay_on())
on_button.pack(ipadx=5, ipady=5, expand=True)
on_button.place(x=490, y=315)

background_threads()
window.mainloop()