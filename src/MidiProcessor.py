#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v1.5
# File: src/MidiProcessor.py
# By:   Josef Meile <jmeile@hotmail.com> @ 28.07.2020
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
                          is_valid_sysex, is_valid_midi_message, \
                          NOTE_SYMBOL_TO_MIDI, NOTE_VELOCITIES, FIRST_OCTAVE, \
                          LAST_OCTAVE, BANK_SELECT_FUNCTIONS, NOTE_TRIGGERS
from StringUtilities import read_text_file, multiple_split
from ByteUtilities import convert_unicode_to_7_bit_bytes, \
                          convert_byte_array_to_list
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
    self.__log.debug("Initializing MidiProcessor")
    super().__init__(midi_in, midi_out, ignore_sysex, ignore_timing,
                     ignore_active_sense)
    self._xml_dict = xml_dict
    self._quit = False
    self._status = None
    self._panic_command = []
    self._send_bank_names = "F0 7D 00 "
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
    self._parse_out_channels('BassPedal', self._xml_dict)
    self._parse_out_channels('Chord', self._xml_dict)
    self._parse_velocity_transpose("BassPedal", "Velocity", self._xml_dict)
    self._parse_velocity_transpose("Chord", "Velocity", self._xml_dict)
    self._parse_velocity_transpose("BassPedal", "Transpose", self._xml_dict)
    self._parse_velocity_transpose("Chord", "Transpose", self._xml_dict)
    self._parse_octave(self._xml_dict)
    if self._xml_dict["@Octave"] == None:
      self._xml_dict["@Octave"] = 0

    #Internally midi channels begin with zero
    self._xml_dict['@InChannel'] -= 1
    self._parse_panic()
    self._parse_banks()
    self._parse_start_stop("Start")
    self._parse_start_stop("Stop")
    #self._parse_panic()
    self.__log.debug("Got:\n%s", PrettyFormat(self._xml_dict))

  def _parse_out_channels(self, channel_name, current_node, parent_node = None):
    """
    Converts the string comma separated list channel numbers to a python list
    Parameters:
    * channel_name: Name of the channel to parse. It can be either: 'BassPedal'
      or 'Chord'
    * current_node: Node that is being currently parsed
    * parent_node: Parent of current_node
    """
    attribute_name = "@Out%sChannel" % channel_name
    attribute_values = current_node.get(attribute_name)
    if (attribute_values == None) and (parent_node != None):
      attribute_values = parent_node.get(attribute_name)

    if attribute_values == None:
      attribute_values = [0]
    
    if type(attribute_values) != type([]):
      attribute_values = attribute_values.split(',')
      attribute_list = []
      for attribute_value in attribute_values:
        #Logically channels begin at 1; however on real MIDI, they start at 0
        attribute_list.append(int(attribute_value) - 1)
      attribute_values = attribute_list

    current_node[attribute_name] = attribute_values

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
    encoding = self._xml_dict.get("@Encoding")
    total_byte_sum = 0
    banks_sysex = [0xF0, 0x7D, 0x00]
    for bank in self._xml_dict['Bank']:
      self.__log.debug("Parsing bank: %d", bank_index)
      bank_name = bank.get('@Name', None)
      if bank_name in [None, '']:
        bank_name = 'Bank' + str(bank_index)
        bank["@Name"] = bank_name
      
      bank_name_bytes = convert_unicode_to_7_bit_bytes(bank_name, \
                                                       encoding = encoding)
      bank_name_sysex, bank_name_lengths, bank_name_sum = \
        convert_byte_array_to_list(bank_name_bytes)
      total_byte_sum += bank_name_sum
      banks_sysex += bank_name_lengths + bank_name_sysex
      self._parse_out_channels('BassPedal', bank, self._xml_dict)
      self._parse_out_channels('Chord', bank, self._xml_dict)
      self._parse_velocity_transpose("BassPedal", "Velocity", bank, 
                                     self._xml_dict)
      self._parse_velocity_transpose("Chord", "Velocity", bank, self._xml_dict)
      self._parse_velocity_transpose("BassPedal", "Transpose", bank, 
                                     self._xml_dict)
      self._parse_velocity_transpose("Chord", "Transpose", bank, self._xml_dict)

      self._parse_octave(bank, self._xml_dict)
      self._parse_pedals(bank, bank_index)
      self.__log.debug("Bank were parsed")
      bank_index += 1
      
    checksum = 128 - (total_byte_sum % 128)
    banks_sysex += [checksum, 0xF7]
    self._xml_dict["@BanksSysEx"] = banks_sysex
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
      
      self._parse_out_channels('BassPedal', pedal, parent_bank)
      self._parse_out_channels('Chord', pedal, parent_bank)
      self._parse_velocity_transpose("BassPedal", "Velocity", pedal, 
                                     parent_bank)
      self._parse_velocity_transpose("Chord", "Velocity", pedal, parent_bank)
      self._parse_velocity_transpose("BassPedal", "Transpose", pedal,
                                     parent_bank)
      self._parse_velocity_transpose("Chord", "Transpose", pedal, parent_bank)
                                   
      self._parse_octave(pedal, parent_bank)

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

    if filter_by_trigger:
      send_panic = xml_node.get('@SendPanic')
      if send_panic:
        self.__log.debug("SendPanic was detected. Appending panic command ")
        message_list = xml_node.get("@MessageList")
        if message_list == None:
          message_list = {'NoteOff': []}
          xml_node["@MessageList"] = message_list

        message_list['NoteOff'].extend(self._panic_command)

    self.__log.debug("Messages were parsed")

  def _parse_chords(self, pedal):
    """
    Parses the given chord notes an converts them to MIDI notes
    """
    self.__log.debug("Parsing chords")
    chord_notes = pedal.get("@ChordNotes")
    if chord_notes != None:
      chord_note_list = chord_notes.split(',')
      chord_transpose = pedal.get("@ChordTranspose")
      numeric_list = chord_note_list[0].isdigit()
      octave = None
      if not numeric_list:
        #You need to have an octave reference when giving note symbols. If you
        #give note numbers, then you already know their octaves
        octave = pedal.get("@Octave")

      note_velocity = pedal["@ChordVelocity"]
      base_note = None
      note_messages = pedal.get("@NoteMessages")
      if note_messages == None:
        note_messages = {NOTE_ON: [], NOTE_OFF: []}
      midi_channel = pedal["@OutChordChannel"]
      note_index = 0
      for chord_note in chord_note_list:
        previous_note = base_note
        if not numeric_list:
          base_note = NOTE_SYMBOL_TO_MIDI[chord_note]
          if (note_index != 0) and (base_note < previous_note) and \
            (not numeric_list):
            octave += 1
        notes = parse_note(chord_note, octave, chord_transpose)
        self._set_note_messages(note_messages, notes, midi_channel,
                                note_velocity)
        
        chord_note_list[note_index] = notes
        note_index += 1
      chord_notes = chord_note_list
      pedal["@NoteMessages"] = note_messages    
    pedal["@ChordNotes"] = chord_notes
    self.__log.debug("Chords were parsed")

  def _set_note_messages(self, note_messages, notes, midi_channels,
                         velocities):
    """
    Sets the NOTE_ON and NOTE_OFF messages for the specified parameters
    Parameters:
    * note_messages: dictionary with two lists: NOTE_ON and NOTE_OFF
    * notes: notes that will be used for the messages
    * midi_channels: MIDI channels that will be set. It is a list with numbers
      between 0 and 15
    * velocity: velocities for the resultant notes. It must be a list with
      numbers between 0 and 127
    Returns:
    * note_messages will be returned with the new note messages
    """
    self.__log.debug("Setting note messages")

    for message_type in [NOTE_ON, NOTE_OFF]:
      note_index = 0
      while note_index < len(notes):
        header = message_type | midi_channels[note_index]
        note_messages[message_type].append([header, notes[note_index], 
                                           velocities[note_index]])
        note_index += 1
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
    notes = parse_note(note, octave)
    pedal['@Note'] = notes[0]
    pedal_list[pedal['@Note']] = pedal
    
    note = pedal.get("@BassNote")
    notes = None
    if note != None:
      notes = parse_note(note, octave, pedal["@BassPedalTranspose"])
      note_messages = {NOTE_ON: [], NOTE_OFF: []}
      pedal_channel = pedal["@OutBassPedalChannel"]
      pedal_velocity = pedal["@BassPedalVelocity"]
      self._set_note_messages(note_messages, notes, pedal_channel,
                              pedal_velocity)
      pedal["@NoteMessages"] = note_messages

    pedal["@BassNote"] = notes
    self.__log.debug("Note were set")

  def _parse_octave(self, current_node, parent_node = None):
    """
    Gets the Octave attribute from the xml_dict
    Parameters:
    * current_node: current note to parse
    * parent_node: reference to the parent node
    """
    self.__log.debug("Parsing Octave attribute")
    attribute_value = current_node.get('@Octave')
    if (attribute_value == None) and (parent_node != None):
      attribute_value = parent_node.get('@Octave')

    if attribute_value == None:
       attribute_value = 0

    current_node['@Octave'] = attribute_value

  def _parse_velocity_transpose(self, attribute_name, attribute_suffix,
                                current_node, parent_node = None):
    """
    Gets the specified attribute_name from the xml_dict and converts it a python
    list
    Parameters:
    * attribute_name: name of the attribute to retreive. It can be either:
      BassPedal or Chord
    * attribute_suffix: suffix for the attribute. It can ve either: Velocity or
      Transpose
    * current_node: current note to parse
    * parent_node: reference to the parent node
    """
    attribute_fullname = "@%s%s" % (attribute_name, attribute_suffix)
    self.__log.debug("Parsing %s attribute" % attribute_fullname)
    
    attribute_values = current_node.get(attribute_fullname)
    out_channels = current_node.get('@Out%sChannel' % attribute_name)
    if attribute_values != None:
      attribute_values = attribute_values.split(',')
    elif (attribute_values == None) and (parent_node != None):
      attribute_values = parent_node.get(attribute_fullname)
      
    if attribute_values == None:
      zero_value = "0"
      if attribute_suffix == "Velocity":
        zero_value = "+0"
      attribute_values = (zero_value + ',') * len(out_channels)
      attribute_values = attribute_values.split(',')[:-1]

    if len(attribute_values) > len(out_channels):
      raise Exception("%s list must be smaller than the output channels.\n"
                      "Output channels: %s\n"
                      "Values: %s" % (attribute_fullname, \
                                      str(out_channels), \
                                      str(attribute_values)))
    value_list = []
    for attribute_value in attribute_values:
      final_value = attribute_value
      is_number = False
      if type(attribute_value) == type(''):
        is_number = attribute_value.isdigit()
      else:
        is_number = True
      if not is_number and (attribute_value[0] not in ['+', '-']):
        final_value = NOTE_VELOCITIES[final_value]
      elif is_number:
        final_value = int(final_value)

      value_list.append(final_value)
    
    last_value = value_list[-1]
    current_value = len(value_list)
    while current_value < len(out_channels):
      value_list.append(last_value)
      current_value += 1
    current_node[attribute_fullname] = value_list

  def _send_midi_message(self, message):
    """
    Overrides the _send_midi_message method from MidiInputHandler.
    """
    self.__log.debug("Processing MIDI message: %s", PrettyFormat(message))
    messages = []
    if not self._panic_in_progress(message):
      status = message[0] & 0xF0
      channel = message[0] & 0x0F
      if (self._xml_dict['@InChannel'] == channel) and \
         status in [NOTE_ON, NOTE_OFF, CONTROL_CHANGE]:
        current_bank = self._xml_dict['Bank'][self._current_bank]
        if status in [NOTE_ON, NOTE_OFF]:
          swapped_note_message = False
          note = message[1]
          current_pedal = current_bank["@PedalList"].get(note)
          if current_pedal != None:
            self.__log.debug("Controller message was detected")
            self._current_velocity = message[2]
            if (self._current_velocity == 0) and \
               (self._xml_dict["@MinVelocityNoteOff"]):
               self.__log.debug("Swapping NOTE ON message with a zero velocity "
                                "to a NOTE OFF message")
               swapped_note_message = True
               #NOTE_ON with a zero velocity will be interpreted as NOTE_OFF
               status = NOTE_OFF

            #First the NOTE ON AND OFF messages will be done
            note_messages = self._set_note_velocity(current_pedal, status,
                                                    swapped_note_message)
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
              self.__log.debug(NOTE_TRIGGERS[status])
              #First the MIDI and SysEx messages will be sent
              if NOTE_TRIGGERS[status] in midi_and_sysex:
                self.__log.debug("Got messages")
                messages += midi_and_sysex[NOTE_TRIGGERS[status]]

            if status == NOTE_OFF:
              #The BANK SELECT messages will be processed only on NOTE OFF
              bank_select = current_pedal.get("@BankSelect")
              if bank_select != None:
                #Now the BANK SELECT message will be processed
                if bank_select not in ["Quit", "Reload", "Reboot", "Shutdown", \
                                       "List"]:
                  self._current_bank = bank_select
                  self.__log.info("Bank changed to: %d", bank_select + 1)
                elif bank_select == "List":
                  messages = [self._xml_dict["@BanksSysEx"]]
                else:
                  self._quit = True
                  self._status = bank_select
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
            if select_value < 119:
              if select_value >= len(self._xml_dict["Bank"]):
                select_value = len(self._xml_dict["Bank"]) - 1
              self._current_bank = select_value
              self.__log.info("Bank changed to: %d", self._current_bank + 1)
            else:
              send_panic = False
              send_bank_list = False
              num_banks = len(self._xml_dict["Bank"])
              if select_value == 119:
                messages = [self._xml_dict["@BanksSysEx"]]
                send_bank_list = True
              elif select_value == 120:
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
              if not self._quit and not send_bank_list:
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
        self.__log.debug("Sending MIDI message: %s", PrettyFormat(message))
        self._midi_out.send_message(message)
    self.__log.debug("MIDI message was processed")

  def _set_note_velocity(self, pedal, message_type,
                         swapped_note_message = False):
    """
    Returns a list of NOTE_ON or NOTE_OFF messages with a modified velocity
    according to the values of: BassPedalVelocity, ChordVelocity, and
    _current_velocity
    Parameters
    * Pedal: pedal for which the messages will be modified
    * message_type: it can be either NOTE_ON or NOTE_OFF
    * swapped_note_message: indicates whether or not this a NOTE ON with a
      velocity of zero, which was changed to NOTE OFF. This is the only case
      where the velocity won't be changed and will be let as zero. Please note
      that for normal NOTE OFF message the velocity won't be always zero; some
      MIDI devices support NOTE OFF messages with a velocity.
    """
    self.__log.debug("Setting note velocity for message: %s", message_type)
    note_messages = pedal.get("@NoteMessages")
    if note_messages == None:
      return []
    
    note_messages = note_messages[message_type]
    new_note_messages = []
    for note_message in note_messages:
      note_velocity = note_message[2]
      if swapped_note_message:
        note_velocity = 0
      else:
        if type(note_velocity) == type(''):
          note_velocity = self._current_velocity + int(note_velocity)
        
        if note_velocity <= 0:
          note_velocity = 1
          self.__log.info("Pedal velocity was justed to 1. Please increase the "
                          "relative velocity")
        elif note_velocity > 127:
          note_velocity = 127
          self.__log.info("Pedal velocity was justed to 127. Please decrease the "
                          "relative velocity")
      new_note_message = note_message[:]
      new_note_message[2] = note_velocity
      new_note_messages.append(new_note_message)
    return new_note_messages

  def _send_system_exclusive(self, message):
    """
    Overrides the _send_system_exclusive method from MidiInputHandler.
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