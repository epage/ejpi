PROJECT_NAME=ejpi
PACKAGE_NAME=$(PROJECT_NAME)
SOURCE_PATH=$(PACKAGE_NAME)
SOURCE=$(shell find $(SOURCE_PATH) -iname "*.py")
PROGRAM=$(PROJECT_NAME)
OBJ=$(SOURCE:.py=.pyc)
DIST_BASE_PATH=./dist
ICON_SIZES=22 28 32 48
ICONS=$(foreach size, $(ICON_SIZES), data/icons/$(size)/$(PROJECT_NAME).png)
TAG_FILE=~/.ctags/$(PROJECT_NAME).tags
TODO_FILE=./TODO

DEBUGGER=winpdb
UNIT_TEST=nosetests --with-doctest -w .
SYNTAX_TEST=support/test_syntax.py
STYLE_TEST=../../Python/tools/pep8.py --ignore=W191,E501
LINT_RC=./support/pylint.rc
LINT=pylint --rcfile=$(LINT_RC)
PROFILE_GEN=python -m cProfile -o .profile
PROFILE_VIEW=python -m pstats .profile
TODO_FINDER=support/todo.py
CTAGS=ctags-exuberant

.PHONY: all run profile debug test build lint tags todo clean distclean

all: test

run: $(OBJ)
	$(PROGRAM)

profile: $(OBJ)
	$(PROFILE_GEN) $(PROGRAM)
	$(PROFILE_VIEW)

debug: $(OBJ)
	$(DEBUGGER) $(PROGRAM)

test: $(OBJ)
	$(UNIT_TEST)

setup.fremantle.py: setup.py
	cog.py -D desktopFilePath=/usr/share/applications/hildon -o ./setup.fremantle.py ./setup.py
	chmod +x ./setup.fremantle.py

setup.harmattan.py: setup.py
	cog.py -D desktopFilePath=/usr/share/applications -o ./setup.harmattan.py ./setup.py
	chmod +x ./setup.harmattan.py

package: $(OBJ) $(ICONS) setup.harmattan.py setup.fremantle.py
	./setup.fremantle.py sdist_diablo -d $(DIST_BASE_PATH)_diablo
	./setup.fremantle.py sdist_fremantle -d $(DIST_BASE_PATH)_fremantle
	./setup.harmattan.py sdist_harmattan -d $(DIST_BASE_PATH)_harmattan

upload:
	dput diablo-extras-builder $(DIST_BASE_PATH)_diablo/$(PROJECT_NAME)*.changes
	dput fremantle-extras-builder $(DIST_BASE_PATH)_fremantle/$(PROJECT_NAME)*.changes

lint: $(OBJ)
	$(foreach file, $(SOURCE), $(LINT) $(file) ; )

tags: $(TAG_FILE) 

todo: $(TODO_FILE)

clean:
	rm -Rf $(OBJ)
	rm -f $(ICONS)
	rm -Rf $(TODO_FILE)
	rm -f setup.harmattan.py setup.fremantle.py
	rm -Rf $(DIST_BASE_PATH)_diablo build
	rm -Rf $(DIST_BASE_PATH)_fremantle build
	rm -Rf $(DIST_BASE_PATH)_harmattan build

distclean: clean
	find $(SOURCE_PATH) -name "*.*~" | xargs rm -f
	find $(SOURCE_PATH) -name "*.swp" | xargs rm -f
	find $(SOURCE_PATH) -name "*.bak" | xargs rm -f
	find $(SOURCE_PATH) -name ".*.swp" | xargs rm -f

$(ICONS): data/$(PROJECT_NAME).png support/scale.py
	mkdir -p $(dir $(ICONS))
	$(foreach size, $(ICON_SIZES), support/scale.py --input data/$(PROJECT_NAME).png --output data/icons/$(size)/$(PROJECT_NAME).png --size $(size) ; )

$(TAG_FILE): $(OBJ)
	mkdir -p $(dir $(TAG_FILE))
	$(CTAGS) -o $(TAG_FILE) $(SOURCE)

$(TODO_FILE): $(SOURCE)
	@- $(TODO_FINDER) $(SOURCE) > $(TODO_FILE)

%.pyc: %.py
	$(SYNTAX_TEST) $<

#Makefile Debugging
#Target to print any variable, can be added to the dependencies of any other target
#Userfule flags for make, -d, -p, -n
print-%: ; @$(error $* is $($*) ($(value $*)) (from $(origin $*)))
