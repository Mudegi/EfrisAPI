from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///efris.db')
conn = engine.connect()

result = conn.execute(text("SELECT qb_name, is_zero_rated, is_exempt FROM products WHERE qb_name IN ('City Tires', 'Amata', 'Hoe')"))

for row in result:
    print(f"{row[0]}: is_zero_rated={row[1]}, is_exempt={row[2]}")

conn.close()
