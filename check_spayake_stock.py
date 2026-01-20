from database.connection import get_db
from database.models import EFRISGood

db = next(get_db())
good = db.query(EFRISGood).filter(
    EFRISGood.company_id == 1,
    EFRISGood.goods_code == 'SpaYake'
).first()

if good:
    print(f'Product: {good.goods_name}')
    print(f'Code: {good.goods_code}')
    print(f'Stock in DB field: {good.stock}')
    if good.efris_data:
        print(f'Stock in efris_data: {good.efris_data.get("stock")}')
    else:
        print('No efris_data')
else:
    print('Product not found')
