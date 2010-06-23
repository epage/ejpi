#!/usr/bin/env python

import math

from PyQt4 import QtGui
from PyQt4 import QtCore


class QActionPieItem(object):

	def __init__(self, action, weight = 1):
		self._action = action
		self._weight = weight

	def action(self):
		return self._action

	def setWeight(self, weight):
		self._weight = weight

	def weight(self):
		return self._weight

	def setEnabled(self, enabled = True):
		self._action.setEnabled(enabled)

	def isEnabled(self):
		return self._action.isEnabled()


class QPieMenu(QtGui.QWidget):

	INNER_RADIUS_DEFAULT = 24
	OUTER_RADIUS_DEFAULT = 64
	ICON_SIZE_DEFAULT = 32

	activated = QtCore.pyqtSignal((), (int, ))
	highlighted = QtCore.pyqtSignal(int)
	canceled = QtCore.pyqtSignal()
	aboutToShow = QtCore.pyqtSignal()
	aboutToHide = QtCore.pyqtSignal()

	def __init__(self, parent = None):
		QtGui.QWidget.__init__(self, parent)
		self._innerRadius = self.INNER_RADIUS_DEFAULT
		self._outerRadius = self.OUTER_RADIUS_DEFAULT
		self._children = []
		self._selectionIndex = -2

		self._motion = 0
		self._mouseButtonPressed = True
		self._mousePosition = ()

		canvasSize = self._outerRadius * 2 + 1
		self._canvas = QtGui.QPixmap(canvasSize, canvasSize)
		self._mask = None

	def popup(self, pos):
		index = self.indexAt(self.mapFromGlobal(QtGui.QCursor.pos()))
		self._mousePosition = pos
		self.show()

	def insertItem(self, item, index = -1):
		self._children.insert(index, item)
		self._invalidate_view()

	def removeItemAt(self, index):
		item = self._children.pop(index)
		self._invalidate_view()

	def clear(self):
		del self._children[:]
		self._invalidate_view()

	def itemAt(self, index):
		return self._children[index]

	def indexAt(self, point):
		return self._angle_to_index(self._angle_at(point))

	def setHighlightedItem(self, index):
		pass

	def highlightedItem(self):
		pass

	def innerRadius(self):
		return self._innerRadius

	def setInnerRadius(self, radius):
		self._innerRadius = radius

	def outerRadius(self):
		return self._outerRadius

	def setOuterRadius(self, radius):
		self._outerRadius = radius
		self._canvas = self._canvas.scaled(self.sizeHint())

	def sizeHint(self):
		diameter = self._outerRadius * 2 + 1
		return QtCore.QSize(diameter, diameter)

	def showEvent(self, showEvent):
		self.aboutToShow.emit()

		if self._mask is None:
			self._mask = QtGui.QBitmap(self._canvas.size())
			self._mask.fill(QtCore.Qt.color0)
			self._generate_mask(self._mask)
			self._canvas.setMask(self._mask)
			self.setMask(self._mask)

		self._motion = 0

		lastMousePos = self.mapFromGlobal(QtGui.QCursor.pos())
		radius = self._radius_at(lastMousePos)
		if self._innerRadius <= radius and radius <= self._outerRadius:
			self._select_at(self._angle_to_index(lastMousePos))
		else:
			if radius < self._innerRadius:
				self._selectionIndex = -1
			else:
				self._selectionIndex = -2

		QtGui.QWidget.showEvent(self, showEvent)

	def hideEvent(self, hideEvent):
		self.canceled.emit()
		self._selectionIndex = -2
		QtGui.QWidget.hideEvent(self, hideEvent)

	def paintEvent(self, paintEvent):
		painter = QtGui.QPainter(self._canvas)
		painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

		adjustmentRect = self._canvas.rect().adjusted(0, 0, -1, -1)

		numChildren = len(self._children)
		if numChildren < 2:
			if self._selectionIndex == 0 and self._children[0].isEnabled():
				painter.setBrush(self.palette().highlight())
			else:
				painter.setBrush(self.palette().background())

			painter.fillRect(self.rect(), painter.brush())
		else:
			for i, child in enumerate(self._children):
				if i == self._selectionIndex:
					painter.setBrush(self.palette().highlight())
				else:
					painter.setBrush(self.palette().background())
				painter.setPen(self.palette().mid().color())

				a = self._index_to_angle(i, True)
				b = self._index_to_angle(i + 1, True)
				if b < a:
					b += 2*math.pi
				size = b - a
				if size < 0:
					size += 2*math.pi

				startAngleInDeg = (a * 360 * 16) / (2*math.pi)
				sizeInDeg = (size * 360 * 16) / (2*math.pi)
				painter.drawPie(adjustmentRect, int(startAngleInDeg), int(sizeInDeg))

		dark = self.palette().dark().color()
		light = self.palette().light().color()
		if self._selectionIndex == -1:
			background = self.palette().highlight().color()
		else:
			background = self.palette().background().color()

		innerRect = QtCore.QRect(
			adjustmentRect.center().x() - self._innerRadius,
			adjustmentRect.center().y() - self._innerRadius,
			self._innerRadius * 2 + 1,
			self._innerRadius * 2 + 1,
		)

		painter.setPen(QtCore.Qt.NoPen)
		painter.setBrush(background)
		painter.drawPie(innerRect, 0, 360 * 16)

		painter.setPen(QtGui.QPen(dark, 1))
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.drawEllipse(innerRect)

		painter.setPen(QtGui.QPen(dark, 1))
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.drawEllipse(adjustmentRect)

		r = QtCore.QRect(innerRect)
		innerRect.setLeft(r.center().x() + ((r.left() - r.center().x()) / 3) * 1)
		innerRect.setRight(r.center().x() + ((r.right() - r.center().x()) / 3) * 1)
		innerRect.setTop(r.center().y() + ((r.top() - r.center().y()) / 3) * 1)
		innerRect.setBottom(r.center().y() + ((r.bottom() - r.center().y()) / 3) * 1)

		if self._selectionIndex == -1:
			text = self.palette().highlightedText().color()
		else:
			text = self.palette().text().color()

		for i, child in enumerate(self._children):
			text = child.action().text()

			a = self._index_to_angle(i, True)
			b = self._index_to_angle(i + 1, True)
			if b < a:
				b += 2*math.pi
			middleAngle = (a + b) / 2
			averageRadius = (self._innerRadius + self._outerRadius) / 2

			sliceX = averageRadius * math.cos(middleAngle)
			sliceY = - averageRadius * math.sin(middleAngle)

			pieX = self._canvas.rect().center().x()
			pieY = self._canvas.rect().center().y()

			fontMetrics = painter.fontMetrics()
			if text:
				textBoundingRect = fontMetrics.boundingRect(text)
			else:
				textBoundingRect = QtCore.QRect()
			textWidth = textBoundingRect.width()
			textHeight = textBoundingRect.height()

			icon = child.action().icon().pixmap(
				QtCore.QSize(self.ICON_SIZE_DEFAULT, self.ICON_SIZE_DEFAULT),
				QtGui.QIcon.Normal,
				QtGui.QIcon.On,
			)
			averageWidth = (icon.width() + textWidth)/2
			if not icon.isNull():
				iconRect = QtCore.QRect(
					pieX + sliceX - averageWidth,
					pieY + sliceY - icon.height()/2,
					icon.width(),
					icon.height(),
				)

				painter.drawPixmap(iconRect, icon)

			if text:
				if i == self._selectionIndex:
					if child.action().isEnabled():
						pen = self.palette().highlightedText()
						brush = self.palette().highlight()
					else:
						pen = self.palette().mid()
						brush = self.palette().background()
				else:
					if child.action().isEnabled():
						pen = self.palette().text()
					else:
						pen = self.palette().mid()
					brush = self.palette().background()

				leftX = pieX + sliceX - averageWidth + icon.width()
				topY = pieY + sliceY + textHeight/2
				painter.setPen(pen.color())
				painter.setBrush(brush)
				painter.drawText(leftX, topY, text)

		screen = QtGui.QPainter(self)
		screen.drawPixmap(QtCore.QPoint(0, 0), self._canvas)

		QtGui.QWidget.paintEvent(self, paintEvent)

	def __len__(self):
		return len(self._children)

	def _invalidate_view(self):
		pass

	def _generate_mask(self, mask):
		"""
		Specifies on the mask the shape of the pie menu
		"""
		painter = QtGui.QPainter(mask)
		painter.setPen(QtCore.Qt.color1)
		painter.setBrush(QtCore.Qt.color1)
		painter.drawEllipse(mask.rect().adjusted(0, 0, -1, -1))

	def _select_at(self, index):
		self._selectionIndex = index

		numChildren = len(self._children)
		loopDelta = max(numChildren, 1)
		while self._selectionIndex < 0:
			self._selectionIndex += loopDelta
		while numChildren <= self._selectionIndex:
			self._selectionIndex -= loopDelta

	def _activate_at(self, index):
		child = self.itemAt(index)
		if child.action.isEnabled:
			child.action.trigger()
		self.activated.emit()
		self.aboutToHide.emit()
		self.hide()

	def _index_to_angle(self, index, isShifted):
		index = index % len(self._children)

		totalWeight = sum(child.weight() for child in self._children)
		if totalWeight == 0:
			totalWeight = 1
		baseAngle = (2 * math.pi) / totalWeight

		angle = math.pi / 2
		if isShifted:
			if self._children:
				angle -= (self._children[0].weight() * baseAngle) / 2
			else:
				angle -= baseAngle / 2
		while angle < 0:
			angle += 2*math.pi

		for i, child in enumerate(self._children):
			if index < i:
				break
			angle += child.weight() * baseAngle
		while (2*math.pi) < angle:
			angle -= 2*math.pi

		return angle

	def _angle_to_index(self, angle):
		numChildren = len(self._children)
		if numChildren == 0:
			return -1

		totalWeight = sum(child.weight() for child in self._children)
		if totalWeight == 0:
			totalWeight = 1
		baseAngle = (2 * math.pi) / totalWeight

		iterAngle = math.pi / 2 - (self.itemAt(0).weight * baseAngle) / 2
		while iterAngle < 0:
			iterAngle += 2 * math.pi

		oldIterAngle = iterAngle
		for index, child in enumerate(self._children):
			iterAngle += child.weight * baseAngle
			if oldIterAngle < iterAngle and angle <= iterAngle:
				return index
			elif oldIterAngle < (iterAngle + 2*math.pi) and angle <= (iterAngle + 2*math.pi):
				return index
			oldIterAngle = iterAngle

	def _radius_at(self, pos):
		xDelta = pos.x() - self.rect().center().x()
		yDelta = pos.y() - self.rect().center().y()

		radius = math.sqrt(xDelta ** 2 + yDelta ** 2)
		return radius

	def _angle_at(self, pos):
		xDelta = pos.x() - self.rect().center().x()
		yDelta = pos.y() - self.rect().center().y()

		radius = math.sqrt(xDelta ** 2 + yDelta ** 2)
		angle = math.acos(xDelta / radius)
		if 0 <= yDelta:
			angle = 2*math.pi - angle

		return angle

	def _on_key_press(self, keyEvent):
		if keyEvent.key in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Down, QtCore.Qt.Key_Tab]:
			self._select_at(self._selectionIndex + 1)
		elif keyEvent.key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Up, QtCore.Qt.Key_Backtab]:
			self._select_at(self._selectionIndex - 1)
		elif keyEvent.key in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space]:
			self._motion = 0
			self._activate_at(self._selectionIndex)
		elif keyEvent.key in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Backspace]:
			pass

	def _on_mouse_press(self, mouseEvent):
		self._mouseButtonPressed = True


if __name__ == "__main__":
	app = QtGui.QApplication([])

	if False:
		pie = QPieMenu()
		pie.show()

	if False:
		singleAction = QtGui.QAction(None)
		singleAction.setText("Boo")
		singleItem = QActionPieItem(singleAction)
		spie = QPieMenu()
		spie.insertItem(singleItem)
		spie.show()

	if True:
		oneAction = QtGui.QAction(None)
		oneAction.setText("Chew")
		oneItem = QActionPieItem(oneAction)
		twoAction = QtGui.QAction(None)
		twoAction.setText("Foo")
		twoItem = QActionPieItem(twoAction)
		mpie = QPieMenu()
		mpie.insertItem(oneItem)
		mpie.insertItem(twoItem)
		mpie.insertItem(oneItem)
		mpie.insertItem(twoItem)
		mpie.show()

	app.exec_()
