#!/bin/bash

# Makefile to quickly build and run test files.
# Use:
# 	make - run seattle's test script
#	make run FN=<testname> - run a single test
#	make clean - delete built tests and test output
TEST_DIR=test
UNIT_TESTS_DIR=unit_tests

# Builds tests first. Then,
# Run seattle's test script.
test: build
	cd ${TEST_DIR} && python run_tests.py

# Runs a single test
# Takes FN as arg, ex. `make run FN=z_test_me.py`
run: build
	cd ${TEST_DIR} && python repy.py restrictions.default ${FN}

clean: 
	rm -f ${TEST_DIR}/[zne]_test*.py ${TEST_DIR}/*.pyc ${TEST_DIR}/foo-Terminated-* ${TEST_DIR}/junk_test.out
	for file in `ls *.repy`; do rm -f ${UNIT_TESTS_DIR}/$${file}; done

#### Private ####
build:
	cd ${UNIT_TESTS_DIR} && ./build.sh
