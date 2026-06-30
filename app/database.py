import sqlite3
import os
from datetime import datetime
from typing import Optional
from app.models import Tender, AnalysisResult

DB_PATH = os.getenv("DB_PATH", "./tenderbot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    print("⏳ 1/1: Инициализирую базу данных…", flush=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            number TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            nmc REAL NOT NULL,
            customer TEXT,
            region TEXT,
            delivery_deadline TEXT,
            publish_date TEXT,
            end_date TEXT,
            url TEXT,
            status TEXT DEFAULT 'new',
            cost_estimate REAL,
            margin_percent REAL,
            rating TEXT,
            analysis_text TEXT,
            analyzed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ База данных готова", flush=True)


def save_tender(tender: Tender) -> bool:
    """Сохраняет тендер. Возвращает True если новый, False если уже был."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO tenders
                (number, title, nmc, customer, region,
                 delivery_deadline, publish_date, end_date, url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tender.number, tender.title, tender.nmc, tender.customer,
            tender.region, tender.delivery_deadline, tender.publish_date,
            tender.end_date, tender.url, tender.status,
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def save_analysis(result: AnalysisResult):
    conn = get_connection()
    conn.execute("""
        UPDATE tenders SET
            cost_estimate = ?,
            margin_percent = ?,
            rating = ?,
            analysis_text = ?,
            analyzed_at = ?,
            status = 'analyzed'
        WHERE number = ?
    """, (
        result.cost_estimate, result.margin_percent, result.rating,
        result.summary, datetime.now().isoformat(), result.tender_number,
    ))
    conn.commit()
    conn.close()


def get_tenders(limit: int = 20, only_analyzed: bool = False) -> list[dict]:
    conn = get_connection()
    if only_analyzed:
        rows = conn.execute(
            "SELECT * FROM tenders WHERE status = 'analyzed' ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tenders ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unanalyzed(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tenders WHERE status = 'new' ORDER BY nmc DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_tenders() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM tenders").fetchone()[0]
    analyzed = conn.execute(
        "SELECT COUNT(*) FROM tenders WHERE status = 'analyzed'"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "analyzed": analyzed}
