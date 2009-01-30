#!/usr/bin/env python


from __future__ import with_statement


def flatten(elem, includeTail = False):
	"""
	Recursively extract text content.

	@note To get rid of all subelements to a given element, and keep just the text, you can do:
		elem.text = flatten(elem); del elem[:]
	"""
	text = elem.text or ""
	for e in elem:
		text += flatten(e)
		if includeTail and e.tail:
			text += e.tail
	return text


def append(elem, item):
	"""
	Universal append to an Element
	@param elem ElementTree.Element
	@param item Either None, Str/Unicode, or ElementTree.Element
	"""
	if item is None:
		return

	if isinstance(item, basestring):
		if len(elem):
			elem[-1].tail = (elem[-1].tail or "") + item
		else:
			elem.text = (elem.text or "") + item
	else:
		elem.append(item)


def indent(elem, level=0, indentation="    "):
	"""
	Add indentation to the data of in an ElementTree

	>>> from xml.etree import ElementTree
	>>> xmlRoot = ElementTree.fromstring("<xml><tree><bird /></tree></xml>")
	>>> indent(xmlRoot)
	>>> ElementTree.dump(xmlRoot)
	<xml>
	    <tree>
	        <bird />
	    </tree>
	</xml>
	"""

	i = "\n" + level*indentation
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + indentation
		for e in elem:
			indent(e, level+1, indentation)
			if not e.tail or not e.tail.strip():
				e.tail = i + indentation
			if not e.tail or not e.tail.strip():
				e.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i


if __name__ == "__main__":
	import sys
	from xml.etree import ElementTree
	if len(sys.argv) == 3:
		xml = ElementTree.parse(sys.argv[1])
		indent(xml.getroot())
		with open(sys.argv[2], "w") as source:
			xml.write(source)
	elif len(sys.argv) == 1:
		xml = ElementTree.parse(sys.stdin)
		indent(xml.getroot())
		xml.write(sys.stdout)
