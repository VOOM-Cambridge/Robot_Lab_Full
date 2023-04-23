from uploadDataInflux import influxUploadData
from emonProcessing import emonProcessing
import json
import tomli
import os
from datetime import datetime
import time
import logging

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)  # move to log config file using python functionality

#with open('util_config/utilisation_config.json') as util_file:
#    config_util = json.load(util_file)

def get_config():
    with open("./config/config.toml", "rb") as f:
        toml_conf = tomli.load(f)
        logger.info(f"config loaded:{toml_conf}")
    return toml_conf

config_util = get_config()
#power = ["Machine1", "Machine2", "Machine3", "Machine4", "Machine5"]
threshold = config_util["constants"]["machine_in_use_threshold"]
hourStart = config_util["constants"]["start_hour_facotry"]
hourEnd = config_util["constants"]["end_hour_factory"]
timeNow = datetime.now()
timeStart = datetime(timeNow.year, timeNow.month, timeNow.day, hourStart, 0, 0)
timeEnd = datetime(timeNow.year, timeNow.month, timeNow.day, hourEnd, 0, 0)
frequUtilUpdate = config_util["constants"]["frequency_update_seconds"]

config_influx_dict = config_util["docker"]
config_influx_dict["org"] = os.environ['DOCKER_INFLUXDB_ORG']
config_influx_dict["token"] = os.environ['DOCKER_CURRENT_INFLUXDB_TOKEN']
config_influx_dict["bucket"] = os.environ['DOCKER_INFLUXDB_BUCKET']

while True:
    
    # update times for day operation limits
    timeNow = datetime.now()
    if timeNow.day != timeStart.day:
        # new day of time
        timeStart = datetime(timeNow.year, timeNow.month, timeNow.day, hourStart, 0, 0)
        timeEnd = datetime(timeNow.year, timeNow.month, timeNow.day, hourEnd, 0, 0)
    
    influxClient = emonProcessing(config_influx_dict)
    #print(time.time())
    machineList = influxClient.findAllMachineNames()
    for machine in machineList:
        # test the last reading look 5 seocnds back in readings
        if type(machine) == list:
            machine = machine[0]
        k, measurement_name, timeStamp, curentVal = influxClient.test_last_read(machine, 5, "current")
        #print("****")
        if len(k) == 1:
            valLabel = "current"
            timeS = time.mktime(timeStart.timetuple())
            #try:
            out = influxClient.updateEmonValue(machine, threshold, measurement_name, timeStamp, curentVal, timeS)
            #except:
            #    logger.info(f"Error calcualting utilisation")

    time.sleep(frequUtilUpdate)


