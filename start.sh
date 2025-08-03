#!/bin/bash
echo "Starting Fitness Tracker application..."
gunicorn --bind 0.0.0.0:$PORT wsgi:app 