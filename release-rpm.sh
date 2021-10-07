#!/bin/bash

VERSION="1.0"

rm softwalltime-predictor-$VERSION -rf
mkdir -p softwalltime-predictor-$VERSION

cp hook_softwalltime_predictor.py softwalltime-predictor-$VERSION/
cp pbs_softwalltime_predictor softwalltime-predictor-$VERSION/
cp softwalltime.conf softwalltime-predictor-$VERSION/
cp softwalltime-predictor.spec softwalltime-predictor-$VERSION/
cp softwalltime_predictor-detector softwalltime-predictor-$VERSION/
cp softwalltime_predictor-runtime_saver softwalltime-predictor-$VERSION/
cp softwalltime_psql.py softwalltime-predictor-$VERSION/

tar -cvzf softwalltime-predictor-${VERSION}.tar.gz softwalltime-predictor-$VERSION
rm softwalltime-predictor-$VERSION -rf

mkdir -p ~/rpmbuild/SOURCES/
mv softwalltime-predictor-${VERSION}.tar.gz ~/rpmbuild/SOURCES/

rpmbuild -ba softwalltime-predictor.spec
