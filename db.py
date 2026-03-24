import json
import os
import sqlite3

DATASET_PATH = "dataset"

def load_jsonl(folder_name):
    folder_path = os.path.join(DATASET_PATH, folder_name)
    if not os.path.isdir(folder_path):
        return []
    for f in os.listdir(folder_path):
        if f.endswith(".jsonl"):
            records = []
            with open(os.path.join(folder_path, f), "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            return records
    return []

def flatten(record):
    """Flatten nested dicts like creationTime: {hours, minutes, seconds}"""
    flat = {}
    for k, v in record.items():
        if isinstance(v, dict):
            flat[k] = str(v)
        else:
            flat[k] = v
    return flat

def ingest():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    tables = [
        "billing_document_cancellations",
        "billing_document_headers",
        "billing_document_items",
        "business_partner_addresses",
        "business_partners",
        "customer_company_assignments",
        "customer_sales_area_assignments",
        "journal_entry_items_accounts_receivable",
        "outbound_delivery_headers",
        "outbound_delivery_items",
        "payments_accounts_receivable",
        "plants",
        "product_descriptions",
        "product_plants",
        "product_storage_locations",
        "products",
        "sales_order_headers",
        "sales_order_items",
        "sales_order_schedule_lines",
    ]

    for table in tables:
        records = load_jsonl(table)
        if not records:
            print(f"SKIPPED (empty): {table}")
            continue

        records = [flatten(r) for r in records]
        columns = list(records[0].keys())
        col_defs = ", ".join([f'"{c}" TEXT' for c in columns])

        cursor.execute(f'DROP TABLE IF EXISTS "{table}"')
        cursor.execute(f'CREATE TABLE "{table}" ({col_defs})')

        for record in records:
            values = [str(record.get(c, "")) if record.get(c) is not None else "" for c in columns]
            placeholders = ", ".join(["?" for _ in columns])
            cursor.execute(f'INSERT INTO "{table}" VALUES ({placeholders})', values)

        print(f"LOADED: {table} — {len(records)} rows")

    conn.commit()
    conn.close()
    print("\nDone! data.db created.")

if __name__ == "__main__":
    ingest()