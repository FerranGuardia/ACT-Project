"""
Text cleaning utilities for scraped webnovel content.

Provides functions to clean and normalize text extracted from webnovel sites,
removing UI elements, HTML artifacts, and other unwanted content.
"""

import re
from typing import Optional


def clean_text(text: Optional[str]) -> str:
    """
    Clean scraped text from webnovel sites.

    Strategy:
    1. Remove HTML artifacts
    2. Remove UI elements (navigation, comments, etc.)
    3. Remove URLs, emails, social media
    4. Remove timestamps and dates
    5. Clean whitespace and formatting
    6. Filter out UI-only lines

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text ready for TTS processing

    Example:
        >>> raw = "<p>Chapter 1</p><div>Content here</div>"
        >>> clean_text(raw)
        'Chapter 1\\n\\nContent here'
    """
    if not text:
        return ""

    # Step 1: Remove HTML artifacts
    text = re.sub(r"<[^>]+>", "", text)  # HTML tags
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&quot;|&#\d+;", " ", text)  # HTML entities

    # Step 2: Remove concatenated UI patterns (always safe - these are never in dialogue)
    concatenated_ui_patterns = [
        r"LatestMost",
        r"MostOldest",
        r"LatestOldest",
        r"LikedOldest",
        r"[a-z](Latest|Most|Oldest)",  # Like "dOldest"
    ]
    for pattern in concatenated_ui_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Step 3: Remove entire UI blocks
    ui_block_patterns = [
        r"What\s+do\s+you\s+think\?.*?Total\s+Responses.*?Sort\s+by.*?",
        r"Total\s+Responses:?\s*\d+.*?Sort\s+by:?.*?(Latest|Most|Oldest|Liked).*?Add\s+a\s+(Comment|Post).*?",
        r"Add\s+a\s+Post.*?Loading.*?Load\s+More.*?",
        r"Reply\s+to.*?Submit\s+Reply.*?",
        r"\[?Thank\s+You\s+For\s+Your\s+Support!?\]?",
    ]
    for pattern in ui_block_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Step 4: Remove navigation elements
    navigation_patterns = [
        r"\bNext\s+Chapter\b",
        r"\bPrevious\s+Chapter\b",
        r"\bTable\s+of\s+Contents\b",
        r"\bTOC\b",
        r"\bAdvertisement\b",
        r"\bAd\s+\d+\b",
        r"\bClick\s+here\b",
        r"\bRead\s+more\b",
        r"\bPage\s+\d+\b",
        r"\d+\s*/\s*\d+",  # Pagination like "1 / 10"
        r"\bNovelBin\b|\bNovelFull\b|\bWebNovel\b|\bWuxiaWorld\b",
        r"\bRead\s+online\b|\bRead\s+free\b",
        r"\bUpdated\s+on\b|\bLast\s+updated\b",
        r"\bPlease\s+enable\s+JavaScript\b",
        r"\bEnable\s+JavaScript\b",
    ]
    for pattern in navigation_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Step 5: Remove URLs, emails, social media
    text = re.sub(r"http[s]?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"@\w+", "", text)  # Social mentions
    text = re.sub(r"#\w+", "", text)  # Hashtags

    # Step 6: Remove timestamps and dates
    text = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", "", text)  # Dates
    text = re.sub(r"\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?", "", text)  # Times

    # Step 7: Remove excessive separators
    text = re.sub(r"[=]{2,}", "", text)  # ===
    text = re.sub(r"[-]{3,}", "", text)  # ---
    text = re.sub(r"[_]{3,}", "", text)  # ___
    text = re.sub(r"[*]{3,}", "", text)  # ***
    text = re.sub(r"[~]{2,}", "", text)  # ~~~
    text = re.sub(r"×", "", text)  # UI multiplication symbol

    # Step 8: Context-aware removal of UI words
    context_aware_patterns = [
        (r"(Sort\s+by:?\s*)(Latest|Most|Oldest)\b", r"\1"),
        (r"Liked(\s*Oldest|\s*Add|\s*Post|\s*Comment|\s*Sort)", r"\1"),
        (r"\b(Latest|Most|Oldest)(\s*Add\s+a\s+Post|\s*Post\s+Comment|\s*Loading|\s*Load\s+More)", r"\2"),
    ]
    for pattern, replacement in context_aware_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Step 9: Remove repeated UI sequences at end of chapters
    text = re.sub(r"(LikedOldest\s*)+$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"((Latest|Most|Oldest)\s*){3,}$", "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Step 10: Line-by-line filtering (whitelist approach)
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Keep empty lines for paragraph breaks
        if not line:
            if cleaned_lines and cleaned_lines[-1]:  # Only if previous line wasn't empty
                cleaned_lines.append("")
            continue

        # Skip lines that are clearly UI elements
        ui_indicators = [
            r"Thank\s+You\s+For\s+Your\s+Support",
            r"What\s+do\s+you\s+think",
            r"Total\s+Responses",
            r"Sort\s+by",
            r"Add\s+a\s+(Post|Comment)",
            r"Post\s+Comment",
            r"Loading",
            r"Load\s+More",
            r"Reply\s+to",
            r"Submit\s+Reply",
            r"^Chapter\s+\d+$",  # Standalone "Chapter X" line
            r"^Next\s+Chapter$",
            r"^Previous\s+Chapter$",
        ]

        is_ui_line = any(re.search(pattern, line, re.IGNORECASE) for pattern in ui_indicators)

        # Skip very short lines that are likely UI (but keep if they look like dialogue)
        is_too_short = len(line) < 15 and not re.search(r'[.!?]["\']', line)

        # Keep the line if it's not UI and has reasonable length
        if not is_ui_line and (len(line) >= 15 or re.search(r"[.!?]", line)):
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Step 11: Final whitespace cleanup
    text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to single space
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Max 2 consecutive newlines
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)  # Trim each line

    return text.strip()

