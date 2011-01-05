"""
Django MetaSettings

Licensed under the MIT License. See LICENSE.
http://creativecommons.org/licenses/MIT/
"""

import socket
import re
import os
from django.conf import settings


HOSTNAME = 'METASETTINGS_MATCHING_METHOD_HOST_NAME'
FQDN = 'METASETTINGS_MATCHING_METHOD_DOMAIN_NAME'
PATH = 'METASETTINGS_MATCHING_METHOD_ROOT_PATH'
ENV = 'METASETTINGS_MATCHING_METHOD_ENVIRONMENTAL_VARIABLE'

# Name of the environment variable containing the key for ENV matching
ENV_NAME = 'METASETTINGS_KEY'


class MetaSettings():
	def __init__(self, settings_dir):
		self._settings_dir = settings_dir
		self._settings = {}
		self._modules = []


	def import_completed(self):
		return bool(self._settings.keys())


	def add_modules(self, method, *patterns):
		# Can't be run once Django has been configured
		if self.import_completed():
			raise RuntimeError('Settings already configured.')

		match = {
						HOSTNAME: lambda: socket.gethostname(),
						FQDN: lambda: socket.getfqdn(),
						PATH: lambda: None,
						ENV: lambda: os.getenv(ENV_NAME),
						None: lambda: None,
		}.get(method)()

		for pattern in patterns:
			if bool(re.match(pattern[0], match)):
				modules = pattern[1]

				# Make sure the list of modules is either a list or a tuple
				if type(modules) not in (list, tuple):
					modules = (modules,)

				# Add the modules to the module list
				self._modules += modules

				return

		raise Exception("No match for %s." % match)


	def import_settings(self, name):
			execfile('%s/%s.py' % (self._settings_dir, name), globals(), self._settings)


	def configure(self):
		# This can only be run once
		if self.import_completed():
			raise MetaSettingsError('MetaSettings has already configured Django.')

		# The base class is always imported first
		self.import_settings('base')

		# Import each additional module in the order specified by the configuration
		for module in self._modules:
			self.import_settings(module)

		# Filter out settings without upper-case names
		conf = dict(
			(key, value)
			for key, value in self._settings.items()
			if key.isupper()
		)

		# Pass the configuration to Django
		settings.configure(**conf)


class MetaSettingsError(Exception):
	"""Base class for errors in Django-MetaSettings."""