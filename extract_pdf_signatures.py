#!/usr/bin/env python3
"""Extract signature generation details from EFRIS API PDFs"""

import pdfplumber
from pathlib import Path

# PDF file paths
pdf_files = {
    "api_v3": r"C:\Users\user\Downloads\How+to+use+the+System+to+System+API_V3.pdf",
    "interface_design": r"C:\Users\user\Downloads\Interface+Design+for+EFRIS+v23.4-en.pdf",
}

# Search keywords
keywords = [
    "signature", "RSA", "hash", "SHA", "MD5", "encryptCode",
    "sign", "sign()", "signContent", "payload", "content",
    "base64", "Base64", "padding", "PKCS", "algorithm",
    "T101", "T103", "T104", "interface", "encrypt",
    "sign data", "signed", "signing", "digital signature"
]

def extract_pdf_content(pdf_path):
    """Extract all text from PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- PAGE {page_num} ---\n{text}"
            return full_text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def find_relevant_sections(text, keywords):
    """Find sections containing relevant keywords"""
    if not text:
        return {}
    
    lines = text.split('\n')
    relevant_sections = {}
    
    for keyword in keywords:
        matches = []
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                # Get context: 5 lines before and after
                start = max(0, i - 5)
                end = min(len(lines), i + 6)
                context = '\n'.join(lines[start:end])
                matches.append((i, context))
        
        if matches:
            relevant_sections[keyword] = matches
    
    return relevant_sections

def main():
    for name, pdf_path in pdf_files.items():
        if not Path(pdf_path).exists():
            print(f"File not found: {pdf_path}")
            continue
        
        content = extract_pdf_content(pdf_path)
        if content:
            # Save to file for reference
            output_file = f"pdf_content_{name}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Extracted {len(content)} characters to: {output_file}")

if __name__ == "__main__":
    main()
