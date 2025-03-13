#!/usr/bin/env bash

set -xe

docker run -d \
  -p 8000:8000 \
  -v chroma-data:/chromadb/data \
  chromadb/chroma
