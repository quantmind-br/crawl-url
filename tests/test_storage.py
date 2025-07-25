"""Tests for URL storage utilities."""

import csv
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from crawl_url.utils.storage import URLStorage, FilenameGenerator, StorageManager


class TestURLStorage:
    """Test URLStorage class."""
    
    def test_storage_initialization(self, temp_output_file):
        """Test storage initialization with file path."""
        storage = URLStorage(temp_output_file)
        assert storage.output_file == temp_output_file
        assert storage.urls == []
    
    def test_add_urls(self, temp_output_file):
        """Test adding URLs to storage."""
        storage = URLStorage(temp_output_file)
        urls = ["https://example.com/page1", "https://example.com/page2"]
        
        storage.add_urls(urls)
        assert storage.urls == urls
        assert storage.get_url_count() == 2
    
    def test_clear_urls(self, temp_output_file):
        """Test clearing URLs from storage."""
        storage = URLStorage(temp_output_file)
        storage.add_urls(["https://example.com/page1"])
        
        storage.clear_urls()
        assert storage.urls == []
        assert storage.get_url_count() == 0
    
    def test_save_as_txt(self, temp_output_file, sample_urls):
        """Test saving URLs as text file."""
        storage = URLStorage(temp_output_file)
        storage.add_urls(sample_urls)
        
        storage.save_to_file("txt")
        
        assert temp_output_file.exists()
        content = temp_output_file.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        assert lines == sample_urls
    
    def test_save_as_json(self, temp_output_file, sample_urls):
        """Test saving URLs as JSON file."""
        storage = URLStorage(temp_output_file)
        storage.add_urls(sample_urls)
        
        with patch('time.strftime', return_value='2024-01-01 12:00:00'):
            storage.save_to_file("json")
        
        assert temp_output_file.exists()
        
        with open(temp_output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['crawl_date'] == '2024-01-01 12:00:00'
        assert data['metadata']['total_urls'] == len(sample_urls)
        assert data['metadata']['format_version'] == '1.0'
        assert data['urls'] == sample_urls
    
    def test_save_as_csv(self, temp_output_file, sample_urls):
        """Test saving URLs as CSV file."""
        storage = URLStorage(temp_output_file)
        storage.add_urls(sample_urls)
        
        storage.save_to_file("csv")
        
        assert temp_output_file.exists()
        
        with open(temp_output_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Check header
        assert rows[0] == ['URL', 'Domain', 'Path']
        
        # Check first URL row
        assert rows[1][0] == sample_urls[0]
        assert rows[1][1] == 'example.com'  # Domain from first URL
        assert len(rows) == len(sample_urls) + 1  # +1 for header
    
    def test_save_invalid_format_raises_error(self, temp_output_file):
        """Test saving with invalid format raises ValueError."""
        storage = URLStorage(temp_output_file)
        storage.add_urls(["https://example.com"])
        
        with pytest.raises(ValueError, match="Unsupported format: xml"):
            storage.save_to_file("xml")
    
    def test_save_creates_parent_directory(self, temp_directory):
        """Test saving creates parent directory if it doesn't exist."""
        nested_path = temp_directory / "subdir" / "output.txt"
        storage = URLStorage(nested_path)
        storage.add_urls(["https://example.com"])
        
        storage.save_to_file("txt")
        
        assert nested_path.exists()
        assert nested_path.parent.exists()


class TestFilenameGenerator:
    """Test FilenameGenerator class."""
    
    def test_generate_basic_filename(self):
        """Test generating basic filename."""
        with patch('time.strftime', return_value='20240101_120000'):
            filename = FilenameGenerator.generate_filename("https://example.com")
        
        assert filename == "example_com_20240101_120000.txt"
    
    def test_generate_filename_different_formats(self):
        """Test generating filenames with different formats."""
        base_url = "https://docs.example.com"
        
        with patch('time.strftime', return_value='20240101_120000'):
            txt_filename = FilenameGenerator.generate_filename(base_url, "txt")
            json_filename = FilenameGenerator.generate_filename(base_url, "json")
            csv_filename = FilenameGenerator.generate_filename(base_url, "csv")
        
        assert txt_filename.endswith(".txt")
        assert json_filename.endswith(".json")
        assert csv_filename.endswith(".csv")
    
    def test_generate_filename_without_timestamp(self):
        """Test generating filename without timestamp."""
        filename = FilenameGenerator.generate_filename(
            "https://example.com", 
            include_timestamp=False
        )
        
        assert filename == "example_com.txt"
        # Ensure no timestamp pattern
        assert "20" not in filename  # No year
    
    def test_generate_filename_with_custom_suffix(self):
        """Test generating filename with custom suffix."""
        with patch('time.strftime', return_value='20240101_120000'):
            filename = FilenameGenerator.generate_filename(
                "https://example.com",
                custom_suffix="filtered"
            )
        
        assert "filtered" in filename
        assert filename == "example_com_filtered_20240101_120000.txt"
    
    def test_clean_filename_removes_invalid_characters(self):
        """Test filename cleaning removes invalid characters."""
        # Test with URL containing invalid filename characters
        problematic_url = "https://sub.domain.com:8080/path?query=value"
        
        with patch('time.strftime', return_value='20240101_120000'):
            filename = FilenameGenerator.generate_filename(problematic_url)
        
        # Should not contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            assert char not in filename
        
        assert filename == "sub_domain_com_8080_20240101_120000.txt"
    
    def test_generate_filename_fallback_for_invalid_url(self):
        """Test filename generation fallback for invalid URL."""
        with patch('time.strftime', return_value='20240101_120000'):
            filename = FilenameGenerator.generate_filename("invalid-url")
        
        assert filename == "crawl_results_20240101_120000.txt"
    
    def test_clean_filename_length_limit(self):
        """Test filename cleaning respects length limits."""
        very_long_name = "a" * 100  # Very long domain name
        cleaned = FilenameGenerator._clean_filename(very_long_name)
        
        assert len(cleaned) <= 50
        assert cleaned == "a" * 50
    
    def test_clean_filename_removes_empty_parts(self):
        """Test filename cleaning removes empty parts."""
        name_with_multiple_underscores = "domain___with____underscores"
        cleaned = FilenameGenerator._clean_filename(name_with_multiple_underscores)
        
        assert cleaned == "domain_with_underscores"


class TestStorageManager:
    """Test StorageManager class."""
    
    def test_create_storage_with_auto_filename(self):
        """Test creating storage with auto-generated filename."""
        manager = StorageManager()
        
        with patch('time.strftime', return_value='20240101_120000'):
            storage = manager.create_storage("https://example.com", "json")
        
        assert isinstance(storage, URLStorage)
        assert storage.output_file.name == "example_com_20240101_120000.json"
        assert manager.current_storage == storage
    
    def test_create_storage_with_custom_path(self, temp_output_file):
        """Test creating storage with custom output path."""
        manager = StorageManager()
        
        storage = manager.create_storage(
            "https://example.com",
            output_path=temp_output_file
        )
        
        assert storage.output_file == temp_output_file
    
    def test_create_storage_with_custom_suffix(self):
        """Test creating storage with custom suffix."""
        manager = StorageManager()
        
        with patch('time.strftime', return_value='20240101_120000'):
            storage = manager.create_storage(
                "https://example.com",
                custom_suffix="filtered"
            )
        
        assert "filtered" in storage.output_file.name
    
    def test_save_urls_convenience_method(self, sample_urls):
        """Test save_urls convenience method."""
        manager = StorageManager()
        
        with patch('time.strftime', return_value='20240101_120000'):
            with patch.object(Path, 'cwd', return_value=Path('/tmp')):
                output_path = manager.save_urls(
                    urls=sample_urls,
                    base_url="https://example.com",
                    format_type="txt"
                )
        
        assert output_path.name == "example_com_20240101_120000.txt"
    
    def test_save_urls_with_custom_output(self, sample_urls, temp_output_file):
        """Test save_urls with custom output path."""
        manager = StorageManager()
        
        output_path = manager.save_urls(
            urls=sample_urls,
            base_url="https://example.com",
            output_path=temp_output_file
        )
        
        assert output_path == temp_output_file
        assert temp_output_file.exists()
        
        # Verify content
        content = temp_output_file.read_text(encoding='utf-8')
        assert content.strip().split('\n') == sample_urls
    
    def test_get_current_storage(self):
        """Test getting current storage instance."""
        manager = StorageManager()
        
        assert manager.get_current_storage() is None
        
        storage = manager.create_storage("https://example.com")
        assert manager.get_current_storage() == storage