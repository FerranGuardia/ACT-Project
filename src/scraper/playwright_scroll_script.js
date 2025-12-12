/**
 * Playwright scroll script for lazy-loading chapter detection.
 * 
 * This script is executed in the browser context by Playwright to:
 * - Detect chapter links using flexible patterns
 * - Scroll to trigger lazy loading
 * - Click "Load More" buttons
 * - Count total chapters available
 * 
 * Matches the Python _is_chapter_url() logic for consistency.
 */

async function scrollAndCountChapters() {
    // Enhanced chapter detection function - matches Python _is_chapter_url() logic
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
        if (/chapter|ch[_-\s]?\d+/.test(href) || /chapter|ch[_-\s]?\d+/.test(text)) {
            return true;
        }
        
        // FanMTL pattern: novel-name_123.html or novel-name/123.html
        if (/\d+\.html/.test(href)) {
            // Check if it's in a chapter list context
            var parent = link.closest('.chapter-list, #chapters, [class*="chapter"], [id*="chapter"]');
            if (parent) return true;
            // Or if link text suggests it's a chapter
            if (/chapter|第.*章|ch\s*\d+/i.test(text)) return true;
        }
        
        // LightNovelPub/NovelLive pattern: /book/novel-name/chapter-123 or /book/novel-name/123
        // Also match /book/novel-name/chapter/123 or similar variations
        if (/\/book\/[^\/]+\/(?:chapter[\/-]?)?\d+/.test(href)) {
            return true;
        }
        
        // Generic pattern: URL contains numbers and link text suggests it's a chapter
        // This is more flexible - checks if text has "chapter" indicator
        if (/\d+/.test(href)) {
            // Check if text contains chapter indicators
            if (/chapter|第.*章|ch\s*\d+/i.test(text)) {
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
    
    // Count chapter links using flexible detection
    function countChapterLinks() {
        var allLinks = Array.from(document.querySelectorAll('a[href]'));
        return allLinks.filter(isChapterLink).length;
    }
    
    var lastCount = 0;
    var currentCount = 0;
    var scrollAttempts = 0;
    var maxScrolls = 1000;  // Increased for thoroughness
    var noChangeCount = 0;
    var maxNoChange = 30;  // Increased to allow more time for lazy loading
    
    async function tryClickLoadMore() {
        // Try multiple strategies to find and click "Load More" buttons
        // Strategy 1: Try by text content (most reliable)
        var allClickable = Array.from(document.querySelectorAll('a, button, span, div, li, [role="button"], [onclick]'));
        for (var btn of allClickable) {
            try {
                var text = (btn.textContent || '').toLowerCase().trim();
                var isVisible = btn.offsetParent !== null && 
                               btn.offsetWidth > 0 && 
                               btn.offsetHeight > 0;
                
                if (isVisible && (
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
                )) {
                    // Scroll button into view first
                    btn.scrollIntoView({ behavior: 'auto', block: 'center' });
                    await new Promise(r => setTimeout(r, 200));
                    btn.click();
                    await new Promise(r => setTimeout(r, 500));
                    return true;
                }
            } catch(e) {}
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
            } catch(e) {}
        }
        
        return false;
    }
    
    // Try to find and scroll within chapter container
    var chapterContainer = document.querySelector('#chapters, .chapter-list, .list-chapter, [class*="chapter"], [id*="chapter"]');
    if (!chapterContainer) {
        chapterContainer = document.querySelector('main, .content, #content, .container');
    }
    if (!chapterContainer) {
        chapterContainer = document.body;
    }
    
    // Initial count
    currentCount = countChapterLinks();
    lastCount = currentCount;
    
    while (scrollAttempts < maxScrolls) {
        // Scroll container if it's not body
        if (chapterContainer !== document.body) {
            var containerHeight = chapterContainer.scrollHeight;
            var containerClient = chapterContainer.clientHeight;
            var currentScroll = chapterContainer.scrollTop;
            
            if (currentScroll + 200 < containerHeight - containerClient) {
                chapterContainer.scrollTop = currentScroll + 200;
            } else {
                chapterContainer.scrollTop = containerHeight;
            }
        }
        
        // Also scroll window
        window.scrollTo(0, document.body.scrollHeight);
        
        // Wait for content to load
        await new Promise(resolve => setTimeout(resolve, 1000));  // Increased from 800
        
        // Try clicking "Load More" buttons more frequently and aggressively
        if (scrollAttempts % 2 === 0) {  // More frequent - every 2 scrolls
            if (await tryClickLoadMore()) {
                // Wait longer after clicking to allow content to load
                await new Promise(resolve => setTimeout(resolve, 2000));  // Increased from 1000
                // Recheck count after load more
                currentCount = countChapterLinks();
                if (currentCount > lastCount) {
                    console.log('Load More clicked! Found ' + currentCount + ' chapters (was ' + lastCount + ')');
                    lastCount = currentCount;
                    noChangeCount = 0;
                }
            }
        }
        
        // Scroll last chapter link into view to trigger lazy loading
        var allLinks = Array.from(document.querySelectorAll('a[href]'));
        var chapterLinks = allLinks.filter(isChapterLink);
        if (chapterLinks.length > 0) {
            var lastLink = chapterLinks[chapterLinks.length - 1];
            try {
                lastLink.scrollIntoView({ behavior: 'auto', block: 'end', inline: 'nearest' });
                await new Promise(resolve => setTimeout(resolve, 800));  // Increased wait
            } catch(e) {}
        }
        
        // Also try scrolling past the last link to trigger infinite scroll
        if (chapterLinks.length > 0) {
            try {
                var lastLinkRect = chapterLinks[chapterLinks.length - 1].getBoundingClientRect();
                window.scrollBy(0, lastLinkRect.height * 2);  // Scroll past last link
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch(e) {}
        }
        
        // Recount chapter links
        currentCount = countChapterLinks();
        
        if (currentCount === lastCount) {
            noChangeCount++;
            if (noChangeCount >= maxNoChange) {
                // Before giving up, try one more aggressive "Load More" attempt
                console.log('No change detected, trying final aggressive Load More attempt...');
                for (var attempt = 0; attempt < 5; attempt++) {
                    if (await tryClickLoadMore()) {
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        currentCount = countChapterLinks();
                        if (currentCount > lastCount) {
                            console.log('Final Load More successful! Found ' + currentCount + ' chapters');
                            lastCount = currentCount;
                            noChangeCount = 0;
                            break;
                        }
                    }
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
                
                if (currentCount === lastCount) {
                    console.log('No more chapters loading after ' + noChangeCount + ' attempts, stopping scroll');
                    break;
                }
            }
        } else {
            noChangeCount = 0;
            console.log('Found ' + currentCount + ' chapters (was ' + lastCount + ')');
        }
        
        lastCount = currentCount;
        scrollAttempts++;
        
        if (scrollAttempts % 10 === 0) {
            console.log('Progress: Scroll ' + scrollAttempts + ', Found ' + currentCount + ' chapters...');
        }
    }
    
    // Final aggressive scroll to ensure everything is loaded
    console.log('Starting final aggressive scroll phase...');
    for (var i = 0; i < 10; i++) {  // Increased from 5 to 10
        if (chapterContainer !== document.body) {
            chapterContainer.scrollTop = chapterContainer.scrollHeight;
        }
        window.scrollTo(0, document.body.scrollHeight);
        
        // Try clicking load more multiple times
        for (var j = 0; j < 3; j++) {
            if (await tryClickLoadMore()) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                var newCount = countChapterLinks();
                if (newCount > currentCount) {
                    console.log('Final scroll found more chapters: ' + newCount);
                    currentCount = newCount;
                }
            }
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Scroll past the last chapter to trigger infinite scroll
        var allLinks = Array.from(document.querySelectorAll('a[href]'));
        var chapterLinks = allLinks.filter(isChapterLink);
        if (chapterLinks.length > 0) {
            var lastLink = chapterLinks[chapterLinks.length - 1];
            try {
                var lastLinkRect = lastLink.getBoundingClientRect();
                window.scrollBy(0, lastLinkRect.height * 3);  // Scroll further past
                await new Promise(resolve => setTimeout(resolve, 1500));
            } catch(e) {}
        }
    }
    
    // Final count
    currentCount = countChapterLinks();
    console.log('Final chapter count: ' + currentCount);
    
    return currentCount;
}

