
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
from sqliteConnect import sqliteConnect

with open("config/config.toml", "rb") as f:
        toml_conf = tomli.load(f)

# create connection to database and make if it doesn't exist
config = toml_conf['sqlite3']
newConnection = sqliteConnect(config)
newConnection.connect()

# Scanner details 
serialID = toml_conf['constants']['serialID'] 
locationID = toml_conf['constants']['location'] 
#'16c0:27db'
#"Printin_Lab"
#usbPort = '1.2:10'

port = 1883
broker = toml_conf['constants']['brokerIP']
topic = "worker_scan/" +locationID + "/"

client = mqtt.Client("rfid1")

# find devices connected and look for scanner needed
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


def mqtt_send(ID_barcode, state_mess, name, workerTime):
    mess = {}
    mess["location"] = locationID
    mess["id"] = ID_barcode
    mess["state"] = state_mess
    mess["name"] = name
    mess['timeWorked'] = workerTime
    mess["timestamp"]= str(datetime.now())
    mess_send = json.dumps(mess)
    print(mess)
    client.connect(broker, port)
    time.sleep(0.1)
    client.publish(topic, mess_send)


def change_sate(barcode, name):
    check = newConnection.checkIfExists(barcode)
    if len(check) > 0:
        # then there is already and entry update it
        stateFound = check[2]
        workerTime = check[4]
        name = check[1]
        if stateFound == "Log in":
            newConnection.updateStatus(barcode, "Log out")
            stateFound = "Log out"
        elif stateFound == "Log out":
            newConnection.updateStatus(barcode, "Log in")
            stateFound = "Log in"
    else:
        # no worker alreayd add new entry
        newConnection.addNew(barcode, name, "Log in")
        stateFound = "Log in"
    check = newConnection.checkIfExists(barcode)
    mqtt_send(barcode, stateFound, name, check[4])
    print(check[4])

async def helper(dev):
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
                    # update database infomation and send MQTT
                    change_sate(barcode, "__blank__")
                    
                    barcode = ""
                else:
                    barcode = barcode + keycode.split("_")[1]
                

while True:
    print("start")
    
    rfid_device = findDevice()
    if len(rfid_device) > 0: 
        loop = asyncio.get_event_loop()
        loop.run_until_complete(helper(rfid_device[0]))
