#!/usr/bin/env python


import itertools
import functools
import decimal

from libraries.recipes import overloading
from libraries.recipes import algorithms


@overloading.overloaded
def serialize_value(value, base, renderer):
	yield renderer(value, base)


@serialize_value.register(complex, overloading.AnyType, overloading.AnyType)
def serialize_complex(value, base, renderer):
	if value.real == 0.0:
		yield renderer(value.imag*1j, base)
	elif value.imag == 0.0:
		yield renderer(value.real, base)
	else:
		yield renderer(value.real, base)
		yield renderer(value.imag*1j, base)
		yield "+"


def render_float(value):
	return str(value)


def render_float_dec(value):
	floatText = str(value)
	dec = decimal.Decimal(floatText)
	return str(dec)


def render_float_eng(value):
	floatText = str(value)
	dec = decimal.Decimal(floatText)
	return dec.to_eng_string()


def render_float_sci(value):
	floatText = str(value)
	dec = decimal.Decimal(floatText)
	return dec.to_sci_string()


def render_complex(floatRender):

	def render_complex_real(value):
		realRendered = floatRender(value.real)
		imagRendered = floatRender(value.imag)
		rendered = "%s+%sj" % (realRendered, imagRendered)
		return rendered

	return render_complex_real


def _seperate_num(rendered, sep, count):
	"""
	>>> _seperate_num("123", ",", 3)
	'123'
	>>> _seperate_num("123456", ",", 3)
	'123,456'
	>>> _seperate_num("1234567", ",", 3)
	'1,234,567'
	"""
	leadCount = len(rendered) % count
	choppyRest = algorithms.itergroup(rendered[leadCount:], count)
	rest = (
		"".join(group)
		for group in choppyRest
	)
	if 0 < leadCount:
		lead = rendered[0:leadCount]
		parts = itertools.chain((lead, ), rest)
	else:
		parts = rest
	return sep.join(parts)


def render_integer_oct(value, sep=""):
	rendered = oct(int(value))
	if 0 < len(sep):
		assert rendered.startswith("0")
		rendered = "0o%s" % _seperate_num(rendered[1:], sep, 3)
	return rendered


def render_integer_dec(value, sep=""):
	rendered = str(int(value))
	if 0 < len(sep):
		rendered = "%s" % _seperate_num(rendered, sep, 3)
	return rendered


def render_integer_hex(value, sep=""):
	rendered = hex(int(value))
	if 0 < len(sep):
		assert rendered.startswith("0x")
		rendered = "0x%s" % _seperate_num(rendered[2:], sep, 3)
	return rendered


def set_render_int_seperator(renderer, sep):

	@functools.wrap(renderer)
	def render_with_sep(value):
		return renderer(value, sep)

	return render_with_sep


class render_number(object):

	def __init__(self,
		ints = None,
		f = None,
		c = None,
	):
		if ints is not None:
			self.render_int = ints
		else:
			self.render_int = {
				2: render_integer_hex,
				8: render_integer_oct,
				10: render_integer_dec,
				16: render_integer_hex,
			}
		self.render_float = f if c is not None else render_float
		self.render_complex = c if c is not None else self

	def __call__(self, value, base):
		return self.render(value, base)

	@overloading.overloaded
	def render(self, value, base):
		return str(value)

	@render.register(overloading.AnyType, int, overloading.AnyType)
	def _render_int(self, value, base):
		renderer = self.render_int.get(base, render_integer_dec)
		return renderer(value)

	@render.register(overloading.AnyType, float, overloading.AnyType)
	def _render_float(self, value, base):
		return self.render_float(value)

	@render.register(overloading.AnyType, complex, overloading.AnyType)
	def _render_complex(self, value, base):
		return self.render_float(value)


class Operation(object):

	def __init__(self):
		self._base = 10

	def __str__(self):
		raise NotImplementedError

	@property
	def base(self):
		base = self._base
		return base

	def get_children(self):
		return []

	def serialize(self, renderer):
		for child in self.get_children():
			for childItem in child.serialize(renderer):
				yield childItem

	def simplify(self):
		"""
		@returns an operation tree with all constant calculations performed and only variables left
		"""
		raise NotImplementedError

	def evaluate(self):
		"""
		@returns a value that the tree represents, if it can't be evaluated,
			then an exception is throwd
		"""
		raise NotImplementedError

	def __call__(self):
		return self.evaluate()


class Value(Operation):

	def __init__(self, value, base):
		super(Value, self).__init__()
		self.value = value
		self._base = base

	def serialize(self, renderer):
		for item in super(Value, self).serialize(renderer):
			yield item
		for component in serialize_value(self.value, self.base, renderer):
			yield component

	def __str__(self):
		return str(self.value)

	def simplify(self):
		return self

	def evaluate(self):
		return self.value


