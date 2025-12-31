/**
 * Container finder module.
 * 
 * Finds the appropriate container element for scrolling operations.
 * Prioritizes chapter-specific containers, then falls back to general content containers.
 */

/**
 * Finds the best container element for chapter scrolling.
 * 
 * Priority order:
 * 1. Chapter-specific containers (#chapters, .chapter-list, etc.)
 * 2. General content containers (main, .content, #content, .container)
 * 3. document.body as fallback
 * 
 * @returns {HTMLElement} The container element to use for scrolling
 */
function findChapterContainer() {
    // Try chapter-specific containers first
    var chapterContainer = document.querySelector(
        '#chapters, .chapter-list, .list-chapter, [class*="chapter"], [id*="chapter"]'
    );
    
    if (!chapterContainer) {
        // Fall back to general content containers
        chapterContainer = document.querySelector('main, .content, #content, .container');
    }
    
    if (!chapterContainer) {
        // Final fallback to body
        chapterContainer = document.body;
    }
    
    return chapterContainer;
}


