#!/usr/bin/env python


from __future__ import with_statement

import inspect
import contextlib
import functools


def TODO(func):
	"""
	unittest test method decorator that ignores
	exceptions raised by test

	Used to annotate test methods for code that may
	not be written yet.  Ignores failures in the
	annotated test method; fails if the text
	unexpectedly succeeds.
	!author http://kbyanc.blogspot.com/2007/06/pythons-unittest-module-aint-that-bad.html

	Example:
	>>> import unittest
	>>> class ExampleTestCase(unittest.TestCase):
	...	@TODO
	...	def testToDo(self):
	...		MyModule.DoesNotExistYet('boo')
	...
	"""

	@functools.wraps(func)
	def wrapper(*args, **kw):
		try:
			func(*args, **kw)
			succeeded = True
		except:
			succeeded = False
		assert succeeded is False, \
			"%s marked TODO but passed" % func.__name__
	return wrapper


def PlatformSpecific(platformList):
	"""
	unittest test method decorator that only
	runs test method if os.name is in the
	given list of platforms
	!author http://kbyanc.blogspot.com/2007/06/pythons-unittest-module-aint-that-bad.html
	Example:
	>>> import unittest
	>>> class ExampleTestCase(unittest.TestCase):
	... 	@PlatformSpecific(('mac', ))
	... 	def testMacOnly(self):
	...		MyModule.SomeMacSpecificFunction()
	...
	"""

	def decorator(func):
		import os

		@functools.wraps(func)
		def wrapper(*args, **kw):
			if os.name in platformList:
				return func(*args, **kw)
		return wrapper
	return decorator


def CheckReferences(func):
	"""
	!author http://kbyanc.blogspot.com/2007/06/pythons-unittest-module-aint-that-bad.html
	"""

	@functools.wraps(func)
	def wrapper(*args, **kw):
		refCounts = []
		for i in range(5):
			func(*args, **kw)
			refCounts.append(XXXGetRefCount())
		assert min(refCounts) != max(refCounts), "Reference counts changed - %r" % refCounts

	return wrapper


class expected(object):
	"""
	>>> with expected(ZeroDivisionError):
	... 	1 / 0
	>>> with expected(AssertionError("expected ZeroDivisionError to have been thrown")):
	... 	with expected(ZeroDivisionError):
	... 		1 / 2
	Traceback (most recent call last):
		File "/usr/lib/python2.5/doctest.py", line 1228, in __run
			compileflags, 1) in test.globs
		File "<doctest libraries.recipes.context.expected[1]>", line 3, in <module>
			1 / 2
		File "/media/data/Personal/Development/bzr/Recollection-trunk/src/libraries/recipes/context.py", line 139, in __exit__
			assert t is not None, ("expected {0:%s} to have been thrown" % (self._t.__name__))
	AssertionError: expected {0:ZeroDivisionError} to have been thrown
	>>> with expected(Exception("foo")):
	... 	raise Exception("foo")
	>>> with expected(Exception("bar")):
	... 	with expected(Exception("foo")): # this won't catch it
	... 		raise Exception("bar")
	... 	assert False, "should not see me"
	>>> with expected(Exception("can specify")):
	... 	raise Exception("can specify prefixes")
	>>> with expected(Exception("Base class fun")):
	... 	raise IndexError("Base class fun")
	"""

	def __init__(self, e):
		if isinstance(e, Exception):
			self._t, self._v = type(e), str(e)
		elif isinstance(e, type):
			self._t, self._v = e, ""
		else:
			raise Exception("usage: with expected(Exception): ... or "
							"with expected(Exception(\"text\")): ...")

	def __enter__(self):
		try:
			pass
		except:
			pass # this is a Python 3000 way of saying sys.exc_clear()

	def __exit__(self, t, v, tb):
		assert t is not None, ("expected {0:%s} to have been thrown" % (self._t.__name__))
		return self._t in inspect.getmro(t) and str(v).startswith(self._v)
