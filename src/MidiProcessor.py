#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MidiProcessor.py
# By: Josef Meile <jmeile@hotmail.com> @ 01.03.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
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
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_OFF, NOTE_ON,
                                  SYSTEM_EXCLUSIVE, END_OF_EXCLUSIVE)

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
               ignore_timing = True, ignore_active_sense = True,
               default_velocity = 64):
    """
    Calls the MidiInputHandler constructor and initializes the sub class
    attributes
    Parameters:
    * xml_dict: dictionary containing the parsed values from the xml
      configuration file
    * midi_in: MIDI IN interface to use
    * midi_out: MIDI OUT interface to use
    * ignore_* parameters: see the "_ignore_messages" method
    * default_velocity: default velocity for NOTE_ON and NOTE_OFF messages
    """
    super().__init__(midi_in, midi_out, ignore_sysex, ignore_timing,
                   ignore_active_sense = True)
    self._xml_dict = xml_dict
    self._default_velocity = default_velocity
    self._quit = False

  def parse_xml(self):
    """Parses the xml dict"""
    self._current_bank = self._xml_dict['@InitialBank'] - 1
    self.__log.info("Current Bank: " + str(self._xml_dict['@InitialBank']))
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
    self._xml_dict['@OutBassPedalChannel'] -= 1
    self._xml_dict['@OutChordChannel'] -= 1
    self._parse_banks()
    #pprint(self._xml_dict)
  
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
    pedal_list = {}
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

      self._parse_notes(pedal, pedal_list)
      self._parse_chords(pedal)
      self._parse_messages(pedal)
      bank_select = pedal.get("@BankSelect")
      num_banks = len(self._xml_dict["Bank"])
      fix_bank = True
      if bank_select != None:
        if bank_select.isdigit():
          bank_select = int(bank_select) - 1
          #Here it is a configuration error. The user gave a higher bank, which
          #doesn't exist
          fix_bank = False
        elif bank_select == '+':
          bank_select = bank_index + 1
        elif bank_select == '-':
          bank_select = bank_index - 1
        elif bank_select == 'L':
          bank_select = num_banks - 1
          
        if isinstance(bank_select, int):
          self.__log.info("BankSelect: " + str(bank_select))
          if (bank_select >= num_banks) and fix_bank:
            bank_select = 0
          elif bank_select < 0:
            bank_select = num_banks - 1
          elif bank_select >= num_banks:
            raise Exception("Bank number: " + str(bank_select + 1) + " On "
                            "BankSelect is out of range. Maximum: " + \
                            str(num_banks))
      pedal["@BankSelect"] = bank_select
    parent_bank["@PedalList"] = pedal_list

  def _parse_messages(self, pedal):
    """
    Parses the given pedal messages storing them in a list
    """
    messages = pedal.get('Message')
    if messages != None:
      message_list = []
      for full_message in messages:
        message_string = full_message["@String"]
        hexadecimal_strings = message_string.split(' ')
        hexadecimal_message = []
        for hexadecimal_string in hexadecimal_strings:
          hexadecimal_message.append(int(hexadecimal_string, 16))
        message_list.append(hexadecimal_message)
      pedal["@MessageList"] = message_list

  def _parse_chords(self, pedal):
    """
    Parses the given chord notes an converts them to MIDI notes
    """
    chord_notes = pedal.get("@ChordNotes")
    if chord_notes != None:
      chord_note_list = chord_notes.split(',')
      octave = pedal.get("@BassOctave")
      if octave == None:
        octave = pedal.get("@Octave")

      bass_note = pedal.get("@BassNote")
      chord_transpose = pedal.get("@ChordTranspose")
      if chord_transpose == None:
        if bass_note != None:
          chord_transpose = pedal.get("@BassPedalTranspose")
        else:
          chord_transpose = 0
          
      note_velocity = pedal["@ChordVelocity"]
      octave += chord_transpose
      base_note = None
      note_messages = pedal.get("@NoteMessages")
      if note_messages == None:
        note_messages = {NOTE_ON: [], NOTE_OFF: []}
      midi_channel = self._xml_dict["@OutChordChannel"]
      note_index = 0
      for chord_note in chord_note_list:
        previous_note = base_note
        base_note = MIDI_NOTES[chord_note]
        if (note_index != 0) and (base_note < previous_note):
          octave += 1

        note, octave = self._parse_note(chord_note, octave)
        self._set_note_messages(note_messages, note, midi_channel,
                                note_velocity)
        if note_index == 0:
          pedal["@ChordOctave"] = octave
        
        chord_note_list[note_index] = note
        note_index += 1
      chord_notes = chord_note_list
      pedal["@NoteMessages"] = note_messages
    
    pedal["@ChordNotes"] = chord_notes

  def _set_note_messages(self, note_messages, note, midi_channel,
                         velocity = None):
    """
    Sets the NOTE_ON and NOTE_OFF messages for the specified parameters
    Parameters:
    * note_messages: dictionary with two lists: NOTE_ON and NOTE_OFF
    * note: note that will be used for the messages
    * midi_channel: MIDI channel that will be set. It is a number between 0 and
      15
    * velocity: velocity for the resultant note. If not given, then
      _default_velocity will be assumed. It must be a number between 0 and 127
    Returns:
    * note_messages will be returned with the new note messages
    """
    if velocity == None:
      velocity = self._default_velocity

    for message_type in [NOTE_ON, NOTE_OFF]:
      header = message_type | midi_channel
      note_messages[message_type].append([header, note, velocity])

  def _parse_note(self, note, octave = None, transpose = 0):
    """
    Given a note string converts it to a MIDI NOTE according to the entered
    parameters.
    Parameters:
    * note: note string to convert
    * octave: if given, the octave of the entered note. This is only necessary
      if the entered note isn't a number, but a note symbol, ie: "C#"
    * transpose: number of octaves to transpose the note.
    Returns
    * The recalculated note and its octave
    """
    if not note.isdigit():
      #Get the base note
      base_note = MIDI_NOTES[note]
    else:
      note = int(note)
      #This is different, a MIDI NOTE number was given, so we need to calculate
      #its octave as follows:
      octave = int(note / 12) + FIRST_OCTAVE
      base_note = note - (12 * (octave - FIRST_OCTAVE))

    octave += transpose
    if octave < FIRST_OCTAVE:
      octave = FIRST_OCTAVE
    elif octave > LAST_OCTAVE:
      octave = LAST_OCTAVE
    if (base_note >= 8) and (octave == LAST_OCTAVE):
      octave -= 1

    note = (12 * (octave - FIRST_OCTAVE)) + base_note     
    return note, octave

  def _parse_notes(self, pedal, pedal_list):
    """
    Parses the set notes in the xml_dict. It will transpose them according to
    the given parameters.
    Parameters
    * pedal: pedal for which the notes are going to be calculated
    * pedal_list: after having calculated notes, pedals will be indexed by pedal
      note
    """
    note = pedal.get('@Note')
    octave = pedal.get('@Octave')
    pedal['@Note'], pedal['@Octave'] = self._parse_note(note, octave)
    pedal_list[pedal['@Note']] = pedal
      
    note = pedal.get("@BassNote")
    if note != None:
      note, octave = self._parse_note(note, pedal['@Octave'],
                                      pedal["@BassPedalTranspose"])
      pedal["@BassOctave"] = octave
      note_messages = {NOTE_ON: [], NOTE_OFF: []}
      pedal_channel = self._xml_dict["@OutBassPedalChannel"]
      pedal_velocity = pedal["@BassPedalVelocity"]
      self._set_note_messages(note_messages, note, pedal_channel,
                              pedal_velocity)
      pedal["@NoteMessages"] = note_messages

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

  def _send_midi_message(self, message):
    """
    Overrides the _send_midi_message method from MidiInputHandler.
    """
    #Do not uncomment this on a productive environment. SysEx messages
    #can be long, so logging them can slower things
    #self.__log.debug("MIDI message: %r" % message)
    
    #This may really slower things because it will do some operations in
    #the message to make it human readable. Use it only for debugging
    #self.__log.debug("MIDI message: %s" % \
    #  '[{}]'.format(' '.join(hex(x).lstrip("0x").upper().zfill(2)
    #  for x in message)))
    status = message[0] & 0xF0
    channel = message[0] & 0x0F
    send_message = False
    messages = []
    if (self._xml_dict['@InChannel'] == channel) and \
       status in [NOTE_ON, NOTE_OFF, CONTROL_CHANGE]:       
      current_bank = self._xml_dict['Bank'][self._current_bank]
      if status in [NOTE_ON, NOTE_OFF]:
        note = message[1]
        pedal = current_bank["@PedalList"].get(note)
        if pedal != None:
          self._current_velocity = message[2]
          if (self._current_velocity == 0) and \
             (self._xml_dict["@MinVelocityNoteOff"]):
             status = NOTE_OFF
          bank_select = pedal.get("@BankSelect")
          if (bank_select != None) and (status == NOTE_OFF):
            if bank_select != "Q":
              self._current_bank = bank_select
              self.__log.info("Bank changed to: " + str(bank_select + 1))
            else:
              self._quit = True
          messages = pedal.get("@MessageList")
          if messages == None:
            messages = []
          note_messages = self._set_note_velocity(pedal, status)
          messages = messages + note_messages
          if message != None:
            send_message = True
        elif self._xml_dict["@MidiEcho"]:
          messages = [message]
          send_message = True
      else:
        controller = message[1]
        if controller == self._xml_dict["@BankSelectController"]:
          select_value = message[2]
          if select_value < 124:
            if select_value >= len(self._xml_dict["Bank"]):
              select_value = len(self._xml_dict["Bank"]) - 1
            self._current_bank = select_value
            self.__log.info("Bank changed to: " + str(self._current_bank + 1))
          else:
            num_banks = len(self._xml_dict["Bank"])
            if select_value == 124:
              self._current_bank -= 1
            elif select_value == 125:
              self._current_bank += 1
            elif select_value == 126:
              self._current_bank = num_banks - 1
            else:
              self._quit = True
            if not self._quit:
              if self._current_bank < 0:
                self._current_bank = num_banks - 1
              elif self._current_bank >= num_banks:
                self._current_bank = 0
              self.__log.info("Bank changed to: " + str(self._current_bank + 1))
        elif self._xml_dict["@MidiEcho"]:
          messages = [message]
          send_message = True

    elif self._xml_dict["@MidiEcho"]:
      messages = [message]
      send_message = True
      
    if send_message:
      for message in messages:
        self._midi_out.send_message(message)

  def _set_note_velocity(self, pedal, message_type):
    """
    Returns a list of NOTE_ON or NOTE_OFF messages with a modified velocity
    according to the values of: BassPedalVelocity, ChordVelocity, and
    _current_velocity
    Parameters
    * Pedal: pedal for which the messages will be modified
    * message_type: it can be either NOTE_ON or NOTE_OFF
    """
    note_messages = pedal.get("@NoteMessages")
    if note_messages == None:
      return []
    
    note_messages = note_messages[message_type]
    pedal_velocity = pedal.get("@BassPedalVelocity")
    chord_velocity = pedal.get("@ChordVelocity")
    bass_note = pedal.get("@BassNote")
    message_index = 0
    if pedal_velocity == None:
      pedal_velocity = self._current_velocity
      if bass_note != None:
        note_messages[message_index][2] = pedal_velocity
        
    if bass_note != None:
      message_index += 1

    if chord_velocity == None:
      chord_velocity = self._current_velocity
      for i in range(message_index, len(note_messages)):
        note_messages[message_index][2] = chord_velocity
        message_index += 1
    return note_messages

  def _send_system_exclusive(self, message):
    """
    Overrides the _send_midi_message method from MidiInputHandler.
    """
    if not self._receive_sysex(message) and self._xml_dict["@MidiEcho"]:
      #This means that the end of the SysEx message (0xF7) was detected,
      #so, no further bytes will be received. Here the SysEx buffer will
      #be sent and afterwards cleared
      self._midi_out.send_message(self._sysex_buffer)
      #Clears SysEx buffer
      self._sysex_buffer = []
      #Resets SysEx count to zero
      self._sysex_chunk = 0

  def read_midi(self):
    """
    Main program loop.
    """
    self.__log.info("Waiting for MIDI messages")
    self.__log.info("Press CTRL+C to finish")
    try:
      while True and not self._quit:
        time.sleep(1)
    except KeyboardInterrupt:
      self.__log.info("Keyboard interrupt detected")
    except:
      error = traceback.format_exc()
      self.__log.info(error)