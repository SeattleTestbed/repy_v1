#!/bin/bash

# Uses repypp to build tests.
# Puts tests in $TESTDIR.

REPYPP=../test/repypp.py
TESTDIR=../test

cp ../tcp.repy .
echo "Building tests..."
files=`ls [zne]_test*.py`
for f in ${files}
do
  echo ${f}
  python ${REPYPP} ${f} ${TESTDIR}/${f}
done
echo "Done"

exit

