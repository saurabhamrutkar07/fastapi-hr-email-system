import io
import re
from pathlib import Path
from typing import Any

import pandas as pd

from pydantic import ValidationError

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    HRContactsV2,
    HRContactEmail,
    HRContactPhone,
)

# from app.schemas.hr_contact_excel import (
#     ExcelContact,
# )

from app.schemas.hr_contacts_excel import ExcelContact


# ============================================================
# Supported file extensions
# ============================================================

ALLOWED_EXTENSIONS = {
    ".xlsx",
    ".xls",
    ".xlsm",
    ".xlsb",
    ".ods",
    ".csv",
}


# ============================================================
# Required columns
# ============================================================

# Personal Email is intentionally NOT required.
#
# If your Excel still has a "Personal Email" column,
# its email value will still be detected because we scan
# all columns for email addresses.

REQUIRED_COLUMNS = {
    "Name",
    "Email",
    "Contact Number",
    "Company",
    "Position",
    "Openings",
}


# ============================================================
# File extension
# ============================================================

def get_file_extension(
    filename: str,
) -> str:

    return Path(
        filename
    ).suffix.lower()


# ============================================================
# Clean generic cell value
# ============================================================

def clean_value(
    value: Any,
) -> str | None:

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    value = str(value).strip()

    if not value:
        return None

    invalid_values = {
        "nan",
        "none",
        "null",
        "n/a",
        "na",
        "not available",
        "not_available",
        "nil",
        "-",
    }

    if value.lower() in invalid_values:
        return None

    return value


# ============================================================
# Extract email addresses
# ============================================================

def extract_emails(
    value: Any,
) -> list[str]:

    value = clean_value(value)

    if not value:
        return []

    matches = re.findall(
        r"[A-Za-z0-9._%+\-]+"
        r"@"
        r"[A-Za-z0-9.\-]+"
        r"\.[A-Za-z]{2,}",
        value,
    )

    emails = []

    for email in matches:

        email = email.lower().strip()

        if email not in emails:
            emails.append(email)

    return emails


# ============================================================
# Extract phone numbers
# ============================================================

def extract_phones(
    value: Any,
) -> list[str]:

    value = clean_value(value)

    if not value:
        return []

    values = re.split(
        r"[,;/|]+",
        value,
    )

    phones = []

    for item in values:

        item = item.strip()

        if not item:
            continue

        # A number Excel stored as 9876543210.0
        item = re.sub(
            r"\.0+$",
            "",
            item,
        )

        phone = re.sub(
            r"[^\d+]",
            "",
            item,
        )

        # +91XXXXXXXXXX
        if phone.startswith("+91"):
            phone = phone[3:]

        # 91XXXXXXXXXX
        elif (
            phone.startswith("91")
            and len(phone) == 12
        ):
            phone = phone[2:]

        # Only accept 10-digit Indian numbers
        if len(phone) != 10:
            continue

        if not phone.isdigit():
            continue

        if phone not in phones:
            phones.append(phone)

    return phones


# ============================================================
# Validate columns
# ============================================================

def validate_excel_columns(
    df: pd.DataFrame,
):

    actual_columns = {
        str(column).strip()
        for column in df.columns
    }

    missing_columns = (
        REQUIRED_COLUMNS - actual_columns
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )


# ============================================================
# Read uploaded file
# ============================================================

def find_header_row(
    raw: pd.DataFrame,
) -> int:
    """
    Position of the first row (among the top 10) that has both a
    "Name" and an "Email" cell. Falls back to the first row, so a
    file without them still gets "Missing required columns".
    """

    for position in range(min(10, len(raw))):

        cells = {
            str(value).strip()
            for value in raw.iloc[position]
            if pd.notna(value)
        }

        if {"Name", "Email"} <= cells:
            return position

    return 0



