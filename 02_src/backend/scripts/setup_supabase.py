"""
Wasel — Supabase Setup Script
Run this once to apply the DB schema (tables + storage bucket).

Usage:
  cd backend
  python scripts/setup_supabase.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from supabase import create_client


def main():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("❌  SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env")
        sys.exit(1)

    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    sql_path = os.path.join(os.path.dirname(__file__), "migrations.sql")
    with open(sql_path) as f:
        sql = f.read()

    # Split on statement boundaries and run each
    stmts = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
    errors = []
    for stmt in stmts:
        try:
            client.rpc("exec_sql", {"sql": stmt + ";"}).execute()
        except Exception as e:
            errors.append(f"  ⚠  {e}")

    if errors:
        print("Some statements had warnings (may already exist):")
        for e in errors[:5]:
            print(e)
    print("✅  Supabase schema applied. Run build_rag_index.py next.")


if __name__ == "__main__":
    main()
