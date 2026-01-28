# parser_engine/extractor.py
import re
from typing import Dict, List, Any

# Indian phone number regex: 10 digits starting with 6-9, optionally prefixed with +91
# Matches: 9876543210, +919876543210, +91 9876543210, +91-9876543210
PHONE_REGEX = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}\b")

# Enhanced email regex patterns
# Primary: standard email with word boundaries
EMAIL_REGEX = re.compile(
    r'\b[a-zA-Z0-9][a-zA-Z0-9._+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}\b',
    re.IGNORECASE
)
# Fallback for emails broken by PDF artifacts (spaces around @ and .)
EMAIL_ARTIFACT_REGEX = re.compile(
    r'[a-zA-Z0-9._+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}',
    re.IGNORECASE
)

LINKEDIN_REGEX = re.compile(r"(linkedin\.com\/in\/[A-Za-z0-9\-\_]+)", re.IGNORECASE)
GITHUB_REGEX = re.compile(r"(github\.com\/[A-Za-z0-9\-\_]+)", re.IGNORECASE)

SECTION_HEADERS = [
    r"education",
    r"experience",
    r"work experience",
    r"projects?",
    r"skills?",
    r"certifications?",
    r"achievements?",
    r"summary",
    r"objective",
]

def _is_valid_indian_phone(phone_str: str) -> bool:
    """Validate that a phone number is a valid Indian mobile number.
    
    Args:
        phone_str: Phone number string to validate
        
    Returns:
        True if valid Indian mobile number, False otherwise
    """
    if not phone_str:
        return False
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_str)
    
    # Handle different formats:
    # 1. 10 digits: 9876543210
    # 2. +91 + 10 digits: +919876543210
    # 3. 91 + 10 digits: 919876543210 (treat as +91)
    
    if cleaned.startswith('+91'):
        # +919876543210 -> should be 13 chars (+, 9, 1, and 10 digits)
        if len(cleaned) == 13:
            return cleaned[3] in '6789'
    elif cleaned.startswith('91') and len(cleaned) == 12:
        # 919876543210 -> should be 12 chars (9, 1, and 10 digits)
        return cleaned[2] in '6789'
    elif len(cleaned) == 10:
        # 9876543210 -> should be exactly 10 chars
        return cleaned[0] in '6789'
    
    return False


