#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MainArgumentParser.py
# By: Josef Meile <jmeile@hotmail.com> @ 27.02.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/src/LICENSE.md
#
"""
Parses the main program command line options. It uses the python library:
argparse: https://docs.python.org/3/library/argparse.html
"""

from __future__ import print_function
import sys
import traceback
import argparse
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

class MainArgumentParser(ArgumentParser):
  """
  ArgumentParser for the main application
  
  Remarks:
  * The main application will accept the following command line options:
    --config: specifies the XML configuration file to use. It can be a relative
      or absolute path.
    --list: the available MIDI IN and OUT ports will be printed.
    --verbose: prints and logs vebose messages.
  """
  
  def __init__(self,
               description = "Translates NOTE ON/OFF messages comming from a "
               "foot controller to chords"):
    """
    Setups the ArgumentParser of the main program
    
    Parameters:
    * description: description of what the program is doing
    """
    self._parser = ArgumentParser(description = description,
      formatter_class = RawTextHelpFormatter, add_help = False)

  def add_arguments(self,
                    main_help = "Shows this help message and exits",
                    config_help = "XML Configuration file to use. If not given, "
                    "then conf/sample-config.xml will be assumed",
                    list_help = "It will show a list of the available MIDI "
                    "ports, then it will exit",
                    verbose_help = "Prints and logs verbose messages"):
    """
    Adds the command line options and commands to the argument parser
    
    Parameters:
    * main_help: text of the -h, --help option
    * config_help: help of the "--config" command line option
    * list_help: help of the "--list" command line option
    * verbose_help: help of the "--verbose" command line option
    """
    self._parser.add_argument("-h", "--help", action = "help",
      default = argparse.SUPPRESS, help = main_help)

    group = self._parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--config", default = "conf/sample-config.xml",
                       help = config_help)
    group.add_argument("-l", "--list", action = "store_true", help = list_help)
    self._parser.add_argument("-v", "--verbose", action = "store_true",
                              help = verbose_help)

  def parse_arguments(self):
    """
    Validates the supplied command line options. It will show an error
    message if the vaildation failed and then it will exit
    """
    return self._parser.parse_args()