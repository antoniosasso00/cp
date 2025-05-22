#!/bin/bash
set -e

# Avvia l'applicazione direttamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 