# parser_engine/parser.py
from pathlib import Path
from typing import Tuple, List, Dict, Any
from pypdf import PdfReader
try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTChar, LTTextBox, LTTextLine
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
import re

def parse_pdf_to_text(pdf_path: Path) -> Tuple[str, dict]:
    """
    Extract raw text from a PDF with improved layout handling.
    Uses pdfminer.six for layout-aware extraction to handle multi-column layouts.
    Returns (text, diagnostics) where diagnostics includes font info and layout hints.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Try pdfminer first for better layout handling
    try:
        return _parse_with_pdfminer(pdf_path)
    except Exception as e:
        # Fallback to pypdf if pdfminer fails
        return _parse_with_pypdf(pdf_path, str(e))


def _parse_with_pdfminer(pdf_path: Path) -> Tuple[str, dict]:
    """Extract text using pdfminer.six with layout analysis."""
    if not PDFMINER_AVAILABLE:
        raise ImportError("pdfminer.six not available")
    
    pages_text = []
    all_font_sizes = []
    all_font_names = []
    layout_issues = []
    page_count = 0

    # Extract clickable links (e.g., GitHub/LinkedIn URLs) using pypdf annotations
    links = _extract_links_with_pypdf(pdf_path)

    for page_layout in extract_pages(str(pdf_path)):
        page_count += 1
        page_text_blocks = []
        page_fonts = []
        
        # Extract text blocks with their positions
        text_blocks = []
        for element in page_layout:
            if isinstance(element, LTTextBox):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        # Get text and position
                        text = text_line.get_text().strip()
                        if text:
                            x0, y0, x1, y1 = text_line.bbox
                            # Collect font info
                            fonts_in_line = []
                            for char in text_line:
                                if isinstance(char, LTChar):
                                    font_size = round(char.height, 1)
                                    font_name = char.fontname if hasattr(char, 'fontname') else None
                                    if font_size > 0:
                                        fonts_in_line.append((font_size, font_name))
                                        all_font_sizes.append(font_size)
                                        if font_name:
                                            all_font_names.append(font_name)
                            
                            text_blocks.append({
                                'text': text,
                                'x0': x0,
                                'y0': y0,
                                'x1': x1,
                                'y1': y1,
                                'fonts': fonts_in_line
                            })
        
        # Detect multi-column layout
        if len(text_blocks) > 10:
            x_positions = [b['x0'] for b in text_blocks]
            # Check if text is spread across multiple columns
            x_median = sorted(x_positions)[len(x_positions) // 2]
            left_column = [b for b in text_blocks if b['x0'] < x_median]
            right_column = [b for b in text_blocks if b['x0'] >= x_median]
            
            if len(left_column) > 5 and len(right_column) > 5:
                # Multi-column detected - sort by Y position (top to bottom) within each column
                left_column.sort(key=lambda b: -b['y0'])  # Top to bottom
                right_column.sort(key=lambda b: -b['y0'])
                
                # Merge columns: alternate or process left then right
                merged_blocks = []
                max_len = max(len(left_column), len(right_column))
                for i in range(max_len):
                    if i < len(left_column):
                        merged_blocks.append(left_column[i])
                    if i < len(right_column):
                        merged_blocks.append(right_column[i])
                
                text_blocks = merged_blocks
                layout_issues.append(f"Multi-column layout detected on page {page_count}")
        
        # Sort by Y position (top to bottom) if not multi-column
        if not layout_issues or page_count == 1:
            text_blocks.sort(key=lambda b: -b['y0'])
        
        # Build page text
        page_lines = []
        for block in text_blocks:
            page_lines.append(block['text'])
        
        pages_text.append('\n'.join(page_lines))
    
    full_text = '\n\n'.join(pages_text).strip()
    
    # Calculate margins from first page layout (if available)
    margins = None
    if page_count > 0 and text_blocks:
        try:
            # Get first page layout
            first_page = next(extract_pages(str(pdf_path)))
            margins = _calculate_margins(text_blocks, first_page)
        except Exception:
            pass  # Margin calculation failed, continue without it
    
    # Analyze font consistency
    font_consistency_score = _analyze_font_consistency(all_font_sizes, all_font_names)
    
    diagnostics = {
        "page_count": page_count,
        "font_sizes_detected": len(set(round(f, 1) for f in all_font_sizes if f > 0)),
        "unique_font_names": len(set(all_font_names)),
        "font_consistency": font_consistency_score,
        "layout_issues": layout_issues,
        "margins": margins,  # NEW: margin data
        "extraction_method": "pdfminer",
        "links": links,
    }
    
    return full_text, diagnostics


def _calculate_margins(text_blocks: List[Dict], page_layout) -> Dict[str, float]:
    """
    Calculate margins from PDF layout.
    Returns dict with top, bottom, left, right margins in points (72 points = 1 inch).
    """
    if not text_blocks:
        return None
    
    # Get page dimensions
    page_width = page_layout.width
    page_height = page_layout.height
    
    # Find content boundaries
    min_x = min(b['x0'] for b in text_blocks)
    max_x = max(b['x1'] for b in text_blocks)
    min_y = min(b['y0'] for b in text_blocks)
    max_y = max(b['y1'] for b in text_blocks)
    
    # Calculate margins (in points)
    margins = {
        'left': round(min_x, 2),
        'right': round(page_width - max_x, 2),
        'top': round(page_height - max_y, 2),
        'bottom': round(min_y, 2),
        'page_width': round(page_width, 2),
        'page_height': round(page_height, 2),
    }
    
    return margins


def _parse_with_pypdf(pdf_path: Path, error_msg: str) -> Tuple[str, dict]:
    """Fallback to pypdf extraction."""
    reader = PdfReader(str(pdf_path))
    texts = []
    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception as e:
            page_text = f"[ERROR extracting page {i}: {e}]"
        texts.append(page_text)
    
    full_text = "\n\n".join(texts).strip()
    links = _extract_links_with_pypdf(pdf_path)
    diagnostics = {
        "page_count": len(reader.pages),
        "extraction_method": "pypdf",
        "pdfminer_error": error_msg,
        "font_consistency": None,
        "links": links,
    }
    return full_text, diagnostics


def _analyze_font_consistency(font_sizes: List[float], font_names: List[str]) -> Dict[str, Any]:
    """Analyze font consistency and return metrics."""
    if not font_sizes:
        return {"score": 0, "issues": ["No font information detected"]}
    
    # Count unique font sizes
    unique_sizes = set(round(f, 1) for f in font_sizes if f > 0)
    
    # Count font size occurrences
    size_counts = {}
    for size in font_sizes:
        rounded = round(size, 1)
        size_counts[rounded] = size_counts.get(rounded, 0) + 1
    
    # Find most common font size (likely body text)
    if size_counts:
        most_common_size = max(size_counts.items(), key=lambda x: x[1])[0]
        total_chars = sum(size_counts.values())
        most_common_pct = (size_counts[most_common_size] / total_chars) * 100
        
        issues = []
        score = 100
        
        # Too many different font sizes = inconsistency
        if len(unique_sizes) > 5:
            issues.append(f"Too many font sizes detected ({len(unique_sizes)}). Use 2-3 consistent sizes.")
            score -= 30
        
        # If most common font is less than 60% of text, inconsistency
        if most_common_pct < 60:
            issues.append(f"Font sizes are inconsistent. Main font used only {most_common_pct:.1f}% of the time.")
            score -= 20
        
        # Check font name consistency
        if font_names:
            unique_fonts = set(font_names)
            if len(unique_fonts) > 3:
                issues.append(f"Multiple font families detected ({len(unique_fonts)}). Use 1-2 consistent fonts.")
                score -= 15
        
        return {
            "score": max(0, score),
            "unique_sizes": len(unique_sizes),
            "most_common_size": most_common_size,
            "most_common_pct": round(most_common_pct, 1),
            "issues": issues
        }
    
    return {"score": 0, "issues": ["Could not analyze fonts"]}


def _extract_links_with_pypdf(pdf_path: Path) -> List[str]:
    """Extract clickable link URLs (e.g., GitHub, LinkedIn) from PDF annotations."""
    links: List[str] = []
    try:
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            for annot in annots:
                try:
                    obj = annot.get_object()
                    if "/A" in obj and "/URI" in obj["/A"]:
                        uri = obj["/A"]["/URI"]
                        if isinstance(uri, str):
                            links.append(uri)
                except Exception:
                    # Ignore broken annotations
                    continue
    except Exception:
        # If anything goes wrong, just return what we have (or empty list)
        pass

    # Deduplicate while preserving order
    seen = set()
    deduped_links: List[str] = []
    for url in links:
        if url not in seen:
            seen.add(url)
            deduped_links.append(url)
    return deduped_links
