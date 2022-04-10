#!/bin/bash
mkdir ../kycnotbackup
cp -r ./* ../kycnotbackup
git pull
docker stop kycnot-newui
docker rm kycnot-newui
docker build -t pluja/kycnot-newui .
docker run -d -p 1338:1337 --name kycnot-newui pluja/kycnot-newui