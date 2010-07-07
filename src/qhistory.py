#!/usr/bin/env python

"""
http://www.grigoriev.ru/svgmath/ (MathML->SVG in Python)
http://helm.cs.unibo.it/mml-widget/ (MathML widget in C++)
"""

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import util.misc as misc_utils
import history
import operation


_moduleLogger = logging.getLogger(__name__)


class RowData(object):

	HEADERS = ["", "Equation", "Result"]
	ALIGNMENT = [QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft]
	CLOSE_COLUMN = 0
	EQ_COLUMN = 1
	RESULT_COLUMN = 2

	def __init__(self, renderer, node, simpleNode):
		self._node = node
		self._simpleNode = simpleNode
		self._prettyRenderer = renderer

	@property
	def node(self):
		return self._node

	@property
	def simpleNode(self):
		return self._simpleNode

	@property
	def equation(self):
		return operation.render_operation(self._prettyRenderer, self._node),

	@property
	def result(self):
		return operation.render_operation(self._prettyRenderer, self._simpleNode),

	def data(self, column):
		if column == self.CLOSE_COLUMN:
			return ""
		elif column == self.EQ_COLUMN:
			return self.equation
		elif column == self.RESULT_COLUMN:
			return self.result
		else:
			return None


class HistoryModel(QtCore.QAbstractItemModel):

	def __init__(self, parent=None):
		super(HistoryModel, self).__init__(parent)

		self._children = []

	@misc_utils.log_exception(_moduleLogger)
	def columnCount(self, parent):
		if parent.isValid():
			return 0
		else:
			return len(RowData.HEADERS)

	@misc_utils.log_exception(_moduleLogger)
	def data(self, index, role):
		if not index.isValid():
			return None
		elif role == QtCore.Qt.DecorationRole:
			if index.column() == RowData.CLOSE_COLUMN:
				return None
			else:
				return None
		elif role == QtCore.Qt.TextAlignmentRole:
			return RowData.ALIGNMENT[index.column()]
		elif role != QtCore.Qt.DisplayRole:
			return None

		item = index.internalPointer()
		if isinstance(item, RowData):
			return item.data(index.column())
		elif item is RowData.HEADERS:
			return item[index.column()]

	@misc_utils.log_exception(_moduleLogger)
	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.NoItemFlags

		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	@misc_utils.log_exception(_moduleLogger)
	def headerData(self, section, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return RowData.HEADERS[section]

		return None

	@misc_utils.log_exception(_moduleLogger)
	def index(self, row, column, parent):
		if not self.hasIndex(row, column, parent):
			return QtCore.QModelIndex()

		if parent.isValid():
			return QtCore.QModelIndex()

		parentItem = RowData.HEADERS
		childItem = self._children[row]
		if childItem:
			return self.createIndex(row, column, childItem)
		else:
			return QtCore.QModelIndex()

	@misc_utils.log_exception(_moduleLogger)
	def parent(self, index):
		if not index.isValid():
			return QtCore.QModelIndex()

		childItem = index.internalPointer()
		if isinstance(childItem, RowData):
			return QtCore.QModelIndex()
		elif childItem is RowData.HEADERS:
			return None

	@misc_utils.log_exception(_moduleLogger)
	def rowCount(self, parent):
		if 0 < parent.column():
			return 0

		if not parent.isValid():
			return len(self._children)
		else:
			return len(self._children)

	def push(self, row):
		self._children.append(row)
		self._signal_rows_added()

	def pop(self):
		data = self._children[-1]
		del self._children[-1]
		self._signal_rows_removed()
		return data

	def peek(self):
		data = self._children[-1]
		return data

	def clear(self):
		del self._children[:]
		self._all_changed

	def __len__(self):
		return len(self._children)

	def __iter__(self):
		return iter(self._children)

	def _signal_rows_added(self):
		# @todo Only signal new rows
		self._all_changed

	def _signal_rows_removed(self):
		# @todo Only signal new rows
		self._all_changed

	def _all_changed(self):
		topLeft = self.createIndex(0, 0, self._children[0])
		bottomRight = self.createIndex(len(self._children)-1, len(RowData.HEADERS)-1, self._children[-1])
		self.dataChanged.emit(topLeft, bottomRight)


class QCalcHistory(history.AbstractHistory):

	def __init__(self):
		super(QCalcHistory, self).__init__()
		self._prettyRenderer = operation.render_number()

		self._historyStore = HistoryModel()

		self._historyView = QtGui.QTreeView()
		self._historyView.setModel(self._historyStore)
		self._historyView.setUniformRowHeights(True)
		self._historyView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self._historyView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._historyView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self._historyView.setHeaderHidden(True)

		viewHeader = self._historyView.header()
		viewHeader.setSortIndicatorShown(True)
		viewHeader.setClickable(True)

		viewHeader.setResizeMode(RowData.CLOSE_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setResizeMode(RowData.EQ_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setResizeMode(RowData.RESULT_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setStretchLastSection(False)

	@property
	def toplevel(self):
		return self._historyView

	def push(self, node):
		simpleNode = node.simplify()
		row = RowData(self._prettyRenderer, node, simpleNode)
		self._historyStore.push(row)

		# @todo Scroll to bottom

	def pop(self):
		if len(self._historyStore) == 0:
			raise IndexError("Not enough items in the history for the operation")

		row = self._historyStore.pop()
		return row.node

	def peek(self):
		if len(self._historyStore) == 0:
			raise IndexError("Not enough items in the history for the operation")
		row = self._historyStore.peek()
		return row.node

	def clear(self):
		self._historyStore.clear()

	def __len__(self):
		return len(self._historyStore)

	def __iter__(self):
		for row in iter(self._historyStore):
			yield row.node
