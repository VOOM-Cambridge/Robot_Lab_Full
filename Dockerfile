FROM python:3

ADD util_config/code/read_data2.py /

#RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir rpi.gpio 
RUN pip3 install bcr-libraries
RUN pip3 install spidev
RUN pip3 install Pillow
RUN pip3 install paho-mqtt
RUN pip3 install datetime
RUN pip3 install influxdb_client
#RUN pip3 install os
#RUN pip3 install time
#RUN apt-get install -yq python-smbus
#CMD ["bash", "setup-i2c.sh"]
# CMD modprobe i2c-dev && python /app/demo.py 
COPY util_config/code/uploadDataInflux.py .
CMD [ "python3", "./read_data2.py"]
