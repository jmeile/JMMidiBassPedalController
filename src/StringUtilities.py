#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# JMMidiBassPedalController v2.0
# File: src/StringUtilities.py
# By:   Josef Meile <jmeile@hotmail.com> @ 02.08.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""Module with some string utilities."""

import re
import os

def multiple_split(source_string, separators, split_by = '\n'):
  """
  This function allows the user to split a  string by using different
  separators.

  Note: This version is faster than using the (s)re.split method (I tested it
  with timeit).

  Parameters:
  * source_string: string to be splitted
  * separators: string containing the characters used to split the source
    string.
  * split_by: all the ocurrences of the separators will be replaced by this
    character, then the split will be done. It defaults to '|' (pipe)
  """
  translate_to = split_by * len(separators)
  translation = str.maketrans(separators, translate_to)
  return source_string.translate(translation).split(split_by)
  
def read_text_file(file_path):
  """
  Gets the contents of a text file
  """
  if not os.path.isfile(file_path):
    return False, ""

  file_pointer = open(file_path)
  contents = file_pointer.read()
  file_pointer.close()
  return True, contents