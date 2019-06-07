#!/bin/bash

filename=central-fed-district-latest
wget --timestamping http://download.geofabrik.de/russia/$filename.osm.pbf

osmupdate $filename.osm.pbf $filename-updated.osm.pbf
osmconvert $filename-updated.osm.pbf -o=$filename.o5m
osmfilter $filename.o5m --drop-author --keep="all highway="   --out-o5m >$filename-filtered.o5m
osmconvert $filename-filtered.o5m -o=$filename-filtered.pbf

mkdir output

ogr2ogr -f "ESRI Shapefile" -progress -overwrite -skipfailures -nlt LINESTRING output $filename-filtered.pbf -oo CONFIG_FILE=osmconf.ini

(cd output;zip -r  ../output.zip * -i 'lines.*';cd ..)
