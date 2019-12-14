BackgroundPlayer.py
-------------------

This is an "offline music player" project for the Raspberry Pi.

More information on this project: https://youtu.be/MuI2SkKT7K8

Disclaimer:
* This code comes with no guarantees or warranties. I accept no responsibility for any use.
* Use at your own risk, for personal curiosity only. I assume no liability for anything. 

Helpful Links:

1. The article that "inspired" the project: 	https://www.instructables.com/id/Raspberry-Pi-Music-Player-1/
2. Auto-starting the script at boot time:	https://www.wikihow.com/Execute-a-Script-at-Startup-on-the-Raspberry-Pi
3. Manual for OMX Player:			https://www.raspberrypi.org/documentation/raspbian/applications/omxplayer.md
4. Making the Pi reboot periodically:		http://www.vk3erw.com/index.php/16-software/58-raspberry-pi-how-to-periodic-reboot-via-cron
5. Web site used to generate the voice prompts: http://www.fromtexttospeech.com/

Note: 

* The initial code was easy, but required additional tweaking to make it run forever.
* To fix this, I added additional parameters to the omxplayer command, and upgraded the Pi's firmware. 