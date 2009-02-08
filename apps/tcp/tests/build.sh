#!/bin/bash

# Uses repypp to build tests.
# Puts tests in $TESTDIR.

: ${1?"Usage: $0 output_directory [files ...]"}

REPYPP=../../../../seattlelib/repypp.py 
TESTDIR=$1

if [ ! -e ../${TESTDIR} ]
then
  mkdir ../${TESTDIR}
fi

files=$2
# copy in included files
cp ../*.repy .
echo "Building tests..."
for f in ${files}
do
  echo ${f}
  python ${REPYPP} ${f} ../${TESTDIR}/${f}
done
echo "Done"

exit

