#!/usr/bin/env python3
"""Entry point for TenderPortal backend."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from portal.config import PORT

if __name__ == "__main__":
    uvicorn.run(
        "portal.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info",
    )
