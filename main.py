import re
import pdfplumber
import requests

# --- Configuration ---
# EPFO UAN Verification API endpoint (replace with actual URL)
EPFO_API_URL = "https://api.epfo.gov.in/uan/verify"
API_KEY = "YOUR_API_KEY_HERE"  # if required

# --- Field Extraction Patterns ---
FIELD_PATTERNS = {
    "employee_name":      r"(?i)\b(?:Employee\s*Name|Name\s*of\s*Employee|Emp\.?\s*Name)\s*[:\-]?\s*(.+)",
    "date_of_joining":    r"(?i)\b(?:Date\s+of\s+Joining|Date\s+Joined|DOJ|Joining\s+Date|Start\s+Date)\s*[:\-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    "designation":       r"(?i)\b(?:Designation|Job\s+Title|Position|Post|Employee\s+Grade)\s*[:\-]?\s*(.+)",
    "location":          r"(?i)\b(?:Office\s+Location|Work\s+Location|Place\s+of\s+Posting|Location|Work\s+City)\s*[:\-]?\s*(.+)",
    "pf_number":         r"(?i)\b(?:PF\s*(?:No|Number|#)?|EPF\s*(?:A/c|Account|No)?)\s*[:\-]?\s*([\w\/\-\s]+)",
    "uan_number":        r"(?i)\b(?:UAN|Universal\s+Account\s+Number)\s*(?:No|Number)?\s*[:\-]?\s*(\d{12})",
    "gross_earnings":    r"(?i)\b(?:Gross\s+Earnings|Gross\s+Pay|Gross\s+Salary|Gross\s+Income|Total\s+Earnings)\s*[:\-]?\s*([\d,]+(?:\.\d+)?)",
    "gross_deductions":  r"(?i)\b(?:Gross\s+Deduction|Gross\s+Deductions|Total\s+Deduction|Total\s+Deductions|Deductions)\s*[:\-]?\s*([\d,]+(?:\.\d+)?)"
}


def extract_text_from_pdf(path: str) -> str:
    """
    Extracts all text from a PDF file using pdfplumber.
    """
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


def extract_fields(text: str) -> dict:
    """
    Uses regex patterns to extract fields from the payslip text.
    """
    data = {}
    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text)
        data[key] = match.group(1).strip() if match else None
    return data


def fetch_epfo_history(uan: str) -> dict:
    """
    Calls the EPFO UAN API to retrieve employee EPF history.

    Returns the JSON response as a dictionary.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {API_KEY}"
    }
    payload = {'uan': uan}
    response = requests.post(EPFO_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def main(payslip_path: str):
    # 1. Extract text
    raw_text = extract_text_from_pdf(payslip_path)

    # 2. Parse payslip fields
    payslip_data = extract_fields(raw_text)
    print("Extracted Payslip Data:")
    for k, v in payslip_data.items():
        print(f"  {k}: {v}")

    # 3. If UAN found, fetch EPFO history
    uan = payslip_data.get('uan')
    if uan:
        try:
            history = fetch_epfo_history(uan)
            print("\nEPFO History:")
            # Pretty print or process as needed
            print(history)
        except Exception as e:
            print(f"Failed to fetch EPFO history: {e}")
    else:
        print("UAN not found; skipping EPFO API call.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract payslip data and fetch EPFO history.")
    parser.add_argument('payslip_pdf', help='Path to the payslip PDF file')
    args = parser.parse_args()

    main(args.payslip_pdf)
