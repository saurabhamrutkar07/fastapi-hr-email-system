import pdfplumber
import re
from collections import defaultdict
from typing import List, Dict, Any

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

def extract_pdf_contact_from_pdf(file_obj) -> List[Dict[str, Any]]:
    """
    Extract HR contact details from a PDF file-like object.

    Returns:
        List of dicts with keys:
        name, email, title, company, phone
    """

    results: List[Dict[str, Any]] = []

    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            try:
                words = page.extract_words(use_text_flow=True)
            except Exception:
                # If extraction fails on a page, skip it
                continue

            if not words or not isinstance(words, list):
                continue

            # Group words by visual line using "top" coordinate
            lines: dict[float, list[str]] = defaultdict(list)

            for w in words:
                # Defensive checks (CRITICAL)
                if not isinstance(w, dict):
                    continue

                text = w.get("text")
                top = w.get("top")

                if not text or not isinstance(text, str):
                    continue
                if not isinstance(top, (int, float)):
                    continue

                line_key = round(top, 1)
                lines[line_key].append(text.strip())

            # Process each reconstructed line
            for word_list in lines.values():
                line = " ".join(word_list).strip()

                if not line:
                    continue
                if line.lower().startswith(("sno", "sr no", "sr.no")):
                    continue

                email_match = EMAIL_REGEX.search(line)
                if not email_match:
                    continue

                email = email_match.group()

                left_part = line[:email_match.start()].strip()
                right_part = line[email_match.end():].strip()

                # Left side: expect "1 John Doe"
                left_tokens = left_part.split(maxsplit=1)
                if len(left_tokens) < 2:
                    continue

                # Validate serial number
                try:
                    int(left_tokens[0])
                except ValueError:
                    continue

                name = left_tokens[1].strip()
                if not name:
                    continue

                # Right side: title + company (best-effort split)
                title = ""
                company = ""

                if right_part:
                    parts = right_part.split()
                    if len(parts) >= 2:
                        title = parts[0]
                        company = " ".join(parts[1:])
                    else:
                        title = right_part

                results.append({
                    "name": name,
                    "email": email,
                    "title": title.strip(),
                    "company": company.strip(),
                    "phone": None
                })

    return results
