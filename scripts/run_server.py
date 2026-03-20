#!/usr/bin/env python3
import os
import sys

os.chdir("/Users/apple/workdata/person/zy/RANGEN-main(syu-python)")
os.environ["PYTHONPATH"] = "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"

import uvicorn
sys.path.insert(0, "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)")

from src.api.server import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
