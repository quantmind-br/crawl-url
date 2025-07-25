"""PyTermGUI interactive interface for crawl-url application."""

import shutil
import sys
from pathlib import Path
from typing import List, Optional

from ..utils.storage import StorageManager
from .crawler import CrawlerService
from .models import CrawlConfig
from .sitemap_parser import SitemapService

# Try to import PyTermGUI with fallback handling
try:
    import pytermgui as ptg
    PTG_AVAILABLE = True
except ImportError:
    PTG_AVAILABLE = False


class CrawlerApp:
    """Main PyTermGUI application for interactive URL crawling."""
    
    def __init__(self) -> None:
        """Initialize the crawler application."""
        self.manager: Optional[ptg.WindowManager] = None
        self.results: List[str] = []
        self.current_config: Optional[CrawlConfig] = None
        self.storage_manager = StorageManager()
        
        # Input field references
        self.url_input: Optional[ptg.InputField] = None
        self.mode_input: Optional[ptg.InputField] = None
        self.filter_input: Optional[ptg.InputField] = None
        self.depth_input: Optional[ptg.InputField] = None
        self.delay_input: Optional[ptg.InputField] = None
        self.format_input: Optional[ptg.InputField] = None
        
        # Status and progress
        self.status_label: Optional[ptg.Label] = None
        self.progress_label: Optional[ptg.Label] = None
        
    def run(self) -> None:
        """Run the interactive TUI application with fallback."""
        import platform
        
        # On Windows, prefer console mode by default due to PyTermGUI compatibility issues
        if platform.system() == "Windows":
            print("Windows detected - using console mode for better compatibility")
            self._run_console_fallback()
            return
            
        if not PTG_AVAILABLE:
            self._run_console_fallback()
            return
        
        try:
            self._test_tui_compatibility()
            self._run_tui_mode()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return
        except Exception as e:
            print(f"TUI mode not available: {str(e)}")
            print("Falling back to console mode...")
            self._run_console_fallback()
    
    def _test_tui_compatibility(self) -> None:
        """Test PyTermGUI compatibility before launching full interface."""
        try:
            # Simple, fast compatibility test - just try to create basic objects
            test_label = ptg.Label("Test")
            test_window = ptg.Window(test_label, width=20, height=3)
            
            # If we can create these objects without exception, TUI should work
            # No need to actually display anything
            
        except Exception as e:
            raise Exception(f"PyTermGUI compatibility test failed: {e}")
    
    def _run_tui_mode(self) -> None:
        """Run the full TUI interface."""
        self.manager = ptg.WindowManager()
        
        try:
            with self.manager:
                main_window = self._create_main_window()
                self.manager.add(main_window)
                self.manager.run()
        except KeyboardInterrupt:
            self._safe_exit("Operation cancelled by user")
        except Exception as e:
            self._safe_exit(f"TUI error: {e}")
    
    def _create_main_window(self) -> ptg.Window:
        """Create the main configuration window."""
        terminal_width, terminal_height = shutil.get_terminal_size()
        
        # Responsive design
        if terminal_width < 80:
            width = terminal_width - 4
            box = ptg.boxes.SINGLE
        else:
            width = 80
            box = ptg.boxes.DOUBLE
        
        # Create input fields
        self.url_input = ptg.InputField("https://", prompt="URL to crawl: ")
        self.mode_input = ptg.InputField("auto", prompt="Mode (auto/sitemap/crawl): ")
        self.filter_input = ptg.InputField("", prompt="Filter base URL (optional): ")
        self.depth_input = ptg.InputField("3", prompt="Max depth (crawl mode): ")
        self.delay_input = ptg.InputField("1.0", prompt="Delay between requests: ")
        self.format_input = ptg.InputField("txt", prompt="Output format (txt/json/csv): ")
        
        # Status label
        self.status_label = ptg.Label("[blue]ℹ️ Ready to crawl[/blue]")
        
        return ptg.Window(
            ptg.Label("[bold blue]🕷️ Crawl-URL Interactive Interface[/bold blue]", centered=True),
            "",
            ptg.Label("[bold]Configuration[/bold]"),
            self.url_input,
            self.mode_input,
            self.filter_input,
            self.depth_input,
            self.delay_input,
            self.format_input,
            "",
            self.status_label,
            "",
            ptg.Container(
                ptg.Button("Start Crawling", self._start_crawl),
                ptg.Button("View Results", self._show_results),
                ptg.Button("Clear Results", self._clear_results),
                ptg.Button("Help", self._show_help),
                ptg.Button("Quit", self._quit_app),
                box=ptg.boxes.EMPTY
            ),
            width=width,
            box=box
        ).center()
    
    def _create_progress_window(self) -> ptg.Window:
        """Create progress display window."""
        self.progress_label = ptg.Label("Initializing...")
        
        return ptg.Window(
            ptg.Label("[bold]Crawling Progress[/bold]", centered=True),
            "",
            self.progress_label,
            ptg.Label(""),
            self.status_label,
            "",
            ptg.Button("Cancel", self._cancel_crawl),
            width=60,
            box=ptg.boxes.SINGLE
        ).center()
    
    def _create_results_window(self) -> ptg.Window:
        """Create results display window with scrollable content."""
        # Create scrollable container for URLs
        results_container = ptg.Container()
        
        if not self.results:
            results_container.add(ptg.Label("[yellow]No results to display[/yellow]"))
        else:
            # Limit display for performance (first 100 URLs)
            display_urls = self.results[:100]
            
            for i, url in enumerate(display_urls, 1):
                # Truncate very long URLs
                display_url = url if len(url) <= 70 else url[:67] + "..."
                label = ptg.Label(f"{i:3d}. {display_url}")
                results_container.add(label)
            
            if len(self.results) > 100:
                results_container.add(ptg.Label(f"[dim]... and {len(self.results) - 100} more URLs[/dim]"))
        
        return ptg.Window(
            ptg.Label(f"[bold]Found {len(self.results)} URLs[/bold]", centered=True),
            "",
            results_container,
            "",
            ptg.Container(
                ptg.Button("Export Results", self._export_results),
                ptg.Button("Back to Main", self._show_main),
                box=ptg.boxes.EMPTY
            ),
            width=min(100, shutil.get_terminal_size()[0] - 4),
            height=min(25, shutil.get_terminal_size()[1] - 4),
            box=ptg.boxes.DOUBLE
        ).center()
    
    def _create_help_window(self) -> ptg.Window:
        """Create help information window."""
        help_text = [
            "[bold]Crawl-URL Help[/bold]",
            "",
            "[bold]Modes:[/bold]",
            "• auto: Automatically detect sitemap or crawl mode",
            "• sitemap: Parse sitemap.xml files only", 
            "• crawl: Recursively crawl website pages",
            "",
            "[bold]URL Filter:[/bold]",
            "Only include URLs starting with the filter base",
            "Example: https://docs.anthropic.com/en/docs/",
            "",
            "[bold]Output Formats:[/bold]",
            "• txt: Plain text, one URL per line",
            "• json: JSON format with metadata",
            "• csv: CSV format with URL components",
            "",
            "[bold]Tips:[/bold]",
            "• Use delay ≥1.0 for respectful crawling",
            "• Filter helps focus on specific site sections",
            "• Check robots.txt compliance automatically"
        ]
        
        help_container = ptg.Container()
        for line in help_text:
            help_container.add(ptg.Label(line))
        
        return ptg.Window(
            help_container,
            "",
            ptg.Button("Close", self._show_main),
            width=60,
            height=20,
            box=ptg.boxes.SINGLE
        ).center()
    
    def _start_crawl(self) -> None:
        """Start the crawling process."""
        try:
            # Validate and create configuration
            config = self._create_config_from_inputs()
            if not config:
                return
            
            self.current_config = config
            
            # Show progress window
            progress_window = self._create_progress_window()
            self.manager.remove_window(self.manager.focused_window)
            self.manager.add(progress_window)
            
            # Update status
            self._update_status("Starting crawl...", "info")
            
            # Perform crawling based on mode
            if config.mode in ("sitemap", "auto") and (
                config.url.endswith('.xml') or config.mode == "sitemap"
            ):
                self._crawl_sitemap(config)
            else:
                self._crawl_website(config)
            
        except Exception as e:
            self._update_status(f"Error: {e}", "error")
    
    def _create_config_from_inputs(self) -> Optional[CrawlConfig]:
        """Create crawl configuration from input fields."""
        try:
            url = self.url_input.value.strip()
            if not url:
                self._update_status("🌐 Please enter a website URL or sitemap.xml URL to crawl", "error")
                return None
            
            mode = self.mode_input.value.strip().lower()
            if mode not in ("auto", "sitemap", "crawl"):
                self._update_status("🔍 Mode must be: 'auto' (detect), 'sitemap' (XML only), or 'crawl' (recursive)", "error")
                return None
            
            try:
                max_depth = int(self.depth_input.value.strip())
                delay = float(self.delay_input.value.strip())
            except ValueError:
                self._update_status("⚙️ Invalid input: Depth must be a whole number (1-10), delay must be a decimal number (e.g., 1.0)", "error")
                return None
            
            filter_base = self.filter_input.value.strip() or None
            output_format = self.format_input.value.strip().lower()
            
            if output_format not in ("txt", "json", "csv"):
                self._update_status("📄 Output format must be: 'txt' (plain text), 'json' (structured), or 'csv' (spreadsheet)", "error")
                return None
            
            return CrawlConfig(
                url=url,
                mode=mode,
                max_depth=max_depth,
                delay=delay,
                filter_base=filter_base,
                output_format=output_format
            )
            
        except Exception as e:
            self._update_status(f"⚠️ Configuration problem: {e}", "error")
            return None
    
    def _crawl_sitemap(self, config: CrawlConfig) -> None:
        """Perform sitemap crawling."""
        service = SitemapService(progress_callback=self._progress_callback)
        
        if config.url.endswith('.xml'):
            result = service.process_sitemap_url(config.url, config.filter_base)
        else:
            result = service.process_base_url(config.url, config.filter_base)
        
        self._handle_crawl_result(result, config)
    
    def _crawl_website(self, config: CrawlConfig) -> None:
        """Perform website crawling."""
        service = CrawlerService(progress_callback=self._progress_callback)
        result = service.crawl_url(
            url=config.url,
            max_depth=config.max_depth,
            delay=config.delay,
            filter_base=config.filter_base
        )
        
        self._handle_crawl_result(result, config)
    
    def _handle_crawl_result(self, result, config: CrawlConfig) -> None:
        """Handle the result of crawling operation."""
        if result.success:
            self.results = result.urls
            self._update_status(f"✅ Found {result.count} URLs", "success")
            
            # Auto-save results
            try:
                output_path = self.storage_manager.save_urls(
                    urls=result.urls,
                    base_url=config.url,
                    format_type=config.output_format
                )
                self._update_status(f"📁 Saved to: {output_path.name}", "info")
            except Exception as e:
                self._update_status(f"⚠️ Crawl completed but save failed: {e}", "warning")
        else:
            self._update_status(f"❌ {result.message}", "error")
    
    def _progress_callback(self, message: str, count: int) -> None:
        """Update progress display."""
        if self.progress_label:
            self.progress_label.value = f"[cyan]🔄 {message}[/cyan]"
        if self.status_label and count > 0:
            self.status_label.value = f"[green]{count} URLs found so far...[/green]"
    
    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status display with colored message."""
        colors = {
            "info": "blue",
            "success": "green", 
            "warning": "yellow",
            "error": "red"
        }
        
        color = colors.get(status_type, "white")
        if self.status_label:
            self.status_label.value = f"[{color}]{message}[/{color}]"
    
    def _show_results(self) -> None:
        """Show results window."""
        results_window = self._create_results_window()
        self.manager.remove_window(self.manager.focused_window)
        self.manager.add(results_window)
    
    def _show_help(self) -> None:
        """Show help window."""
        help_window = self._create_help_window()
        self.manager.remove_window(self.manager.focused_window)
        self.manager.add(help_window)
    
    def _show_main(self) -> None:
        """Return to main window."""
        main_window = self._create_main_window()
        self.manager.remove_window(self.manager.focused_window)
        self.manager.add(main_window)
    
    def _export_results(self) -> None:
        """Export results in different format."""
        if not self.results or not self.current_config:
            self._update_status("No results to export", "warning")
            return
        
        try:
            formats = ["txt", "json", "csv"]
            current_format = self.current_config.output_format
            
            # Try next format in sequence
            next_format_idx = (formats.index(current_format) + 1) % len(formats)
            next_format = formats[next_format_idx]
            
            output_path = self.storage_manager.save_urls(
                urls=self.results,
                base_url=self.current_config.url,
                format_type=next_format,
                custom_suffix="export"
            )
            
            self._update_status(f"📁 Exported as {next_format.upper()}: {output_path.name}", "success")
            
        except Exception as e:
            self._update_status(f"Export failed: {e}", "error")
    
    def _clear_results(self) -> None:
        """Clear current results."""
        self.results.clear()
        self._update_status("Results cleared", "info")
    
    def _cancel_crawl(self) -> None:
        """Cancel current crawl operation."""
        self._show_main()
        self._update_status("Crawl cancelled", "warning")
    
    def _quit_app(self) -> None:
        """Quit the application."""
        self._safe_exit("Goodbye!")
    
    def _safe_exit(self, message: str = "") -> None:
        """Safely exit the application."""
        if message:
            print(message)
        if self.manager:
            self.manager.stop()
        sys.exit(0)
    
    def _run_console_fallback(self) -> None:
        """Run simplified console-based interface when TUI is not available."""
        print("Crawl-URL Console Mode")
        print("=" * 50)
        print("Running in console mode for Windows compatibility.")
        print("For full interactive experience on Linux, PyTermGUI is available.")
        print()
        
        try:
            url = input("Enter URL to crawl: ").strip()
            if not url:
                print("No URL provided. Exiting.")
                return
            
            mode = input("Mode (auto/sitemap/crawl) [auto]: ").strip().lower() or "auto"
            filter_base = input("Filter base URL (optional): ").strip() or None
            
            print("\nStarting crawl...")
            
            if mode in ("sitemap", "auto") and (url.endswith('.xml') or mode == "sitemap"):
                service = SitemapService()
                if url.endswith('.xml'):
                    result = service.process_sitemap_url(url, filter_base)
                else:
                    result = service.process_base_url(url, filter_base)
            else:
                service = CrawlerService()
                result = service.crawl_url(url=url, filter_base=filter_base)
            
            if result.success:
                print(f"\n[SUCCESS] Found {result.count} URLs")
                
                # Save results
                storage_manager = StorageManager()
                output_path = storage_manager.save_urls(
                    urls=result.urls,
                    base_url=url,
                    format_type="txt"
                )
                print(f"Results saved to: {output_path}")
                
                # Show first few URLs
                print("\nFirst 10 URLs:")
                for i, result_url in enumerate(result.urls[:10], 1):
                    print(f"{i:2d}. {result_url}")
                
                if len(result.urls) > 10:
                    print(f"... and {len(result.urls) - 10} more URLs")
            else:
                print(f"\n[FAILED] Crawl failed: {result.message}")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
        except Exception as e:
            print(f"\nError: {e}")


# Mock classes for testing when PyTermGUI is not available
class MockWindowManager:
    """Mock WindowManager for testing."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def add(self, window):
        pass
    
    def run(self):
        pass