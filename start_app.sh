#!/bin/bash
gunicorn --bind 0.0.0.0:5001 --reuse-port --reload main:app