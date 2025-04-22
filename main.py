from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os
import difflib
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReportRequest(BaseModel):
    chain_name: str
    start_date: str
    end_date: str
    organization: str
    fee_override: Optional[float] = None
    include_gustazos: bool = True
    include_giftcards: bool = True
    include_referrals: bool = False

def load_chain_mapping(file_path="chains-2025-04-19.csv"):
    chain_map = {}
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        merchant = row["Name"].strip().lower()
        chain = row["Name"].split()[0].lower()
        chain_map[merchant] = chain
    return chain_map

def match_chain_name(merchant_name, mapping):
    merchant_name = merchant_name.lower()
    if merchant_name in mapping:
        return mapping[merchant_name]
    close_matches = difflib.get_close_matches(merchant_name, mapping.keys(), n=1, cutoff=0.6)
    if close_matches:
        return mapping[close_matches[0]]
    return merchant_name.split()[0]

def load_and_summarize_transactions(chain_name, start_date, end_date, organization):
    df = pd.read_parquet("clean_transactions.parquet")

    chain_map = load_chain_mapping()
    df["Matched Chain"] = df["Merchant"].apply(lambda x: match_chain_name(str(x), chain_map))

    df = df[
        (df["Matched Chain"].str.lower() == chain_name.lower()) &
        (df["Organization"].str.lower() == organization.lower())
    ]

    df["Created at"] = pd.to_datetime(df["Created at"], errors='coerce')
    mask = (df["Created at"] >= pd.to_datetime(start_date)) & (df["Created at"] <= pd.to_datetime(end_date))
    df = df[mask]

    total_tx = len(df)
    total_users = df["User"].nunique()
    total_gmv = df["Gross total cents"].sum() / 100

    return {
        "total_transactions": total_tx,
        "total_users": total_users,
        "total_gmv": round(total_gmv, 2)
    }

@app.post("/create-report")
def create_report(req: ReportRequest):
    try:
        metrics = load_and_summarize_transactions(
            chain_name=req.chain_name,
            start_date=req.start_date,
            end_date=req.end_date,
            organization=req.organization
        )

        filename = f"report_{req.chain_name.replace(' ', '_').lower()}_{req.start_date}_to_{req.end_date}.html"
        filepath = os.path.join("reports", filename)
        os.makedirs("reports", exist_ok=True)

        html = f"""
        <html>
        <head><title>{req.chain_name} Report</title></head>
        <body style='font-family:sans-serif;padding:40px;'>
            <h1>📊 GustitosGo Merchant Report</h1>
            <p><strong>Chain:</strong> {req.chain_name}</p>
            <p><strong>Organization:</strong> {req.organization}</p>
            <p><strong>Date Range:</strong> {req.start_date} → {req.end_date}</p>
            <p><strong>Transactions:</strong> {metrics['total_transactions']}</p>
            <p><strong>Unique Users:</strong> {metrics['total_users']}</p>
            <p><strong>Total GMV:</strong> ${metrics['total_gmv']:,.2f}</p>
            <hr>
            <p>Gustazos: {"✅" if req.include_gustazos else "❌"}</p>
            <p>Gift Cards: {"✅" if req.include_giftcards else "❌"}</p>
            <p>Referrals: {"✅" if req.include_referrals else "❌"}</p>
        </body>
        </html>
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return {
            "success": True,
            "report_url": f"/reports/{filename}"
        }

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return {"success": False, "error": str(e)}

from fastapi.staticfiles import StaticFiles
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

@app.get("/")
def read_root():
    return {"message": "✅ GustitosGo backend is running."}