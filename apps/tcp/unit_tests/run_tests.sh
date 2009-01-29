#!/bin/bash

# Must call ./build.sh first to make tests.
# Runs test files.  Output is undefined.
# Does not check whether the tests pass or fail.

TESTDIR=../test
REPY=../test/repy.py
RESTR=../test/restrictions.default

echo "Running tests..."
files=`ls ../test/[zne]_test*.py`
for f in ${files}
do
  echo ${f}
  python ${REPY} ${RESTR} ${f}
done
echo "Done"

exit

