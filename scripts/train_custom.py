#!/usr/bin/env python3
"""
Train Bruce AI - Custom Domain Training from Files
Ingest .txt, .md, .pdf files and URLs from a directory into the knowledge base.
"""

import argparse
import glob
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_ingestor import KnowledgeIngestor


def read_text_file(filepath: str) -> str:
    """Read a text file with encoding fallbacks."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    print(f"    WARNING: Could not decode {filepath}")
    return ""


def read_pdf_file(filepath: str) -> str:
    """Read a PDF file, with fallback if PyPDF2/pdfplumber not available."""
    # Try pdfplumber first (better extraction)
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        pass

    # Try PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        pass

    print(f"    WARNING: No PDF library available (install pdfplumber or PyPDF2). Skipping {filepath}")
    return ""


def ingest_directory(
    source_dir: str,
    domain: str,
    ingestor: KnowledgeIngestor,
) -> dict:
    """Ingest all supported files from a directory."""
    results = {
        "files_processed": 0,
        "files_skipped": 0,
        "urls_processed": 0,
        "urls_failed": 0,
        "total_chunks": 0,
        "total_chars": 0,
        "errors": [],
    }

    if not os.path.isdir(source_dir):
        print(f"  ERROR: Directory not found: {source_dir}")
        return results

    # Collect supported files
    patterns = ["*.txt", "*.md", "*.pdf"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(source_dir, "**", pattern), recursive=True))
    files.sort()

    print(f"\n{'='*60}")
    print(f"  Bruce AI - Custom Domain Training")
    print(f"  Source: {source_dir}")
    print(f"  Domain: {domain}")
    print(f"  Files found: {len(files)}")
    print(f"{'='*60}\n")

    # Process files
    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        print(f"  [{i}/{len(files)}] Processing: {filename}...", end=" ")
        start = time.time()

        try:
            if ext in (".txt", ".md"):
                text = read_text_file(filepath)
            elif ext == ".pdf":
                text = read_pdf_file(filepath)
            else:
                print("SKIPPED (unsupported)")
                results["files_skipped"] += 1
                continue

            if not text.strip():
                print("SKIPPED (empty)")
                results["files_skipped"] += 1
                continue

            result = ingestor.ingest_text(
                text=text,
                source=f"custom/{domain}/{filename}",
                metadata={
                    "domain": domain,
                    "source_file": filepath,
                    "filename": filename,
                    "file_type": ext,
                    "training_type": "custom_document",
                },
            )

            elapsed = time.time() - start
            chunks = result.get("chunks_added", 0)
            chars = result.get("total_chars", 0)
            results["total_chunks"] += chunks
            results["total_chars"] += chars
            results["files_processed"] += 1

            print(f"OK ({chunks} chunks, {chars} chars, {elapsed:.2f}s)")

        except Exception as e:
            print(f"ERROR: {e}")
            results["errors"].append({"file": filepath, "error": str(e)})
            results["files_skipped"] += 1

    # Process URLs from urls.txt
    urls_file = os.path.join(source_dir, "urls.txt")
    if os.path.exists(urls_file):
        print(f"\n  Processing URLs from urls.txt...")
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        for j, url in enumerate(urls, 1):
            print(f"  [URL {j}/{len(urls)}] Ingesting: {url}...", end=" ")
            start = time.time()

            try:
                result = ingestor.ingest_url(
                    url=url,
                    metadata={
                        "domain": domain,
                        "training_type": "custom_url",
                    },
                )

                elapsed = time.time() - start
                if result.get("status") == "ingested":
                    chunks = result.get("chunks_added", 0)
                    results["total_chunks"] += chunks
                    results["urls_processed"] += 1
                    print(f"OK ({chunks} chunks, {elapsed:.2f}s)")
                else:
                    results["urls_failed"] += 1
                    print(f"FAILED: {result.get('error', 'unknown')}")

            except Exception as e:
                results["urls_failed"] += 1
                print(f"ERROR: {e}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Files processed: {results['files_processed']}")
    print(f"  Files skipped: {results['files_skipped']}")
    print(f"  URLs processed: {results['urls_processed']}")
    print(f"  URLs failed: {results['urls_failed']}")
    print(f"  Total chunks: {results['total_chunks']}")
    print(f"  Total characters: {results['total_chars']}")
    print(f"{'='*60}")

    if results["errors"]:
        print(f"\n  Errors:")
        for err in results["errors"]:
            print(f"    - {err['file']}: {err['error']}")

    stats = ingestor.get_knowledge_stats()
    print(f"\n  Knowledge Base Stats:")
    print(f"  - Total chunks in KB: {stats['total_chunks']}")
    print(f"  - Total sources: {stats['total_sources']}")
    print(f"  - Disk size: {stats['disk_size_bytes'] / 1024:.1f} KB")
    print()

    return results


def main():
    parser = argparse.ArgumentParser(description="Train Bruce AI from custom documents")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to directory containing training documents (.txt, .md, .pdf, urls.txt)",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="general",
        help="Domain label for the ingested knowledge (e.g., 'shipping', 'crypto', 'finance')",
    )
    args = parser.parse_args()

    source_dir = os.path.abspath(args.source)
    ingestor = KnowledgeIngestor()
    ingest_directory(source_dir, args.domain, ingestor)


if __name__ == "__main__":
    main()
