#!/usr/bin/env python

"""
Example Operators for comparison
>>> class C(object):
...     def __init__(self, x):
...         self.x = x
...
>>> x, y, z = C(1), C(1), C(2)
>>> x == y, hash(x) == hash(y)
(False, False)
"""


import operator
import itertools


class KeyedEqualityOperators(object):
	"""
	Mixin for auto-implementing comparison operators
	@note Requires inheriting class to implement a '__key__' function
	Example:
	>>> class C(KeyedEqualityOperators):
	...     def __init__(self, x):
	...         self.x = x
	...     def __key__(self):
	...         return self.x
	...
	>>> x, y, z = C(1), C(1), C(2)
	>>> x == y, hash(x) == hash(y)
	(True, False)
	"""

	def __init__(self):
		self.__key__ = None

	def __eq__(self, other):
		return self.__key__() == other.__key__()

	def __ne__(self, other):
		return self.__key__() != other.__key__()


class KeyedComparisonOperators(KeyedEqualityOperators):
	"""
	Mixin for auto-implementing comparison operators
	@note Requires inheriting class to implement a '__key__' function
	Example:
	>>> class C(KeyedComparisonOperators):
	...     def __init__(self, x):
	...         self.x = x
	...     def __key__(self):
	...         return self.x
	...
	>>> x, y, z = C(1), C(1), C(2)
	>>> x == y, y < z, hash(x) == hash(y)
	(True, True, False)
	"""

	def __init__(self):
		self.__key__ = None

	def __cmp__(self, other):
		return cmp(self.__key__(), other.__key__())

	def __lt__(self, other):
		return self.__key__() < other.__key__()

	def __le__(self, other):
		return self.__key__() <= other.__key__()

	def __gt__(self, other):
		return self.__key__() > other.__key__()

	def __ge__(self, other):
		return self.__key__() >= other.__key__()


class KeyedHashing(object):
	"""
	Mixin for auto-implementing comparison operators
	@note Requires inheriting class to implement a '__key__' function
	Example:
	>>> class C(KeyedHashing):
	...     def __init__(self, x):
	...         self.x = x
	...     def __key__(self):
	...         return self.x
	...
	>>> x, y, z = C(1), C(1), C(2)
	>>> x == y, hash(x) == hash(y)
	(False, True)
	"""

	def __init__(self):
		self.__key__ = None

	def __hash__(self):
		return hash(self.__key__())


class NotEqualOperator(object):
	"""
	Mixin for auto-implementing comparison operators
	@note Requires inheriting class to implement '__eq__' function
	"""

	def __ne__(self, other):
		return not (self == other)


class ComparisonOperators(NotEqualOperator):
	"""
	Mixin for auto-implementing comparison operators
	@note Requires inheriting class to implement '__lt__' function
	"""

	def __le__(self, other):
		return(self < other) or(self == other)

	def __gt__(self, other):
		return not(self <= other)

	def __ge__(self, other):
		return not(self < other)


class infix(object):
	"""
	Recipe #384122
	http://code.activestate.com/recipes/384122/

	>>> import operator
	>>> x = infix(operator.mul)
	>>> 1 |x| 2 |x| 10
	20
	"""

	def __init__(self, func):
		self.__name__ = func.__name__
		self.__doc__ = func.__doc__
		try:
			self.__dict__.update(func.__dict__)
		except AttributeError:
			pass
		self.function = func

	def __ror__(self, other):
		return infix(lambda x: self.function(other, x))

	def __or__(self, other):
		return self.function(other)

	def __call__(self, lhs, rhs):
		return self.function(lhs, rhs)


class Just(object):
	"""
	@see mreturn
	"""

	def __init__(self, value):
		self.value = value


@infix
def mbind(maybe, func):
	"""
	@see mreturn
	"""
	if maybe is None:
		return None
	else:
		return func(maybe.value)


def mreturn(value):
	"""
	>>> class Sheep(object):
	... 	def __init__(self, name):
	... 		self.name = name
	... 		self.mother = None
	... 		self.father = None
	...
	>>> def father(sheep):
	... 	if sheep.father is None:
	... 		return None
	... 	else:
	... 		return Just(sheep.father)
	...
	>>> def mother(sheep):
	... 	if sheep.mother is None:
	... 		return None
	... 	else:
	... 		return Just(sheep.mother)
	...
	>>> def mothersFather(sheep):
	... 	return mreturn(sheep) |mbind| mother |mbind| father
	...
	>>> def mothersPaternalGrandfather(sheep):
	... 	return mreturn(sheep) |mbind| mother |mbind| father |mbind| father
	...
	>>> shawn = Sheep("Shawn")
	>>> gertrude = Sheep("Gertrude")
	>>> ernie = Sheep("Ernie")
	>>> frank = Sheep("Frank")
	>>>
	>>> shawn.mother = gertrude
	>>> gertrude.father = ernie
	>>> ernie.father = frank
	>>>
	>>> print mothersFather(shawn).value.name
	Ernie
	>>> print mothersPaternalGrandfather(shawn).value.name
	Frank
	>>> print mothersPaternalGrandfather(ernie)
	None
	"""
	return Just(value)


def xor(*args):
	truth = itertools.imap(operator.truth, args)
	return reduce(operator.xor, truth)


def equiv(*args):
	truth = itertools.imap(operator.truth, args)
	return reduce(lambda a, b: not operator.xor(a, b), truth)
