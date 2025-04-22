- GustitosGo is a FastAPI + React project that generates merchant performance reports for a coalition rewards program. It's being developed to support internal and merchant-facing analytics.

- Core Features (already implemented):
  - FastAPI backend accepting POST requests with parameters like chain_name, organization, date range
  - Uses cleaned Parquet transaction file and chain mapping CSV
  - Filters transactions by date, merchant chain, and organization
  - Summarizes total revenue (GMV)
  - Generates HTML reports saved to /reports/ directory
  - Fully CORS-enabled for local frontend access
  - React frontend with form inputs and download functionality

- Next features to implement:
  1. PDF Output - Convert HTML reports to downloadable PDFs
  2. Report History - Store metadata for report recall
  3. Frontend Enhancements - Display report status and history
  4. Admin Dashboard - View/search all reports
  5. Optional Features - Email reports, charts, AI summaries

- Key files: main.py (FastAPI backend), clean_transactions.parquet (dataset), chains CSV, reports directory, frontend React components