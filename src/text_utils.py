"""
Unified text processing utilities.

This module provides comprehensive text cleaning functions for both
web scraping and text-to-speech processing. It consolidates the
previously separate text_cleaner modules into a unified architecture.
"""

import re
import unicodedata
from typing import Callable, Optional

from core.logger import get_logger

logger = get_logger("text_utils")


def clean_text(text: Optional[str]) -> str:
    """
    Clean scraped text from webnovel sites.

    This is the comprehensive text cleaner optimized for web scraping,
    removing HTML artifacts, UI elements, and unwanted content.

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

    # Step 1.5: Handle tables and structured content
    # Convert table separators to readable text
    text = re.sub(r"\|{2,}", " | ", text)  # Table column separators
    text = re.sub(r"\|(?=\s*\w)", " | ", text)  # Table pipes with spacing
    text = re.sub(r"\+-+\+", "", text)  # Table borders
    text = re.sub(r"-{3,}", " ", text)  # Table row separators (but keep shorter dashes for dialogue)

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

    # Step 2.1: Remove common social engagement and rating UI patterns (before individual social media removal)
    social_ui_patterns = [
        r"Like\s+this\s+chapter\?.*?Rate\s+it\s+\d+\s+stars?!?",
        r"Rate\s+this\s+chapter.*?\d+\s+stars?",
        r"Follow\s+@\w+\s+on\s+(Twitter|Facebook|Instagram)",
        r"Contact\s*:\s*\w+@\w+\.\w+",
    ]
    for pattern in social_ui_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Step 3: Remove entire UI blocks
    ui_block_patterns = [
        r"What\s+do\s+you\s+think\?.*?Total\s+Responses.*?Sort\s+by.*?Add\s+a\s+(Comment|Post).*?",
        r"Total\s+Responses:?\s*\d+.*?Sort\s+by:?.*?(Latest|Most|Oldest|Liked).*?Add\s+a\s+(Comment|Post).*?",
        r"Add\s+a\s+Post.*?Loading.*?Load\s+More.*?",
        r"Reply\s+to.*?Submit\s+Reply.*?",
        r"\[?Thank\s+You\s+For\s+Your\s+Support!?\]?",
    ]
    for pattern in ui_block_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Step 4: Remove translator/editor credits (common at start/end of chapters)
    translator_patterns = [
        r"Translator\s*:?\s*\w+",
        r"Editor\s*:?\s*\w+",
        r"Translation\s*:?\s*\w+",
        r"Translated\s+by\s*:?\s*\w+",
        r"Edited\s+by\s*:?\s*\w+",
        r"Translator\s*:?\s*\w+\s*Editor\s*:?\s*\w+",
        r"Translator\s*:?\s*\w+\s*In\s*Editor\s*:?\s*\w+",
        r"\w+\s*Editor\s*:?\s*\w+",
        r"Translator\s*:?\s*[A-Za-z_]+",
        r"Editor\s*:?\s*[A-Za-z_]+",
        # Specific format: Translator:Name_Editor:Name or Translator:NameEditor:Name
        r"Translator\s*:?\s*[A-Za-z_]+\s*_?\s*Editor\s*:?\s*[A-Za-z_]+",
        r"Translator\s*:?\s*[A-Za-z_]+\s*Editor\s*:?\s*[A-Za-z_]+",
        # Standalone lines with translator/editor info
        r"^Translator\s*:?\s*[A-Za-z_]+\s*Editor\s*:?\s*[A-Za-z_]+\s*In\s*$",
        r"^Translator\s*:?\s*[A-Za-z_]+\s*_?\s*Editor\s*:?\s*[A-Za-z_]+\s*In\s*$",
        # Author attribution patterns (common in chapter headers)
        r"By\s+[A-Za-z\s]+(?:\|.*)?",  # "By Author Name | ..." patterns
    ]
    for pattern in translator_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Step 5: Remove navigation elements
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

    # Step 6: Remove URLs, emails, social media
    text = re.sub(r"http[s]?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"@\w+", "", text)  # Social mentions
    text = re.sub(r"#\w+", "", text)  # Hashtags

    # Step 7: Remove timestamps and dates
    text = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", "", text)  # Dates
    text = re.sub(r"\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?", "", text)  # Times

    # Step 8: Remove excessive separators
    text = re.sub(r"[=]{2,}", "", text)  # ===
    text = re.sub(r"[-]{3,}", "", text)  # ---
    text = re.sub(r"[_]{3,}", "", text)  # ___
    text = re.sub(r"[*]{3,}", "", text)  # ***
    text = re.sub(r"[~]{2,}", "", text)  # ~~~

    # Step 9: Context-aware removal of UI words
    context_aware_patterns = [
        (r"(Sort\s+by:?\s*)(Latest|Most|Oldest)\b", r"\1"),
        (r"Liked(\s*Oldest|\s*Add|\s*Post|\s*Comment|\s*Sort)", r"\1"),
        (r"\b(Latest|Most|Oldest)(\s*Add\s+a\s+Post|\s*Post\s+Comment|\s*Loading|\s*Load\s+More)", r"\2"),
    ]
    for pattern, replacement in context_aware_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Step 10: Remove repeated UI sequences at end of chapters
    text = re.sub(r"(LikedOldest\s*)+$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"((Latest|Most|Oldest)\s*){3,}$", "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Step 11: Line-by-line filtering (whitelist approach)
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

        # Keep the line if it's not UI and has reasonable length
        if not is_ui_line and (len(line) >= 15 or re.search(r"[.!?]", line)):
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Step 12: Handle emojis and special Unicode characters for TTS
    # Convert common emojis to text descriptions or remove them
    emoji_replacements = {
        '🗿': ' (stone face) ',  # Moai emoji - common in Royal Road
        '😀': '', '😃': '', '😄': '', '😁': '', '😆': '', '😅': '', '🤣': '', '😂': '',
        '🙂': '', '🙃': '', '😉': '', '😊': '', '😇': '', '🥰': '', '😍': '', '🤩': '',
        '😘': '', '😗': '', '😚': '', '😙': '', '😋': '', '😛': '', '😜': '', '🤪': '',
        '😝': '', '🤑': '', '🤗': '', '🤭': '', '🤫': '', '🤔': '', '🤐': '', '🤨': '',
        '😐': '', '😑': '', '😶': '', '😏': '', '😒': '', '🙄': '', '😬': '', '🤥': '',
        '😌': '', '😔': '', '😪': '', '🤤': '', '😴': '', '😷': '', '🤒': '', '🤕': '',
        '🤢': '', '🤮': '', '🤧': '', '🥵': '', '🥶': '', '😵': '', '🤯': '', '🤠': '',
        '🥳': '', '😎': '', '🤓': '', '🧐': '', '😕': '', '😟': '', '🙁': '', '☹️': '',
        '😮': '', '😯': '', '😲': '', '😳': '', '🥺': '', '😦': '', '😧': '', '😨': '',
        '😰': '', '😥': '', '😢': '', '😭': '', '😱': '', '😖': '', '😣': '', '😞': '',
        '😓': '', '😩': '', '😫': '', '🥱': '', '😤': '', '😡': '', '😠': '', '🤬': '',
        '😈': '', '👿': '', '💀': '', '☠️': '', '💩': '', '🤡': '', '👹': '', '👺': '',
        '👻': '', '👽': '', '👾': '', '🤖': '', '😺': '', '😸': '', '😹': '', '😻': '',
        '😼': '', '😽': '', '🙀': '', '😿': '', '😾': '',
        # Common symbols that TTS might read awkwardly
        '→': ' to ', '←': ' from ', '↑': ' up ', '↓': ' down ',
        '⇒': ' then ', '⇐': ' from ', '⇔': ' or ',
        '★': ' star ', '☆': ' star ', '✦': ' star ', '✧': ' star ',
        '♥': ' heart ', '♡': ' heart ', '♦': ' diamond ', '♣': ' club ', '♠': ' spade ',
        '♪': ' note ', '♫': ' notes ', '♬': ' notes ',
        '©': ' copyright ', '®': ' registered ', '™': ' trademark ',
        '…': '...',  # Ellipsis character to three dots
        '—': ' - ',  # Em dash to hyphen
        '–': ' - ',  # En dash to hyphen
        '"': '"', '"': '"',  # Smart quotes to regular quotes
        ''': "'", ''': "'",  # Smart apostrophes to regular apostrophes
    }

    # Replace known emojis and symbols
    for emoji, replacement in emoji_replacements.items():
        text = text.replace(emoji, replacement)

    # Remove other emojis and special Unicode characters that TTS can't handle well
    # Keep basic punctuation and letters/numbers
    def is_tts_safe(char):
        """Check if character is safe for TTS (English letters, numbers, basic punctuation)"""
        # Keep basic ASCII alphanumeric
        if char.isalnum() and ord(char) < 128:  # Only ASCII letters/numbers
            return True
        if char in " .,!?;:()[]{}\"'/-_=+*&%$#@~`|\\":
            return True

        # Check Unicode category - only keep basic punctuation
        category = unicodedata.category(char)
        # Keep punctuation, symbols that are common in text
        if category in ('Po', 'Pd', 'Pe', 'Pf', 'Pi', 'Ps'):
            return True

        # Explicitly filter out non-English character ranges
        char_code = ord(char)

        # Filter out Chinese characters (CJK Unified Ideographs)
        if 0x4E00 <= char_code <= 0x9FFF:
            return False

        # Filter out Korean Hangul syllables
        if 0xAC00 <= char_code <= 0xD7AF:
            return False

        # Filter out Korean Hangul consonants (Jamo)
        if 0x1100 <= char_code <= 0x11FF:
            return False

        # Filter out Korean Hangul compatibility jamo
        if 0x3130 <= char_code <= 0x318F:
            return False

        # Filter out Japanese Hiragana and Katakana
        if 0x3040 <= char_code <= 0x30FF:  # Hiragana + Katakana
            return False

        # Filter out CJK symbols and punctuation that might interfere
        if 0x3000 <= char_code <= 0x303F:  # CJK symbols and punctuation
            return False

        # Filter out fullwidth forms (fullwidth ASCII punctuation used in CJK)
        if 0xFF00 <= char_code <= 0xFFEF:  # Halfwidth and Fullwidth Forms
            return False

        # Filter out CJK radicals and strokes
        if 0x2E80 <= char_code <= 0x2EFF:  # CJK Radicals Supplement
            return False

        # Filter out CJK compatibility ideographs
        if 0xF900 <= char_code <= 0xFAFF:  # CJK Compatibility Ideographs
            return False

        # Filter out vertical forms and other CJK extensions that might cause issues
        if 0xFE30 <= char_code <= 0xFE4F:  # CJK Compatibility Forms
            return False

        # Filter out emoji and pictographic symbols
        if category == 'So' and char_code > 0x1F000:  # Emoji range
            return False

        return False  # Default: filter out anything not explicitly allowed

    # Filter out problematic Unicode characters
    text = ''.join(char if is_tts_safe(char) else ' ' for char in text)

    # Step 13: Replace square brackets with parentheses for TTS compatibility
    # TTS engines may read [] as "bracket" or "square bracket", so use () instead
    text = text.replace('[', '(').replace(']', ')')

    # Step 14: Normalize punctuation for TTS
    # Multiple punctuation marks can confuse TTS
    # Fix dot spacing patterns: ". .." or ".. ." or ". . ." should become "..."
    # Order matters: handle ". . ." first, then ". .." and ".. ."
    text = re.sub(r"\.\s+\.\s+\.", "...", text)  # ". . ." → "..."
    text = re.sub(r"\.\s+\.\.", "...", text)  # ". .." → "..."
    text = re.sub(r"\.\.\s+\.", "...", text)  # ".. ." → "..."
    # Also handle cases where there might be more dots with spaces
    text = re.sub(r"\.\s+\.{2,}", "...", text)  # ". ..." or ". ...." → "..."
    text = re.sub(r"\.{2,}\s+\.", "...", text)  # ".. ." or "... ." → "..."
    text = re.sub(r"\.{4,}", ".", text)  # More than 3 dots becomes single dot
    text = re.sub(r"!{3,}", "!", text)  # Multiple ! becomes single (3+ only)
    text = re.sub(r"\?{3,}", "??", text)  # Multiple ? becomes ?? (3+ becomes 2)
    text = re.sub(r",{2,}", ",", text)  # Multiple commas to single
    text = re.sub(r";{2,}", ";", text)  # Multiple semicolons to single
    text = re.sub(r":{2,}", ":", text)  # Multiple colons to single (but keep time like 12:30)

    # Step 15: Clean up spacing around punctuation (improves TTS flow)
    # But preserve ellipses and quotes - don't add space after them
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)  # Remove space before punctuation
    # Add space after punctuation if missing, but not after ellipses, quotes, or between consecutive punctuation
    text = re.sub(r"([,.!?;:])([^\s,.!?;:\"\'`])", r"\1 \2", text)  # Add space after punctuation if next char is not punctuation or quotes
    # Handle ellipses separately - ensure space after "..."
    text = re.sub(r"\.{3}([^\s,.!?;:\"\'`])", r"... \1", text)  # Add space after "..." if next char is not punctuation or quotes

    # Step 16: Handle special formatting that might confuse TTS
    # Remove standalone symbols on their own lines
    text = re.sub(r"^\s*[=*#~|_-]{2,}\s*$", "", text, flags=re.MULTILINE)
    # Remove lines with only symbols and numbers (likely UI elements)
    text = re.sub(r"^\s*[\d\s=*#~|_-]+\s*$", "", text, flags=re.MULTILINE)

    # Step 17: Final whitespace cleanup
    text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to single space
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Max 2 consecutive newlines
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)  # Trim each line

    # Step 18: Remove empty parentheses and brackets (leftover from cleaning)
    text = re.sub(r"\(\s*\)", "", text)  # Empty parentheses
    text = re.sub(r"\[\s*\]", "", text)  # Empty brackets
    text = re.sub(r"\{\s*\}", "", text)  # Empty braces

    # Final cleanup of any double spaces that might have been created
    text = re.sub(r"  +", " ", text)

    return text.strip()


def clean_text_for_tts(text: str, base_cleaner: Optional[Callable[[str], str]] = None) -> str:
    """
    Clean text specifically for text-to-speech conversion.

    First applies base cleaner (if provided) to remove UI elements,
    then applies TTS-specific cleaning to remove symbols that TTS reads incorrectly.

    Args:
        text: Text to clean
        base_cleaner: Optional function to apply first (e.g., scraper text cleaner)

    Returns:
        Cleaned text ready for TTS
    """
    if not text:
        return ""

    # Apply base cleaner first if provided
    if base_cleaner:
        try:
            cleaned = base_cleaner(text)
            text = cleaned if isinstance(cleaned, str) else str(cleaned or "")
        except Exception as e:
            logger.warning(f"Error applying base cleaner: {e}")

    # Precompile regex patterns once for performance
    RE_SEPARATORS = re.compile(r'(=+|-{3,}|_{3,}|\*{3,}|#{2,}|~{2,}|\|{2,})')
    RE_STANDALONE = re.compile(r'\s+[=*#~|_-]+\s+')
    RE_SYMBOL_LINES = re.compile(r'^\s*[=*#~|_-]+\s*$', flags=re.MULTILINE)
    RE_PUNCT = re.compile(r'(\.{4,}|!{3,}|\?{3,})')
    RE_BRACKETS = re.compile(r'[\[\]]')
    RE_SPACES = re.compile(r'[ \t]+')
    RE_NEWLINES = re.compile(r'\n\s*\n\s*\n+')

    # Remove separators
    text = RE_SEPARATORS.sub(' ', text)

    # Remove standalone symbol groups
    text = RE_STANDALONE.sub(' ', text)
    text = RE_SYMBOL_LINES.sub('', text)

    # Normalize punctuation
    text = RE_PUNCT.sub(lambda m: m.group(0)[0] * 3 if m.group(0)[0] in '.!?' else m.group(0), text)

    # Replace brackets with parentheses
    text = RE_BRACKETS.sub(lambda m: '(' if m.group(0) == '[' else ')', text)

    # Whitespace cleanup
    text = RE_SPACES.sub(' ', text)
    text = RE_NEWLINES.sub('\n\n', text)

    return text.strip()


# Backwards compatibility aliases
# These will be deprecated in favor of direct imports from this module
scraper_clean_text = clean_text
tts_clean_text_for_tts = clean_text_for_tts


__all__ = [
    # Main functions
    "clean_text",
    "clean_text_for_tts",

    # Backwards compatibility (deprecated)
    "scraper_clean_text",
    "tts_clean_text_for_tts",
]