def read_upload_file(
    contents: bytes,
    filename: str,
) -> pd.DataFrame:

    extension = get_file_extension(
        filename
    )

    try:

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        if extension == ".csv":

            raw = pd.read_csv(
                io.BytesIO(contents),
                sep=None,
                engine="python",
                header=None,
                dtype=str,
            )

        # ----------------------------------------------------
        # XLSB
        # ----------------------------------------------------

        elif extension == ".xlsb":

            raw = pd.read_excel(
                io.BytesIO(contents),
                engine="pyxlsb",
                sheet_name=0,
                header=None,
                dtype=str,
            )

        # ----------------------------------------------------
        # ODS
        # ----------------------------------------------------

        elif extension == ".ods":

            raw = pd.read_excel(
                io.BytesIO(contents),
                engine="odf",
                sheet_name=0,
                header=None,
                dtype=str,
            )

        # ----------------------------------------------------
        # XLS / XLSX / XLSM
        # ----------------------------------------------------

        else:

            raw = pd.read_excel(
                io.BytesIO(contents),
                sheet_name=0,
                header=None,
                dtype=str,
            )

    except Exception as exc:

        raise ValueError(
            f"Unable to read {extension} file: {exc}"
        )

    # ----------------------------------------------------
    # Header row: wherever "Name" and "Email" are, so a sheet
    # may start with a title row (or not)
    # ----------------------------------------------------

    header_row = find_header_row(
        raw
    )

    df = raw.iloc[header_row + 1:]

    # Blank header cells get a placeholder name, so two blank
    # headers never collide
    df.columns = [
        str(value).strip()
        if pd.notna(value) and str(value).strip()
        else f"Column {position + 1}"
        for position, value in enumerate(
            raw.iloc[header_row]
        )
    ]

    # Keep pandas' row numbers in step with the spreadsheet:
    # build_contacts_from_excel() reports `index + 2` as the row.
    df.index = range(
        header_row,
        header_row + len(df),
    )

    df = df.dropna(
        how="all"
    )

    if df.empty:

        raise ValueError(
            "Uploaded file contains no data."
        )


    validate_excel_columns(
        df
    )

    return df


# ============================================================
# Extract ALL emails from a row
# ============================================================

def extract_row_emails(
    row: pd.Series,
) -> list[str]:

    emails = []

    # We deliberately scan every column.
    #
    # Therefore these all work:
    #
    # Email
    # Personal Email
    # Work Email
    # Secondary Email
    # Unnamed: 7
    # Other Contact
    #
    # If a cell contains an email address,
    # it gets collected.

    for column in row.index:

        value = row.get(column)

        row_emails = extract_emails(
            value
        )

        for email in row_emails:

            if email not in emails:

                emails.append(email)

    return emails


# ============================================================
# Extract phones
# ============================================================

def extract_row_phones(
    row: pd.Series,
) -> list[str]:

    phones = []

    # We only inspect columns that look like
    # phone/mobile/contact columns.
    #
    # This avoids interpreting random numbers such as
    # job IDs or years as phone numbers.

    phone_columns = [
        column
        for column in row.index
        if (
            "phone" in str(column).lower()
            or "mobile" in str(column).lower()
            or "contact" in str(column).lower()
        )
    ]

    for column in phone_columns:

        row_phones = extract_phones(
            row.get(column)
        )

        for phone in row_phones:

            if phone not in phones:

                phones.append(phone)

    return phones


# ============================================================
# Build normalized contacts
# ============================================================

