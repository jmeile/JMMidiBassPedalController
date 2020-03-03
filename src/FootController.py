#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# FootController.py
# By: Josef Meile <jmeile@hotmail.com> @ 27.02.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/LICENSE.md
#
"""
Main program for the whole JMMidiBassPedalController package.

Run the script as follows:
python FootController.py -h

There you will see the diferent command-line options supported by the script.
"""

from __future__ import print_function
from MainArgumentParser import MainArgumentParser
from MidiConnector import MidiConnector

if __name__ == "__main__":
  parser = MainArgumentParser()
  parser.add_arguments()
  args = parser.parse_arguments()
  midi = MidiConnector(args)
  midi.start()