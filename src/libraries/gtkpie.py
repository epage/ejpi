#!/usr/bin/env python

"""
@todo Handle sizing in a better manner http://www.gtkmm.org/docs/gtkmm-2.4/docs/tutorial/html/sec-custom-widgets.html
"""


from __future__ import division

import os
import weakref
import math
import copy
import warnings

import gobject
import gtk
import cairo
import pango

try:
	import rsvg
except ImportError:
	rsvg = None


def deg_to_rad(deg):
	return (2 * math.pi * deg) / 360.0


def rad_to_deg(rad):
	return (360.0 * rad) / (2 * math.pi)


def normalize_radian_angle(radAng):
	"""
	Restricts @param radAng to the range [0..2pi)
	"""
	twoPi = 2 * math.pi

	while radAng < 0:
		radAng += twoPi
	while twoPi <= radAng:
		radAng -= twoPi

	return radAng


def delta_to_rtheta(dx, dy):
	distance = math.sqrt(dx**2 + dy**2)

	angleInRads = math.atan2(-dy, dx)
	if angleInRads < 0:
		angleInRads = 2*math.pi + angleInRads
	return distance, angleInRads


class FontCache(object):

	def __init__(self):
		self.__fontCache = {}

	def get_font(self, s):
		if s in self.__fontCache:
			return self.__fontCache[s]

		descr = pango.FontDescription(s)
		self.__fontCache[s] = descr

		return descr


FONTS = FontCache()


class ImageCache(object):

	def __init__(self):
		self.__imageCache = {}
		self.__imagePaths = [
			os.path.join(os.path.dirname(__file__), "images"),
		]

	def add_path(self, path):
		self.__imagePaths.append(path)

	def get_image(self, s):
		if s in self.__imageCache:
			return self.__imageCache[s]

		image = None

		if s.lower().endswith(".png"):
			for path in self.__imagePaths:
				imagePath = os.path.join(path, s)
				try:
					image = cairo.ImageSurface.create_from_png(imagePath)
					break
				except:
					warnings.warn("Unable to load image %s" % imagePath)
		elif s.lower().endswith(".svg") and rsvg is not None:
			for path in self.__imagePaths:
				imagePath = os.path.join(path, s)
				try:
					image = rsvg.Handle(file=imagePath)
				except:
					warnings.warn("Unable to load image %s" % imagePath)
		else:
			print "Don't know how to load image file type:", s

		if image is not None:
			self.__imageCache[s] = image

		return image


IMAGES = ImageCache()


def convert_color(gtkColor):
	r = gtkColor.red / 65535
	g = gtkColor.green / 65535
	b = gtkColor.blue / 65535
	return r, g, b


def generate_pie_style(widget):
	"""
	@bug This seems to always pick the same colors irregardless of the theme
	"""
	# GTK states:
	# * gtk.STATE_NORMAL - The state of a sensitive widget that is not active and does not have the focus
	# * gtk.STATE_ACTIVE - The state of a sensitive widget when it is active e.g. a button that is pressed but not yet released
	# * gtk.STATE_PRELIGHT - The state of a sensitive widget that has the focus e.g. a button that has the mouse pointer over it.
	# * gtk.STATE_SELECTED - The state of a widget that is selected e.g. selected text in a gtk.Entry widget
	# * gtk.STATE_INSENSITIVE - The state of a widget that is insensitive and will not respond to any events e.g. cannot be activated, selected or prelit.

	widget.ensure_style()
	gtkStyle = widget.get_style()
	sliceStyle = dict(
		(gtkStyleState, {
			"text": convert_color(gtkStyle.text[gtkStyleState]),
			"fill": convert_color(gtkStyle.bg[gtkStyleState]),
			"stroke": None,
		})
		for gtkStyleState in (
			gtk.STATE_NORMAL, gtk.STATE_ACTIVE, gtk.STATE_PRELIGHT, gtk.STATE_SELECTED, gtk.STATE_INSENSITIVE
		)
	)

	return sliceStyle