class Constant(Operation):

	def __init__(self, name, valueNode):
		super(Constant, self).__init__()
		self.name = name
		self.__valueNode = valueNode

	def serialize(self, renderer):
		for item in super(Constant, self).serialize(renderer):
			yield item
		yield self.name

	def __str__(self):
		return self.name

	def simplify(self):
		return self.__valueNode.simplify()

	def evaluate(self):
		return self.__valueNode.evaluate()


class Variable(Operation):

	def __init__(self, name):
		super(Variable, self).__init__()
		self.name = name

	def serialize(self, renderer):
		for item in super(Variable, self).serialize(renderer):
			yield item
		yield self.name

	def __str__(self):
		return self.name

	def simplify(self):
		return self

	def evaluate(self):
		raise KeyError


class Function(Operation):

	REP_FUNCTION = 0
	REP_PREFIX = 1
	REP_INFIX = 2
	REP_POSTFIX = 3

	_op = None
	_rep = REP_FUNCTION
	symbol = None
	argumentCount = 0

	def __init__(self, *args, **kwd):
		super(Function, self).__init__()
		self._base = None
		self._args = args
		self._kwd = kwd
		self._simple = self._simplify()
		self._str = self.pretty_print(args, kwd)

	def serialize(self, renderer):
		for item in super(Function, self).serialize(renderer):
			yield item
		yield self.symbol

	def get_children(self):
		return (
			arg
			for arg in self._args
		)

	@property
	def base(self):
		base = self._base
		if base is None:
			bases = [arg.base for arg in self._args]
			base = bases[0]
		assert base is not None
		return base

	def __str__(self):
		return self._str

	def simplify(self):
		return self._simple

	def evaluate(self):
		selfArgs = [arg.evaluate() for arg in self._args]
		return Value(self._op(*selfArgs))

	def _simplify(self):
		selfArgs = [arg.simplify() for arg in self._args]
		selfKwd = dict(
			(name, arg.simplify())
			for (name, arg) in self._kwd
		)

		try:
			args = [arg.evaluate() for arg in selfArgs]
			base = self.base
			result = self._op(*args)

			node = Value(result, base)
		except KeyError:
			node = self

		return node

	@classmethod
	def pretty_print(cls, args = None, kwds = None):
		if args is None:
			args = []
		if kwds is None:
			kwds = {}

		if cls._rep == cls.REP_FUNCTION:
			positional = (str(arg) for arg in args)
			named = (
				"%s=%s" % (str(key), str(value))
				for (key, value) in kwds.iteritems()
			)
			return "%s(%s)" % (
				cls.symbol,
				", ".join(itertools.chain(named, positional)),
			)
		elif cls._rep == cls.REP_PREFIX:
			assert len(args) == 1
			return "%s %s" % (cls.symbol, args[0])
		elif cls._rep == cls.REP_POSTFIX:
			assert len(args) == 1
			return "%s %s" % (args[0], cls.symbol)
		elif cls._rep == cls.REP_INFIX:
			assert len(args) == 2
			return "(%s %s %s)" % (
				str(args[0]),
				str(cls.symbol),
				str(args[1]),
			)
		else:
			raise AssertionError("Unsupported rep style")


def generate_function(op, rep, style, numArgs):

	class GenFunc(Function):

		def __init__(self, *args, **kwd):
			super(GenFunc, self).__init__(*args, **kwd)

		_op = op
		_rep = style
		symbol = rep
		argumentCount = numArgs

	GenFunc.__name__ = op.__name__
	return GenFunc


def change_base(base, rep):

	class GenFunc(Function):

		def __init__(self, *args, **kwd):
			super(GenFunc, self).__init__(*args, **kwd)
			self._base = base
			self._simple = self._simplify()
			self._str = self.pretty_print(args, kwd)

		_op = lambda self, n: n
		_rep = Function.REP_FUNCTION
		symbol = rep
		argumentCount = 1

	GenFunc.__name__ = rep
	return GenFunc


@overloading.overloaded
def render_operation(render_func, operation):
	return str(operation)


@render_operation.register(overloading.AnyType, Value)
def render_value(render_func, operation):
	return render_func(operation.value, operation.base)


@render_operation.register(overloading.AnyType, Variable)
@render_operation.register(overloading.AnyType, Constant)
def render_variable(render_func, operation):
	return operation.name


@render_operation.register(overloading.AnyType, Function)
def render_function(render_func, operation):
	args = [
		render_operation(render_func, arg)
		for arg in operation.get_children()
	]
	return operation.pretty_print(args)
