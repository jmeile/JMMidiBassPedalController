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
#from MidiProcessor import MidiProcessor

#By default, file logging is enabled
Logger.init_logging()
#Disable file logging as follows:
#Logger.init_logging(file_log_level = logging.NOTSET)

#Creates a logger for this module. By default, console logging is disabled
#logger = Logger().setup_logger()
#Enable console debug logging as follows
#logger = Logger(console_log_level = logging.DEBUG).setup_logger()
#Show only information message. Same behavious as print
logger = Logger(
      console_log_level = logging.INFO,
      #Here only message will be printed in the console
      log_format = "%(message)s"
     ).setup_logger()

@logged(logger)
class MidiConnector:
  """
  Opens the MIDI ports and process the incomming connections
  """
  
  def __init__(self, args):
    """Initializes the MidiConnector class"""
    self._args = args
    self._midi_in = None
    self._midi_out = None
    self._in_ports = []
    self._in_port = 0
    self._out_ports = []
    self._out_port = 0

  def start(self):
    """
    Starts the processing requests
    Remarks:
    * It will either list the available MIDI ports, run in interative or
      silent mode, according to the passed command line options
    """
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
        """
        self._open_ports()
        MidiProcessor(
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
        ).read_midi()
        self._close_ports()
        """
        #Ignore this until the implementation is finished
        pass

    self._free_midi()
  
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
    self._open_port(self._midi_out, self._out_port)
  
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
    self._close_port(self._midi_out)
  
  def _parse_port(self, port_list, arg_name):
    """
    Gets the specified port from command line
    Parameters:
    * port_list: List of available MIDI ports
    * arg_name: name of the argument to get. It can be: in_port or out_port
    """
    num_ports = len(port_list)
    port_value = getattr(self._args, arg_name)
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
      port_value = port_index
    
    if port_value >= num_ports:
      self.__log.info("Invalid port number was supplied")
      self._free_midi()
      sys.exit()
      
    return port_value
  
  def _parse_ports(self):
    """
    Gets the passed ports to the command line
    """
    self._in_port = self._parse_port(self._in_ports, 'in_port')
    self._out_port = self._parse_port(self._out_ports, 'out_port')
  
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

  def _read_port(self, port_list, msg):
    """
    Asks the user for a MIDI port to use.
    Parameters:
    * port_list: ports from which the user has to choose from
    * msg: message to show to the user.
    """
    num_ports = len(port_list)
    ports_str = self._get_formatted_port_list(port_list)
    port = -1
    while port == -1:
      self.__log.info(msg)
      self.__log.info(ports_str)
      try:
        port = int(input("Type the port you want to use [0-" + \
             str(num_ports - 1) + "] or CTRL+C to abort: "))
      except KeyboardInterrupt:
        self.__log.info("The operation was aborted")
        self._free_midi()
        sys.exit()
      except:
        self.__log.info("\nAn unexpected error occured")
        error = traceback.format_exc()
        self.__log.info(error + "\n")
        port = -1
      if port >= num_ports:
        port = -1
        self.__log.info("\nInvalid port number was given\n")
        
    return port
    
  def _read_ports(self):
    self._in_port = self._read_port(self._in_ports, "Available MIDI IN "
      "ports:")
    print("")
    self._out_port = self._read_port(self._out_ports, "Available MIDI OUT "
      "ports:")

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