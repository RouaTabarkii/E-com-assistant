import os
os.environ["PGSYSCONFDIR"] = "C:\\olistiq"
os.environ["PGPASSFILE"] = ""
os.environ["PGSERVICEFILE"] = ""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "olist"

CSV_TABLES = {
    "olist_customers_dataset.csv":           "customers",
    "olist_orders_dataset.csv":              "orders",
    "olist_order_items_dataset.csv":         "order_items",
    "olist_order_payments_dataset.csv":      "order_payments",
    "olist_order_reviews_dataset.csv":       "order_reviews",
    "olist_products_dataset.csv":            "products",
    "olist_sellers_dataset.csv":             "sellers",
    "olist_geolocation_dataset.csv":         "geolocation",
    "product_category_name_translation.csv": "product_category_translation",
}


def load_csv_to_postgres():
    engine = create_engine(
        DB_URL,
        connect_args={"passfile": ""}
    )

    with engine.connect() as conn:
        for csv_file, table_name in CSV_TABLES.items():
            csv_path = DATA_DIR / csv_file

            if not csv_path.exists():
                print(f"[SKIP] {csv_file} not found")
                continue

            print(f"[LOADING] {csv_file} → table '{table_name}'...")
            df = pd.read_csv(csv_path)

            df.to_sql(
                name=table_name,
                con=engine,
                if_exists="replace",
                index=False,
                chunksize=1000,
            )

            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"[OK] '{table_name}' — {count} rows loaded")

    print("\n✅ All tables loaded successfully.")


if __name__ == "__main__":
    load_csv_to_postgres()