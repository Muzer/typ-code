#!/bin/bash

while true; do
  ./data_logger.py >>log.txt 2>>err.txt
done