def _is_valid_email(email_str: str) -> bool:
    """Validate email format and filter out common false positives.
    
    Args:
        email_str: Email string to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    email = email_str.lower().strip()
    
    # Must contain @ and at least one dot after @
    if '@' not in email or '.' not in email.split('@')[1]:
        return False
    
    # Split into local and domain parts
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local, domain = parts
    
    # Local part validation
    if not local or len(local) < 1 or len(local) > 64:
        return False
    
    # Domain validation
    if not domain or len(domain) < 3 or len(domain) > 255:
        return False
    
    # Domain must have at least one dot
    if '.' not in domain:
        return False
    
    # TLD (top-level domain) must be at least 2 characters
    tld = domain.split('.')[-1]
    if len(tld) < 2:
        return False
    
    # Filter out common false positives
    # Avoid emails with multiple dots in a row
    if '..' in email:
        return False
    
    # Avoid emails ending/starting with dots or special chars
    if email[0] in '.-_+' or email[-1] in '.-_+':
        return False
    
    # Check for reasonable TLDs
    common_tlds = ['com', 'org', 'net', 'edu', 'gov', 'in', 'co', 'io', 'dev', 'app', 
                   'tech', 'info', 'ai', 'me', 'us', 'uk', 'ca', 'au', 'de', 'fr']
    if tld not in common_tlds and len(tld) > 6:
        return False
    
    return True


def find_contact_info(text: str) -> Dict[str, Any]:
    contact = {"phones": [], "emails": [], "linkedin": None, "github": None}
    
    # Normalize text: replace common PDF extraction artifacts
    # Sometimes PDFs extract with weird spacing or line breaks in emails
    # First, normalize Unicode spaces and other whitespace characters
    text_normalized_unicode = text.replace('\u00A0', ' ')  # Non-breaking space
    text_normalized_unicode = text_normalized_unicode.replace('\u2009', ' ')  # Thin space
    text_normalized_unicode = text_normalized_unicode.replace('\u202F', ' ')  # Narrow no-break space
    
    # Fix emails that might be broken across lines
    # Remove line breaks and spaces before @ and around domain extensions
    text_fixed = re.sub(r'([a-zA-Z0-9._+-])\s+@\s*([a-zA-Z0-9.-]+)', r'\1@\2', text_normalized_unicode, flags=re.IGNORECASE)
    text_fixed = re.sub(r'([a-zA-Z0-9._+-]@[a-zA-Z0-9.-]+)\s+\.\s*([a-zA-Z]+)', r'\1.\2', text_fixed, flags=re.IGNORECASE)
    normalized_text = re.sub(r'\s+', ' ', text_fixed)  # Normalize remaining whitespace to single spaces
    
    # Extract and validate emails
    emails_set = set()
    
    # Try primary regex on all text variants
    for text_variant in [text, text_normalized_unicode, normalized_text, text_fixed]:
        for m in EMAIL_REGEX.finditer(text_variant):
            email = m.group(0).strip()
            # Clean up any remaining artifacts
            email = re.sub(r'\s+', '', email)  # Remove any internal spaces
            if _is_valid_email(email):
                emails_set.add(email.lower())  # Normalize to lowercase
    
    # Try artifact-aware regex for broken emails
    for text_variant in [text, text_normalized_unicode, text_fixed]:
        for m in EMAIL_ARTIFACT_REGEX.finditer(text_variant):
            email = m.group(0).strip()
            email = re.sub(r'\s+', '', email)  # Remove spaces
            if _is_valid_email(email):
                emails_set.add(email.lower())
    
    contact["emails"] = sorted(list(emails_set))  # Sort for consistency
    
    # Extract and validate phone numbers
    phone_matches = PHONE_REGEX.finditer(normalized_text)
    valid_phones = []
    for match in phone_matches:
        phone = match.group(0).strip()
        if _is_valid_indian_phone(phone):
            # Normalize phone format (add +91 if not present)
            cleaned = re.sub(r'[^\d+]', '', phone)
            if not cleaned.startswith('+'):
                # Format as +91XXXXXXXXXX for consistency
                phone = f"+91{cleaned}"
            valid_phones.append(phone)
    
    contact["phones"] = list(set(valid_phones))  # Remove duplicates
    
    linkedin = LINKEDIN_REGEX.search(text) or LINKEDIN_REGEX.search(normalized_text)
    github = GITHUB_REGEX.search(text) or GITHUB_REGEX.search(normalized_text)
    if linkedin:
        contact["linkedin"] = linkedin.group(0)
    if github:
        contact["github"] = github.group(0)
    return contact

def split_sections(text: str) -> Dict[str, str]:
    """
    Improved heuristic split: find likely headers and return header->block mapping.
    Handles multi-column layouts by cleaning up jumbled text first.
    """
    # Pre-process: clean up jumbled text from multi-column layouts
    text = _clean_jumbled_text(text)
    
    lines = [l.rstrip() for l in text.splitlines()]
    header_positions = []
    
    # More flexible header detection
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        low = line_stripped.lower().rstrip(":").strip()
        # Remove common bullet / markdown markers like '#', '-', '•'
        low = re.sub(r'^[#\-\*\u2022]+\s*', '', low)
        # Remove common prefixes/suffixes
        low_clean = re.sub(r'^(section|part)\s+', '', low)
        low_clean = re.sub(r'\s+(section|part)$', '', low_clean)
        low_clean = low_clean.strip()
        
        # direct header match (exact or starts with)
        matched = False
        for h in SECTION_HEADERS:
            # Exact match
            if low_clean == h:
                header_positions.append((i, h))
                matched = True
                break
            # Starts with header
            elif low_clean.startswith(h + " ") or low_clean.startswith(h + ":"):
                header_positions.append((i, h))
                matched = True
                break
            # Ends with header
            elif low_clean.endswith(" " + h):
                header_positions.append((i, h))
                matched = True
                break
            # Header is contained (for cases like "EDUCATION" matching "education")
            elif h in low_clean and len(low_clean.split()) <= 3:
                header_positions.append((i, h))
                matched = True
                break
        
        if not matched:
            # More flexible heuristic: ALL CAPS single words that match headers
            if line_stripped.isupper() and len(line_stripped.split()) <= 2:
                low_upper = line_stripped.lower().strip()
                for h in SECTION_HEADERS:
                    if h == low_upper or low_upper.startswith(h):
                        header_positions.append((i, h))
                        matched = True
                        break
            
            # Title case or single word headers
            if not matched:
                words = line_stripped.split()
                if (1 <= len(words) <= 5 and 
                    (line_stripped.isupper() or line_stripped.istitle() or 
                     (len(words) == 1 and len(line_stripped) <= 20))):
                    # Additional check: next line should have content
                    if i + 1 < len(lines) and len(lines[i + 1].strip()) > 5:
                        # Check if it matches any header when lowercased
                        low_check = line_stripped.lower().strip()
                        for h in SECTION_HEADERS:
                            if h == low_check or low_check.startswith(h):
                                header_positions.append((i, h))
                                matched = True
                                break
                        if not matched:
                            header_positions.append((i, low_clean))

    if not header_positions:
        return {"full": text}

    # Remove duplicate headers (same position or very close)
    header_positions = _deduplicate_headers(header_positions)
    header_positions.append((len(lines), "end"))
    
    sections = {}
    for idx in range(len(header_positions)-1):
        start_i, header = header_positions[idx]
        next_i, _ = header_positions[idx+1]
        block = "\n".join(lines[start_i+1:next_i]).strip()
        key = header.strip() or f"section_{idx}"
        sections[key] = block
    return sections


def _clean_jumbled_text(text: str) -> str:
    """
    Clean up text that may be jumbled from multi-column layouts.
    Attempts to reorder and fix common issues.
    """
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append("")
            continue
        
        # Detect if line has text that looks jumbled (very short fragments)
        words = line.split()
        
        # If line has many single-character "words" or very short fragments, might be jumbled
        if len(words) > 10:
            # Check for patterns like "word1 word2 word3" that might be from columns
            # Try to detect and fix common jumbling patterns
            pass  # Keep as-is for now, pdfminer should handle layout
        
        # Remove excessive whitespace
        line = re.sub(r'\s+', ' ', line)
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def _deduplicate_headers(header_positions: List[tuple]) -> List[tuple]:
    """Remove duplicate or very close header positions."""
    if not header_positions:
        return []
    
    # Sort by position
    sorted_headers = sorted(header_positions, key=lambda x: x[0])
    deduplicated = [sorted_headers[0]]
    
    for pos, header in sorted_headers[1:]:
        last_pos, _ = deduplicated[-1]
        # If headers are more than 2 lines apart, keep both
        if pos - last_pos > 2:
            deduplicated.append((pos, header))
        # Otherwise, prefer the one that matches known headers better
        elif any(h in header.lower() for h in SECTION_HEADERS):
            deduplicated[-1] = (pos, header)
    
    return deduplicated

def extract_skills(text: str) -> List[str]:
    lowered = text.lower()
    skills = []
    # Try to locate a skills section
    m = re.search(r"skills[:\n]\s*([\s\S]{1,400})", lowered)
    if m:
        block = m.group(1)
        parts = re.split(r"[,\|\•\-\n;]+", block)
        for p in parts:
            p = p.strip()
            if 1 < len(p) <= 60:
                skills.append(p)
        return list(dict.fromkeys([s for s in skills if s]))
    # fallback: pull common tech tokens
    candidates = re.findall(r"\b(java|python|c\+\+|c#|javascript|react|node|sql|postgres|mysql|aws|docker|kubernetes|tensorflow|pytorch)\b", text, flags=re.I)
    return list(dict.fromkeys([c.lower() for c in candidates]))

def extract_experience_blocks(sections: Dict[str, str]) -> List[Dict[str, Any]]:
    exp_blocks = []
    for k, block in sections.items():
        if "experience" in k or "work experience" in k:
            bullets = re.split(r"\n(?:\s*[-•\*]|\s*\d+\.)\s*", block)
            bullets = [b.strip() for b in bullets if b.strip()]
            exp_blocks.append({"section": k, "raw": block, "bullets": bullets})
    return exp_blocks

def extract_projects(sections: Dict[str, str]) -> List[Dict[str, Any]]:
    projects = []
    for k, block in sections.items():
        if "project" in k:
            items = [it.strip() for it in re.split(r"\n\s*\n+|\n[-•\*]\s*", block) if it.strip()]
            for it in items:
                projects.append({"title_and_desc": it})
    return projects

def extract_all(raw_text: str) -> Dict[str, Any]:
    contact = find_contact_info(raw_text)
    sections = split_sections(raw_text)
    skills = extract_skills(raw_text)
    experiences = extract_experience_blocks(sections)
    projects = extract_projects(sections)
    return {
        "contact": contact,
        "sections_found": list(sections.keys()),
        "skills": skills,
        "experience_blocks": experiences,
        "projects": projects,
        "raw_text": raw_text,  # Include raw text for scoring functions
        "raw_text_length": len(raw_text),
    }
