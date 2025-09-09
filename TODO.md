# TODO: Add --output-dir CLI Argument

## Tasks
- [x] Modify pogorarity/scraper.py to add output_dir attribute in __init__
- [x] Modify export_to_csv method in scraper.py to use output_dir for filename
- [x] Add os import to scraper.py for path operations
- [x] Modify pogorarity/cli.py to add --output-dir argument to argparse
- [x] Test the new CLI argument functionality

## Notes
- Use relative imports as per project structure
- Ensure output directory is created if it doesn't exist
- Default behavior remains unchanged if --output-dir not specified
