/**
 * Scroll operations module.
 * 
 * Provides helper functions for performing scroll operations on containers and windows.
 */

/**
 * Scrolls a container element by a specified amount.
 * 
 * @param {HTMLElement} container - The container element to scroll
 * @param {number} scrollAmount - Amount in pixels to scroll (default: 200)
 */
function scrollContainer(container, scrollAmount) {
    scrollAmount = scrollAmount || 200;
    
    if (container !== document.body) {
        var containerHeight = container.scrollHeight;
        var containerClient = container.clientHeight;
        var currentScroll = container.scrollTop;
        
        if (currentScroll + scrollAmount < containerHeight - containerClient) {
            container.scrollTop = currentScroll + scrollAmount;
        } else {
            // Scroll to bottom
            container.scrollTop = containerHeight;
        }
    }
    
    // Also scroll window
    window.scrollTo(0, document.body.scrollHeight);
}

/**
 * Scrolls container to its maximum height (bottom).
 * 
 * @param {HTMLElement} container - The container element to scroll
 */
function scrollContainerToBottom(container) {
    if (container !== document.body) {
        container.scrollTop = container.scrollHeight;
    }
    window.scrollTo(0, document.body.scrollHeight);
}

/**
 * Scrolls the last chapter link into view to trigger lazy loading.
 * 
 * @param {Array<HTMLElement>} chapterLinks - Array of chapter link elements
 * @param {number} waitTime - Time to wait after scrolling in milliseconds (default: 800)
 * @returns {Promise<void>}
 */
async function scrollToLastChapter(chapterLinks, waitTime) {
    waitTime = waitTime || 800;
    
    if (chapterLinks.length > 0) {
        var lastLink = chapterLinks[chapterLinks.length - 1];
        try {
            lastLink.scrollIntoView({ behavior: 'auto', block: 'end', inline: 'nearest' });
            await new Promise(resolve => setTimeout(resolve, waitTime));
        } catch(e) {
            // Ignore errors
        }
    }
}

/**
 * Scrolls past the last chapter link to trigger infinite scroll.
 * 
 * @param {Array<HTMLElement>} chapterLinks - Array of chapter link elements
 * @param {number} multiplier - Multiplier for scroll distance (default: 2)
 * @param {number} waitTime - Time to wait after scrolling in milliseconds (default: 500)
 * @returns {Promise<void>}
 */
async function scrollPastLastChapter(chapterLinks, multiplier, waitTime) {
    multiplier = multiplier || 2;
    waitTime = waitTime || 500;
    
    if (chapterLinks.length > 0) {
        try {
            var lastLinkRect = chapterLinks[chapterLinks.length - 1].getBoundingClientRect();
            window.scrollBy(0, lastLinkRect.height * multiplier);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        } catch(e) {
            // Ignore errors
        }
    }
}







