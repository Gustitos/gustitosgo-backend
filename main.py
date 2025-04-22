from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os
import difflib
import time
import uuid

app = FastAPI()

# Allow CORS for all origins (limit this in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the reports folder exists
os.makedirs("reports", exist_ok=True)

# Define file paths
TRANSACTION_FILE = "clean_transactions.parquet"
CHAIN_MAP_FILE = "chains-2025-04-19.csv"

# Function to safely load data files with fallback
def load_transaction_data():
    try:
        if os.path.exists(TRANSACTION_FILE):
            return pd.read_parquet(TRANSACTION_FILE)
        else:
            # Fallback - create dummy data if file doesn't exist
            print(f"Warning: {TRANSACTION_FILE} not found. Creating dummy data.")
            return pd.DataFrame({
                "Created at": pd.date_range(start="2024-01-01", periods=100),
                "Merchant": ["Test Merchant " + str(i % 10) for i in range(100)],
                "Gross total cents": [i * 100 for i in range(100)],
                "Organization": ["Org " + str(i % 5) for i in range(100)]
            })
    except Exception as e:
        print(f"Error loading transaction data: {e}")
        # Return minimal dummy data on error
        return pd.DataFrame({
            "Created at": pd.date_range(start="2024-01-01", periods=10),
            "Merchant": ["Error Fallback Merchant"] * 10,
            "Gross total cents": [1000] * 10,
            "Organization": ["Error Fallback Org"] * 10
        })

def load_chain_map():
    try:
        if os.path.exists(CHAIN_MAP_FILE):
            return pd.read_csv(CHAIN_MAP_FILE)
        else:
            # Fallback - create dummy data if file doesn't exist
            print(f"Warning: {CHAIN_MAP_FILE} not found. Creating dummy data.")
            chains = ["ChainA", "ChainB", "ChainC", "Test Merchant 1", "Test Merchant 2"]
            return pd.DataFrame({
                "merchant_name": chains,
                "chain": chains
            })
    except Exception as e:
        print(f"Error loading chain map: {e}")
        # Return minimal dummy data on error
        return pd.DataFrame({
            "merchant_name": ["Fallback Merchant"],
            "chain": ["Fallback Chain"]
        })

# Load data at startup
transactions_df = load_transaction_data()
chain_map_df = load_chain_map()

# Create lookup from merchant name to chain (exact and fuzzy)
chain_lookup = {}
merchant_names = list(chain_map_df['merchant_name'].unique())
for _, row in chain_map_df.iterrows():
    merchant_name = row['merchant_name']
    chain = row['chain']
    chain_lookup[merchant_name.lower()] = chain

def resolve_chain_name(chain_query):
    # Try exact match
    exact = [v for k, v in chain_lookup.items() if k == chain_query.lower()]
    if exact:
        return exact[0]
    # Try fuzzy
    matches = difflib.get_close_matches(chain_query.lower(), merchant_names, n=1, cutoff=0.8)
    if matches:
        return chain_lookup.get(matches[0].lower())
    return chain_query  # fallback

class ReportRequest(BaseModel):
    chain_name: str
    start_date: str
    end_date: str
    organization: Optional[str] = None
    fee_override: Optional[float] = None
    include_gustazos: bool = True
    include_giftcards: bool = True
    include_referrals: bool = False

@app.get("/")
def read_root():
    return {"message": "✅ GustitosGo backend is running successfully"}

@app.get("/healthz")
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "timestamp": time.time()}

def load_and_summarize_transactions(chain_name, start_date, end_date, organization=None):
    # Match chain name
    resolved_chain = resolve_chain_name(chain_name)
    df = transactions_df.copy()
    
    # Ensure datetime format
    if not pd.api.types.is_datetime64_dtype(df["Created at"]):
        df["Created at"] = pd.to_datetime(df["Created at"])
    
    # Filter data
    df = df[
        df["Created at"].between(start_date, end_date)
        & (df["Merchant"].str.lower().str.contains(resolved_chain.lower()))
    ]
    
    if organization:
        df = df[df["Organization"].str.lower() == organization.lower()]
    
    return {
        "transaction_count": len(df),
        "total_gross": df["Gross total cents"].sum() / 100,
        "matching_chain": resolved_chain
    }

@app.post("/create-report")
def create_report(req: ReportRequest):
    try:
        metrics = load_and_summarize_transactions(
            req.chain_name,
            req.start_date,
            req.end_date,
            organization=req.organization,
        )
        
        # Generate unique file name to avoid collisions
        report_id = uuid.uuid4().hex[:8]
        file_name = f"report_{req.chain_name.lower().replace(' ', '_')}_{req.start_date}_to_{req.end_date}_{report_id}.html"
        file_path = f"reports/{file_name}"

        html = f"""
        <html>
        <head>
            <title>GustitosGo Merchant Report</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #3a6ea5; }}
                .metrics {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .metric-group {{ margin-bottom: 20px; }}
                .footer {{ margin-top: 40px; font-size: 0.8em; color: #6c757d; text-align: center; }}
            </style>
        </head>
        <body>
            <h1>📊 GustitosGo Merchant Report</h1>
            
            <div class="metrics">
                <div class="metric-group">
                    <p><strong>Chain:</strong> {metrics['matching_chain']}</p>
                    <p><strong>Organization:</strong> {req.organization or "N/A"}</p>
                    <p><strong>Date Range:</strong> {req.start_date} → {req.end_date}</p>
                    <p><strong>Fee Override:</strong> {req.fee_override or "Default"}</p>
                </div>
                
                <div class="metric-group">
                    <p><strong>Transactions:</strong> {metrics['transaction_count']}</p>
                    <p><strong>Gross Volume:</strong> ${metrics['total_gross']:.2f}</p>
                </div>
                
                <hr>
                
                <div class="metric-group">
                    <p><strong>Modules Enabled:</strong></p>
                    <ul>
                        {"<li>✅ Gustazos</li>" if req.include_gustazos else "<li>❌ Gustazos</li>"}
                        {"<li>✅ Gift Cards</li>" if req.include_giftcards else "<li>❌ Gift Cards</li>"}
                        {"<li>✅ Referrals</li>" if req.include_referrals else "<li>❌ Referrals</li>"}
                    </ul>
                </div>
            </div>
            
            <p>📌 This report was automatically generated based on transaction data.</p>
            
            <div class="footer">
                <p>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>GustitosGo © {pd.Timestamp.now().year}</p>
            </div>
        </body>
        </html>
        """
        
        with open(file_path, "w") as f:
            f.write(html)

        # Create the full URL with the Render service domain
        base_url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:10000")
        report_url = f"{base_url}/reports/{file_name}"
        
        return {
            "success": True,
            "report_url": report_url
        }
    except Exception as e:
        print(f"Error creating report: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/reports/{file_name}")
def get_report(file_name: str):
    file_path = f"reports/{file_name}"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='text/html')
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Report not found"}
        )

# Mount reports directory for static file serving
app.mount("/reports", StaticFiles(directory="reports"), name="reports")