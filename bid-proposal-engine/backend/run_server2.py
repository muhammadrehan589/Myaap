import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
import logging
import traceback

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server_debug.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

try:
    from main import app
    logger.info("App imported successfully")
    
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host='0.0.0.0', port=8001, log_level='debug')
except Exception as e:
    logger.error(f"Server failed: {e}")
    traceback.print_exc()
