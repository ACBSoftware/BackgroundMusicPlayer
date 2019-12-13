#!/usr/bin/env python'
import RPi.GPIO as GPIO
import time
import os
import subprocess
import random
import datetime
from subprocess import Popen
import shutil

### DISCLAIMER: THIS CODE IS FOR ENTERTAINMENT PURPOSES ONLY. NO WARRANTIES OR GUARANTEES IMPLIED. 
### For more info on this script see youtube.com/ACBMemphis

##########################
##### CONFIG AREA ########
##########################

#Within the controldata object, specify GPIO number for playlist select button and LEDs
controldata = {}
controldata["playlistButtonGPIONumber"] = 24 #Ground -> Resistor -> Momentary Switch -> GPIO
controldata["output"] = "local" #local for line level or "hdmi"
controldata["playlists"] = {}

playlist = {}
playlist["filespath"] = "/home/pi/Music/collection1/"
playlist["LEDGPIONumber"] = 16 #Ground -> Resistor -> LED -> GPIO
controldata["playlists"][0] = playlist

playlist = {}
playlist["filespath"] = "/home/pi/Music/collection2/"
playlist["LEDGPIONumber"] = 20
controldata["playlists"][1] = playlist

playlist = {}
playlist["filespath"] = "/home/pi/Music/collection3/"
playlist["LEDGPIONumber"] = 21
controldata["playlists"][2] = playlist

scriptrundir = "/home/pi/Desktop"

##########################
#### HELPER FUNCTIONS ####
##########################

###### Sets one LED on and others off
def SetActivePlaylistLED(number):
    for key, value in controldata["playlists"].items():
        if key == number:
            GPIO.output(value["LEDGPIONumber"],GPIO.HIGH)
        else:
            GPIO.output(value["LEDGPIONumber"],GPIO.LOW)

###### Plays a sound effect file during playlist update
def PlaySoundEffect(filename):
    try:
        tempprocess = Popen(['omxplayer',"-o",controldata["output"],"--no-keys", filename])
        tempprocess.wait()
        time.sleep(2)
    except:
        print("Error playing sound effect " + filename)
        
###### Replaces playlist folder from USB drive during update
def ReplacePlaylistFolder(sourcefolder, destfolder):
    try:
        print("Deleting files in " + destfolder)
        dst_files = os.listdir(destfolder)
        for file_name in dst_files:
            full_file_name = os.path.join(destfolder, file_name)
            if os.path.isfile(full_file_name):
                try:
                    os.remove(full_file_name)
                except:
                    print("Error deleting: " + full_file_name)
                    
        print("Copying files from " + sourcefolder + " to " + destfolder)
        src_files = os.listdir(sourcefolder)
        for file_name in src_files:
            full_file_name = os.path.join(sourcefolder, file_name)
            dest_file_name = os.path.join(destfolder, file_name)
            if os.path.isfile(full_file_name):
                try:
                    shutil.copy(full_file_name, dest_file_name)
                    print(".")
                except:
                    print("Error copying: " + full_file_name)
    except:
        print("ERROR REPLACING PLAYLIST FOLDER!")
        
###### Runs update of playlist from a USB Drive
###### Assumes folders /media/pi/VOLUMELABEL/collectionX where x is 1,2,3
def CheckForUpgrade():
    try:
        foundsomething=False
        print("CHECKING FOR USB DRIVE WITH MP3 UPDATE")
        arrayofdrives = os.listdir("/media/pi/")
        if len(arrayofdrives) > 0:
            PlaySoundEffect("updatemode.mp3")
            time.sleep(1)
            runningprocess = None
            pathtocheck = "/media/pi/" + arrayofdrives[0] + "/"
            arrayoftoplevel = os.listdir(pathtocheck)
            for foldername in arrayoftoplevel:
                if foldername.startswith('collection'):
                    print('Found ' + foldername)
                    filesinfolder = os.listdir(pathtocheck + foldername)
                    playlistindextoreplace = int(foldername[-1:]) - 1
                    if len(filesinfolder) > 0:
                        foundsomething=True
                        print('Upgrading ' + foldername + ' from USB drive...')
                        PlaySoundEffect("updatestarted.mp3")
                        ReplacePlaylistFolder(pathtocheck + foldername, controldata["playlists"][playlistindextoreplace]["filespath"])
            if foundsomething:
                PlaySoundEffect("updatecomplete.mp3")
                print("UPDATE COMPLETE")
            else:
                PlaySoundEffect("updatemissing.mp3")
                print("NO FILES UPDATED")
            #EJECT USB DRIVE
            print("Eject")
            PlaySoundEffect("ejectingusb.mp3")
            os.system("sudo umount /media/pi/" + arrayofdrives[0])
        else:
            print("USB DRIVE NOT DETECTED")
    except:
        print("Error doing update")
        
