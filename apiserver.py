#!/usr/bin/env python

# apiserver.py		API server for the PiSpy camera
# version		0.0.8
# author		Brian Walter @briantwalter
# description		RESTful API for controlling and 
#			reading data for the PiSpy Camera

# imports
import os
import hashlib
import re
import json
import subprocess
from flask import Flask, Response, jsonify, request

# static configs
path = "/home/pi/src/pispy/www/archive"
cputempfile = "/sys/class/thermal/thermal_zone0/temp"
gputempcmd = "/opt/vc/bin/vcgencmd measure_temp | sed -e 's/^temp\=//' | rev | cut -c 3- | rev"

# create flask application object
app = Flask(__name__)

# non-routable functions
def json_error():
  return jsonify(status='error',error='generic', descrption='none')

def json_error_not_implemented():
  return jsonify(status='error',error='method', descrption='not implemented')

# routes for API calls
## temperature sensor
@app.route('/api/temp', methods=['GET', 'POST'])
def json_temp():
  location = open('/etc/location', "r")
  city = location.readline()
  location.close()
  if city.rstrip("\n") == 'boise':
    thermfile = "/sys/bus/w1/devices/28-000005ff95db/w1_slave" # Boise thermometer
  if city.rstrip("\n") == 'seattle':
    thermfile = "/sys/bus/w1/devices/28-000005fd70d4/w1_slave" # Seattle thermometer
  if city.rstrip("\n") == 'dummy':
    thermfile = "/home/pi/src/pispy/w1_slave.dummy" # Dummy thermometer
  if request.method == 'GET':
    infile = open(thermfile, "r")
    templine = infile.readlines()[1:]
    infile.close()
    match = re.search('t=...', str(templine))
    if match:
      # start external DS18B20 read
      longc = re.sub(r't=', '', match.group())
      decc = float(longc) / 10;
      decf = float(((decc * 9) / 5) + 32)
      externaltemp = { 'celsius': round(decc, 1), 'fahrenheit': round(decf, 1) }
      # start internal CPU read
      fh_cputemp = open(cputempfile, "r")
      cputemp_longc = fh_cputemp.readline()
      fh_cputemp.close() 
      cputemp_c = float(cputemp_longc) / 1000;
      cputemp_f = float(((cputemp_c * 9) / 5) + 32) 
      cputemp = { 'celsius': round(cputemp_c, 1), 'fahrenheit': round(cputemp_f, 1) }
      # start internal GPU read
      gputemp_c = subprocess.check_output(gputempcmd, shell=True)
      gputemp_f = float(((float(gputemp_c) * 9) / 5) + 32) 
      gputemp = { 'celsius': round(float(gputemp_c), 1), 'fahrenheit': round(gputemp_f, 1) }
      # build payload to return
      payload = ({'external': externaltemp, 'cpu': cputemp, 'gpu': gputemp})
      return Response(json.dumps(payload, indent=4, sort_keys=True), mimetype='application/json')
    else:
      return json_error()

## list contents of archive
@app.route('/api/archive/ls', methods=['GET'])
def json_archive_ls():
  if request.method == 'GET':
    images = []
    movies = []
    contents_jpg = sorted(os.listdir(path + "/jpg"))
    for image in contents_jpg:
      filename = image
      mtime = os.stat(path + "/jpg/" + image).st_mtime
      bytes = os.stat(path + "/jpg/" + image).st_size
      md5sum = hashlib.md5(path + "/jpg/" + image).hexdigest()
      images.append({'filename': filename, 'mtime': mtime, 'bytes': bytes, 'md5sum': md5sum})
    contents_mpg = sorted(os.listdir(path + "/mpg"))
    for movie in contents_mpg:
      filename = movie
      mtime = os.stat(path + "/mpg/" + movie).st_mtime
      bytes = os.stat(path + "/mpg/" + movie).st_size
      md5sum = hashlib.md5(path + "/mpg/" + movie).hexdigest()
      movies.append({'filename': filename, 'mtime': mtime, 'bytes': bytes, 'md5sum': md5sum})
  if images and movies:
    return Response(json.dumps({'images': images,'movies': movies},indent=4, sort_keys=True), mimetype='application/json')
  else:
    return json_error()

## remove a file in the archive
@app.route('/api/archive/rm/<filename>', methods=['GET', 'POST', 'DELETE'])
def json_archive_rm(filename):
  if request.method == 'GET':
    return json_error_not_implemented()
  if request.method == 'POST' or request.method == 'DELETE':
    if os.path.isfile(path + "/jpg/" + filename):
      os.remove(path + "/jpg/" + filename)
      return jsonify({'status': 'removed file', 'filename': filename})
    if os.path.isfile(path + "/mpg/" + filename):
      os.remove(path + "/mpg/" + filename)
      return jsonify({'status': 'removed file', 'filename': filename})
    else:
      return jsonify({'status': 'not a file', 'filename': filename})
  else:
    return json_error()


# main
if __name__ == '__main__':
  host = '0.0.0.0'
  port = 5000
  app.debug = True
  app.run(host, port)
