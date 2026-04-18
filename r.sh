#!/usr/bin/env bash

mkdir -p tmp/local tmp/pnpm-home tmp/pnpm-store tmp/npm-cache
docker run --rm -it \
  --init \
  --ipc=host \
  --mount type=bind,src="$PWD",dst=/code \
  -w /code \
  -p 127.0.0.1:8821:8821 \
  -p 127.0.0.1:8822:8822 \
  -p 127.0.0.1:8823:8823 \
  data_camp_exp
