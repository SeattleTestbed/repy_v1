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

UNITS=${TESTS_SRC_DIR}/units
FUNCS=${TESTS_SRC_DIR}/functionals
INGRS=${TESTS_SRC_DIR}/integrations

# Builds tests first. Then,
all: cp_units cp_funcs cp_ingrs build test
units: cp_units build test
funcs: cp_funcs build test
ingrs: cp_ingrs build test

# Run seattle's test script.
test: 
	cd ${TESTDIR} && python run_tests.py

clean: 
	rm -rf ${TESTDIR}
	for file in `ls *.repy`; do rm -f ${TESTS_SRC_DIR}/$${file}; done
	for file in `ls ${UNITS}/*`; do rm -f ${TESTS_SRC_DIR}/`basename $${file}`; done
	for file in `ls ${FUNCS}/*`; do rm -f ${TESTS_SRC_DIR}/`basename $${file}`; done
	for file in `ls ${INGRS}/*`; do rm -f ${TESTS_SRC_DIR}/`basename $${file}`; done

#### Private ####
# Builds all test files
# Takes FN as arg, ex. `make FN=*controller*` to build all files with glob.
build:
	cd ${TESTS_SRC_DIR} && ./build.sh ${TESTDIR} "*${FN}*"
	cp ${TESTS_SRC_DIR}/*.txt ${TESTDIR}
	cp ${TESTS_SRC_DIR}/restrictions.* ${TESTDIR}
	cp ${TESTS_SRC_DIR}/run_tests.py ${TESTDIR}
	cp ../../*.py ${TESTDIR}

cp_units:
	cp ${UNITS}/* ${TESTS_SRC_DIR}
cp_funcs:
	cp ${FUNCS}/* ${TESTS_SRC_DIR}
cp_ingrs:
	cp ${INGRS}/* ${TESTS_SRC_DIR}


##### Deprecated ###
# Use make FN=<filename> instead
run: cp_units cp_funcs cp_ingrs build
	cd ${TESTDIR} && python repy.py restrictions.default ${FN}

