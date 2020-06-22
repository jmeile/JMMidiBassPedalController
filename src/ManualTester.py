#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v1.3
# File: src/ManualTester.py
# By:   Josef Meile <jmeile@hotmail.com> @ 21.06.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""Manually tests the pedal configuration by sending MIDI messages."""

from __future__ import print_function
import traceback
from CustomLogger import CustomLogger, PrettyFormat
import logging
from autologging import logged
import time
from rtmidi.midiconstants import CONTROL_CHANGE, NOTE_OFF, NOTE_ON, \
                                 SYSTEM_EXCLUSIVE
from rtmidi.midiutil import open_midioutput, open_midiinput
from MidiUtilities import get_velocity_symbol, calculate_base_note_octave, \
                          parse_note, is_valid_midi_message, is_valid_sysex, \
                          NOTE_MIDI_TO_SYMBOL, NOTE_SYMBOL_TO_MIDI, \
                          FIRST_OCTAVE, LAST_OCTAVE
from MidiInputHandler import MidiInputHandler
from ByteUtilities import convert_unicode_from_7_bit_bytes

#By default, file logging is enabled
file_log_level = logging.DEBUG
  
#Disable file logging as follows:
#file_log_level = logging.NOTSET
  
CustomLogger.init_logging(file_log_level = file_log_level)

#Creates a logger for this module.
logger = logging.getLogger(CustomLogger.get_module_name())

#Setups the logger with the standard settings
logger.setup()

