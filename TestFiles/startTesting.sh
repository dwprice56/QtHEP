#!/usr/bin/env bash

while read line
  do
    chmod +x ../$line
  done < executableFiles.txt

rm *.xml
