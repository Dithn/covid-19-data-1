"""
Merges all COVID-19 data into a 'megafile';
- Follows a long format of 1 row per country & date, and variables as columns;
- Published in CSV, XLSX, and JSON formats;
- Includes derived variables that can't be easily calculated, such as X per capita;
- Includes country ISO codes in a column next to country names.
"""

from cowidev.megafile.generate import generate_megafile
from cowidev.utils.log import get_logger


if __name__ == "__main__":
    logger = get_logger()
    generate_megafile(logger)