#Register the logger with this class
@logged(logger)
class MyMidiInputHandler(MidiInputHandler):
  """
  Subclass from MidiInputHandler. Here you should only refefine the methods
  you want to modify, ie: _on_note_on. Never overwrite __init__ or
  __call__. If you want to overwrite __init__, then make sure that you
  also call the superclass method
  """
  
  def __init__(self, midi_in, midi_out, midi_in_channel, bank_controller,
               note_velocity):
    """
    Initializes the class attributes
    Parameters:
    * midi_in: MIDI IN interface to use
    * midi_out: MIDI OUT interface to use. If None, then the messages will be
      printed into the console
    * midi_in_channel: MIDI IN channel used by the controller for listening to
      messages
    * bank_controller: Controller used to change banks
    * note_velocity: default note velocity to send
    """
    super().__init__(midi_in, midi_out, ignore_sysex = False,
                     ignore_timing = False, ignore_active_sense = False,
                     console_echo = True)
    self._midi_in_channel = midi_in_channel
    self._bank_controller = controller
    self._note_velocity = note_velocity
    self._got_answer = False
  
  def _send_midi_message(self, message):
    """
    Overrides the default _send_midi_message. We don't need to send the message
    it will be only printed.
    """
    self._print_message(message, "Answer")
    self._got_answer = True
  
  def _handle_note(self, message):
    """
    Handles NOTE ON and OFF messages
    Parameters:
    * message: full MIDI message
    """
    self._print_message(message, "Answer")
    self._got_answer = True

  def _print_message(self, message, operation):
    """
    Given a raw MIDI message, it transforms it to a human readable
    representation
    Parameters:
    * message: Raw MIDI message to transform
    * operation: it is either: "Answer" or "Sending"
    """
    status = message[0] & 0xF0
    if status == 0xF0:
      status = message[0]

    message_type = self._midi_messages[status]
    channel = message[0] & 0x0F
    message_string = \
        '[{}]'.format(' '.join(hex(x).lstrip("0x").upper().zfill(2)
        for x in message))
    if status in [NOTE_ON, NOTE_OFF]:
      note = message[1]
      base_note, octave = calculate_base_note_octave(note)
      note_symbol = NOTE_MIDI_TO_SYMBOL[base_note] + str(octave)
      velocity = message[2]
      velocity_symbol = get_velocity_symbol(velocity)
      self.__log.info("%s: %s at channel: %d - Note: %d(%s), Velocity: "
                      "%d(%s), Raw MIDI: %s", operation, message_type,
                      channel + 1, note, note_symbol, velocity, velocity_symbol,
                      message_string)
    elif status != SYSTEM_EXCLUSIVE:
      self.__log.info("%s: %s at channel: %d, Raw MIDI: %s", operation,
                      message_type, channel + 1, message_string)
    else:
      self.__log.info("%s: %s, Raw message: %s", operation, message_type,
                      message_string)

  def _on_note_on(self, message):
    """
    Callback method for NOTE ON messages
    """
    self._handle_note(message)
    
  def _on_note_off(self, message):
    """
    Callback method for NOTE OFF messages
    """
    self._handle_note(message)
    
  def _on_control_change(self, message):
    """
    Callback method for CONTROL CHANGE messages
    """
    self._print_message(message, "Answer")
    self._got_answer = True

  def _on_system_exclusive(self, message):
    """
    Callback method for SYSTEM EXCLUSIVE messages
    """
    if not self._receive_sysex(message):
      #This means that the end of the SysEx message (0xF7) was detected,
      #so, no further bytes will be received. Here the SysEx buffer will
      #be sent and afterwards cleared
      
      if message[0:3] == [0xF0, 0x7D, 0x00]:
        #A bank list was requested, so now we need to print it
        time.sleep(2)
        self.__log.info("\n\nBank list:")
        bank_number = 0
        byte_number = 3
        total_byte_sum = 0
        num_bytes = len(message)
        data_length = 0
        while byte_number < num_bytes - 2:
          byte = message[byte_number]
          total_byte_sum += byte
          if byte == 0x00:
            data_length += 0x7F
            byte_number += 1
          else:
            data_length += byte
            byte_number += 1
            data_count = 1
            byte_lst = []
            while (byte_number < num_bytes - 2) and (data_count <= data_length):
              byte = message[byte_number]
              byte_lst += [byte]
              total_byte_sum += byte
              data_count += 1
              byte_number += 1
              
            if data_count <= data_length:
              raise Exception("Malformed SysEx: misssing data from bank: %d, "
                              "expected: %d bytes, got %d bytes" % \
                              (bank_number, data_length, data_count - 1))
            
            bank_name = convert_unicode_from_7_bit_bytes(bytes(byte_lst))
            self.__log.info(str(bank_number) + " - " + bank_name)
            bank_number += 1
            data_length = 0
            
        checksum = message[byte_number]
        calculated_checksum = 128 - (total_byte_sum % 128)
        if checksum != calculated_checksum:
          raise Exception("Malformed SysEx: invalid checksum, got: %d, "
                          "expected: %d" % (calculated_checksum, checksum))
      else:
        self._print_message(message, "Answer")

      #Clears SysEx buffer
      self._sysex_buffer = []
      #Resets SysEx count to zero
      self._sysex_chunk = 0
      
      self._got_answer = True

  def _process_note(self, user_option):
    """
    Reads the note message parameters: note and velocity, then sends it to the
    foot controller
    Parameters:
    * user_option: option choosen by the user: 1 = send a NOTE ON or 2 = send
      a NOTE OFF
    Returns:
    * A tuple with the following values:
      - First position: whether or not to wait for an answer from the
        controller.
      - Second position: the sent message
    """
    status = NOTE_ON
    if user_option == '2':
      status = NOTE_OFF
      
    status = status | self._midi_in_channel
    message = [status]
    validated = False
    while not validated:
      note_symbol = input("\nNote to send [C:x, C#:x, D:x, D#:x,..., or 0-127],"
                          " where x is the octave (Control-C to exit): ")
      note = note_symbol
      if not note.isdigit():
        note = note.upper()
        note_parts = note.split(":")
        if (len(note_parts) == 2) and \
           (note_parts[0] in NOTE_SYMBOL_TO_MIDI.keys()):
          note = note_parts[0]
          try:
            octave = int(note_parts[1])
            validated = True
          except:
            pass
          if validated and (FIRST_OCTAVE <= octave) and \
            (octave <= LAST_OCTAVE):
            note, octave = parse_note(note, octave)
          else:
            validated = False
      elif (note.isdigit()):
        note = int(note)
        if (0 <= note) and (note <= 127):
          validated = True

      if not validated:
        self.__log.info("\nWrong value. Posible values: [C:x, C#:x, D:x, D#:x, "
                        "..., or 0-127], where x is the octave")
    print('')
    message += [note, self._note_velocity]
    self._print_message(message, "Sending")
    self._midi_out.send_message(message)
    return True, message

  def _process_control_change(self, user_option):
    """
    Reads the CONTROL CHANGE message parameters: controller (only if
    user_option != 3) and value.
    Parameters:
    * user_option: option choosen by the user: 3 = send a BANK SELECT or 4 = 
      send a CONTROL CHANGE
    Returns:
    * Whether or not to wait for an answer from the controller.
    """
    status = CONTROL_CHANGE
    status = status | self._midi_in_channel
    message = [status]
    
    controller = self._bank_controller
    if user_option != '3':
      validated = False
      while not validated:
        controller = input("\nController [0-127] (Control-C to exit): ")
        try:
          controller = int(controller)
          validated = True
        except:
          pass
        
        if (validated) and (0 <= controller) and (controller <= 127):
          validated = True
        else:
          validated = False
        
        if not validated:
          self.__log.info("\nWrong value. Please enter numbers between 0 and "
                          "127")

    validated = False
    while not validated:
      value = input("\nValue [0-127] (Control-C to exit): ")
      try:
        value = int(value)
        validated = True
      except:
        pass
      
      if (validated) and (0 <= value) and (value <= 127):
        validated = True
      else:
        validated = False
      
      if not validated:
        self.__log.info("\nWrong value. Please enter numbers between 0 and 127")
    message += [controller, value]
    self._print_message(message, "Sending")
    self._midi_out.send_message(message)
    
    if controller == self._bank_controller:
      return False
    return True

  def _process_midi_or_sysex(self):
    """
    Reads the raw MIDI or SysEx message from the standard input.
    Returns:
    * Whether or not to wait for an answer from the controller.
    """
    validated = False
    while not validated:
      value = input("\nRaw MIDI (ie: 91 3E 40) or SysEx (ie: F0 ... F7) "
                    "(Control-C to exit): ")

      if (is_valid_midi_message(value)) or (is_valid_sysex(value)):
        message_parts = value.split(' ')
        message = []
        for part in message_parts:
          message.append(int(part, 16))
        validated = True
      
      if not validated:
        self.__log.info("\nWrong value. Please enter valid hexadecimal strings")
    
    self._print_message(message, "Sending")
    self._midi_out.send_message(message)
    return True

  def read_user_input(self):
    """Asks the user what kind of message to send"""
    user_option = ''
    options = ['1', '2', '3', '4', '5']
    while user_option not in options:
      print('')
      self.__log.info('[1] Send a NOTE ON message')
      self.__log.info('[2] Send a NOTE OFF message')
      self.__log.info('[3] Send a BANK SELECT message')
      self.__log.info('[4] Send a CONTROL CHANGE message')
      self.__log.info('[5] Send a raw MIDI or SysEx message')
      user_option = input("Enter your option (Control-C to exit): ")
      if user_option not in options:
        self.__log.info("\nWrong option. Only %s are allowed" % repr(options))
    
    wait_answer = False
    if user_option in ['1', '2']:
      wait_answer, message = self._process_note(user_option)
    elif user_option in ['3', '4']:
      wait_answer = self._process_control_change(user_option)
    else:
      wait_answer = self._process_midi_or_sysex()
    
    if user_option != '3' and wait_answer:
      self._got_answer = False
      counter = 0
      while not self._got_answer and counter < 2:
        time.sleep(1)
        counter += 1
        user_choice = ''
        if (self._got_answer) or (counter == 2):
          if user_option == '1':
            while user_choice not in ['1', '2']:
              user_choice = input("Send a NOTE OFF? (1=yes, 2=no)? ")
              if user_choice not in ['1', '2']:
                self.__log.info("Wrong option. Please enter 1 or 2")

            if user_choice == '1':
              message[0] = NOTE_OFF | self._midi_in_channel
              self._print_message(message, "Sending")
              self._midi_out.send_message(message)
              time.sleep(1)
            break

