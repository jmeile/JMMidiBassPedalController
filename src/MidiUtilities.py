#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v3.0
# File: src/MidiUtilities.py
# By:   Josef Meile <jmeile@hotmail.com> @ 28.10.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""Module with some utility functions and constants."""

from bisect import bisect
import re
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF

#Equivalences of the numeric velocities to a dynamic level. You may change them,
#but keep in mind that 's' and 'ffff' must remain the same.
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

#Special BankSelect commands
BANK_SELECT_FUNCTIONS = {
  124: 'Quit',
  125: 'Reload',
  126: 'Reboot',
  127: 'Shutdown'
}

#Note trigger actions
NOTE_TRIGGERS = {
  'NoteOn': NOTE_ON,
  'NoteOff': NOTE_OFF
}

"""
SysEx messages must contain pairs of hexadecimal numbers separated by one space,
begining with F0 and ending with F7 and each byte in between can only go from 00 
until 7F.
"""
SYSEX_REGEX = "F0 ([0-7][0-9A-F] )+F7"
def is_valid_sysex(sysex_message):
  """
  Matches the SYSEX_REGEX pattern against the entered string.
  Parameters:
  * sysex_message: message to validate
  Returns:
  * True if it maches or false if it doesn't
  """
  result = re.fullmatch(SYSEX_REGEX, sysex_message, flags = re.IGNORECASE)
  is_valid = (result != None)
  return is_valid

"""
Since MIDI messages don't have always the same length, the pattern looks kind of
complicated. You have 1, 2, and three byte messages as follows:
8n 0xxxxxxx 0yyyyyyy = NOTE OFF
9n 0xxxxxxx 0yyyyyyy = NOTE ON
An 0xxxxxxx 0yyyyyyy = Polyphonic Key Pressure
Bn 0xxxxxxx 0yyyyyyy = Control Change
Cn 0xxxxxxx          = Program Change
Dn 0xxxxxxx          = Channel Pressure
En 0xxxxxxx 0yyyyyyy = Pitch Bend Change
System Common Messages (SysEx belongs here, but it will be handled separatelly)
F1 0xxxxxxx          = MIDI Time Code Quarter Frame
F2 0xxxxxxx 0yyyyyyy = Song Position Pointer
F3 0xxxxxxx          = Song Select
F6                   = Tune Request
System Real-Time Messages 
F8                   = Timing Clock
FA                   = Start
FB                   = Continue
FC                   = Stop
FE                   = Active Sensing
FF                   = Reset
Where:
* n        = MIDI channel from 0 till F
* 0xxxxxxx = First data byte going from 00 until 7F
* 0yyyyyyy = Second data byte going from 00 until 7F

The messages: F4, F5, F9, and FD are undefined (reserved for future use)
"""
MIDI_REGEX = "(F(6|8|[A-C]|[E-F]))|((((F2|([8-9A-CE][0-9A-F])) " + \
             "([0-7][0-9A-F]))|((F(1|3))|((C|D)[0-9A-F]))) " + \
             "([0-7][0-9A-F]))"

def is_valid_midi_message(midi_message):
  """
  Matches the MIDI_REGEX pattern against the entered string.
  Parameters:
  * midi_message: message to validate
  Returns:
  * True if it maches or false if it doesn't
  """
  result = re.fullmatch(MIDI_REGEX, midi_message, flags = re.IGNORECASE)
  is_valid = (result != None)
  return is_valid

def create_lookup_table():
  """Creates a lookup table to approximate a value to a velocity symbol"""
  velocity_symbols = []
  velocity_ranges = []
  velocity_dict_keys = list(NOTE_VELOCITIES)
  velocity_dict_values = list(NOTE_VELOCITIES.values())
  key_index = 0
  num_keys = len(velocity_dict_keys)
  while key_index < num_keys:
    velocity_symbols.append(velocity_dict_keys[key_index])
    if key_index not in [0, num_keys - 2, num_keys - 1]:
      velocity_ranges.append(velocity_dict_values[key_index + 1])
    elif key_index == 0:
      velocity_ranges.append(1)
    elif key_index == num_keys - 2:
      velocity_ranges.append(velocity_dict_values[key_index + 1])
    else:
      velocity_ranges.append(velocity_dict_values[key_index] + 1)
    key_index += 1
  return velocity_symbols, velocity_ranges
  
VELOCITY_SYMBOLS, VELOCITY_RANGES = create_lookup_table()

def get_velocity_symbol(numeric_velocity):
  """
  Gets the approximate symbolic value for the entered numeric velocity
  Parameters:
  * numeric_velocity: a number between 0 and 127
  Returns:
  * The symbolic representation of the entered velocity
  """
  return VELOCITY_SYMBOLS[bisect(VELOCITY_RANGES, numeric_velocity)]
  
#Equivalent of a note symbol to a MIDI note number
NOTE_SYMBOL_TO_MIDI = {
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

#Here the inverse dictionary to NOTE_SYMBOL_TO_MIDI will be created
NOTE_MIDI_TO_SYMBOL = {}
for key, value in NOTE_SYMBOL_TO_MIDI.items():
  NOTE_MIDI_TO_SYMBOL[value] = key

#Here we assume -2 as the first octave, so, the first note would be C-2 and the
#middle C is C3. Other systems assume the first octave to be -1
FIRST_OCTAVE = -2

#The last octave is calculated in terms of the first one
LAST_OCTAVE = 10 + FIRST_OCTAVE

def calculate_base_note_octave(midi_note):
  """
  Calculates the base note and octave for a given midi note
  """
  octave = int(midi_note / 12) + FIRST_OCTAVE
  base_note = midi_note - (12 * (octave - FIRST_OCTAVE))
  return base_note, octave
  
def parse_note(note, octave = None, transpose_list = [0]):
  """
  Given a note string converts it to a MIDI NOTE according to the entered
  parameters.
  Parameters:
  * note: note string to convert
  * octave: if given, the octave of the entered note. This is only necessary
    if the entered note isn't a number, but a note symbol, ie: "C#". Here the
    octave of the pedal note will be used
  * transpose_list: number of semitones to transpose the note.
  Returns
  * The recalculated notes according to the transpose list.
  """
  if (type(note) == type('')) and not note.isdigit():
    if octave == None:
      raise Exception("An octave is needed when working with note letters; none"
                      " was given")
    #Get the base note
    note = (12 * (octave - FIRST_OCTAVE)) + NOTE_SYMBOL_TO_MIDI[note]
  else:
    note = int(note)

  notes = []
  for transpose in transpose_list:
    new_note = note + int(transpose)
    if (new_note < 0) or (new_note > 127):
      modulo = new_note
      offset = 0
      if new_note > 127:
        offset = 120
        if modulo >= 8:
          offset = 108
      new_note = modulo + offset
    notes.append(new_note)
  return notes