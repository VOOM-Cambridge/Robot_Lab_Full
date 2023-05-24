    #!/usr/bin/env python
import pyudev
import evdev
import asyncio
from evdev import ecodes, categorize
import paho.mqtt.client as mqtt
from datetime import datetime
import json
import time
import tomli

with open("config.toml", "rb") as f:
        toml_conf = tomli.load(f)

serialID = toml_conf['constants']['serialID'] 
locationID = toml_conf['constants']['location'] 
#'16c0:27db'
#"Printin_Lab"
#usbPort = '1.2:10'

state = "Log out"


port = 1883
broker = toml_conf['constants']['brokerIP']
topic = "worker_scan/" +locationID + "/"

store_data = {}

client = mqtt.Client("rfid1")
def findDevice():
    context = pyudev.Context()
    rfid_device = []
    #print(list(context.list_devices(subsystem = 'input', ID_BUS = 'usb')))
    for device in context.list_devices(subsystem = 'input', ID_BUS = 'usb'):
        ID = device.properties['ID_VENDOR_ID'] + ":" + device.properties['ID_MODEL_ID']
        #ID = device
        if ID == serialID and device.device_node != None:
            dev = device
        #rfid_device = evdev.InputDevice(device.device_node)
            if device.tags.__contains__('power-switch'):
                x = evdev.InputDevice(device.device_node)
                rfid_device.append(x)
                print("device found")
                print(device)
    return rfid_device




def mqtt_send(ID_barcode, state_mess):
    mess = {}
    mess["location"] = locationID
    mess["id"] = ID_barcode
    mess["state"] = state_mess
    mess["timestamp"]= str(datetime.now())
    
    mess_send = json.dumps(mess)
    
    client.connect(broker, port)
    time.sleep(0.1)
    client.publish(topic, mess_send)
    print("mess sent")


def save_date(IDnum, state):
    store_data[IDnum] ={}
    store_data[IDnum]["state"] = state
    store_data[IDnum]["last_update"] = datetime.now()
    
def update_data(IDnum, state):
    store_data[IDnum]["state"] = state
    store_data[IDnum]["last_update"] = datetime.now()


def check_sate(barcode):
    for key in store_data:
        if key == barcode:
            return store_data[key]["state"]
        
    return ""

async def helper(dev, state):
    barcode = ""
    async for ev in dev.async_read_loop():
        #keyname = x.keycode[4:]
        if ev.type == ecodes.EV_KEY:
            x=categorize(ev)
            
            if x.keystate == 1:
                #print(x)
                scancode = x.scancode
                keycode = x.keycode
                
                if keycode=="KEY_ENTER":
                    print(barcode)
                    check = check_sate(barcode)
                    
                    if check == "" or check == None:
                        save_date(barcode, "Log in")
                    else:
                        if check =="Log in":
                            new ="Log out"
                        else:
                            new = "Log in"
                        update_data(barcode, new) 
                    
                    state = check
                    
                    if state =="Log in":
                        mqtt_send(str(barcode), "Log out")
                        state ="Log out"
                        
                    else:
                        mqtt_send(str(barcode), "Log in")
                        state ="Log in"
                    barcode = ""
                    
                else:
                    barcode = barcode + keycode.split("_")[1]
                

while True:
    
    state = "Log in"
    print("start")
    
    rfid_device = findDevice()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(helper(rfid_device[0], state))



# if len(rfid_device)>0:
#     print("devices = 1")
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(helper(rfid_device[0]))
#     
#     
#     if len(rfid_device)>1:
#         print("devices = 2")
#         loop2 = asyncio.get_event_loop()
#         loop2.run_until_complete(helper(rfid_device[1]))
#         print("loop")
        
    
