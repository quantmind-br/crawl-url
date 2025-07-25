"""URL storage and file output utilities for crawl-url application."""

import csv
import json
import time
from pathlib import Path
from typing import List, Union, Optional
from urllib.parse import urlparse


class URLStorage:
    """Handle URL storage and export to various file formats."""
    
    def __init__(self, output_file: Union[str, Path]) -> None:
        """Initialize URL storage with output file path."""
        self.output_file = Path(output_file)
        self.urls: List[str] = []
    
    def add_urls(self, urls: List[str]) -> None:
        """Add URLs to storage."""
        self.urls.extend(urls)
    
    def clear_urls(self) -> None:
        """Clear all stored URLs."""
        self.urls.clear()
    
    def get_url_count(self) -> int:
        """Get the number of stored URLs."""
        return len(self.urls)
    
    def save_to_file(self, format_type: str = 'txt') -> None:
        """Save URLs to file in specified format."""
        # Ensure parent directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == 'txt':
            self._save_as_txt()
        elif format_type == 'json':
            self._save_as_json()
        elif format_type == 'csv':
            self._save_as_csv()
        else:
            raise ValueError(
                f"Unsupported output format '{format_type}'. Please choose from:\n"
                f"  • 'txt' - Plain text file with one URL per line\n"
                f"  • 'json' - Structured JSON file with metadata and URLs array\n"
                f"  • 'csv' - Comma-separated values file with URL, domain, and path columns"
            )
    
    def _save_as_txt(self) -> None:
        """Save URLs as plain text file (one URL per line)."""
        content = '\n'.join(self.urls)
        self.output_file.write_text(content, encoding='utf-8')
    
    def _save_as_json(self) -> None:
        """Save URLs as JSON file with metadata."""
        data = {
            'metadata': {
                'crawl_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_urls': len(self.urls),
                'format_version': '1.0'
            },
            'urls': self.urls
        }
        content = json.dumps(data, indent=2, ensure_ascii=False)
        self.output_file.write_text(content, encoding='utf-8')
    
    def _save_as_csv(self) -> None:
        """Save URLs as CSV file."""
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['URL', 'Domain', 'Path'])
            
            # Write URL data with parsed components
            for url in self.urls:
                try:
                    parsed = urlparse(url)
                    writer.writerow([url, parsed.netloc, parsed.path])
                except Exception:
                    # Fallback for malformed URLs
                    writer.writerow([url, '', ''])


class FilenameGenerator:
    """Generate appropriate filenames for crawl results."""
    
    @staticmethod
    def generate_filename(
        base_url: str, 
        format_type: str = 'txt',
        include_timestamp: bool = True,
        custom_suffix: str = ''
    ) -> str:
        """
        Generate filename based on domain and optional parameters.
        
        Args:
            base_url: The base URL that was crawled
            format_type: File format extension (txt, json, csv)
            include_timestamp: Whether to include timestamp in filename
            custom_suffix: Custom suffix to add before extension
            
        Returns:
            Generated filename string
        """
        try:
            # Extract domain from URL
            parsed = urlparse(base_url)
            domain = parsed.netloc or 'crawl_results'
            
        except Exception:
            domain = 'crawl_results'
        
        # Clean domain name for filename
        domain = FilenameGenerator._clean_filename(domain)
        
        # Build filename components
        parts = [domain]
        
        if custom_suffix:
            parts.append(FilenameGenerator._clean_filename(custom_suffix))
        
        if include_timestamp:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            parts.append(timestamp)
        
        # Join parts and add extension
        filename = '_'.join(parts) + f'.{format_type}'
        return filename
    
    @staticmethod
    def _clean_filename(name: str) -> str:
        """Clean filename by removing invalid characters."""
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Remove dots except for the extension
        name = name.replace('.', '_')
        
        # Limit length and remove extra underscores
        name = name[:50]  # Reasonable filename length
        name = '_'.join(part for part in name.split('_') if part)
        
        return name or 'unnamed'


class StorageManager:
    """High-level storage management for crawl-url application."""
    
    def __init__(self) -> None:
        """Initialize storage manager."""
        self.current_storage: Optional[URLStorage] = None
    
    def create_storage(
        self, 
        base_url: str, 
        format_type: str = 'txt',
        output_path: Optional[Path] = None,
        custom_suffix: str = ''
    ) -> URLStorage:
        """
        Create a new URL storage instance.
        
        Args:
            base_url: Base URL being crawled (for filename generation)
            format_type: Output format (txt, json, csv)
            output_path: Specific output path (overrides auto-generation)
            custom_suffix: Custom suffix for auto-generated filenames
            
        Returns:
            URLStorage instance
        """
        if output_path:
            filename = output_path
        else:
            # Auto-generate filename
            filename_str = FilenameGenerator.generate_filename(
                base_url=base_url,
                format_type=format_type,
                custom_suffix=custom_suffix
            )
            filename = Path.cwd() / filename_str
        
        self.current_storage = URLStorage(filename)
        return self.current_storage
    
    def save_urls(
        self, 
        urls: List[str], 
        base_url: str,
        format_type: str = 'txt',
        output_path: Optional[Path] = None,
        custom_suffix: str = ''
    ) -> Path:
        """
        Convenience method to save URLs directly.
        
        Args:
            urls: List of URLs to save
            base_url: Base URL being crawled
            format_type: Output format
            output_path: Specific output path
            custom_suffix: Custom suffix for filename
            
        Returns:
            Path where the file was saved
        """
        storage = self.create_storage(
            base_url=base_url,
            format_type=format_type,
            output_path=output_path,
            custom_suffix=custom_suffix
        )
        
        storage.add_urls(urls)
        storage.save_to_file(format_type)
        
        return storage.output_file
    
    def get_current_storage(self) -> Optional[URLStorage]:
        """Get the current storage instance."""
        return self.current_storage