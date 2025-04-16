import os
import sys
import subprocess
import platform

def install_talib():
    """Install TA-Lib from source, bypassing pip's build process."""
    print("Installing TA-Lib from source...")
    
    # Set environment variables
    os.environ['TA_LIBRARY_PATH'] = '/usr/lib'
    os.environ['TA_INCLUDE_PATH'] = '/usr/include'
    
    # Clone the ta-lib-python repository
    subprocess.check_call([
        sys.executable, '-m', 'pip', 'install', 
        'git+https://github.com/mrjbq7/ta-lib.git@master'
    ])
    
    print("TA-Lib installation completed.")

if __name__ == "__main__":
    install_talib()