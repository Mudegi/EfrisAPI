"""
Load Testing for EFRIS API
Tests system performance under concurrent load

Requirements:
    pip install locust faker

Run load test:
    locust -f tests/test_load.py --host=http://localhost:8001
    
Then open: http://localhost:8089

Test scenarios:
    1. Light Load: 10 users, 2/sec spawn rate
    2. Medium Load: 50 users, 5/sec spawn rate
    3. Heavy Load: 100 users, 10/sec spawn rate
    4. Stress Test: 200+ users, 20/sec spawn rate
"""

from locust import HttpUser, task, between, events
from faker import Faker
import json
import random
import time
from datetime import datetime

fake = Faker()


class EFRISUser(HttpUser):
    """Simulates a typical EFRIS API user"""
    
    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    # API key for authentication (set via environment or config)
    api_key = None
    
    def on_start(self):
        """Called when a user starts - login/authenticate"""
        # Simulate login
        self.client.headers.update({
            "Content-Type": "application/json"
        })
        
        # Try to authenticate (adjust endpoint as needed)
        try:
            response = self.client.post("/api/auth/login", json={
                "email": f"loadtest_{fake.uuid4()[:8]}@example.com",
                "password": "testpassword"
            }, name="/api/auth/login [login]")
            
            if response.status_code == 200:
                data = response.json()
                self.api_key = data.get("api_key") or data.get("token")
                if self.api_key:
                    self.client.headers.update({
                        "X-API-Key": self.api_key
                    })
        except Exception as e:
            print(f"Login failed: {e}")
    
    @task(5)
    def get_dashboard_stats(self):
        """Get dashboard statistics (most common operation)"""
        self.client.get(
            "/api/dashboard/stats",
            name="/api/dashboard/stats"
        )
    
    @task(10)
    def list_invoices(self):
        """List invoices (very common)"""
        params = {
            "page": random.randint(1, 5),
            "limit": 20
        }
        self.client.get(
            "/api/invoices",
            params=params,
            name="/api/invoices [list]"
        )
    
    @task(3)
    def get_invoice_details(self):
        """Get specific invoice details"""
        invoice_id = random.randint(1, 1000)
        self.client.get(
            f"/api/invoices/{invoice_id}",
            name="/api/invoices/:id [details]"
        )
    
    @task(2)
    def create_invoice(self):
        """Create new invoice (less common but important)"""
        invoice_data = {
            "sellerDetails": {
                "tin": "1000000000",
                "legalName": fake.company(),
                "address": fake.address()[:50],
                "mobilePhone": fake.phone_number()[:15],
                "emailAddress": fake.email()
            },
            "basicInformation": {
                "invoiceNo": f"LOAD-{int(time.time())}-{random.randint(1000, 9999)}",
                "deviceNo": "1000000000_02",
                "issuedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "LoadTest",
                "currency": "UGX",
                "invoiceType": "1",
                "invoiceKind": "1"
            },
            "buyerDetails": {
                "buyerTin": str(random.randint(1000000000, 9999999999)),
                "buyerLegalName": fake.company(),
                "buyerAddress": fake.address()[:50],
                "buyerEmail": fake.email(),
                "buyerMobilePhone": fake.phone_number()[:15]
            },
            "goodsDetails": [{
                "item": fake.word(),
                "itemCode": f"ITEM{random.randint(100, 999)}",
                "qty": str(random.randint(1, 10)),
                "unitOfMeasure": "101",
                "unitPrice": str(random.randint(1000, 100000)),
                "total": str(random.randint(1000, 100000)),
                "taxRate": "0.18",
                "tax": str(random.randint(180, 18000)),
                "goodsCategoryId": "1234567890123"
            }],
            "summary": {
                "netAmount": str(random.randint(10000, 1000000)),
                "taxAmount": str(random.randint(1800, 180000)),
                "grossAmount": str(random.randint(11800, 1180000)),
                "itemCount": "1"
            }
        }
        
        self.client.post(
            "/api/invoices/submit",
            json=invoice_data,
            name="/api/invoices/submit [create]"
        )
    
    @task(4)
    def list_products(self):
        """List products"""
        self.client.get(
            "/api/products",
            name="/api/products [list]"
        )
    
    @task(2)
    def search_products(self):
        """Search products"""
        params = {
            "q": fake.word(),
            "limit": 20
        }
        self.client.get(
            "/api/products/search",
            params=params,
            name="/api/products/search"
        )
    
    @task(3)
    def get_company_info(self):
        """Get company information"""
        self.client.get(
            "/api/company/info",
            name="/api/company/info"
        )
    
    @task(1)
    def external_api_call(self):
        """External API call (for Custom ERP integrations)"""
        invoice_data = {
            "customer_name": fake.company(),
            "customer_tin": str(random.randint(1000000000, 9999999999)),
            "items": [{
                "name": fake.word(),
                "quantity": random.randint(1, 10),
                "unit_price": random.randint(1000, 100000)
            }]
        }
        
        self.client.post(
            "/api/external/v1/invoices",
            json=invoice_data,
            headers={"X-API-Key": "test_api_key"},
            name="/api/external/v1/invoices [external]"
        )


