import aiosqlite
from portal.config import DB_PATH


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        yield db


async def init_portal_schema() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT NOT NULL,
            last_name   TEXT,
            role        TEXT NOT NULL DEFAULT 'member',
            status      TEXT NOT NULL DEFAULT 'pending',
            position    TEXT,
            color       TEXT DEFAULT '#388bfd',
            created_at  TEXT NOT NULL,
            approved_by INTEGER,
            approved_at TEXT,
            last_seen   TEXT
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            status           TEXT NOT NULL DEFAULT 'new',
            priority         TEXT DEFAULT 'med',
            assignee_id      INTEGER,
            co_assignees     TEXT DEFAULT '[]',
            tender_number    TEXT,
            due_date         TEXT,
            progress_pct     INTEGER DEFAULT 0,
            time_spent_min   INTEGER DEFAULT 0,
            time_estimate_min INTEGER,
            created_at       TEXT NOT NULL,
            closed_at        TEXT,
            FOREIGN KEY (assignee_id) REFERENCES users(telegram_id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            type       TEXT NOT NULL,
            text       TEXT NOT NULL,
            is_read    INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            link       TEXT,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_tender   ON tasks(tender_number);
        CREATE INDEX IF NOT EXISTS idx_notif_user     ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notif_read     ON notifications(is_read);
        """)

        # Extend existing tenders table with portal-specific columns (safe migration)
        portal_cols = [
            ("portal_status", "TEXT DEFAULT 'free'"),
            ("assigned_to",   "INTEGER"),
            ("taken_at",      "TEXT"),
            ("taken_by_name", "TEXT"),
            ("law",           "TEXT DEFAULT '44-ФЗ'"),
            ("delivery_days", "INTEGER"),
            ("federal_district", "TEXT"),
            ("cert_requirements", "TEXT"),
            ("typical_participants", "INTEGER"),
        ]
        for col, defn in portal_cols:
            try:
                await db.execute(f"ALTER TABLE tenders ADD COLUMN {col} {defn}")
            except Exception:
                pass  # column already exists

        await db.commit()
