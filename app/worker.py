# app/worker.py
import asyncio
import aiohttp
import time
import os
import tempfile
import base64
import re

from urllib.parse import urljoin

from .scraping import render_page_html, find_urls_from_text, download_file
from .processing import sum_values_in_pdf_table
from .config import TIMEOUT_SECONDS, PLAYWRIGHT_HEADLESS


async def solve_single_quiz(email: str, secret: str, url: str):
    results = {"attempts": [], "final_url": url}
    deadline = time.time() + TIMEOUT_SECONDS

    current_url = url

    async with aiohttp.ClientSession() as session:
        while time.time() < deadline and current_url:

            rendered = await render_page_html(current_url, headless=PLAYWRIGHT_HEADLESS)
            text = rendered["text"]

            findings = find_urls_from_text(text)

            # Fix relative URLs
            for key in ["download", "submit"]:
                if findings.get(key) and findings[key].startswith("/"):
                    findings[key] = urljoin(current_url, findings[key])

            answer = None

            # Download PDF if found
            if findings.get("download"):
                temp = tempfile.mktemp(suffix=".pdf")
                try:
                    await download_file(findings["download"], session, temp)
                    answer = sum_values_in_pdf_table(temp, page_number=2, colname_hint="value")
                except Exception as e:
                    results["attempts"].append({"url": current_url, "error": str(e)})

            # Base64 fallback
            if answer is None:
                b = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', rendered["html"])
                if b:
                    try:
                        decoded = base64.b64decode(b.group(1)).decode("utf-8", "ignore")
                        nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", decoded)]
                        if nums:
                            answer = sum(nums)
                    except Exception:
                        pass

            submit_url = findings.get("submit")

            # If we have answer + submit -> POST
            if answer is not None and submit_url:
                payload = {"email": email, "secret": secret, "url": current_url, "answer": answer}

                try:
                    async with session.post(submit_url, json=payload, timeout=30) as resp:
                        try:
                            j = await resp.json()
                        except:
                            j = {"status": resp.status, "text": await resp.text()}

                        results["attempts"].append(
                            {"url": current_url, "submit_response": j, "answer": answer}
                        )

                        if isinstance(j, dict) and j.get("url"):
                            current_url = j["url"]
                            results["final_url"] = current_url
                            continue
                        else:
                            break

                except Exception as e:
                    results["attempts"].append({"url": current_url, "submit_error": str(e)})
                    break

            else:
                # No submit or no answer: stop
                results["attempts"].append(
                    {"url": current_url, "answer_attempt": answer, "findings": findings}
                )
                break

    return results
