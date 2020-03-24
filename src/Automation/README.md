# Automation with an scheduled task (Windows) or a service (Linux)
If you are planning to use the software, but you don't want to always start it
manually, then you can use scheduled tasks on Windows or a service on Linux.

## Scheduled Task (Windows)

You will find four files here:

- **Start_FootController_Windows_Normal_Startup.xml**: this will schedule a task
  with the following parameters:
  - Run whether the user is logged on or not
  - Run with highest privileges
  - Trigger at system startup
  - Action > start a program:
    - Program: "C:\Program Files\Python37\python.exe"
    - Arguments: "C:\Users\my_user\Documents\JMMidiBassPedalController\src\FootController.py" --config="conf\bass-pedal-config.xml"
    - Start in: C:\Users\my_user\Documents\JMMidiBassPedalController\src
  - Start the task only if the computer is on AC power -> this is disabled
- **Start_FootController_Windows_Verbose_Startup.xml**: this is essentially the
  same as the previous task, but the "--verbose" switch is enabled, so, debug
  messages will be written to the log file.
- **Start_FootController_Windows_Normal_Logon.xml**: this will schedule a task
  with the following parameters:
  - Run whether the user is logged on or not
  - Run with highest privileges
  - Trigger at system logon of any user and delay for 30 seconds
  - Action > start a program:
    - Program: "C:\Program Files\Python37\python.exe"
    - Arguments: "C:\Users\my_user\Documents\JMMidiBassPedalController\src\FootController.py" --config="conf\bass-pedal-config.xml"
    - Start in: C:\Users\my_user\Documents\JMMidiBassPedalController\src
  - Start the task only if the computer is on AC power -> this is disabled
- **Start_FootController_Windows_Verbose_Logon.xml**: this is essentially the
  same as the previous task, but the "--verbose" switch is enabled, so, debug
  messages will be written to the log file.
  
You will need to edit those files and change the python and your script paths.
After having done this, you need to open the Windows Task Scheduler as
administrator (Do not do this as a normal user; otherwise it won't work). Then
import the desired XML file. After you confirm the changes, Windows will ask you
for a user name; it is important that you use a user with admin rights.

Please also note that the tasks with the startup trigger will only work with
physical MIDI ports, ie: USB to MIDI cable and it must be connected before
starting the system. Virtual ports created with loopMIDI because those ports are
only created after a user logins in the system.

For the logon tasks, if working with physical ports, ie: USB to MIDI cable, then
you can drop the delay. For testing purposes, ie: using loopMIDI virtual ports,
you need a delay from at least 30 seconds because those ports are created some
seconds after the user logons.