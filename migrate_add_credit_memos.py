"""
Add credit_memos table to database
"""
from database.connection import engine
from sqlalchemy import text

# Create credit_memos table
create_table_sql = """
CREATE TABLE IF NOT EXISTS credit_memos (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    qb_credit_memo_id VARCHAR(50) NOT NULL,
    qb_doc_number VARCHAR(100),
    qb_customer_name VARCHAR(255),
    qb_txn_date TIMESTAMP WITH TIME ZONE,
    qb_total_amt FLOAT,
    qb_data JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_credit_memos_qb_credit_memo_id ON credit_memos(qb_credit_memo_id);
CREATE INDEX IF NOT EXISTS ix_credit_memos_company_id ON credit_memos(company_id);
"""

with engine.connect() as conn:
    conn.execute(text(create_table_sql))
    conn.commit()
    print("✓ credit_memos table created successfully")
