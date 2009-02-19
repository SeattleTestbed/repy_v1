###############
# Usage
###############
# Makefile to quickly build and run test files.
# Use:
# 	make - run all tests
# 	make units - run low-level function tests
# 	make funcs - run class scope tests
# 	make ingrs - run integrations
#	make clean - delete built tests and test output
#
# You can pass the FN=<regex> to match subsets of tests.
# Ex. make units FN=state_machin
#     make ingrs FN=net_tiny
#
# You can run a file without the test framework by:
#	make run FN=<regex>
# Ex. make run FN=z_test_me.repy
################

############
# Constants
###########
TESTDIR=tmp_test_dir
TESTS_SRC_DIR=tests
FN=[zne]_test_*
UNITS=${TESTS_SRC_DIR}/units
FUNCS=${TESTS_SRC_DIR}/functionals
INGRS=${TESTS_SRC_DIR}/integrations

#############
# Public Commands
#############

# Run through Test framework
all: cp_units cp_funcs cp_ingrs build test
units: cp_units build test
funcs: cp_funcs build test
ingrs: cp_ingrs build test

# Use to execute a single test file without framework.
# Ex. make run FN=<filename>
run: cp_units cp_funcs cp_ingrs build
	cd ${TESTDIR} && python repy.py restrictions.default *${FN}*

clean: 
	rm -rf ${TESTDIR}
	for file in `ls *.repy`; do rm -f ${TESTS_SRC_DIR}/$${file}; done
	for file in `ls ${UNITS}/*`; do rm -f ${TESTS_SRC_DIR}/`basename $${file}`; done
	for file in `ls ${FUNCS}/*`; do rm -f ${TESTS_SRC_DIR}/`basename $${file}`; done
	for file in `ls ${INGRS}/*`; do rm -f ${TESTS_SRC_DIR}/`basename $${file}`; done


################
# Private Commands
###############

# Run seattle's test script.  Test should be built first.
test: 
	cd ${TESTDIR} && python run_tests.py

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



