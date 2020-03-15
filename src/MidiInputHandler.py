#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MidiInputHandler.py
# By: Josef Meile <jmeile@hotmail.com> @ 01.03.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""Wraps MidiIn to add convenience methods for catching common MIDI events."""

from __future__ import print_function
from Logger import Logger
import logging
from autologging import logged
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROL_CHANGE,
                  MIDI_TIME_CODE, NOTE_OFF, NOTE_ON,
                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE,
                  SONG_POSITION_POINTER, SONG_SELECT,
                  TIMING_CLOCK, TUNE_REQUEST, SONG_START,
                  SONG_CONTINUE, SONG_STOP, ACTIVE_SENSING,
                  SYSTEM_RESET, SYSTEM_EXCLUSIVE,
                  END_OF_EXCLUSIVE)

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
class MidiInputHandler:
  """
  Instead of handling MIDI messages equally, it will use convenience methods
  to fire them. Per default this class will only echo all catched messages.
  If you want to add certain functionalities, then subclass it and rewrite
  the _on_* methods. Please note that if you change: _callback_preffix, then
  you need to use that preffix on the subclass overrides
  """
  
  """
  List of callbacks to be defined. In order to customize them, you need to
  create a subclass of MidiInputHandler and then define the respective handler,
  ie: for NOTE_ON, you need to define a method with the signature:
    def _on_note_on(self, message):
  Note that here, I'm assuming that _callback_preffix is equal to: "_on_"
  """
  _midi_messages = {
    NOTE_ON: 'note_on',
    NOTE_OFF: 'note_off',
    POLY_PRESSURE: 'after_touch_poly',
    CONTROL_CHANGE: 'control_change',
    PROGRAM_CHANGE: 'program_change',
    CHANNEL_PRESSURE: 'after_touch_channel',
    PITCH_BEND: 'pitch_bend',
    MIDI_TIME_CODE: 'time_code_quarter_frame',
    SONG_POSITION_POINTER: 'song_position',
    SONG_SELECT: 'song_select',
    SONG_START: 'song_start',
    SONG_CONTINUE: 'song_continue',
    SONG_STOP: 'song_stop',
    ACTIVE_SENSING: 'active_sensing',
    TIMING_CLOCK: 'clock',
    TUNE_REQUEST: 'tune_request',
    SYSTEM_RESET: 'system_reset',
    SYSTEM_EXCLUSIVE: 'system_exclusive'
  }
  
  """
  Preffix of all callbacks. If you change it, please make sure that all your
  subclass overrides begin with that preffix
  """
  _callback_preffix = '_on_'
  
  def __init__(self, midi_in, midi_out, console_echo = False,
               ignore_sysex = True, ignore_timing = True,
               ignore_active_sense = True):
    """
    Initializes the class attributes
    Parameters:
    * midi_in: MIDI IN interface to use
    * midi_out: MIDI OUT interface to use. If None, then the messages will be
      printed into the console
    * console_echo: if used together with midi_out, then the message will be
      first printed into the console, then it will be sent
    * ignore_* parameters: see the "_ignore_messages" method
    """
    self.__log.debug(("*" * 80) + "\nIf you are seeing this message on the"
      " console, consider disabling it by setting\nconsole_log_level to "
      "logging.NOTSET on the Logger(...) call. You may also want\nto "
      "disable the log file by setting file_log_level to logging.NOTSET "
      "on the\nLogger.init_logging(...) call. Console logging may "
      "slower the excecution of\nyour script; use it only for debugging "
      "purposes\n" + ("*" * 80) + "\n")
    self._midi_in = midi_in
    self._midi_out = midi_out
    self._console_echo = console_echo
    self._sysex_buffer = []
    self._sysex_chunk = 0

    self._ignore_messages(ignore_sysex, ignore_timing, ignore_active_sense)
    
    #Sets the main MIDI callback where all preprocessing will be done
    self._midi_in.set_callback(self)
    
    #Creates the built-in callbacks, which will only echo the MIDI message
    base_callback = getattr(self, '_send_midi_message')
    for midi_message in self._midi_messages.values():
      callback = base_callback
      if midi_message == 'system_exclusive':
        callback = getattr(self, '_send_system_exclusive')
      
      message_callback_name = self._callback_preffix + midi_message
      if not hasattr(self, message_callback_name):
        #This means that the callback hasn't defined by a subclass, so
        #it will define here at the superclass
        setattr(self, message_callback_name, callback)

  def __call__(self, event, data = None):
    message, deltatime = event
    status = message[0]
    if message[0] != SYSTEM_EXCLUSIVE:
      new_status = message[0] & 0xF0
      if new_status != SYSTEM_EXCLUSIVE:
        #This will avoid that messages like SONG_START (0XFA) get
        #wrongly classified as SysEx
        status = new_status
    
    midi_message = self._midi_messages.get(status, None)
    callback_name = '_send_midi_message'
    if midi_message is None:
      if len(self._sysex_buffer) != 0:
        self.__log.debug("Catched SysEx message chunk")
        #This means that a SysEx message started
        callback_name = self._callback_preffix + 'system_exclusive'
      else:
        self.__log.debug("Catched unhandled MIDI message")
    else:
      self.__log.debug("Catched message: %s" % midi_message)
      callback_name = self._callback_preffix + midi_message
    callback = getattr(self, callback_name)
    callback(message)

  def _send_midi_message(self, message):
    """
    Handles a midi message. By default it just sends it back.
    Parameters:
    * message: Contains a list with the bytes of the MIDI Message, ie:
      [147, 60, 112] (in Hexadecimal: 93 3C 70) represents a sending a
      middle C NOTE ON with a velocity of 112 through the MIDI channel 4.
    Remarks:
    * Please note that this callback isn't supposed to be overwritten by a
      subclass. To create a custom handler, override the midi message that
      you want by creating a: "_on_*" handler on the subclass (here I'm
      assuming _callback_preffix equal to "_on_")
    """
    #Do not uncomment this on a productive environment. SysEx messages
    #can be long, so logging them can slower things
    #self.__log.debug("MIDI message: %r" % message)
    
    #This may really slower things because it will do some operations in
    #the message to make it human readable. Use it only for debugging
    message_string = "MIDI message: %s" % \
      '[{}]'.format(' '.join(hex(x).lstrip("0x").upper().zfill(2)
      for x in message))
    self.__log.debug(message_string)

    if (self._midi_out == None) or (self._console_echo):
      self.__log.info(message_string)
    
    if self._midi_out != None:
      self._midi_out.send_message(message)

  def _receive_sysex(self, message):
    """
    Appends the entered message to the SysEx buffer.
    Parameters:
    * message: SysEx message chunk to append to the buffer
    Returns: False if the end of the SysEx message (0xF7) was detected, so,
         no more data needs to be read. True will be returned if the
         SysEx message is not yet complete
    Remarks:
    * Please note that this method will be only called after the reception
      of a SysEx message was started. This must be done inside the
      _on_system_exclusive handler. Do not override this on the subclass
    """
    self._sysex_chunk += 1
    if len(self._sysex_buffer) == 0:
      self.__log.debug("Beginning SysEx reception. Chunk number: %d, "
        "bytes: %d" % (self._sysex_chunk, len(message)))
      #gets the first part of the system_exclusive message
      self._sysex_buffer = message
    else:
      self.__log.debug("Reading next SysEx fragment. Chunk number: %s, "
        "bytes: %d" % (self._sysex_chunk, len(message)))
      #appends the next part of the system_exclusive message
      self._sysex_buffer.extend(message)

    if self._sysex_buffer[-1] == END_OF_EXCLUSIVE:
      #End receiving SysEx
      self.__log.debug("SysEx reception was completed. Total chunks: %s, "
        "total bytes: %d" % (self._sysex_chunk, 
                   len(self._sysex_buffer)))
      
      #Do not uncomment this on a productive environment. SysEx messages
      #can be long, so logging them can slower things
      #self.__log.debug("SysEx message: %r" % self._sysex_buffer)
      
      #This may really slower things because it will do some operations in
      #the message to make it human readable. Use it only for debugging 
      self.__log.debug("MIDI message: %s" % \
        '[{}]'.format(' '.join(hex(x).lstrip("0x").upper().zfill(2)
        for x in self._sysex_buffer)))
      return False

    return True

  def _send_system_exclusive(self, message):
    """
    Handles a SysEx (system exlusive) message. By default it just sends it
    back.
    Parameters:
    * message: Contains a list with the bytes of the MIDI Message, ie:
      [240, 67, 112, 247] (in Hexadecimal: F0 43 70, F7). Please note that
      if the SysEx message is too long, then this method will be called
      several times untill the end byte of the SysEx (0xF7) gets sent.
    Remarks:
    * Please note that this callback isn't supposed to be overwritten by
      a subclass. Instead of doing this, create a handler called:
      _on_system_exclusive (Here I'm assuming that _callback_preffix is
      equal to "_on_"), then leave the part receiving the SysEx equal; only
      after you have received the whole SysEx, you should add your post
      processing. You must also clear the SysEx buffer afterwards
    """
    if not self._receive_sysex(message):
      #This means that the end of the SysEx message (0xF7) was detected,
      #so, no further bytes will be received. Here the SysEx buffer will
      #be sent and afterwards cleared
      if (self._midi_out == None) or (self._console_echo):
        self.__log.info(repr(self._sysex_buffer))
        
      if self._midi_out != None:
        self._midi_out.send_message(self._sysex_buffer)

      #Clears SysEx buffer
      self._sysex_buffer = []
      #Resets SysEx count to zero
      self._sysex_chunk = 0

  def _ignore_messages(self, ignore_sysex = True, ignore_timing = True,
              ignore_active_sense = True):
    """
    Enables or disables the following MIDI messages: SysEx (System
    Exclusive), timing (clock), and active sense
    Parameters:
    * ignore_*: by default python rtmidi will ignore these messages: SysEx 
      (System exclusive, timing, and active sense.  Normally you don't need
      them on a MIDI application; they are basically used by the
      synthezisers and other MIDI equipment; however there maybe cases
      where you want to for example filter out some SysEx; on that case,
      set the ignore_sysex parameter to False. Similarly, you can do the
      same for the other messages, ie: your keyboard sends constantly clock
      and active sensing messages, so, you need to set the parameters to
      False
    """
    self._midi_in.ignore_types(sysex = ignore_sysex,
      timing = ignore_timing, active_sense = ignore_active_sense)