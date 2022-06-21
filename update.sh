#!/bin/bash
mkdir ../kycnotbackup
cp -r ./* ../kycnotbackup
docker stop kycnot-newui
docker rm kycnot-newui
docker build -t pluja/kycnot-newui .