class PieSlice(object):

	SLICE_CENTER = 0
	SLICE_EAST = 1
	SLICE_SOUTH_EAST = 2
	SLICE_SOUTH = 3
	SLICE_SOUTH_WEST = 4
	SLICE_WEST = 5
	SLICE_NORTH_WEST = 6
	SLICE_NORTH = 7
	SLICE_NORTH_EAST = 8

	MAX_ANGULAR_SLICES = 8

	SLICE_DIRECTIONS = [
		SLICE_CENTER,
		SLICE_EAST,
		SLICE_SOUTH_EAST,
		SLICE_SOUTH,
		SLICE_SOUTH_WEST,
		SLICE_WEST,
		SLICE_NORTH_WEST,
		SLICE_NORTH,
		SLICE_NORTH_EAST,
	]

	SLICE_DIRECTION_NAMES = [
		"CENTER",
		"EAST",
		"SOUTH_EAST",
		"SOUTH",
		"SOUTH_WEST",
		"WEST",
		"NORTH_WEST",
		"NORTH",
		"NORTH_EAST",
	]

	def __init__(self, handler = (lambda p, s, d: None)):
		self._direction = self.SLICE_CENTER
		self._pie = None
		self._style = None
		self._handler = handler

	def menu_init(self, pie, direction):
		self._direction = direction
		self._pie = weakref.ref(pie)
		self._style = pie.sliceStyle

	def calculate_minimum_radius(self, context, textLayout):
		return 0

	def draw_fg(self, styleState, isSelected, context, textLayout):
		if isSelected:
			styleState = gtk.STATE_ACTIVE
		self._draw_fg(styleState, context, textLayout)

	def draw_bg(self, styleState, isSelected, context, textLayout):
		if isSelected:
			styleState = gtk.STATE_ACTIVE
		self._draw_bg(styleState, context, textLayout)

	def _draw_fg(self, styleState, context, textLayout):
		pass

	def _draw_bg(self, styleState, context, textLayout):
		centerPosition = self._pie().centerPosition
		radius = max(self._pie().radius, self.calculate_minimum_radius(context, textLayout))
		outerRadius = self._pie().outerRadius

		fillColor = self._style[styleState]["fill"]
		if not fillColor:
			return

		if self._direction == self.SLICE_CENTER:
			context.arc(
				centerPosition[0],
				centerPosition[1],
				radius,
				0,
				2 * math.pi
			)

			context.set_source_rgb(*fillColor)
			context.fill()
		else:
			sliceCenterAngle = self.quadrant_to_theta(self._direction)
			sliceArcWidth = 2*math.pi / self.MAX_ANGULAR_SLICES
			sliceStartAngle = sliceCenterAngle - sliceArcWidth/2
			sliceEndAngle = sliceCenterAngle + sliceArcWidth/2

			context.arc(
				centerPosition[0],
				centerPosition[1],
				radius,
				sliceStartAngle,
				sliceEndAngle,
			)
			context.arc_negative(
				centerPosition[0],
				centerPosition[1],
				outerRadius,
				sliceEndAngle,
				sliceStartAngle,
			)
			context.close_path()

			context.set_source_rgb(*fillColor)
			context.fill()

	def activate(self):
		self._handler(self._pie(), self, self._direction)

	@classmethod
	def rtheta_to_quadrant(cls, distance, angleInRads, innerRadius):
		if distance < innerRadius:
			quadrant = 0
		else:
			gradians = angleInRads / (2*math.pi)
			preciseQuadrant = gradians * cls.MAX_ANGULAR_SLICES + cls.MAX_ANGULAR_SLICES / (2 * 2*math.pi)
			quadrantWithWrap = int(preciseQuadrant)
			quadrant = quadrantWithWrap % cls.MAX_ANGULAR_SLICES
			quadrant += 1

		return quadrant

	@classmethod
	def quadrant_to_theta(cls, quadrant):
		assert quadrant != 0
		quadrant -= 1

		gradians = quadrant / cls.MAX_ANGULAR_SLICES
		radians = gradians * 2*math.pi

		return radians


class NullPieSlice(PieSlice):

	def draw_bg(self, styleState, isSelected, context, textLayout):
		super(NullPieSlice, self).draw_bg(styleState, False, context, textLayout)


