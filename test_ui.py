import os
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

load_dotenv()
DASH_URL = os.getenv("DASH_URL", "http://localhost:8050")


def test_dashboard_loads(page: Page):
    page.goto(DASH_URL, wait_until="domcontentloaded")

    # Проверяем, что кнопка и поле есть
    expect(page.get_by_role("button", name="Обновить")).to_be_visible(timeout=10_000)
    expect(page.locator("#where")).to_be_visible(timeout=10_000)

    # Таблица должна появиться
    expect(page.locator("table, [role='grid']")).to_have_count(1, timeout=15_000)


def test_refresh_button_updates(page: Page):
    page.goto(DASH_URL, wait_until="domcontentloaded")

    page.get_by_role("button", name="Обновить").click()

    # Должны отрендериться 2 графика Plotly
    expect(page.locator(".js-plotly-plot")).to_have_count(2, timeout=20_000)


def test_where_filter_input_works(page: Page):
    page.goto(DASH_URL, wait_until="domcontentloaded")

    page.locator("#where").fill("(Id,gt,0)")
    page.get_by_role("button", name="Обновить").click()

    expect(page.locator(".js-plotly-plot")).to_have_count(2, timeout=20_000)