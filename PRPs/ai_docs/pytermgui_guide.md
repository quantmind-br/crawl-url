# PyTermGUI Implementation Guide for Crawl-URL

## Overview
PyTermGUI is the primary TUI library for creating the interactive terminal interface. This guide provides essential patterns and gotchas for implementation.

## Critical Installation & Compatibility
```bash
pip install pytermgui
```

**IMPORTANT GOTCHA**: PyTermGUI may have import hanging issues on some Windows terminals until a key is pressed. Always test thoroughly on Windows environments and provide console fallback if needed.

## Core Architecture Pattern

### Basic Application Structure
```python
import pytermgui as ptg
import sys

class CrawlerApp:
    def __init__(self):
        self.manager = ptg.WindowManager()
        self.results = []
        
    def create_main_window(self):
        return ptg.Window(
            ptg.Label("[bold]🕷️ Crawl-URL v1.0[/bold]", centered=True),
            "",
            ptg.InputField("https://", prompt="URL to crawl: "),
            ptg.InputField("sitemap", prompt="Mode (url/sitemap): "),
            ptg.InputField("", prompt="Filter base URL (optional): "),
            "",
            ptg.Container(
                ptg.Button("Start Crawling", self.start_crawl),
                ptg.Button("View Results", self.show_results),
                ptg.Button("Export", self.export_results),
                ptg.Button("Quit", self.quit_app),
                box="EMPTY"
            ),
            width=70,
            box="DOUBLE"
        ).center()
    
    def run(self):
        try:
            with self.manager:
                self.manager.add(self.create_main_window())
                self.manager.run()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
```

## Input Validation Pattern
```python
class ValidatedURLInput(ptg.InputField):
    def handle_key(self, key: str) -> bool:
        if super().handle_key(key):
            return True
            
        if key == ptg.keys.ENTER:
            if self.validate_url(self.value):
                return self.submit()
            else:
                # Show error in status area
                self.show_error("Invalid URL format")
                return True
        return False
    
    def validate_url(self, url: str) -> bool:
        import re
        pattern = r'^https?://.+'
        return bool(re.match(pattern, url))
```

## Progress Display Pattern
```python
def create_progress_window(self):
    """Create progress display for crawling operation"""
    self.progress_label = ptg.Label("Ready to start...")
    self.status_label = ptg.Label("")
    
    return ptg.Window(
        ptg.Label("[bold]Crawling Progress[/bold]", centered=True),
        "",
        self.progress_label,
        self.status_label,
        "",
        ptg.Button("Cancel", self.cancel_crawl),
        width=60,
        box="SINGLE"
    ).center()

def update_progress(self, message: str, status: str = "info"):
    """Update progress display"""
    colors = {
        "info": "blue",
        "success": "green", 
        "warning": "yellow",
        "error": "red"
    }
    
    color = colors.get(status, "white")
    self.progress_label.value = f"[{color}]{message}[/{color}]"
    self.status_label.value = f"Status: {status}"
```

## Results Display Pattern
```python
def create_results_window(self, urls):
    """Create scrollable results display"""
    # Create scrollable container for URLs
    results_container = ptg.Container()
    
    for i, url in enumerate(urls[:100]):  # Limit display for performance
        label = ptg.Label(f"{i+1:3d}. {url}")
        results_container.add(label)
    
    return ptg.Window(
        ptg.Label(f"[bold]Found {len(urls)} URLs[/bold]", centered=True),
        "",
        results_container,
        "",
        ptg.Container(
            ptg.Button("Export", lambda: self.export_results(urls)),
            ptg.Button("Back", self.show_main),
            box="EMPTY"
        ),
        width=80,
        height=25,
        box="DOUBLE"
    ).center()
```

## Cross-Platform Considerations

### Windows Compatibility
- Test import behavior - may hang until key pressed
- Provide console fallback mode if TUI fails
- Use proper exception handling for terminal state

### Terminal Size Handling
```python
def create_responsive_window(self):
    """Adapt window size to terminal"""
    import shutil
    terminal_width, terminal_height = shutil.get_terminal_size()
    
    if terminal_width < 80:
        width = terminal_width - 4
        box = "SINGLE"
    else:
        width = 80
        box = "DOUBLE"
        
    return ptg.Window(
        # ... content
        width=width,
        box=box
    )
```

## Error Handling Pattern
```python
def safe_tui_launch(self):
    """Launch TUI with fallback to console mode"""
    try:
        # Test PyTermGUI import
        import pytermgui as ptg
        
        # Try to create a simple window
        with ptg.WindowManager() as manager:
            window = ptg.Window("Testing...", width=20)
            manager.add(window)
            
        # If we get here, TUI should work
        return self.run_tui_mode()
        
    except (ImportError, Exception) as e:
        print(f"TUI not available ({e}), falling back to console mode")
        return self.run_console_mode()
```

## Key TIM Markup Patterns
```python
# Status indicators
success_msg = "[green]✅ Crawl completed successfully[/green]"
error_msg = "[red]❌ Crawl failed[/red]"
warning_msg = "[yellow]⚠️ Some URLs failed[/yellow]"
info_msg = "[blue]ℹ️ Starting crawl...[/blue]"

# Progress indicators
progress_msg = "[cyan]🔄 Processing URL {current}/{total}...[/cyan]"

# Headers and titles
title = "[bold blue]🕷️ Crawl-URL Application[/bold blue]"
section = "[bold]Configuration[/bold]"
```

## Performance Considerations
- Limit displayed results (e.g., first 1000 URLs)
- Use generators for large result sets
- Clear widgets when switching windows to prevent memory leaks
- Implement pagination for very large result sets

## Testing Pattern
```python
# Mock TUI for testing
class MockWindowManager:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def add(self, window):
        pass
    def run(self):
        pass

# Use in tests
def test_crawler_app():
    app = CrawlerApp()
    app.manager = MockWindowManager()
    # Test app logic without actual TUI
```

## Critical Gotchas
1. **Import Hanging**: May hang on Windows - always test
2. **Terminal State**: Use proper cleanup with context managers
3. **Color Compatibility**: Works across terminals but test thoroughly
4. **Memory Management**: Clear widgets and limit displayed data
5. **Exception Handling**: Always handle TUI failures gracefully

This guide provides the essential patterns needed to implement a robust PyTermGUI-based interface for the crawl-url application.