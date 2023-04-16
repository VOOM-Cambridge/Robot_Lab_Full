import socket
import paho.mqtt.client as mqtt
import asyncio

class AsyncioHelper:
    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write
        self.error = self.loop.create_future()

    def on_socket_open(self, client, userdata, sock):
        print("MQTT> Socket opened")
        def cb():
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        print("MQTT> Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        print("MQTT> Watching socket for writability.")
        def cb():
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        print("MQTT> Stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                print("MQTT> MISC TASK CANCELLED")
                break
        self.error.set_result(True)


class AsyncMqttLoop:
    def __init__(self, loop, queue_out, queue_in, config):
        self.client_id = config.get('client_name','mqtt_default')
        self.loop = loop
        self.queue_out = queue_out
        self.queue_in = queue_in
        self.ca_cert_path = config.get('ca_cert','')
        self.initial_topics = config.get('sub_topics',[])
        self.broker_fqdn = config.get('broker_fqdn',"localhost")
        self.broker_port = config.get('broker_port',1883)
        self.keepalive = config.get('keepalive',60)

    def on_connect(self, client, userdata, flags, rc):
        print("MQTT> {id}: subscribing to initial topics: {topics}".format(id=self.client_id,topics=self.initial_topics))
        for topic in self.initial_topics:
            client.subscribe(topic,qos=1)

    def on_message(self, client, userdata, msg):
        if not self.got_message:
            print("MQTT> {id}: Got unexpected message: {msg}".format(id=self.client_id, msg=msg.decode()))
        else:
            self.got_message.set_result(msg)

    def on_disconnect(self, client, userdata, rc):
        self.disconnected.set_result(rc)

    async def run(self):
        self.disconnected = self.loop.create_future()

        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        aioh = AsyncioHelper(self.loop, self.client)
        
        if self.ca_cert_path != '':
            self.client.tls_set(self.ca_cert_path,tls_version=2)
        connected = False
        while not connected:
            try:
                self.client.connect(self.broker_fqdn, self.broker_port, self.keepalive)
                connected=True
            except Exception as e:
                print(e)
        
        t1 = asyncio.create_task(self.check_inbound())
        t2 = asyncio.create_task(self.check_outbound())
        while True:
            await aioh.error
            print("MQTT> ERROR IN MQTT LOOP")
            self.client.disconnect()
            print("MQTT> Disconnected: {}".format(await self.disconnected))
            self.client.reconnect()
            #aioh = AsyncioHelper(self.loop, self.client)

    async def check_inbound(self):
        self.got_message = self.loop.create_future()
        while True:
            msg = await self.got_message
            print("MQTT> {id}: Got msg: {msg}".format(msg=msg,id=self.client_id))
            await self.queue_in.put(msg)
            self.got_message = self.loop.create_future()
    
    async def forwardOn(mess, self):
            broker="192.168.5.220"
            port=8883
            def on_publishForward(client,userdata,result):            
                print("MQTT> sending second messeage to other broker")
                pass
            client_id_new = "test_connection_1"
            client1= mqtt.Client(client_id_new)                           #create client object
            client1.on_publish = on_publishForward                         #assign function to callback
            client1.connect(broker, port)                                 #establish connection
            print("MQTT> forwading on a new messeage for other broker _________________________________ space" )
            client1.publish(mess['topic'],mess['payload'], qos=1)
            client1.disconnect()

    async def check_outbound(self):
        while True:
            msg_out = await self.queue_out.get()
            print("MQTT> {id}: Sending: {msg}".format(msg=msg_out,id=self.client_id))
            self.client.publish(msg_out['topic'],msg_out['payload'], qos=1)
            self.forwardOn(msg_out, self)
