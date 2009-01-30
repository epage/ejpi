#!/usr/bin/env python


"""
This module provides three types of queues, with these constructors:
	Stack([items])	-- Create a Last In First Out queue, implemented as a list
	Queue([items])	-- Create a First In First Out queue
	PriorityQueue([items]) -- Create a queue where minimum item (by <) is first
Here [items] is an optional list of initial items; if omitted, queue is empty.
Each type supports the following methods and functions:
	len(q)		-- number of items in q (also q.__len__())
	q.append(item)-- add an item to the queue
	q.extend(items) -- add each of the items to the queue
	q.pop()		 -- remove and return the "first" item from the queue
"""


import types
import operator


def Stack(items=None):
	"A stack, or last-in-first-out queue, is implemented as a list."
	return items or []


class Queue(object):
	"A first-in-first-out queue."

	def __init__(self, initialItems=None):
		self.start = 0
		self.items = initialItems or []

	def __len__(self):
		return len(self.items) - self.start

	def append(self, item):
		self.items.append(item)

	def extend(self, items):
		self.items.extend(items)

	def pop(self):
		items = self.items
		item = items[self.start]
		self.start += 1
		if self.start > 100 and self.start > len(items)/2:
			del items[:self.start]
			self.start = 0
		return item


class PriorityQueue(object):
	"A queue in which the minimum element (as determined by cmp) is first."

	def __init__(self, initialItems=None, comparator=operator.lt):
		self.items = []
		self.cmp = comparator
		if initialItems is not None:
			self.extend(initialItems)

	def __len__(self):
		return len(self.items)

	def append(self, item):
		items, cmp_func = self.items, self.cmp
		items.append(item)
		i = len(items) - 1
		while i > 0 and cmp_func(item, items[i//2]):
			items[i], i = items[i//2], i//2
		items[i] = item

	def extend(self, items):
		for item in items:
			self.append(item)

	def pop(self):
		items = self.items
		if len(items) == 1:
			return items.pop()
		e = items[0]
		items[0] = items.pop()
		self.heapify(0)
		return e

	def heapify(self, i):
		"""
		itemsssumes items is an array whose left and right children are heaps,
		move items[i] into the correct position.See CLR&S p. 130
		"""
		items, cmp_func = self.items, self.cmp
		left, right, N = 2*i + 1, 2*i + 2, len(items)-1
		if left <= N and cmp_func(items[left], items[i]):
			smallest = left
		else:
			smallest = i

		if right <= N and cmp_func(items[right], items[smallest]):
			smallest = right
		if smallest != i:
			items[i], items[smallest] = items[smallest], items[i]
			self.heapify(smallest)


class AttrDict(object):
	"""
	Can act as a mixin to add dictionary access to members to ease dynamic attribute access
	or as a wrapper around a class

	>>> class Mixin (AttrDict):
	... 	def __init__ (self):
	... 		AttrDict.__init__ (self)
	... 		self.x = 5
	...
	>>> mixinExample = Mixin ()
	>>> mixinExample.x
	5
	>>> mixinExample["x"]
	5
	>>> mixinExample["x"] = 10; mixinExample.x
	10
	>>> "x" in mixinExample
	True
	>>> class Wrapper (object):
	... 	def __init__ (self):
	... 		self.y = 10
	...
	>>> wrapper = Wrapper()
	>>> wrapper.y
	10
	>>> wrapperExample = AttrDict (wrapper)
	>>> wrapperExample["y"]
	10
	>>> wrapperExample["y"] = 20; wrapper.y
	20
	>>> "y" in wrapperExample
	True
	"""

	def __init__(self, obj = None):
		self.__obj = obj if obj is not None else self

	def __getitem__(self, name):
		return getattr(self.__obj, name)

	def __setitem__(self, name, value):
		setattr(self.__obj, name, value)

	def __delitem__(self, name):
		delattr(self.__obj, name)

	def __contains__(self, name):
		return hasattr(self.__obj, name)


class Uncertain(object):
	"""
	Represents a numeric value with a known small uncertainty
	(error, standard deviation...).
	Numeric operators are overloaded to work with other Uncertain or
	numeric objects.
	The uncertainty (error) must be small. Otherwise the linearization
	employed here becomes wrong.

	>>> pie = Uncertain(3.14, 0.01)
	>>> ee = Uncertain(2.718, 0.001)
	>>> pie, repr(pie)
	(Uncertain(3.14, 0.01), 'Uncertain(3.14, 0.01)')
	>>> ee, repr(ee)
	(Uncertain(2.718, 0.001), 'Uncertain(2.718, 0.001)')
	>>> pie + ee
	Uncertain(5.858, 0.0100498756211)
	>>> pie * ee
	Uncertain(8.53452, 0.0273607748428)
	"""

	def __init__(self, value=0., error=0., *a, **t):
		self.value = value
		self.error = abs(error)
		super(Uncertain, self).__init__(*a, **t)

	# Conversions

	def __str__(self):
		return "%g+-%g" % (self.value, self.error)

	def __repr__(self):
		return "Uncertain(%s, %s)" % (self.value, self.error)

	def __complex__(self):
		return complex(self.value)

	def __int__(self):
		return int(self.value)

	def __long__(self):
		return long(self.value)

	def __float__(self):
		return self.value

	# Comparison

	def __eq__(self, other):
		epsilon = max(self.error, other.error)
		return abs(other.value - self.value) < epsilon

	def __ne__(self, other):
		return not (self == other)

	def __hash__(self):
		return hash(self.value) ^ hash(self.error)

	def __le__(self, other):
		return self.value < other.value or self == other

	def __lt__(self, other):
		return self.value < other.value and self != other

	def __gt__(self, other):
		return not (self <= other)

	def __ge__(self, other):
		return not (self < other)

	def __nonzero__(self):
		return self.error < abs(self.value)

	# Math

	def assign(self, other):
		if isinstance(other, Uncertain):
			self.value = other.value
			self.error = other.error
		else:
			self.value = other
			self.error = 0.

	def __add__(self, other):
		if isinstance(other, Uncertain):
			v = self.value + other.value
			e = (self.error**2 + other.error**2) ** .5
			return Uncertain(v, e)
		else:
			return Uncertain(self.value+other, self.error)

	def __sub__(self, other):
		return self + (-other)

	def __mul__(self, other):
		if isinstance(other, Uncertain):
			v = self.value * other.value
			e = ((self.error * other.value)**2 + (other.error * self.value)**2) ** .5
			return Uncertain(v, e)
		else:
			return Uncertain(self.value*other,
					self.error*other)

	def __div__(self, other):
		return self*(1./other)

	def __truediv__(self, other):
		return self*(1./other)

	def __radd__(self, other):
		return self + other

	def __rsub__(self, other):
		return -self + other

	def __rmul__(self, other):
		return self * other

	def __rdiv__(self, other):
		return (self/other)**-1.

	def __rtruediv__(self, other):
		return (self/other)**-1.

	def __neg__(self):
		return self*-1

	def __pos__(self):
		return self

	def __abs__(self):
		return Uncertain(abs(self.value), self.error)


class Enumeration(object):
	"""
	C-Style enumeration mapping attributes to numbers

	>>> Color = Enumeration("Color", ["Red", "Green", "Blue"])
	>>> Color.Red, Color.Green, Color.Blue
	(0, 1, 2)
	>>>
	>>> Color["Red"], Color.whatis(0)
	(0, 'Red')
	>>> Color.names(), Color.values()
	(['Blue', 'Green', 'Red'], [2, 1, 0])
	>>>
	>>> str(Color)
	"Color: {'Blue': 2, 'Green': 1, 'Red': 0}"
	>>>
	>>> 0 in Color, 10 in Color
	(True, False)
	>>> "Red" in Color, "Black" in Color
	(True, False)
	"""

	def __init__(self, name, enumList):
		self.__name__ = name
		self.__doc__ = name
		lookup = { }
		reverseLookup = { }

		i = 0
		uniqueNames = [ ]
		uniqueValues = [ ]
		for x in enumList:
			if type(x) == types.TupleType:
				x, i = x
			if type(x) != types.StringType:
				raise TypeError("enum name is not a string: " + x)
			if type(i) != types.IntType:
				raise TypeError("enum value is not an integer: " + str(i))
			if x in uniqueNames:
				raise ValueError("enum name is not unique: " + x)
			if i in uniqueValues:
				raise ValueError("enum value is not unique for " + x)
			uniqueNames.append(x)
			uniqueValues.append(i)
			lookup[x] = i
			reverseLookup[i] = x
			i = i + 1

		self.__lookup = lookup
		self.__reverseLookup = reverseLookup

	def whatis(self, value):
		return self.__reverseLookup[value]

	def names(self):
		return self.__lookup.keys()

	def values(self):
		return self.__lookup.values()

	def __getattr__(self, attr):
		if attr not in self.__lookup:
			raise (AttributeError)
		return self.__lookup[attr]

	def __str__(self):
		return str(self.__doc__)+": "+str(self.__lookup)

	def __len__(self):
		return len(self.__lookup)

	def __contains__(self, x):
		return (x in self.__lookup) or (x in self.__reverseLookup)

	def __getitem__(self, attr):
		return self.__lookup[attr]

	def __iter__(self):
		return self.__lookup.itervalues()

	def iterkeys(self):
		return self.__lookup.iterkeys()

	def itervalues(self):
		return self.__lookup.itervalues()

	def iteritems(self):
		return self.__lookup.iteritems()


def make_enum(cls):
	"""
	@todo Make more object orientated (inheritance?)
	"""
	name = cls.__name__
	values = cls.__values__
	return Enumeration(name, values)
