#!/bin/bash

# JMMidiBassPedalController v1.5
# File: src/Automation/MACOS/Start_FootController_MACOS_Startup.sh
# By:   Josef Meile <jmeile@hotmail.com> @ 28.07.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#

#Script to start the JMMidiBassPedalController while starting MACOS

#Usage:
#This script should be used as a Launch Daemon or Agent. See the README.md file
#inside the Automation folder for more details.

#You can customize the following variables according to your needs

#Directory where the FootController.py script is located
WORKING_DIR="/Users/your_user/Documents/JMMidiBassPedalController/src"

#Script command line options.
#Set this to "--verbose" to enable debug messages
SCRIPT_OPTIONS=""

#Path to the python3 binary
PYTHON_BIN="/usr/local/bin/python3"

#Configuration file to use
CONFIG_FILE="conf/bass-pedal-config.xml"

function shutdown()
{
  echo `date` " " `whoami` " Received a signal to shutdown"
}

function startup()
{
  echo `date` " " `whoami` " Starting..."
  cd $WORKING_DIR
  $PYTHON_BIN FootController.py --config=$CONFIG_FILE $SCRIPT_OPTIONS
  tail -f /dev/null &
  wait $!
}

trap shutdown SIGTERM
trap shutdown SIGKILL

startup;
