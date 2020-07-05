# Automatic start during system boot / logon
**JMMidiBassPedalController v1.4**\
**File: src/Automation/README.md**\
**By:   Josef Meile <jmeile@hotmail.com> @ 05.07.2020**

If you are planning to use the software, but you don't want to always start it
manually, then you can use scheduled tasks on Windows, a service on Linux, or
a Launch Daemon/Agent on MACOS. You will find the needed files on the Automation
folder.

# Table of Contents

- [Windows](#windows)
  - [Starting the software whenever a user logons
    ](#starting-the-software-whenever-a-user-logons)
  - [Starting the software after Windows has started
    ](#starting-the-software-after-windows-has-started)
- [MACOS](#macos)
  - [Starting the software whenever a user logons
    ](#starting-the-software-whenever-a-user-logons)
  - [Starting the software after MACOS has started
    ](#starting-the-software-after-macos-has-started)
- [Linux](#linux)
  - [Starting the software after Linux has started
    ](#starting-the-software-after-linux-has-started)


# Windows

Under Windows, some xml Tasks, which can be imported on the Windows Scheduler,
are available. Here you have two alternatives: either run the task when a user
logons or during system startup. Personally, I prefer the last option, since you
won't have to login to the system and it will be ready as soon as Windows starts.

In order to import an xml Task do the following:

- Type: "Task Scheduler" on the search field from Windows, then right click on:
  "Task Scheduler", and choose: "Run as Administrator".

- Select "Task Scheduler Library", right click on it, and select: "Import Task".

- Choose one of the files mentioned above. 

## Starting the software whenever a user logons

Here you will find these two files:

- [Start_FootController_Windows_Normal_Logon.xml
  ](Windows/Start_FootController_Windows_Normal_Logon.xml): this will schedule a
  task with the following parameters:
  - Run whether the user is logged on or not
  - Run with highest privileges
  - Trigger at system logon of any user and delay for 30 seconds
  - Action > start a program:
    - Program:
      ```
      "C:\Program Files\Python37\python.exe"
      ```
    - Arguments:
      ```
      "C:\Users\my_user\Documents\JMMidiBassPedalController\src\FootController.py" --config="conf\bass-pedal-config.xml"
      ```
    - Start in:
      ```
      C:\Users\my_user\Documents\JMMidiBassPedalController\src
      ```
  - Start the task only if the computer is on AC power -> this is disabled

- [Start_FootController_Windows_Verbose_Logon.xml
  ](Windows/Start_FootController_Windows_Verbose_Logon.xml): this is essentially
  the same as the previous task, but the "--verbose" switch is enabled, so, debug
  messages will be written to the log file.

After importing the files, you will need to edit the triggered action under
the "Action" tab, then change the python path (*Program/script* section), the
path to FootController script (*Add arguments* section), and the working
directory (*Start in* section). Please note the following:

- Paths on the "Program/script" and "Add arguments" section must be enclosed
  by double qoutes.

- The "Start in" section can be only a path and it can't be enclosed by double
  qoutes; otherwise, the task won't run.

Once you have confirmed the changes, Windows will ask you for a user name;  it
is important that you use a user with admin rights.

If working with physical ports, ie: USB to MIDI cable, then you can drop the
start delay. For testing purposes, ie: using loopMIDI virtual ports, you need
a delay from at least 30 seconds because those ports are created some seconds
after the user logons.

Another parameter that you could change is the user that will trigger the script,
ie: if you want to run the task only when a specific user logons, then edit
the "At log on" trigger and change: "Any user" to "Specific user", then select
the user you want to use.

## Starting the software after Windows has started

Here you will find these two files:

- [Start_FootController_Windows_Normal_Startup.xml
  ](Windows/Start_FootController_Windows_Normal_Startup.xml): this will schedule
  a task with the following parameters:
  - Run whether the user is logged on or not
  - Run with highest privileges
  - Trigger at system startup
  - Action > start a program:
    - Program:
      ```
      "C:\Program Files\Python37\python.exe"
      ```
    - Arguments:
      ```
      "C:\Users\my_user\Documents\JMMidiBassPedalController\src\FootController.py" --config="conf\bass-pedal-config.xml"
      ```
    - Start in:
      ```
      C:\Users\my_user\Documents\JMMidiBassPedalController\src
      ```
  - Start the task only if the computer is on AC power -> this is disabled
- [Start_FootController_Windows_Verbose_Startup.xml
  ](Windows/Start_FootController_Windows_Verbose_Startup.xml): this is
  essentially the same as the previous task, but the "--verbose" switch is
  enabled, so, debug messages will be written to the log file.

After importing the files, you will need to edit the triggered action under
the "Action" tab, then change the python path (*Program/script* section), the
path to FootController script (*Add arguments* section), and the working
directory (*Start in* section). Please note the following:

- Paths on the "Program/script" and "Add arguments" section must be enclosed
  by double qoutes.

- The "Start in" section can be only a path and it can't be enclosed by double
  qoutes; otherwise, the task won't run.

Once you have confirmed the changes, Windows will ask you for a user name;  it
is important that you use a user with admin rights.

Please also note that the tasks with the startup trigger will only work with
physical MIDI ports, ie: USB to MIDI cable and it must be connected before
starting the system. Virtual ports created with loopMIDI because those ports are
only created after a user logins in the system.

# MACOS

Under MACOS you have two alternatives for automatically starting tasks: either
run the task when a user logons (Login Item) or during system startup (Launch
Daemon or Agent). Personally, I prefer the last option, since you won't have to
login to the system and it will be ready as soon as MACOS starts. Please note
that when running Daemons as root, the MIDI configuration for virtual ports isn't
available; only physical port, ie: an USB to MIDI cable, are visible.

## Starting the software whenever a user logons

Here you will find this folder:

- [Start_FootController_MACOS_Logon.app
  ](MACOS/Start_FootController_MACOS_Logon.app): this will schedule a task as
  soon as a user logons. 

In order to use this task, do the following:

- Open a Finder Window.

- Go to "Applications", then open "Automator".

- Locate the File and open it.

- Change the following variables:
  - WORKING_DIR: Directory where the FootController.py script is located
  - SCRIPT_OPTIONS: Script command line options. Set this to "--verbose"
    to enable debug messages; otherwise, leave it as it is.
  - PYTHON_BIN: Path to the python3 binary
  - CONFIG_FILE: Configuration file to use

- You may test if it is working by pressing the "Run" button. Then try to send
  messages with the ManualTester.py script.

- Go to "Apple menu > System Preferences", then choose: "Users & Groups".

- Select the user to run the task (usually: "Current User"), then click the
  "Login Items" tab.

- Add the .app file by clicking on the '+' (plus) sign.

Now the task will be executed as soon as that user logons.

Please take in note that "Reboot" and "Shutdown" commands won't work here because
those commands need root privileges and the "Login Items" will be run with normal
user rights.

## Starting the software after MACOS has started

Note: I didn't manage to make this work. It seems that MACOS will only start the
MIDI devices as soon as a user logins. So, no way of doing it on an unattended
installation. I guess you will have to run a logon script and setup your user
to automatically login.

To install this as a Launch Agent or Daemon do the following:

- Copy the file: [technosoft.solutions.run_foot_controller.plist
  ](MACOS/technosoft.solutions.run_foot_controller.plist) to either:
  - /Library/LaunchAgents, /Library/LaunchDaemons -> The task will be run for all
    users.
  - or ~/Library/LaunchAgents -> The task will be run only for the current user. 

- Then edit the .plist file and change this settings:
  - UserName: Use this only if seting up a LaunchDaemon. This is the user that
    will run the Daemon. If not setup, root will be the default. If you copy this
    file to either /Library/LaunchAgents or ~/Library/LaunchAgents, then it will
    run as root or the current user respectively.
  - ProgramArguments: Here you need to setup the right path to the shell script:
    Start_FootController_MACOS_Startup.sh. It must be an absolute path.
  - WorkingDirectory: Path containing the shell script. It is used to set some
    relative paths to the log files.
  - StandardOutPath: This is the path were the status messages will be saved. It
    can be either relative to WorkingDirectory or an absolute path.
  - StandardErrorPath: Path for the error log. It can be either relative to
    WorkingDirectory or an absolute path.

- Open the [Start_FootController_MACOS_Startup.sh
  ](MACOS/Start_FootController_MACOS_Startup.sh) script and edit this variables:
  - WORKING_DIR: Directory where the FootController.py script is located
  - SCRIPT_OPTIONS: Script command line options. Set this to "--verbose"
    to enable debug messages; otherwise, leave it as it is.
  - PYTHON_BIN: Path to the python3 binary
  - CONFIG_FILE: Configuration file to use

- Now go on a Terminal, go to the directory were you copied the .plist file:
  ```
  cd ~/Library/LauchAgents
  ```

- Register and load the daemon:
  ```
  launchctl load -w technosoft.solutions.run_foot_controller.plist
  ```

- The daemon should be running now. To verify it run:
  launchctl list | grep technosoft

  If everything goes well, then you should see something similar to this:
  3134	0	technosoft.solutions.run_foot_controller

  3134 is the id of the running process, which may be different in your case. On
  the other hand, if you get a dash on the begin, ie:

  -	78	technosoft.solutions.run_foot_controller

  it means that the daemon didn't start because of a configuration error, ie:
  - The user running the daemon doesn't have excecution permissions of the
    Start_FootController_MACOS_Startup.sh script. To correct this run this
    command:
    ```
    sudo chmod +x Start_FootController_MACOS_Startup.sh
    ```
  - The user running the daemon doesn't have write permissions on the log files.
    To correct this, run this command:
    ```
    sudo chmod +w status.log error.log
    ```
  - The user running the daemon doesn't have reading permissions on the folders
    where the FootController.py script is located. To correct this, run this
    command:
    ```
    sudo chmod -R +r /path/to/FootController
    ```
  - The paths in the "ProgramArguments" and the "WorkingDirectory" are wrong or
    not accessible.

  You can also debug daemons with this utility (not for free, but on the trial
  mode will detect errors):
  - [LaunchControl / The launchd GUI](https://www.soma-zone.com/LaunchControl)

  The file: /var/log/system.log may also have some clues.

  If you want to remove the Daemon, then run:
  ```
  launchctl unload -w technosoft.solutions.run_foot_controller.plist
  ```

  You can also stop the daemon like this:
  ```
  launchctl stop technosoft.solutions.run_foot_controller
  ```

  Or start it:
  ```
  launchctl start technosoft.solutions.run_foot_controller
  ```

# Linux
The scripts contained here only work for debian and its based distros, ie:
Ubuntu and Raspbian. It depends on systemd, so, your Linux must have it.

## Starting the software after Linux has started
In order to install this, first modify this file:
[Start_FootController_Linux_Startup.sh
](Linux/Start_FootController_Linux_Startup.sh)

Modify this variables:
* WORKING_DIR: Directory where this file is located.
* SCRIPT_DIR: Directory where the FootController.py script is located
* SCRIPT_OPTIONS: If you want that the script runs in debug mode, set it to:
  ```
  SCRIPT_OPTIONS="--verbose"
  ```
* PYTHON_BIN: Path to the python3 binary, usually: /usr/bin/python3
* CONFIG_FILE: Configuration file to use

Then modify the file:
- WorkingDirectory: Location of the Start_Foot_Controller_Linux_Startup.sh file.
- ExecStart: Command to start the service. You only have to modify the path to
  the script. The final part: "Start_FootController_Linux_Startup.sh start"
  remains the same.
- ExecStop: Command to stop the service. You only have to modify the path to the
  script. The final part: "Start_FootController_Linux_Startup.sh stop" remains
  the same.

Once this is done, you can install the script:
```
sudo ./Start_FootController_Linux_Startup.sh install
```

The script will be started automatically during boot.

Here some usefull commands:
- To manually starting it, run:
  ```
  sudo service JMMidiBassPedalController start
  ```
- To stop it run:
  ```
  sudo service JMMidiBassPedalController stop
  ```
- To query its status, run:
  ```
  sudo service JMMidiBassPedalController status
  ```
- To remove the service, run:
  ```
  sudo ./Start_FootController_Linux_Startup.sh remove
  ```
