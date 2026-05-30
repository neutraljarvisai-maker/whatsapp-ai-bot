import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from services.database import run_query

logger = logging.getLogger(__name__)

class VectaScheduler:
    def __init__(self, poll_interval: int = 60):
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"VECTA Scheduler started (poll interval: {self.poll_interval}s)")

    def stop(self):
        self._stop_event.set()
        if self._thread: self._thread.join()

    def _poll_loop(self):
        while not self._stop_event.is_set():
            try:
                self.check_and_execute_tasks()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(self.poll_interval)

    def check_and_execute_tasks(self):
        """Checks for scheduled tasks in the database."""
        now = datetime.now(timezone.utc).isoformat()
        # Find tasks where next_run <= now
        # For prototype, we'll simulate one daily task
        if datetime.now().hour == 8 and datetime.now().minute == 0:
            logger.info("Triggering Morning Digest...")
            self.trigger_morning_digest()

    def trigger_morning_digest(self):
        """Simulates the proactive morning briefing."""
        # This would call the brain to generate a digest and send it to the client
        logger.info("VECTA is preparing your morning briefing.")

# Singleton
scheduler = VectaScheduler()
