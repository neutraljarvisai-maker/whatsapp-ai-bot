import time
import logging
from vecta_os.agents.coordinator import coordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("VECTA Worker Service Starting (Polling Queue)...")
    # This would typically poll a Task Queue (Redis/Postgres)
    # For now, it keeps the process alive as a placeholder for long-running tasks
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("VECTA Worker Service Stopped.")
