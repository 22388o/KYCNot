FROM python:3-alpine AS base
# Image to Build Dependencies
FROM base AS builder
WORKDIR /app
COPY ./requirements.txt /app
# Build Dependencies
RUN apk update
RUN apk add musl-dev g++ gcc make 
RUN apk add python3-dev build-base git
RUN apk add libffi-dev openssl-dev libxml2-dev 
RUN apk add libxslt-dev llvm-dev file

# Python Dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir --prefix=/install gunicorn
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime Environment Image
FROM base
WORKDIR /app

# CRONJOBS
RUN crontab -l | { cat; echo "0 3 * * * python3 /app/automated-checks.py"; } | crontab -

# Runtime Dependencies
COPY --from=builder /install /usr/local
COPY . /app/
RUN apk --no-cache add libxml2 libxslt musl-dev zlib-dev jpeg-dev gcc
RUN pip install pillow
EXPOSE 1337
CMD sanic kycnot.app --host=0.0.0.0 --port=1337 --workers=4
#CMD gunicorn kycnot:app --bind 0.0.0.0:1337 --worker-class sanic.worker.GunicornWorker