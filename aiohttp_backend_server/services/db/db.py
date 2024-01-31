import asyncpg
from aiohttp.web_app import Application
from asyncpg.pool import Pool

DB_KEY = 'database'

async def create_db_pool(app: Application,
                         host: str = 'localhost',
                         port: int = 5432,
                         user: str = 'postgres',
                         password: str = 'password',
                         db: str = 'test'):
    pool: Pool = await asyncpg.create_pool(host=host,
                                           port=port,
                                           user=user,
                                           password=password,
                                           database=db,
                                           min_size=6,
                                           max_size=6)
    app[DB_KEY] = pool

async def destroy_db_pool(app: Application):
    pool: Pool = app[DB_KEY]
    await pool.close()