#!/usr/bin/env python3
"""
Script to clean __pycache__ directories and .pyc files.

This script recursively finds and removes all __pycache__ directories
and .pyc files from the project directory and its subdirectories.
"""

import os
import shutil
import sys
import argparse
from pathlib import Path


def get_logger():
    """Get a simple logger for the script."""
    import logging
    
    logger = logging.getLogger('clean_pycache')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def clean_pycache_directories(root_dir, dry_run=False, verbose=False):
    """
    Find and remove __pycache__ directories.
    
    Args:
        root_dir (str): Root directory to search from
        dry_run (bool): If True, only show what would be deleted
        verbose (bool): If True, show detailed output
    
    Returns:
        tuple: (directories_found, directories_removed)
    """
    logger = get_logger()
    directories_found = 0
    directories_removed = 0
    
    root_path = Path(root_dir)
    
    if verbose:
        logger.info(f"Searching for __pycache__ directories in: {root_path.absolute()}")
    
    # Find all __pycache__ directories
    for pycache_dir in root_path.rglob('__pycache__'):
        directories_found += 1
        
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would remove directory: {pycache_dir}")
            else:
                if verbose:
                    logger.info(f"Removing directory: {pycache_dir}")
                
                shutil.rmtree(pycache_dir)
                directories_removed += 1
                logger.info(f"Removed __pycache__ directory: {pycache_dir}")
                
        except Exception as e:
            logger.error(f"Failed to remove {pycache_dir}: {e}")
    
    return directories_found, directories_removed


def clean_pyc_files(root_dir, dry_run=False, verbose=False):
    """
    Find and remove .pyc files.
    
    Args:
        root_dir (str): Root directory to search from
        dry_run (bool): If True, only show what would be deleted
        verbose (bool): If True, show detailed output
    
    Returns:
        tuple: (files_found, files_removed)
    """
    logger = get_logger()
    files_found = 0
    files_removed = 0
    
    root_path = Path(root_dir)
    
    if verbose:
        logger.info(f"Searching for .pyc files in: {root_path.absolute()}")
    
    # Find all .pyc files
    for pyc_file in root_path.rglob('*.pyc'):
        files_found += 1
        
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would remove file: {pyc_file}")
            else:
                if verbose:
                    logger.info(f"Removing file: {pyc_file}")
                
                pyc_file.unlink()
                files_removed += 1
                logger.info(f"Removed .pyc file: {pyc_file}")
                
        except Exception as e:
            logger.error(f"Failed to remove {pyc_file}: {e}")
    
    return files_found, files_removed


def clean_pyo_files(root_dir, dry_run=False, verbose=False):
    """
    Find and remove .pyo files (optimized bytecode).
    
    Args:
        root_dir (str): Root directory to search from
        dry_run (bool): If True, only show what would be deleted
        verbose (bool): If True, show detailed output
    
    Returns:
        tuple: (files_found, files_removed)
    """
    logger = get_logger()
    files_found = 0
    files_removed = 0
    
    root_path = Path(root_dir)
    
    if verbose:
        logger.info(f"Searching for .pyo files in: {root_path.absolute()}")
    
    # Find all .pyo files
    for pyo_file in root_path.rglob('*.pyo'):
        files_found += 1
        
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would remove file: {pyo_file}")
            else:
                if verbose:
                    logger.info(f"Removing file: {pyo_file}")
                
                pyo_file.unlink()
                files_removed += 1
                logger.info(f"Removed .pyo file: {pyo_file}")
                
        except Exception as e:
            logger.error(f"Failed to remove {pyo_file}: {e}")
    
    return files_found, files_removed


def main():
    """Main function to handle command line arguments and execute cleaning."""
    parser = argparse.ArgumentParser(
        description='Clean __pycache__ directories and Python bytecode files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Clean current directory
  %(prog)s /path/to/project   # Clean specific directory
  %(prog)s --dry-run          # Show what would be deleted
  %(prog)s --verbose          # Show detailed output
  %(prog)s --pyc-only         # Clean only .pyc files
  %(prog)s --pycache-only     # Clean only __pycache__ directories
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to clean (default: current directory)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    
    parser.add_argument(
        '--pyc-only',
        action='store_true',
        help='Clean only .pyc files (not __pycache__ directories)'
    )
    
    parser.add_argument(
        '--pycache-only',
        action='store_true',
        help='Clean only __pycache__ directories (not .pyc files)'
    )
    
    parser.add_argument(
        '--include-pyo',
        action='store_true',
        help='Also clean .pyo files (optimized bytecode)'
    )
    
    args = parser.parse_args()
    logger = get_logger()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)
    
    # Determine what to clean
    clean_pycache = not args.pyc_only
    clean_pyc = not args.pycache_only
    clean_pyo = args.include_pyo
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will actually be deleted")
    
    logger.info(f"Starting cleanup in: {os.path.abspath(args.directory)}")
    logger.info("-" * 50)
    
    total_dirs_found = 0
    total_dirs_removed = 0
    total_pyc_found = 0
    total_pyc_removed = 0
    total_pyo_found = 0
    total_pyo_removed = 0
    
    # Clean __pycache__ directories
    if clean_pycache:
        dirs_found, dirs_removed = clean_pycache_directories(
            args.directory, args.dry_run, args.verbose
        )
        total_dirs_found += dirs_found
        total_dirs_removed += dirs_removed
    
    # Clean .pyc files
    if clean_pyc:
        pyc_found, pyc_removed = clean_pyc_files(
            args.directory, args.dry_run, args.verbose
        )
        total_pyc_found += pyc_found
        total_pyc_removed += pyc_removed
    
    # Clean .pyo files
    if clean_pyo:
        pyo_found, pyo_removed = clean_pyo_files(
            args.directory, args.dry_run, args.verbose
        )
        total_pyo_found += pyo_found
        total_pyo_removed += pyo_removed
    
    # Show summary
    logger.info("-" * 50)
    logger.info("CLEANUP SUMMARY:")
    
    if clean_pycache:
        logger.info(f"  __pycache__ directories found: {total_dirs_found}")
        if not args.dry_run:
            logger.info(f"  __pycache__ directories removed: {total_dirs_removed}")
    
    if clean_pyc:
        logger.info(f"  .pyc files found: {total_pyc_found}")
        if not args.dry_run:
            logger.info(f"  .pyc files removed: {total_pyc_removed}")
    
    if clean_pyo:
        logger.info(f"  .pyo files found: {total_pyo_found}")
        if not args.dry_run:
            logger.info(f"  .pyo files removed: {total_pyo_removed}")
    
    total_found = total_dirs_found + total_pyc_found + total_pyo_found
    total_removed = total_dirs_removed + total_pyc_removed + total_pyo_removed
    
    logger.info(f"  Total items found: {total_found}")
    if not args.dry_run:
        logger.info(f"  Total items removed: {total_removed}")
    
    if args.dry_run:
        logger.info("\nRun without --dry-run to actually delete these files.")
    
    if total_found == 0:
        logger.info("No Python cache files found to clean.")


if __name__ == '__main__':
    main()
