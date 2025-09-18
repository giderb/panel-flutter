#!/usr/bin/env python
"""Run the GUI with suppressed warnings."""

import sys
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Redirect stderr to suppress console warnings
class SuppressOutput:
    def write(self, text):
        # Only suppress known non-critical warnings
        if any(x in text for x in ["No module named 'nastran'", "can't invoke", "event command"]):
            return
        sys.__stderr__.write(text)

    def flush(self):
        pass

# Apply suppression
sys.stderr = SuppressOutput()

# Run the main application
if __name__ == "__main__":
    from main import main
    main()