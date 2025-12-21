#!/usr/bin/env python3
"""
7zip Folder Compression Script with Progress Bar
Compresses each folder in a directory using 7zip with progress indication.
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import Optional
import shutil
from tqdm import tqdm


def check_7zip_installed() -> bool:
    """Check if 7zip is installed on the system."""
    return shutil.which("7z") is not None


def get_directory_size(path: Path) -> int:
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total_size += entry.stat().st_size
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not access {entry}: {e}")
    return total_size


def compress_folder(
    folder_path: Path,
    output_dir: Optional[Path] = None,
    compression_level: int = 5,
    progress_bar: Optional[tqdm] = None
) -> bool:
    """
    Compress a folder using 7zip with progress bar.
    
    Args:
        folder_path: Path to the folder to compress
        output_dir: Directory where the archive will be saved (default: same as folder)
        compression_level: Compression level (0-9, default: 5)
        progress_bar: Optional tqdm progress bar to update
    
    Returns:
        True if compression was successful, False otherwise
    """
    if not folder_path.is_dir():
        if progress_bar:
            progress_bar.write(f"Error: {folder_path} is not a directory")
        else:
            print(f"Error: {folder_path} is not a directory")
        return False
    
    # Determine output archive path
    if output_dir is None:
        output_dir = folder_path.parent
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    archive_path = output_dir / f"{folder_path.name}.7z"
    
    # Skip if archive already exists
    if archive_path.exists():
        if progress_bar:
            progress_bar.write(f"Skipping {folder_path.name}: Archive already exists")
        else:
            print(f"Skipping {folder_path.name}: Archive already exists")
        return False
    
    # Create progress bar for this folder if not provided
    local_pbar = None
    if progress_bar is None:
        local_pbar = tqdm(
            total=100,
            desc=f"Compressing {folder_path.name}",
            unit="%",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}% [{elapsed}<{remaining}]"
        )
        progress_bar = local_pbar
    
    # Build 7z command
    # -mx=5: compression level (0=no compression, 9=maximum)
    # -mmt=on: multi-threading enabled
    # -bb1: show progress information (level 1)
    # -y: assume yes to all queries
    cmd = [
        "7z", "a",
        "-mx=" + str(compression_level),
        "-mmt=on",
        "-bb1",
        "-y",
        str(archive_path),
        str(folder_path)
    ]
    
    try:
        # Run 7z command and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Parse 7z output for progress
        current_percent = 0
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            # Parse percentage from 7z output
            # 7z output format: " 15% 12345       file.txt"
            percent_match = re.search(r'(\d+)%', line)
            if percent_match:
                new_percent = int(percent_match.group(1))
                if new_percent > current_percent:
                    current_percent = new_percent
                    progress_bar.n = current_percent
                    progress_bar.refresh()
        
        process.wait()
        
        # Complete the progress bar
        progress_bar.n = 100
        progress_bar.refresh()
        
        if local_pbar:
            local_pbar.close()
        
        if process.returncode == 0:
            archive_size = archive_path.stat().st_size if archive_path.exists() else 0
            size_mb = archive_size / (1024 * 1024)
            if progress_bar and not local_pbar:
                progress_bar.write(f"✓ Successfully compressed: {archive_path.name} ({size_mb:.2f} MB)")
            else:
                print(f"✓ Successfully compressed: {archive_path.name} ({size_mb:.2f} MB)")
            return True
        else:
            if progress_bar and not local_pbar:
                progress_bar.write(f"✗ Failed to compress: {folder_path.name}")
            else:
                print(f"✗ Failed to compress: {folder_path.name}")
            return False
            
    except Exception as e:
        if local_pbar:
            local_pbar.close()
        error_msg = f"✗ Error compressing {folder_path.name}: {e}"
        if progress_bar and not local_pbar:
            progress_bar.write(error_msg)
        else:
            print(error_msg)
        return False


def compress_all_folders(
    directory: Path,
    output_dir: Optional[Path] = None,
    compression_level: int = 5
):
    """
    Compress all folders in a directory with progress bars.
    
    Args:
        directory: Directory containing folders to compress
        output_dir: Directory where archives will be saved (default: same as source)
        compression_level: Compression level (0-9, default: 5)
    """
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        return
    
    # Get all folders in the directory
    folders = [f for f in directory.iterdir() if f.is_dir()]
    
    if not folders:
        print(f"No folders found in {directory}")
        return
    
    print(f"\nFound {len(folders)} folder(s) to compress\n")
    
    successful = 0
    failed = 0
    
    # Create overall progress bar
    overall_pbar = tqdm(
        total=len(folders),
        desc="Overall Progress",
        unit="folder",
        position=0,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} folders [{elapsed}<{remaining}]"
    )
    
    # Compress each folder
    for folder in folders:
        overall_pbar.set_description(f"Processing: {folder.name}")
        if compress_folder(folder, output_dir, compression_level, progress_bar=None):
            successful += 1
        else:
            failed += 1
        overall_pbar.update(1)
    
    overall_pbar.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Compression Summary:")
    print("=" * 60)
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(folders)}")
    print("=" * 60)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compress each folder in a directory using 7zip with progress bars"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing folders to compress (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory for archives (default: same as source directory)"
    )
    parser.add_argument(
        "-l", "--level",
        type=int,
        default=5,
        choices=range(0, 10),
        metavar="0-9",
        help="Compression level 0-9 (0=no compression, 9=maximum, default: 5)"
    )
    
    args = parser.parse_args()
    
    # Check if 7zip is installed
    if not check_7zip_installed():
        print("Error: 7zip (7z) is not installed or not in PATH")
        print("Please install 7zip:")
        print("  Ubuntu/Debian: sudo apt-get install p7zip-full")
        print("  Fedora/RHEL: sudo dnf install p7zip-full")
        print("  macOS: brew install p7zip")
        print("  Windows: Download from https://www.7-zip.org/")
        sys.exit(1)
    
    # Resolve directory paths
    directory = Path(args.directory).resolve()
    output_dir = Path(args.output).resolve() if args.output else None
    
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    print("=" * 60)
    print("7zip Folder Compression Tool")
    print("=" * 60)
    print(f"Source directory: {directory}")
    if output_dir:
        print(f"Output directory: {output_dir}")
    print(f"Compression level: {args.level}")
    print("=" * 60)
    
    # Compress all folders
    compress_all_folders(directory, output_dir, args.level)


if __name__ == "__main__":
    main()

