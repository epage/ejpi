#!/usr/bin/env python

import math

from PyQt4 import QtGui
from PyQt4 import QtCore


def _radius_at(center, pos):
	delta = pos - center
	xDelta = delta.x()
	yDelta = delta.y()

	radius = math.sqrt(xDelta ** 2 + yDelta ** 2)
	return radius


def _angle_at(center, pos):
	delta = pos - center
	xDelta = delta.x()
	yDelta = delta.y()

	radius = math.sqrt(xDelta ** 2 + yDelta ** 2)
	angle = math.acos(xDelta / radius)
	if 0 <= yDelta:
		angle = 2*math.pi - angle

	return angle


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


class PieFiling(object):

	INNER_RADIUS_DEFAULT = 32
	OUTER_RADIUS_DEFAULT = 128

	SELECTION_CENTER = -1
	SELECTION_NONE = -2

	NULL_CENTER = QActionPieItem(QtGui.QAction(None))

	def __init__(self):
		self._innerRadius = self.INNER_RADIUS_DEFAULT
		self._outerRadius = self.OUTER_RADIUS_DEFAULT
		self._children = []
		self._center = self.NULL_CENTER

	def insertItem(self, item, index = -1):
		self._children.insert(index, item)

	def removeItemAt(self, index):
		item = self._children.pop(index)

	def set_center(self, item):
		if item is None:
			item = self.NULL_CENTER
		self._center = item

	def center(self):
		return self._center

	def clear(self):
		del self._children[:]

	def itemAt(self, index):
		return self._children[index]

	def indexAt(self, center, point):
		return self._angle_to_index(_angle_at(center, point))

	def innerRadius(self):
		return self._innerRadius

	def setInnerRadius(self, radius):
		self._innerRadius = radius

	def outerRadius(self):
		return self._outerRadius

	def setOuterRadius(self, radius):
		self._outerRadius = radius

	def __iter__(self):
		return iter(self._children)

	def __len__(self):
		return len(self._children)

	def __getitem__(self, index):
		return self._children[index]

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
			return self.SELECTION_CENTER

		totalWeight = sum(child.weight() for child in self._children)
		if totalWeight == 0:
			totalWeight = 1
		baseAngle = (2 * math.pi) / totalWeight

		iterAngle = math.pi / 2 - (self.itemAt(0).weight() * baseAngle) / 2
		while iterAngle < 0:
			iterAngle += 2 * math.pi

		oldIterAngle = iterAngle
		for index, child in enumerate(self._children):
			iterAngle += child.weight() * baseAngle
			if oldIterAngle < angle and angle <= iterAngle:
				return index - 1 if index != 0 else numChildren - 1
			elif oldIterAngle < (angle + 2*math.pi) and (angle + 2*math.pi <= iterAngle):
				return index - 1 if index != 0 else numChildren - 1
			oldIterAngle = iterAngle


