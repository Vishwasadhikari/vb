from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from .auth import require_user_email
from .db import get_db


router = APIRouter(prefix="/projects", tags=["projects"])


async def get_projects_collection() -> AsyncIOMotorCollection:
    db = get_db()
    return db.get_collection("projects")


def _serialize_id(obj: dict) -> dict:
    out = dict(obj)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    return out


@router.get("")
async def list_projects(
    authorization: str | None = Header(default=None),
    coll: AsyncIOMotorCollection = Depends(get_projects_collection),
) -> list[dict]:
    email = await require_user_email(authorization or "")
    cursor = coll.find({"user_email": email}).sort("created_at", -1)
    return [_serialize_id(doc) async for doc in cursor]


@router.post("")
async def create_project(
    body: dict,
    authorization: str | None = Header(default=None),
    coll: AsyncIOMotorCollection = Depends(get_projects_collection),
) -> dict:
    email = await require_user_email(authorization or "")
    name = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required.")
    doc = {
        "user_email": email,
        "name": name,
        "description": description,
        "created_at": datetime.now(timezone.utc),
    }
    res = await coll.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _serialize_id(doc)


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    authorization: str | None = Header(default=None),
    coll: AsyncIOMotorCollection = Depends(get_projects_collection),
) -> dict:
    email = await require_user_email(authorization or "")
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project id.")
    doc = await coll.find_one({"_id": oid, "user_email": email})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _serialize_id(doc)