class LabelPieSlice(PieSlice):

	def _align_label(self, labelWidth, labelHeight):
		centerPosition = self._pie().centerPosition
		if self._direction == PieSlice.SLICE_CENTER:
			labelX = centerPosition[0] - labelWidth/2
			labelY = centerPosition[1] - labelHeight/2
		else:
			if self._direction in (PieSlice.SLICE_NORTH_WEST, PieSlice.SLICE_WEST, PieSlice.SLICE_SOUTH_WEST):
				outerX = 0
				labelX = outerX
			elif self._direction in (PieSlice.SLICE_SOUTH, PieSlice.SLICE_NORTH):
				outerX = centerPosition[0]
				labelX = outerX - labelWidth/2
			elif self._direction in (PieSlice.SLICE_NORTH_EAST, PieSlice.SLICE_EAST, PieSlice.SLICE_SOUTH_EAST):
				outerX = centerPosition[0] * 2
				labelX = outerX - labelWidth
			else:
				assert False, "Direction %d is incorrect" % self._direction

			if self._direction in (PieSlice.SLICE_NORTH_EAST, PieSlice.SLICE_NORTH, PieSlice.SLICE_NORTH_WEST):
				outerY = 0
				labelY = outerY
			elif self._direction in (PieSlice.SLICE_EAST, PieSlice.SLICE_WEST):
				outerY = centerPosition[1]
				labelY = outerY - labelHeight/2
			elif self._direction in (PieSlice.SLICE_SOUTH_EAST, PieSlice.SLICE_SOUTH, PieSlice.SLICE_SOUTH_WEST):
				outerY = centerPosition[1] * 2
				labelY = outerY - labelHeight
			else:
				assert False, "Direction %d is incorrect" % self._direction

		return int(labelX), int(labelY)


class TextLabelPieSlice(LabelPieSlice):

	def __init__(self, text, fontName = 'Helvetica 12', handler = (lambda p, s, d: None)):
		super(TextLabelPieSlice, self).__init__(handler = handler)
		self.__text = text
		self.__fontName = fontName

	def calculate_minimum_radius(self, context, textLayout):
		font = FONTS.get_font(self.__fontName)
		textLayout.set_font_description(font)
		textLayout.set_markup(self.__text)

		labelWidth, labelHeight = textLayout.get_pixel_size()
		return min(labelWidth, labelHeight) / 2

	def _draw_fg(self, styleState, context, textLayout):
		super(TextLabelPieSlice, self)._draw_fg(styleState, context, textLayout)

		textColor = self._style[styleState]["text"]
		font = FONTS.get_font(self.__fontName)

		context.set_source_rgb(*textColor)
		textLayout.set_font_description(font)
		textLayout.set_markup(self.__text)
		labelWidth, labelHeight = textLayout.get_pixel_size()
		labelX, labelY = self._align_label(labelWidth, labelHeight)

		context.move_to(
			labelX,
			labelY,
		)

		context.show_layout(textLayout)


class ImageLabelPieSlice(LabelPieSlice):

	def __init__(self, imagePath, handler = (lambda p, s, d: None)):
		super(ImageLabelPieSlice, self).__init__(handler = handler)
		self.__imagePath = imagePath

	def calculate_minimum_radius(self, context, textLayout):
		image = IMAGES.get_image(self.__imagePath)
		if image is None:
			return
		labelWidth, labelHeight = image.get_width(), image.get_height()
		return min(labelWidth, labelHeight) / 2

	def _draw_fg(self, styleState, context, textLayout):
		super(ImageLabelPieSlice, self)._draw_fg(styleState, context, textLayout)

		image = IMAGES.get_image(self.__imagePath)
		if image is None:
			return

		labelWidth, labelHeight = image.get_width(), image.get_height()
		labelX, labelY = self._align_label(labelWidth, labelHeight)

		context.set_source_surface(
			image,
			labelX,
			labelY,
		)

		context.paint()