class PieArtist(object):

	ICON_SIZE_DEFAULT = 32

	def __init__(self, filing):
		self._filing = filing

		self._cachedOuterRadius = self._filing.outerRadius()
		self._cachedInnerRadius = self._filing.innerRadius()
		canvasSize = self._cachedOuterRadius * 2 + 1
		self._canvas = QtGui.QPixmap(canvasSize, canvasSize)
		self._mask = None
		self.palette = None

	def pieSize(self):
		diameter = self._filing.outerRadius() * 2 + 1
		return QtCore.QSize(diameter, diameter)

	def centerSize(self):
		painter = QtGui.QPainter(self._canvas)
		text = self._filing.center().action().text()
		fontMetrics = painter.fontMetrics()
		if text:
			textBoundingRect = fontMetrics.boundingRect(text)
		else:
			textBoundingRect = QtCore.QRect()
		textWidth = textBoundingRect.width()
		textHeight = textBoundingRect.height()

		return QtCore.QSize(
			textWidth + self.ICON_SIZE_DEFAULT,
			max(textHeight, self.ICON_SIZE_DEFAULT),
		)

	def show(self, palette):
		self.palette = palette

		if (
			self._cachedOuterRadius != self._filing.outerRadius() or
			self._cachedInnerRadius != self._filing.innerRadius()
		):
			self._cachedOuterRadius = self._filing.outerRadius()
			self._cachedInnerRadius = self._filing.innerRadius()
			self._canvas = self._canvas.scaled(self.pieSize())

		if self._mask is None:
			self._mask = QtGui.QBitmap(self._canvas.size())
			self._mask.fill(QtCore.Qt.color0)
			self._generate_mask(self._mask)
			self._canvas.setMask(self._mask)
		return self._mask

	def hide(self):
		self.palette = None

	def paint(self, selectionIndex):
		painter = QtGui.QPainter(self._canvas)
		painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

		adjustmentRect = self._canvas.rect().adjusted(0, 0, -1, -1)

		numChildren = len(self._filing)
		if numChildren == 0:
			if selectionIndex == PieFiling.SELECTION_CENTER and self._filing.center().isEnabled():
				painter.setBrush(self.palette.highlight())
			else:
				painter.setBrush(self.palette.background())

			painter.fillRect(self._canvas.rect(), painter.brush())
			self._paint_center_foreground(painter, selectionIndex)
			return self._canvas
		elif numChildren == 1:
			if selectionIndex == 0 and self._filing[0].isEnabled():
				painter.setBrush(self.palette.highlight())
			else:
				painter.setBrush(self.palette.background())

			painter.fillRect(self._canvas.rect(), painter.brush())
		else:
			for i in xrange(len(self._filing)):
				self._paint_slice_background(painter, adjustmentRect, i, selectionIndex)

		self._paint_center_background(painter, adjustmentRect, selectionIndex)
		self._paint_center_foreground(painter, selectionIndex)

		for i in xrange(len(self._filing)):
			self._paint_slice_foreground(painter, i, selectionIndex)

		return self._canvas

	def _generate_mask(self, mask):
		"""
		Specifies on the mask the shape of the pie menu
		"""
		painter = QtGui.QPainter(mask)
		painter.setPen(QtCore.Qt.color1)
		painter.setBrush(QtCore.Qt.color1)
		painter.drawEllipse(mask.rect().adjusted(0, 0, -1, -1))

	def _paint_slice_background(self, painter, adjustmentRect, i, selectionIndex):
		if i == selectionIndex and self._filing[i].isEnabled():
			painter.setBrush(self.palette.highlight())
		else:
			painter.setBrush(self.palette.background())
		painter.setPen(self.palette.mid().color())

		a = self._filing._index_to_angle(i, True)
		b = self._filing._index_to_angle(i + 1, True)
		if b < a:
			b += 2*math.pi
		size = b - a
		if size < 0:
			size += 2*math.pi

		startAngleInDeg = (a * 360 * 16) / (2*math.pi)
		sizeInDeg = (size * 360 * 16) / (2*math.pi)
		painter.drawPie(adjustmentRect, int(startAngleInDeg), int(sizeInDeg))

	def _paint_slice_foreground(self, painter, i, selectionIndex):
		child = self._filing[i]

		a = self._filing._index_to_angle(i, True)
		b = self._filing._index_to_angle(i + 1, True)
		if b < a:
			b += 2*math.pi
		middleAngle = (a + b) / 2
		averageRadius = (self._cachedInnerRadius + self._cachedOuterRadius) / 2

		sliceX = averageRadius * math.cos(middleAngle)
		sliceY = - averageRadius * math.sin(middleAngle)

		piePos = self._canvas.rect().center()
		pieX = piePos.x()
		pieY = piePos.y()
		self._paint_label(
			painter, child.action(), i == selectionIndex, pieX+sliceX, pieY+sliceY
		)

	def _paint_label(self, painter, action, isSelected, x, y):
		text = action.text()
		fontMetrics = painter.fontMetrics()
		if text:
			textBoundingRect = fontMetrics.boundingRect(text)
		else:
			textBoundingRect = QtCore.QRect()
		textWidth = textBoundingRect.width()
		textHeight = textBoundingRect.height()

		icon = action.icon().pixmap(
			QtCore.QSize(self.ICON_SIZE_DEFAULT, self.ICON_SIZE_DEFAULT),
			QtGui.QIcon.Normal,
			QtGui.QIcon.On,
		)
		iconWidth = icon.width()
		iconHeight = icon.width()
		averageWidth = (iconWidth + textWidth)/2
		if not icon.isNull():
			iconRect = QtCore.QRect(
				x - averageWidth,
				y - iconHeight/2,
				iconWidth,
				iconHeight,
			)

			painter.drawPixmap(iconRect, icon)

		if text:
			if isSelected:
				if action.isEnabled():
					pen = self.palette.highlightedText()
					brush = self.palette.highlight()
				else:
					pen = self.palette.mid()
					brush = self.palette.background()
			else:
				if action.isEnabled():
					pen = self.palette.text()
				else:
					pen = self.palette.mid()
				brush = self.palette.background()

			leftX = x - averageWidth + iconWidth
			topY = y + textHeight/2
			painter.setPen(pen.color())
			painter.setBrush(brush)
			painter.drawText(leftX, topY, text)

	def _paint_center_background(self, painter, adjustmentRect, selectionIndex):
		dark = self.palette.dark().color()
		light = self.palette.light().color()
		if selectionIndex == PieFiling.SELECTION_CENTER and self._filing.center().isEnabled():
			background = self.palette.highlight().color()
		else:
			background = self.palette.background().color()

		innerRadius = self._cachedInnerRadius
		adjustmentCenterPos = adjustmentRect.center()
		innerRect = QtCore.QRect(
			adjustmentCenterPos.x() - innerRadius,
			adjustmentCenterPos.y() - innerRadius,
			innerRadius * 2 + 1,
			innerRadius * 2 + 1,
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
		innerCenter = r.center()
		innerRect.setLeft(innerCenter.x() + ((r.left() - innerCenter.x()) / 3) * 1)
		innerRect.setRight(innerCenter.x() + ((r.right() - innerCenter.x()) / 3) * 1)
		innerRect.setTop(innerCenter.y() + ((r.top() - innerCenter.y()) / 3) * 1)
		innerRect.setBottom(innerCenter.y() + ((r.bottom() - innerCenter.y()) / 3) * 1)

	def _paint_center_foreground(self, painter, selectionIndex):
		centerPos = self._canvas.rect().center()
		pieX = centerPos.x()
		pieY = centerPos.y()

		x = pieX
		y = pieY

		self._paint_label(
			painter,
			self._filing.center().action(),
			selectionIndex == PieFiling.SELECTION_CENTER,
			x, y
		)


class QPieDisplay(QtGui.QWidget):

	def __init__(self, filing, parent = None, flags = QtCore.Qt.Window):
		QtGui.QWidget.__init__(self, parent, flags)
		self._filing = filing
		self._artist = PieArtist(self._filing)
		self._selectionIndex = PieFiling.SELECTION_NONE

	def popup(self, pos):
		self._update_selection(pos)
		self.show()

	def sizeHint(self):
		return self._artist.pieSize()

	def showEvent(self, showEvent):
		mask = self._artist.show(self.palette())
		self.setMask(mask)

		QtGui.QWidget.showEvent(self, showEvent)

	def hideEvent(self, hideEvent):
		self._artist.hide()
		self._selectionIndex = PieFiling.SELECTION_NONE
		QtGui.QWidget.hideEvent(self, hideEvent)

	def paintEvent(self, paintEvent):
		canvas = self._artist.paint(self._selectionIndex)

		screen = QtGui.QPainter(self)
		screen.drawPixmap(QtCore.QPoint(0, 0), canvas)

		QtGui.QWidget.paintEvent(self, paintEvent)

	def selectAt(self, index):
		self._selectionIndex = index
		self.update()


class QPieButton(QtGui.QWidget):

	activated = QtCore.pyqtSignal(int)
	highlighted = QtCore.pyqtSignal(int)
	canceled = QtCore.pyqtSignal()
	aboutToShow = QtCore.pyqtSignal()
	aboutToHide = QtCore.pyqtSignal()

	def __init__(self, buttonSlice, parent = None):
		QtGui.QWidget.__init__(self, parent)
		self._filing = PieFiling()
		self._display = QPieDisplay(self._filing, None, QtCore.Qt.SplashScreen)
		self._selectionIndex = PieFiling.SELECTION_NONE

		self._buttonFiling = PieFiling()
		self._buttonFiling.set_center(buttonSlice)
		self._buttonArtist = PieArtist(self._buttonFiling)
		centerSize = self._buttonArtist.centerSize()
		self._buttonFiling.setOuterRadius(max(centerSize.width(), centerSize.height()))
		self._poppedUp = False

		self._mousePosition = None
		self.setFocusPolicy(QtCore.Qt.StrongFocus)

	def insertItem(self, item, index = -1):
		self._filing.insertItem(item, index)

	def removeItemAt(self, index):
		self._filing.removeItemAt(index)

	def set_center(self, item):
		self._filing.set_center(item)

	def set_button(self, item):
		self.update()

	def clear(self):
		self._filing.clear()

	def itemAt(self, index):
		return self._filing.itemAt(index)

	def indexAt(self, point):
		return self._filing.indexAt(self.rect().center(), point)

	def innerRadius(self):
		return self._filing.innerRadius()

	def setInnerRadius(self, radius):
		self._filing.setInnerRadius(radius)

	def outerRadius(self):
		return self._filing.outerRadius()

	def setOuterRadius(self, radius):
		self._filing.setOuterRadius(radius)

	def sizeHint(self):
		return self._buttonArtist.pieSize()

	def mousePressEvent(self, mouseEvent):
		self._popup_child(mouseEvent.globalPos())
		lastSelection = self._selectionIndex

		lastMousePos = mouseEvent.pos()
		self._mousePosition = lastMousePos
		self._update_selection(self.rect().center())

		if lastSelection != self._selectionIndex:
			self.highlighted.emit(self._selectionIndex)
			self._display.selectAt(self._selectionIndex)

	def mouseMoveEvent(self, mouseEvent):
		lastSelection = self._selectionIndex

		lastMousePos = mouseEvent.pos()
		if self._mousePosition is None:
			# Absolute
			self._update_selection(lastMousePos)
		else:
			# Relative
			self._update_selection(self.rect().center() + (lastMousePos - self._mousePosition))

		if lastSelection != self._selectionIndex:
			self.highlighted.emit(self._selectionIndex)
			self._display.selectAt(self._selectionIndex)

	def mouseReleaseEvent(self, mouseEvent):
		lastSelection = self._selectionIndex

		lastMousePos = mouseEvent.pos()
		if self._mousePosition is None:
			# Absolute
			self._update_selection(lastMousePos)
		else:
			# Relative
			self._update_selection(self.rect().center() + (lastMousePos - self._mousePosition))
		self._mousePosition = None

		self._activate_at(self._selectionIndex)
		self._hide_child()

	def keyPressEvent(self, keyEvent):
		if keyEvent.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Down, QtCore.Qt.Key_Tab]:
			self._popup_child(QtGui.QCursor.pos())
			if self._selectionIndex != len(self._filing) - 1:
				nextSelection = self._selectionIndex + 1
			else:
				nextSelection = 0
			self._select_at(nextSelection)
			self._display.selectAt(self._selectionIndex)
		elif keyEvent.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Up, QtCore.Qt.Key_Backtab]:
			self._popup_child(QtGui.QCursor.pos())
			if 0 < self._selectionIndex:
				nextSelection = self._selectionIndex - 1
			else:
				nextSelection = len(self._filing) - 1
			self._select_at(nextSelection)
			self._display.selectAt(self._selectionIndex)
		elif keyEvent.key() in [QtCore.Qt.Key_Space]:
			self._popup_child(QtGui.QCursor.pos())
			self._select_at(PieFiling.SELECTION_CENTER)
			self._display.selectAt(self._selectionIndex)
		elif keyEvent.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space]:
			self._activate_at(self._selectionIndex)
			self._hide_child()
		elif keyEvent.key() in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Backspace]:
			self._activate_at(PieFiling.SELECTION_NONE)
			self._hide_child()
		else:
			QtGui.QWidget.keyPressEvent(self, keyEvent)

	def showEvent(self, showEvent):
		self._buttonArtist.show(self.palette())

		QtGui.QWidget.showEvent(self, showEvent)

	def hideEvent(self, hideEvent):
		self._display.hide()
		self._select_at(PieFiling.SELECTION_NONE)
		QtGui.QWidget.hideEvent(self, hideEvent)

	def paintEvent(self, paintEvent):
		if self._poppedUp:
			canvas = self._buttonArtist.paint(PieFiling.SELECTION_CENTER)
		else:
			canvas = self._buttonArtist.paint(PieFiling.SELECTION_NONE)

		screen = QtGui.QPainter(self)
		screen.drawPixmap(QtCore.QPoint(0, 0), canvas)

		QtGui.QWidget.paintEvent(self, paintEvent)

	def _popup_child(self, position):
		self._poppedUp = True
		self.aboutToShow.emit()

		position = position - QtCore.QPoint(self._filing.outerRadius(), self._filing.outerRadius())
		self._display.move(position)
		self._display.show()

		self.update()

	def _hide_child(self):
		self._poppedUp = False
		self.aboutToHide.emit()
		self._display.hide()
		self.update()

	def _select_at(self, index):
		self._selectionIndex = index

	def _update_selection(self, lastMousePos):
		radius = _radius_at(self.rect().center(), lastMousePos)
		if radius < self._filing.innerRadius():
			self._select_at(PieFiling.SELECTION_CENTER)
		elif radius <= self._filing.outerRadius():
			self._select_at(self.indexAt(lastMousePos))
		else:
			self._select_at(PieFiling.SELECTION_NONE)

	def _activate_at(self, index):
		if index == PieFiling.SELECTION_NONE:
			self.canceled.emit()
			return
		elif index == PieFiling.SELECTION_CENTER:
			child = self._filing.center()
		else:
			child = self.itemAt(index)

		if child.action().isEnabled():
			child.action().trigger()
			self.activated.emit(index)
		else:
			self.canceled.emit()


