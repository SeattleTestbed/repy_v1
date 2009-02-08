#!/bin/bash

# Makefile to quickly build and run test files.
# Use:
# 	make - run seattle's test script
#	make CN=<classname> - runs only specific class tests
#	make run FN=<testname> - run a single test
#	make clean - delete built tests and test output
TESTDIR=tmp_test_dir
TESTS_SRC_DIR=tests
FN=[zne]_test_*

# Builds tests first. Then,
# Run seattle's test script.
test: build
	cd ${TESTDIR} && python run_tests.py

clean: 
	rm -rf ${TESTDIR}
	for file in `ls *.repy`; do rm -f ${TESTS_SRC_DIR}/$${file}; done

#### Private ####
# Builds all test files
# Takes FN as arg, ex. `make FN=*controller*` to build all files with glob.
build:
	cd ${TESTS_SRC_DIR} && ./build.sh ${TESTDIR} "${FN}"
	cp ${TESTS_SRC_DIR}/*.txt ${TESTDIR}
	cp ${TESTS_SRC_DIR}/restrictions.* ${TESTDIR}
	cp ${TESTS_SRC_DIR}/run_tests.py ${TESTDIR}
	cp ../../*.py ${TESTDIR}

##### Deprecated ###
# Use make FN=<filename> instead
run: build
	cd ${TESTDIR} && python repy.py restrictions.default ${FN}

