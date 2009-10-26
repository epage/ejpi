#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import cPickle
import weakref
import threading
import errno
import time
import functools
import contextlib


def synchronized(lock):
	"""
	Synchronization decorator.

	>>> import misc
	>>> misc.validate_decorator(synchronized(object()))
	"""

	def wrap(f):

		@functools.wraps(f)
		def newFunction(*args, **kw):
			lock.acquire()
			try:
				return f(*args, **kw)
			finally:
				lock.release()
		return newFunction
	return wrap


@contextlib.contextmanager
def qlock(queue, gblock = True, gtimeout = None, pblock = True, ptimeout = None):
	"""
	Locking with a queue, good for when you want to lock an item passed around

	>>> import Queue
	>>> item = 5
	>>> lock = Queue.Queue()
	>>> lock.put(item)
	>>> with qlock(lock) as i:
	... 	print i
	5
	"""
	item = queue.get(gblock, gtimeout)
	try:
		yield item
	finally:
		queue.put(item, pblock, ptimeout)


@contextlib.contextmanager
def flock(path, timeout=-1):
	WAIT_FOREVER = -1
	DELAY = 0.1
	timeSpent = 0

	acquired = False

	while timeSpent <= timeout or timeout == WAIT_FOREVER:
		try:
			fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
			acquired = True
			break
		except OSError, e:
			if e.errno != errno.EEXIST:
				raise
		time.sleep(DELAY)
		timeSpent += DELAY

	assert acquired, "Failed to grab file-lock %s within timeout %d" % (path, timeout)

	try:
		yield fd
	finally:
		os.unlink(path)


def threaded(f):
	"""
	This decorator calls the method in a new thread, so execution returns straight away

	>>> import misc
	>>> misc.validate_decorator(threaded)
	"""

	@functools.wraps(f)
	def wrapper(*args, **kwargs):
		t = threading.Thread(target=f, args=args, kwargs=kwargs)
		t.setDaemon(True)
		t.start()
	return wrapper


def fork(f):
	"""
	Fork a function into a seperate process and block on it, for forcing reclaiming of resources for highly intensive functions
	@return The original value through pickling.  If it is unable to be pickled, then the pickling exception is passed through
	@throws Through pickling, exceptions are passed back and re-raised
	@note source: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/511474

	>>> import misc
	>>> misc.validate_decorator(fork)
	"""

	@functools.wraps(f)
	def wrapper(*args, **kwds):
		pread, pwrite = os.pipe()
		pid = os.fork()
		if pid > 0:
			os.close(pwrite)
			with os.fdopen(pread, 'rb') as f:
				status, result = cPickle.load(f)
			os.waitpid(pid, 0)
			if status == 0:
				return result
			else:
				raise result
		else:
			os.close(pread)
			try:
				result = f(*args, **kwds)
				status = 0
			except Exception, exc:
				result = exc
				status = 1
			with os.fdopen(pwrite, 'wb') as f:
				try:
					cPickle.dump((status, result), f, cPickle.HIGHEST_PROTOCOL)
				except cPickle.PicklingError, exc:
					cPickle.dump((2, exc), f, cPickle.HIGHEST_PROTOCOL)
			f.close()
			sys.exit(0)
	return wrapper


@contextlib.contextmanager
def qlock(queue, gblock = True, gtimeout = None, pblock = True, ptimeout = None):
	"""
	Locking with a queue, good for when you want to lock an item passed around

	>>> import Queue
	>>> item = 5
	>>> lock = Queue.Queue()
	>>> lock.put(item)
	>>> with qlock(lock) as i:
	... 	print i
	5
	"""
	item = queue.get(gblock, gtimeout)
	yield item
	queue.put(item, pblock, ptimeout)


