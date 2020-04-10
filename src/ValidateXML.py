#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v1.0
# File: src/ValidateXML.py
# By:   Josef Meile <jmeile@hotmail.com> @ 10.04.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""
Helper script to check that the XSD schema and the XML config file are valid.

In case that the XSD and the XML files are valid, then it should print "True"
and a dictionary with all values from your XML file. Otherwise, some error
messages will be printed.

Run the script as follows:
python ValidateXML.py -h

There you will see the diferent command-line options supported by the script.
"""

from __future__ import print_function
import argparse
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import xmlschema
from pprint import pprint

class ValidateXMLArgumentParser(ArgumentParser):
  """
  ArgumentParser for the helper application
  
  Remarks:
  - The helper application will accept the following command line options:
    * --config: XML configuration file to check against the XSD schema.
  """

  def __init__(self, description = "Checks the specified XML file against the "
               "XSD schema"):
    """
    Setups the ArgumentParser of the helper program
    
    Parameters:
    * description: description of what the program is doing
    """
    self._parser = ArgumentParser(description = description,
      formatter_class = RawTextHelpFormatter, add_help = False)

  def add_arguments(self,
                    main_help = "Shows this help message and exits",
                    config_help = "XML file to use. If not given, then"
                    "conf/sample-config.xml will\nbe assumed\n"):
    """
    Adds the command line options and commands to the argument parser
    
    Parameters:
    * main_help: text of the -h, --help option
    * config_help: help of the "--config" command line option
    """
    self._parser.add_argument("-h", "--help", action = "help",
      default = argparse.SUPPRESS, help = main_help)

    self._parser.add_argument("-c", "--config",
                              default = "conf/sample-config.xml",
                              help = config_help)
                              
  def parse_arguments(self):
    """
    Validates the supplied command line options. It will show an error
    message if the vaildation failed and then it will exit
    """
    return self._parser.parse_args()

schema_name = 'conf/MidiBassPedalController.xsd'
if __name__ == "__main__":
  parser = ValidateXMLArgumentParser()
  parser.add_arguments()
  args = parser.parse_arguments()
  
  my_schema = xmlschema.XMLSchema11(schema_name)
  pprint(my_schema.is_valid(args.config))
  pprint(my_schema.to_dict(args.config))
