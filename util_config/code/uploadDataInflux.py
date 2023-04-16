import json
from datetime import datetime
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

""" 
This class is designed to help format use of the influx client and API
For each databases connected to, organisations or buckets a different instance can be created
"""
class influxUploadData:
    def __init__(self, config_file_json):
        self.org = config_file_json['org']
        self.token = config_file_json['token']
        self.bucketName = config_file_json['bucket']
        self.ipaddress = config_file_json['ip']
        self.port = config_file_json['port']
        self.freq = config_file_json["frequency_record_seconds"]
        self.influx_client = InfluxDBClient(
            url="http://{0}:{1}".format(self.ipaddress, self.port),
            token=self.token,
            org=self.org,
            verify_ssl=False)
        #print(self)
    
    def store_data(self, data, device_name, measurementName, sensor_name):
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        leng = len(data)
        for i in range(leng):
            variable_value = data[i]
            variable_name = device_name[i]
            point = Point.measurement(measurementName).tag("sensor_type", sensor_name).tag("Machine", variable_name).field(variable_name, variable_value)#.time(date_time_obj)
            self.write_api.write(bucket=self.bucketName, org=self.org, record=point)
            #print("submitted")

    def sum_energy_use(self, datetimeStart, datetimeEnd, machineName, emonFreq):  # sum total energy use in kWh
        startT = time.mktime(datetimeStart.timetuple())
        endT = time.mktime(datetimeEnd.timetuple())
        #from(bucket: "example-bucket")
        #|> range(start: 1621726200, stop: 1621728000)
        query_api = self.influx_client.query_api() 
    
        query = 'from(bucket: "'+ self.bucketName +'")\
            |> range(start: '+ str(round(startT)) +', stop: ' + str(round(endT)) +')\
            |> filter(fn: (r) => r["_field"] == "'+ machineName +'")\
            |> filter(fn: (r) => r["_measurement"] == "Power")\
            |> sum()'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
        #print(output[0][0])
        try:
            kwoutput = output[0][0]*emonFreq/3600
        except:
            try:
                kwoutput = output[0]*emonFreq/3600
            except:
                kwoutput = output*emonFreq/3600
        return kwoutput
        
    def calcualte_util(self, minsGone, machineName):
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "'+ self.bucketName +'")\
            |> range(start: ' + str(-minsGone) + 'm)\
            |> filter(fn: (r) => r["_field"] == "'+ machineName +'")\
            |> filter(fn: (r) => r["_measurement"] == "machineState")'
        table = query_api.query(query)
        leng = 1 + len(table.to_values(columns=['_value']))
        output = table.to_values(columns=['_value'])
        total = sum([sum(a) for a in output])/leng
        return total
    