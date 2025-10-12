"""
Performance and Benchmark Tests for ClamAV GUI.

These tests measure performance of various operations and ensure they meet performance requirements.
"""

import pytest
import sys
import os
import time
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import clamav_gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clamav_gui.lang.lang_manager import SimpleLanguageManager
from clamav_gui.utils.quarantine_manager import QuarantineManager


class TestPerformanceBenchmarks:
    """Performance benchmark tests for core functionality."""

    @pytest.fixture
    def language_manager(self):
        """Create a language manager for performance testing."""
        return SimpleLanguageManager()

    @pytest.fixture
    def quarantine_manager(self, tmp_path):
        """Create a quarantine manager for performance testing."""
        return QuarantineManager(str(tmp_path))

    def test_language_manager_initialization_performance(self, benchmark, language_manager):
        """Benchmark language manager initialization."""
        def create_language_manager():
            return SimpleLanguageManager()

        result = benchmark(create_language_manager)
        assert result is not None
        assert result.current_lang == 'en_US'

    def test_translation_lookup_performance(self, benchmark, language_manager):
        """Benchmark translation lookup performance."""
        def translate_key():
            return language_manager.tr('scan.start', 'Start Scan')

        result = benchmark(translate_key)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_language_switching_performance(self, benchmark, language_manager):
        """Benchmark language switching performance."""
        def switch_language():
            return language_manager.set_language('it_IT')

        result = benchmark(switch_language)
        assert result is True
        assert language_manager.current_lang == 'it_IT'

    def test_quarantine_stats_performance(self, benchmark, quarantine_manager):
        """Benchmark quarantine statistics calculation."""
        def get_stats():
            return quarantine_manager.get_quarantine_stats()

        result = benchmark(get_stats)
        assert isinstance(result, dict)
        assert 'total_quarantined' in result

    def test_quarantine_file_listing_performance(self, benchmark, quarantine_manager):
        """Benchmark quarantine file listing performance."""
        def list_files():
            return quarantine_manager.list_quarantined_files()

        result = benchmark(list_files)
        assert isinstance(result, list)


class TestMemoryUsage:
    """Test memory usage and efficiency of operations."""

    def test_language_manager_memory_efficiency(self):
        """Test that language manager doesn't leak memory."""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and destroy multiple language managers
        for _ in range(100):
            lm = SimpleLanguageManager()
            del lm

        gc.collect()
        final_memory = process.memory_info().rss

        # Memory increase should be reasonable (less than 50MB for 100 managers)
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50 * 1024 * 1024, f"Memory increase too high: {memory_increase} bytes"

    def test_translation_caching_efficiency(self, language_manager):
        """Test that translation results are properly cached."""
        # First call
        start_time = time.time()
        result1 = language_manager.tr('scan.start', 'Start Scan')
        first_call_time = time.time() - start_time

        # Subsequent calls should be faster (cached)
        start_time = time.time()
        result2 = language_manager.tr('scan.start', 'Start Scan')
        second_call_time = time.time() - start_time

        # Second call should be faster or at least not significantly slower
        assert second_call_time <= first_call_time * 2
        assert result1 == result2


class TestConcurrencyPerformance:
    """Test performance under concurrent load."""

    def test_concurrent_translation_requests(self, language_manager):
        """Test translation performance with concurrent requests."""
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def worker_thread(thread_id):
            try:
                for i in range(100):
                    key = f'test.key.{thread_id}.{i}'
                    result = language_manager.tr(key, f'Default {i}')
                    results.put(result)
            except Exception as e:
                errors.put(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        # Check results
        while not results.empty():
            result = results.get()
            assert isinstance(result, str)

        # Check for errors
        error_count = 0
        while not errors.empty():
            error_count += 1
            errors.get()

        assert error_count == 0, f"Encountered {error_count} errors in concurrent translation"


class TestScalabilityPerformance:
    """Test performance scalability with larger datasets."""

    def test_large_translation_file_performance(self, benchmark):
        """Benchmark performance with many translation keys."""
        # Create a language manager with many translation keys
        manager = SimpleLanguageManager()

        # Add many translation keys for testing
        large_translations = {}
        for i in range(1000):
            large_translations[f'key_{i}'] = f'Translation {i}'

        # Mock the translations for this test
        with patch.object(manager, 'translations') as mock_translations:
            mock_translations.__getitem__ = Mock(return_value=large_translations)

            def lookup_many_keys():
                results = []
                for i in range(100):
                    result = manager.tr(f'key_{i}', f'Default {i}')
                    results.append(result)
                return results

            results = benchmark(lookup_many_keys)
            assert len(results) == 100
            assert all(isinstance(r, str) for r in results)

    def test_quarantine_manager_large_dataset_performance(self, benchmark, tmp_path):
        """Benchmark quarantine manager with many files."""
        manager = QuarantineManager(str(tmp_path))

        # Create many mock quarantine files
        import json
        quarantine_dir = os.path.join(tmp_path, 'quarantine')

        for i in range(100):
            metadata = {
                'original_filename': f'file_{i}.txt',
                'threat_name': f'Virus_{i}',
                'file_size': 1024 + i,
                'quarantine_date': f'2025-01-01T{i%24:02d}:00:00'
            }

            metadata_file = os.path.join(quarantine_dir, f'file_{i}.txt.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)

        def list_many_files():
            return manager.list_quarantined_files()

        files = benchmark(list_many_files)
        assert len(files) == 100
        assert all('original_filename' in f for f in files)
