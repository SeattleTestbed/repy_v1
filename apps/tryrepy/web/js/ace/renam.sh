#! /bin/bash
IFS=$'\n'

for x in $(find . -iname "theme*" ); do
y=${x/theme-/}   
mv "$x" "${y}"

done

