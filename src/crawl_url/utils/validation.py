"""Validation utilities with user-friendly error messages."""

import re
from typing import Tuple
from urllib.parse import urlparse


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format and provide helpful error messages.
    
    Args:
        url: URL string to validate
        
    Returns:
        Tuple of (is_valid, error_message). error_message is empty string if valid.
    """
    if not url or not url.strip():
        return False, "🌐 URL cannot be empty. Please enter a website URL (e.g., https://example.com)"
    
    url = url.strip()
    
    # Check for common protocol mistakes
    if not url.startswith(('http://', 'https://')):
        if url.startswith(('www.', 'ftp.', 'mail.')):
            return False, (
                f"🔗 Missing protocol. Did you mean 'https://{url}'?\n"
                f"URLs must start with 'http://' or 'https://'"
            )
        elif '.' in url and not url.startswith(('mailto:', 'javascript:', 'file:')):
            return False, (
                f"🔗 Missing protocol. Did you mean 'https://{url}'?\n"
                f"URLs must start with 'http://' or 'https://'"
            )
        else:
            return False, (
                "🔗 Invalid URL format. URLs must start with 'http://' or 'https://'\n"
                "Examples: https://example.com, http://subdomain.site.org/path"
            )
    
    # Parse URL to validate structure
    try:
        parsed = urlparse(url)
        
        if not parsed.netloc:
            return False, (
                "🌐 Invalid URL: Missing domain name\n"
                "Example of valid URL: https://example.com/path"
            )
        
        # Check for common mistakes
        if parsed.netloc.startswith('.') or parsed.netloc.endswith('.'):
            return False, (
                f"🌐 Invalid domain '{parsed.netloc}': Domain cannot start or end with a dot\n"
                "Example: https://example.com (not https://.example.com.)"
            )
        
        if '..' in parsed.netloc:
            return False, (
                f"🌐 Invalid domain '{parsed.netloc}': Domain cannot contain consecutive dots\n"
                "Example: https://sub.example.com (not https://sub..example.com)"
            )
        
        # Check for suspicious protocols in parsed URL
        if parsed.scheme.lower() not in ('http', 'https'):
            return False, (
                f"🔒 Unsupported protocol '{parsed.scheme}'. Only HTTP and HTTPS are supported\n"
                "Please use URLs starting with 'http://' or 'https://'"
            )
        
        return True, ""
        
    except Exception as e:
        return False, (
            f"🔗 Invalid URL format: {str(e)}\n"
            "Please check your URL and try again. Example: https://example.com"
        )


def validate_crawl_depth(depth_str: str) -> Tuple[bool, str, int]:
    """
    Validate crawl depth input with helpful error messages.
    
    Args:
        depth_str: String representation of depth
        
    Returns:
        Tuple of (is_valid, error_message, parsed_depth)
    """
    if not depth_str or not depth_str.strip():
        return False, "🔍 Crawl depth cannot be empty. Please enter a number between 1 and 10", 0
    
    depth_str = depth_str.strip()
    
    try:
        depth = int(depth_str)
        
        if depth < 1:
            return False, (
                f"🔍 Crawl depth '{depth}' is too low. Minimum depth is 1\n"
                "Depth 1 means crawling only the starting page"
            ), 0
        
        if depth > 10:
            return False, (
                f"🔍 Crawl depth '{depth}' is too high. Maximum depth is 10\n"
                "High depths can take very long and may overwhelm websites"
            ), 0
        
        # Provide guidance for different depth values
        guidance = ""
        if depth == 1:
            guidance = " (Quick: crawls only the starting page)"
        elif depth <= 3:
            guidance = " (Recommended: good balance of speed and coverage)"
        elif depth <= 5:
            guidance = " (Thorough: may take longer but finds more URLs)"
        else:
            guidance = " (Deep crawl: may be very slow, use with caution)"
        
        return True, guidance, depth
        
    except ValueError:
        if '.' in depth_str:
            return False, (
                f"🔍 Crawl depth '{depth_str}' must be a whole number, not a decimal\n"
                "Examples: 1, 2, 3 (not 1.5, 2.0)"
            ), 0
        else:
            return False, (
                f"🔍 Invalid crawl depth '{depth_str}'. Please enter a whole number between 1 and 10\n"
                "Examples: 1 (surface), 3 (recommended), 5 (thorough)"
            ), 0


def validate_delay(delay_str: str) -> Tuple[bool, str, float]:
    """
    Validate delay input with helpful error messages.
    
    Args:
        delay_str: String representation of delay in seconds
        
    Returns:
        Tuple of (is_valid, error_message, parsed_delay)
    """
    if not delay_str or not delay_str.strip():
        return False, "⏱️ Delay cannot be empty. Please enter a number (e.g., 1.0 for 1 second)", 0.0
    
    delay_str = delay_str.strip()
    
    try:
        delay = float(delay_str)
        
        if delay < 0:
            return False, (
                f"⏱️ Delay '{delay}' cannot be negative\n"
                "Use 0 for no delay, or positive numbers like 1.0 for delays"
            ), 0.0
        
        if delay < 0.5 and delay > 0:
            return False, (
                f"⏱️ Delay '{delay}' is too short. Minimum recommended delay is 0.5 seconds\n"
                "Short delays may overwhelm websites and get you blocked"
            ), 0.0
        
        if delay > 10:
            return False, (
                f"⏱️ Delay '{delay}' is very long. Consider using a shorter delay\n"
                "Delays over 10 seconds will make crawling extremely slow"
            ), 0.0
        
        # Provide guidance for different delay values
        guidance = ""
        if delay == 0:
            guidance = " (No delay: fastest but may overwhelm servers)"
        elif delay < 1:
            guidance = " (Fast: minimal delay)"
        elif delay <= 2:
            guidance = " (Recommended: respectful crawling speed)"
        else:
            guidance = " (Conservative: very respectful but slower)"
        
        return True, guidance, delay
        
    except ValueError:
        return False, (
            f"⏱️ Invalid delay '{delay_str}'. Please enter a number\n"
            "Examples: 1.0 (1 second), 0.5 (half second), 2.5 (2.5 seconds)"
        ), 0.0


def validate_filter_url(filter_url: str, base_url: str) -> Tuple[bool, str]:
    """
    Validate URL filter with helpful error messages.
    
    Args:
        filter_url: Filter URL string
        base_url: Base URL being crawled
        
    Returns:
        Tuple of (is_valid, error_message). error_message is empty string if valid.
    """
    if not filter_url or not filter_url.strip():
        return True, ""  # Empty filter is valid (no filtering)
    
    filter_url = filter_url.strip()
    
    # Validate filter URL format
    is_valid, error = validate_url(filter_url)
    if not is_valid:
        return False, f"🎯 Filter URL is invalid: {error}"
    
    # Check if filter is related to base URL (helpful warning)
    try:
        base_domain = urlparse(base_url).netloc
        filter_domain = urlparse(filter_url).netloc
        
        if base_domain and filter_domain and base_domain != filter_domain:
            return False, (
                f"🎯 Filter domain '{filter_domain}' doesn't match crawl domain '{base_domain}'\n"
                f"This will likely result in no URLs being found.\n"
                f"Example valid filter for {base_url}: {base_url}/docs/"
            )
        
        return True, ""
        
    except Exception:
        # If parsing fails, still allow the filter (let the crawler handle it)
        return True, ""


def suggest_url_fix(invalid_url: str) -> str:
    """
    Suggest a corrected URL for common user mistakes.
    
    Args:
        invalid_url: The invalid URL string
        
    Returns:
        Suggested corrected URL or empty string if no obvious fix
    """
    if not invalid_url:
        return ""
    
    invalid_url = invalid_url.strip()
    
    # Common case: missing protocol
    if not invalid_url.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
        if '.' in invalid_url and not invalid_url.startswith(('.', '/')):
            return f"https://{invalid_url}"
    
    # Common case: mixed up protocols
    if invalid_url.startswith('htp://') or invalid_url.startswith('htps://'):
        return invalid_url.replace('htp://', 'http://').replace('htps://', 'https://')
    
    if invalid_url.startswith('http:///') or invalid_url.startswith('https:///'):
        return invalid_url.replace(':///', '://')
    
    return ""


def get_crawl_mode_explanation(mode: str) -> str:
    """
    Get detailed explanation of a crawling mode.
    
    Args:
        mode: Crawling mode ('auto', 'sitemap', 'crawl')
        
    Returns:
        Detailed explanation string
    """
    explanations = {
        'auto': (
            "🔍 Auto mode automatically detects the best crawling method:\n"
            "  • If URL ends with .xml → Uses sitemap mode\n"
            "  • Otherwise → Uses website crawling mode\n"
            "  • Best choice when you're unsure"
        ),
        'sitemap': (
            "🗺️ Sitemap mode extracts URLs from XML sitemaps:\n"
            "  • Fastest method for supported websites\n"
            "  • Finds URLs listed in sitemap.xml files\n"
            "  • Automatically discovers sitemaps from robots.txt\n"
            "  • Use when you know the site has sitemaps"
        ),
        'crawl': (
            "🕷️ Crawl mode recursively explores website pages:\n"
            "  • Follows links from page to page\n"
            "  • Can find URLs not in sitemaps\n"
            "  • Respects robots.txt and rate limits\n"
            "  • Use when sitemaps aren't available"
        )
    }
    
    return explanations.get(mode, f"Unknown mode: {mode}")


def get_output_format_explanation(format_type: str) -> str:
    """
    Get detailed explanation of an output format.
    
    Args:
        format_type: Output format ('txt', 'json', 'csv')
        
    Returns:
        Detailed explanation string
    """
    explanations = {
        'txt': (
            "📄 Plain text format (.txt):\n"
            "  • One URL per line\n"
            "  • Simple and lightweight\n"
            "  • Easy to process with scripts\n"
            "  • Best for: Simple URL lists"
        ),
        'json': (
            "📊 JSON format (.json):\n"
            "  • Structured data with metadata\n"
            "  • Includes crawl date, count, base URL\n"
            "  • Machine-readable format\n"
            "  • Best for: API integration, data analysis"
        ),
        'csv': (
            "📈 CSV format (.csv):\n"
            "  • Comma-separated values\n"
            "  • Columns: URL, Domain, Path\n"
            "  • Opens in Excel/Google Sheets\n"
            "  • Best for: Spreadsheet analysis, sorting"
        )
    }
    
    return explanations.get(format_type, f"Unknown format: {format_type}")