def build_contacts_from_excel(
    df: pd.DataFrame,
):

    contacts = []

    errors = []

    # Current contact being constructed.
    current_contact = None

    for index, row in df.iterrows():

        # read_upload_file() numbers the rows so that
        # index + 2 is the row number in the spreadsheet.
        excel_row_number = index + 2

        # ----------------------------------------------------
        # Basic fields
        # ----------------------------------------------------

        name = clean_value(
            row.get("Name")
        )

        company = clean_value(
            row.get("Company")
        )

        position = clean_value(
            row.get("Position")
        )

        openings = clean_value(
            row.get("Openings")
        )

        # ----------------------------------------------------
        # Emails
        # ----------------------------------------------------

        emails = extract_row_emails(
            row
        )

        # ----------------------------------------------------
        # Phones
        # ----------------------------------------------------

        phones = extract_row_phones(
            row
        )

        # ====================================================
        # NEW CONTACT
        # ====================================================

        if name:

            current_contact = {
                "name": name,
                "emails": [],
                "phones": [],
                "company": company,
                "position": position,
                "openings": openings,
            }

            contacts.append(
                current_contact
            )

        # ====================================================
        # CONTINUATION ROW
        # ====================================================

        elif current_contact is None:

            if emails or phones:

                errors.append(
                    {
                        "row": excel_row_number,
                        "error": (
                            "Email or phone found "
                            "without a preceding contact."
                        ),
                    }
                )

            continue

        # ====================================================
        # Add emails
        # ====================================================

        for email in emails:

            if (
                email
                not in current_contact["emails"]
            ):

                current_contact["emails"].append(
                    email
                )

        # ====================================================
        # Add phones
        # ====================================================

        for phone in phones:

            if (
                phone
                not in current_contact["phones"]
            ):

                current_contact["phones"].append(
                    phone
                )

        # ====================================================
        # Fill missing information
        # ====================================================

        if (
            not current_contact["company"]
            and company
        ):
            current_contact["company"] = company

        if (
            not current_contact["position"]
            and position
        ):
            current_contact["position"] = position

        if (
            not current_contact["openings"]
            and openings
        ):
            current_contact["openings"] = openings

    # ========================================================
    # Pydantic validation
    # ========================================================

    validated_contacts = []

    for contact in contacts:

        try:

            validated_contact = ExcelContact(
                **contact
            )

            # Your current HRContactsV2.email is
            # nullable=False, so at least one email
            # is required.

            if not validated_contact.emails:

                errors.append(
                    {
                        "name": validated_contact.name,
                        "error": (
                            "No valid email address "
                            "found for contact."
                        ),
                    }
                )

                continue

            validated_contacts.append(
                validated_contact
            )

        except ValidationError as exc:

            errors.append(
                {
                    "name": contact.get("name"),
                    "error": exc.errors(),
                }
            )

    return (
        validated_contacts,
        errors,
    )


# ============================================================
# Find existing contact
# ============================================================

async def find_existing_contact(
    contact: ExcelContact,
    db: AsyncSession,
):

    # Search using any email belonging to the contact.

    for email in contact.emails:

        # ----------------------------------------------------
        # Search normalized email table
        # ----------------------------------------------------

        result = await db.execute(
            select(HRContactEmail).where(
                HRContactEmail.email == email
            )
        )

        existing_email = result.scalar_one_or_none()

        if existing_email:

            # We deliberately run a SECOND query here instead of
            # accessing `existing_email.contact` (the relationship).
            #
            # AsyncSession does not support implicit lazy-loading --
            # touching an unloaded relationship attribute without an
            # explicit await raises `MissingGreenlet`. Querying
            # HRContactsV2 directly by id avoids that trap entirely.

            result = await db.execute(
                select(HRContactsV2).where(
                    HRContactsV2.id == existing_email.contact_id
                )
            )

            return result.scalar_one_or_none()

        # ----------------------------------------------------
        # Search old HRContactsV2.email column
        # ----------------------------------------------------

        result = await db.execute(
            select(HRContactsV2).where(
                HRContactsV2.email == email
            )
        )

        existing_contact = result.scalar_one_or_none()

        if existing_contact:

            return existing_contact

    return None


# ============================================================
# Save contacts
# ============================================================

