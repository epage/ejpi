#!/usr/bin/env python

"""
http://www.grigoriev.ru/svgmath/ (MathML->SVG in Python)
http://helm.cs.unibo.it/mml-widget/ (MathML widget in C++)
"""

from __future__ import with_statement

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

from util import qui_utils
import util.misc as misc_utils
import history
import operation


_moduleLogger = logging.getLogger(__name__)


class QCalcHistory(history.AbstractHistory):

	_CLOSE_COLUMN = 0
	_EQ_COLUMN = 1
	_RESULT_COLUMN = 2

	def __init__(self, errorReporter):
		super(QCalcHistory, self).__init__()
		self._prettyRenderer = operation.render_number()
		self._errorLog = errorReporter

		self._historyStore = QtGui.QStandardItemModel()
		self._historyStore.setHorizontalHeaderLabels(["", "Equation", "Result"])
		self._historyStore.itemChanged.connect(self._on_item_changed)

		self._historyView = QtGui.QTreeView()
		self._historyView.setModel(self._historyStore)
		self._historyView.setUniformRowHeights(True)
		self._historyView.setRootIsDecorated(False)
		self._historyView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self._historyView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._historyView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self._historyView.setHeaderHidden(True)
		self._historyView.activated.connect(self._on_row_activated)

		viewHeader = self._historyView.header()
		viewHeader.setSortIndicatorShown(True)
		viewHeader.setClickable(True)

		viewHeader.setResizeMode(self._CLOSE_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setResizeMode(self._EQ_COLUMN, QtGui.QHeaderView.Stretch)
		viewHeader.setResizeMode(self._RESULT_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setStretchLastSection(False)

		self._rowCount = 0
		self._programmaticUpdate = False
		self._closeIcon = qui_utils.get_theme_icon(("window-close", "general_close", "gtk-close"))

	@property
	def toplevel(self):
		return self._historyView

	def push(self, node):
		simpleNode = node.simplify()

		closeIcon = self._closeIcon
		icon = QtGui.QStandardItem(closeIcon, "")
		icon.setEditable(False)
		icon.setCheckable(False)
		equation = QtGui.QStandardItem(operation.render_operation(self._prettyRenderer, node))
		equation.setData(node)
		equation.setCheckable(False)
		eqFont = equation.font()
		eqFont.setPointSize(max(eqFont.pointSize() - 3, 5))
		equation.setFont(eqFont)

		result = QtGui.QStandardItem(operation.render_operation(self._prettyRenderer, simpleNode))
		result.setData(simpleNode)
		result.setEditable(False)
		result.setCheckable(False)

		row = (icon, equation, result)
		self._historyStore.appendRow(row)

		index = result.index()
		self._historyView.scrollToBottom()
		self._rowCount += 1

	def pop(self):
		if len(self) == 0:
			raise IndexError("Not enough items in the history for the operation")

		icon, equation, result = self._historyStore.takeRow(self._rowCount - 1)
		self._rowCount -= 1
		return equation.data().toPyObject()

	def peek(self):
		if len(self) == 0:
			raise IndexError("Not enough items in the history for the operation")

		icon, equation, result = self._historyStore.takeRow(self._rowCount - 1)
		row = (icon, equation, result)
		self._historyStore.appendRow(row)

		return equation.data().toPyObject()

	def clear(self):
		self._historyStore.clear()
		self._rowCount = 0

	def scroll_to_bottom(self):
		self._historyView.scrollToBottom()

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, index):
		with qui_utils.notify_error(self._errorLog):
			if index.column() == self._CLOSE_COLUMN:
				self._historyStore.removeRow(index.row(), index.parent())
				self._rowCount -= 1
			elif index.column() == self._EQ_COLUMN:
				self._duplicate_row(index)
			elif index.column() == self._RESULT_COLUMN:
				self._duplicate_row(index)
			else:
				raise NotImplementedError("Unsupported column to activate %s" % index.column())

	@misc_utils.log_exception(_moduleLogger)
	def _on_item_changed(self, item):
		with qui_utils.notify_error(self._errorLog):
			if self._programmaticUpdate:
				_moduleLogger.info("Blocking updating %r recursively" % item)
				return
			self._programmaticUpdate = True
			try:
				if item.column() in [self._EQ_COLUMN, self._RESULT_COLUMN]:
					self._update_input(item)
				else:
					raise NotImplementedError("Unsupported column to edit %s" % item.column())
			except StandardError, e:
				self._errorReporter.push_exception()
			finally:
				self._programmaticUpdate = False

	def _duplicate_row(self, index):
		item = self._historyStore.item(index.row(), self._EQ_COLUMN)
		self.push(item.data().toPyObject())

	def _parse_value(self, value):
		raise NotImplementedError("What?")

	def _update_input(self, item):
		node = item.data().toPyObject()
		try:
			eqNode = self._parse_value(str(item.text()))
			newText = operation.render_operation(self._prettyRenderer, eqNode)

			eqItem = self._historyStore.item(item.row(), self._EQ_COLUMN)
			eqItem.setData(eqNode)
			eqItem.setText(newText)

			resultNode = eqNode.simplify()
			resultText = operation.render_operation(self._prettyRenderer, resultNode)
			resultItem = self._historyStore.item(item.row(), self._RESULT_COLUMN)
			resultItem.setData(resultNode)
			resultItem.setText(resultText)
		except:
			oldText = operation.render_operation(self._prettyRenderer, node)
			item.setText(oldText)
			raise

	def __len__(self):
		return self._rowCount

	def __iter__(self):
		for i in xrange(self._rowCount):
			item = self._historyStore.item(i, self._EQ_COLUMN)
			if item is None:
				continue
			yield item.data().toPyObject()
