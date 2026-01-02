/**
 * Load More button handler module.
 * 
 * Handles detection and clicking of "Load More" buttons to trigger lazy loading.
 * Uses multiple strategies to find and interact with load more buttons.
 */

/**
 * Attempts to find and click a "Load More" button.
 * 
 * Uses two strategies:
 * 1. Text-based detection (most reliable)
 * 2. CSS selector pattern matching
 * 
 * @returns {Promise<boolean>} True if a button was found and clicked, false otherwise
 */
async function tryClickLoadMore() {
    // Strategy 1: Try by text content (most reliable)
    var allClickable = Array.from(document.querySelectorAll('a, button, span, div, li, [role="button"], [onclick]'));
    for (var btn of allClickable) {
        try {
            var text = (btn.textContent || '').toLowerCase().trim();
            var isVisible = btn.offsetParent !== null && 
                           btn.offsetWidth > 0 && 
                           btn.offsetHeight > 0;
            
            if (isVisible && matchesLoadMoreText(text)) {
                // Scroll button into view first
                btn.scrollIntoView({ behavior: 'auto', block: 'center' });
                await new Promise(r => setTimeout(r, 200));
                btn.click();
                await new Promise(r => setTimeout(r, 500));
                return true;
            }
        } catch(e) {
            // Continue to next button if this one fails
        }
    }
    
    // Strategy 2: Try by class/id patterns
    var patternSelectors = [
        '[class*="load-more"]',
        '[class*="loadmore"]',
        '[id*="load-more"]',
        '[id*="loadmore"]',
        '[class*="show-more"]',
        '[class*="expand"]',
        '[class*="more-button"]',
        '[class*="load-button"]',
    ];
    
    for (var selector of patternSelectors) {
        try {
            var elements = document.querySelectorAll(selector);
            for (var el of elements) {
                if (el.offsetParent !== null && el.offsetWidth > 0) {
                    el.scrollIntoView({ behavior: 'auto', block: 'center' });
                    await new Promise(r => setTimeout(r, 200));
                    el.click();
                    await new Promise(r => setTimeout(r, 500));
                    return true;
                }
            }
        } catch(e) {
            // Continue to next selector if this one fails
        }
    }
    
    return false;
}

/**
 * Checks if text matches common "Load More" button patterns.
 * 
 * @param {string} text - The text content to check
 * @returns {boolean} True if text matches load more patterns
 */
function matchesLoadMoreText(text) {
    return (
        text.includes('load more') || 
        text.includes('show more') ||
        text.includes('view more') || 
        text.includes('see more') ||
        text.includes('more chapters') || 
        text.includes('next page') ||
        text.includes('load all') ||
        text.includes('show all') ||
        text.includes('expand') ||
        text === 'more' ||
        text === 'load' ||
        (text.includes('more') && text.length < 20)
    );
}

/**
 * Performs multiple aggressive attempts to click Load More buttons.
 * 
 * @param {number} maxAttempts - Maximum number of attempts to make
 * @param {number} delayBetweenAttempts - Delay in milliseconds between attempts
 * @returns {Promise<boolean>} True if any attempt succeeded
 */
async function tryClickLoadMoreAggressive(maxAttempts, delayBetweenAttempts) {
    for (var attempt = 0; attempt < maxAttempts; attempt++) {
        if (await tryClickLoadMore()) {
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, delayBetweenAttempts));
    }
    return false;
}





