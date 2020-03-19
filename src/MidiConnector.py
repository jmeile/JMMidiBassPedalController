#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MidiConnector.py
# By: Josef Meile <jmeile@hotmail.com> @ 27.02.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""
Connects to the MIDI ports
"""

from __future__ import print_function
import traceback
from Logger import Logger
import logging
from autologging import logged
import sys
import fnmatch
from rtmidi import MidiIn, MidiOut
import xmlschema
from MidiProcessor import MidiProcessor

#By default, file logging is enabled
file_log_level = logging.DEBUG

#Disable file logging as follows:
#file_log_level = logging.NOTSET

Logger.init_logging(file_log_level = file_log_level)

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
logger = Logger(console_log_level = console_log_level, log_format = log_format
         ).setup_logger()

@logged(logger)
class MidiConnector:
  """
  Opens the MIDI ports and process the incomming connections
  """
  
  def __init__(self, args, xsd_schema = 'conf/MidiBassPedalController.xsd'):
    """
    Initializes the MidiConnector class
    Parameters:
    * args: command-line arguments
    * xsd_schema: path to the xsd schema
    """
    self._args = args
    self._xsd_schema = xsd_schema
    self._midi_in = None
    self._midi_out = None
    self._in_ports = []
    self._in_port = 0
    self._out_ports = []
    self._out_port = 0
    self._xml_dict = {}

  def start(self):
    """
    Starts the processing requests
    Remarks:
    * It will either list the available MIDI ports, run in interative or
      silent mode, according to the passed command line options
    Returns:
    * A status string; either: "Quit", "Restart", "Reboot", or "Shutdown"
    """
    status = None
    self.__log.info("Starting MIDI")
    self._get_all_ports()
    exit = False
    if len(self._in_ports) == 0:
      self.__log.info("No MIDI IN ports were found. Please connect your MIDI "
          "device and run the script again")
      exit = True

    if len(self._out_ports) == 0:
      self.__log.info("No MIDI OUT ports were found. Please connect your MIDI "
          "device and run the script again")
      exit = True
      
    if not exit:
      if self._args.list:
        self._list_ports()
      else:
        self._parse_xml_config()
        self._parse_ports()
        self._open_ports()
        midi_processor = MidiProcessor(
          self._xml_dict,
          self._midi_in,
          self._midi_out,
          #Unless you want to grap SysEx dumps, you should enable this.
          #This is the only utility of the FCB1010 SysEx messages.
          #ignore_sysex = False,
          #The next two message won't be transmitted by the FCB1010, So,
          #don't enable it; they won't do anything. You should use them
          #if using another Foot controller that transmits them
          #ignore_timing = False,
          #ignore_active_sense = False,
        )
        midi_processor.parse_xml()
        status = midi_processor.read_midi()
        self.__log.info("Exiting")
        self._close_ports()
    self._free_midi()
    return status

  def _parse_xml_config(self):
    """
    Parses the specified xml configuration file
    """
    self.__log.info("Parsing XML config")
    exit = False
    try:
      xsd_schema = xmlschema.XMLSchema11(self._xsd_schema)
    except:
      exit = True
      error = traceback.format_exc()
      self.__log.info("Error while parsing xsd file:\n" + self._xsd_schema + \
                      "\n\n" + error)
      
    if not exit:
      try:
        xml_dict = xsd_schema.to_dict(self._args.config)
        #A last manual validation must be done here: the InitialBank value must
        #be less or equal than the total number of banks
        if xml_dict['@InitialBank'] > len(xml_dict['Bank']):
          raise Exception("InitialBank is higher than the possible number of "
                          "banks / maximum: " + str(len(xml_dict['Bank'])) + \
                          ", given value: " + str(xml_dict['@InitialBank']))
      except:
        exit = True
        error = traceback.format_exc()
        self.__log.info("Error while parsing xml file:\n" + \
                        self._args.config + "\n\n" + error)
    
    if exit:
      self._free_midi()
      sys.exit()
      
    self._xml_dict = xml_dict

  def _open_port(self, midi_interface, midi_port):
    """
    Opens the specified MIDI port for the entered midi_interface
    Parameters:
    * midi_interface: MIDI interface that will be opened
    * midi_port: MIDI port used to open the MIDI interface
    """
    try:
      midi_interface.open_port(midi_port)
    except:
      error = traceback.format_exc()
      self.__log.info(error)
      self._free_midi()
      sys.exit()

  def _open_ports(self):
    """
    Opens the entered MIDI ports
    """
    self._open_port(self._midi_in, self._in_port)
    self.__log.info("MIDI IN Port: '" + self._in_ports[self._in_port] + \
                    "' was opened")
    self._open_port(self._midi_out, self._out_port)
    self.__log.info("MIDI OUT Port: '" + self._out_ports[self._out_port] + \
                    "' was opened")
  
  def _close_port(self, midi_interface):
    """
    Closes the specified MIDI interface
    Parameters:
    * midi_interface: MIDI interface that will be closed
    """
    try:
      midi_interface.close_port()
    except:
      error = traceback.format_exc()
      self.__log.info(error)

  def _close_ports(self):
    """
    Closes all opened MIDI ports
    """
    self._close_port(self._midi_in)
    self.__log.info("MIDI IN Port: '" + self._in_ports[self._in_port] + \
                    "' was closed")
    self._close_port(self._midi_out)
    self.__log.info("MIDI OUT Port: '" + self._out_ports[self._out_port] + \
                    "' was closed")

  def _parse_port(self, port_list, arg_name):
    """
    Gets the specified port from command line
    Parameters:
    * port_list: List of available MIDI ports
    * arg_name: name of the argument to get. It can be: InPort or OutPort
    """
    num_ports = len(port_list)
    port_value = self._xml_dict.get('@'+arg_name, num_ports)
    if (type(port_value) == str) and port_value.isdigit():
      port_value = int(port_value)
    elif type(port_value) == str:
      #On this case, a string with part of the name was given, so, it
      #will be searched in the available ports
      port_index = 0
      port_found = False
      for port_name in port_list:
        filtered = fnmatch.filter([port_name], port_value)
        if filtered != []:
          port_found = True
          break
        port_index += 1
      if not port_found:
        self.__log.info("The " + arg_name + ": " + port_value + " wasn't found.")
        self._free_midi()
        sys.exit()
      port_value = port_index + 1
    
    #Internally, port numbers start from 0 because they are in an array
    port_value -= 1
    if port_value >= num_ports:
      self.__log.info("Invalid port number was supplied")
      self._free_midi()
      sys.exit()
      
    return port_value
  
  def _parse_ports(self):
    """
    Gets the passed ports to the command line
    """
    self._in_port = self._parse_port(self._in_ports, 'InPort')
    self._out_port = self._parse_port(self._out_ports, 'OutPort')
  
  def _open_midi(self):
    """Starts MIDI without opening a port"""
    try:
      self._midi_out = MidiOut()
      self._midi_in = MidiIn()
      #Note: if you need to catch SysEx, MIDI clock, and active sense
      #messages, then use the method: ignore_types as follows:
      #self._midi_in.ignore_types(sysex = False, timing = False,
      #             active_sense = False)
      #They are ignored by default. I don't need this right now, so the
      #standard behaviour is OK for me
    except:
      error = traceback.format_exc()
      self.__log.info(error)
      del self._midi_out
      del self._midi_in
      return False
    return True
  
  def _free_midi(self):
    """Frees MIDI resources"""
    del self._midi_in
    del self._midi_out
    self.__log.info("MIDI was released")
  
  def _get_midi_ports(self, midi_interface):
    """
    Gets the available ports for the specified MIDI interface
    Parameters:
    * midi_interface: interface used for listing the ports. It can be
      either _midi_in or _midi_out.
    """
    ports = midi_interface.get_ports()
    port_index = 0
    for port in ports:
      port_index_str = str(port_index)
      
      #This line drops the port number from the end and adds it at the
      #beginning. I think this:
      # "1: Bome MIDI Translator 1"
      #is much clearer than this:
      # "Bome MIDI Translator 1 1"
      port = port[:-(len(port_index_str) + 1)]
      
      ports[port_index] = port
      port_index += 1
    return ports

  def _get_all_ports(self):
    """
    Gets all the available MIDI IN and Out ports.
    """
    in_ports = []
    out_ports = []
    if self._open_midi():
      in_ports = self._get_midi_ports(self._midi_in)
      out_ports = self._get_midi_ports(self._midi_out)
    self._in_ports = in_ports
    self._out_ports = out_ports
  
  def _get_formatted_port_list(self, port_list):
    """
    Gets the port list as follows:
      <port_index>: <port_name>
    """
    port_list_tuples = []
    for port_index, port_name in enumerate(port_list):
      port_list_tuples.append(str(port_index + 1) + ": " + port_name)
    return '\n\r'.join(port_list_tuples)
  
  def _list_ports(self):
    """
    Lists all the available MIDI IN and Out ports.
    """
    self.__log.info("\nAvailable MIDI IN ports:")
    self.__log.info(self._get_formatted_port_list(self._in_ports))
    
    self.__log.info("\nAvailable MIDI OUT ports:")
    self.__log.info(self._get_formatted_port_list(self._out_ports))