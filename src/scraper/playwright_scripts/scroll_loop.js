/**
 * Scroll loop module.
 * 
 * Contains the main scrolling loop logic that orchestrates scrolling,
 * load more button clicking, and chapter counting.
 */

/**
 * Configuration constants for the scroll loop.
 */
var SCROLL_CONFIG = {
    maxScrolls: 1000,
    maxNoChange: 30,
    scrollDelay: 1000,
    loadMoreCheckInterval: 2,  // Check every N scrolls
    loadMoreWaitAfterClick: 2000,
    finalAggressiveScrolls: 10,
    finalAggressiveLoadMoreAttempts: 3,
    finalAggressiveWait: 1000,
    progressLogInterval: 10
};

/**
 * Performs the main scrolling loop to load all chapters.
 * 
 * @param {Object} dependencies - Object containing required functions:
 *   - countChapterLinks: Function to count chapter links
 *   - getChapterLinks: Function to get chapter link elements
 *   - tryClickLoadMore: Function to attempt clicking load more buttons
 *   - findChapterContainer: Function to find the scroll container
 *   - scrollContainer: Function to scroll the container
 *   - scrollContainerToBottom: Function to scroll container to bottom
 *   - scrollToLastChapter: Function to scroll to last chapter
 *   - scrollPastLastChapter: Function to scroll past last chapter
 * @returns {Promise<number>} Final chapter count
 */
async function performScrollLoop(dependencies) {
    var countChapterLinks = dependencies.countChapterLinks;
    var getChapterLinks = dependencies.getChapterLinks;
    var tryClickLoadMore = dependencies.tryClickLoadMore;
    var findChapterContainer = dependencies.findChapterContainer;
    var scrollContainer = dependencies.scrollContainer;
    var scrollContainerToBottom = dependencies.scrollContainerToBottom;
    var scrollToLastChapter = dependencies.scrollToLastChapter;
    var scrollPastLastChapter = dependencies.scrollPastLastChapter;
    
    var lastCount = 0;
    var currentCount = 0;
    var scrollAttempts = 0;
    var noChangeCount = 0;
    
    // Find container
    var chapterContainer = findChapterContainer();
    
    // Initial count
    currentCount = countChapterLinks();
    lastCount = currentCount;
    
    // Main scroll loop
    while (scrollAttempts < SCROLL_CONFIG.maxScrolls) {
        // Scroll container
        scrollContainer(chapterContainer);
        await new Promise(resolve => setTimeout(resolve, SCROLL_CONFIG.scrollDelay));
        
        // Try clicking Load More buttons periodically
        if (scrollAttempts % SCROLL_CONFIG.loadMoreCheckInterval === 0) {
            if (await tryClickLoadMore()) {
                await new Promise(resolve => setTimeout(resolve, SCROLL_CONFIG.loadMoreWaitAfterClick));
                currentCount = countChapterLinks();
                if (currentCount > lastCount) {
                    console.log('Load More clicked! Found ' + currentCount + ' chapters (was ' + lastCount + ')');
                    lastCount = currentCount;
                    noChangeCount = 0;
                }
            }
        }
        
        // Scroll to last chapter to trigger lazy loading
        var chapterLinks = getChapterLinks();
        await scrollToLastChapter(chapterLinks);
        
        // Also try scrolling past the last link to trigger infinite scroll
        await scrollPastLastChapter(chapterLinks);
        
        // Recount chapter links
        currentCount = countChapterLinks();
        
        // Check if we're making progress
        if (currentCount === lastCount) {
            noChangeCount++;
            if (noChangeCount >= SCROLL_CONFIG.maxNoChange) {
                // Before giving up, try aggressive Load More attempts
                if (await performFinalLoadMoreAttempts(tryClickLoadMore, countChapterLinks)) {
                    currentCount = countChapterLinks();
                    if (currentCount > lastCount) {
                        lastCount = currentCount;
                        noChangeCount = 0;
                        continue;
                    }
                }
                
                // Still no change, stop scrolling
                console.log('No more chapters loading after ' + noChangeCount + ' attempts, stopping scroll');
                break;
            }
        } else {
            noChangeCount = 0;
            console.log('Found ' + currentCount + ' chapters (was ' + lastCount + ')');
        }
        
        lastCount = currentCount;
        scrollAttempts++;
        
        // Log progress periodically
        if (scrollAttempts % SCROLL_CONFIG.progressLogInterval === 0) {
            console.log('Progress: Scroll ' + scrollAttempts + ', Found ' + currentCount + ' chapters...');
        }
    }
    
    // Perform final aggressive scroll phase
    await performFinalAggressiveScroll(
        chapterContainer,
        dependencies,
        currentCount
    );
    
    // Final count
    currentCount = countChapterLinks();
    console.log('Final chapter count: ' + currentCount);
    
    return currentCount;
}

/**
 * Performs final aggressive Load More attempts before giving up.
 * 
 * @param {Function} tryClickLoadMore - Function to attempt clicking load more
 * @param {Function} countChapterLinks - Function to count chapters
 * @returns {Promise<boolean>} True if more chapters were found
 */
async function performFinalLoadMoreAttempts(tryClickLoadMore, countChapterLinks) {
    console.log('No change detected, trying final aggressive Load More attempt...');
    var lastCount = countChapterLinks();
    
    for (var attempt = 0; attempt < 5; attempt++) {
        if (await tryClickLoadMore()) {
            await new Promise(resolve => setTimeout(resolve, 3000));
            var currentCount = countChapterLinks();
            if (currentCount > lastCount) {
                console.log('Final Load More successful! Found ' + currentCount + ' chapters');
                return true;
            }
        }
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    return false;
}

/**
 * Performs final aggressive scrolling phase to ensure everything is loaded.
 * 
 * @param {HTMLElement} chapterContainer - The container element
 * @param {Object} dependencies - Object containing required functions
 * @param {number} currentCount - Current chapter count
 * @returns {Promise<number>} Updated chapter count
 */
async function performFinalAggressiveScroll(chapterContainer, dependencies, currentCount) {
    var scrollContainerToBottom = dependencies.scrollContainerToBottom;
    var tryClickLoadMore = dependencies.tryClickLoadMore;
    var countChapterLinks = dependencies.countChapterLinks;
    var getChapterLinks = dependencies.getChapterLinks;
    var scrollPastLastChapter = dependencies.scrollPastLastChapter;
    
    console.log('Starting final aggressive scroll phase...');
    
    for (var i = 0; i < SCROLL_CONFIG.finalAggressiveScrolls; i++) {
        scrollContainerToBottom(chapterContainer);
        
        // Try clicking load more multiple times
        for (var j = 0; j < SCROLL_CONFIG.finalAggressiveLoadMoreAttempts; j++) {
            if (await tryClickLoadMore()) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                var newCount = countChapterLinks();
                if (newCount > currentCount) {
                    console.log('Final scroll found more chapters: ' + newCount);
                    currentCount = newCount;
                }
            }
        }
        
        await new Promise(resolve => setTimeout(resolve, SCROLL_CONFIG.finalAggressiveWait));
        
        // Scroll past the last chapter to trigger infinite scroll
        var chapterLinks = getChapterLinks();
        await scrollPastLastChapter(chapterLinks, 3, 1500);
    }
    
    return currentCount;
}



