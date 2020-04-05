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
import sys
import fnmatch
from rtmidi import MidiIn, MidiOut
from rtmidi.midiutil import open_midiport
from MidiProcessor import MidiProcessor
from CustomLogger import CustomLogger, PrettyFormat
import logging
from autologging import logged
import xmlschema
import platform

VIRTUAL_PREFFIX = "Virtual:"

#Creates a logger for this module.
logger = logging.getLogger(CustomLogger.get_module_name())

#Setups the logger with default settings
logger.setup()

#Register the logger with this class
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
    self.__log.debug("Initializing MidiConnector")
    self._args = args
    self._xsd_schema = xsd_schema
    self._midi_in = None
    self._midi_out = None
    self._in_ports = []
    self._in_port = 0
    self._use_virtual_in = False 
    self._out_ports = []
    self._out_port = 0
    self._use_virtual_out = False
    self._xml_dict = {}
    self.__log.debug("MidiConnector was initialized:\n%s", 
                     PrettyFormat(self.__dict__))

  def start(self):
    """
    Starts the processing requests
    Remarks:
    * It will either list the available MIDI ports, run in interative or
      silent mode, according to the passed command line options
    Returns:
    * A status string; either: "Quit", "Reload", "Reboot", or "Shutdown"
    """
    self.__log.info("Starting MidiConnector")
    status = None
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
        self.__log.debug("--list switch was passed")
        self._list_ports()
      else:
        self._parse_xml_config()
        self._parse_ports()
        self._open_ports()
        midi_processor = MidiProcessor(
          self._xml_dict,
          self._midi_in,
          self._midi_out,
          ignore_sysex = False,
          ignore_timing = False,
          ignore_active_sense = False,
        )
        midi_processor.parse_xml()
        status = midi_processor.read_midi()
        self.__log.info("Exiting")
        self._close_ports()
        self._free_midi()
    self.__log.debug("MidiConnector has been ended")
    return status

  def _parse_xml_config(self):
    """
    Parses the specified xml configuration file
    """
    self.__log.info("Parsing XML config")
    exit = False
    self.__log.debug("Calling XMLSchema11 api")
    try:
      xsd_schema = xmlschema.XMLSchema11(self._xsd_schema)
    except:
      exit = True
      error = traceback.format_exc()
      self.__log.info("Error while parsing xsd file:\n%s\n\n%s", 
                      self._xsd_schema, error)

    if not exit:
      self.__log.debug("Converting XML schema to dict")
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
        self.__log.info("Error while parsing xml file:\n%s\n\n%s", 
                        self._args.config, error)
    self.__log.debug("Got: \n%s", PrettyFormat(xml_dict))
    if exit:
      self.__log.debug("Unexpected error occured, aborting...")
      self._free_midi()
      sys.exit()
      
    self._xml_dict = xml_dict

  def _open_port(self, interface_type, midi_port, is_virtual = False):
    """
    Opens the specified MIDI port for the entered midi_callback
    Parameters:
    * interface_type: which interface to open: 'input' or 'output' 
    * midi_port: MIDI port used to open the MIDI interface
    * is_virtual: whether or not the port is virtual
    Returns:
    * In case of opening a virtual port, it will return a MIDI interface
    """
    if not is_virtual:
      self.__log.debug("Opening MIDI port: %s", str(midi_port))
      port_name = None
      client_name = None
    else:
      self.__log.debug("Opening Virtual MIDI port")
      port_name = midi_port
      midi_port = None
      client_name = VIRTUAL_PREFFIX[:-1]
    try:
      midi_interface = open_midiport(port = midi_port, type_ = interface_type,
                                     use_virtual = is_virtual,
                                     interactive = False,
                                     client_name = client_name,
                                     port_name = port_name)[0]
    except:
      error = traceback.format_exc()
      self.__log.info(error)
      self._free_midi()
      sys.exit()
    return midi_interface

  def _open_ports(self):
    """
    Opens the entered MIDI ports
    """
    self._midi_in = self._open_port("input", self._in_port,
                                    self._use_virtual_in)
    if self._use_virtual_in:
      port_name = self._in_port
    else:
      port_name = self._in_ports[self._in_port] 
    self.__log.info("MIDI IN Port: '%s' was opened", port_name)

    self._midi_out = self._open_port("output", self._out_port,
                                     self._use_virtual_out)
    if self._use_virtual_out:
      port_name = self._out_port
    else:
      port_name = self._out_ports[self._out_port] 
    self.__log.info("MIDI OUT Port: '%s' was opened", port_name)

  def _close_port(self, midi_interface):
    """
    Closes the specified MIDI interface
    Parameters:
    * midi_interface: MIDI interface that will be closed
    """
    self.__log.debug("Closing MIDI port")
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
    if self._use_virtual_in:
      port_name = self._in_port
    else:
      port_name = self._in_ports[self._in_port]
    self.__log.info("MIDI IN Port: '%s' was closed", port_name)
    self._close_port(self._midi_out)
    if self._use_virtual_out:
      port_name = self._out_port
    else:
      port_name = self._out_ports[self._out_port]
    self.__log.info("MIDI OUT Port: '%s' was closed", port_name)

  def _parse_port(self, port_list, arg_name):
    """
    Gets the specified port from command line
    Parameters:
    * port_list: List of available MIDI ports
    * arg_name: name of the argument to get. It can be: InPort or OutPort
    Returns:
    * A tupple containing:
      - either a port index or a virtual port string name
      - either if using a virtual or a real port
    """
    self.__log.debug("Getting: %s from:\n%s", arg_name, PrettyFormat(port_list))
    use_virtual = False
    num_ports = len(port_list)
    port_value = self._xml_dict.get('@'+arg_name, num_ports)
    self.__log.debug("Port value: %s", port_value)
    if (type(port_value) == str) and port_value.isdigit():
      port_value = int(port_value)
    elif type(port_value) == str:
      is_windows = (platform.system() == "Windows") 
      if port_value.startswith(VIRTUAL_PREFFIX):
        if not is_windows:
          #Virtual port only work unser MACOS and Linux. Windows doesn't
          #supports this. On the last operating system, the Virtual part will be
          #removed and it will be threatened as a normal port. You can assure
          #compatibilty between Windows and other OS by creating first the ports
          #with loopMIDI
          use_virtual = True
        port_value = port_value[len(VIRTUAL_PREFFIX):]
      if not use_virtual: 
        self.__log.debug("Searching port")
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
          self.__log.info("The %s: %s wasn't found.", arg_name, port_value)
          self._free_midi()
          self.__log.debug("Port wasn't found, exiting")
          sys.exit()
        port_value = port_index + 1
        self.__log.debug("Port was found, index: %d", port_value)
      else:
        self.__log.debug("Virutal Port will be used")
  
    if not use_virtual:
      #Internally, port numbers start from 0 because they are in an array
      port_value -= 1
      if port_value >= num_ports:
        self.__log.info("Invalid port number was supplied")
        self._free_midi()
        self.__log.debug("Exiting after getting invalid port")
        sys.exit()
      
    return port_value, use_virtual
  
  def _parse_ports(self):
    """
    Gets the passed ports to the command line
    """
    self.__log.debug("Parsing ports")
    self._in_port, self._use_virtual_in = self._parse_port(self._in_ports,
                                                           'InPort')
    self._out_port, self._use_virtual_out = self._parse_port(self._out_ports,
                                                             'OutPort')
    self.__log.debug("Ports were parsed")
  
  def _open_midi(self):
    """Starts MIDI without opening a port"""
    self.__log.info("Opening MIDI interfaces")
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
      self._free_midi()
      return False
    self.__log.debug("MIDI interfaces were opened")
    return True
  
  def _free_midi(self):
    """Frees MIDI resources"""
    self.__log.debug("Releasing MIDI")
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
    self.__log.debug("Getting available MIDI ports")
    ports = midi_interface.get_ports()
    self.__log.debug("Got:\n%s", PrettyFormat(ports))
    port_index = 0
    for port in ports:
      port_index_str = str(port_index)
      ports[port_index] = port
      port_index += 1
    self.__log.debug("Fixed port indexes:\n%s", PrettyFormat(ports))
    return ports

  def _get_all_ports(self):
    """
    Gets all the available MIDI IN and Out ports.
    """
    in_ports = []
    out_ports = []
    if self._open_midi():
      self.__log.debug("Getting all MIDI IN ports")
      in_ports = self._get_midi_ports(self._midi_in)
      self.__log.debug("Got:\n%s", PrettyFormat(in_ports))
      self.__log.debug("Getting all MIDI OUT ports")
      out_ports = self._get_midi_ports(self._midi_out)
      self.__log.debug("Got:\n%s", PrettyFormat(out_ports))
    self._in_ports = in_ports
    self._out_ports = out_ports
    self._free_midi()
  
  def _get_formatted_port_list(self, port_list):
    """
    Gets the port list as follows:
      <port_index>: <port_name>
    """
    self.__log.debug("Getting formatted port list")
    port_list_tuples = []
    for port_index, port_name in enumerate(port_list):
      port_list_tuples.append(str(port_index + 1) + ": " + port_name)
    self.__log.debug("Got: %s", PrettyFormat(port_list_tuples))
    return '\n\r'.join(port_list_tuples)
  
  def _list_ports(self):
    """
    Lists all the available MIDI IN and Out ports.
    """
    self.__log.info("\nAvailable MIDI IN ports:")
    self.__log.info(self._get_formatted_port_list(self._in_ports))
    
    self.__log.info("\nAvailable MIDI OUT ports:")
    self.__log.info(self._get_formatted_port_list(self._out_ports))
