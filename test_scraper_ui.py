"""
Basic Scraper Test UI
Standalone test interface for the scraper module.
Uses the new scraper code from src/scraper/
"""

import sys
import os
from pathlib import Path
import threading
import time

# Add src to path so we can import scraper modules
# The scraper modules use 'from core.logger' so we need src in the path
project_root = Path(__file__).parent
src_path = project_root / "src"
# Add src first so 'core' module can be found (it's in src/core)
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

# Try to import tkinter
try:
    import tkinter as tk
    from tkinter import scrolledtext, messagebox, ttk, StringVar, BooleanVar
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("ERROR: tkinter not available. Please install it.")
    sys.exit(1)

# Import scraper modules
try:
    # First import core modules to ensure they're available
    from core.logger import get_logger
    from core.config_manager import get_config
    # Now import scraper modules (they depend on core)
    from scraper import GenericScraper, ChapterUrlFetcher, ContentScraper
    from scraper.chapter_parser import extract_chapter_number
    HAS_SCRAPER = True
except ImportError as e:
    import traceback
    print(f"ERROR: Could not import scraper modules: {e}")
    print("Traceback:")
    traceback.print_exc()
    print("\nMake sure you're running from the ACT project root directory")
    HAS_SCRAPER = False

logger = get_logger("scraper.test_ui") if HAS_SCRAPER else None


class ScraperTestUI:
    """Basic UI for testing the scraper module."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Scraper Test UI - ACT")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # State variables
        self.is_processing = False
        self.should_stop = False
        self.scraper = None
        
        # Export folder on desktop
        self.export_folder = Path.home() / "Desktop" / "ACT_Scraped_Content"
        self.export_folder.mkdir(exist_ok=True)
        
        # Setup UI
        self.setup_ui()
        
        # Initialize scraper if available
        if HAS_SCRAPER:
            self.log("✓ Scraper modules loaded successfully")
        else:
            self.log("❌ ERROR: Scraper modules not available")
            messagebox.showerror("Error", "Could not import scraper modules. Check console for details.")
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main container with notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Configuration
        config_frame = tk.Frame(notebook, bg="#f0f4f8")
        notebook.add(config_frame, text="⚙️ Configuration")
        self.setup_config_tab(config_frame)
        
        # Tab 2: Test Scraping
        test_frame = tk.Frame(notebook, bg="#f0f4f8")
        notebook.add(test_frame, text="🧪 Test Scraping")
        self.setup_test_tab(test_frame)
        
        # Tab 3: Logs
        logs_frame = tk.Frame(notebook, bg="#f0f4f8")
        notebook.add(logs_frame, text="📊 Logs")
        self.setup_logs_tab(logs_frame)
    
    def setup_config_tab(self, parent):
        """Setup configuration tab."""
        main_frame = tk.Frame(parent, bg="#f0f4f8")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            main_frame,
            text="📖 Scraper Configuration",
            font=("Segoe UI", 18, "bold"),
            bg="#f0f4f8",
            fg="#2c3e50"
        )
        title.pack(pady=(0, 20))
        
        # Configuration frame
        config_frame = tk.LabelFrame(
            main_frame,
            text="URL Configuration",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            padx=20,
            pady=15
        )
        config_frame.pack(fill="x", pady=10)
        
        # Base URL
        tk.Label(
            config_frame,
            text="Base URL:",
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).grid(row=0, column=0, sticky="w", pady=10, padx=10)
        
        self.base_url_var = StringVar()
        base_url_entry = tk.Entry(
            config_frame,
            textvariable=self.base_url_var,
            width=70,
            font=("Segoe UI", 9)
        )
        base_url_entry.grid(row=0, column=1, sticky="ew", pady=10, padx=10)
        config_frame.columnconfigure(1, weight=1)
        
        # Table of Contents URL
        tk.Label(
            config_frame,
            text="TOC URL:",
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).grid(row=1, column=0, sticky="w", pady=10, padx=10)
        
        self.toc_url_var = StringVar()
        toc_url_entry = tk.Entry(
            config_frame,
            textvariable=self.toc_url_var,
            width=70,
            font=("Segoe UI", 9)
        )
        toc_url_entry.grid(row=1, column=1, sticky="ew", pady=10, padx=10)
        
        # Example URLs
        example_frame = tk.LabelFrame(
            main_frame,
            text="Example URLs",
            font=("Segoe UI", 10),
            bg="#ffffff",
            padx=15,
            pady=10
        )
        example_frame.pack(fill="x", pady=10)
        
        example_text = """Example NovelBin:
Base URL: https://novelbin.me
TOC URL: https://novelbin.me/novel-book/the-archmages-restaurant#tab-chapters-title