async def save_contacts(
    contacts: list[ExcelContact],
    db: AsyncSession,
):

    created_contacts = 0
    existing_contacts = 0
    emails_added = 0
    phones_added = 0
    save_errors = []

    for contact_data in contacts:

        # ----------------------------------------------------
        # Each contact gets its own SAVEPOINT.
        #
        # If saving this contact fails, only this contact's
        # changes are rolled back -- everything already
        # committed to earlier savepoints in this loop, and
        # the outer transaction itself, are unaffected.
        # ----------------------------------------------------

        try:

            # `async with` is required here (not plain `with`) --
            # AsyncSession.begin_nested() returns an async context
            # manager. Using plain `with` would raise immediately.

            async with db.begin_nested():

                local_created = 0
                local_existing = 0
                local_emails = 0
                local_phones = 0

                # ------------------------------------------------
                # Find existing contact
                # ------------------------------------------------

                contact = await find_existing_contact(
                    contact_data,
                    db,
                )

                # =================================================
                # Existing contact
                # =================================================

                if contact:

                    local_existing = 1

                # =================================================
                # New contact
                # =================================================

                else:

                    # First email becomes the legacy
                    # primary email.

                    primary_email = (
                        contact_data.emails[0]
                    )

                    # Phone is optional.
                    #
                    # If no phone exists, this becomes None.

                    primary_phone = (
                        contact_data.phones[0]
                        if contact_data.phones
                        else None
                    )

                    contact = HRContactsV2(
                        name=contact_data.name,
                        email=primary_email,
                        phone=primary_phone,
                        company=contact_data.company,
                        title=contact_data.position,
                    )

                    db.add(contact)

                    # Get generated contact.id
                    await db.flush()

                    local_created = 1

                # =================================================
                # Emails
                # =================================================

                for index, email in enumerate(
                    contact_data.emails
                ):

                    result = await db.execute(
                        select(HRContactEmail).where(
                            HRContactEmail.email == email
                        )
                    )

                    existing_email = result.scalar_one_or_none()

                    if existing_email:

                        continue

                    db.add(
                        HRContactEmail(
                            contact_id=contact.id,
                            email=email,
                            is_primary=(
                                index == 0
                            ),
                        )
                    )

                    local_emails += 1

                # =================================================
                # Phones
                # =================================================

                for index, phone in enumerate(
                    contact_data.phones
                ):

                    result = await db.execute(
                        select(HRContactPhone).where(
                            HRContactPhone.phone == phone
                        )
                    )

                    existing_phone = result.scalar_one_or_none()

                    if existing_phone:

                        continue

                    db.add(
                        HRContactPhone(
                            contact_id=contact.id,
                            phone=phone,
                            is_primary=(
                                index == 0
                            ),
                        )
                    )

                    local_phones += 1

            # Reached only if the savepoint block above committed
            # without raising -- safe to fold the local counts into
            # the running totals now.

            created_contacts += local_created
            existing_contacts += local_existing
            emails_added += local_emails
            phones_added += local_phones

        except Exception as exc:

            # The savepoint already rolled back this contact's
            # own changes. The outer transaction (and every
            # previously saved contact) is untouched, so we just
            # record the failure and move on to the next contact.

            save_errors.append(
                {
                    "name": contact_data.name,
                    "error": f"Failed to save contact: {exc}",
                }
            )

            continue

    # ----------------------------------------------------
    # Commit everything that succeeded
    # ----------------------------------------------------

    try:

        await db.commit()

    except Exception:

        await db.rollback()

        raise

    return {
        "status": "success",
        "created_contacts": created_contacts,
        "existing_contacts": existing_contacts,
        "emails_added": emails_added,
        "phones_added": phones_added,
        "save_errors": save_errors,
    }


# ============================================================
# Main service
# ============================================================

async def process_hr_contacts_file(
    contents: bytes,
    filename: str,
    db: AsyncSession,
):

    extension = get_file_extension(
        filename
    )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "Unsupported file format. "
            "Supported formats: "
            + ", ".join(
                sorted(ALLOWED_EXTENSIONS)
            )
        )

    # --------------------------------------------------------
    # Read spreadsheet
    # --------------------------------------------------------

    df = read_upload_file(
        contents,
        filename,
    )

    # --------------------------------------------------------
    # Parse and validate
    # --------------------------------------------------------

    (
        contacts,
        errors,
    ) = build_contacts_from_excel(
        df
    )

    # --------------------------------------------------------
    # Don't partially insert invalid files
    # --------------------------------------------------------

    if not contacts:

        return {
            "status": "validation_failed",
            "file_name": filename,
            "file_type": extension,
            "total_rows": len(df),
            "valid_contacts": 0,
            "created_contacts": 0,
            "emails_added": 0,
            "phones_added": 0,
            "errors": errors,
        }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    result = await save_contacts(
        contacts,
        db,
    )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    # Errors can come from two independent stages:
    #   - parsing/validation errors (rows dropped before saving)
    #   - save_errors (contacts that failed their own SAVEPOINT
    #     during save_contacts, see there for details)

    save_errors = result.pop("save_errors", [])
    all_errors = errors + save_errors

    result.update(
        {
            "status": (
                "partial_success"
                if all_errors
                else "success"
            ),
            "file_name": filename,
            "file_type": extension,
            "total_rows": len(df),
            "valid_contacts": len(contacts),
            "skipped_contacts": len(all_errors),
            "errors": all_errors,
        }
    )

    return result