class AdminUser(HttpUser):
    """Simulates admin/owner portal operations"""
    
    wait_time = between(2, 5)
    
    @task(3)
    def view_all_clients(self):
        """View all clients (owner portal)"""
        self.client.get(
            "/api/owner/clients",
            name="/api/owner/clients"
        )
    
    @task(2)
    def view_resellers(self):
        """View all resellers"""
        self.client.get(
            "/api/owner/resellers",
            name="/api/owner/resellers"
        )
    
    @task(1)
    def approve_client(self):
        """Approve pending client"""
        client_id = random.randint(1, 100)
        self.client.post(
            f"/api/owner/clients/{client_id}/approve",
            name="/api/owner/clients/:id/approve"
        )
    
    @task(2)
    def view_audit_logs(self):
        """View security audit logs"""
        self.client.get(
            "/api/owner/audit-logs",
            name="/api/owner/audit-logs"
        )
    
    @task(1)
    def update_rate_limit(self):
        """Update client rate limit"""
        client_id = random.randint(1, 100)
        self.client.put(
            f"/api/owner/clients/{client_id}/rate-limit",
            json={"rate_limit": random.randint(100, 10000)},
            name="/api/owner/clients/:id/rate-limit"
        )


class ResellerUser(HttpUser):
    """Simulates reseller portal operations"""
    
    wait_time = between(2, 4)
    
    @task(5)
    def view_my_clients(self):
        """View reseller's clients"""
        self.client.get(
            "/api/reseller/clients",
            name="/api/reseller/clients"
        )
    
    @task(2)
    def add_new_client(self):
        """Add new client referral"""
        client_data = {
            "company_name": fake.company(),
            "tin": str(random.randint(1000000000, 9999999999)),
            "email": fake.email(),
            "contact_name": fake.name(),
            "phone": fake.phone_number()[:15]
        }
        
        self.client.post(
            "/api/reseller/clients",
            json=client_data,
            name="/api/reseller/clients [add]"
        )
    
    @task(3)
    def view_referral_status(self):
        """Check referral status"""
        self.client.get(
            "/api/reseller/referrals/status",
            name="/api/reseller/referrals/status"
        )


# Performance thresholds
RESPONSE_TIME_THRESHOLDS = {
    "fast": 200,      # < 200ms
    "acceptable": 1000,  # < 1s
    "slow": 3000      # < 3s
}

# Track metrics
stats = {
    "total_requests": 0,
    "failed_requests": 0,
    "slow_requests": 0
}


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics"""
    stats["total_requests"] += 1
    
    if exception:
        stats["failed_requests"] += 1
    
    if response_time > RESPONSE_TIME_THRESHOLDS["slow"]:
        stats["slow_requests"] += 1
        print(f"⚠️  SLOW REQUEST: {name} took {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary when test stops"""
    print("\n" + "="*60)
    print("LOAD TEST SUMMARY")
    print("="*60)
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Failed Requests: {stats['failed_requests']} ({stats['failed_requests']/stats['total_requests']*100:.2f}%)")
    print(f"Slow Requests (>{RESPONSE_TIME_THRESHOLDS['slow']}ms): {stats['slow_requests']} ({stats['slow_requests']/stats['total_requests']*100:.2f}%)")
    
    # Performance goals
    print("\n" + "-"*60)
    print("PERFORMANCE GOALS")
    print("-"*60)
    
    failure_rate = stats['failed_requests'] / stats['total_requests'] * 100 if stats['total_requests'] > 0 else 0
    slow_rate = stats['slow_requests'] / stats['total_requests'] * 100 if stats['total_requests'] > 0 else 0
    
    goals = {
        "Failure Rate < 1%": failure_rate < 1.0,
        "Slow Requests < 5%": slow_rate < 5.0,
    }
    
    for goal, passed in goals.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {goal}")
    
    print("="*60 + "\n")


# Custom test scenarios
class QuickLoadTest(HttpUser):
    """Quick smoke test - 10 users, 1 minute"""
    wait_time = between(1, 2)
    
    @task
    def smoke_test(self):
        """Basic endpoints smoke test"""
        endpoints = [
            "/api/health",
            "/api/dashboard/stats",
            "/api/invoices",
            "/api/products"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name=f"{endpoint} [smoke]")


class StressTest(HttpUser):
    """Stress test - push system to limits"""
    wait_time = between(0.1, 0.5)  # Very short wait
    
    @task(10)
    def rapid_fire_requests(self):
        """Rapid successive requests"""
        self.client.get("/api/dashboard/stats", name="/api/dashboard/stats [stress]")
    
    @task(5)
    def concurrent_invoice_creation(self):
        """Create invoices rapidly"""
        invoice_data = {
            "basicInformation": {
                "invoiceNo": f"STRESS-{int(time.time())}-{random.randint(1, 99999)}",
                "issuedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "summary": {
                "netAmount": "10000",
                "taxAmount": "1800",
                "grossAmount": "11800"
            }
        }
        
        self.client.post("/api/invoices/submit", json=invoice_data, name="/api/invoices/submit [stress]")


# Custom load shapes
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    Step load pattern:
    - 10 users for 1 min
    - 50 users for 2 min
    - 100 users for 2 min
    - 50 users for 1 min
    - 10 users for 1 min
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 180, "users": 50, "spawn_rate": 5},
        {"duration": 300, "users": 100, "spawn_rate": 10},
        {"duration": 360, "users": 50, "spawn_rate": 5},
        {"duration": 420, "users": 10, "spawn_rate": 2},
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None


if __name__ == "__main__":
    import os
    os.system("locust -f tests/test_load.py --host=http://localhost:8001")
