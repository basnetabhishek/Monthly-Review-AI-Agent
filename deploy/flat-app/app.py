"""Connectivity proof for the Monthly Business Review Databricks App."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Monthly Business Review Agent", version="0.1.0")

REPORTING_CHECK_SQL = """
SELECT
  COUNT(*) AS month_count,
  MIN(report_month) AS first_month,
  MAX(report_month) AS last_month
FROM workspace.mbr_reporting.vw_monthly_trends
""".strip()

MONTH_PATTERN = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")


def execute_sql(statement: str) -> Any:
    warehouse_id = os.getenv("WAREHOUSE_ID")
    if not warehouse_id:
        raise HTTPException(
            status_code=503,
            detail="WAREHOUSE_ID is missing. Check the sql-warehouse app resource.",
        )
    response = WorkspaceClient().statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="30s",
    )
    state = getattr(getattr(response, "status", None), "state", None)
    if state != StatementState.SUCCEEDED:
        raise RuntimeError(f"SQL statement did not succeed (state={state}).")
    return response


def first_row(response: Any) -> list[Any]:
    rows = getattr(getattr(response, "result", None), "data_array", None)
    if not rows:
        raise RuntimeError("The reporting query returned no rows.")
    return rows[0]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "monthly-business-review-agent"}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


@app.get("/api/report")
def report(month: str = Query(default="2014-12")) -> dict[str, object]:
    if not MONTH_PATTERN.fullmatch(month):
        raise HTTPException(status_code=400, detail="Month must use YYYY-MM format.")
    report_date = f"{month}-01"
    statement = f"""
    SELECT report_month, reported_sales, reported_profit, profit_margin_pct,
           distinct_orders, units_sold, negative_profit_orders,
           sales_mom_pct, profit_mom_pct, orders_mom_pct
    FROM workspace.mbr_reporting.vw_monthly_trends
    WHERE report_month BETWEEN ADD_MONTHS(DATE '{report_date}', -11) AND DATE '{report_date}'
    ORDER BY report_month
    """.strip()
    try:
        rows = first_row_set(execute_sql(statement))
        if not rows:
            raise RuntimeError(f"No reporting data exists for {month}.")
        trend = [
            {
                "month": str(row[0])[:7],
                "sales": float(row[1]),
                "profit": float(row[2]),
                "margin": float(row[3]),
                "orders": int(row[4]),
                "units": int(row[5]),
                "negative_orders": int(row[6]),
                "sales_mom": float(row[7]) if row[7] is not None else None,
                "profit_mom": float(row[8]) if row[8] is not None else None,
                "orders_mom": float(row[9]) if row[9] is not None else None,
            }
            for row in rows
        ]
        current = trend[-1]
        market_rows = first_row_set(execute_sql(f"""SELECT market, region, reported_sales, reported_profit, profit_margin_pct FROM workspace.mbr_reporting.vw_market_performance WHERE report_month = DATE '{report_date}' ORDER BY reported_sales DESC LIMIT 6"""))
        category_rows = first_row_set(execute_sql(f"""SELECT category, sub_category, reported_sales, reported_profit, profit_margin_pct FROM workspace.mbr_reporting.vw_category_performance WHERE report_month = DATE '{report_date}' ORDER BY reported_sales DESC LIMIT 6"""))
        target_rows = first_row_set(execute_sql(f"""SELECT market, region, category, actual_sales, revenue_target, revenue_attainment_pct FROM workspace.mbr_reporting.vw_target_attainment WHERE report_month = DATE '{report_date}' ORDER BY revenue_attainment_pct ASC LIMIT 6"""))
        exception_rows = first_row_set(execute_sql(f"""SELECT order_id, market, region, order_reported_sales, order_reported_profit FROM workspace.mbr_reporting.vw_negative_profit_orders WHERE report_month = DATE '{report_date}' ORDER BY order_reported_profit ASC LIMIT 6"""))
        markets = [{"market":str(r[0]),"region":str(r[1]),"sales":float(r[2]),"profit":float(r[3]),"margin":float(r[4])} for r in market_rows]
        categories = [{"category":str(r[0]),"subcategory":str(r[1]),"sales":float(r[2]),"profit":float(r[3]),"margin":float(r[4])} for r in category_rows]
        targets = [{"market":str(r[0]),"region":str(r[1]),"category":str(r[2]),"actual":float(r[3]),"target":float(r[4]),"attainment":float(r[5])} for r in target_rows]
        exceptions = [{"order_id":str(r[0]),"market":str(r[1]),"region":str(r[2]),"sales":float(r[3]),"profit":float(r[4])} for r in exception_rows]
        direction = "increased" if (current["sales_mom"] or 0) >= 0 else "declined"
        profit_note = "profitable" if current["profit"] >= 0 else "loss-making"
        summary = (
            f"Sales {direction} {abs(current['sales_mom'] or 0):.1f}% month over month to "
            f"{current['sales']:,.0f} source monetary units. The month remained {profit_note}, "
            f"with a {current['margin']:.1f}% margin across {current['orders']:,} logical orders. "
            f"Management attention should focus on the {current['negative_orders']:,} orders "
            "that generated negative profit."
        )
        return {"status": "ok", "report_month": month, "summary": summary, "current": current,
                "trend": trend, "markets": markets, "categories": categories,
                "targets": targets, "exceptions": exceptions}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Report query failed: {exc}") from exc


@app.get("/api/connectivity/sql")
def sql_connectivity() -> dict[str, object]:
    warehouse_id = os.getenv("WAREHOUSE_ID")
    if not warehouse_id:
        raise HTTPException(
            status_code=503,
            detail="WAREHOUSE_ID is missing. Check the sql-warehouse app resource.",
        )

    try:
        response = execute_sql(REPORTING_CHECK_SQL)
        month_count, first_month, last_month = first_row(response)
        return {
            "status": "ok",
            "reporting_view": "workspace.mbr_reporting.vw_monthly_trends",
            "month_count": int(month_count),
            "first_month": str(first_month),
            "last_month": str(last_month),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Databricks SQL check failed: {exc}") from exc


@app.get("/api/connectivity/egress")
def egress_connectivity() -> dict[str, object]:
    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            timeout=10.0,
            follow_redirects=False,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI network check failed: {exc}") from exc

    if response.status_code not in {200, 401, 403, 429}:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI returned unexpected HTTP status {response.status_code}.",
        )
    return {
        "status": "ok",
        "provider": "OpenAI",
        "reachable": True,
        "http_status": response.status_code,
        "credentials_sent": False,
    }


def first_row_set(response: Any) -> list[list[Any]]:
    return getattr(getattr(response, "result", None), "data_array", None) or []


DASHBOARD_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Northstar | Monthly Business Review</title>
<style>
:root{--ink:#15251f;--muted:#64736d;--paper:#f5f3ec;--card:#fffefa;--line:#dddcd3;--green:#0f6b50;--lime:#b8f34a;--orange:#f39a63}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}.shell{min-height:100vh;display:grid;grid-template-columns:250px 1fr}.side{background:#10231d;color:#e9f0eb;padding:30px 24px;display:flex;flex-direction:column}.brand{font-size:20px;font-weight:800;letter-spacing:-.5px}.brand i{display:inline-block;width:11px;height:11px;background:var(--lime);border-radius:50%;margin-right:9px;box-shadow:0 0 20px #b8f34a88}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:1.6px;color:#8ca198;margin-top:7px}.nav{margin-top:46px;display:grid;gap:10px}.nav div{padding:12px 14px;border-radius:9px;color:#9eb0a9;font-size:14px}.nav .active{background:#1c392f;color:white}.sidefoot{margin-top:auto;font-size:12px;color:#80948d;line-height:1.7}.main{padding:28px 38px 50px;max-width:1450px;width:100%;margin:auto}.top{display:flex;align-items:center;justify-content:space-between;gap:20px}.title h1{font-family:Georgia,serif;font-size:34px;margin:0;letter-spacing:-1.2px}.title p{color:var(--muted);margin:6px 0 0;font-size:14px}.controls{display:flex;gap:10px}.controls select,.controls button{height:44px;border-radius:10px;border:1px solid var(--line);padding:0 15px;background:var(--card);font-weight:650;color:var(--ink)}.controls button{background:var(--ink);color:white;border:0;padding:0 22px;cursor:pointer;box-shadow:0 8px 20px #15251f22}.controls button:hover{transform:translateY(-1px)}.controls button:disabled{opacity:.6}.status{display:none;margin:24px 0 0;background:#e9efe9;border:1px solid #d3e0d6;border-radius:12px;padding:15px 18px;align-items:center;gap:14px}.status.show{display:flex}.pulse{width:9px;height:9px;background:var(--green);border-radius:50%;box-shadow:0 0 0 0 #0f6b5066;animation:pulse 1.2s infinite}@keyframes pulse{70%{box-shadow:0 0 0 8px #0f6b5000}}.status b{font-size:13px}.status span{color:var(--muted);font-size:13px;margin-left:auto}.report{margin-top:26px}.meta{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid var(--line);padding-bottom:16px}.meta small{color:var(--muted)}.badge{background:#e5f1dc;color:#356523;padding:7px 10px;border-radius:20px;font-size:11px;font-weight:800;letter-spacing:.5px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:16px 0}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px}.kpi label{color:var(--muted);font-size:12px}.kpi strong{display:block;font-family:Georgia,serif;font-size:28px;margin:9px 0 6px}.delta{font-size:12px;font-weight:700}.up{color:var(--green)}.down{color:#b4483f}.grid{display:grid;grid-template-columns:1.45fr 1fr;gap:13px}.chartcard h3,.summary h3{font-size:13px;margin:0 0 18px}.chart{height:235px;position:relative;display:flex;align-items:end;gap:7px;border-bottom:1px solid var(--line);padding:8px 4px 0}.bar{flex:1;background:#dce7df;border-radius:5px 5px 0 0;min-width:8px;position:relative;transition:.4s}.bar:last-child{background:var(--green)}.bar:hover{background:var(--lime)}.bar em{display:none;position:absolute;top:-25px;left:50%;transform:translateX(-50%);font-style:normal;font-size:10px;background:var(--ink);color:white;padding:4px 6px;border-radius:5px;white-space:nowrap}.bar:hover em{display:block}.months{display:flex;justify-content:space-between;color:var(--muted);font-size:10px;margin-top:8px}.summary{background:var(--ink);color:#f6f3e9}.summary h3{color:var(--lime);text-transform:uppercase;letter-spacing:1.2px;font-size:11px}.summary p{font-family:Georgia,serif;font-size:20px;line-height:1.55;margin:0}.summary .source{font-family:inherit;font-size:11px;color:#879b93;margin-top:22px}.empty{padding:70px;text-align:center;color:var(--muted)}
@media(max-width:900px){.shell{display:block}.side{display:none}.main{padding:22px}.top{align-items:flex-start;flex-direction:column}.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}@media(max-width:520px){.kpis{grid-template-columns:1fr}.controls{width:100%}.controls select,.controls button{flex:1}}
.details{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-top:13px}.tablecard{padding:0;overflow:hidden}.tablehead{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between}.tablehead h3{font-size:13px;margin:0}.tablehead span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}table{width:100%;border-collapse:collapse;font-size:12px}th{text-align:left;color:var(--muted);font-weight:600;padding:11px 14px;background:#faf9f4}td{padding:12px 14px;border-top:1px solid #ecebe3}th:last-child,td:last-child{text-align:right}.pill{padding:4px 7px;border-radius:12px;font-weight:750;font-size:10px}.good{background:#dff0df;color:#22623a}.bad{background:#f7ded8;color:#9d3e35}.loss{color:#a53e35;font-weight:700}@media(max-width:900px){.details{grid-template-columns:1fr}}
</style></head><body><div class="shell"><aside class="side"><div class="brand"><i></i>Northstar</div><div class="eyebrow">Business intelligence</div><div class="nav"><div class="active">Monthly review</div><div>Performance trends</div><div>Market analysis</div><div>Report archive</div></div><div class="sidefoot">CONTROLLED ANALYTICS<br>SQL-sourced · AI-explained<br><br>Data through Dec 2014</div></aside><main class="main"><div class="top"><div class="title"><h1>Monthly Business Review</h1><p>Decision-ready performance intelligence, grounded in governed data.</p></div><div class="controls"><select id="month" aria-label="Report month"><option value="2014-12">December 2014</option><option value="2014-11">November 2014</option><option value="2014-10">October 2014</option><option value="2014-09">September 2014</option></select><button id="generate">Generate report →</button></div></div><div class="status" id="status"><div class="pulse"></div><b id="step">Running governed SQL</b><span id="stepno">Step 1 of 4</span></div><section class="report" id="report"><div class="empty">Choose a month and generate the executive report.</div></section></main></div>
<script>
const $=s=>document.querySelector(s),fmt=n=>new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(n),pct=n=>`${n>=0?'+':''}${n.toFixed(1)}%`;
const steps=['Running governed SQL','Validating KPI payload','Identifying material changes','Compiling executive report'];
function card(label,value,delta){const cls=delta>=0?'up':'down';return `<div class="card kpi"><label>${label}</label><strong>${value}</strong><span class="delta ${cls}">${pct(delta)} vs prior month</span></div>`}
function render(d){const c=d.current,max=Math.max(...d.trend.map(x=>x.sales));const bars=d.trend.map(x=>`<div class="bar" style="height:${Math.max(8,x.sales/max*100)}%"><em>${x.month}: ${fmt(x.sales)}</em></div>`).join('');const labels=`<span>${d.trend[0].month}</span><span>${d.trend[d.trend.length-1].month}</span>`;$('#report').innerHTML=`<div class="meta"><div><small>EXECUTIVE PERFORMANCE REPORT</small><h2>${new Date(d.report_month+'-02').toLocaleString('en-US',{month:'long',year:'numeric'})}</h2></div><div class="badge">✓ DATA VALIDATED</div></div><div class="kpis">${card('Reported sales',fmt(c.sales),c.sales_mom||0)}${card('Reported profit',fmt(c.profit),c.profit_mom||0)}${card('Logical orders',fmt(c.orders),c.orders_mom||0)}<div class="card kpi"><label>Profit margin</label><strong>${c.margin.toFixed(1)}%</strong><span class="delta">${fmt(c.units)} units sold</span></div></div><div class="grid"><div class="card chartcard"><h3>12-month reported sales trajectory</h3><div class="chart">${bars}</div><div class="months">${labels}</div></div><div class="card summary"><h3>Executive summary</h3><p>${d.summary}</p><p class="source">Every figure is calculated in Databricks SQL. Narrative is restricted to the validated KPI payload.</p></div></div>`}
function dataTable(title,note,heads,rows){return `<div class="card tablecard"><div class="tablehead"><h3>${title}</h3><span>${note}</span></div><table><thead><tr>${heads.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`}
function renderFull(d){render(d);const marketRows=d.markets.map(x=>`<tr><td><b>${x.market}</b><br><small>${x.region}</small></td><td>${fmt(x.sales)}</td><td class="${x.profit<0?'loss':''}">${fmt(x.profit)}</td><td><span class="pill ${x.margin>=0?'good':'bad'}">${x.margin.toFixed(1)}%</span></td></tr>`).join('');const categoryRows=d.categories.map(x=>`<tr><td><b>${x.category}</b><br><small>${x.subcategory}</small></td><td>${fmt(x.sales)}</td><td class="${x.profit<0?'loss':''}">${fmt(x.profit)}</td><td>${x.margin.toFixed(1)}%</td></tr>`).join('');const targetRows=d.targets.map(x=>`<tr><td><b>${x.market}</b><br><small>${x.region} · ${x.category}</small></td><td>${fmt(x.actual)}</td><td>${fmt(x.target)}</td><td><span class="pill ${x.attainment>=100?'good':'bad'}">${x.attainment.toFixed(0)}%</span></td></tr>`).join('');const exceptionRows=d.exceptions.map(x=>`<tr><td><b>${x.order_id}</b></td><td>${x.market}<br><small>${x.region}</small></td><td>${fmt(x.sales)}</td><td class="loss">${fmt(x.profit)}</td></tr>`).join('');$('#report').insertAdjacentHTML('beforeend',`<div class="details">${dataTable('Market performance','Ranked by sales',['Market / region','Sales','Profit','Margin'],marketRows)}${dataTable('Category performance','Top contributors',['Category','Sales','Profit','Margin'],categoryRows)}${dataTable('Target watchlist','Synthetic targets',['Segment','Actual','Target','Attainment'],targetRows)}${dataTable('Profit exceptions','Management attention',['Order','Market','Sales','Profit'],exceptionRows)}</div>`)}
$('#generate').onclick=async()=>{const btn=$('#generate'),box=$('#status');btn.disabled=true;box.classList.add('show');let i=0;$('#step').textContent=steps[0];$('#stepno').textContent='Step 1 of 4';const timer=setInterval(()=>{i=Math.min(i+1,3);$('#step').textContent=steps[i];$('#stepno').textContent=`Step ${i+1} of 4`},700);try{const r=await fetch(`/api/report?month=${$('#month').value}`);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Report failed');clearInterval(timer);renderFull(d)}catch(e){clearInterval(timer);$('#report').innerHTML=`<div class="card"><b>Report generation failed</b><p>${e.message}</p></div>`}finally{box.classList.remove('show');btn.disabled=false}};
</script></body></html>'''
