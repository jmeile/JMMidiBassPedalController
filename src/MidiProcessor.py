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
from pprint import pprint

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

#Here we assume -2 as the first octave, so, the first note would be C-2 and the
#middle C is C3. Other systems assume the first octave to be -1
FIRST_OCTAVE = -2

#The last octave is calculated in terms of the first one
LAST_OCTAVE = 10 + FIRST_OCTAVE

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

#First MIDI octave starting from C-2
MIDI_NOTES = {
  'C' :   0,
  'C#':   1,
  'D' :   2,
  'D#':   3,
  'E' :   4,
  'F' :   5,
  'F#':   6,
  'G' :   7,
  'G#':   8,
  'A' :   9,
  'A#':  10,
  'B' :  11
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
    pprint(self._xml_dict)
    self._current_bank = self._xml_dict['@InitialBank'] - 1
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

    #Internally midi channels begin with zero
    self._xml_dict['@InChannel'] -= 1
    self._xml_dict['@OutGeneralMidiChannel'] -= 1
    self._xml_dict['@OutBassPedalChannel'] -= 1
    self._xml_dict['@OutChordChannel'] -= 1
    self._parse_banks()
    pprint(self._xml_dict)
  
  def _parse_banks(self):
    """
    Parses the banks from the xml_dict
    """
    bank_index = 0
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
      self._parse_pedals(bank, bank_index)
      bank_index += 1
  
  def _parse_pedals(self, parent_bank, bank_index):
    """
     Parses the pedals from the current bank
     Parameters:
     * parent_bank: bank on which this pedal is contained
     * bank_index: index of the bank inside the controller node (begins with
       zero)
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

      self._parse_notes(pedal)
      bank_select = pedal.get("@BankSelect")
      num_banks = len(self._xml_dict["Bank"])
      if bank_select != None:
        if bank_select.isdigit():
          bank_select = int(bank_select) - 1
        elif bank_select == '+':
          bank_select = bank_index + 1
        elif bank_select == '-':
          bank_select = bank_index - 1
        elif bank_select == 'L':
          bank_select = num_banks - 1
          
        if isinstance(bank_select, int):
          if bank_select >= num_banks:
            bank_select = 0
          elif bank_select < 0:
            bank_select = num_banks - 1
      pedal["@BankSelect"] = bank_select

  def _parse_notes(self, pedal):
    """
    Parses the set notes in the xml_dict. It will transpose them according to
    the given parameters.
    """
    note = pedal.get('@Note')
    if not note.isdigit():
      #The formula to calculate the MIDI note number is:
      #Note = (12 * (octave - FIRST_OCTAVE)) + MIDI_NOTES[note]
      octave = pedal.get('@Octave')
      #Get the base note
      base_note = MIDI_NOTES[note]
      note = (12 * (octave - FIRST_OCTAVE)) + base_note
    else:
      note = int(note)
      #This is different, a MIDI NOTE number was given, so we need to calculate
      #its octave as follows:
      #int(note / 12)+FIRST_OCTAVE
      pedal['@Octave'] = int(note / 12) + FIRST_OCTAVE
    
    pedal['@Note'] = note
    
    note = pedal.get("@BassNote")
    if note is not None:
      if not note.isdigit():
        base_note = MIDI_NOTES[note]
        bass_octave = pedal["@Octave"]
      else:
        note = int(note)
        #Here we need to calculate the octave of the entered note
        bass_octave = int(note / 12) + FIRST_OCTAVE
        pedal["@Octave"] = bass_octave
        
        #Then we get the base note
        base_note = note - (12 * (bass_octave - FIRST_OCTAVE))
      
      #Now we need to see if there is a transposition factor and increase the
      #octave accordingly
      new_octave = pedal["@BassPedalTranspose"] + bass_octave
      if new_octave < FIRST_OCTAVE:
        new_octave = FIRST_OCTAVE
      elif new_octave > LAST_OCTAVE:
        new_octave = LAST_OCTAVE
        if base_note >= 8:
          #This is the case when you have a note higher or equal than G#, but
          #you want to put transpose it to the last octave, which is imposible,
          #so, it will be transposed to the previous octave
          new_octave -= 1
      
      pedal["@BassOctave"] = new_octave
      note = base_note + (12 * (new_octave - FIRST_OCTAVE))
      
    pedal["@BassNote"] = note

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