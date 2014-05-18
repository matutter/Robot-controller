#! /usr/bin/python3
# non-blocking chatter demo #
####################################
# so occasionally the other thread will linger on std in
# and get that and then put the changed data back in the
# main process
import sys
import select
import time
import threading
import queue
####################################
# imports for RES
'''RES Controller'''
import motionSensor as mS
import motorControl as mC
import photocellManagement as pM
import ledManagement as lM
import ultrasonicSensor as uS
import temperatureSensor as tS
import RPi.GPIO as GPIO

'''print override for streamIO'''
instream = [sys.stdin]
# the timeout for maybe set to 0
# its a precausion for race conditions against the hardware
# example: data doesn't come in at the right time on the UART
timeout  = 0.01
baud_rate = 0.04
cmdQueue        = queue.Queue()
last_interrupt  = time.time()
global die
die = 0

def print(*args, **kwargs):
    __builtins__.print(*args, **kwargs)
    sys.stdout.flush()
    time.sleep(timeout)

def jprint(s1,s2):
  print('{"',s1,'":"',s2,'"}')

def jread():
  return sys.stdin.read().rstrip('\n')


'''SETUP ALL THE PINS'''
####################################
# resets
#GPIO.cleanup()
time.sleep(.02)
#ultrasonic
trig = 10
echo = 8
####################################
#photoresistor
pr = 5
####################################
#gear motors
left1 = 21
left2 = 11
right1 = 16
right2 = 18
####################################
#motion sensor
motion = 3
####################################
#LEDs
red = 13  
green = 19  
blue = 15   
rearl = 23
rearr = 26

uS.uSensorSetup(trig, echo)
pM.photoresistorSetup(pr)
mS.PIRSetup(motion)
lM.ledSetup(red, green, blue, rearl, rearr)
mC.motorPins(left1, left2, right1, right2)


global cur_dir
cur_dir = "S"
global dir_cycle
dir_cycle = 0
cycle_life = 1

def mstop():
  global dir_cycle
  global cur_dir
  cur_dir = "S"
  dir_cycle = 0
  #jprint("####################"," STOP ")
  mC.off()

def mforward():
  global dir_cycle
  global cur_dir
  cur_dir = "F"
  dir_cycle = cycle_life
  #jprint("####################"," FRONT ")
  mC.forward()

def mbackward():
  global dir_cycle
  global cur_dir
  cur_dir = "F"
  dir_cycle = cycle_life
  #jprint("####################","BACK")
  mC.reverse()

def mstop():
  global dir_cycle
  global cur_dir
  cur_dir = "S"
  dir_cycle = 0
  #jprint("####################"," STOP ")
  mC.off()

def mturnleft():
  global dir_cycle
  global cur_dir
  cur_dir = "FL"
  dir_cycle = cycle_life
  #jprint("####################"," FRONT ")
  mC.turnLeft()

def mturnright():
  global dir_cycle
  global cur_dir
  cur_dir = "FR"
  dir_cycle = cycle_life
  #jprint("####################","BACK")
  mC.turnRight()

global motor_keyword
motor_keyword = {}
#motor_keyword["S"] = mstop()
#motor_keyword["F"] = mforward()
#motor_keyword["FL"]= mC.turnLeft()
#motor_keyword["FR"]= mC.turnRight()
#motor_keyword["B"] = mbackward()
#motor_keyword["BL"]= mC.
#motor_keyword["BR"]= mC.


#####################################
# LONG POLL THREAD FOR PHOTO
def get_photo():
  global die
  last_light = 0

  while 1:
    if(die == 1):
      break
    time.sleep(timeout) 
    new_light = pM.lightLevel()
    if( new_light != last_light  ):
      jprint("photo", new_light )
      last_light = new_light


photo_thread = threading.Thread(target=get_photo)

