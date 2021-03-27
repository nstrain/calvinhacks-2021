# Lab 4: Program to continuously read A/D converter and log data
import Adafruit_MCP3008
import signal
from datetime import datetime
import RPi.GPIO as GPIO
import subprocess
import requests
# Constants
SAMPLE_TIME = 5
A2D_CHANNEL = 0
LED = 16
# SPI pin assignments
CLK = 25
MISO = 24
MOSI = 23
CS = 18
LIGHT = 75
MacNames = {"MAC NOT ON GITHUB": ["nathan", 0]}
#2 mins
LIGHT_MAX = 5*(60/SAMPLE_TIME)
WEB_LINK = 'https://cs326-final-n.herokuapp.com/devices/'
light_val = [False, 0, LIGHT_MAX]
# Instantiate a new A/D object
a2d = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)
# timer signal callback
def handler(signum, frame):
    print("evaluating")
    current_light = checkLight()
    lostFound = btCheck()
    uploadStatus(lostFound)
    if(current_light) < LIGHT:
        if(light_val[2] < LIGHT_MAX):
            light_val[2] -= 1
            if light_val[2] == 0:
                light_val[2] = LIGHT_MAX
                GPIO.output(LED, False)
        if light_val[1] > LIGHT and current_light < LIGHT:
            GPIO.output(LED, True)
            light_val[2] -= 1
        if (len(lostFound[1]) > 0):
            GPIO.output(LED, True)
            light_val[2] -= 1


    else:
        GPIO.output(LED, False)
        light_val[2] = LIGHT_MAX
    light_val[1] = current_light
    print("\tdone")

def checkLight():
    ''' Timer signal handler
    '''
    value = a2d.read_adc(A2D_CHANNEL)
    time = datetime.now().time()

    return value
def btCheck():
    returnList = [[],[]]
    for key in MacNames.keys():

        btName = str(subprocess.Popen("hcitool name " + str(key),shell=True,stdout=subprocess.PIPE).stdout.read())
        #Not found
        if(not len(btName) > len("b''")):
            #recently lost
            if(MacNames[key][1] > 0):
                returnList[0].append(MacNames[key][0])
                MacNames[key][1] = 0
                continue
        #recently found
        elif(MacNames[key][1] == 0): 
            returnList[1].append(MacNames[key][0])
            MacNames[key][1] = 1
    return returnList



def uploadStatus(lostFound):
    for i in lostFound[0]:
        requests.put(WEB_LINK + i + "/0")
    for i in lostFound[1]:
        requests.put(WEB_LINK + i + "/1")
# Setup interval timer signal every sample time
signal.signal(signal.SIGALRM, handler)
signal.setitimer(signal.ITIMER_REAL, 1, SAMPLE_TIME)

print('Press Ctrl-C to quit...')
try:
    while True:
        signal.pause()
except KeyboardInterrupt:
    signal.setitimer(signal.ITIMER_REAL, 0, 0) # Cancel inteval timer
    GPIO.cleanup()
    print('Done')