###### Checks for a file with the last index, so we resume on the same playlist after a power outage
def RetrieveLastPlaylistIndex():
    lastplaylistindex = 0
    try:
        if os.path.isfile("last.txt"):
            with open ('last.txt', 'r') as afile:
                valuefromfile=afile.read()
                lastplaylistindex = int(valuefromfile)
    except:
        print("Error getting last playlist index")
    print ("last index = " + str(lastplaylistindex))
    return lastplaylistindex

###### Writes last index to a file, so we resume on the same playlist after a power outage
def SaveLastPlaylistIndex(index):
    try:
        with open ('last.txt', 'w') as afile:
            afile.write(str(index))
    except:
        print("Error saving last playlist index")


############################
###### INITIALIZATION ######
##### (App starts here) ####       
############################
#Change working directory to that of this script so sounds will work       
os.chdir(scriptrundir)        
PlaySoundEffect("startupsound.mp3")

print('Setting up...')
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

print('Setting playlist select button up as GPIO ' + str(controldata["playlistButtonGPIONumber"]))
GPIO.setup(controldata["playlistButtonGPIONumber"], GPIO.IN, pull_up_down=GPIO.PUD_UP)

max_playlist = 0
for key, value in controldata["playlists"].items():
    print('Setting playlist ' + str(key) + ' LED as GPIO ' + str(value["LEDGPIONumber"]))
    GPIO.setup(value["LEDGPIONumber"],GPIO.OUT)
    GPIO.output(value["LEDGPIONumber"],GPIO.HIGH)
    max_playlist = int(key) 
    print(key, value)

#Set the initial state of important variables
runningprocess = None
currentplindex = RetrieveLastPlaylistIndex() #0
currentsongindex = 0
israndom = True #todo In the future, might tie this to hardware switch

SetActivePlaylistLED(-1) #All LED's off
requestupdatecheck = False



###################################
###### BUTTON PRESS CALLBACK ######
###################################
def buttonPressed(channel):
    global runningprocess
    global currentplindex
    global currentsongindex
    global requestupdatecheck

    #This next if helps with "false positives" --
    #Without this code, I can touch the wire with my finger and generate a button press
    #When you're first testing etc you could comment these next 3 lines out:
    if GPIO.input(controldata["playlistButtonGPIONumber"]) == 1:
        print ("False button press / ignore")
        return
    
    #If anything is already playing, kill it
    if runningprocess != None:
        os.system('killall omxplayer.bin')
        runningprocess = None
        
    #Next playlist was requested, advance current, set LED, reset counter
    currentplindex = currentplindex+1
    if currentplindex > max_playlist:
        currentplindex = 0
        requestupdatecheck = True #Check for updates by cycling all playlists
    SetActivePlaylistLED(currentplindex)
    currentsongindex=0
    print("New playlist selected")
    SaveLastPlaylistIndex(currentplindex)


###############################
##### MORE INITIALIZATION #####
###############################

#Attach callback function above to button press
GPIO.add_event_detect(controldata["playlistButtonGPIONumber"], GPIO.FALLING, callback=buttonPressed, bouncetime=1500)

#Light up the LED for current playlist
SetActivePlaylistLED(currentplindex)

#####################
##### MAIN LOOP #####
#####################

while True:
    time.sleep(0.9)
    
    ### If update check requested, look for updated playlists on USB drive
    if requestupdatecheck:
        requestupdatecheck = False
        CheckForUpgrade()
    
    ### If Sunday afterboon, reboot - weekly
    if datetime.datetime.today().weekday() == 6:
        checktimereboot = datetime.datetime.now().strftime("%H:%M:%S")
        if checktimereboot == "16:10:00":
                os.system("sudo reboot")
    
    ### If process is running (song playing) do nothing, else queue up next song
    if runningprocess != None:
        if runningprocess.poll() == None:
            print("Running - song playing. " + str(datetime.datetime.now()))
        else:
            print("Song finished playing.")
            runningprocess = None

    else:
        print("No Music is playing - queueing next song.")
        filepath = controldata["playlists"][currentplindex]["filespath"]
        arrayoffiles = os.listdir(filepath)
        if len(arrayoffiles) > 0:
            if israndom:
                nextfile = random.choice(arrayoffiles)
            else:
                nextfile = arrayoffiles[currentsongindex]
                currentsongindex = currentsongindex + 1
                if currentsongindex > (len(arrayoffiles) - 1):
                    currentsongindex = 0
            fullfile = filepath + nextfile
            print("Playing: " + fullfile)
            runningprocess = Popen(['omxplayer',"-o",controldata["output"], "--no-keys","--no-osd",fullfile])
  
       
    
