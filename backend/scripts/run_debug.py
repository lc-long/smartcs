import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("server_debug.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

import uvicorn

uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000)
