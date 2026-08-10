"""
===============================================================================
PDF HR Contact Extraction Engine (pdf_hr_extraction_service.py)
===============================================================================
Parses PDF document pages using `pdfplumber`, reconstructs text lines based on 
visual Y-coordinates (`top`), matches email regex patterns, and extracts structured 
recruiter contacts (name, email, title, company).
===============================================================================
"""

import pdfplumber
import re
from collections import defaultdict
from typing import List, Dict, Any

# Standard Regular Expression for matching email addresses
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)


def extract_pdf_contact_from_pdf(file_obj) -> List[Dict[str, Any]]:
    """
    Extracts structured HR contact details from a PDF binary file stream.

    Parameters:
    -----------
    file_obj : file-like binary stream
        Uploaded PDF file object.

    Returns:
    --------
    List[Dict[str, Any]]:
        Array of extracted contact dictionaries containing: `name`, `email`, `title`, `company`, `phone`.
    """

    results: List[Dict[str, Any]] = []

    # Open PDF document with pdfplumber
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            try:
                # Extract words maintaining visual reading flow
                words = page.extract_words(use_text_flow=True)
            except Exception:
                # Skip page if text extraction fails
                continue

            if not words or not isinstance(words, list):
                continue

            # Group words into visual lines using the "top" Y-coordinate
            lines: dict[float, list[str]] = defaultdict(list)

            for w in words:
                # Defensive checks for word data structure
                if not isinstance(w, dict):
                    continue

                text = w.get("text")
                top = w.get("top")

                if not text or not isinstance(text, str):
                    continue
                if not isinstance(top, (int, float)):
                    continue

                # Round Y-coordinate to group words on the same horizontal visual line
                line_key = round(top, 1)
                lines[line_key].append(text.strip())

            # Process each reconstructed text line
            for word_list in lines.values():
                line = " ".join(word_list).strip()

                if not line:
                    continue
                
                # Skip header rows (e.g. "SNo Name Email Title Company")
                if line.lower().startswith(("sno", "sr no", "sr.no")):
                    continue

                # Locate email address in line via regex
                email_match = EMAIL_REGEX.search(line)
                if not email_match:
                    continue

                email = email_match.group()

                # Split line relative to email position
                left_part = line[:email_match.start()].strip()
                right_part = line[email_match.end():].strip()

                # Left side expected format: "1 John Doe"
                left_tokens = left_part.split(maxsplit=1)
                if len(left_tokens) < 2:
                    continue

                # Validate leading serial number
                try:
                    int(left_tokens[0])
                except ValueError:
                    continue

                name = left_tokens[1].strip()
                if not name:
                    continue

                # Right side expected format: Title & Company
                title = ""
                company = ""

                if right_part:
                    parts = right_part.split()
                    if len(parts) >= 2:
                        title = parts[0]
                        company = " ".join(parts[1:])
                    else:
                        title = right_part

                # Append extracted contact dictionary
                results.append({
                    "name": name,
                    "email": email,
                    "title": title.strip(),
                    "company": company.strip(),
                    "phone": None
                })

    return results

