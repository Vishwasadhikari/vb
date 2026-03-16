import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase


mongo_client: AsyncIOMotorClient | None = None


def init_mongo(uri: str) -> None:
    global mongo_client
    mongo_client = AsyncIOMotorClient(uri)


def close_mongo() -> None:
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None


def get_db() -> AsyncIOMotorDatabase:
    if not mongo_client:
        raise RuntimeError("MongoDB client not configured (DATABASE_URL missing?)")
    db_name = (os.getenv("MONGODB_DB_NAME") or "vibecoderdb").strip()
    return mongo_client.get_database(db_name)


async def get_users_collection() -> AsyncIOMotorCollection:
    db = get_db()
    name = (os.getenv("MONGODB_USERS_COLLECTION") or "users").strip()
    return db.get_collection(name)

