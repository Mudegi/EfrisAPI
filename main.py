"""
Main entry point for the EFRIS Multi-Tenant API Server.

This file starts the multi-tenant EFRIS API with QuickBooks integration.
All functionality is now in api_multitenant.py.

To run the server:
    py main.py
    
Or directly with uvicorn:
    py -m uvicorn api_multitenant:app --host 0.0.0.0 --port 8001
"""

import uvicorn

def main():
    print("=" * 60)
    print("  EFRIS Multi-Tenant API Server")
    print("  Starting on http://0.0.0.0:8001")
    print("=" * 60)
    
    uvicorn.run(
        "api_multitenant:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )

if __name__ == "__main__":
    main()
