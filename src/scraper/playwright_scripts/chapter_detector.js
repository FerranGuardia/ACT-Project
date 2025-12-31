/**
 * Chapter link detection module.
 * 
 * Detects chapter links using flexible patterns that match Python _is_chapter_url() logic.
 * This module provides the core chapter detection functionality used throughout the scroll script.
 */

/**
 * Determines if a link element is a chapter link.
 * 
 * @param {HTMLElement} link - The link element to check
 * @returns {boolean} True if the link appears to be a chapter link
 */
function isChapterLink(link) {
    if (!link || !link.href) return false;
    
    var href = link.href.toLowerCase();
    var text = (link.textContent || '').trim().toLowerCase();
    
    // Most important: Check if text contains "chapter" followed by a number
    // This catches cases where href doesn't have "chapter" but text does
    if (/^chapter\s+\d+/i.test(text) || /chapter\s+\d+/i.test(text)) {
        return true;
    }
    
    // Standard patterns: /chapter/, chapter-123, ch_123, etc. in href
    // Match chapter/ch followed by separator and number, or /chapter/ in path
    if (/\/chapter\/|\/chapter-|chapter[_-\s]\d+|ch[_-\s]\d+/.test(href) || /chapter[_-\s]\d+|ch[_-\s]\d+/.test(text)) {
        return true;
    }
    
    // FanMTL pattern: novel-name_123.html or novel-name/123.html
    if (/\d+\.html/.test(href)) {
        // Check if it's in a chapter list context
        var parent = link.closest('.chapter-list, #chapters, [class*="chapter"], [id*="chapter"]');
        if (parent) return true;
        // Or if link text suggests it's a chapter (must have chapter followed by number)
        if (/chapter\s*\d+|第.*章|ch\s*\d+/i.test(text)) return true;
    }
    
    // LightNovelPub/NovelLive pattern: /book/novel-name/chapter-123 or /book/novel-name/123
    // Also match /book/novel-name/chapter/123 or similar variations
    if (/\/book\/[^\/]+\/(?:chapter[\/-]?)?\d+/.test(href)) {
        return true;
    }
    
    // Generic pattern: URL contains numbers and link text suggests it's a chapter
    // This is more flexible - checks if text has "chapter" indicator
    if (/\d+/.test(href)) {
        // Check if text contains chapter indicators (must have chapter followed by number)
        if (/chapter\s*\d+|第.*章|ch\s*\d+/i.test(text)) {
            // Also check if it's in a chapter list container
            var parent = link.closest('.chapter-list, #chapters, .list-chapter, [class*="chapter"], [id*="chapter"], ul, ol, [role="list"]');
            if (parent) {
                // Additional check: see if parent or siblings have chapter-related content
                var parentText = (parent.textContent || '').toLowerCase();
                if (/chapter/i.test(parentText)) {
                    return true;
                }
            }
            // If text clearly indicates chapter, trust it
            if (/^chapter\s+\d+/i.test(text)) {
                return true;
            }
        }
    }
    
    return false;
}


