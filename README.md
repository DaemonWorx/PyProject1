# PyProject1

A CLI tool for generating file hashes using the top 5 hash algorithms.

## Features

- Interactive CLI that prompts for filename and hash algorithm selection
- Supports 5 hash algorithms: MD5, SHA1, SHA256, SHA384, SHA512
- Option to calculate all 5 hashes at once
- Efficiently handles large files by reading in chunks
- Validates file existence before processing

## Setup

1. Create a virtual environment (optional):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: This tool uses only Python standard library (hashlib, os, pathlib), so no additional dependencies are required.

## Usage

Run the script:
```bash
python main.py
```

The tool will:
1. Display the current directory
2. Prompt you to enter a filename (must be in the current directory)
3. Show a menu to select a hash algorithm (1-5) or all algorithms (6)
4. Calculate and display the hash(es) for the selected file

### Example Output

```
==================================================
File Hash Generator
==================================================
Current directory: /home/joel/Desktop/PyProject1

Enter the filename (in current path): main.py

==================================================
Select Hash Algorithm:
==================================================
1. MD5
2. SHA1
3. SHA256
4. SHA384
5. SHA512
6. All 5 algorithms
==================================================

Enter your choice (1-6): 6

==================================================
Hash Results for: main.py
==================================================

MD5:
  a1b2c3d4e5f6...

SHA1:
  abc123def456...

SHA256:
  1234567890abcdef...

SHA384:
  fedcba0987654321...

SHA512:
  9876543210fedcba...

==================================================
```

