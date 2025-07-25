"""Main CLI entry point for crawl-url application."""

import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from . import __version__, __description__
from .core.crawler import CrawlerService
from .core.models import CrawlConfig
from .core.sitemap_parser import SitemapService
from .core.ui import CrawlerApp
from .utils.storage import StorageManager

# Create main Typer app
app = typer.Typer(
    name="crawl-url",
    help=f"🕷️ {__description__}",
    epilog="Made with ❤️ using Typer and PyTermGUI",
    add_completion=True,
    rich_markup_mode="rich"
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]crawl-url[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, 
        "--version", 
        "-V", 
        callback=version_callback,
        help="Show version and exit"
    )
) -> None:
    """🕷️ Crawl-URL: A powerful terminal application for URL crawling."""
    pass


@app.command()
def interactive() -> None:
    """🖥️ Launch interactive terminal UI mode."""
    try:
        crawler_app = CrawlerApp()
        crawler_app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error launching interactive mode: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def crawl(
    url: str = typer.Argument(
        ..., 
        help="🌐 URL to crawl (website URL or sitemap.xml URL)"
    ),
    mode: str = typer.Option(
        "auto", 
        "--mode", 
        "-m", 
        help="🔍 Crawling mode: auto (detect), sitemap (XML only), crawl (recursive)",
        case_sensitive=False
    ),
    output: Optional[Path] = typer.Option(
        None, 
        "--output", 
        "-o", 
        help="💾 Output file path (auto-generated if not specified)"
    ),
    format_type: str = typer.Option(
        "txt", 
        "--format", 
        "-f", 
        help="📄 Output format",
        case_sensitive=False
    ),
    depth: int = typer.Option(
        3, 
        "--depth", 
        "-d", 
        help="🔍 Maximum crawling depth (crawl mode only)",
        min=1,
        max=10
    ),
    filter_base: Optional[str] = typer.Option(
        None,
        "--filter",
        "-fb",
        help="🎯 Filter URLs by base URL (only URLs starting with this will be included)"
    ),
    delay: float = typer.Option(
        1.0, 
        "--delay", 
        help="⏱️ Delay between requests in seconds (minimum 0.5 for respectful crawling)",
        min=0.5
    ),
    max_urls: int = typer.Option(
        1000,
        "--max-urls",
        help="📊 Maximum number of URLs to extract",
        min=1,
        max=10000
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-v", 
        help="🔊 Enable verbose output with progress information"
    ),
) -> None:
    """🕷️ Crawl a URL and extract URLs (command-line mode)."""
    
    # Create configuration
    try:
        config = CrawlConfig(
            url=url,
            mode=mode,
            max_depth=depth,
            delay=delay,
            filter_base=filter_base,
            output_path=output,
            output_format=format_type,
            verbose=verbose
        )
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    
    # Show initial information
    if verbose:
        _display_crawl_info(config, max_urls)
    
    # Determine output filename if not provided
    if output is None:
        domain = urlparse(url).netloc or "crawl_results"
        timestamp = __import__('time').strftime('%Y%m%d_%H%M%S')
        output = Path(f"{domain}_{timestamp}.{format_type}")
    
    try:
        # Perform crawling based on mode
        if mode == "sitemap" or (mode == "auto" and url.endswith('.xml')):
            result = _crawl_sitemap_mode(config, verbose)
        else:
            result = _crawl_website_mode(config, max_urls, verbose)
        
        if result.success:
            # Save results
            storage_manager = StorageManager()
            final_output_path = storage_manager.save_urls(
                urls=result.urls,
                base_url=config.url,
                format_type=config.output_format,
                output_path=output
            )
            
            # Display success information
            console.print(f"\n[green]Success![/green]")
            console.print(f"Found [bold cyan]{result.count}[/bold cyan] URLs")
            console.print(f"Saved to: [bold]{final_output_path}[/bold]")
            
            if verbose and result.urls:
                _display_summary_table(result.urls[:10])  # Show first 10
            
            # Show any warnings/errors
            if result.errors:
                console.print(f"\n[yellow]{len(result.errors)} warnings/errors occurred:[/yellow]")
                for error in result.errors[:5]:  # Show first 5 errors
                    console.print(f"  • {error}")
                if len(result.errors) > 5:
                    console.print(f"  • ... and {len(result.errors) - 5} more")
        else:
            console.print(f"[red]{result.message}[/red]")
            if result.errors and verbose:
                console.print("[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  • {error}")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            console.print("[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def _display_crawl_info(config: CrawlConfig, max_urls: int) -> None:
    """Display crawl configuration information."""
    table = Table(title="Crawl Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("URL", config.url)
    table.add_row("Mode", config.mode)
    table.add_row("Max Depth", str(config.max_depth))
    table.add_row("Delay", f"{config.delay}s")
    table.add_row("Max URLs", str(max_urls))
    table.add_row("Output Format", config.output_format.upper())
    
    if config.filter_base:
        table.add_row("URL Filter", config.filter_base)
    
    console.print(table)
    console.print()


def _crawl_sitemap_mode(config: CrawlConfig, verbose: bool):
    """Perform sitemap crawling with progress display."""
    console.print("[blue]Sitemap crawling mode[/blue]")
    
    if verbose:
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[urls_found]}[/cyan] URLs found"),
            console=console,
            transient=True
        ) as progress:
            
            progress_task = progress.add_task("Processing sitemap...", urls_found=0)
            
            def progress_callback(message: str, count: int):
                progress.update(progress_task, description=message, urls_found=count)
            
            service = SitemapService(progress_callback=progress_callback)
            
            if config.url.endswith('.xml'):
                result = service.process_sitemap_url(config.url, config.filter_base)
            else:
                result = service.process_base_url(config.url, config.filter_base)
    else:
        # Simple mode without progress
        service = SitemapService()
        
        if config.url.endswith('.xml'):
            result = service.process_sitemap_url(config.url, config.filter_base)
        else:
            result = service.process_base_url(config.url, config.filter_base)
    
    return result


def _crawl_website_mode(config: CrawlConfig, max_urls: int, verbose: bool):
    """Perform website crawling with progress display."""
    console.print("[blue]Website crawling mode[/blue]")
    
    if verbose:
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[urls_found]}[/cyan] URLs"),
            console=console,
            transient=True
        ) as progress:
            
            progress_task = progress.add_task(
                "Crawling website...", 
                total=max_urls,
                urls_found=0
            )
            
            def progress_callback(message: str, count: int):
                progress.update(
                    progress_task, 
                    description=message,
                    completed=min(count, max_urls),
                    urls_found=count
                )
            
            service = CrawlerService(progress_callback=progress_callback)
            result = service.crawl_url(
                url=config.url,
                max_depth=config.max_depth,
                delay=config.delay,
                filter_base=config.filter_base
            )
    else:
        # Simple mode without progress
        service = CrawlerService()
        result = service.crawl_url(
            url=config.url,
            max_depth=config.max_depth,
            delay=config.delay,
            filter_base=config.filter_base
        )
    
    return result


def _display_summary_table(urls: List[str]) -> None:
    """Display summary table of URLs."""
    table = Table(title="Sample URLs Found")
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("URL", style="blue")
    
    for i, url in enumerate(urls, 1):
        # Truncate very long URLs for display
        display_url = url if len(url) <= 80 else url[:77] + "..."
        table.add_row(str(i), display_url)
    
    console.print(table)


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()