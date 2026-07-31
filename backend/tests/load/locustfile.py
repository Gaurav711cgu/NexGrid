"""
NexaGrid Load Test Suite
Run: locust -f backend/tests/load/locustfile.py --headless -u 50 -r 5 \
     --run-time 120s --host http://localhost:8000
"""
import json
import time
import random
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser

TEST_EMAIL = f"loadtest_{int(time.time())}@nexagrid.dev"
TEST_PASSWORD = "LoadTest_Secure_2026!"

class NexaGridUser(FastHttpUser):
    wait_time = between(0.5, 2.0)
    token: str = None
    room_id: str = None

    def on_start(self):
        """Register + login once per simulated user."""
        r = self.client.post("/api/auth/register", json={
            "email": f"user_{id(self)}_{random.randint(1000, 9999)}@loadtest.dev",
            "password": TEST_PASSWORD,
            "display_name": f"LoadUser_{id(self)}"
        })
        if r.status_code in (200, 201):
            self.token = r.json().get("access_token")
        elif r.status_code == 400:
            r = self.client.post("/api/auth/login", json={
                "email": f"user_{id(self)}@loadtest.dev",
                "password": TEST_PASSWORD
            })
            self.token = r.json().get("access_token", "")

        # Create a room
        if self.token:
            r = self.client.post("/api/rooms", json={
                "name": "Load Test Room",
                "language": "python"
            }, headers=self._auth_headers())
            if r.status_code == 201:
                self.room_id = r.json().get("id")

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def execute_code(self):
        """Core execution path — measure sandbox latency."""
        if not self.room_id or not self.token:
            return
        code = f"x = {random.randint(1, 100)}\nresult = x * x\nprint(f'{{x}}^2 = {{result}}')"
        self.client.post(
            f"/api/execution/{self.room_id}/run",
            json={"code": code, "language": "python"},
            headers=self._auth_headers(),
            name="/api/execution/[room_id]/run"
        )

    @task(3)
    def get_history(self):
        """Cursor pagination path."""
        if not self.room_id or not self.token:
            return
        self.client.get(
            f"/api/rooms/{self.room_id}/history",
            headers=self._auth_headers(),
            name="/api/rooms/[room_id]/history"
        )

    @task(1)
    def get_analytics(self):
        """Window function + CTE path."""
        if not self.room_id or not self.token:
            return
        self.client.get(
            f"/api/analytics/room/{self.room_id}/summary",
            headers=self._auth_headers(),
            name="/api/analytics/room/[room_id]/summary"
        )

    @task(2)
    def health_check(self):
        self.client.get("/health")

@events.quitting.add_listener
def print_summary(environment, **kwargs):
    """Print benchmark summary for README."""
    stats = environment.runner.stats
    print("\n=== NexaGrid Load Test Results ===")
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            print(f"{name[1]}: p50={entry.get_response_time_percentile(0.5):.1f}ms "
                  f"p95={entry.get_response_time_percentile(0.95):.1f}ms "
                  f"p99={entry.get_response_time_percentile(0.99):.1f}ms "
                  f"rps={entry.current_rps:.1f}")
