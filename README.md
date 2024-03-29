# JMMidiBassPedalController v3.0
**File: README.md**\
**By:   Josef Meile <jmeile@hotmail.com> @ 28.10.2020**

This software translates **NOTE ON/OFF** messages comming from a
**foot controller** to **chords**. It allows you to save several configurations
in **banks**, which can be switched through **CONTROL CHANGE** messages.

# Table of Contents

- [Features](#features)
- [Definitions](#definitions)
- [Requirements](#requirements)
- [Installation](#installation)
- [Hardware connections](#hardware-connections)
  - [Connecting a foot controller to a laptop or a Rasberry Pi
    ](#connecting-a-foot-controller-to-a-laptop-or-a-rasberry-pi)
  - [Connecting a foot and a bass pedal controllers with a laptop or a Raspberry
    Pi](#connecting-a-foot-and-a-bass-pedal-controllers-with-a-laptop-or-a-raspberry-pi)
- [Setting up the hardware](#setting-up-the-hardware)
  - [Setting up a Behringer FCB1010 (optional)
    ](#setting-up-a-behringer-fcb1010-optional)
    - [Entering "GLOBAL CONFIGURATION" mode](#entering-global-configuration-mode)
      - [Enabling the "MERGE" function](#enabling-the-merge-function)
      - [Set the MIDI channel for the "CNT" function
        ](#set-the-midi-channel-for-the-cnt-function)
      - [Set the MIDI channel for the "NOTE" function
        ](#set-the-midi-channel-for-the-note-function)
    - [Entering "PRESET programming" mode](#entering-preset-programming-mode)
      - [Set "NOTE" messages](#set-note-messages)
      - [Set "CNT" messages](#set-cnt-messages)
- [Setting up the software](#setting-up-the-software)
- [Running the software](#running-the-software)
- [Automatic start during system boot](#automatic-start-during-system-boot)
- [Troubleshooting](#troubleshooting)
  - [Using two "Virtual MIDI Piano Keyboars"
    ](#using-two-virtual-midi-piano-keyboars)
  - [Using the ManualTester script together with "Virtual MIDI Piano Keyboard"
    ](#using-the-manualtester-script-together-with-virtual-midi-piano-keyboard)
    - [Mapping MIDI notes to computer keyboard keys on Virtual MIDI Piano Keyboard
	  ](#mapping-midi-notes-to-computer-keyboard-keys-on-virtual-midi-piano-keyboard)
  - [Use a software for intercepting MIDI messages
    ](#use-a-software-for-intercepting-midi-messages)
  - [Using a sequencer software](#using-a-sequencer-software)
  - [Activating the verbose mode](#activating-the-verbose-mode)
- [License](#license)

# Features

- **XML configuration file**.
- Fully customizable parameters:
  - **MIDI IN and OUT** ports and channels. You can use as many **MIDI OUT**
    ports as you want, ie: sending one chord to different voices.
  - **MIDI Echo** function.
  - **Start**, **Stop**, and **Panic** commands.
  - Define multiple **banks** to store different pedal layouts. You can also
    use descriptive names to identify them.
  - Each pedal can send this messages:
    - **Bass** and **Chord** notes, which can be expressed with symbols, ie: C#
      or by their MIDI NOTE values, ie: 84 for C5.
    - **BANK SELECT** messages to set change select different banks and also an
      option to list them.
    - **Panic messages**
    - **MIDI** or **SysEx** messages. You can also define when to trigger them:
      either during a **NOTE ON** or a **NOTE OFF** message.
    - **Reload** configuration during excecution.
    - **Quit** the controller software.
    - **Reboot** or **shutdown** the device running the controller software.
      Currently supported operating systems: Windows, MACOS, and Linux.
  - Setup custom **bass note** and **chord velocities** either absolute values
    or relative to the current pedal controller speed. Here you can use either
    symbols ie: fff or its MIDI representation: 114.
  - Use different **octaves** for each pedal.
  - Setup **semitone transpositions**
  - Either setup the pedals to be either polyphonic or monophonic.
- Its flexibility allows it to be used with several **foot controllers** at once.

# Definitions
From time to time, I use the following terms on my software:

- **Bank**: in my software I reffer this to be a way of grouping different
  settings. So, you can have for example a bank with the C Major scale chords
  and another bank with the C Minor scale chords. The nice thing of these groups
  is that you can easily switch them while playing your keyboard. This is
  actually an optional feature that you may use or not.

- **BANK SELECT message**: message used to change the active bank to another one,
  for example: you can navigate to the next, previous, or last banks, or you can
  also jump to a specific bank.

- **Bass note:** for me, a bass note is the note that comes when you hit a bass 
  pedal; it is usually the root note of a chord, but since you can setup your
  pedals as you want, this may not be always the case.

- **Bass pedal controller:** to be honest, I don't know if this term is correct;
  I think that **pedalboard** may be better, but I want to emphasize that it is
  a foot controller that looks like those bass pedals from an old organ, for
  example, the **studiologic MP-117**:

  [![studiologic MP-117 pedalboard](assets/Studiologic_MP-117_small.jpg)
  ](assets/Studiologic_MP-117.jpg)\
  Please note that it is not necessary that you use a bass pedal controller, you
  can also use a foot controller like the **Behringer FCB1010**:

  [![Behringer FCB1010 foot controller
  ](assets/Behringer_FCB1010_small.jpg)](assets/Behringer_FCB1010.jpg)\
  However the feeling won't be the same as when you use a real bass pedal; for
  example the switches may be harder and so difficult to push. Another advantage
  of the bass pedal controller is that it may also include the force (velocity)
  that you use to push an specific pedal. Finally, you can also use both
  together, ie: the bass pedal controller for sending your chords and the foot
  controller to switch between banks and setup other things on your keyboard.

- **CONTROL CHANGE message**: this message allows you to modify several settings
  on a keyboard or a controller, ie: switch between banks, change modulation and
  pitch wheel levels, modify the main volume, set several accoustic effects,
  etc.. In the software, I will use this mainly to switch between banks.

- **Foot controller:** it is basically a MIDI controller that you can manipulate
  with your feet. It allows you to do some common MIDI tasks, ie: send
  **NOTE ON**, **NOTE OFF**, **PROGRAM** and **CONTROLLER  CHANGE** messages.
  There are some that even allow you to send **SYSTEM EXCLUSIVE** messages.

- **MIDI** and related terms: this would cost me a lot of time to write down
  everything here, so, I will just let you some links:
  - [Summary of MIDI Messages from the MIDI association.
    ](https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message )
  - [MIDI definition from Wikipedia](https://en.wikipedia.org/wiki/MIDI)
  - [MIDI tutorial from Dominique Vandenneucker.
    ](http://www.music-software-development.com/midi-tutorial.html)
  - [How MIDI Works, YouTube playlist from Andrew Kilpatrick.
    ](https://www.youtube.com/watch?v=5IQvu8zlmJk&list=PLgWv1tajHyBsAo5OBLiQlY0hLC4ZagyJB)
 
- **MIDI Echo function:** this is the ability of the software to fordward other
  not recognized messages to the connected devices. ie: let's say that you want
  to send a **System Exclusive** message; the software won't process it, but it
  will send it through the **MIDI OUT** port.
 
- **Log file:** file where the debug information is going to be stored. It is
  usally named *debug.log* and it is located in the same folder of the main
  program. It is useful to help you detect possible issues that you may have with
  your equimpment.
 
- **MIDI port:** it is the physical connection where you connect your MIDI cables
  on the keyboard and your foot controllers. Please note that you can also have
  virtual ports, which are used inside the software to simulate a real port. You
  can have **IN** (input) and **OUT** (output) ports to receive and send messages
  comming from or to other connected devices.

- **MIDI to USB cable**: since modern computers don't have **MIDI ports**, this
  cable allows you to have two ports: **MIDI IN and OUT** connected through an
  USB port. Right now, I use M-Audio Uno USB cable:

  [![M-Audio Uno USB cable](assets/M-Audio_Uno_USB_cable_small.jpg)
  ](assets/M-Audio_Uno_USB_cable.jpg)

- **NOTE ON/OFF message:** messages that results when hitting or releasing a note
  on a keyboard or a foot controller respectively. **NOTE ON** messages are
  commonly associated with at note velocity. You may also have this on a **NOTE
  OFF** message, but it is uncommon.

- **Note Transposition:** usually you can move notes by semitones, tones, and
  octaves, ie: if you have a C3 (middle C), you can transpose it by a semitone,
  then you get: C#3 or by an octave: C4.

- **Note velocity**: it is the pressure you apply to hit a key on your keyboard
  or bass pedal controller. It is commonly associated to the volume (see MIDI for
  more details).

- **Raspberry Pi**: think of it as a mini computer (micro controller to be
  exact), for example, the Raspberry Pi 4:

  [![Raspberry Pi 4](assets/Raspberry_pi_4_small.jpg)
  ](assets/Raspberry_pi_4.jpg)\
  They are really small and allow you to excecute some tasks that a computer also
  can do, but with the advantage that they are really small and usually after you
  setup them, then you don't need a keyboard or a screen to start it.

- **Sequencer software:** since the MIDI message are send sequentially to your
  keyboard, sequencer is a software that is used to catch those messages or send
  them. It counts with nice graphical tools, ie: message list (human readable
  list) and also a staff view to see the note messages.

- **System Exclusive message or SysEx:** this is a way of sending a manufacturer
  specific message to your keyboard, ie: activate a voice on the keyboard's
  panel.

- **XML file**: this is just a file where you can save the configuration of your
  bass foot controller.

# Requirements

Before installing the requirements, please make sure that you have admin rights.
Under Linux/MACOS use:

```
sudo <install_command>
```

Under Windows run a "**cmd**" (Command propt) as Administrator.

- For Microsoft Windows from branch 3.0, you need the  [Microsoft C++ Build 
  Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools). Once
  you execute the installer, you only need to select: **"C++ build tools"**;
  here you can leave the standard options. No more is needed. Be aware that
  this will require 2 GB of free space.

- [Python 3.9](https://www.python.org/downloads/release/python-390). After you
  have installed it, you need to do update some built-in packages:
  ```
  pip3 install --upgrade setuptools
  pip3 install --upgrade pip
  ```

- [Python rtmidi module](https://pypi.org/project/python-rtmidi)\
  This can be installed as follows:
  ```
  pip3 install python-rtmidi
  ```
  If you have an older version, then you can upgrade it with:
  ```
  pip3 install --upgrade python-rtmidi
  ```
 
- [Python Autologging module](https://pypi.org/project/Autologging)\
  This can be installed as follows:
  ```
  pip3 install Autologging
  ```
  If you have an older version, then you can upgrade it with:
  ```
  pip3 install --upgrade Autologging
  ```
 
- [Python xmlschema module](https://pypi.org/project/xmlschema)\
  This can be installed as follows:
  ```
  pip3 install xmlschema
  ```
  If you have an older version, then you can upgrade it with:
  ```
  pip3 install --upgrade xmlschema
  ```
 
- Under Windows, you may need to upgrade setuptools if you get the error:
  ```
  error: command 'cl.exe' failed: No such file or directory
  ```
  To do so, run this command:
  ```
  pip3 install --upgrade setuptools
  ```

- Alternativelly to all **pip3** commands, you can also use the 
  **requirements.txt** file as follows:
  ```
  pip3 install -r requirements.txt
  ```
  All the python dependencies will be installed automatically. Since it is an
  easy way of doing it, you may not get the latest versions.
 
- MIDI USB interface, for example the
  [M-Audio Uno USB cable](https://www.m-audio.com/products/view/uno). Another
  MIDI Audio interface or cable may also work. I tested this with the M-Audio
  cable.
 
- A foot controller capable of sending **NOTE ON/OFF messages**, ie: a
  **Studiologic MP-117**, which looks like more as organ bass pedals, or a
  **Behringer FCB1010**, which allows you to do more things, but it doesn't give
  you the same feeling as the organ bass pedals, or both.

- And off course you need a keyboard with the old **MIDI ports**. USB MIDI may
  also work, but you will have to use two USB ports on your laptop or Raspberry
  Pi.

# Installation
The easiest way of installing the software is getting it from
[here](https://github.com/jmeile/JMMidiBassPedalController/archive/3.0.zip) then
decompress the zip file and put it contents wherever you want.

Alternatively, you can also clone the git repository:
```
git clone https://github.com/jmeile/JMMidiBassPedalController.git -b 3.0
```

# Hardware connections
Before running the software, it is important that you make the right connections
between your devices and your computer, which can be also a **Raspberry Pi**.

## Connecting a foot controller to a laptop or a Rasberry Pi
This setup is ideal if only have a foot controller, ie: a **Studiologic MP-117**
(bass pedal controller) or a **Behringer FCB1010** (foot controller). Do the
following connections:

<!-- Text Version
+----------+                       +---------+
|Foot      +---+  TO MIDI OUT  +---+Laptop   |
|Controller|OUT+◄------+-------+USB|Raspberry|
|          +---+       |       +---+         |
+----------+           |           +---------+
                       |TO
                       |MIDI IN
                       |
                       |           +--------+
                       |       +---+        |
                       +------►+IN |Keyboard|
                               +---+        |
                                   +--------+
-->
[![Connecting foot controller only
](assets/connecting_foot_controller_only_small.jpg)
](assets/connecting_foot_controller_only.jpg)

**Explanation:**
- Connect the USB-TO-MIDI cable to the USB-Port from your Laptop or the Raspberry
  Pi.
- Connect the MIDI end labeled with "TO MIDI OUT" to the MIDI OUT port from your
  foot controller.
- Connect the MIDI end labeled with "TO MIDI IN" to the MIDI IN port from your
  keyboard.

## Connecting a foot and a bass pedal controllers with a laptop or a Raspberry Pi
If you own a foot controller (ie: a **FCB1010**) and a bass pedal controller (ie:
a **Studiologic MP-117**), then you can connect them as follows:

<!-- Text Version
+----------+              +----------+                       +---------+
|Pedal     +---+      +---+Foot      +---+  TO MIDI OUT  +---+Laptop   |
|Controller|OUT+-----►+IN |Controller|OUT+◄------+-------+USB|Raspberry|
|          +---+      +---+          +---+       |       +---+         |
+----------+              +----------+           |           +---------+
                                                 |
                                                 |TO
                                                 |MIDI IN
                                                 |           +--------+
                                                 |       +---+        |
                                                 +------►+IN |Keyboard|
                                                         +---+        |
                                                             +--------+
-->
[![Connecting bass and foot controllers only
](assets/connecting_bass_and_foot_controllers_small.jpg)
](assets/connecting_bass_and_foot_controllers.jpg)

**Explanation:**
- Connect the **USB-TO-MIDI cable** to the **USB-Port** from your laptop or the
  Raspberry Pi.
- Connect the MIDI end from the USB cable labeled with **TO MIDI OUT** to the
  **MIDI OUT** port from your foot controller.
- Connect the MIDI end from the USB cable labeled with **TO MIDI IN** to the
  **MIDI IN** port from your keyboard.
- Connect the **MIDI OUT** port from your pedal controller to the **MIDI IN**
  port of your foot controller.

**Remarks:**
- The only thing that you need to be aware of if you are using a **Behringer
  FCB1010** is that you will have to enable the **Merge** function under the
  **GLOBAL CONFIGURATION**. This will fordward all messages comming from the
  **MIDI IN** to the **MIDI OUT** port. For more information about this process,
  see: [Setting up a Behringer FCB1010](#setting-up-a-behringer-fcb1010-optional)

# Setting up the hardware
In order to make this to work, you will have to do the following steps:

- Setup the **MIDI OUT channel** of your bass pedal controller to whatever you
  want to use. If you are using both: a bass pedal controller and a foot
  controller, then setup the same port on both devices. Since the **Studiologic
  MP-117** I have is an old version and settings will be resseted on power off,
  I will leave the default **MIDI channel**, which is channel 1.

- Setup the **NOTE ON** messages on your foot or bass pedal controller:
  - For a **FCB1010** or similar: you only need to setup **NOTE ON** messages and
    write down each MIDI note number that you are using.
  - For a **Studiologic MP-117**: the only thing you have to do is to setup the
    **Transpose** parameter; on my case, I will leave the default, which is 0
    (zero), no transposition. Here you need to see write down the **NOTE ON**
    messages are comming out from your bass pedal controller (specially if you
    changed the transpose parameter and used semitones).

- If using both a bass pedal and a foot controller, then you can also use your
  foot controller to switch between banks. For this, you need to send **CONTROL
  CHANGE** messages on controller 32 (see the comments on the *sample-config.xml*
  file). Additionally, if you want to send other MIDI messages, then you can do
  it as well, but be aware that **NOTE ON** messages should use either use a
  different channel or use notes that you are not listenning to. Also be careful
  with **CONTROL CHANGE** messages on control 32; if you need to send something
  to the keyboard, then make sure to use a different channel for this message.

- Setup your keyboard to do chord detection on a specific **MIDI channel**. If
  you have an old MIDI keyboard and you can't set this up, then you need to
  figure out, which channel your keyboard uses; usually old keyboards have one
  or two voices for the right hand, and one voice for the left hand. and they use
  consecutive **MIDI channels**, so, if you have one right voice and one left
  voice, then the used channels would be channel 1 and channel 2 respectively.

- If you want also want to play bass notes, then setup a **MIDI channel** on your
  keyboard for doing this. If you have an old keyboard, then you can select the
  channel from your right or left voices.

## Setting up a Behringer FCB1010 (optional)
If using this foot controller with or without another controller, then you may
need to setup some parameters, for example:
[MIDI Merge](#enabling-the-merge-function), MIDI channel for
[NOTE ON/OFF](#set-the-midi-channel-for-the-note-function) or
[CONTROL CHANGE](#set-the-midi-channel-for-the-cnt-function) messages, values for
[NOTE ON/OFF](#set-note-messages) or [CONTROL CHANGE](#set-cnt-messages), etc..
The first thing you have to go is to go to either
["GLOBAL CONFIGURATION"](#entering-global-configuration-mode) or
["PRESET programming"](#entering-preset-programming-mode) mode.

### Entering "GLOBAL CONFIGURATION" mode
Keep the DOWN switch pressed during power-up for about 2.5 seconds to enter
"GLOBAL CONFIGURATION" mode. Here the "DIRECT SELECT" LED in the display lights
up.

#### Enabling the "MERGE" function
This function is needed if you want to connect two controllers: a Behringer
FCB1010 and a bass pedal controller (ie: a Studiologic MP-117), see:\
[Connecting a foot and a bass pedal controllers with a laptop or a Raspberry Pi
](#connecting-a-foot-and-a-bass-pedal-controllers-with-a-laptop-or-a-raspberry-pi)\
This will just merge the messages from your FCB1010 with your bass pedal
controller, allowing them to use the same MIDI OUT port. In order to enable this
function do follow this steps:
- Go to the "GLOBAL CONFIGURATION" mode (click
  [here](#entering-global-configuration-mode) for more details.
- Use the "DOWN" or "UP" switches until you reach the "CONFIG" page.
- Press the Switch 8 until its LED is on. This will activate the MERGE function.
- You may want to setup other parameters before exiting this mode, ie: [set the
  MIDI channel for the "CNT" function
  ](#set-the-midi-channel-for-the-cnt-function) or [set the MIDI channel for
  "NOTE" function](#set-the-midi-channel-for-the-note-function).
- After you are done, press the "DOWN" switch for about 2.5 seconds to save
  changes.

#### Set the MIDI channel for the "CNT" function
If you are going to use the FCB1010 for sending "BANK SELECT" messages, then you
will have to set the right channel for the CNT (CONTROL CHANGE) function. Here
you can use two controllers CNT1 or CNT2; which one you choose is up to you. For
doing this, follow this steps:
- Go to the "GLOBAL CONFIGURATION" mode (click [here
  ](#entering-global-configuration-mode) for more details).
- Use the "DOWN" or "UP" switches until you reach the "SELECT MIDI FUNCTION"
  page. Its LED starts flashing.
- Then hit the switch 6. It will start flashing. If you want to use "CNT 2"
  instead, then hit the switch 7.
- Press the "UP/ENTER" switch to confirm that you want to change the MIDI channel
  for that function.
- Press the switches from 1 until 10 to change the channel value, which will
  appear on the display, ie: choose "1" for MIDI channel 1.
- Then press the "UP/ENTER" switch to go back to the "CONFIG" page and save the
  changes. To undo changes, hit the "DOWN/ESCAPE" switch.
- If you want, you can setup other parameters here, ie: [set the MIDI channel for
  the "NOTE" function](#set-the-midi-channel-for-the-note-function).
- After you are done, press the "DOWN" switch for about 2.5 seconds to save
  changes.

#### Set the MIDI channel for the "NOTE" function
If you are going to use the FCB1010 for sending "NOTE ON/OFF" messages, then you
will have to set the right channel for the NOTE function. For doing this, follow
this steps:
- Go to the "GLOBAL CONFIGURATION" mode (click [here
  ](#entering-global-configuration-mode) for more details).
- Use the "DOWN" or "UP" switches until you reach the "SELECT MIDI FUNCTION"
  page. Its LED starts flashing.
- Then hit the switch 10. It will start flashing.
- Press the "UP/ENTER" switch to confirm that you want to change the MIDI channel
  for that function.
- Press the switches from 1 until 10 to change the channel value, which will
  appear on the display, ie: choose "1" for MIDI channel 1.
- Then press the "UP/ENTER" switch to go back to the "CONFIG" page and save the
  changes. To undo changes, hit the "DOWN/ESCAPE" switch.
- If you want, you can setup other parameters here, ie: [set the MIDI channel for
  the "CNT" function](#set-the-midi-channel-for-the-cnt-function).
- After you are done, press the "DOWN" switch for about 2.5 seconds to save
  changes.


### Entering "PRESET programming" mode
In order to change the messages sent by each switch, you will have to follow this
steps:
- Turn on the FCB1010
- Hit the switch you want to change.
- Press the "DOWN" switch for about 2.5 seconds until the SWITCH 1/SWITCH 2 LED
  starts flashing.
- Press the "UP/ENTER" switch to enter the programming mode.
- Here you may set ["NOTE"](#set-note-messages) or ["CNT"](#set-cnt-messages)
  messages.
- Finally save changes, by pressing the "DOWN" swich for a few seconds.

#### Set "NOTE" messages
For sending bass notes and chords with the FCB1010, you will have to set "NOTE"
messages. For doing this, follow this steps:
- Go to the "PRESET programming" mode (click [here
  ](#entering-preset-programming-mode)
  for more details).
- Press the switch 10 for a few seconds until its LED is on.
- Hit it again. It will start flashing.
- Confirm the selection by pressing the "UP/ENTER" switch.
- Enter the note you want to send by pressing the switchs from 1 until 10.
- Confirm the entered value by pressing the "UP/ENTER" switch or cancel it by
  pressing "DOWN/ESCAPE".
- At this point, you may select a different function and setup its value, ie:
  [Set "CNT" messages](#set-cnt-messages).
- To save changes, press the "DOWN" swich for a few seconds.

#### Set "CNT" messages
For sending BANK SELECT messages with the FCB1010, you will have to either set
"CNT1" or "CNT2" messages; this choice is up to you. In order to setup this
messages, follow this steps:
- Go to the "PRESET programming" mode (click [here
  ](#entering-preset-programming-mode) for more details).
- Press the switch 6 (CNT1) or 7 (CNT2) for a few seconds until its LED is on.
- Hit it again. It will start flashing.
- Confirm the selection by pressing the "UP/ENTER" switch.
- Enter the controller you want to use for "BANK SELECT" messages (usually 32;
  depending on your xml configuration file) by pressing the switchs from 1 until
  10.
- Confirm the entered value by pressing the "UP/ENTER" switch or cancel it by
  pressing "DOWN/ESCAPE".
- Then enter the "BANK SELECT" message you want to sent:
  - Value from 0 until 120 for selecting banks from 1 until 121 respectively.
  - 121 will go to the previous bank.
  - 122 will go to the next bank.
  - 123 will go to the last bank.
  - 124 will cause the controller software to quit.
  - 125 will cause the controller software to restart and reread the xml
     configuration file.
  - 126 will cause the computer running the controller software to reboot.
  - 127 will cause the computer running the controller software to shutdown.
- Confirm the entered value by pressing the "UP/ENTER" switch or cancel it by
  pressing "DOWN/ESCAPE".
- At this point, you may select a different function and setup its value, ie:
  [Set "NOTE" messages](#set-note-messages).
- To save changes, press the "DOWN" swich for a few seconds.

# Setting up the software
- First figure out how the ports used by your **USB-TO-MIDI cable** are called.
  If your **MIDI** setup isn't going to change, then the port number should be
  also enough. In order to figure this out, run the software as follows:
  ``` 
  python3 FootController.py --list
  ``` 
  If using an **M-Audio USB UNO cable**, then the ports should be named similar
  to:
  - 1: USB Uno MIDI Interface
  
  where:
  - The first part is the port number and the last part the port name.

- After you have done this, open either the file: [sample-config.xml
  ](src/conf/sample-config.xml), an **XML configuration file** with lots of
  comments documenting what to do, or: [bass-pedal-config.xml
  ](src/conf/bass-pedal-config.xml), simple configuration with a **bass pedal
  controller** and save it as: *config.xml* or any other meaningful name.

- Open that file and modify it as you wish by filling your parameters, ie: **MIDI
  IN** port, **MIDI IN and OUT** channels, **NOTE ON** messages, etc..

# Running the software
Now you are ready to go. Go to the **src** folder, then type:
``` 
python3 FootController.py
``` 
Alternativelly, you can also setup another name for your configuration file, ie:
*my-config.xml*. Under Windows, run the sofware as follows:
``` 
python3 FootController.py --config "C:\file\path\my-config.xml"
``` 
or under Linux:
``` 
python3 FootController.py --config "/file/path/my-config.xml"
``` 
If your file is saved on the same folder as *FootController.py*, then this should
be enough:
``` 
python3 FootController.py --config "my-config.xml"
``` 

# Automatic start during system boot
If you are planning to use the software, but you don't want to always start it
manually, then you have several alternatives according to your operating system. 

You will find the needed files on the Automation folder. See the README.md file
located there or access an online version [here](src/Automation).

# Troubleshooting
If your equipment is not reacting as expected, then you can proceed as follows.

The most common problem would be that you get:

`'python3' is not recognized as an internal or external command, operable
program or batch file`

under Windows. This is because on Windows, there is no python3, so, you will
have to use either "python" or the full path to it, ie:
`"C:\Program Files\Python37\python.exe"`

Similarly, under Linux you may get:
`-bash: python3: command not found`

This is because python is not installed or your default python is already
python3. On the first case, install python3, on a debian like distro this can be
accomplished as follows:
`sudo apt install python3`

On the second case, then try to just run: `python`. Please make sure that it is
a 3.x version.

Before going in detail through the following options, if you are under Windows,
then you may need a software to create virtual midi ports:

  - [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html).

Under Linux and MACOS, you don't need any additional software. You can create
virtual ports by setting them on the configuration file, ie:
```
InPort="Virtual:MIDI IN" OutPort="Virtual:MIDI OUT"
```
where:
- The string after the keyword: "Virtual:" is the name you want to give to the
  port.
  
Under Linux, it is also possible to create virtual ports as follows:
```
sudo modprobe snd-virmidi snd_index=1
```
However, I didn't manage to make the MIDI connections working with those ports,
so, I used rtmidi virtual ports instead.

Alternativelly, on MACOS you can use the "Audio MIDI Setup" app:
- Open the Finder and go to: Applications > Utilities
- Click on: "Audio MIDI Setup.app"
- On the "Window" menu, choose: "Show MIDI Studio"
- Double click the "IAC Driver" icon
- Enable the: "Device is online" checkbox
- Under "Ports" you can add new ports by clicking on the '+' sign.
- If you want to rename the port name, then click on it and write the new name.
- You can change the base name of your MIDI ports by setting a new "Device Name".
- Finally click the "Apply" button.
- Note: the virtual ports created here won't be seen by a "sudo" shell. It will
  only work with normal user rigths.

For seeing the available MIDI ports, you can run:
```
python3 FootController.py --list
```

## Using two "Virtual MIDI Piano Keyboars"
- First create two virtual ports: MIDI In and MIDI Out
- Then start the controller software and start it as follows:
  ```
  python FootController.py --config=conf\virtual-midi-keyboards.xml --verbose
  ```
  That configuration configuration file will use the ports MIDI In and Out for
  receiving messages from the pedal controller and sending the respective bass
  and chord notes to the keyboard respectively.
- Next start two "Virtual MIDI Piano Keyboards"
- The first instance will emulate the pedal board, here setup the following
  parameters:
  - Channel: 1
  - Base Octave: 3
  - Transpose: 0
  - Velocity: set whatever you want; this will determine the volume of your
    notes.
  - Then Go to "Edit > MIDI Connections" and setup this:
    - Enable MIDI Input: disabled
    - MIDI OUT Driver: Windors MM
    - Output MIDI Connection: MIDI In
  - Go to: "Edit > Preferences" and do this:
    - Press: "Restore Defaults"
    - Set "Note highlight color" to: "MIDI Channels"
  - Optionally, if you want to see what happens when pressing two or more bass
    notes simultaneously, then you can load the keyboard map located in the
    assets folder. For achieving this, do the following:
    - Go to: "Edit > Keyboard Map"
    - Press "Open"
    - Go to the assets folder and choose: "Virtual_Keyboard_Map.xml"
    - Hit "OK"
    This will file will map the computer keyboard keys to the MIDI notes. You
    can find the keyboard map file equivalences [here
    ](#mapping-midi-notes-to-computer-keyboard-keys-on-virtual-midi-piano-keyboard)

- The second instance will emulate the bass and left hand voices, here setup
  the following parameters:
  - Go to: "Edit > MIDI Connections" and setup this:
    - Enable MIDI Input: enabled
	- MIDI Omni Mode: enabled -> this will allow the software to process
	  several MIDI channels at the same time
	- MIDI IN Driver: Windors MM
	- Input MIDI Connection: MIDI OUT
	- Enable MIDI Thru on MIDI Output: enabled
	- MIDI OUT Driver: Windors MM
	- Output MIDI Connection:
      - On Microsoft Windows: Microsoft GS Wavetable Synth
      - On other operating systems: choose the software MIDI syntheziser
        offered by your operating system
    - Go to: "Edit > Preferences" and do this:
      - Press: "Restore Defaults"
	  - Set "Note highlight color" to: "MIDI Channels"
  - On the main interface set this:
    - Base Octave: 3
    - Transpose: 0
    - Velocity: this value doesn't really matter; it will be set by the
      software
    - Change channel to 2 and under Bank set:
      - Bank: General MIDI
      - Program: Set the voice you want to hear for the bass pedals
      - Do the same for channel 3, which is where the chords will be played
- Finally play the first octave notes of the first Virtual MIDI Piano Keyboard
  instance. If every is ok, then you should see the bass pedals in color blue
  and the chord notes in color green at the second Virtual MIDI Piano Keyboard;
  you should also hear the voices you setup.

## Using the ManualTester script together with "Virtual MIDI Piano Keyboard"

- First create two virtual ports.
- Then setup the ports as follows:
  - In Port (xml file): Virtual Port 1; you may use another name, ie: MIDI In
  - Out Port (xml file): Virtual Port 2; you may use another name, ie: MIDI Out
- Finally run the script:
  ```
  python3 ManualTester.py
  ```
  and setup this parameters:
  - In Port: choose Virtual Port 2
  - Out Port: choose Virtual Port 1
  - MIDI IN channel and Bank select controller used by controller: use the ones
    defined on your config file
  - Default velocity for NOTE ON messages: here you can use whatever you want
  - Start sending NOTE ON/OFF, BANK SELECT, CONTROL CHANGE, raw MIDI, or SysEx
    messages.

For visualizing the notes, you can optionally use [Virtual MIDI Piano Keyboard
](https://vmpk.sourceforge.io). It can run parallelly to the ManualTester
script; just start it and setup it as follows:
- Open the menu: "Edit > MIDI Connections" and set the dialog as follows:
  - Check: "Enable MIDI Input"
  - Check: "MIDI Omni Mode" -> With this setting, you will see everything
                               comming out from the FootController software
  - On "MIDI IN Driver" choose: "Windows MM"
  - On "Input MIDI Connection" choose: "Virtual Port 2"
  - Uncheck: "Enable MIDI Thru on MIDI Output" -> If you don't do this, then
                                                  your NOTE messages will be
                                                  sent in an infinite loop
  - On "MIDI OUT Driver" choose: "Windows MM"
  - On "Output MIDI Connection" choose: "Virtual Port 1"
  - Uncheck: "Show Advanced Connections" -> Not needed
- Open the menu: "Edit > Preferences" and set it as follows:
  - Number of keys: here you are free to choose what ever you want. Normally
    you will see: 61. The maximum is 121. This depends on how many octaves you
    are going to use.
  - Starting Key: C
  - Note highlight color: MIDI Channels -> different colors will be used for
                                           each MIDI channel
  - Instruments file: leave the default, which is: "gmgsxg.ins". I think this
    doesn't really matter
  - Instrument: General MIDI
  - Keyboard Map: load the map: Virtual_Keyboard_Map.xml located on the assets
    folder
  - Raw Keyboard Map: default. I think this also doesn't matter
  - Drums Channel: 10
  - Uncheck: "MIDI channel state consistency" -> I don't know what this is
                                                 supposed to do
  - Check: "Translate MIDI velocity to key pressed color tint"
  - Check: "Always On Top"
  - Set whatever you want under: "Enable Computer Keyboard Input" and "Raw
    Computer Keyboard".
  - Check: "Enable Mouse Input"
  - Set whatever you want under: "Enable Touch Screen Input"
- On the main interface, set this parameters:
  - Channel: 1
  - Base Octave: 3
  - Transpose: 0
  - Velocity: set whatever you want
  
  With those parameters, the first key on that keyboard will be 36 = C1. You
  can find the keyboard map file equivalences [here
  ](#mapping-midi-notes-to-computer-keyboard-keys-on-virtual-midi-piano-keyboard)
  
  You may change other settings to fit your needs.
  
  Now you can send notes and bank select commands through the ManualTester
  script and you will see the results on the "Virtual MIDI Piano Keyboard". You
  may also use the virtual keyboard to send note messages; however, with a
  normal mouse, you can only push a note at a time. I guess on a touch screen
  you should be able to push more than one, but I'm not sure. You can simulate
  simultaneous key press by pressing simultaneous letters from your computer
  keyboard, ie: pressing and holding Q and W will send NOTE ON for: C1 and C#1;
  when releasing them, then the NOTE OFF messages will be sent.

### Mapping MIDI notes to computer keyboard keys on Virtual MIDI Piano Keyboard

Inside this project, you will find a file called: Virtual_Keyboard_Map.xml,
which setups the following equivalences:

| Number | Note | Keyboard key |
| ------ | ---- |--------------|
| 0      | C1   | C            |
| 1      | C#1  | V            |
| 2      | D1   | D            |
| 3      | D#1  | W            |
| 4      | E1   | E            |
| 5      | F1   | F            |
| 6      | F#1  | R            |
| 7      | G1   | G            |
| 8      | G#1  | H            |
| 9      | A1   | A            |
| 10     | A#1  | S            |
| 11     | B1   | B            |
| 12     | C2   | M            |
| 13     | C#2  | M            |
| 14     | D2   | J            |
| 15     | D#2  | K            |
| 16     | E2   | L            |

If you want to have your own map, then open that file and change the respective
key mappings.

## Use a software for intercepting MIDI messages

You can debug your system by watching the **MIDI** messages comming out from your
laptop or the **Raspberry Pi**. For doing this, you can use the following
software:

- Under Windows:
  - [Bome Send SX](https://www.bome.com/products/sendsx).

- Under Ubuntu Linux/MACOS:
  - [MIOS Studio 2](http://www.ucapps.de/mios_studio.html).

Then setup your system as follows:
- Create two virtual ports

Then setup the ports as follows:
- In Port (xml file): Virtual Port 1
- Out Port (xml file): Virtual Port 2
- In Port (Bome Send SX / MIOS Studio 2): Virtual Port 2
- Out Port (Bome Send SX / MIOS Studio 2): Virtual Port 1
- Then begin to send NOTE IN, NOTE ON, and CC messages, ie:
  - 80 0F 00 -> Sends a NOTE OFF on channel 1, whith note = 15 (0x0F)
  - 90 0F 40 -> Sends a NOTE ON on channel 1, whith note = 15 (0x0F), and
    velocity = 64 (0x40)
  - B0 20 01 -> Send a CONTROL CHANGE message on channel 1, with
                controller = 32 (0x20) and value = 01, which will select bank 2.

If you sent notes that are defined on your XML configuration file, then you
should see the resulting messages on the output of Bome Send SX or MIOS Studio 2.

Other option would be to connect your foot controller to Bome Send SX or MIOS
Studio 2. Here you will need the USB-TO-MIDI cable, then setup the system as
follows:
- Connect the USB-TO-MIDI to your laptop or Raspberry Pi USB port.
- The part labeled with "TO MIDI OUT" connect it to your Foot Controller
- Then on Bome Send SX or MIOS Studio 2 setup MIDI IN to: "USB Uno MIDI
  Interface"
- Start pressing the pedals or switches, then you should see the output either in
  Bome Send SX or MIOS Studio 2.

## Using a sequencer software

Alternativelly you could also use a **sequencer software**, ie: under Windows:
[Aria Maestosa](https://ariamaestosa.github.io/ariamaestosa/docs/index.html),
[Anvil Studio](https://www.anvilstudio.com),
[KaraKEYoke Karaoke](http://karakeyoke.com/software/karakeyoke.html); under
Linux: [Aria Maestosa
](https://ariamaestosa.github.io/ariamaestosa/docs/index.html), or any other
sequencer you know. The idea would be to route the **USB Uno MIDI Interface** to
that software and start looking at the **MIDI** data comming. You have there
several views: *staff view* (you will see the notes) or *message list* (you will
see the MIDI messages on a human-readable format).

## Activating the verbose mode

Finally you can activate the **debug mode** as follows:
```
python3 FootController.py --config "my-config.xml" --verbose
```
Then check the **log file**, which should be called: *debug.log* and it should be
stored in the same folder of *FootController.py*. Please enable this mode only if
you are experiencing problems; it may decrease the performance of your system.

I may also help you, but you need to create a new issue [here
](https://github.com/jmeile/JMMidiBassPedalController/issues). Please include the
following information:
- Screenshot or text of the error message
- If there isn't an error message, then explain exactly what's the issue
- If relevant, also include:
  - Your XML configuration file
  - The file: *debug.log*, which is located on the same folder of the main
    script.

Since this is a hobby, I may not have many time to solve the issue, so, do not
expected me to fix it quickly.

# License
This project is licensed under the [MIT License](LICENSE.md)
