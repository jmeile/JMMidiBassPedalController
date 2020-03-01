#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Logger.py
# By: Josef Meile <jmeile@hotmail.com> @ 27.02.2020
# This project is licensed under the MIT License. Please see the LICENSE.md file
# on the main folder of this code. An online version can be found here:
# https://github.com/jmeile/JMMidiBassPedalController/blob/master/src/LICENSE.md
#
"""Implements a logger system for the running modules."""

from __future__ import print_function
import logging
import inspect
from logging import handlers
import os
import sys

class Logger:
	"""
	Class to create a logger for a module. It can log either on a file, the
	console, both, or none
	"""

	"""
	Indicated whether or not logging was initialized. This static attribute is
	unfurtunatelly needed because you can't share a rotating log file between
	different loggers, so, it must be setup in the basic configuration and only
	once. If you don't do this and use different log handlers with the same log
	file, then you will get an error (at least on Windows) when the log gets
	rotated, see:
	* PermissionError when using python 3.3.4 and RotatingFileHandler
	  https://stackoverflow.com/questions/22459850/permissionerror-when-using-python-3-3-4-and-rotatingfilehandler
	  Answer by: Anand Joshi
	"""
	_logging_init = True

	def __init__(self, console_log_level = logging.NOTSET,
				 log_format = "%(asctime)s - %(name)s -> %(funcName)s, "
				 "line: %(lineno)d\n%(message)s",
				 timestamp_format = "%d.%m.%Y %H:%M:%S"):
		"""
		Initializes console logging for the active module
		Parameters:
		* console_log_level: Messages that will be printed to the console. If
		  you set it to: logging.NOTSET, then no message will be printed at all
		* log_format: Format of the printed messages, by default the timestamp,
		  the logger name (Module and Class where the message gets printted),
		  function name and line number were the logger was used, and finally
		  the message on the next line will be used:
				%(asctime)s - %(name)s -> %(funcName)s, line: %(lineno)d
				\n%(message)s
		* timestamp_format: Format of the timestamps for the printed messages.
		  It defaults to: "%d.%m.%Y %H:%M:%S", which is the one used in
		  Switzerland, Germany, and Austria
		"""
		self._timestamp_format = timestamp_format
		self._log_format = log_format
		self._console_log_level = console_log_level

	@staticmethod
	def init_logging(file_log_level = logging.DEBUG,
		log_format = "%(asctime)s - %(name)s -> %(funcName)s, line: %(lineno)d"
					 "\n%(message)s",
		timestamp_format = "%d.%m.%Y %H:%M:%S", file_log_name = "debug.log",
		file_log_encoding = 'utf-8', max_log_files = 5,
		max_log_size = 20 * 1048576):
		"""
		Initializes the file logger.
		Parameters:
		* file_log_level: Messages that will be logged to the file. If you set
		  this to: logging.NOTSET, then no log file will be created. It
		  defaults to logging.DEBUG
		* log_format: Format of the log file, by default the timestamp, the
		  logger name (Module and Class where the message gets logged),
		  function name and line number were the logger was used, and finally
		  the message on the next line will be used:
				%(asctime)s - %(name)s -> %(funcName)s, line: %(lineno)d
				\n%(message)s
		* timestamp_format: Format of the timestamps for the log file It
		  defaults to: "%d.%m.%Y %H:%M:%S", which is the one used in 
		  Switzerland, Germany, and Austria
		* file_log_name: File were the log messages are going to be stored. It
		  defaults to "debug.log"
		* file_log_encoding: Encoding used for the log file. It is "utf-8" by
		  default
		* max_log_files: Number of logs that will remain. It defaults to 5, so,
		  6 files will be keept: debug.log, debug.log.1 until debug.log.5.
		* max_log_size: Maximum size in bytes of each log file. It defaults to:
		  20 * 1048576, which is 20 MiB
		Remarks:
		* I'm not a fan of static attributes or methods; however, on this case,
		  I couldn't avoid this. Unfurtunatelly needed because you can't share
		  a rotating log file between different loggers, so, it must be setup
		  in the basic configuration and only once. If you don't do this and
		  use different log handlers with the same log file, then you will get
		  an error (at least on Windows) when the log gets rotated, see:
		  - PermissionError when using python 3.3.4 and RotatingFileHandler
		    https://stackoverflow.com/questions/22459850/permissionerror-when-using-python-3-3-4-and-rotatingfilehandler
		    Answer by: Anand Joshi
		"""	
		if Logger._logging_init:
			#The logger hasn't initialized yet, so do it know and disable
			#further initalizations
			Logger._logging_init = False
			if file_log_level != logging.NOTSET:
				formatter = logging.Formatter(log_format, timestamp_format)
				log_handler = handlers.RotatingFileHandler(file_log_name,
					maxBytes = max_log_size, backupCount = max_log_files,
					encoding = file_log_encoding)
				log_handler.setFormatter(formatter)
				log_handler.setLevel(file_log_level)
				logging.basicConfig(handlers=[log_handler])
	
	def setup_logger(self):
		"""
		Creates the console logger according to the parameters passed in the
		__init__ method
		"""
		caller_module_name = self._get_module_name()
		logger = logging.getLogger(caller_module_name)
		logger.setLevel(logging.DEBUG)
		if self._console_log_level != logging.NOTSET:
			#Console logging will be set if the level is different than NOTSET
			formatter = logging.Formatter(self._log_format, self._timestamp_format)
			log_handler = logging.StreamHandler(sys.stdout)
			log_handler.setFormatter(formatter)
			log_handler.setLevel(self._console_log_level)
			logger.addHandler(log_handler)
			
		return logger
	
	def _get_module_name(self):
		"""
		Get's name of the module that created the Logger instance. This is
		needed in order to know where the messages get logged; this is usefull
		if using it in several modules at once
		"""
		caller_module_name = inspect.stack()[2][1].split('.')[0]
		last_path_separator = caller_module_name.rfind(os.sep)
		if last_path_separator >= 0:
			caller_module_name = caller_module_name[last_path_separator + 1:]
		return caller_module_name