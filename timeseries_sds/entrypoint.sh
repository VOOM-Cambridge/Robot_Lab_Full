#!/bin/sh

set -e
influx bucket create -n $DOCKER_INFLUXDB_BUCKET -r 7d
influx bucket create -n $DB_BUCKET_SECOND -r 7d