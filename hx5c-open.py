#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# RaspBerry Pi based Beehive Monitoring System
# Geo Meadows - 23Nov16
# 24Feb17 trap high temps
# 14Jun2018 
# HX711 code from 
# https://github.com/dcrystalj/hx711py3
#
# Thingspeak code from
# https://bitbucket.org/MattHawkinsUK/rpispy-misc/raw/master/python/templogger.py
#
# This version imports outside temperature from Skymeter 
# 
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

honeypi1 = 1				#select HoneyPi unit before running
import RPi.GPIO as GPIO
import time
import sys
import os
import urllib          
import urllib2 
import json        
from hx711 import HX711

SKYMETERKEY = 'VM1WO8P4K6WBIIK'	#skymeter
SKYCHANNEL_ID = '234010'
THINGSPEAKKEY_pi1 = 'Z80T57FMRRWHK3Y'  #currently hive 4
THINGSPEAKKEY_pi2 = 'MEV1ROOIWERHY0I' 	#currently hive 2
THINGSPEAKURL = 'https://api.thingspeak.com/update'

def readchan():		#get ambient off skymeter TS
    conn = urllib2.urlopen("http://api.thingspeak.com/channels/%s/feeds/last.json?api_key=%s" \
                           % (SKYCHANNEL_ID,SKYMETERKEY))
    response = conn.read()
    #print "http status code=%s" % (conn.getcode())
    data=json.loads(response)
    ambient = data['field4']
    #print ambient[0:4]
    #print data['field2'],data['created_at']
    conn.close()
    return (ambient)

def cleanAndExit():
    print "Cleaning..."
    GPIO.cleanup()
    print "Bye!"
    sys.exit()

def sendData(url,key,field1,field2,field3,field4,field5,field6,field7,weight,temp,amb,wt3,wt4,wt5,wt6):
  values = {'api_key' : key, 'field1' : weight, 'field2' : temp, 'field3':amb, 'field4':wt3, 'field5':wt4, 'field6':wt5, 'field7':wt6}

  postdata = urllib.urlencode(values)
  req = urllib2.Request(url, postdata)

  log = time.strftime("%d-%m-%Y,%H:%M:%S") + ","
  log = log + "{:.2f}Kg".format(weight) + ","
  log = log + "{:.1f}C".format(temp) + ","
  log = log + "{:.2f}C".format(amb) + ","

  try:			# Send data to Thingspeak
    response = urllib2.urlopen(req, None, 5)
    html_string = response.read()
    response.close()
    log = log + 'Update ' + html_string

  except urllib2.HTTPError, e:
    log = log + 'Server could not fulfill the request.  '
  except urllib2.URLError, e:
    log = log + 'Failed to reach server. ' 
  except:
    log = log + 'Unknown error'

  print log

###############
# Main Program
###############

print "\n+++ Starting Honey Pi +++\n"

f = open("./hive/zero.txt")
offset = f.read()
print "Loading Weight Offset: {}".format(offset)
f.close

f = open("./hive/chBzero.txt")
chBoffset = f.read()
print "Loading Temp Offset: {}\n".format(chBoffset)
f.close

time.sleep(30)	

while True:
    try:
        hx = HX711(17,27,128)			#(data,clk,chan A) Weight
        hx.set_reading_format("LSB", "MSB")
        if (honeypi1 == 1):
        	hx.set_reference_unit(92000)  	#106000 scaling - inc for smaller wt
        else:
		hx.set_reference_unit(106000)  	
        hx.set_offset(int(offset))    		#set zero offset
        load = 2*(hx.get_avg_weight(300,5))  	# (samples, spikes)
        print "weight = {:.3f}".format(load)
        time.sleep(1)
        GPIO.cleanup()

	hx = HX711(17,27,32)			#(data,clk,chan B) Temperature
	hx.set_reading_format("LSB","MSB")
        if (honeypi1 == 1):
		hx.set_reference_unit(470)
	else:
		hx.set_reference_unit(170000)    # scaling
        hx.set_offset(int(chBoffset)) 
        temp = hx.get_avg_weight(100,5)    
	time.sleep(5)
        temp = hx.get_avg_weight(100,5) 	
        print "temp = {:.2f}".format(temp)
        GPIO.cleanup()

	if (honeypi1 == 1):
        #	amb = float(readchan())		#get ambient off SkyMeter Pi
		amb = 1
	else:
		amb = 10
        print "ambient = {:.1f}".format(amb)
	
        if (honeypi1 == 1):
		key = THINGSPEAKKEY_pi1
        else:
		key = THINGSPEAKKEY_pi2
	
	if (temp>50):				# trap spikes	
	        temp = 30
	sendData(THINGSPEAKURL,key,'field1','field2','field3','field4','field5','field6','field7',load,temp,amb,load,load,load,load)
	sys.stdout.flush()

        print "Sleeping \n"
        time.sleep(125)#(90)				#  360=6min
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
