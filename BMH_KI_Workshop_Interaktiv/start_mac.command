#!/bin/bash
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 fehlt. Bitte Python 3 installieren (https://www.python.org/downloads/)."
  read -r -p "Enter zum Schliessen …"
  exit 1
fi
python3 ki_workshop.py
read -r -p "Enter zum Schliessen …"
