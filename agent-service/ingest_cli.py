"""
ingest_cli.py — CLI tool for ingesting documents from local folder or Google Drive.

Usage:
    uv run python ingest_cli.py --source ./docs
    uv run python ingest_cli.py --drive-folder-id <FOLDER_ID>
"""

import argparse
from dotenv import load_dotenv

load_dotenv()

from services.ingest import ingest_texts, read_folder, read_google_drive


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the vector store.")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source",          help="Local folder path")
    group.add_argument("--drive-folder-id", help="Google Drive folder ID")
    args = parser.parse_args()

    def on_progress(filename, chunk_count):
        print(f"  ✓ {filename} — {chunk_count} chunks stored")

    if args.source:
        source_iter = read_folder(args.source)
    else:
        source_iter = read_google_drive(args.drive_folder_id)

    print("Starting ingestion …\n")
    result = ingest_texts(source_iter, on_progress=on_progress)
    print(f"\n✓ Done — {result['files']} file(s), {result['chunks']:,} chunks stored")


if __name__ == "__main__":
    main()
