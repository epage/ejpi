PROJECT_NAME=ejpi
SOURCE_PATH=src
SOURCE=$(shell find $(SOURCE_PATH) -iname *.py)
OBJ=$(SOURCE:.py=.pyc)
TAG_FILE=~/.ctags/$(PROJECT_NAME).tags
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

.PHONY: all run debug test lint tags todo package clean

all: test package

run: $(SOURCE)
	$(SOURCE_PATH)/ejpi_glade.py

debug: $(SOURCE)
	$(DEBUGGER) $(SOURCE_PATH)/ejpi_glade.py

test: $(SOURCE)
	$(SOURCE_PATH)/ejpi_glade.py -t

package:
	./builddeb.py

lint:
	$(foreach file, $(SOURCE), $(LINT) $(file) ; )

tags: $(TAG_FILE) 

todo: $(TODO_FILE)

clean:
	rm -Rf $(OBJ)

$(TAG_FILE): $(SOURCE)
	mkdir -p $(dir $(TAG_FILE))
	$(CTAGS) -o $(TAG_FILE) $(SOURCE)

$(TODO_FILE): $(SOURCE)
	@- $(TODO_FINDER) $(SOURCE) > $(TODO_FILE)

#Makefile Debugging
#Target to print any variable, can be added to the dependencies of any other target
#Userfule flags for make, -d, -p, -n
print-%: ; @$(error $* is $($*) ($(value $*)) (from $(origin $*)))
