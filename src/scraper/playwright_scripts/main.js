/**
 * Main Playwright scroll script entry point.
 * 
 * This script orchestrates all modules to perform lazy-loading chapter detection.
 * It combines chapter detection, scrolling, and load more button handling.
 * 
 * This script is executed in the browser context by Playwright.
 */

/**
 * Main function that performs scrolling and chapter counting.
 * 
 * This function:
 * - Detects chapter links using flexible patterns
 * - Scrolls to trigger lazy loading
 * - Clicks "Load More" buttons
 * - Counts total chapters available
 * 
 * @returns {Promise<number>} The final count of chapter links found
 */
async function scrollAndCountChapters() {
    // Note: In browser context, all module functions are available in the global scope
    // after being bundled together by the Python loader
    
    // Create dependencies object for scroll loop
    var dependencies = {
        countChapterLinks: function() {
            return countChapterLinks(isChapterLink);
        },
        getChapterLinks: function() {
            return getChapterLinks(isChapterLink);
        },
        tryClickLoadMore: tryClickLoadMore,
        findChapterContainer: findChapterContainer,
        scrollContainer: scrollContainer,
        scrollContainerToBottom: scrollContainerToBottom,
        scrollToLastChapter: scrollToLastChapter,
        scrollPastLastChapter: scrollPastLastChapter
    };
    
    // Perform the main scroll loop
    var finalCount = await performScrollLoop(dependencies);
    
    return finalCount;
}







