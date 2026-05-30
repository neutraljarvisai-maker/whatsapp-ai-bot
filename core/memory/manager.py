import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages VECTA's long-term and short-term memory with compression."""

    def compress_history(self, history_lines: List[str], max_lines: int = 20) -> str:
        """Compresses old conversation history to stay within context limits."""
        if len(history_lines) <= max_lines:
            return "\n".join(history_lines)

        logger.info(f"VECTA is compressing {len(history_lines)} turns of history.")

        # Keep the most recent 10 turns as full context
        recent = history_lines[-10:]
        # Summarize the older turns (Simple rule-based summarization for prototype)
        older = history_lines[:-10]
        summary = f"[System: Previous interaction summary: User and VECTA discussed {len(older)//2} topics earlier in the session.]"

        return summary + "\n" + "\n".join(recent)

    def record_learning(self, task: str, success: bool, feedback: str = ""):
        """Records a 'trace' of a task for future self-learning."""
        logger.info(f"VECTA recording learning trace: Task='{task}', Success={success}")
        # In a full implementation, this would save to a 'traces' table in Supabase
        pass

# Singleton
memory = MemoryManager()