class PieMenu(gtk.DrawingArea):

	def __init__(self, style = None, **kwds):
		super(PieMenu, self).__init__()

		self.sliceStyle = style
		self.centerPosition = 0, 0
		self.radius = 20
		self.outerRadius = self.radius * 2

		self.connect("expose_event", self._on_expose)
		self.connect("motion_notify_event", self._on_motion_notify)
		self.connect("leave_notify_event", self._on_leave_notify)
		self.connect("proximity_in_event", self._on_motion_notify)
		self.connect("proximity_out_event", self._on_leave_notify)
		self.connect("button_press_event", self._on_button_press)
		self.connect("button_release_event", self._on_button_release)

		self.set_events(
			gtk.gdk.EXPOSURE_MASK |
			gtk.gdk.POINTER_MOTION_MASK |
			gtk.gdk.POINTER_MOTION_HINT_MASK |
			gtk.gdk.BUTTON_MOTION_MASK |
			gtk.gdk.BUTTON_PRESS_MASK |
			gtk.gdk.BUTTON_RELEASE_MASK |
			gtk.gdk.PROXIMITY_IN_MASK |
			gtk.gdk.PROXIMITY_OUT_MASK |
			gtk.gdk.LEAVE_NOTIFY_MASK
		)

		self.__activeSlice = None
		self.__slices = {}
		for direction in PieSlice.SLICE_DIRECTIONS:
			self.add_slice(NullPieSlice(), direction)

		self.__clickPosition = 0, 0
		self.__styleState = gtk.STATE_NORMAL

	def add_slice(self, slice, direction):
		assert direction in PieSlice.SLICE_DIRECTIONS

		slice.menu_init(self, direction)
		self.__slices[direction] = slice

		if direction == PieSlice.SLICE_CENTER:
			self.__activeSlice = self.__slices[PieSlice.SLICE_CENTER]

	def __update_state(self, mousePosition):
		rect = self.get_allocation()
		newStyleState = self.__styleState

		if (
			0 <= mousePosition[0] and mousePosition[1] < rect.width and
			0 <= mousePosition[1] and mousePosition[1] < rect.height
		):
			if self.__clickPosition == (0, 0):
				newStyleState = gtk.STATE_PRELIGHT
		else:
			if self.__clickPosition != (0, 0):
				newStyleState = gtk.STATE_PRELIGHT

		if newStyleState != self.__styleState:
			self.__generate_draw_event()
			self.__styleState = newStyleState

	def __process_mouse_position(self, mousePosition):
		self.__update_state(mousePosition)
		if self.__clickPosition == (0, 0):
			return

		delta = (
			mousePosition[0] - self.centerPosition[0],
			- (mousePosition[1] - self.centerPosition[1])
		)
		distance, angleInRads = delta_to_rtheta(delta[0], delta[1])
		quadrant = PieSlice.rtheta_to_quadrant(distance, angleInRads, self.radius)
		self.__select_slice(self.__slices[quadrant])

	def __select_slice(self, newSlice):
		if newSlice is self.__activeSlice:
			return

		oldSlice = self.__activeSlice
		self.__activeSlice = newSlice
		self.__generate_draw_event()

	def __generate_draw_event(self):
		if self.window is None:
			return
		self.queue_draw()

	def _on_expose(self, widget, event):
		cairoContext = self.window.cairo_create()
		pangoContext = self.create_pango_context()
		textLayout = pango.Layout(pangoContext)

		rect = self.get_allocation()
		position = 0, 0
		dimensions = rect.width, rect.height

		self.centerPosition = position[0] + dimensions[0] / 2, position[1] + dimensions[1] / 2
		self.outerRadius = max(*dimensions) # be larger than the view
		self.radius = self.outerRadius / (3*2) # fit inside the middle cell

		# Draw Background
		cairoContext.rectangle(
			position[0],
			position[1],
			dimensions[0],
			dimensions[1],
		)
		cairoContext.set_source_rgb(*self.sliceStyle[self.__styleState]["fill"])
		cairoContext.fill()

		isSelected = self.__clickPosition != (0, 0)
		self.__activeSlice.draw_bg(self.__styleState, isSelected, cairoContext, textLayout)

		# Draw Foreground
		for slice in self.__slices.itervalues():
			isSelected = (slice is self.__activeSlice)
			if not isSelected:
				slice.draw_fg(self.__styleState, isSelected, cairoContext, textLayout)

		isSelected = self.__clickPosition != (0, 0)
		self.__activeSlice.draw_fg(self.__styleState, isSelected, cairoContext, textLayout)

	def _on_leave_notify(self, widget, event):
		newStyleState = gtk.STATE_NORMAL
		if newStyleState != self.__styleState:
			self.__generate_draw_event()
			self.__styleState = newStyleState

		mousePosition = event.get_coords()
		self.__process_mouse_position(mousePosition)

	def _on_motion_notify(self, widget, event):
		mousePosition = event.get_coords()
		self.__process_mouse_position(mousePosition)

	def _on_button_press(self, widget, event):
		self.__clickPosition = event.get_coords()

		self._on_motion_notify(widget, event)
		self.__generate_draw_event()

	def _on_button_release(self, widget, event):
		self._on_motion_notify(widget, event)

		self.__activeSlice.activate()
		self.__activeSlice = self.__slices[PieSlice.SLICE_CENTER]
		self.__clickPosition = 0, 0

		self.__generate_draw_event()


