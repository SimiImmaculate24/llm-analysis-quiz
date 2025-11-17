# app/processing.py
import pdfplumber
import pandas as pd
from typing import Optional
import os

def sum_values_in_pdf_table(pdf_path: str, page_number: int = 2, colname_hint: str = "value") -> Optional[float]:
    """
    Open pdf, find tables on page_number (1-indexed), sum column with name like colname_hint.
    Returns float or None.
    """
    if not os.path.exists(pdf_path):
        return None
    with pdfplumber.open(pdf_path) as pdf:
        if page_number <= 0 or page_number > len(pdf.pages):
            return None
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()
        # try to find table and column
        for table in tables:
            df = pd.DataFrame(table[1:], columns=table[0])
            # normalize column names
            cols = [str(c).strip().lower() for c in df.columns]
            for idx, cn in enumerate(cols):
                if colname_hint.lower() in cn:
                    # convert column values to numeric
                    s = pd.to_numeric(df.iloc[:, idx].replace(r'[^0-9.\-]', '', regex=True), errors='coerce')
                    return float(s.sum(skipna=True))
        # fallback: try to parse all numbers on page and sum? Not safe; return None
    return None
