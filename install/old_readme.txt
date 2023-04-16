Preferences --> RPi Configuration --> Interfaces and enable all
Add CRobotics hat to the RPi, to 4th row of pins (0-1-2-3-4)

$cd energy
$sudo install.sh

$docker container ls
CONTAINER ID   IMAGE                        COMMAND                  CREATED        STATUS        PORTS                              NAMES
4f9308f22ca8   read_data:v1                 "python3 ./read_data…"   27 hours ago   Up 23 hours                                      read_data
4fdfe3dab6bd   grafana/grafana              "/run.sh"                27 hours ago   Up 23 hours   0.0.0.0:3000->3000/tcp             grafana
2943c5fe5b03   hypriot/rpi-influxdb         "/usr/bin/entry.sh /…"   27 hours ago   Up 23 hours   0.0.0.0:8089->8086/tcp             influxdb
bd55080a1540   pascaldevink/rpi-mosquitto   "/bin/sh -c '/usr/sb…"   27 hours ago   Up 23 hours   0.0.0.0:1883->1883/tcp, 9001/tcp   mosquitto

open a browser to localhost:3000
In Grafana:
1- go to bottom left, choose data sources
2- Add data surce button
3- Choose InfluxDB
4- vi energy/docker-compose.yml
4- In HTTP section complete the URL box with the IP from services > influxcb_emon > ipv4_address
5- In Database complete the box with "emon"
6- Save and test
7- go to top left, choose Dashboards
8- Add a new dashboard
9- Add a gauge for Power and a gauge for Current
10- Add time series for power and energy <-- to complete