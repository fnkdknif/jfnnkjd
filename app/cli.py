"""
Command-line interface for Local Knowledge Base.
"""
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.core.config import get_config
from app.core.logging import get_logger
from app.db.session import init_db, get_db_session
from app.core.parser.base import get_parser_factory
from app.core.chunker import create_chunker
from app.models.documents import Document, DocumentType, DocumentStatus
from app.core.utils import get_file_info, calculate_file_hash
from datetime import datetime

console = Console()
logger = get_logger("lkb-cli")


@click.group()
@click.version_option(version="0.1.0")
@click.option("--config", type=click.Path(exists=True), help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cli(config: Optional[str], verbose: bool):
    """
    Local Knowledge Base - CLI Tool

    A local, explainable RAG system for knowledge workers.
    """
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Initialize database
    init_db()
    console.print("[green]✓[/green] Database initialized")


@cli.command()
def init():
    """Initialize the knowledge base."""
    config = get_config()

    with console.status("[bold green]Initializing knowledge base..."):
        # Ensure directories exist
        config.ensure_paths()

        # Initialize database
        init_db()

    console.print("[green]✓[/green] Knowledge base initialized successfully!")
    console.print(f"Data directory: {config.paths.data_root}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--recursive", "-r", is_flag=True, help="Recursively ingest directory")
def ingest(path: str, recursive: bool):
    """
    Ingest a document or directory.

    Args:
        path: Path to file or directory
        recursive: Process directories recursively
    """
    path_obj = Path(path)

    if path_obj.is_file():
        _ingest_file(path_obj)
    elif path_obj.is_dir():
        _ingest_directory(path_obj, recursive)
    else:
        console.print(f"[red]✗[/red] Invalid path: {path}")
        sys.exit(1)


def _ingest_file(file_path: Path):
    """Ingest a single file."""
    console.print(f"\n[bold]Ingesting:[/bold] {file_path.name}")

    # Check if parser is available
    parser_factory = get_parser_factory()
    parser = parser_factory.get_parser(file_path)

    if not parser:
        console.print(f"[yellow]⚠[/yellow] Unsupported file type: {file_path.suffix}")
        return

    session = get_db_session()

    try:
        # Get file info
        file_info = get_file_info(file_path)

        # Check if already ingested
        existing = session.query(Document).filter(
            Document.file_hash == file_info["hash"]
        ).first()

        if existing:
            console.print(f"[yellow]⚠[/yellow] Document already exists (ID: {existing.id})")

            # Check if file was modified
            if existing.file_mtime < file_info["mtime"]:
                console.print("[blue]ℹ[/blue] File was modified, will re-index")
                # TODO: Implement incremental update

            session.close()
            return

        # Parse document
        with console.status("[bold green]Parsing document..."):
            start_time = datetime.now()
            parsed_doc = parser.parse(file_path)
            parse_duration = (datetime.now() - start_time).total_seconds() * 1000

        console.print(f"[green]✓[/green] Parsed in {parse_duration:.0f}ms")
        console.print(f"  Sections: {len(parsed_doc.sections)}")
        console.print(f"  Pages: {parsed_doc.page_count or 'N/A'}")

        # Chunk document
        with console.status("[bold green]Chunking document..."):
            chunker = create_chunker()
            chunks = chunker.chunk_document(parsed_doc)

        console.print(f"[green]✓[/green] Created {len(chunks)} chunks")

        # Create document record
        doc_type = DocumentType(file_path.suffix.lower().lstrip("."))

        doc = Document(
            file_path=str(file_path.absolute()),
            file_name=file_path.name,
            file_type=doc_type,
            file_size=file_info["size"],
            file_hash=file_info["hash"],
            file_mtime=file_info["mtime"],
            title=parsed_doc.title,
            author=parsed_doc.author,
            language=parsed_doc.language,
            page_count=parsed_doc.page_count,
            word_count=parsed_doc.get_word_count(),
            status=DocumentStatus.PARSING,
            parsed_at=datetime.now(),
            doc_metadata=parsed_doc.metadata,
            chunk_count=len(chunks),
        )

        session.add(doc)
        session.commit()
        session.refresh(doc)

        console.print(f"[green]✓[/green] Document saved (ID: {doc.id})")

        # TODO: Index chunks (will implement in Phase 1)
        console.print("[yellow]⚠[/yellow] Indexing not yet implemented")

        session.close()

    except Exception as e:
        logger.error(f"Failed to ingest {file_path}", error=str(e))
        console.print(f"[red]✗[/red] Error: {e}")
        session.close()
        sys.exit(1)


def _ingest_directory(dir_path: Path, recursive: bool):
    """Ingest all supported files in directory."""
    parser_factory = get_parser_factory()

    # Find all supported files
    files = []

    if recursive:
        for ext in [".pdf", ".md", ".markdown", ".txt"]:
            files.extend(dir_path.rglob(f"*{ext}"))
    else:
        for ext in [".pdf", ".md", ".markdown", ".txt"]:
            files.extend(dir_path.glob(f"*{ext}"))

    if not files:
        console.print("[yellow]⚠[/yellow] No supported files found")
        return

    console.print(f"[bold]Found {len(files)} file(s) to ingest[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Ingesting...", total=len(files))

        for file_path in files:
            progress.update(task, description=f"Processing {file_path.name}")
            _ingest_file(file_path)
            progress.advance(task)


@cli.command()
@click.option("--status", type=str, help="Filter by status")
@click.option("--limit", type=int, default=20, help="Number of documents to show")
def list(status: Optional[str], limit: int):
    """List ingested documents."""
    session = get_db_session()

    query = session.query(Document)

    if status:
        query = query.filter(Document.status == status)

    docs = query.order_by(Document.created_at.desc()).limit(limit).all()

    if not docs:
        console.print("[yellow]No documents found[/yellow]")
        session.close()
        return

    # Create table
    table = Table(title=f"Documents ({len(docs)})")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Title", style="green")
    table.add_column("Type", style="blue", width=8)
    table.add_column("Chunks", justify="right", width=8)
    table.add_column("Status", style="magenta", width=12)
    table.add_column("Created", style="yellow", width=12)

    for doc in docs:
        title = doc.title or doc.file_name
        if len(title) > 50:
            title = title[:47] + "..."

        created = doc.created_at.strftime("%Y-%m-%d")

        table.add_row(
            str(doc.id),
            title,
            doc.file_type.value,
            str(doc.chunk_count),
            doc.status.value,
            created,
        )

    console.print(table)
    session.close()


@cli.command()
@click.argument("doc_id", type=int)
def info(doc_id: int):
    """Show detailed information about a document."""
    session = get_db_session()

    doc = session.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        console.print(f"[red]✗[/red] Document {doc_id} not found")
        session.close()
        sys.exit(1)

    # Display document info
    console.print(f"\n[bold]Document ID:[/bold] {doc.id}")
    console.print(f"[bold]Title:[/bold] {doc.title or 'N/A'}")
    console.print(f"[bold]Author:[/bold] {doc.author or 'N/A'}")
    console.print(f"[bold]File:[/bold] {doc.file_name}")
    console.print(f"[bold]Type:[/bold] {doc.file_type.value}")
    console.print(f"[bold]Size:[/bold] {doc.file_size / 1024:.1f} KB")
    console.print(f"[bold]Status:[/bold] {doc.status.value}")
    console.print(f"[bold]Chunks:[/bold] {doc.chunk_count}")
    console.print(f"[bold]Pages:[/bold] {doc.page_count or 'N/A'}")
    console.print(f"[bold]Words:[/bold] {doc.word_count or 'N/A'}")
    console.print(f"[bold]Language:[/bold] {doc.language or 'N/A'}")
    console.print(f"[bold]Created:[/bold] {doc.created_at}")
    console.print(f"[bold]Updated:[/bold] {doc.updated_at}")

    if doc.doc_metadata:
        console.print(f"\n[bold]Metadata:[/bold]")
        for key, value in doc.doc_metadata.items():
            console.print(f"  {key}: {value}")

    session.close()


@cli.command()
@click.argument("query")
def search(query: str):
    """Search documents (not yet implemented)."""
    console.print(f"[yellow]Searching for:[/yellow] {query}")
    console.print("[red]Search not yet implemented (Phase 1)[/red]")


@cli.command()
@click.argument("query")
def ask(query: str):
    """Ask a question (not yet implemented)."""
    console.print(f"[yellow]Question:[/yellow] {query}")
    console.print("[red]RAG not yet implemented (Phase 1)[/red]")


@cli.command()
def status():
    """Show system status."""
    config = get_config()
    session = get_db_session()

    # Count documents
    total_docs = session.query(Document).count()
    completed_docs = session.query(Document).filter(
        Document.status == DocumentStatus.COMPLETED
    ).count()

    # Count chunks
    from app.models.chunks import Chunk
    total_chunks = session.query(Chunk).count()

    console.print("\n[bold]Local Knowledge Base Status[/bold]\n")
    console.print(f"Documents: {total_docs} ({completed_docs} indexed)")
    console.print(f"Chunks: {total_chunks}")
    console.print(f"Data directory: {config.paths.data_root}")
    console.print(f"Database: {config.paths.database}")

    session.close()


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error("CLI error", error=str(e))
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