Example RoyalRoad:
Base URL: https://www.royalroad.com
TOC URL: https://www.royalroad.com/fiction/12345/novel-title"""
        
        tk.Label(
            example_frame,
            text=example_text,
            font=("Consolas", 9),
            bg="#ffffff",
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=10, pady=5)
    
    def setup_test_tab(self, parent):
        """Setup test scraping tab."""
        main_frame = tk.Frame(parent, bg="#f0f4f8")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            main_frame,
            text="🧪 Test Scraper Functions",
            font=("Segoe UI", 18, "bold"),
            bg="#f0f4f8",
            fg="#2c3e50"
        )
        title.pack(pady=(0, 20))
        
        # Test options frame
        options_frame = tk.LabelFrame(
            main_frame,
            text="Test Options",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            padx=20,
            pady=15
        )
        options_frame.pack(fill="x", pady=10)
        
        # Test chapter count
        self.test_count_var = BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Test: Get Chapter Count (Reference)",
            variable=self.test_count_var,
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).pack(anchor="w", pady=5)
        
        # Test URL fetching
        self.test_urls_var = BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Test: Fetch Chapter URLs",
            variable=self.test_urls_var,
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).pack(anchor="w", pady=5)
        
        # Test content scraping
        self.test_content_var = BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Test: Scrape Chapter Content",
            variable=self.test_content_var,
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).pack(anchor="w", pady=5)
        
        # Chapter range selection
        range_frame = tk.LabelFrame(
            main_frame,
            text="Chapter Range (for content scraping)",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            padx=20,
            pady=15
        )
        range_frame.pack(fill="x", pady=10)
        
        range_inner = tk.Frame(range_frame, bg="#ffffff")
        range_inner.pack(fill="x")
        
        tk.Label(
            range_inner,
            text="Start Chapter:",
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).pack(side="left", padx=10)
        
        self.start_chapter_var = StringVar(value="1")
        start_entry = tk.Entry(
            range_inner,
            textvariable=self.start_chapter_var,
            width=10,
            font=("Segoe UI", 10)
        )
        start_entry.pack(side="left", padx=5)
        
        tk.Label(
            range_inner,
            text="End Chapter:",
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).pack(side="left", padx=10)
        
        self.end_chapter_var = StringVar(value="")
        end_entry = tk.Entry(
            range_inner,
            textvariable=self.end_chapter_var,
            width=10,
            font=("Segoe UI", 10)
        )
        end_entry.pack(side="left", padx=5)
        
        tk.Label(
            range_inner,
            text="(leave empty for all chapters)",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#7f8c8d"
        ).pack(side="left", padx=10)
        
        # Option to scrape all or just test range
        self.scrape_range_var = BooleanVar(value=False)
        tk.Checkbutton(
            range_frame,
            text="Scrape all chapters in range (not just test)",
            variable=self.scrape_range_var,
            font=("Segoe UI", 10),
            bg="#ffffff"
        ).pack(anchor="w", padx=10, pady=5)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg="#f0f4f8")
        button_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start Test",
            command=self.start_test,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=30,
            pady=12,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_test,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=30,
            pady=12,
            relief=tk.FLAT,
            cursor="hand2",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)
        
        # Results frame
        results_frame = tk.LabelFrame(
            main_frame,
            text="Test Results",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            padx=20,
            pady=15
        )
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#2c3e50",
            height=15
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def setup_logs_tab(self, parent):
        """Setup logs tab."""
        main_frame = tk.Frame(parent, bg="#f0f4f8")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            main_frame,
            text="📊 Application Logs",
            font=("Segoe UI", 18, "bold"),
            bg="#f0f4f8",
            fg="#2c3e50"
        )
        title.pack(pady=(0, 10))
        
        # Logs text area
        self.logs_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff"
        )
        self.logs_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Clear button
        clear_btn = tk.Button(
            main_frame,
            text="Clear Logs",
            command=self.clear_logs,
            font=("Segoe UI", 10),
            bg="#7f8c8d",
            fg="white",
            padx=20,
            pady=5
        )
        clear_btn.pack(pady=5)
    
    def log(self, message):
        """Add a message to the logs."""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.logs_text.insert(tk.END, log_message)
        self.logs_text.see(tk.END)
        self.root.update_idletasks()
        
        # Also log to console
        print(log_message.strip())
        if logger:
            logger.info(message)
    
    def clear_logs(self):
        """Clear the logs text area."""
        self.logs_text.delete(1.0, tk.END)
    
    def add_result(self, message):
        """Add a message to the results area."""
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_results(self):
        """Clear the results text area."""
        self.results_text.delete(1.0, tk.END)
    
    def start_test(self):
        """Start the test in a separate thread."""
        if self.is_processing:
            messagebox.showwarning("Warning", "Test is already running!")
            return
        
        # Validate URLs
        base_url = self.base_url_var.get().strip()
        toc_url = self.toc_url_var.get().strip()
        
        if not base_url or not toc_url:
            messagebox.showerror("Error", "Please enter both Base URL and TOC URL!")
            return
        
        # Check if any test is selected
        if not (self.test_count_var.get() or self.test_urls_var.get() or self.test_content_var.get()):
            messagebox.showwarning("Warning", "Please select at least one test to run!")
            return
        
        # Start test in thread
        self.is_processing = True
        self.should_stop = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self.clear_results()
        self.log("=" * 60)
        self.log("Starting scraper test...")
        self.log(f"Base URL: {base_url}")
        self.log(f"TOC URL: {toc_url}")
        self.log("=" * 60)
        
        thread = threading.Thread(target=self.run_test, args=(base_url, toc_url), daemon=True)
        thread.start()
    
    def stop_test(self):
        """Stop the current test."""
        self.should_stop = True
        self.log("Stopping test...")
    
    def run_test(self, base_url, toc_url):
        """Run the actual test."""
        try:
            if not HAS_SCRAPER:
                self.add_result("❌ ERROR: Scraper modules not available")
                self.finish_test()
                return
            
            # Initialize scraper
            self.log("Initializing GenericScraper...")
            self.scraper = GenericScraper(base_url=base_url)
            self.add_result("✓ GenericScraper initialized")
            
            # Test 1: Get reference chapter count
            if self.test_count_var.get() and not self.should_stop:
                self.log("\n--- Test 1: Get Reference Chapter Count ---")
                self.add_result("\n" + "=" * 60)
                self.add_result("Test 1: Get Reference Chapter Count")
                self.add_result("=" * 60)
                
                try:
                    url_fetcher = ChapterUrlFetcher(base_url=base_url)
                    count = url_fetcher.get_reference_count(toc_url, should_stop=lambda: self.should_stop)
                    
                    if count is not None:
                        self.log(f"✓ Reference chapter count: {count}")
                        self.add_result(f"✓ Reference chapter count: {count}")
                    else:
                        self.log("⚠ Could not get reference count (may need Playwright)")
                        self.add_result("⚠ Could not get reference count (may need Playwright)")
                except Exception as e:
                    error_msg = f"❌ Error getting reference count: {str(e)}"
                    self.log(error_msg)
                    self.add_result(error_msg)
                    import traceback
                    self.log(traceback.format_exc())
            
            # Test 2: Fetch chapter URLs
            if self.test_urls_var.get() and not self.should_stop:
                self.log("\n--- Test 2: Fetch Chapter URLs ---")
                self.add_result("\n" + "=" * 60)
                self.add_result("Test 2: Fetch Chapter URLs")
                self.add_result("=" * 60)
                
                try:
                    self.log("Fetching chapter URLs...")
                    chapter_urls = self.scraper.get_chapter_urls(toc_url)
                    
                    if chapter_urls:
                        self.log(f"✓ Found {len(chapter_urls)} chapter URLs")
                        self.add_result(f"✓ Found {len(chapter_urls)} chapter URLs")
                        self.add_result(f"\nFirst 5 URLs:")
                        for i, url in enumerate(chapter_urls[:5], 1):
                            self.add_result(f"  {i}. {url}")
                        if len(chapter_urls) > 5:
                            self.add_result(f"  ... and {len(chapter_urls) - 5} more")
                    else:
                        self.log("❌ No chapter URLs found")
                        self.add_result("❌ No chapter URLs found")
                except Exception as e:
                    error_msg = f"❌ Error fetching URLs: {str(e)}"
                    self.log(error_msg)
                    self.add_result(error_msg)
                    import traceback
                    self.log(traceback.format_exc())
            
            # Test 3: Scrape chapter content (with range support)
            if self.test_content_var.get() and not self.should_stop:
                self.log("\n--- Test 3: Scrape Chapter Content ---")
                self.add_result("\n" + "=" * 60)
                self.add_result("Test 3: Scrape Chapter Content")
                self.add_result("=" * 60)
                
                try:
                    # First get URLs
                    self.log("Getting chapter URLs...")
                    chapter_urls = self.scraper.get_chapter_urls(toc_url)
                    
                    if not chapter_urls:
                        self.log("❌ No chapter URLs to scrape")
                        self.add_result("❌ No chapter URLs to scrape")
                    else:
                        # Filter by chapter range
                        start_ch_str = self.start_chapter_var.get().strip()
                        end_ch_str = self.end_chapter_var.get().strip()
                        
                        filtered_urls = chapter_urls
                        range_info = "all chapters"
                        
                        if start_ch_str or end_ch_str:
                            try:
                                start_ch = int(start_ch_str) if start_ch_str else 1
                                end_ch = int(end_ch_str) if end_ch_str else None
                                
                                # Filter URLs by chapter number
                                filtered_urls = []
                                for url in chapter_urls:
                                    ch_num = extract_chapter_number(url)
                                    if ch_num is not None:
                                        if ch_num >= start_ch:
                                            if end_ch is None or ch_num <= end_ch:
                                                filtered_urls.append(url)
                                
                                if end_ch:
                                    range_info = f"chapters {start_ch} to {end_ch}"
                                else:
                                    range_info = f"chapters {start_ch} onwards"
                                
                                self.log(f"Filtered to {len(filtered_urls)} URLs ({range_info})")
                                self.add_result(f"Filtered to {len(filtered_urls)} URLs ({range_info})")
                            except ValueError:
                                self.log("⚠ Invalid chapter range, using all chapters")
                                self.add_result("⚠ Invalid chapter range, using all chapters")
                        
                        if not filtered_urls:
                            self.log("❌ No chapters in specified range")
                            self.add_result("❌ No chapters in specified range")
                        else:
                            # Determine how many to scrape
                            scrape_all = self.scrape_range_var.get()
                            
                            if scrape_all:
                                chapters_to_scrape = filtered_urls
                                self.log(f"Scraping {len(chapters_to_scrape)} chapters ({range_info})...")
                                self.add_result(f"Scraping {len(chapters_to_scrape)} chapters ({range_info})...")
                            else:
                                # Just test first 3 chapters in range
                                chapters_to_scrape = filtered_urls[:3]
                                self.log(f"Testing first {len(chapters_to_scrape)} chapters in range...")
                                self.add_result(f"Testing first {len(chapters_to_scrape)} chapters in range...")
                            
                            # Scrape chapters
                            successful = 0
                            failed = 0
                            
                            for i, url in enumerate(chapters_to_scrape, 1):
                                if self.should_stop:
                                    break
                                
                                ch_num = extract_chapter_number(url) or i
                                self.log(f"Scraping chapter {ch_num} ({i}/{len(chapters_to_scrape)})...")
                                
                                content, title, error = self.scraper.scrape_chapter(url)
                                
                                if error:
                                    self.log(f"  ❌ Error: {error}")
                                    failed += 1
                                elif content:
                                    self.log(f"  ✓ Scraped successfully! ({len(content)} chars)")
                                    successful += 1
                                    
                                    # Save scraped content to file
                                    try:
                                        # Create a safe filename
                                        if title:
                                            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
                                            filename = f"Chapter_{ch_num:04d}_{safe_title}.txt"
                                        else:
                                            filename = f"Chapter_{ch_num:04d}.txt"
                                        
                                        # Save to export folder (clean content only, no metadata)
                                        filepath = self.export_folder / filename
                                        with open(filepath, 'w', encoding='utf-8') as f:
                                            # Write only the clean content, ready for TTS
                                            f.write(content)
                                        
                                        self.log(f"  ✓ Saved to: {filepath.name}")
                                    except Exception as save_error:
                                        self.log(f"  ⚠ Could not save file: {save_error}")
                                else:
                                    self.log(f"  ❌ No content scraped")
                                    failed += 1
                            
                            # Summary
                            self.add_result(f"\n--- Summary ---")
                            self.add_result(f"✓ Successfully scraped: {successful} chapters")
                            if failed > 0:
                                self.add_result(f"❌ Failed: {failed} chapters")
                            
                            if successful > 0 and not scrape_all:
                                self.add_result(f"\nNote: Only tested first {len(chapters_to_scrape)} chapters.")
                                self.add_result(f"Check 'Scrape all chapters in range' to scrape all {len(filtered_urls)} chapters.")
                            
                except Exception as e:
                    error_msg = f"❌ Error scraping content: {str(e)}"
                    self.log(error_msg)
                    self.add_result(error_msg)
                    import traceback
                    self.log(traceback.format_exc())
            
            self.log("\n" + "=" * 60)
            self.log("Test completed!")
            self.add_result("\n" + "=" * 60)
            self.add_result("Test completed!")
            
        except Exception as e:
            error_msg = f"❌ Fatal error: {str(e)}"
            self.log(error_msg)
            self.add_result(error_msg)
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.finish_test()
    
    def finish_test(self):
        """Finish the test and update UI."""
        self.is_processing = False
        self.should_stop = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")


def main():
    """Main entry point."""
    if not HAS_TKINTER:
        print("ERROR: tkinter is required but not available.")
        print("On Linux, install with: sudo apt-get install python3-tk")
        sys.exit(1)
    
    root = tk.Tk()
    app = ScraperTestUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

