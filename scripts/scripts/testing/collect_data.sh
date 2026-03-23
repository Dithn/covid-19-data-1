#!/bin/bash
set -e


if [ $1 == quick ]
then
  mode=incremental
elif [ $1 == update ]
then
  mode=all
else
  echo "Wrong execution mode ('quick' or 'update')."
  exit
fi


cd ~/repos/covid-19-data
git pull

cowid test get -c $mode