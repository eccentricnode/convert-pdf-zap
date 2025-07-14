"""
Timeout functionality for PDF conversion operations.
Extracted from main.py to enable reusability and testing.
"""

import signal
import sys


def timeout_handler(signum, frame):
    """
    Signal handler for timeout operations.
    Prints error message and exits when timeout occurs.
    """
    print("ERROR: Operation timed out!")
    print("The conversion appears to be hanging.")
    sys.exit(1)


def run_with_timeout(func, timeout_seconds=300):
    """
    Run a function with a timeout.
    
    Args:
        func: Function to execute
        timeout_seconds: Maximum time to allow (default: 5 minutes)
        
    Returns:
        Result of the function call
        
    Raises:
        Any exception raised by the function
        SystemExit: If timeout occurs
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        result = func()
        signal.alarm(0)  # Cancel the alarm
        return result
    except:
        signal.alarm(0)  # Cancel the alarm
        raise
