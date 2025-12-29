from fastapi import FastAPI, HTTPException, Query
from efris_client import EfrisManager

app = FastAPI(title="EFRIS API", description="API for EFRIS integration")
print("App created")

# Initialize the manager
manager = EfrisManager(tin='1014409555', test_mode=True)
print("Manager created")

@app.get("/api/{tin}/registration-details")
async def get_registration_details(tin: str, token: str = Query(...)):
    # Simple token check (replace with proper auth)
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        details = manager.get_registration_details()
        return {
            "returnStateInfo": {
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            },
            "data": details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/{tin}/goods-and-services")
async def get_goods_and_services(tin: str, token: str = Query(...)):
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Assuming empty request_data for GET
        goods = manager.get_goods_and_services({})
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": goods
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/{tin}/generate-fiscal-invoice")
async def generate_fiscal_invoice(tin: str, invoice_data: dict, token: str = Query(...)):
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        invoice = manager.generate_invoice(invoice_data)
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": invoice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/{tin}/generate-fiscal-receipt")
async def generate_fiscal_receipt(tin: str, receipt_data: dict, token: str = Query(...)):
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Assuming similar to invoice, but adjust as needed
        receipt = manager.generate_invoice(receipt_data)  # Or add separate method
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": receipt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/query-taxpayer/{tin}")
async def query_taxpayer(tin: str, token: str = Query(...), ninBrn: str = Query(default="")):
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        result = manager.query_taxpayer_by_tin(tin, ninBrn)
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-server-time")
async def get_server_time_api(token: str = Query(...)):
    if token != "test_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        result = manager.get_server_time()
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)