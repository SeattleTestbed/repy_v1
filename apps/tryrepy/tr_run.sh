#! /bin/bash

if [ $# -ne 2 ]
  then
    echo "Usage: $1 </abspath/to/seattle_repy> <serverport>" >&2
    exit 1
fi

if [ ! -d "$1" ]
  then
    echo "Usage: $1 </abspath/to/seattle_repy> <serverport>" >&2
    exit 2
fi


echo "Copying files from build to seattle_repy directory..."
cp build/* $1
echo "Changing to $1"
cd $1
echo "Preprocessing tr_webcontroller.py..."
python repypp.py tr_webcontroller.py tr_webcontroller.repy
echo "Executing tr_webcontroller.repy..."
python repy.py restrictions.tryrepy tr_webcontroller.repy $2

exit 0