#!/usr/bin/env python


from __future__ import with_statement

import contextlib
import functools
import math

import gobject
import gtk
import gtk.glade


def make_idler(func):
	"""
	Decorator that makes a generator-function into a function that will continue execution on next call

	>>> import misc
	>>> misc.validate_decorator(make_idler)

	"""
	a = []

	@functools.wraps(func)
	def decorated_func(*args, **kwds):
		if not a:
			a.append(func(*args, **kwds))
		try:
			a[0].next()
			return True
		except StopIteration:
			del a[:]
			return False

	return decorated_func


@contextlib.contextmanager
def gtk_critical_section():
	#The API changed and I hope these are the right calls
	gtk.gdk.threads_enter()
	yield
	gtk.gdk.threads_leave()


if __name__ == "__main__":
	#gtk.gdk.threads_init()
	pass