class QPieMenu(QtGui.QWidget):

	activated = QtCore.pyqtSignal(int)
	highlighted = QtCore.pyqtSignal(int)
	canceled = QtCore.pyqtSignal()
	aboutToShow = QtCore.pyqtSignal()
	aboutToHide = QtCore.pyqtSignal()

	def __init__(self, parent = None):
		QtGui.QWidget.__init__(self, parent)
		self._filing = PieFiling()
		self._artist = PieArtist(self._filing)
		self._selectionIndex = PieFiling.SELECTION_NONE

		self._mousePosition = ()
		self.setFocusPolicy(QtCore.Qt.StrongFocus)

	def popup(self, pos):
		self._update_selection(pos)
		self.show()

	def insertItem(self, item, index = -1):
		self._filing.insertItem(item, index)
		self.update()

	def removeItemAt(self, index):
		self._filing.removeItemAt(index)
		self.update()

	def set_center(self, item):
		self._filing.set_center(item)
		self.update()

	def clear(self):
		self._filing.clear()
		self.update()

	def itemAt(self, index):
		return self._filing.itemAt(index)

	def indexAt(self, point):
		return self._filing.indexAt(self.rect().center(), point)

	def innerRadius(self):
		return self._filing.innerRadius()

	def setInnerRadius(self, radius):
		self._filing.setInnerRadius(radius)
		self.update()

	def outerRadius(self):
		return self._filing.outerRadius()

	def setOuterRadius(self, radius):
		self._filing.setOuterRadius(radius)
		self.update()

	def sizeHint(self):
		return self._artist.pieSize()

	def mousePressEvent(self, mouseEvent):
		lastSelection = self._selectionIndex

		lastMousePos = mouseEvent.pos()
		self._update_selection(lastMousePos)
		self._mousePosition = lastMousePos

		if lastSelection != self._selectionIndex:
			self.highlighted.emit(self._selectionIndex)
			self.update()

	def mouseMoveEvent(self, mouseEvent):
		lastSelection = self._selectionIndex

		lastMousePos = mouseEvent.pos()
		self._update_selection(lastMousePos)

		if lastSelection != self._selectionIndex:
			self.highlighted.emit(self._selectionIndex)
			self.update()

	def mouseReleaseEvent(self, mouseEvent):
		lastSelection = self._selectionIndex

		lastMousePos = mouseEvent.pos()
		self._update_selection(lastMousePos)
		self._mousePosition = ()

		self._activate_at(self._selectionIndex)
		self.update()

	def keyPressEvent(self, keyEvent):
		if keyEvent.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Down, QtCore.Qt.Key_Tab]:
			self._select_at(self._selectionIndex + 1)
			self.update()
		elif keyEvent.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Up, QtCore.Qt.Key_Backtab]:
			self._select_at(self._selectionIndex - 1)
			self.update()
		elif keyEvent.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space]:
			self._activate_at(self._selectionIndex)
		elif keyEvent.key() in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Backspace]:
			self._activate_at(PieFiling.SELECTION_NONE)
		else:
			QtGui.QWidget.keyPressEvent(self, keyEvent)

	def showEvent(self, showEvent):
		self.aboutToShow.emit()

		mask = self._artist.show(self.palette())
		self.setMask(mask)

		lastMousePos = self.mapFromGlobal(QtGui.QCursor.pos())
		self._update_selection(lastMousePos)

		QtGui.QWidget.showEvent(self, showEvent)

	def hideEvent(self, hideEvent):
		self._artist.hide()
		self._selectionIndex = PieFiling.SELECTION_NONE
		QtGui.QWidget.hideEvent(self, hideEvent)

	def paintEvent(self, paintEvent):
		canvas = self._artist.paint(self._selectionIndex)

		screen = QtGui.QPainter(self)
		screen.drawPixmap(QtCore.QPoint(0, 0), canvas)

		QtGui.QWidget.paintEvent(self, paintEvent)

	def _select_at(self, index):
		self._selectionIndex = index

		numChildren = len(self._filing)
		loopDelta = max(numChildren, 1)
		while self._selectionIndex < 0:
			self._selectionIndex += loopDelta
		while numChildren <= self._selectionIndex:
			self._selectionIndex -= loopDelta

	def _update_selection(self, lastMousePos):
		radius = _radius_at(self.rect().center(), lastMousePos)
		if radius < self._filing.innerRadius():
			self._selectionIndex = PieFiling.SELECTION_CENTER
		elif radius <= self._filing.outerRadius():
			self._select_at(self.indexAt(lastMousePos))
		else:
			self._selectionIndex = PieFiling.SELECTION_NONE

	def _activate_at(self, index):
		if index == PieFiling.SELECTION_NONE:
			self.canceled.emit()
			self.aboutToHide.emit()
			self.hide()
			return
		elif index == PieFiling.SELECTION_CENTER:
			child = self._filing.center()
		else:
			child = self.itemAt(index)

		if child.isEnabled():
			child.action().trigger()
			self.activated.emit(index)
		else:
			self.canceled.emit()
		self.aboutToHide.emit()
		self.hide()


