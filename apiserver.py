#!/usr/bin/env python

# apiserver.py		API server for the PiSpy camera
# version		0.0.5
# author		Brian Walter @briantwalter
# description		RESTful API for controlling and 
#			reading data for the PiSpy Camera

# imports
import os
import hashlib
import re
import json
from flask import Flask, jsonify, request

# static configs
path = "/home/pi/src/pispy/www/archive/jpg"

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
  print "DEBUG: city is", city.rstrip("\n")
  if city.rstrip("\n") == 'boise':
    thermfile = "/sys/bus/w1/devices/28-000005ff95db/w1_slave" # Boise thermometer
  if city.rstrip("\n") == 'seattle':
    thermfile = "/sys/bus/w1/devices/28-000005fd70d4/w1_slave" # Seattle thermometer
  print "DEBUG: thermfile is: ", thermfile
  if request.method == 'GET':
    infile = open(thermfile, "r")
    templine = infile.readlines()[1:]
    infile.close()
    print "DEBUG: raw file line: ", templine
    match = re.search('t=...', str(templine))
    if match:
      longc = re.sub(r't=', '', match.group())
      decc = float(longc) / 10;
      decf = float(((decc * 9) / 5) + 32)
      currenttemp = { 'celsius': round(decc, 1), 'fahrenheit': round(decf, 1) }
      return jsonify({'currenttemp': currenttemp})
    else:
      return json_error()

## list contents of archive
@app.route('/api/archive/ls', methods=['GET'])
def json_archive_ls():
  if request.method == 'GET':
    files = []
    contents = sorted(os.listdir(path))
    for file in contents:
      filename = file
      mtime = os.stat(path + "/" + file).st_mtime
      bytes = os.stat(path + "/" + file).st_size
      md5sum = hashlib.md5(path + "/" + file).hexdigest()
      files.append({'filename': filename, 'mtime': mtime, 'bytes': bytes, 'md5sum': md5sum})
  if files:
    return jsonify({'contents': files})
  else:
    return json_error()

## remove a file in the archive
@app.route('/api/archive/rm/<filename>', methods=['GET', 'POST', 'DELETE'])
def json_archive_rm(filename):
  if request.method == 'GET':
    return json_error_not_implemented()
  if request.method == 'POST' or request.method == 'DELETE':
    if os.path.isfile(path + "/" + filename):
      os.remove(path + "/" + filename)
      return jsonify({'status': 'removed file', 'filename': filename})
    else:
      return jsonify({'status': 'not a file', 'filename': filename})
  else:
    return json_error()


# main
if __name__ == '__main__':
  #app.debug = True
  app.port = 5000
  app.run()
