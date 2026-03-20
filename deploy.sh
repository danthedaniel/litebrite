#!/bin/bash
set -e
mpremote cp main.py :main.py + cp font.py :font.py + cp index.html :index.html + reset
echo "Deployed and reset."
