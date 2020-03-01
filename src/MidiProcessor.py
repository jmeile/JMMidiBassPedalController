#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MidiProcessor.py
# By: Josef Meile <jmeile@hotmail.com> @ 01.03.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/src/LICENSE.md
#
"""
Intercepts MIDI IN messages by subclassing the MidiInputHandler class and
overwritting the NOTE ON, NOTE OFF, AND CONTROL CHANGE messages
"""

from __future__ import print_function
import traceback
import time
from MidiInputHandler import MidiInputHandler
from Logger import Logger
import logging
from autologging import logged

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

#Equivalences of the numeric velocities to a dynamic level
NOTE_VELOCITIES = {
  's'   :   0,  #silence
  'pppp':  10,  #minimum value
  'ppp' :  23,  #pianississimo, very very soft
  'pp'  :  36,  #pianissimo,    very soft
  'p'   :  49,  #piano,         soft
  'mp'  :  62,  #mezzo-piano,   moderately soft
  'mf'  :  75,  #mezzo-forte,   moderately loud
  'f'   :  88,  #forte,         loud
  'ff'  : 101,  #fortissimo,    very loud
  'fff' : 114,  #fortississimo, very very loud
  'ffff': 127   #maximum value
}

@logged(logger)
class MidiProcessor(MidiInputHandler):
  """
  Overwrites MidiInputHandler to provide custom handlers for NOTE ON, NOTE
  OFF, and CONTROL CHANGE messages
  """
  
  def __init__(self, xml_dict, midi_in, midi_out, ignore_sysex = True,
               ignore_timing = True, ignore_active_sense = True):
    """
    Calls the MidiInputHandler constructor and initializes the sub class
    attributes
    Parameters:
    * xml_dict: dictionary containing the parsed values from the xml
      configuration file
    * midi_in: MIDI IN interface to use
    * midi_out: MIDI OUT interface to use
    * ignore_* parameters: see the "_ignore_messages" method
    """
    super().__init__(midi_in, midi_out, ignore_sysex, ignore_timing,
                   ignore_active_sense = True)
    self._xml_dict = xml_dict

  def parse_xml(self):
    """Parses the xml dict"""
    self._current_bank = self._xml_dict['@InitialBank']
    self._current_velocity = 0
    self._xml_dict["@BassPedalVelocity"] = self._parse_velocity_transpose(
                                             "BassPedalVelocity",
                                             self._xml_dict)
    self._xml_dict["@ChordVelocity"] = self._parse_velocity_transpose(
                                         "ChordVelocity", self._xml_dict)
                                          
    self._xml_dict["@BassPedalTranspose"] = self._parse_velocity_transpose(
                                              "BassPedalTranspose",
                                              self._xml_dict)
    if self._xml_dict["@BassPedalTranspose"] == None:
      self._xml_dict["@BassPedalTranspose"] = 0
                                              
    self._xml_dict["@ChordTranspose"] = self._parse_velocity_transpose(
                                          "ChordTranspose", self._xml_dict)
    if self._xml_dict["@ChordTranspose"] == None:
      self._xml_dict["@ChordTranspose"] = 0

    self._parse_banks()
  
  def _parse_banks(self):
    """
    Parses the banks from the xml_dict
    """
    for bank in self._xml_dict['Bank']:
      bank["@BassPedalVelocity"] = self._parse_velocity_transpose(
                                     "BassPedalVelocity", bank, self._xml_dict)
      bank["@ChordVelocity"] = self._parse_velocity_transpose("ChordVelocity",
                                                              bank,
                                                              self._xml_dict)
      bank["@BassPedalTranspose"] = self._parse_velocity_transpose(
                                      "BassPedalTranspose", bank,
                                      self._xml_dict)
      bank["@ChordTranspose"] = self._parse_velocity_transpose("ChordTranspose",
                                                               bank,
                                                               self._xml_dict)
      self._parse_pedals(bank)
  
  def _parse_pedals(self, parent_bank):
    """
     Parses the pedals from the current bank
     Parameters:
     * parent_bank: bank on which this pedal is contained
    """
    for pedal in parent_bank['Pedal']:
      pedal["@BassPedalVelocity"] = self._parse_velocity_transpose(
                                      "BassPedalVelocity", pedal, parent_bank)
      pedal["@ChordVelocity"] = self._parse_velocity_transpose("ChordVelocity",
                                                               pedal,
                                                               parent_bank)
      pedal["@BassPedalTranspose"] = self._parse_velocity_transpose(
                                       "BassPedalTranspose", pedal, parent_bank)
      pedal["@ChordTranspose"] = self._parse_velocity_transpose(
                                   "ChordTranspose", pedal, parent_bank)

  def _parse_velocity_transpose(self, attribute_name, current_node,
                                parent_node = None):
    """
    Gets the specified attribute_name from the xml_dict and converts it to its
    numeric representation
    Parameters:
    * attribute_name: name of the attribute to retreive. It can be either:
      BassPedalVelocity, ChordVelocity, BassPedalTranspose, or ChordTranspose
    * current_node: current note to parse
    * parent_node: reference to the parent node
    Returns:
    * If the specified attribute is not None for the current_node, then returns
      its value; otherwise, the value of the parent node will be returned. If
      there is no parent node, then the attribute_name from xml_dict will be
      returned.
    """
    attribute_value = current_node.get('@' + attribute_name)
    if attribute_value != None:
      if not isinstance(attribute_value, int):
        #This will be only true for velocities; transpositions are always
        #integers
        if attribute_value.isdigit():
          attribute_value = int(attribute_value)
        else:
          attribute_value = NOTE_VELOCITIES[attribute_value]
      return attribute_value

    if parent_node == None:
      return self._xml_dict.get('@' + attribute_name)
      
    return self._parse_velocity_transpose(attribute_name, parent_node)

  def _on_note_on(self, message):
    self.__log.debug("MIDI message: %r" % message)
    
  def _on_note_off(self, message):
    self.__log.debug("MIDI message: %r" % message)
    
  def _on_control_change(self, message):
    self.__log.debug("MIDI message: %r" % message)
    
  def read_midi(self):
    """
    Main program loop.
    """
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      self.__log.info("Exit...")
    except:
      error = traceback.format_exc()
      self.__log.info(error)