#!/bin/sh

# JMMidiBassPedalController v1.4
# File: src/Automation/Linux/Start_FootController_Linux_Startup.sh
# By:   Josef Meile <jmeile@hotmail.com> @ 05.07.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#

# Shell script started by the JMMidiBassPedalController service

# Usage:
# This script should be used as a Linux service. See the README.md file inside
#the Automation folder for more details.

. /lib/lsb/init-functions

SERVICE_NAME=JMMidiBassPedalController

#You can customize the following variables according to your needs

#Directory where this file is located
WORKING_DIR="/home/your_user/Documents/JMMidiBassPedalController/src/Automation/Linux"

#Directory where the FootController.py script is located
SCRIPT_DIR="/home/your_user/Documents/JMMidiBassPedalController/src"

#Script command line options.
#Set this to "--verbose" to enable debug messages
SCRIPT_OPTIONS=""

#Path to the python3 binary, usually /usr/bin/python3
PYTHON_BIN="/usr/bin/python3"

#Configuration file to use
CONFIG_FILE="conf/bass-pedal-config.xml"

stop()
{
  echo `date` " " `whoami` " Received a signal to shutdown"
}

start()
{
  echo `date` " " `whoami` " Starting..."
  cd $SCRIPT_DIR
  ( $PYTHON_BIN FootController.py --config=$CONFIG_FILE $SCRIPT_OPTIONS ) &
}

install()
{
  echo "Installing the $SERVICE_NAME service"
  cd $WORKING_DIR
  sudo cp $SERVICE_NAME.service /etc/systemd/system
  sudo systemctl enable $SERVICE_NAME
  sudo systemctl daemon-reload
  sudo service $SERVICE_NAME start
}

remove()
{
  echo "Removing the $SERVICE_NAME service"
  sudo service $SERVICE_NAME stop
  sudo systemctl disable $SERVICE_NAME
  sudo rm /etc/systemd/system/$SERVICE_NAME.service
  sudo systemctl daemon-reload
}

case "$1" in
start)
start
;;

stop)
stop
;;

install)
install
;;

remove)
remove
;;

*)

esac
exit ${RETVAL}
