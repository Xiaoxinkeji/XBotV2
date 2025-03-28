#!/bin/bash
redis-server /etc/redis/redis.conf --daemonize yes
python app.py
