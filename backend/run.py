#!/usr/bin/env python
import os
import sys
import uvicorn

# Ajouter le répertoire backend au sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Démarrer le serveur
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
