#!/usr/bin/env python3
"""
Scan all source PDFs for formatting issues like incorrect roman numeral bullets
or other problematic formatting in special sections.
"""

import pypdf
import os
import re

def scan_pdfs_for_issues():
    """Scan all source PDFs for numbering and formatting issues."""
    
    source_dir = "/Users/aiyshwarya/Documents/Portfolio/Project_Explanation_Detailed copy"
    
    print("=== SCANNING ALL SOURCE PDFs FOR NUMBERING ISSUES ===\n")
    
    issues_by_pdf = {}
    
    for filename in sorted(os.listdir(source_dir)):
        if not filename.endswith(".pdf"):
            continue
        
        pdf_path = os.path.join(source_dir, filename)
        
        try:
            reader = pypdf.PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            issues = []
            
            # Pattern 1: Look for "i)" "ii)" "iii)" at start of lines after section headers
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and re.match(r'^[ivxlcdm]+\)\s+', stripped):
                    # Found roman numeral format
                    # Check if it's in a special section
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        context = f"After '{prev_line[:40]}'" if prev_line else "Start of section"
                        issues.append({
                            'type': 'roman_numeral',
                            'line': stripped[:80],
                            'context': context
                        })
            
            # Pattern 2: Check for Business logic formatting
            for i, line in enumerate(lines):
                if 'Business logic' in line.lower():
                    # Get next few lines
                    for j in range(i+1, min(i+6, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and re.match(r'^[ivxlcdm]+\)\s+', next_line):
                            issues.append({
                                'type': 'business_logic_roman',
                                'line': next_line[:80],
                                'context': 'Under "Business logic" section'
                            })
            
            if issues:
                issues_by_pdf[filename] = issues
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            issues_by_pdf[filename] = [{'type': 'error', 'error': str(e)}]
    
    # Report findings
    if not issues_by_pdf:
        print("✓ No roman numeral numbering issues found in any PDFs.\n")
    else:
        print("⚠ ISSUES FOUND:\n")
        for filename in sorted(issues_by_pdf.keys()):
            issues = issues_by_pdf[filename]
            print(f"  [{filename}]")
            for issue in issues:
                if issue['type'] == 'error':
                    print(f"    Error: {issue.get('error')}")
                else:
                    print(f"    {issue['type']}: {issue['line']}")
                    print(f"      Context: {issue['context']}")
            print()

if __name__ == "__main__":
    scan_pdfs_for_issues()
