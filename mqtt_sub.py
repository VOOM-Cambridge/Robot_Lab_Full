import paho.mqtt.client as mqtt

port = 1883
broker = "localhost"
#broker = "192.168.5.94"
timelive = 60

with open('influxdb/config/config_influx.json') as influx_file:
    config_influx_dict = json.load(influx_file)
with open('util_config/utilisation_config.json') as util_file:
    config_util = json.load(util_file)
    
threshold = config_util["machine_in_use_threshold"]
hourStart = config_util["start_hour_facotry"]
hourEnd = config_util["end_hour_factory"]
bucketName = config_influx_dict['bucket']
timeNow = datetime.now()
timeStart = datetime(timeNow.year, timeNow.month, timeNow.day, hourStart, 0, 0)
timeEnd = datetime(timeNow.year, timeNow.month, timeNow.day, hourEnd, 0, 0)
frequUtilUpdate = config_util["frequency_update_seconds"]
timeUpdUtil = datetime.now()
freqEmon = config_influx_dict["frequency_record_seconds"]
timeSenLast = time.time()
influx_client = InfluxDBClient(
    url="http://{0}:{1}".format(config_influx_dict['ip'], config_influx_dict['port']),
    token=config_influx_dict['token'],
    org=config_influx_dict['org'],
    verify_ssl=False
   )

def on_conn(client, userdata, flag, rc):
    print("connected")
    client.subscribe("#")

def on_diss(client, userdata, flag, rc):
    print("not connected")
    client.subscribe("#")
    
def on_mess(client, userdata, msg):
    print("messeage: ")
    topic = msg.topic
    mess = msg.payload.decode()
    uploadToInflux(topic, mess, influx_client)

def uploadToInflux(topic, mess, influx_client):
    if topic == "energy":
        uploadEnergy(mess, influx_client)
    elif topic == "weight":
        uploadWeight(mess, influx_client)
    else:
        uploadOther(mess, influx_client)
    

client = mqtt.Client()
client.connect(broker, port, timelive)
client.on_connect = on_conn
client.on_disconnect = on_diss
client.on_message = on_mess


client.loop_forever()
