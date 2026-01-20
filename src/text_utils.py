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

    # Step 11.5: De-obfuscate letter-spaced lines before whitespace collapse
    def _deobfuscate_spaced_letters_line(line: str) -> str:
        # First handle double-space obfuscation (existing logic)
        if "  " in line:
            words = re.findall(r"[A-Za-z]+", line)
            if len(words) >= 6:
                short_ratio = sum(1 for w in words if len(w) <= 2) / len(words)
                avg_len = sum(len(w) for w in words) / len(words)
                if short_ratio >= 0.6 and avg_len <= 2.2:
                    word_break_token = "__WB__"
                    marked = re.sub(r" {2,}", f" {word_break_token} ", line)
                    marked = re.sub(
                        r"(?<=\b[A-Za-z]{1,2})\s+(?=[A-Za-z]{1,2}\b)",
                        "",
                        marked,
                    )
                    marked = re.sub(rf"\s*{word_break_token}\s*", " ", marked)
                    return marked

        # Handle single-space syllable obfuscation (new logic)
        # Check for lines with many short alphabetic fragments separated by single spaces
        words = re.findall(r"[A-Za-z]+", line)
        if len(words) < 6:
            return line

        # Calculate metrics for single-space obfuscation detection
        short_ratio = sum(1 for w in words if len(w) <= 3) / len(words)  # Allow up to 3-letter fragments
        avg_len = sum(len(w) for w in words) / len(words)
        space_count = line.count(' ')

        # Detect obfuscation: high ratio of short fragments, many spaces
        is_obfuscated = (
            short_ratio >= 0.6 and  # 60%+ of fragments are 3 letters or less
            avg_len <= 3.0 and      # Average fragment length <= 3.0
            space_count >= len(words) - 1  # At least one space per word
        )

        if not is_obfuscated:
            return line

        # Smart deobfuscation: reconstruct words from syllable fragments with proper spacing

        # Extract all fragments
        fragments = re.findall(r'[A-Za-z]+', line)

        if len(fragments) < 6:
            return line

        # Process fragments into properly spaced words
        words = []
        current_word = ''

        function_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'this', 'that', 'these', 'those',
            'he', 'she', 'it', 'they', 'we', 'you', 'i', 'his', 'her', 'its', 'their', 'our', 'your', 'my',
            'who', 'what', 'where', 'when', 'why', 'how', 'all', 'not', 'only', 'also', 'then', 'than'
        }

        # Simple syllable-based word reconstruction
        # This uses basic heuristics to group syllables into readable words

        words = []
        current_word = ''

        # Common syllable patterns and word boundaries
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'

        for fragment in fragments:
            fragment_lower = fragment.lower()

            # If this is a function word, start new word
            if fragment_lower in function_words:
                if current_word:
                    words.append(current_word)
                words.append(fragment)
                current_word = ''
            # If capitalized, likely a proper noun - start new word
            elif fragment and fragment[0].isupper():
                if current_word:
                    words.append(current_word)
                current_word = fragment
            # If fragment ends with vowel and next starts with consonant, continue word
            elif current_word and current_word[-1].lower() in vowels and fragment_lower[0] in consonants:
                current_word += fragment
            # If fragment is very short (1-2 chars), likely part of current word
            elif len(fragment) <= 2:
                current_word += fragment
            # Otherwise, start new word
            else:
                if current_word:
                    words.append(current_word)
                current_word = fragment

        if current_word:
            words.append(current_word)

        # Add the last word
        if current_word:
            words.append(current_word)


        # Reconstruct the line with proper spacing
        result = ' '.join(words)

        # Preserve sentence-ending punctuation from the original
        if line.endswith('.'):
            result += '.'
        elif line.endswith('!'):
            result += '!'
        elif line.endswith('?'):
            result += '?'

        return result

    def _split_into_words_maximum_matching(text: str) -> list[str]:
        """Split concatenated text into words using maximum matching algorithm."""
        if not text:
            return []

        # Common English words for word boundary detection (prioritize longer words)
        common_words = {
            # Long/common words first for maximum matching
            'magnificent', 'glorious', 'country', 'place', 'called', 'metropolis', 'incorporated',
            'military', 'cultural', 'commercial', 'aspects', 'known', 'core', 'southern', 'region',
            'inside', 'dain', 'jiuhua', 'acity', 'that', 'not', 'only', 'all', 'the', 'was', 'and',
            'but', 'also', 'with', 'for', 'are', 'had', 'from', 'they', 'this', 'were', 'have', 'been',
            'when', 'where', 'what', 'how', 'who', 'why', 'here', 'there', 'then', 'than', 'can', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'ought', 'dare', 'need',
            'used', 'made', 'done', 'gone', 'come', 'take', 'give', 'make', 'find', 'lose', 'keep', 'hold',
            'city', 'town', 'house', 'room', 'door', 'wall', 'floor', 'ceiling', 'window', 'table', 'chair',
            'book', 'page', 'word', 'letter', 'line', 'point', 'time', 'day', 'night', 'week', 'month', 'year',
            'man', 'woman', 'person', 'people', 'child', 'boy', 'girl', 'father', 'mother', 'brother', 'sister',
            'friend', 'enemy', 'leader', 'follower', 'teacher', 'student', 'doctor', 'patient', 'soldier', 'warrior',
            'king', 'queen', 'prince', 'princess', 'lord', 'lady', 'master', 'slave', 'rich', 'poor', 'strong', 'weak',
            'good', 'bad', 'right', 'wrong', 'true', 'false', 'real', 'fake', 'old', 'new', 'young', 'big', 'small',
            'long', 'short', 'high', 'low', 'fast', 'slow', 'hot', 'cold', 'hard', 'soft', 'easy', 'difficult',
            'happy', 'sad', 'angry', 'afraid', 'love', 'hate', 'like', 'fear', 'hope', 'wish', 'dream', 'sleep',
            'walk', 'run', 'jump', 'sit', 'stand', 'lie', 'eat', 'drink', 'sleep', 'wake', 'live', 'die', 'kill',
            'work', 'play', 'rest', 'fight', 'win', 'lose', 'begin', 'end', 'start', 'stop', 'open', 'close',
            'white', 'black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'brown', 'gray', 'pink',
            'north', 'south', 'east', 'west', 'left', 'right', 'front', 'back', 'top', 'bottom', 'middle', 'center'
        }

        words = []
        remaining = text.lower()
        text_lower = text.lower()

        while remaining:
            # Try to find the longest possible word from the start
            found_word = None
            for length in range(min(len(remaining), 15), 2, -1):  # Try lengths from 15 down to 3
                candidate = remaining[:length]
                if candidate in common_words:
                    found_word = candidate
                    break

            if found_word:
                # Use the original casing for the word
                start_idx = text_lower.find(found_word)
                original_word = text[start_idx:start_idx + len(found_word)]
                words.append(original_word)
                remaining = remaining[len(found_word):]
                text_lower = text_lower[len(found_word):]
            else:
                # No word found, take next 3-5 characters as a word (heuristic)
                word_length = min(5, len(remaining))
                if len(remaining) <= 3:
                    word_length = len(remaining)

                word = remaining[:word_length]
                original_word = text[:word_length]
                words.append(original_word)

                remaining = remaining[word_length:]
                text = text[word_length:]

        return words

    def _reconstruct_words_from_fragments(fragments: list[str]) -> str:
        """Reconstruct words from syllable/letter fragments."""
        if len(fragments) <= 1:
            return ' '.join(fragments)

        # Simple heuristic: join fragments that are likely part of the same word
        # Based on common syllable patterns in English

        result_words = []
        current_word = fragments[0]

        for fragment in fragments[1:]:
            # Decide whether to continue current word or start a new one

            # If current word + fragment would be too long, or if fragment looks like a new word start
            should_start_new_word = (
                len(current_word + fragment) > 12 or  # Combined word too long
                (len(fragment) >= 3 and fragment[0].isupper()) or  # Capitalized fragment (proper noun)
                fragment.lower() in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']  # Common short words
            )

            if should_start_new_word:
                result_words.append(current_word)
                current_word = fragment
            else:
                current_word += fragment

        result_words.append(current_word)

        return ' '.join(result_words)

    text = "\n".join(_deobfuscate_spaced_letters_line(line) for line in text.splitlines())

    # Step 12: Handle emojis and special Unicode characters for TTS
    # Convert common emojis to text descriptions or remove them
    emoji_replacements = {
        '': ' (stone face) ',  # Moai emoji - common in Royal Road
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '', '': '', '': '', '': '',
        '': '', '': '', '': '', '': '', '': '',
        # Common symbols that TTS might read awkwardly
        '→': ' to ', '←': ' from ', '↑': ' up ', '↓': ' down ',
        '⇒': ' then ', '⇐': ' from ', '⇔': ' or ',
        '': ' star ', '': ' star ', '': ' star ', '': ' star ',
        '': ' heart ', '': ' heart ', '': ' diamond ', '': ' club ', '': ' spade ',
        '': ' note ', '': ' notes ', '': ' notes ',
        '©': ' copyright ', '®': ' registered ', '™': ' trademark ',
        '…': '...',  # Ellipsis character to three dots
        '—': ' - ',  # Em dash to hyphen
        '–': ' - ',  # En dash to hyphen
        '"': '"', '"': '"',  # Smart quotes to regular quotes
        ''': "'", ''': "'",  # Smart apostrophes to regular apostrophes
    }

    # Replace known emojis and symbols (skip empty keys)
    for emoji, replacement in emoji_replacements.items():
        if not emoji:
            continue
        text = text.replace(emoji, replacement)

    # Step 12.1: Normalize music-note artifacts that separate letters/words
    note_break_token = "__WB__"
    text = re.sub(r"(?:notes){2,}", f" {note_break_token} ", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:\bnotes?\b\s*){2,}", f" {note_break_token} ", text, flags=re.IGNORECASE)

    # Collapse patterns like "a notes b notes c" back into letters
    for _ in range(6):
        updated = re.sub(
            r"\b([A-Za-z])\b\s+notes?\s+\b([A-Za-z])\b",
            r"\1\2",
            text,
            flags=re.IGNORECASE,
        )
        if updated == text:
            break
        text = updated

    # Remove remaining note tokens and restore word breaks
    text = re.sub(r"\bnotes?\b", " ", text, flags=re.IGNORECASE)
    text = text.replace(note_break_token, " ")

    # Collapse sequences of spaced single letters into words (e.g., "n o t e s" -> "notes")
    def _collapse_spaced_letters(match: re.Match[str]) -> str:
        return re.sub(r"\s+", "", match.group(0))

    text = re.sub(
        r"(?:[A-Za-z]\s+){3,}[A-Za-z]",
        _collapse_spaced_letters,
        text,
    )

    def _collapse_spelled_out_line(line: str) -> str:
        tokens = re.findall(r"\b\w+\b", line)
        if not tokens:
            return line
        single_ratio = sum(1 for t in tokens if len(t) == 1) / len(tokens)
        if single_ratio < 0.2:
            return line
        return re.sub(r"\b([A-Za-z])\b\s+", r"\1", line)

    text = "\n".join(_collapse_spelled_out_line(line) for line in text.splitlines())

    # Step 12.2: Remove zero-width and control characters without inserting spaces
    # Some sites insert these to confuse scrapers; keep word cohesion intact.
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

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

    # Filter out problematic Unicode characters for TTS
    def is_tts_safe(char):
        """Check if character is safe for TTS (English letters, numbers, basic punctuation)."""
        # Keep basic ASCII alphanumeric
        if char.isalnum() and ord(char) < 128:
            return True

        char_code = ord(char)
        # Keep Latin-1 Supplement characters (accented letters)
        if 0x80 <= char_code <= 0xFF:
            return char_code >= 0xA0

        if char in " .,!?;:()[]{}\"'/-_=+*&%$#@~`|\\":
            return True

        # Keep general punctuation
        category = unicodedata.category(char)
        if category in ('Po', 'Pd', 'Pe', 'Pf', 'Pi', 'Ps'):
            return True

        return False

    text = ''.join(char if is_tts_safe(char) else ' ' for char in text)

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