if __name__ == '__main__':
  print("")
  midi_in = None
  midi_out = None

  try:
    #Open a MIDI IN and OUT ports. Let's say you have two ports: Port01 and
    #Port02. For testing, first start this script and set the following:
    #* Input port: Port01
    #* Output port: Port02
    #Then start an application that sends and receives MIDI messages, ie: Bome
    #SendSX, there set the ports as follows:
    #* Input port: Port02
    #* Output port: Port01
    #Finally start sending MIDI messages from your MIDI application. You should
    #see the same messages in the MIDI IN and OUT. In the console there should
    #be some debug messages
    midi_in, out_port = open_midiinput(interactive = True)
    print("")
    midi_out, out_port = open_midioutput(interactive = True)

    validated = False
    while not validated:
      midi_channel = input("\nMIDI IN channel used by controller [1-16] "
                           "(Control-C to exit): ")
      try:
        midi_channel = int(midi_channel)
        validated = True
      except:
        pass
      
      if (validated) and (1 <= midi_channel) and (midi_channel <= 16):
        validated = True
      else:
        validated = False
      
      if not validated:
        logger.info("\nWrong value. Please enter numbers between 1 and 16")

    midi_channel -= 1
    validated = False
    while not validated:
      controller = input("\nBank select controller [0-127] (Control-C to "
                         "exit): ")
      try:
        controller = int(controller)
        validated = True
      except:
        pass
      
      if (validated) and (0 <= controller) and (controller <= 127):
        validated = True
      else:
        validated = False
      
      if not validated:
        logger.info("\nWrong value. Please enter numbers between 0 and 127")
    
    validated = False
    while not validated:
      velocity = input("\nDefault velocity for NOTE ON messages [0-127] "
                       "(Control-C to exit): ")
      try:
        velocity = int(velocity)
        validated = True
      except:
        pass
      
      if (validated) and (0 <= velocity) and (velocity <= 127):
        validated = True
      else:
        validated = False
      
      if not validated:
        logger.info("\nWrong value. Please enter numbers between 0 and 127")
    
    #Instead of using the Superclass MidiInputHandler, we use it's subclass:
    #MyMidiInputHandler
    midi_in_wrapper = MyMidiInputHandler(midi_in, midi_out, midi_channel,
                                         controller, velocity)
    
    logger.info("Entering main loop. Press Control-C to exit.")

    # Just wait for keyboard interrupt,
    # everything else is handled via the input callback.
    while True:
      midi_in_wrapper.read_user_input()
  except KeyboardInterrupt:
    logger.info('KeyboardInterrupt detected')
  except:
    error = traceback.format_exc()
    logger.info(error)
  finally:
    logger.info("Exit.")
    if midi_in is not None:
      midi_in.close_port()
    
    if midi_out is not None:
      midi_out.close_port()
    del midi_in
    del midi_out
