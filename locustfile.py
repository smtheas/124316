import os
import random
from locust import HttpUser, task, between

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080").rstrip("/")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN", "ACmEJK3iMNyOH5ZCWCQo8RuzWp4lztVj5rQ_1VLQ")
THEMES_TABLE_ID = os.getenv("THEMES_TABLE_ID", "mwfefucaxriw1rv")

class DashUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def open_home(self):
        # Главная страница Dash
        self.client.get("/", name="Dash: GET /")


class NocoDBUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        if NOCODB_TOKEN:
            self.client.headers.update({"xc-token": NOCODB_TOKEN})

    @task
    def list_records(self):
        with self.client.get(
            f"/api/v2/tables/{THEMES_TABLE_ID}/records",
            params={"limit": 25},
            name="NocoDB: list records",
            catch_response=True
        ) as r:
            if r.status_code != 200:
                r.failure(f"{r.status_code} {r.url} | {r.text[:300]}")