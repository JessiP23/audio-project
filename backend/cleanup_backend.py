#!/usr/bin/env python3
"""
Backend Cleanup Script
Cleans up unnecessary files and optimizes the codebase.
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_files():
    """Clean up unnecessary files."""
    print("🧹 Starting backend cleanup...")
    
    # Remove old processed files
    old_files = glob.glob("uploads/processed_file_*.wav")
    for file in old_files:
        os.remove(file)
        print(f"✅ Removed old file: {file}")
    
    # Clear log file
    log_file = "audio_processing.log"
    if os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write("")
        print(f"✅ Cleared log file: {log_file}")
    
    # Remove __pycache__ directories
    pycache_dirs = glob.glob("**/__pycache__", recursive=True)
    for dir_path in pycache_dirs:
        shutil.rmtree(dir_path)
        print(f"✅ Removed cache directory: {dir_path}")
    
    # Remove .pyc files
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    for file in pyc_files:
        os.remove(file)
        print(f"✅ Removed cache file: {file}")
    
    print("✅ File cleanup completed!")

def cleanup_uploads():
    """Clean up uploads directory."""
    print("\n📁 Cleaning uploads directory...")
    
    # Keep only recent processed files (last 5)
    processed_dir = Path("uploads/processed")
    if processed_dir.exists():
        files = list(processed_dir.glob("*.wav"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep only the 5 most recent files
        for file in files[5:]:
            file.unlink()
            print(f"✅ Removed old processed file: {file.name}")
    
    print("✅ Uploads cleanup completed!")

if __name__ == "__main__":
    cleanup_files()
    cleanup_uploads()
    print("\n🎉 Backend cleanup completed successfully!") 