# app/scraping.py
import asyncio
from playwright.async_api import async_playwright
from typing import Dict, Any, Optional
import re


async def render_page_html(url: str, headless: bool = True, wait_for: str = "networkidle") -> Dict[str, Any]:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url, wait_until=wait_for, timeout=60000)
        await asyncio.sleep(0.4)

        html = await page.content()
        text = await page.inner_text("body")
        final_url = page.url

        await browser.close()
        return {"html": html, "text": text, "final_url": final_url}


async def download_file(url: str, session, dest_path: str):
    async with session.get(url, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(await resp.read())
    return dest_path


def find_urls_from_text(text: str) -> Dict[str, Optional[str]]:
    out = {"submit": None, "download": None}

    submit = re.search(r"(https?://[^\s\"']*submit[^\s\"']*)", text, re.IGNORECASE)
    if submit:
        out["submit"] = submit.group(1)

    download = re.search(r"(https?://[^\s\"']*download[^\s\"']*)", text, re.IGNORECASE)
    if download:
        out["download"] = download.group(1)

    # relative download
    rel_d = re.search(r"(/download[^\s\"']*)", text, re.IGNORECASE)
    if rel_d and not out["download"]:
        out["download"] = rel_d.group(1)

    return out
