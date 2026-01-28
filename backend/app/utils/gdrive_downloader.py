# backend/app/utils/gdrive_downloader.py
"""
Google Drive file downloader utility.
Downloads PDFs from public Google Drive shareable links.
"""

import re
import requests
from typing import Optional


def extract_file_id(gdrive_link: str) -> Optional[str]:
    """
    Extract Google Drive file ID from various link formats.
    
    Supported formats:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID&export=download
    
    Args:
        gdrive_link: Google Drive URL
        
    Returns:
        File ID if found, None otherwise
    """
    if not gdrive_link or not isinstance(gdrive_link, str):
        return None
    
    # Pattern 1: /file/d/FILE_ID/view or /file/d/FILE_ID
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', gdrive_link)
    if match:
        return match.group(1)
    
    # Pattern 2: ?id=FILE_ID or &id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', gdrive_link)
    if match:
        return match.group(1)
    
    # Pattern 3: /open?id=FILE_ID
    match = re.search(r'/open\?id=([a-zA-Z0-9_-]+)', gdrive_link)
    if match:
        return match.group(1)
    
    return None


def download_from_gdrive(link: str, timeout: int = 60) -> bytes:
    """
    Download file from public Google Drive link.
    
    Args:
        link: Google Drive shareable link (must be publicly accessible)
        timeout: Download timeout in seconds (default: 60)
    
    Returns:
        PDF file content as bytes
    
    Raises:
        ValueError: If file ID cannot be extracted or file is not a PDF
        requests.HTTPError: If download fails (file private, not found, etc.)
        requests.Timeout: If download exceeds timeout
    """
    # Extract file ID
    file_id = extract_file_id(link)
    if not file_id:
        raise ValueError(f"Invalid Google Drive link format: {link}")
    
    # Construct direct download URL
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Attempt download with streaming
    session = requests.Session()
    response = session.get(download_url, timeout=timeout, stream=True)
    
    # Handle virus scan warning for large files
    if 'download_warning' in response.text or 'confirm=' in response.url:
        # Extract confirmation token from cookies
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                confirm_url = f"{download_url}&confirm={value}"
                response = session.get(confirm_url, timeout=timeout, stream=True)
                break
    
    # Check for errors
    response.raise_for_status()
    
    # Download content
    content = response.content
    
    # Verify it's a PDF file
    if not content.startswith(b'%PDF'):
        # Check if we got an HTML error page
        if content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            raise ValueError(
                f"Cannot access file (link may be private or require permission). "
                f"Ensure file has 'Anyone with the link' viewing permission."
            )
        raise ValueError(f"Downloaded file is not a valid PDF")
    
    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size:
        raise ValueError(f"File too large ({len(content) / 1024 / 1024:.1f}MB). Maximum: 10MB")
    
    return content


def validate_gdrive_link(link: str) -> tuple[bool, str]:
    """
    Validate if link is a proper Google Drive link.
    
    Args:
        link: URL string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not link or not isinstance(link, str):
        return False, "Link is empty or invalid"
    
    link = link.strip()
    
    # Check if it's a Google Drive domain
    if 'drive.google.com' not in link:
        return False, "Not a Google Drive link"
    
    # Check if we can extract file ID
    file_id = extract_file_id(link)
    if not file_id:
        return False, "Cannot extract file ID from link"
    
    # Check file ID format (typical length and characters)
    if len(file_id) < 10:
        return False, "File ID appears invalid (too short)"
    
    return True, ""
