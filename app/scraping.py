# app/scraping.py
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from typing import Optional, Dict, Any
import re
import aiohttp
from urllib.parse import urljoin

async def render_page_html(url: str, headless: bool = True, wait_for: str = "networkidle") -> Dict[str, Any]:
    """
    Launch Playwright, visit the URL, wait for render, return page content and final url.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until=wait_for, timeout=60000)
        # wait a little to ensure inline JS execution
        await asyncio.sleep(0.5)
        content = await page.content()
        final_url = page.url
        # Extract potential submit URL and download links heuristically
        # Look for form action or JS variables containing "submit" or "answer"
        text = await page.inner_text("body")
        await browser.close()
        return {"html": content, "text": text, "final_url": final_url}

async def download_file(url: str, session: aiohttp.ClientSession, dest_path: str):
    async with session.get(url, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(await resp.read())
    return dest_path

def find_urls_from_text(text: str) -> Dict[str, Optional[str]]:
    """
    Heuristic search for links: submit URL, download URLs, base64 strings, etc.
    """
    out = {"submit": None, "download": None}
    # find JSON-like endpoints or forms
    m = re.search(r'(https?://[^\s"\'<>]+?/submit[^\s"\'<>]*)', text, re.IGNORECASE)
    if m:
        out["submit"] = m.group(1)
    m2 = re.search(r'(https?://[^\s"\'<>]+?\.(pdf|csv|zip)[^\s"\'<>]*)', text, re.IGNORECASE)
    if m2:
        out["download"] = m2.group(1)
    return out
