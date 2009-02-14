PROJECT_NAME=ejpi
SOURCE_PATH=src
SOURCE=$(shell find $(SOURCE_PATH) -iname *.py)
PROGRAM=$(SOURCE_PATH)/$(PROJECT_NAME).py
DATA_TYPES=*.ini *.map *.glade *.png
DATA=$(foreach type, $(DATA_TYPES), $(shell find $(SOURCE_PATH) -iname $(type)))
OBJ=$(SOURCE:.py=.pyc)
BUILD_PATH=./build/
BUILD_SOURCE=$(foreach file, $(SOURCE), $(BUILD_PATH)/$(subst /,-,$(file)))
TAG_FILE=~/.ctags/$(PROJECT_NAME).tags
TODO_FILE=./TODO

DEBUGGER=winpdb
UNIT_TEST=nosetests --with-doctest -w $(TEST_PATH)
STYLE_TEST=../../Python/tools/pep8.py --ignore=W191,E501
LINT_RC=./support/pylint.rc
LINT=pylint --rcfile=$(LINT_RC)
TODO_FINDER=support/todo.py
PROFILE_GEN=python -m cProfile -o .profile
PROFILE_VIEW=python -m pstats .profile
CTAGS=ctags-exuberant

.PHONY: all run profile debug test lint tags todo package clean distclean

all: test package

run: $(SOURCE)
	$(SOURCE_PATH)/ejpi_glade.py

profile: $(SOURCE)
	$(PROFILE_GEN) $(PROGRAM)
	$(PROFILE_VIEW)

debug: $(SOURCE)
	$(DEBUGGER) $(PROGRAM)

test: $(SOURCE)
	$(UNIT_TEST)

package:
	rm -Rf $(BUILD_PATH)
	mkdir $(BUILD_PATH)
	cp $(SOURCE_PATH)/$(PROJECT_NAME).py  $(BUILD_PATH)
	$(foreach file, $(DATA), cp $(file) $(BUILD_PATH)/$(subst /,-,$(file)) ; )
	$(foreach file, $(SOURCE), cp $(file) $(BUILD_PATH)/$(subst /,-,$(file)) ; )
	cp support/$(PROJECT_NAME).desktop $(BUILD_PATH)
	cp support/builddeb.py $(BUILD_PATH)

lint: $(SOURCE)
	$(foreach file, $(SOURCE), $(LINT) $(file) ; )

tags: $(TAG_FILE) 

todo: $(TODO_FILE)

clean:
	rm -Rf $(OBJ)
	rm -Rf $(BUILD_PATH)

distclean:
	rm -Rf $(OBJ)
	rm -Rf $(BUILD_PATH)
	rm -Rf $(TAG_FILE)
	find $(SOURCE_PATH) -name "*.*~" | xargs rm -f
	find $(SOURCE_PATH) -name "*.swp" | xargs rm -f
	find $(SOURCE_PATH) -name "*.bak" | xargs rm -f
	find $(SOURCE_PATH) -name ".*.swp" | xargs rm -f

$(TAG_FILE): $(SOURCE)
	mkdir -p $(dir $(TAG_FILE))
	$(CTAGS) -o $(TAG_FILE) $(SOURCE)

$(TODO_FILE): $(SOURCE)
	@- $(TODO_FINDER) $(SOURCE) > $(TODO_FILE)

#Makefile Debugging
#Target to print any variable, can be added to the dependencies of any other target
#Userfule flags for make, -d, -p, -n
print-%: ; @$(error $* is $($*) ($(value $*)) (from $(origin $*)))
