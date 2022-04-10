#!/bin/bash
mkdir ../kycnotbackup
cp -r ./* ../kycnotbackup
git pull
docker stop kycnot-newui
docker rm kycnot-newui
docker build -t pluja/kycnot-newui .
docker run -p 1337:1337 --name kycnot-newui pluja/kycnot-newui
#docker exec -it kycnot apk add zlib-dev jpeg-dev gcc musl-dev
#docker exec -it kycnot pip install pillow