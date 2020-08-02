#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v2.0
# File: src/ByteUtilities.py
# By:   Josef Meile <jmeile@hotmail.com> @ 02.08.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""Module with some byte manipulation utilities."""

def convert_to_7_bit_bytes(source_bytes):
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
  
def convert_from_7_bit_bytes(source_bytes):
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
  
def convert_unicode_to_7_bit_bytes(source_str, encoding = 'UTF-8'):
  """
  Converts an unicode string to its 7 bit bytes representation.
  
  Parameters:
  * source_str: string to convert
  * encoding: encoding used by the entered string
  
  Returns a byte array of the string converted to 7 bit bytes
  """
  source_bytes = source_str.encode(encoding = encoding)
  return convert_to_7_bit_bytes(source_bytes)
  
def convert_unicode_from_7_bit_bytes(source_bytes, encoding = "UTF-8"):
  """
  Converts a 7 bit byte array to its unicode representation
  
  Parameters:
  * source_bytes: 7 bit bytes to convert
  * encoding: encoding of the resulting string
  
  Returns an unicode string resulting of converting the source_bytes
  """
  converted_bytes = convert_from_7_bit_bytes(source_bytes)
  return converted_bytes.decode(encoding = encoding)
  
def convert_byte_array_to_list(source_bytes):
  """
  Converts the entered byte array to a list of bytes, returns the computed
  lengths for sending the data through SysEx and the sum of its bytes.
  
  Parameters:
  * source_bytes: bytes to convert
    
  Returns a tuple containing the list of bytes, the computed lengths, and the
  sum of its bytes.
  
  Remaks:
  * The method will itearate through the whole source_bytes parameters and gets
    each byte and put it into a list.
  * Parallely, the cumulated lengths will be calculated as follows:
    - If at some point the length of the processed bytes superates 127, then a
      hex 00H will be written to lengths_lst indicating that the length will
      continue summing on the next field.
    - Otherwise the hex of the cumulated value will be written.
    - Each byte will be also summed
  """
  cumulated_length = 0
  byte_sum = 0
  lengths_lst = []
  byte_lst = []
  for byte in source_bytes:
    byte_lst += [byte]
    byte_sum += byte
    cumulated_length += 1
    if cumulated_length > 0x7F:
      cumulated_length = 1
      lengths_lst += [0x00]
  lengths_lst += [cumulated_length]
  byte_sum += cumulated_length
  return byte_lst, lengths_lst, byte_sum
  
def calculate_checksum(source_bytes):
  """
  Calculates the checksum of the entered bytes.
  
  Returns the calculated checksum
  
  Remarks:
  * The checksum will be calculated by using this rule:
    checksum = 128 - (sum(data) % 128)
  """
  total_byte_sum = 0
  for byte in source_bytes:
    total_byte_sum += byte
    
  return 128 - (total_byte_sum % 128)