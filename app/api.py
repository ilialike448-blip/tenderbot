import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="TenderBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/tenders")
def list_tenders(limit: int = 20, analyzed_only: bool = False):
    from app.database import get_tenders
    return get_tenders(limit=limit, only_analyzed=analyzed_only)


@app.get("/api/status")
def get_status():
    from app.database import count_tenders
    return count_tenders()


@app.post("/api/parse")
async def trigger_parse():
    from parsers.eis_parser import parse_eis
    from app.database import save_tender
    try:
        tenders = await parse_eis(pages=3)
        new_count = sum(1 for t in tenders if save_tender(t))
        return {"found": len(tenders), "new": new_count}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/analyze")
def trigger_analyze():
    from app.database import get_unanalyzed, save_analysis
    from services.claude_agent import triage_tender, analyze_tender

    tenders = get_unanalyzed(limit=20)
    analyzed = 0
    for t in tenders:
        if triage_tender(t["title"], t["nmc"]):
            try:
                result = analyze_tender(
                    t["number"], t["title"], t["nmc"],
                    t["customer"], t["region"],
                )
                save_analysis(result)
                analyzed += 1
            except Exception:
                continue
    return {"analyzed": analyzed}


@app.get("/api/export/excel")
def export_excel():
    from export.to_excel import generate_excel
    import tempfile, os
    from datetime import datetime
    from fastapi.responses import Response

    xlsx_bytes = generate_excel()
    filename = f"tenders_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
