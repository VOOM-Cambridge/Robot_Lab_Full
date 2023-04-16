import json
from datetime import datetime
import time
from uploadDataInflux import influxUploadData
import os
import paho.mqtt.client as mqtt
import random

try:
    from bcr_mcp3008 import MCP3008
    adc0 = [MCP3008(device = 0), MCP3008(device = 0), MCP3008(device = 0), MCP3008(device = 0), MCP3008(device = 1)]
except:
    print("Sensor connection not possible")

broker = "mosquitto"
port = 1883
freq = 5

if isinstance(port, str):
    port = int(port)

if isinstance(freq, str):
    freq = int(freq)

def on_pub(client, userdata, result):
    print("Published MQTT")
    pass

freqEmon = 2
power = ["Machine1", "Machine2", "Machine3", "Machine4", "Machine5"]
interval = 0.1             # How long we want to wait between loops (in seconds)
sampleDelay = 0.20          # Waiting time between readings from channel (in seconds)
maxSamples = 5              # Maximum number of samples
channel = [1, 3, 4, 6, 0]                 # Channel number from BCRobotics hat 
lineVoltage = 230           # Assumed voltage in the line
CTRange = 20                # Nominal Amps of the CT clamp 
deviceVoltage = 3.3         # Voltage of the device 3.3 for RPi or 5.0 for Arduino
numSen = len(power)
ACC_total = [0]*numSen
ti_lastMqtt = datetime.now()
num =0
util = [0]*numSen
sumEmon = [0]*numSen
totalUtil = [0]*numSen
client1 = mqtt.Client("energyMon")

with open('util_config/utilisation_config.json') as util_file:
    config_util = json.load(util_file)
    
threshold = config_util["machine_in_use_threshold"]
hourStart = config_util["start_hour_facotry"]
hourEnd = config_util["end_hour_factory"]
timeNow = datetime.now()
timeSenLast = datetime.now()
timeStart = datetime(timeNow.year, timeNow.month, timeNow.day, hourStart, 0, 0)
timeEnd = datetime(timeNow.year, timeNow.month, timeNow.day, hourEnd, 0, 0)
frequUtilUpdate = config_util["frequency_update_seconds"]
timeUpdUtil = datetime.now()
minsGone = 0

def findSenValue():
    readValue = [0]*numSen
    data = [0]*numSen 
    for i in range(maxSamples):
        for i in range(numSen):
            try:
                dat = adc0[i].readData(channel[i]) -1
            except:
                dat = 0
            data[i] = dat
            readValue[i] = readValue[i] + dat
        time.sleep(sampleDelay)
    readValue[:] = [x/maxSamples for x in readValue] 
    voltageVirtualValue = [x*0.7706 for x in readValue]
    voltageVirtualValue[:] = [(x/1024 * deviceVoltage) / 2 for x in voltageVirtualValue]
    ACCurrtntValue = [x*CTRange for x in voltageVirtualValue]
    powerValue = [x*lineVoltage for x in ACCurrtntValue]
    machineOn = [int(x > threshold) for x in ACCurrtntValue]

    return ACCurrtntValue, powerValue, machineOn

def send_data_mqtt(data, names):
    m ={}
    for i in range(len(data)):
        nameToUse = names[i]
        m[nameToUse] = data[i] 
    mess = json.dumps(m)
    #print(mess)
    client1.on_publish = on_pub
    client1.connect(broker, port)
    client1.publish("dataIn/energy/", mess)


while True:
    with open('influxdb/config/config_influx.json') as influx_file:
        config_influx_dict = json.load(influx_file)
    device_type = "current_sensorV2"
    #print(config_influx_dict)
    influxClient = influxUploadData(config_influx_dict)
    machineOn =[0]*numSen
    variable_list = ["current"]
    # set time of end and start if new day and time loop values
    timeNow = datetime.now()
    if timeNow.day != timeStart.day:
        # new day of time
        timeStart = datetime(timeNow.year, timeNow.month, timeNow.day, hourStart, 0, 0)
        timeEnd = datetime(timeNow.year, timeNow.month, timeNow.day, hourEnd, 0, 0)
        # reset new time 
        number_readings = 0
    # Set new day if not set 
    if timeNow.hour >= timeEnd.hour:
        minsGone = round((timeEnd - timeStart).total_seconds() / 60.0)
    else:
        minsGone = round((timeNow - timeStart).total_seconds() / 60.0)
    
    # if frequency of Energy reporting is found the
    if (timeNow - timeSenLast).total_seconds() > freqEmon:
        try:
            currentData, powerData, machineOn = findSenValue()
        except:
            currentData = [0]*numSen
            powerData = [0]*numSen
            machineOn = [0]*numSen

        # Sendign all data in different formats to Influxdb
        influxClient.store_data(powerData, power, "Power", device_type)
        influxClient.store_data(machineOn, power, "machineState", device_type)
        influxClient.store_data(currentData, power, "current", device_type)
        influxClient.store_data(powerData, power, "Power", device_type)
        totalUtil = [(totalUtil[i] + machineOn[i]) for i in range(numSen)]
        for i in range(numSen): 
            sumEmon[i] = influxClient.sum_energy_use(timeStart, timeNow, power[i], freqEmon)
        influxClient.store_data(sumEmon, power, "totalUse", device_type)
        timeSenLast = datetime.now()
    
    if (timeNow - timeUpdUtil).total_seconds() >= frequUtilUpdate:
        for i in range(numSen):
            totalUtil[i] = influxClient.calcualte_util(minsGone, power[i])
        util =  totalUtil
        #print(util)
        influxClient.store_data(util, power, "utilisation", device_type)
        timeUpdUtil = datetime.now()

    #if (timeNow - ti_lastMqtt).total_seconds() >= freq:
        #try:
        #    send_data_mqtt(powerData, power)
        #except:
        #    print("No MQTT connection")        
        #ti_lastMqtt = datetime.now()

    time.sleep(0.2)