gobject.type_register(PieMenu)


class FakeEvent(object):

	def __init__(self, x, y, isHint):
		self.x = x
		self.y = y
		self.is_hint = isHint

	def get_coords(self):
		return self.x, self.y


class PiePopup(gtk.DrawingArea):

	def __init__(self, style = None, **kwds):
		super(PiePopup, self).__init__()

		self.showAllSlices = True
		self.sliceStyle = style
		self.centerPosition = 0, 0
		self.radius = 20
		self.outerRadius = self.radius * 2

		self.connect("expose_event", self._on_expose)
		self.connect("motion_notify_event", self._on_motion_notify)
		self.connect("proximity_in_event", self._on_motion_notify)
		self.connect("proximity_out_event", self._on_leave_notify)
		self.connect("leave_notify_event", self._on_leave_notify)
		self.connect("button_press_event", self._on_button_press)
		self.connect("button_release_event", self._on_button_release)

		self.set_events(
			gtk.gdk.EXPOSURE_MASK |
			gtk.gdk.POINTER_MOTION_MASK |
			gtk.gdk.POINTER_MOTION_HINT_MASK |
			gtk.gdk.BUTTON_MOTION_MASK |
			gtk.gdk.BUTTON_PRESS_MASK |
			gtk.gdk.BUTTON_RELEASE_MASK |
			gtk.gdk.PROXIMITY_IN_MASK |
			gtk.gdk.PROXIMITY_OUT_MASK |
			gtk.gdk.LEAVE_NOTIFY_MASK
		)

		self.__popped = False
		self.__styleState = gtk.STATE_NORMAL
		self.__activeSlice = None
		self.__slices = {}
		self.__localSlices = {}

		self.__clickPosition = 0, 0
		self.__popupTimeDelay = None

		self.__pie = None
		self.__pie = PieMenu(self.sliceStyle)
		self.__pie.connect("button_release_event", self._on_button_release)
		self.__pie.show()

		self.__popupWindow = gtk.Window(type = gtk.WINDOW_POPUP)
		self.__popupWindow.set_title("")
		self.__popupWindow.add(self.__pie)

		self.add_slice(NullPieSlice(), PieSlice.SLICE_CENTER)

	def add_slice(self, slice, direction):
		assert direction in PieSlice.SLICE_DIRECTIONS

		self.__pie.add_slice(copy.copy(slice), direction)

		if self.showAllSlices or direction == PieSlice.SLICE_CENTER:
			self.__localSlices[direction] = slice
			self.__localSlices[direction].menu_init(self, direction)
		if direction == PieSlice.SLICE_CENTER:
			self.__activeSlice = self.__localSlices[PieSlice.SLICE_CENTER]

	def __update_state(self, mousePosition):
		rect = self.get_allocation()
		newStyleState = self.__styleState

		if (
			0 <= mousePosition[0] and mousePosition[0] < rect.width and
			0 <= mousePosition[1] and mousePosition[1] < rect.height
		):
			if self.__clickPosition == (0, 0):
				newStyleState = gtk.STATE_PRELIGHT
		else:
			if self.__clickPosition != (0, 0):
				newStyleState = gtk.STATE_PRELIGHT

		if newStyleState != self.__styleState:
			self.__styleState = newStyleState
			self.__generate_draw_event()

	def __generate_draw_event(self):
		self.queue_draw()

	def _on_expose(self, widget, event):
		rect = self.get_allocation()
		position = 0, 0
		dimensions = rect.width, rect.height

		# update sizing information
		self.centerPosition = position[0] + dimensions[0] / 2, position[1] + dimensions[1] / 2
		self.outerRadius = max(*dimensions) # be larger than the view
		self.radius = self.outerRadius / (3*2) # fit inside the middle cell

		# Draw Background
		cairoContext = self.window.cairo_create()
		cairoContext.rectangle(
			position[0],
			position[1],
			dimensions[0],
			dimensions[1],
		)
		cairoContext.set_source_rgb(*self.sliceStyle[self.__styleState]["fill"])
		cairoContext.fill()

		# Draw Foreground
		pangoContext = self.create_pango_context()
		textLayout = pango.Layout(pangoContext)
		for slice in self.__localSlices.itervalues():
			isSelected = (slice is self.__activeSlice)
			if not isSelected:
				slice.draw_fg(self.__styleState, isSelected, cairoContext, textLayout)

		isSelected = self.__clickPosition != (0, 0)
		self.__activeSlice.draw_fg(self.__styleState, isSelected, cairoContext, textLayout)

	def _on_leave_notify(self, widget, event):
		newStyleState = gtk.STATE_NORMAL
		if newStyleState != self.__styleState:
			self.__styleState = newStyleState
			self.__generate_draw_event()

		self._on_motion_notify(widget, event)

	def _on_motion_notify(self, widget, event):
		self.__update_state(event.get_coords())
		if not self.__popped:
			return

		mousePosition = event.get_root_coords()
		piePosition = self.__popupWindow.get_position()
		event.x = mousePosition[0] - piePosition[0]
		event.y = mousePosition[1] - piePosition[1]
		self.__pie._on_motion_notify(self.__pie, event)

	def _on_button_press(self, widget, event):
		if len(self.__localSlices) == 0:
			return

		if self.__popupTimeDelay is not None:
			# This press is for a double click for which we do not get a release
			# self._on_button_release(widget, event)
			return

		self.__clickPosition = event.get_root_coords()
		self.__generate_draw_event()
		self.__popupTimeDelay = gobject.timeout_add(150, self._on_delayed_popup)

	def _on_delayed_popup(self):
		self.__popup(self.__clickPosition)
		gobject.source_remove(self.__popupTimeDelay)
		self.__popupTimeDelay = None
		return False

	def _on_button_release(self, widget, event):
		if len(self.__localSlices) == 0:
			return

		if self.__popupTimeDelay is None:
			mousePosition = event.get_root_coords()
			piePosition = self.__popupWindow.get_position()
			eventX = mousePosition[0] - piePosition[0]
			eventY = mousePosition[1] - piePosition[1]
			pieRelease = FakeEvent(eventX, eventY, False)
			self.__pie._on_button_release(self.__pie, pieRelease)

			self.__unpop()
		else:
			gobject.source_remove(self.__popupTimeDelay)
			self.__popupTimeDelay = None
			self.__activeSlice.activate()

		self.__clickPosition = 0, 0
		self.__generate_draw_event()

	def __popup(self, position):
		assert not self.__popped
		self.__popped = True

		width, height = 256, 256
		popupX, popupY = position[0] - width/2, position[1] - height/2

		self.__popupWindow.move(int(popupX), int(popupY))
		self.__popupWindow.resize(width, height)
		pieClick = FakeEvent(width/2, height/2, False)
		self.__pie._on_button_press(self.__pie, pieClick)
		self.__pie.grab_focus()

		self.__popupWindow.show()

	def __unpop(self):
		assert self.__popped
		self.__popped = False

		piePosition = self.__popupWindow.get_position()
		self.grab_focus()

		self.__popupWindow.hide()


gobject.type_register(PiePopup)


def pie_main(isPop):
	win = gtk.Window()
	win.set_title("Pie Menu Test")

	sliceStyle = generate_pie_style(win)
	if isPop:
		target = PiePopup(sliceStyle)
	else:
		target = PieMenu(sliceStyle)

	def handler(pie, slice, direction):
		print pie, slice, direction
	target.add_slice(TextLabelPieSlice("C", handler=handler), PieSlice.SLICE_CENTER)
	target.add_slice(TextLabelPieSlice("N", handler=handler), PieSlice.SLICE_NORTH)
	target.add_slice(TextLabelPieSlice("S", handler=handler), PieSlice.SLICE_SOUTH)
	target.add_slice(TextLabelPieSlice("E", handler=handler), PieSlice.SLICE_EAST)
	target.add_slice(TextLabelPieSlice("W", handler=handler), PieSlice.SLICE_WEST)

	win.add(target)
	win.resize(300, 300)
	win.connect("destroy", lambda w: gtk.main_quit())
	win.show_all()


if __name__ == "__main__":
	pie_main(False)
	pie_main(True)
	gtk.main()