class EventSource(object):
	"""
	Asynchronous implementation of the observer pattern

	>>> sourceRoot = EventSource()
	>>> sourceChild1 = EventSource()
	>>> sourceChild1.register_provided_events("1-event-0", "1-event-1")
	>>> sourceChild2 = EventSource()
	>>> sourceChild2.register_provided_events("1-event-0", "1-event-1")
	>>> sourceRoot.add_children(sourceChild1, sourceChild2)
	"""

	def __init__(self):
		"""
		@warning Not thread safe
		"""

		self.__callbackQueues = {}
		self.__children = []

	def add_children(self, *childrenSources):
		"""
		@warning Not thread safe
		"""

		self.__children.extend(childrenSources)

	def remove_children(self, *childrenSources):
		"""
		@warning Not thread safe
		"""

		for child in childrenSources:
			self.__children.remove(child)

	def register_provided_events(self, *events):
		"""
		@warning Not thread safe
		"""

		self.__callbackQueues.update(dict((event, []) for event in events))

	def notify_observers(self, event, message):
		"""
		@warning As threadsafe as the queue used.  qlock is recommended for the message if it needs locking
		"""

		for queue in self.__callbackQueues[event]:
			queue.put(message)

	def _register_queue(self, event, queue):
		"""
		@warning Not thread safe
		"""

		if event in self.__callbackQueues:
			self.__callbackQueues[event].append(queue)
			return self
		else:
			for child in self.__children:
				source = child._register_queue(event, queue)
				if source is not None:
					return source
			else:
				return None

	def _unregister_queue(self, event, queue):
		"""
		@warning Not thread safe
		"""

		if event in self.__callbackQueues:
			self.__callbackQueues[event].remove(queue)
			return self
		else:
			for child in self.__children:
				source = child._unregister_queue(event, queue)
				if source is not None:
					return source
			else:
				return None


class StrongEventSourceProxy(object):

	def __init__(self, source):
		"""
		@warning Not thread safe
		"""

		self.source = source

	def register(self, event, queue):
		"""
		@warning Not thread safe
		"""

		actualSource = self.source._register_queue(event, queue)
		ActualType = type(self)
		return ActualType(actualSource)

	def unregister(self, event, queue):
		"""
		@warning Not thread safe
		"""

		actualSource = self.source._unregister_queue(event, queue)
		ActualType = type(self)
		return ActualType(actualSource)


class WeakEventSourceProxy(object):

	def __init__(self, source):
		"""
		@warning Not thread safe
		"""

		self.source = weakref.ref(source)

	def register(self, event, queue):
		"""
		@warning Not thread safe
		"""

		actualSource = self.source()._register_queue(event, queue)
		ActualType = type(self)
		return ActualType(actualSource)

	def unregister(self, event, queue):
		"""
		@warning Not thread safe
		"""

		actualSource = self.source()._unregister_queue(event, queue)
		ActualType = type(self)
		return ActualType(actualSource)


class EventObserver(object):
	"""

	>>> import Queue
	>>> class Observer(EventObserver):
	... 	def connect_to_source(self, eventSourceRoot):
	... 		self.queue = Queue.Queue()
	... 		self.source = eventSourceRoot.register("1-event-0", self.queue)
	>>>
	>>> sourceRoot = EventSource()
	>>> sourceChild1 = EventSource()
	>>> sourceChild1.register_provided_events("1-event-0", "1-event-1")
	>>> sourceChild2 = EventSource()
	>>> sourceChild2.register_provided_events("1-event-0", "1-event-1")
	>>> sourceRoot.add_children(sourceChild1, sourceChild2)
	>>>
	>>> o1 = Observer()
	>>> o1.connect_to_source(StrongEventSourceProxy(sourceRoot))
	>>> o2 = Observer()
	>>> o2.connect_to_source(WeakEventSourceProxy(sourceRoot))
	>>>
	>>> sourceChild1.notify_observers("1-event-0", "Hello World")
	>>> o1.queue.get(False)
	'Hello World'
	>>> o2.queue.get(False)
	'Hello World'
	"""

	def connect_to_source(self, eventSourceRoot):
		raise NotImplementedError
