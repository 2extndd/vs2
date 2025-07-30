#!/usr/bin/env python3
"""
Wrapper script to start vinted_scanner.py
This ensures proper Python environment and imports
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main scanner
if __name__ == "__main__":
    try:
        from vinted_scanner import main
        main()
    except ImportError:
        # Fallback: execute as subprocess
        import subprocess
        subprocess.run([sys.executable, "vinted_scanner.py"])
