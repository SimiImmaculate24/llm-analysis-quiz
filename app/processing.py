# app/processing.py
import pdfplumber
import pandas as pd
import re
import os
from typing import Optional


def sum_values_in_pdf_table(pdf_path: str, page_number: int = 2, colname_hint: str = "value") -> Optional[float]:
    """
    Extract tables from a PDF and sum the column containing `colname_hint`.
    """

    if not os.path.exists(pdf_path):
        return None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_number <= 0 or page_number > len(pdf.pages):
                return None

            page = pdf.pages[page_number - 1]
            tables = page.extract_tables()

            # First try: table extraction
            for table in tables:
                header = table[0]
                rows = table[1:]
                df = pd.DataFrame(rows, columns=header)

                # Normalize
                cols = [str(c).strip().lower() for c in df.columns]

                for idx, cn in enumerate(cols):
                    if colname_hint.lower() in cn:
                        # Clean values
                        s = pd.to_numeric(
                            df.iloc[:, idx].replace(r"[^0-9.\-]", "", regex=True),
                            errors="coerce"
                        )
                        return float(s.sum(skipna=True))

            # Fallback: sum all numbers on page
            text = page.extract_text() or ""
            nums = re.findall(r"-?\d+\.?\d*", text)

            if nums:
                return sum(float(n) for n in nums)

    except Exception:
        return None

    return None
