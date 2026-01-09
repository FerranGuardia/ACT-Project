"""
Text cleaning utilities for scraped webnovel content.

Provides functions to clean and normalize text extracted from webnovel sites,
removing UI elements, HTML artifacts, and other unwanted content.
Optimized for TTS (text-to-speech) readability.
"""

import re
import unicodedata
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

    # Step 2.1: Remove common social engagement and rating UI patterns
    social_ui_patterns = [
        r"Like\s+this\s+chapter\?.*?Rate\s+it\s+\d+\s+stars?!?",
        r"Rate\s+this\s+chapter.*?\d+\s+stars?",
        r"Follow\s+.*?\s+on\s+(Twitter|Facebook|Instagram)",
        r"Contact\s*:\s*\w+@\w+\.\w+",
    ]
    for pattern in social_ui_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

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
    text = re.sub(r"×", "", text)  # UI multiplication symbol

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
        """Check if character is safe for TTS (letters, numbers, basic punctuation)"""
        if char.isalnum():
            return True
        if char in " .,!?;:()[]{}\"'/-_=+*&%$#@~`|\\":
            return True
        # Check Unicode category
        category = unicodedata.category(char)
        # Keep punctuation, symbols that are common in text
        if category in ('Po', 'Pd', 'Pe', 'Pf', 'Pi', 'Ps', 'Sc', 'Sk', 'Sm', 'So'):
            # But skip emoji and pictographic symbols
            if category == 'So' and ord(char) > 0x1F000:  # Emoji range
                return False
            return True
        return False
    
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


