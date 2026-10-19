from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from dotenv import load_dotenv
import os
load_dotenv()

# Format: postgresql://<username>:<password>@<host>:<port>/<database_name>
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Taki2399@localhost:5432/postraid")

# Create a connection pool; kwargs like dict_row return results as key-value dictionaries
pool = ConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=10, kwargs={"row_factory": dict_row})

def get_db():
    """Dependency that yields a database connection from the pool."""
    with pool.connection() as conn:
        yield conn