from vecta_os.services.database import db
from vecta_os.personality.base import PROFILE_COLUMNS
import logging

logger = logging.getLogger(__name__)

def load_profile(uid):
    try:
        query = f"SELECT {', '.join(PROFILE_COLUMNS)} FROM profile WHERE user_id=%s;"
        r = db.run_query(query, (uid,), fetch=True)
        if not r: return {}
        profile_data = {}
        for i, col_name in enumerate(PROFILE_COLUMNS):
            if i < len(r[0]) and r[0][i] is not None:
                profile_data[col_name] = r[0][i]
        return profile_data
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        return {}

def format_profile_for_llm(profile):
    if not profile: return "No profile data available."
    lines = []
    for k in PROFILE_COLUMNS:
        v = profile.get(k)
        if v and str(v).strip():
            lines.append(f"{k.replace('_', ' ').title()}: {v}")
    return "\n".join(lines) if lines else "No profile data available."