# this is where input should be taken and inturperated into the 
# global commands that tell the robot what to do
# DO NOT PUT ANYTHING BLOCKING IN HERE
def handler(s):
  global last_interrupt
  global motor_keyword
  global die
  last_s = " "
  #jprint('handling',s)
  if(s == "die"):
    die = 1
    jprint("msg","goodbye")
    GPIO.cleanup()
    time.sleep( 2 )
    exit()
  if( last_s == s ):
    return


  if( s == "S" ):
    mstop()
  elif( s == "F" ):
    jprint("__DIR__","forward")
    mforward()
  elif( s == "B" ):      
    mbackward()
  elif( s == "FR" ):
    mturnright()
  elif( s == "FL" ):
    mturnleft()

  if( s == "red-light_1" ):
    lM.rgbActivate(lM.RED)
    jprint("leds-group",s)
  elif( s == "green-light_1" ):
    lM.rgbActivate(lM.GREEN)
    jprint("leds-group",s)
  elif( s == "blue-light_1" ):  
    lM.rgbActivate(lM.BLUE)
    jprint("leds-group",s)
  elif( s == "brake-light_1" ):
    lM.ledActivate(lM.rearl)
    lM.ledActivate(lM.rearr)
    jprint("leds-group",s)
  elif( s == "white-light_1" ):
    lM.rgbActivate(lM.WHITE)
    jprint("leds-group",s)

  elif( s == "red-light_0" ):
    lM.rgbDeactivate(lM.RED)
    jprint("leds-group",s)
  elif( s == "green-light_0" ):
    lM.rgbDeactivate(lM.GREEN)
    jprint("leds-group",s)
  elif( s == "blue-light_0" ):  
    lM.rgbDeactivate(lM.BLUE)
    jprint("leds-group",s)
  elif( s == "brake-light_0" ):
    lM.ledDeactivate(lM.rearl)
    lM.ledDeactivate(lM.rearr)
    jprint("leds-group",s)
  elif( s == "white-light_0" ):
    lM.rgbDeactivate(lM.WHITE)
    jprint("leds-group",s)

  last_s = s

  last_interrupt = time.time()

global last_life
last_life = 0
global new_life 
new_life = 0

def MAIN_LOOP():
  global last_interrupt
  global die
  global last_life
  global new_life
  global cur_dir
  global dir_cycle
  now = time.time()
  if now - last_interrupt > baud_rate:
    #jprint('msg','running smooth')
    ##########################
    # ROUTINES ###############

    if( dir_cycle > 0):
      dir_cycle-=1
      #jprint("^^^^^^^^^^^^^^^^^^",dir_cycle)
    else:
      mC.off()

    if( die ):
      return

    jprint("temp",tS.tempC())
    jprint("obstruction", uS.distance() )
    
    new_life = mS.PIRReading()
    if( last_life != new_life ):
      jprint("life", new_life)
      last_life = new_life

    ######################
    last_interrupt = now


# used to test if something got blocked and didn't run
# is called on a Ctrl-C
def cleanup():
  #print()
  while not cmdQueue.empty():
    s = cmdQueue.get()
    jprint("could not execute", s)
    GPIO.cleanup()
#########################################################
# non-blocking stdin read using semaphore locked thread #
#########################################################
interrupted = threading.Lock()
interrupted.acquire()

def get_stdin():
  while (instream and not interrupted.acquire(blocking=False)):
    ready = select.select(instream, [], [], timeout)[0]
    for file in ready:
      s = file.readline().rstrip('\n')
      handler(s)
      if not s:
        instream.remove(file)
  jprint('msg','stdin was closed')

input_thread = threading.Thread(target=get_stdin)
input_thread.start()

#########################################################

################################
# start other threads
photo_thread.start()

try:
  while True:
    if cmdQueue.empty() and not input_thread.is_alive():
      break
    else:
      try:
        handler(cmdQueue.get(timeout=timeout))
      except queue.Empty:
        MAIN_LOOP()
except KeyboardInterrupt:
  cleanup()

interrupted.release() # kill child zombies! :D
jprint('status','not_running')
