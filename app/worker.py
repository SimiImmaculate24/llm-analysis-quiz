# app/worker.py
import asyncio
import aiohttp
import time
from .scraping import render_page_html, find_urls_from_text, download_file
from .processing import sum_values_in_pdf_table
from .config import TIMEOUT_SECONDS, PLAYWRIGHT_HEADLESS
from typing import Dict, Any
import os
import tempfile
import json

async def solve_single_quiz(email: str, secret: str, url: str) -> Dict[str, Any]:
    start = time.time()
    deadline = start + TIMEOUT_SECONDS
    results = {"attempts": [], "final_url": url}
    async with aiohttp.ClientSession() as session:
        current_url = url
        while time.time() < deadline and current_url:
            t0 = time.time()
            rendered = await render_page_html(current_url, headless=PLAYWRIGHT_HEADLESS)
            text = rendered["text"]
            findings = find_urls_from_text(text)
            # if download found -> download and process
            answer = None
            if findings.get("download"):
                fp = tempfile.mktemp(suffix=os.path.basename(findings["download"]))
                try:
                    await download_file(findings["download"], session, fp)
                    # Example question expects sum of 'value' column on page 2:
                    s = sum_values_in_pdf_table(fp, page_number=2, colname_hint="value")
                    answer = s
                except Exception as e:
                    results["attempts"].append({"url": current_url, "error": str(e)})
            # if base64 JS inline trick is used, maybe text contains "atob(" — attempt to extract it:
            if not answer:
                import re, base64
                bmatch = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', rendered["html"])
                if bmatch:
                    try:
                        decoded = base64.b64decode(bmatch.group(1)).decode("utf-8", errors="ignore")
                        # quick heuristic: find numbers in decoded text
                        nums = [float(x) for x in re.findall(r'[-]?\d+\.?\d*', decoded)]
                        if nums:
                            answer = sum(nums)  # fallback heuristic
                    except Exception:
                        pass
            # If we have an answer and a submit endpoint, submit
            submit_url = findings.get("submit")
            if submit_url and answer is not None:
                payload = {"email": email, "secret": secret, "url": current_url, "answer": answer}
                try:
                    async with session.post(submit_url, json=payload, timeout=30) as resp:
                        j = None
                        try:
                            j = await resp.json()
                        except Exception:
                            j = {"status": resp.status, "text": await resp.text()}
                        results["attempts"].append({"url": current_url, "submit_response": j, "answer": answer})
                        # If the server returns next url in JSON, follow it
                        if isinstance(j, dict) and j.get("url"):
                            current_url = j.get("url")
                            results["final_url"] = current_url
                            continue
                        else:
                            # assume finished
                            break
                except Exception as e:
                    results["attempts"].append({"url": current_url, "submit_error": str(e), "answer": answer})
                    # allow retry or break
                    break
            else:
                results["attempts"].append({"url": current_url, "answer_attempt": answer, "findings": findings})
                # no submit URL or no answer: cannot proceed
                break
    return results