def _print(msg):
	print msg


def _on_about_to_hide(app):
	app.exit()


if __name__ == "__main__":
	app = QtGui.QApplication([])
	PieFiling.NULL_CENTER.setEnabled(False)

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

	if False:
		oneAction = QtGui.QAction(None)
		oneAction.setText("Chew")
		oneItem = QActionPieItem(oneAction)
		twoAction = QtGui.QAction(None)
		twoAction.setText("Foo")
		twoItem = QActionPieItem(twoAction)
		iconTextAction = QtGui.QAction(None)
		iconTextAction.setText("Icon")
		iconTextAction.setIcon(QtGui.QIcon.fromTheme("gtk-close"))
		iconTextItem = QActionPieItem(iconTextAction)
		mpie = QPieMenu()
		mpie.insertItem(oneItem)
		mpie.insertItem(twoItem)
		mpie.insertItem(oneItem)
		mpie.insertItem(iconTextItem)
		mpie.show()

	if False:
		oneAction = QtGui.QAction(None)
		oneAction.setText("Chew")
		oneAction.triggered.connect(lambda: _print("Chew"))
		oneItem = QActionPieItem(oneAction)
		twoAction = QtGui.QAction(None)
		twoAction.setText("Foo")
		twoAction.triggered.connect(lambda: _print("Foo"))
		twoItem = QActionPieItem(twoAction)
		iconAction = QtGui.QAction(None)
		iconAction.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
		iconAction.triggered.connect(lambda: _print("Icon"))
		iconItem = QActionPieItem(iconAction)
		iconTextAction = QtGui.QAction(None)
		iconTextAction.setText("Icon")
		iconTextAction.setIcon(QtGui.QIcon.fromTheme("gtk-close"))
		iconTextAction.triggered.connect(lambda: _print("Icon and text"))
		iconTextItem = QActionPieItem(iconTextAction)
		mpie = QPieMenu()
		mpie.set_center(iconItem)
		mpie.insertItem(oneItem)
		mpie.insertItem(twoItem)
		mpie.insertItem(oneItem)
		mpie.insertItem(iconTextItem)
		mpie.show()
		mpie.aboutToHide.connect(lambda: _on_about_to_hide(app))
		mpie.canceled.connect(lambda: _print("Canceled"))

	if True:
		oneAction = QtGui.QAction(None)
		oneAction.setText("Chew")
		oneAction.triggered.connect(lambda: _print("Chew"))
		oneItem = QActionPieItem(oneAction)
		twoAction = QtGui.QAction(None)
		twoAction.setText("Foo")
		twoAction.triggered.connect(lambda: _print("Foo"))
		twoItem = QActionPieItem(twoAction)
		iconAction = QtGui.QAction(None)
		iconAction.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
		iconAction.triggered.connect(lambda: _print("Icon"))
		iconItem = QActionPieItem(iconAction)
		iconTextAction = QtGui.QAction(None)
		iconTextAction.setText("Icon")
		iconTextAction.setIcon(QtGui.QIcon.fromTheme("gtk-close"))
		iconTextAction.triggered.connect(lambda: _print("Icon and text"))
		iconTextItem = QActionPieItem(iconTextAction)
		pieFiling = PieFiling()
		pieFiling.set_center(iconItem)
		pieFiling.insertItem(oneItem)
		pieFiling.insertItem(twoItem)
		pieFiling.insertItem(oneItem)
		pieFiling.insertItem(iconTextItem)
		mpie = QPieDisplay(pieFiling)
		mpie.show()

	if False:
		oneAction = QtGui.QAction(None)
		oneAction.setText("Chew")
		oneAction.triggered.connect(lambda: _print("Chew"))
		oneItem = QActionPieItem(oneAction)
		twoAction = QtGui.QAction(None)
		twoAction.setText("Foo")
		twoAction.triggered.connect(lambda: _print("Foo"))
		twoItem = QActionPieItem(twoAction)
		iconAction = QtGui.QAction(None)
		iconAction.setIcon(QtGui.QIcon.fromTheme("gtk-open"))
		iconAction.triggered.connect(lambda: _print("Icon"))
		iconItem = QActionPieItem(iconAction)
		iconTextAction = QtGui.QAction(None)
		iconTextAction.setText("Icon")
		iconTextAction.setIcon(QtGui.QIcon.fromTheme("gtk-close"))
		iconTextAction.triggered.connect(lambda: _print("Icon and text"))
		iconTextItem = QActionPieItem(iconTextAction)
		mpie = QPieButton(iconItem)
		mpie.set_center(iconItem)
		mpie.insertItem(oneItem)
		mpie.insertItem(twoItem)
		mpie.insertItem(oneItem)
		mpie.insertItem(iconTextItem)
		mpie.show()
		mpie.aboutToHide.connect(lambda: _on_about_to_hide(app))
		mpie.canceled.connect(lambda: _print("Canceled"))

	app.exec_()
