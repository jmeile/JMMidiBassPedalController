#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# FootController.py
# By: Josef Meile <jmeile@hotmail.com> @ 27.02.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""
Main program for the whole JMMidiBassPedalController package.

Run the script as follows:
python FootController.py -h

There you will see the diferent command-line options supported by the script.
"""
from __future__ import print_function
import os
import platform
from MainArgumentParser import MainArgumentParser
from CustomLogger import CustomLogger
import logging
from MidiConnector import MidiConnector

if __name__ == "__main__":
  parser = MainArgumentParser()
  parser.add_arguments()
  args = parser.parse_arguments()

  #By default, file logging is enabled
  file_log_level = logging.INFO
  
  #Disable file logging as follows:
  #file_log_level = logging.NOTSET
  
  if args.verbose:
    file_log_level = logging.DEBUG

  CustomLogger.init_logging(file_log_level = file_log_level)

  #By default, only info message will be printed to the console
  console_log_level = logging.INFO

  #Enable console debug logging as follows
  #console_log_level = logging.DEBUG

  #By default show only information message. Same behaviour as print
  log_format = "%(message)s"

  #You may add a much more verbose output by setting this
  #log_format = "%(asctime)s - %(name)s -> %(funcName)s, line: %(lineno)d\n"
  #              "%(message)s"

  #Creates a logger for this module.
  logger = logging.getLogger(CustomLogger.get_module_name())

  #Setups the logger with the given parameters
  logger.setup(console_log_level = console_log_level, log_format = log_format)

  if (file_log_level == logging.DEBUG):
    logger.debug("--verbose was detected, DEBUG log was enabled")

  def get_shutdown_command():
    """
    Gets the shutdown command according to the plattform
    """
    global logger
    logger.debug("Generating shutdown command")
    shutdown_command = ''
    operating_system = platform.system()
    if operating_system == "Windows":
      logger.debug("Windows detected")
      shutdown_command = 'shutdown /s /f /t 0 /d p:0:0 /c'
    elif operating_system == "Linux":
      logger.debug("Linux detected")
      shutdown_command = 'shutdown -h now'
    elif operating_system == "Darwin":
      logger.debug("MACOS detected")
      shutdown_command = 'shutdown -h now'
    else:
      logger.debug("Unsupported OS.")
      raise Exception("Unsupported operating system")
    shutdown_command += ' "MidiBassPedal restart"'
    return shutdown_command
    
  def get_reboot_command():
    """
    Gets the reboot command according to the plattform
    """
    global logger
    logger.debug("Generating reboot command")
    reboot_command = ''
    operating_system = platform.system()
    if operating_system == "Windows":
      logger.debug("Windows detected")
      reboot_command = 'shutdown /r /f /t 0 /d p:0:0 /c'
    elif operating_system == "Linux":
      logger.debug("Linux detected")
      reboot_command = 'shutdown -r now'
    elif operating_system == "Darwin":
      logger.debug("MACOS detected")
      reboot_command = 'shutdown -r now'
    else:
      logger.debug("Unsupported OS.")
      raise Exception("Unsupported operating system")
    reboot_command += ' "MidiBassPedal restart"'
    return reboot_command

  midi = MidiConnector(args)
  status = None
  logger.info("Initializing main loop")
  while status == None:
    status = midi.start()
    command = None
    if status == "Reload":
      logger.info("Controller reload received")
      #Here nothing need to be done. The loop will restart MIDI
      status = None
    elif status == "Reboot":
      logger.info("Controller reboot received")
      command = get_reboot_command()
    elif status == "Shutdown":
      logger.info("Controller shutdown received")
      command = get_shutdown_command()
    else:
      logger.info("Quitting controller")
      break
      
    if command != None:
      logger.debug("Running command: %s", command)
      os.system(command)
