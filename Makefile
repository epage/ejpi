PROJECT_NAME=ejpi
SOURCE_PATH=src
SOURCE=$(shell find $(SOURCE_PATH) -iname *.py)
DATA=$(shell find $(SOURCE_PATH) -iname *.ini) $(shell find $(SOURCE_PATH) -iname *.map)
OBJ=$(SOURCE:.py=.pyc)
TAG_FILE=~/.ctags/$(PROJECT_NAME).tags
BUILD_PATH=./build/
BUILD_SOURCE=$(foreach file, $(SOURCE), $(BUILD_PATH)/$(subst /,-,$(file)))
TODO_FILE=./TODO

DEBUGGER=winpdb
UNIT_TEST=nosetests -w $(TEST_PATH)
STYLE_TEST=../../Python/tools/pep8.py --ignore=W191
LINT_RC=./support/pylint.rc
LINT=pylint --rcfile=$(LINT_RC)
COVERAGE_TEST=figleaf
PROFILER=pyprofiler
CTAGS=ctags-exuberant
TODO_FINDER=support/todo.py

.PHONY: all run debug test lint tags todo package clean distclean

all: test package

run: $(SOURCE)
	$(SOURCE_PATH)/ejpi_glade.py

debug: $(SOURCE)
	$(DEBUGGER) $(SOURCE_PATH)/ejpi_glade.py

test: $(SOURCE)
	$(SOURCE_PATH)/ejpi_glade.py -t

package:
	rm -Rf $(BUILD_PATH)
	mkdir $(BUILD_PATH)
	cp $(SOURCE_PATH)/$(PROJECT_NAME).py  $(BUILD_PATH)
	cp $(SOURCE_PATH)/$(PROJECT_NAME).glade  $(BUILD_PATH)
	$(foreach file, $(DATA), cp $(file) $(BUILD_PATH)/$(subst /,-,$(file)) ; )
	$(foreach file, $(SOURCE), cp $(file) $(BUILD_PATH)/$(subst /,-,$(file)) ; )
	cp support/$(PROJECT_NAME).desktop $(BUILD_PATH)
	cp support/builddeb.py $(BUILD_PATH)

lint:
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

$(TAG_FILE): $(SOURCE)
	mkdir -p $(dir $(TAG_FILE))
	$(CTAGS) -o $(TAG_FILE) $(SOURCE)

$(TODO_FILE): $(SOURCE)
	@- $(TODO_FINDER) $(SOURCE) > $(TODO_FILE)

#Makefile Debugging
#Target to print any variable, can be added to the dependencies of any other target
#Userfule flags for make, -d, -p, -n
print-%: ; @$(error $* is $($*) ($(value $*)) (from $(origin $*)))
