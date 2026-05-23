import subprocess
import sys
import os
import os

def run_scripts():
    scripts = ['create-csv.py','sql-filltables.py', 'sql-duplicates.py','sql-empty.py', 'sql-cleaning.py', 'function_cleaning.py','balance.py', 'log.py']

    for script in scripts:
        print(f"\n--- Running {script} ---")
        result = subprocess.run([sys.executable, script])

        if result.returncode != 0:
            print(f"Error in {script}. Stopping execution.")
            break
        else:
            print(f"Successfully completed {script}")


if __name__ == "__main__":
    run_scripts()