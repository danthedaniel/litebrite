#!/bin/bash
set -e
mpremote \
  cp main.py :main.py + \
  cp microdot.py :microdot.py + \
  cp font.py :font.py + \
  cp screen.py :screen.py + \
  cp index.html :index.html + \
  reset
echo "Deployed and reset."
