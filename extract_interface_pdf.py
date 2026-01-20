#!/usr/bin/env python3
"""Extract signature-related pages from Interface Design PDF"""

import pdfplumber

pdf_path = r'C:\Users\user\Downloads\Interface+Design+for+EFRIS+v23.4-en.pdf'
keywords = ['signature', 'sign(', 'RSA', 'hash', 'SHA', 'MD5', 'PKCS', 'encrypt', 'T104', 'T101', 'T103']

try:
    with pdfplumber.open(pdf_path) as pdf:
        found_pages = []
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if text:
                    text_lower = text.lower()
                    if any(kw.lower() in text_lower for kw in keywords):
                        found_pages.append((i+1, text))
            except:
                pass
        
        print(f'Found {len(found_pages)} pages with relevant keywords')
        
        # Save all relevant pages
        with open('pdf_interface_signatures.txt', 'w', encoding='utf-8') as f:
            for page_num, text in found_pages:
                f.write(f'\n=== PAGE {page_num} ===\n{text}\n')
        
        print('Saved to pdf_interface_signatures.txt')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
