import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
import logging
import traceback
import asyncio

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Import the route handler
from routes.retrieve import RetrieveRequest, retrieve_capabilities

async def test():
    req = RetrieveRequest(requirements=["Must have HIPAA compliance certification"])
    logger.info(f"Testing retrieve_capabilities with: {req.requirements}")
    try:
        result = await retrieve_capabilities(req)
        logger.info(f"Success: {result}")
    except Exception as e:
        logger.error(f"Error: {e}")
        traceback.print_exc()

asyncio.run(test())
