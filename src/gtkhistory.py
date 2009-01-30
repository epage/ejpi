#!/usr/bin/env python

"""
http://www.grigoriev.ru/svgmath/ (MathML->SVG in Python)
http://helm.cs.unibo.it/mml-widget/ (MathML widget in C++)
"""


import gobject
import gtk


import history
import operation


class GtkCalcHistory(history.AbstractHistory):

	BUTTON_IDX = 0
	VIEW_DATA_IDX = 1
	VIEW_RESULT_IDX = 2
	DATA_IDX = 3
	RESULT_IDX = 4

	def __init__(self, view):
		super(GtkCalcHistory, self).__init__()
		self.__prettyRenderer = operation.render_number()
		self._historyView = view

		# stock-id, display, value
		self.__historyStore = gtk.ListStore(
			gobject.TYPE_STRING, # stock id for pixbuf
			gobject.TYPE_STRING, # view of data
			gobject.TYPE_STRING, # view of result
			object, # data
			object, # result
		)
		self._historyView.set_model(self.__historyStore)

		# create the TreeViewColumns to display the data
		self.__closeColumn = gtk.TreeViewColumn('')
		self._historyView.append_column(self.__closeColumn)

		self.__historyColumn = gtk.TreeViewColumn('History')
		self.__historyColumn.set_sort_column_id(0)
		self.__historyColumn.set_expand(True)
		self._historyView.append_column(self.__historyColumn)

		self.__resultColumn = gtk.TreeViewColumn('')
		self.__resultColumn.set_sort_column_id(0)
		self._historyView.append_column(self.__resultColumn)

		# create a CellRenderers to render the data
		self.__closeCell = gtk.CellRendererPixbuf()
		self.__closeColumn.pack_start(self.__closeCell, False)
		self.__closeColumn.set_attributes(self.__closeCell, stock_id=0)

		self.__expressionCell = gtk.CellRendererText()
		self.__historyColumn.pack_start(self.__expressionCell, True)
		self.__historyColumn.set_attributes(self.__expressionCell, text=1)

		self.__valueCell = gtk.CellRendererText()
		self.__resultColumn.pack_end(self.__valueCell, False)
		self.__resultColumn.set_attributes(self.__valueCell, text=2)

		self._historyView.set_reorderable(True)
		self._historyView.connect("row-activated", self._on_close_activated)

	def push(self, node):
		simpleNode = node.simplify()
		self.__historyStore.prepend([
			gtk.STOCK_CLOSE,
			operation.render_operation(self.__prettyRenderer, node),
			operation.render_operation(self.__prettyRenderer, simpleNode),
			node,
			simpleNode
		])

	def pop(self):
		if len(self.__historyStore) == 0:
			raise IndexError("Not enough items in the history for the operation")

		row = self.__historyStore[0]
		data = row[self.DATA_IDX]
		del self.__historyStore[0]

		return data

	def peek(self):
		if len(self.__historyStore) == 0:
			raise IndexError("Not enough items in the history for the operation")
		row = self.__historyStore[0]
		data = row[self.DATA_IDX]
		return data

	def clear(self):
		self.__historyStore.clear()

	def __len__(self):
		return len(self.__historyStore)

	def __iter__(self):
		for row in iter(self.__historyStore):
			data = row[self.DATA_IDX]
			yield data

	def _on_close_activated(self, treeView, path, viewColumn):
		if viewColumn is self.__closeColumn:
			del self.__historyStore[path[0]]
		elif viewColumn is self.__resultColumn:
			row = self.__historyStore[path[0]]
			data = row[self.RESULT_IDX]
			self.push(data)
		elif viewColumn is self.__historyColumn:
			row = self.__historyStore[path[0]]
			data = row[self.DATA_IDX]
			self.push(data)
		else:
			assert False
