#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v1.3
# File: src/ByteUtilities.py
# By:   Josef Meile <jmeile@hotmail.com> @ 21.06.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""Module with some byte manipulation utilities."""

def convert_to_7_bit(source_bytes):
  """
  Converts the entered bytes to a 7 bit bytes representation.

  Parameters:
  * source_bytes: 8 bit byte array to be converted to 7 bit byte
  
  Returns:
  * A byte array with the 7 bit byte converted data

  Remarks:
  * This is the same algorithm used by Yamaha to store their data into the
    Electone digital organs. See the file "7_to_8_bit_byte_conversion.pdf"
    inside the "assets" folder.
  
    This conversion will be used to transmit unicode data, ie: UTF-8 or GB2312,
    through MIDI; this protocol is unfortunatelly limited to values until: 127
    (or 7F in hex or 0111 1111 in binary), so bigger unicode values won't fit.
    For this reason, the data needs to be convert to 7 bit bytes.
  """
  msb = 0xC0
  lsb = 0x3F
  #Control byte
  cbt = 0x40
  byte_array = b''
  for byte in source_bytes:
    full_bytes = []
    if (byte >= 0x40):
      rest_bits = lsb & byte
      first_byte = cbt | rest_bits
      full_bytes.append(first_byte)
      control_bits = (msb & byte) >> 2
      second_byte = cbt | control_bits
      full_bytes.append(second_byte)
    else:
      full_bytes.append(byte)
    
    byte_array += bytes(full_bytes)
  return byte_array
  
def convert_from_7_bit(source_bytes):
  """
  Converts a 7 bit byte array to a 8 bit byte array
  
  Remarks:
  * Once the 7 bit byte data is transmitted through MIDI, you need to convert it
    back to 8 bit bytes in order to read the unicode strings
  """
  lsb = 0x3F
  #Control byte
  cbt = 0x30
  current_byte = 0
  num_bytes = len(source_bytes)
  byte_array = b''
  while current_byte < num_bytes:
    full_bytes = b''
    byte = source_bytes[current_byte]
    if (byte > 0x3F) and (current_byte + 1 < num_bytes):
      next_byte = source_bytes[current_byte + 1]
      if next_byte in [0x50, 0x60, 0x70]:
        control_bits = (next_byte & cbt) << 2
        byte = (lsb & byte) | control_bits
        current_byte += 1      
    elif (byte > 0x3F):
      raise Exception("Missing control byte, either: 0x50, 0x60, or 0x70")
    
    byte_array += bytes([byte])
    current_byte += 1
  return byte_array