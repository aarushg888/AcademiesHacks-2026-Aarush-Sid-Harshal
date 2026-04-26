
import os
from rag import ingest_investor, INVESTORS

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def main():
    print("DecisionDNA — Investor Data Ingestion\n" + "=" * 40)
    for investor in INVESTORS:
        path = os.path.join(DATA_DIR, f"{investor}.txt")
        if not os.path.exists(path):
            print(f"[SKIP] No data file found for '{investor}' at {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        count = ingest_investor(investor, text)
        print(f"[OK]   {investor.title():10s} — {count} chunks ingested")

    print("\nAll investors ingested.")
    print("Run:  streamlit run app.py")


if __name__ == "__main__":
    main()
