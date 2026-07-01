import json
from datetime import datetime
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from portal.auth import require_approved
from portal.database import get_db

router = APIRouter()


def _fmt_task(r) -> dict:
    d = dict(r)
    try:
        d["co_assignees"] = json.loads(d.get("co_assignees") or "[]")
    except Exception:
        d["co_assignees"] = []
    return d


@router.get("/tasks")
async def list_tasks(
    status: str = Query("all", regex="^(all|new|in_work|review|done)$"),
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    role = user["role"]
    uid = user["telegram_id"]

    if status == "all":
        where_status = ""
        params: list = []
    else:
        where_status = "AND t.status = ?"
        params = [status]

    # members see only their own tasks; lead/admin see all
    if role == "member":
        where_role = "AND t.assignee_id = ?"
        params.append(uid)
    else:
        where_role = ""

    sql = f"""
        SELECT t.*,
               u.first_name  AS assignee_first,
               u.last_name   AS assignee_last,
               u.color       AS assignee_color,
               ten.name      AS tender_name
        FROM tasks t
        LEFT JOIN users u  ON t.assignee_id = u.telegram_id
        LEFT JOIN tenders ten ON t.tender_number = ten.external_number
        WHERE 1=1 {where_status} {where_role}
        ORDER BY
            CASE t.status WHEN 'in_work' THEN 1 WHEN 'review' THEN 2
                          WHEN 'new' THEN 3 WHEN 'done' THEN 4 ELSE 5 END,
            t.due_date ASC NULLS LAST
    """
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
    return [_fmt_task(r) for r in rows]


class CreateTask(BaseModel):
    title: str
    assignee_id: Optional[int] = None
    co_assignees: list[int] = []
    tender_number: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "med"
    time_estimate_min: Optional[int] = None


@router.post("/tasks")
async def create_task(
    body: CreateTask,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    assignee = body.assignee_id or user["telegram_id"]

    cur = await db.execute(
        """INSERT INTO tasks (title, status, priority, assignee_id, co_assignees,
                              tender_number, due_date, time_estimate_min, created_at)
           VALUES (?, 'new', ?, ?, ?, ?, ?, ?, ?)""",
        (body.title, body.priority, assignee,
         json.dumps(body.co_assignees), body.tender_number,
         body.due_date, body.time_estimate_min, now),
    )
    await db.commit()
    task_id = cur.lastrowid

    async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as c:
        row = await c.fetchone()
    return _fmt_task(row)


class UpdateTask(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[str] = None
    progress_pct: Optional[int] = None
    time_spent_min: Optional[int] = None
    time_estimate_min: Optional[int] = None


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    body: UpdateTask,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, detail={"error": "Task not found", "code": 404})

    task = dict(row)
    # members can only edit their own tasks
    if user["role"] == "member" and task["assignee_id"] != user["telegram_id"]:
        raise HTTPException(403, detail={"error": "Cannot edit others' tasks", "code": 403})

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return _fmt_task(row)

    if updates.get("status") == "done" and task["status"] != "done":
        updates["closed_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        updates["progress_pct"] = 100

    fields = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]
    await db.execute(f"UPDATE tasks SET {fields} WHERE id = ?", values)
    await db.commit()

    async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cur:
        row = await cur.fetchone()
    return _fmt_task(row)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if user["role"] not in ("admin", "lead"):
        raise HTTPException(403, detail={"error": "Only lead/admin can delete tasks", "code": 403})
    await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    await db.commit()
    return {"ok": True}
