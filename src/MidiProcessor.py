#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v1.0
# File: src/MidiProcessor.py
# By:   Josef Meile <jmeile@hotmail.com> @ 10.04.2020
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
from MidiUtilities import calculate_base_note_octave, parse_note, \
                          read_text_file, multiple_split, is_valid_sysex, \
                          is_valid_midi_message, NOTE_SYMBOL_TO_MIDI, \
                          NOTE_VELOCITIES, FIRST_OCTAVE, LAST_OCTAVE, \
                          BANK_SELECT_FUNCTIONS, NOTE_TRIGGERS
from CustomLogger import CustomLogger, PrettyFormat
import logging
from autologging import logged
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_OFF, NOTE_ON,
                                  SYSTEM_EXCLUSIVE, END_OF_EXCLUSIVE)

#Creates a logger for this module.
logger = logging.getLogger(CustomLogger.get_module_name())

#Setups the logger with default settings
logger.setup()

#Register the logger with this class
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
    self.__log.debug("Initializing MidiProcessor")
    super().__init__(midi_in, midi_out, ignore_sysex, ignore_timing,
                     ignore_active_sense)
    self._xml_dict = xml_dict
    self._default_velocity = default_velocity
    self._quit = False
    self._status = None
    self._panic_command = []
    self._panic_pointer = -1
    self.__log.debug("MidiProcessor Initialized:\n%s",
                     PrettyFormat(self.__dict__))

  def parse_xml(self):
    """Parses the xml dict"""
    self.__log.debug("Parsing xml file")
    self._current_bank = self._xml_dict['@InitialBank'] - 1
    self._previous_pedal = None
    self.__log.info("Current Bank: %s", self._xml_dict['@InitialBank'])
    self._current_velocity = 0
    self._xml_dict["@BassPedalVelocity"], \
    self._xml_dict["@BassPedalVelocityRelative"] = \
      self._parse_velocity("BassPedalVelocity", self._xml_dict)
    self._xml_dict["@ChordVelocity"], \
    self._xml_dict["@ChordVelocityRelative"] = \
      self._parse_velocity("ChordVelocity", self._xml_dict)
    self._xml_dict["@BassPedalTranspose"] = self._parse_common_attribute(
                                              "BassPedalTranspose",
                                              self._xml_dict)

    if self._xml_dict["@BassPedalTranspose"] == None:
      self._xml_dict["@BassPedalTranspose"] = 0
                                              
    self._xml_dict["@ChordTranspose"] = self._parse_common_attribute(
                                          "ChordTranspose", self._xml_dict)

    self._xml_dict["@Octave"] = self._parse_common_attribute("Octave",
                                                             self._xml_dict)
    if self._xml_dict["@Octave"] == None:
      self._xml_dict["@Octave"] = 0

    #Internally midi channels begin with zero
    self._xml_dict['@InChannel'] -= 1
    self._xml_dict['@OutBassPedalChannel'] -= 1
    self._xml_dict['@OutChordChannel'] -= 1
    self._parse_banks()
    self._parse_start_stop("Start")
    self._parse_start_stop("Stop")
    self._parse_panic()
    self.__log.debug("Got:\n%s", PrettyFormat(self._xml_dict))
  
  def _parse_start_stop(self, node_name):
    """
    Parses the specified node
    Parameters:
    * node_name: node to parse; it can be either: "Start" or "Stop"
    """
    self.__log.debug("Parsing XML node: '%s'", node_name)
    node = self._xml_dict.get(node_name)
    if node != None:
      self._parse_messages(node, False)
    self.__log.debug("Node was parsed")
  
  def _parse_panic(self):
    """
    Parses the panic mode
    """
    self.__log.debug("Parsing XML node: Panic")
    node = self._xml_dict.get("Panic")
    if node != None:
      if type(node) == str:
        node_str = node
        command_file = None
      else:
        node_str = node.get('$')
        command_file = node.get('@File')
        
      commad_list = []
      if node_str != None:
        commad_list = self._parse_panic_string(node_str)
      
      if (commad_list != []) and command_file:
        message = "The Panic node only accepts either the inline command or a" \
                  " 'File' attribute, but not both"
        self.__log.debug(message)
        raise Exception(message)

      if (commad_list == []) and command_file:
        is_valid, command_str = read_text_file(command_file)
        if not is_valid:
          message = "Trouble accessing file: %s" % command_file
          self.__log.debug(message)
          raise Exception(message)
        commad_list = self._parse_panic_string(command_str)

      self._panic_command = commad_list
      if len(self._panic_command) > 0:
        self._panic_pointer = 0
      self.__log.debug("Got:\n%s", PrettyFormat(self._panic_command))
    self.__log.debug("Node was parsed")

  def _parse_panic_string(self, command_str):
    """
    Parses the entered command string and returns a list of MIDI or SysEx
    commands.
    """
    commad_list = multiple_split(command_str, '\r\n')
    panic_command = []
    for command in commad_list:
      stripped = command.strip()
      if not stripped.startswith('//') and stripped != '':
        if is_valid_midi_message(stripped) or is_valid_sysex(stripped):
          hex_strings = stripped.split(' ')
          hex_list = []
          for hex_string in hex_strings:
            hex_list.append(int(hex_string, 16))
          panic_command.append(hex_list)
        else:
          message = "Invalid MIDI or SysEx message: %s" % stripped
          self.__log.debug(message)
          raise Exception(message)
    return panic_command

  def _panic_in_progress(self, message):
    """
    Determines whether or not a panic message is in progress
    """
    continue_panic = False
    if self._panic_pointer >= 0:
      if self._panic_command[self._panic_pointer] == message:
        if self._panic_pointer == 0:
          self.__log.debug("Panic command was started")
        self.__log.debug("Sending panic message #%d", self._panic_pointer)
        continue_panic = True
        self._panic_pointer += 1
      else:
        if self._panic_pointer != 0:
          self.__log.debug("Panic command was terminated")
          self._panic_pointer = 0

      if self._panic_pointer >= len(self._panic_command):
        self.__log.debug("Panic command was fully sent")
        self._panic_pointer = 0
    return continue_panic

  def _parse_banks(self):
    """
    Parses the banks from the xml_dict
    """
    self.__log.debug("Parsing banks")
    bank_index = 0
    for bank in self._xml_dict['Bank']:
      self.__log.debug("Parsing bank: %d", bank_index + 1)
      bank["@BassPedalVelocity"], \
      bank["@BassPedalVelocityRelative"] = \
        self._parse_velocity("BassPedalVelocity", bank, self._xml_dict)
      bank["@ChordVelocity"], \
      bank["@ChordVelocityRelative"] = \
        self._parse_velocity("ChordVelocity", bank, self._xml_dict)
      bank["@BassPedalTranspose"] = self._parse_common_attribute(
                                      "BassPedalTranspose", bank,
                                      self._xml_dict)
      bank["@ChordTranspose"] = self._parse_common_attribute("ChordTranspose",
                                                               bank,
                                                               self._xml_dict)
                                                               
      bank["@Octave"] = self._parse_common_attribute("Octave", bank,
                                                     self._xml_dict)
      self._parse_pedals(bank, bank_index)
      self.__log.debug("Bank were parsed")
      bank_index += 1
    self.__log.debug("Banks were parsed")
  
  def _parse_pedals(self, parent_bank, bank_index):
    """
     Parses the pedals from the current bank
     Parameters:
     * parent_bank: bank on which this pedal is contained
     * bank_index: index of the bank inside the controller node (begins with
       zero)
    """
    self.__log.debug("Parsing pedals")
    pedal_list = {}
    pedal_index = 0
    for pedal in parent_bank['Pedal']:
      self.__log.debug("Parsing pedal: %d", pedal_index + 1)
      pedal["@BassPedalVelocity"], \
      pedal["@BassPedalVelocityRelative"] = \
        self._parse_velocity("BassPedalVelocity", pedal, parent_bank)
      pedal["@ChordVelocity"], \
      pedal["@ChordVelocityRelative"] = \
        self._parse_velocity("ChordVelocity", pedal, parent_bank)
      pedal["@BassPedalTranspose"] = self._parse_common_attribute(
                                       "BassPedalTranspose", pedal, parent_bank)
      pedal["@ChordTranspose"] = self._parse_common_attribute(
                                   "ChordTranspose", pedal, parent_bank)
                                   
      pedal["@Octave"] = self._parse_common_attribute("Octave", pedal,
                                                      parent_bank)

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
        elif bank_select == "Next":
          bank_select = bank_index + 1
        elif bank_select == "Previous":
          bank_select = bank_index - 1
        elif bank_select == "Last":
          bank_select = num_banks - 1
          
        if isinstance(bank_select, int):
          if (bank_select >= num_banks) and fix_bank:
            bank_select = 0
          elif bank_select < 0:
            bank_select = num_banks - 1
          elif bank_select >= num_banks:
            raise Exception("Bank number: " + str(bank_select + 1) + " On "
                            "BankSelect is out of range. Maximum: " + \
                            str(num_banks))
      pedal["@BankSelect"] = bank_select
      pedal_index += 1
      self.__log.debug("Pedal was parsed")
    parent_bank["@PedalList"] = pedal_list
    self.__log.debug("Pedals were parsed")

  def _parse_messages(self, xml_node, filter_by_trigger = True):
    """
    Parses the messages for the specified xml_node, which can be either a pedal,
    the start, or stop node.
    Parameters:
    * xml_node: xml values to parse
    * filter_by_trigger: either to group the messages by trigger or not. It
      defaults to True.
    """
    self.__log.debug("Parsing node messages and filtering by trigger: %s",
                     filter_by_trigger)
    messages = xml_node.get('Message')
    if messages != None:
      if filter_by_trigger:
        message_list = {'NoteOn': [], 'NoteOff': []}
      else:
        message_list = []
      for full_message in messages:
        trigger = full_message["@Trigger"]
        message_string = full_message["@String"]
        hexadecimal_strings = message_string.split(' ')
        hexadecimal_message = []
        for hexadecimal_string in hexadecimal_strings:
          hexadecimal_message.append(int(hexadecimal_string, 16))
        if filter_by_trigger:
          message_list[trigger].append(hexadecimal_message)
        else:
          message_list.append(hexadecimal_message)
      xml_node["@MessageList"] = message_list
    self.__log.debug("Messages were parsed")

  def _parse_chords(self, pedal):
    """
    Parses the given chord notes an converts them to MIDI notes
    """
    self.__log.debug("Parsing chords")
    chord_notes = pedal.get("@ChordNotes")
    if chord_notes != None:
      chord_note_list = chord_notes.split(',')
      bass_note = pedal.get("@BassNote")
      chord_transpose = pedal.get("@ChordTranspose")
      if chord_transpose == None:
        if bass_note != None:
          chord_transpose = pedal.get("@BassPedalTranspose")
        else:
          chord_transpose = 0

      numeric_list = chord_note_list[0].isdigit()
      if not numeric_list:
        #You need to have an octave reference when giving note symbols. If you
        #give note numbers, then you already know their octaves
        octave = pedal.get("@BassOctave")
        if octave == None:
          octave = pedal.get("@Octave")

      note_velocity = pedal["@ChordVelocity"]
      base_note = None
      note_messages = pedal.get("@NoteMessages")
      if note_messages == None:
        note_messages = {NOTE_ON: [], NOTE_OFF: []}
      midi_channel = self._xml_dict["@OutChordChannel"]
      note_index = 0
      for chord_note in chord_note_list:
        previous_note = base_note
        if not numeric_list:
          base_note = NOTE_SYMBOL_TO_MIDI[chord_note]
        else:
          base_note, octave = calculate_base_note_octave(int(chord_note))
        if (note_index != 0) and (base_note < previous_note) and \
           (not numeric_list):
          octave += 1

        note, chord_octave = parse_note(chord_note, octave, chord_transpose)

        self._set_note_messages(note_messages, note, midi_channel,
                                note_velocity)
        if note_index == 0:
          pedal["@ChordOctave"] = chord_octave
        
        chord_note_list[note_index] = note
        note_index += 1
      chord_notes = chord_note_list
      pedal["@NoteMessages"] = note_messages    
    pedal["@ChordNotes"] = chord_notes
    self.__log.debug("Chords were parsed")

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
    self.__log.debug("Setting note messages")
    if velocity == None:
      velocity = self._default_velocity

    for message_type in [NOTE_ON, NOTE_OFF]:
      header = message_type | midi_channel
      note_messages[message_type].append([header, note, velocity])
    self.__log.debug("Note messages were set")

  def _parse_notes(self, pedal, pedal_list):
    """
    Parses the set notes in the xml_dict. It will transpose them according to
    the given parameters.
    Parameters
    * pedal: pedal for which the notes are going to be calculated
    * pedal_list: after having calculated notes, pedals will be indexed by pedal
      note
    """
    self.__log.debug("Parsing notes")
    note = pedal.get('@Note')
    octave = pedal.get('@Octave')
    pedal['@Note'], pedal['@Octave'] = parse_note(note, octave)
    pedal_list[pedal['@Note']] = pedal
      
    note = pedal.get("@BassNote")
    if note != None:
      note, octave = parse_note(note, pedal['@Octave'],
                                pedal["@BassPedalTranspose"])
      pedal["@BassOctave"] = octave
      note_messages = {NOTE_ON: [], NOTE_OFF: []}
      pedal_channel = self._xml_dict["@OutBassPedalChannel"]
      pedal_velocity = pedal["@BassPedalVelocity"]
      self._set_note_messages(note_messages, note, pedal_channel,
                              pedal_velocity)
      pedal["@NoteMessages"] = note_messages

    pedal["@BassNote"] = note
    self.__log.debug("Note were set")

  def _parse_common_attribute(self, attribute_name, current_node,
                              parent_node = None):
    """
    Gets the specified attribute_name from the xml_dict and converts it to its
    numeric representation
    Parameters:
    * attribute_name: name of the attribute to retreive. It can be either:
      BassPedalTranspose, ChordTranspose, or Octave
    * current_node: current note to parse
    * parent_node: reference to the parent node
    Returns:
    * If the specified attribute is not None for the current_node, then returns
      its value; otherwise, the value of the parent node will be returned. If
      there is no parent node, then the attribute_name from xml_dict will be
      returned.
    """
    self.__log.debug("Parsing common XML attributes")
    attribute_value = current_node.get('@' + attribute_name)
    if attribute_value != None:
      return attribute_value

    if parent_node == None:
      return self._xml_dict.get('@' + attribute_name)
    self.__log.debug("Common XML attributes were parsed")
    return self._parse_common_attribute(attribute_name, parent_node)

  def _parse_velocity(self, attribute_name, current_node, parent_node = None):
    """
    Gets the specified attribute_name from the xml_dict and converts it to its
    numeric representation
    Parameters:
    * attribute_name: name of the attribute to retreive. It can be either:
      BassPedalVelocity or ChordVelocity
    * current_node: current note to parse
    * parent_node: reference to the parent node
    Returns:
    * A tuple containing the following:
      - first element: velocity numeric value. It can be a number between -127
        and 127
      - second element: either if this is an absolute or relative velocity
    """
    self.__log.debug("Parsing velocity XML attributes")
    attribute_value = current_node.get('@' + attribute_name)
    is_relative = current_node.get('@' + attribute_name + 'Relative', False)
    if attribute_value != None:
      if not isinstance(attribute_value, int):
        if attribute_value[0] in ['-', '+']:
          is_relative = True
          attribute_value = int(attribute_value)
        elif attribute_value.isdigit():
          attribute_value = int(attribute_value)
        else:
          attribute_value = NOTE_VELOCITIES[attribute_value]
      
      if not is_relative:
        return attribute_value, False
    else:
      attribute_value = 0
      is_relative = True

    parent_velocity = 0
    is_parent_relative = True
    if (parent_node == None) and (current_node != self._xml_dict):
      parent_velocity = self._xml_dict.get('@' + attribute_name)
      is_parent_relative = self._xml_dict.get('@' + attribute_name + 'Relative')
    elif parent_node != None:
      parent_velocity, is_parent_relative = \
        self._parse_velocity(attribute_name, parent_node)

    attribute_value = attribute_value + parent_velocity
    if not is_parent_relative:
      if attribute_value > 127:
        attribute_value = 127
      elif attribute_value < 0:
        attribute_value = 0
      is_relative = False

    self.__log.debug("Common XML attributes were parsed")
    return attribute_value, is_relative

  def _send_midi_message(self, message):
    """
    Overrides the _send_midi_message method from MidiInputHandler.
    """
    self.__log.debug("Sending MIDI message: %s", PrettyFormat(message))
    messages = []
    if not self._panic_in_progress(message):
      status = message[0] & 0xF0
      channel = message[0] & 0x0F
      if (self._xml_dict['@InChannel'] == channel) and \
         status in [NOTE_ON, NOTE_OFF, CONTROL_CHANGE]:
        current_bank = self._xml_dict['Bank'][self._current_bank]
        if status in [NOTE_ON, NOTE_OFF]:
          note = message[1]
          current_pedal = current_bank["@PedalList"].get(note)
          if current_pedal != None:
            self._current_velocity = message[2]
            if (self._current_velocity == 0) and \
               (self._xml_dict["@MinVelocityNoteOff"]):
               #NOTE_ON with a zero velocity will be interpreted as NOTE_OFF
               status = NOTE_OFF

            #First the NOTE ON AND OFF messages will be done
            note_messages = self._set_note_velocity(current_pedal, status)
            messages += note_messages
            if (self._xml_dict["@PedalMonophony"]) and \
               (self._previous_pedal != None):
              #Only one pedal at the time is allowed and a pedal was already
              #pushed or released
              if (status == NOTE_ON):
                #This means that a previous pedal was pushed, so the NOTE OFF
                #messages for that pedal will be sent first
                note_messages = self._set_note_velocity(self._previous_pedal,
                                                        NOTE_OFF)
                messages = note_messages + messages
                self._previous_pedal = current_pedal
              elif current_pedal != self._previous_pedal:
                #This means that the released pedal is not the same as the one
                #that was pushed before, so, nothing will be done
                messages = []
              else:
                #We reset the previous pedal to None
                self._previous_pedal = None
            elif (self._previous_pedal == None) and (status == NOTE_ON):
              self._previous_pedal = current_pedal


            midi_and_sysex = current_pedal.get("@MessageList")
            if midi_and_sysex != None:
              #First the MIDI and SysEx messages will be sent
              messages += midi_and_sysex[NOTE_TRIGGERS[status]]

            if status == NOTE_OFF:
              #The BANK SELECT messages will be processed only on NOTE OFF
              bank_select = current_pedal.get("@BankSelect")
              if bank_select != None:
                #Now the BANK SELECT message will be processed
                if bank_select not in ["Panic", "Quit", "Reload", "Reboot", \
                                       "Shutdown"]:
                  self._current_bank = bank_select
                  self.__log.info("Bank changed to: %d", bank_select + 1)
                elif bank_select != "Panic":
                  self._quit = True
                  self._status = bank_select
                else:
                  messages = self._panic_command
                  self.__log.debug("Sending software Panic:\n%s", \
                                   PrettyFormat(self._panic_command))
          elif self._xml_dict["@MidiEcho"]:
            #This is an unregistered note, so fordward it whatever it is
            messages = [message]
        else:
          #Here it is a CONTROL CHANGE message.
          controller = message[1]
          if controller == self._xml_dict["@BankSelectController"]:
            #If it is the BankSelectController, then the respective BANK SELECT
            #message will be excecuted
            select_value = message[2]
            if select_value < 120:
              if select_value >= len(self._xml_dict["Bank"]):
                select_value = len(self._xml_dict["Bank"]) - 1
              self._current_bank = select_value
              self.__log.info("Bank changed to: %d", self._current_bank + 1)
            else:
              send_panic = False
              num_banks = len(self._xml_dict["Bank"])
              if select_value == 120:
                self._current_bank -= 1
              elif select_value == 121:
                self._current_bank += 1
              elif select_value == 122:
                self._current_bank = num_banks - 1
              elif select_value == 123:
                send_panic = True
                messages = self._panic_command
                self.__log.debug("Sending software Panic:\n%s", \
                                 PrettyFormat(self._panic_command))
              else:
                self._quit = True
                self._status = BANK_SELECT_FUNCTIONS[select_value]
              if not self._quit and not send_panic:
                if self._current_bank < 0:
                  self._current_bank = num_banks - 1
                elif self._current_bank >= num_banks:
                  self._current_bank = 0
                self.__log.info("Bank changed to: %d", self._current_bank + 1)
          elif self._xml_dict["@MidiEcho"]:
            #This is another CONTROL CHANGE message, so it will be fordwarded
            messages = [message]
      elif self._xml_dict["@MidiEcho"]:
        #Fordward the message whatever it is
        messages = [message]

      if self._quit and (self._previous_pedal != None):
        #Before quitting, the NOTE OFF for the previous pedal need to be
        #sent
        note_messages = self._set_note_velocity(self._previous_pedal,
                                                NOTE_OFF)
        messages += note_messages
    else:
      messages.append(message)

    if messages != []:
      for message in messages:
        self._midi_out.send_message(message)
    self.__log.debug("MIDI message was sent")

  def _set_note_velocity(self, pedal, message_type):
    """
    Returns a list of NOTE_ON or NOTE_OFF messages with a modified velocity
    according to the values of: BassPedalVelocity, ChordVelocity, and
    _current_velocity
    Parameters
    * Pedal: pedal for which the messages will be modified
    * message_type: it can be either NOTE_ON or NOTE_OFF
    """
    self.__log.debug("Sending note velocity for message: %s", message_type)
    note_messages = pedal.get("@NoteMessages")
    if note_messages == None:
      return []
    
    note_messages = note_messages[message_type]
    pedal_velocity = pedal.get("@BassPedalVelocity")
    is_pedal_velocity_relative = pedal.get("@BassPedalVelocityRelative")
    chord_velocity = pedal.get("@ChordVelocity")
    is_chord_velocity_relative = pedal.get("@ChordVelocityRelative")
    bass_note = pedal.get("@BassNote")
    message_index = 0
    if is_pedal_velocity_relative:
      pedal_velocity += self._current_velocity
      if pedal_velocity <= 0:
        pedal_velocity = 1
        self.__log.info("Pedal velocity was justed to 1. Please increase the "
                        "relative velocity")
      elif pedal_velocity > 127:
        pedal_velocity = 127
        self.__log.info("Pedal velocity was justed to 127. Please decrease the "
                        "relative velocity")
      if bass_note != None:
        note_messages[message_index][2] = pedal_velocity
        
    if bass_note != None:
      message_index += 1

    if is_chord_velocity_relative:
      chord_velocity += self._current_velocity
      if chord_velocity <= 0:
        chord_velocity = 1
        self.__log.info("Chord velocity was justed to 1. Please increase the "
                        "relative velocity")
      elif chord_velocity > 127:
        chord_velocity = 127
        self.__log.info("Pedal velocity was justed to 127. Please decrease the "
                        "relative velocity")
      for i in range(message_index, len(note_messages)):
        note_messages[message_index][2] = chord_velocity
        message_index += 1
    self.__log.debug("Note velocity was set")
    return note_messages

  def _send_system_exclusive(self, message):
    """
    Overrides the _send_midi_message method from MidiInputHandler.
    """
    self.__log.debug("Sending SysEx message: %s", PrettyFormat(message))
    if not self._receive_sysex(message) and self._xml_dict["@MidiEcho"]:
      #This means that the end of the SysEx message (0xF7) was detected,
      #so, no further bytes will be received. Here the SysEx buffer will
      #be sent and afterwards cleared
      self._midi_out.send_message(self._sysex_buffer)
      #Clears SysEx buffer
      self._sysex_buffer = []
      #Resets SysEx count to zero
      self._sysex_chunk = 0
    self.__log.debug("SysEx was sent")

  def _process_start_stop_messages(self, node_name):
    """
    Sends the messages from the specified node
    Parameters:
    * node_name: name of the node to process; it can be either: "Start" or
      "Stop"
    """
    self.__log.debug("Processing messages for node: %s", node_name)
    node = self._xml_dict.get(node_name)
    if node != None:
      message_list = node["@MessageList"]
      if message_list != None:
        xml_messages = node["Message"]
        for i in range(0, len(message_list)):
          if xml_messages[i]['@Type'] == "Midi":
            self._send_midi_message(message_list[i])
          else:
            self._send_system_exclusive(message_list[i])
    self.__log.debug("Messages were processed")

  def read_midi(self):
    """
    Main program loop.
    """
    self.__log.info("Waiting for MIDI messages")
    self.__log.info("Press CTRL+C to finish")
    try:
      self._process_start_stop_messages("Start")
      while True and not self._quit:
        time.sleep(1)
      self._process_start_stop_messages("Stop")
      return self._status
    except KeyboardInterrupt:
      self.__log.info("Keyboard interrupt detected")
      self._process_start_stop_messages("Stop")
    except:
      error = traceback.format_exc()
      self.__log.info(error)
    return False
