# Authors:
#   Jason Gerard DeRose <jderose@redhat.com>
#
# Copyright (C) 2008  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; version 2 only
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""
Base classes for plug-in architecture and generative API.
"""

import inspect
import exceptions


class Named(object):
	#def __init__(self, prefix):
	#	clsname = self.__class__.__name__
	def __get_name(self):
		return self.__class__.__name__
	name = property(__get_name)

	def __get_cli_name(self):
		return self.name.replace('_', '-')
	cli_name = property(__get_cli_name)


class Command(Named):

	def normalize(self, kw):
		raise NotImplementedError

	def validate(self, kw):
		raise NotImplementedError

	def execute(self, kw):
		raise NotImplementedError

	def __call__(self, **kw):
		normalized = self.normalize(kw)
		invalid = self.validate(normalized)
		if invalid:
			return invalid
		return self.execute(normalize)


class Argument(object):
	pass


class NameSpace(object):
	"""
	A read-only namespace of (key, value) pairs that can be accessed
	both as instance attributes and as dictionary items.  For example:

	>>> ns = NameSpace(dict(my_message='Hello world!'))
	>>> ns.my_message
	'Hello world!'
	>>> ns['my_message']
	'Hello world!'

	Keep in mind that Python doesn't offer true ready-only attributes. A
	NameSpace is read-only in that it prevents programmers from
	*accidentally* setting its attributes, but a motivated programmer can
	still set them.

	For example, setting an attribute the normal way will raise an exception:

	>>> ns.my_message = 'some new value'
	(raises exceptions.SetAttributeError)

	But a programmer could still set the attribute like this:

	>>> ns.__dict__['my_message'] = 'some new value'

	You should especially not implement a security feature that relies upon
	NameSpace being strictly read-only.
	"""

	__locked = False # Whether __setattr__ has been locked

	def __init__(self, kw):
		"""
		The single constructor argument `kw` is a dict of the (key, value)
		pairs to be in this NameSpace instance.
		"""
		assert isinstance(kw, dict)
		self.__kw = dict(kw)
		for (key, value) in self.__kw.items():
			assert not key.startswith('_')
			setattr(self, key, value)
		self.__keys = sorted(self.__kw)
		self.__locked = True

	def __setattr__(self, name, value):
		"""
		Raises an exception if trying to set an attribute after the
		NameSpace has been locked; otherwise calls object.__setattr__().
		"""
		if self.__locked:
			raise exceptions.SetAttributeError(name)
		super(NameSpace, self).__setattr__(name, value)

	def __getitem__(self, key):
		"""
		Returns item from namespace named `key`.
		"""
		return self.__kw[key]

	def __hasitem__(self, key):
		"""
		Returns True if namespace has an item named `key`.
		"""
		return key in self.__kw

	def __iter__(self):
		"""
		Yields the names in this NameSpace in ascending order.

		For example:

		>>> ns = NameSpace(dict(attr_b='world', attr_a='hello'))
		>>> list(ns)
		['attr_a', 'attr_b']
		>>> [ns[k] for k in ns]
		['hello', 'world']
		"""
		for key in self.__keys:
			yield key

	def __len__(self):
		"""
		Returns number of items in this NameSpace.
		"""
		return len(self.__keys)


class API(object):
	__commands = None
	__objects = None
	__locked = False

	def __init__(self):
		self.__c = {} # Proposed commands
		self.__o = {} # Proposed objects

	def __get_objects(self):
		return self.__objects
	objects = property(__get_objects)

	def __get_commands(self):
		return self.__commands
	commands = property(__get_commands)

	def __merge(self, target, base, cls, override):
		assert type(target) is dict
		assert inspect.isclass(base)
		assert inspect.isclass(cls)
		assert type(override) is bool
		if not issubclass(cls, base):
			raise exceptions.RegistrationError(
				cls,
				'%s.%s' % (base.__module__, base.__name__)
			)

	def register_command(self, cls, override=False):
		self.__merge(self.__c, Command, cls, override)

	def finalize(self):
		pass
