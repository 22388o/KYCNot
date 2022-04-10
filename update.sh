#!/bin/bash
mkdir ../kycnotbackup
cp -r ./* ../kycnotbackup
git pull
docker stop kycnot
docker rm kycnot
docker build -t pluja/kycnot .
docker run -p 1337:1337 --name kycnot pluja/kycnot
#docker exec -it kycnot apk add zlib-dev jpeg-dev gcc musl-dev
#docker exec -it kycnot pip install pillow