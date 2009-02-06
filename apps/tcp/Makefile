#!/bin/bash

# Makefile to quickly build and run test files.
# Use:
# 	make - run seattle's test script
#	make CN=<classname> - runs only specific class tests
#	make run FN=<testname> - run a single test
#	make clean - delete built tests and test output
TESTDIR=tmp_test_dir
TESTS_SRC_DIR=tests

# Builds tests first. Then,
# Run seattle's test script.
test: build
	cd ${TESTDIR} && python run_tests.py

# Runs a single test
# Takes FN as arg, ex. `make run FN=z_test_me.py`
run: build
	cd ${TESTDIR} && python repy.py restrictions.default ${FN}

clean: 
	rm -rf ${TESTDIR}
	for file in `ls *.repy`; do rm -f ${TESTS_SRC_DIR}/$${file}; done

#### Private ####
# Builds all test files
# Takes CN as arg, ex. `make run CN=controller` to only build a certain class
build:
	cd ${TESTS_SRC_DIR} && ./build.sh ${TESTDIR} ${CN}
	cp ${TESTS_SRC_DIR}/*.txt ${TESTDIR}
	cp ${TESTS_SRC_DIR}/restrictions.* ${TESTDIR}
	cp ${TESTS_SRC_DIR}/run_tests.py ${TESTDIR}
	cp ../../*.py ${TESTDIR}
