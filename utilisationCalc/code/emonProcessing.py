import json
from datetime import datetime
import time
from uploadDataInflux import influxUploadData
import logging

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

class emonProcessing(influxUploadData):
        
    def findUtil(self, startTime, endTime, name):
        try:
            query_api = self.influx_client.query_api()
            eTime = time.mktime(endTime.timetuple())
            # query to integrate the machine state curve to find utilisation
            query = 'from(bucket: "'+ self.bucketName +'")\
                |> range(start: ' + str(round(startTime)) +', stop: ' + str(round(eTime)) +')\
                |> filter(fn: (r) => r["machine"] == "'+ name +'")\
                |> filter(fn: (r) => r["_field"] == "machineState")\
                |> integral(unit: 1s)'
            table = query_api.query(query)
            output = table.to_values(columns=['_value'])
            # take value from integration and divide by the number of seconds past 
            utilValue = output[0][0]/(eTime - startTime)
        except:
            utilValue = []
            logger.info(f"Error no data found for utilisation")
        return utilValue
    
    def findTotalKWh(self, startTime, endTime, name):
        try:
            query_api = self.influx_client.query_api()
            eTime = time.mktime(endTime.timetuple())
            # query to integrate the machine state curve to find utilisation
            query = 'from(bucket: "'+ self.bucketName +'")\
                |> range(start: ' + str(round(startTime)) +', stop: ' + str(round(eTime)) +')\
                |> filter(fn: (r) => r["machine"] == "'+ name +'")\
                |> filter(fn: (r) => r["_field"] == "power")\
                |> integral(unit: 1s)'
            table = query_api.query(query)
            output = table.to_values(columns=['_value'])
            # take value from integration and divide by the number of seconds past 
            total = output[0][0]/3600/1000
        except:
            total =[]
            logger.info(f"Error no data found for Power Use calculation")
        return total
    
    def test_last_read(self, name, sec, measure):
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "'+ self.bucketName +'")\
                |> range(start: ' + str(-sec) + 's)\
                |> filter(fn: (r) => r["machine"] == "' + name +'")\
                |> filter(fn: (r) => r["_field"] == "'+ measure +'")\
                |> last(column: "_time")'
        table = query_api.query(query)
        output = table.to_values(columns=['_measurement', '_value', '_time'])
        len(output)
        if len(output) > 0:
            measurement_name = output[0][0]
            timeOut = output[0][2]
            current = output[0][1]
        else:
            measurement_name = None
            timeOut = datetime.now()
            timeOut = time.mktime(timeOut.timetuple())
            current = None
        return output, measurement_name, timeOut, current
    
    def updateEmonValue(self, name, threshold, measurementName, timeStamp, curentVal, timeS):
        machOn = int(curentVal > threshold)
        self.store_data("machineState", machOn, name, measurementName, timeStamp)
        util = self.findUtil(timeS, timeStamp, name)
        totalPower = self.findTotalKWh(timeS, timeStamp, name)
        self.store_data("utilisation", util, name,  measurementName, timeStamp)
        self.store_data("totalUse", totalPower, name,  measurementName, timeStamp)
        #return "Done"

    def findAllMachineNames(self):
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "'+ self.bucketName +'")\
                |> range(start: ' + str(-1) + 'd)\
                |> filter(fn: (r) => r["_field"] == "current")\
                |> last(column: "_time")'
        table = query_api.query(query)
        output = table.to_values(columns=['machine'])
        return output
    