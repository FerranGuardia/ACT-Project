/**
 * Link counting module.
 * 
 * Provides functionality to count chapter links in the DOM.
 * Depends on chapter_detector.js for the isChapterLink function.
 */

/**
 * Counts all chapter links currently in the DOM.
 * 
 * @param {Function} isChapterLinkFn - The chapter detection function from chapter_detector.js
 * @returns {number} The number of chapter links found
 */
function countChapterLinks(isChapterLinkFn) {
    var allLinks = Array.from(document.querySelectorAll('a[href]'));
    return allLinks.filter(isChapterLinkFn).length;
}

/**
 * Gets all chapter links from the DOM.
 * 
 * @param {Function} isChapterLinkFn - The chapter detection function from chapter_detector.js
 * @returns {Array<HTMLElement>} Array of chapter link elements
 */
function getChapterLinks(isChapterLinkFn) {
    var allLinks = Array.from(document.querySelectorAll('a[href]'));
    return allLinks.filter(isChapterLinkFn);
}





