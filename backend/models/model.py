import sys
from pathlib import Path

# Adds project root directory (PostRaid) to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from backend.database.db import pool

def run_test_query():
    """Executes a test query against PostgreSQL and returns the fetched row."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    NOW() AS current_time, 
                    VERSION() AS postgres_version;
            """)
            result = cur.fetchone()
            return result

data = run_test_query()
print(data)