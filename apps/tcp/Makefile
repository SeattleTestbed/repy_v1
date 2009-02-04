#!/bin/bash

# Makefile to quickly build and run test files.
# Use:
# 	make - run seattle's test script
#	make test - run without a test framework
#	make clean - delete built tests
TEST_DIR=test
UNIT_TESTS_DIR=unit_tests

# Builds tests first. Then,
# Run seattle's test script.
seattle_test: build
	cd ${TEST_DIR} && python run_tests.py

# Builds tests first. Then,
# Run the tests without a test framework.
test: build
	cd ${UNIT_TESTS_DIR} && ./run_tests.sh

# Takes FN as arg like `make run FN=<testname>`
run: build
	cd ${TEST_DIR} && python repy.py restrictions.default ${FN}

clean: 
	rm -f ${TEST_DIR}/[zne]_test*.py ${TEST_DIR}/*.pyc ${TEST_DIR}/foo-Terminated-* ${UNIT_TESTS_DIR}/tcp.repy

#### Private ####
build:
	cd ${UNIT_TESTS_DIR} && ./build.sh
