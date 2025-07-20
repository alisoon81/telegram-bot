import asyncpg

DATABASE_URL = "postgresql://neondb_owner:npg_gtFu06zhUKJj@ep-mute-hill-afp0p6oi-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    msg_id TEXT PRIMARY KEY,
                    translated TEXT NOT NULL
                )
            ''')

    async def save_translation(self, msg_id: str, translated: str):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO translations (msg_id, translated)
                VALUES ($1, $2)
                ON CONFLICT (msg_id) DO UPDATE SET translated = EXCLUDED.translated
            ''', msg_id, translated)

    async def get_translation(self, msg_id: str):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT translated FROM translations WHERE msg_id = $1', msg_id)
            return row['translated'] if row else None

db = Database()
