#!/bin/bash

filename=central-fed-district-latest
wget -t http://download.geofabrik.de/russia/$filename.osm.pbf

osmconvert $filename.osm.pbf -o=$filename.o5m
osmfilter $filename.o5m --drop-author --keep="all highway="   --out-o5m >$filename-filtered.o5m
osmconvert $filename-filtered.o5m -o=$filename-filtered.pbf
