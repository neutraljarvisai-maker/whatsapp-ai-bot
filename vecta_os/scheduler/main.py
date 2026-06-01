import time
import logging
from vecta_os.scheduler.scheduler import scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("VECTA Scheduler Service Starting...")
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("VECTA Scheduler Service Stopped.")
