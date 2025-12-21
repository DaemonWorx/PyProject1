#!/usr/bin/env python3
"""
File Hash Generator CLI Tool
Creates hashes for files using the top 5 hash algorithms.
"""

import hashlib
from pathlib import Path


# Top 5 hash algorithms
HASH_ALGORITHMS = {
    "1": ("MD5", hashlib.md5),
    "2": ("SHA1", hashlib.sha1),
    "3": ("SHA256", hashlib.sha256),
    "4": ("SHA384", hashlib.sha384),
    "5": ("SHA512", hashlib.sha512),
}


def get_filename() -> str:
    """Prompt user for full file path."""
    while True:
        filename = input("\nEnter the filename (full path): ").strip()
        if not filename:
            print("Filename cannot be empty. Please try again.")
            continue
        
        file_path = Path(filename)
        if not file_path.exists():
            print(f"Error: File '{filename}' not found.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return None
        else:
            return filename


def display_menu() -> str:
    """Display hash algorithm selection menu."""
    print("\n" + "="*50)
    print("Select Hash Algorithm:")
    print("="*50)
    for key, (name, _) in HASH_ALGORITHMS.items():
        print(f"{key}. {name}")
    print("6. All 5 algorithms")
    print("="*50)
    
    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        if choice in HASH_ALGORITHMS.keys() or choice == "6":
            return choice
        print("Invalid choice. Please enter a number between 1 and 6.")


def calculate_hash(file_path: Path, hash_func) -> str:
    """Calculate hash for a file using the given hash function."""
    hash_obj = hash_func()
    
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file: {e}")


def display_results(filename: str, selected_choice: str):
    """Calculate and display hash results."""
    file_path = Path(filename)
    
    print("\n" + "="*50)
    print(f"Hash Results for: {filename}")
    print("="*50)
    
    if selected_choice == "6":
        # Calculate all 5 hashes
        for key in sorted(HASH_ALGORITHMS.keys()):
            name, hash_func = HASH_ALGORITHMS[key]
            try:
                hash_value = calculate_hash(file_path, hash_func)
                print(f"\n{name}:")
                print(f"  {hash_value}")
            except IOError as e:
                print(f"\n{name}: Error - {e}")
    else:
        # Calculate selected hash
        name, hash_func = HASH_ALGORITHMS[selected_choice]
        try:
            hash_value = calculate_hash(file_path, hash_func)
            print(f"\n{name}:")
            print(f"  {hash_value}")
        except IOError as e:
            print(f"Error: {e}")
    
    print("\n" + "="*50)


def main():
    """Main function to run the CLI tool."""
    print("="*50)
    print("File Hash Generator")
    print("="*50)
    
    # Get filename
    filename = get_filename()
    if filename is None:
        print("\nExiting...")
        return
    
    # Get hash algorithm selection
    choice = display_menu()
    
    # Calculate and display results
    display_results(filename, choice)
    
    print("\nDone!")


if __name__ == "__main__":
    main()

