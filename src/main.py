import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from config import DEFAULT_RENDER_DPI
from classification.classify_slide_batch import classify_unclassified_slides
from content.analyze_content import analyze_content
from database.repository import get_database_summary
from database.repository import get_classification_summary
from database.repository import get_content_summary
from database.schema import initialize_database
from embeddings.build_vector_index import embed_classified_slides
from embeddings.embedding_repository import get_embedding_summary
from embeddings.search_similar_slides import search_similar_slides_by_text
from ingestion.collect_library import ingest_deck
from pptx_generation.content_first_deck_generator import (
    generate_content_first_deck_from_file,
    generate_content_first_deck_from_text,
)
from pptx_generation.editable_reference_deck_generator import (
    generate_editable_reference_deck_from_file,
    generate_editable_reference_deck_from_recommendation,
    generate_editable_reference_deck_from_text,
)
from pptx_generation.placeholder_deck_generator import (
    generate_placeholder_deck_from_file,
    generate_placeholder_deck_from_recommendation,
    generate_placeholder_deck_from_text,
)
from pptx_generation.pptx_repository import list_generated_decks, python_pptx_available
from pptx_generation.reference_deck_generator import (
    generate_reference_deck_from_file,
    generate_reference_deck_from_recommendation,
    generate_reference_deck_from_text,
)
from quality_control.generated_deck_qa import review_generated_deck
from quality_control.qa_report_builder import build_markdown_qa_report, build_terminal_qa_summary
from quality_control.qa_repository import (
    find_latest_generated_deck,
    find_matching_metadata_for_deck,
    find_matching_notes_for_deck,
    list_qa_reports,
    save_qa_json,
    save_qa_markdown,
)
from quality_control.recommendation_qa import review_recommendation
from recommendation.recommend_from_content import recommend_from_content
from utils.file_utils import ensure_project_directories, resolve_input_file
from utils.logging_utils import configure_logging


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slide Intelligence System CLI",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Convert a PDF/PPTX deck into slide images, extracted text, and metadata JSON.",
    )
    ingest_parser.add_argument(
        "--file",
        help="Path to a PDF or PPTX deck.",
    )
    ingest_parser.add_argument(
        "--folder",
        help="Path to a folder containing PDF/PPTX decks.",
    )
    ingest_parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_RENDER_DPI,
        help=f"Render DPI for slide images. Default: {DEFAULT_RENDER_DPI}.",
    )

    subparsers.add_parser(
        "db-init",
        help="Create the SQLite database and tables if they do not exist.",
    )

    subparsers.add_parser(
        "db-summary",
        help="Print database deck and slide counts.",
    )

    classify_parser = subparsers.add_parser(
        "classify",
        help="Classify unclassified slides using the OpenAI API.",
    )
    classify_parser.add_argument(
        "--limit",
        type=int,
        help="Classify up to this many slides.",
    )
    classify_parser.add_argument(
        "--deck",
        help="Classify unclassified slides for this deck name.",
    )
    classify_parser.add_argument(
        "--all",
        action="store_true",
        help="Classify all unclassified slides.",
    )
    classify_parser.add_argument(
        "--force",
        action="store_true",
        help="Reclassify slides even if classification already exists.",
    )

    subparsers.add_parser(
        "classification-summary",
        help="Print classification coverage and type counts.",
    )

    analyze_parser = subparsers.add_parser(
        "analyze-content",
        help="Extract and analyze source content for slide/deck recommendation.",
    )
    analyze_parser.add_argument("--file", help="Path to source content file.")
    analyze_parser.add_argument("--text", help="Pasted source text.")
    analyze_parser.add_argument("--goal", help="Optional presentation goal.")
    analyze_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="auto",
        help="Requested output mode.",
    )

    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Analyze source content and recommend a slide/deck structure.",
    )
    recommend_parser.add_argument("--file", help="Path to source content file.")
    recommend_parser.add_argument("--text", help="Pasted source text.")
    recommend_parser.add_argument("--goal", help="Optional presentation goal.")
    recommend_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="auto",
        help="Requested output mode.",
    )
    recommend_parser.add_argument(
        "--prompt",
        action="store_true",
        help="Also save a reusable TXT prompt.",
    )

    subparsers.add_parser(
        "content-summary",
        help="Print content library and recommendation summary.",
    )

    embed_parser = subparsers.add_parser(
        "embed-slides",
        help="Generate text embeddings for classified slides.",
    )
    embed_parser.add_argument("--limit", type=int, help="Embed up to this many slides.")
    embed_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings even when they already exist.",
    )

    search_parser = subparsers.add_parser(
        "search-slides",
        help="Search the slide library using semantic vector search.",
    )
    search_parser.add_argument("--query", required=True, help="Search query text.")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results.")

    subparsers.add_parser(
        "embedding-summary",
        help="Print embedding coverage and latest embedded slides.",
    )

    generate_parser = subparsers.add_parser(
        "generate-pptx",
        help="Generate an editable placeholder PPTX from a recommendation JSON file.",
    )
    generate_parser.add_argument(
        "--recommendation",
        required=True,
        help="Path to recommendation JSON. Use output/recommendations/latest_recommendation.json for the latest file.",
    )
    generate_parser.add_argument("--output", help="Output PPTX path.")

    generate_text_parser = subparsers.add_parser(
        "generate-pptx-from-text",
        help="Run the content-first consultant flow from pasted text, then generate a polished PPTX draft.",
    )
    generate_text_parser.add_argument("--text", required=True, help="Pasted source text.")
    generate_text_parser.add_argument("--goal", help="Optional presentation goal.")
    generate_text_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="deck",
        help="Requested output mode.",
    )
    generate_text_parser.add_argument("--output", help="Output PPTX path.")

    generate_file_parser = subparsers.add_parser(
        "generate-pptx-from-file",
        help="Run the content-first consultant flow from a source file, then generate a polished PPTX draft.",
    )
    generate_file_parser.add_argument("--file", required=True, help="Path to source content file.")
    generate_file_parser.add_argument("--goal", help="Optional presentation goal.")
    generate_file_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="deck",
        help="Requested output mode.",
    )
    generate_file_parser.add_argument("--output", help="Output PPTX path.")

    subparsers.add_parser(
        "generated-deck-summary",
        help="Print generated placeholder deck summary.",
    )

    reference_parser = subparsers.add_parser(
        "generate-reference-pptx",
        help="Generate a reference-slide-background PPTX from a recommendation JSON file.",
    )
    reference_parser.add_argument(
        "--recommendation",
        required=True,
        help="Path to recommendation JSON. Use output/recommendations/latest_recommendation.json for the latest file.",
    )
    reference_parser.add_argument("--output", help="Output PPTX path.")

    reference_text_parser = subparsers.add_parser(
        "generate-reference-pptx-from-text",
        help="Run recommendation from pasted text, then generate a reference-style PPTX.",
    )
    reference_text_parser.add_argument("--text", required=True, help="Pasted source text.")
    reference_text_parser.add_argument("--goal", help="Optional presentation goal.")
    reference_text_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="deck",
        help="Requested output mode.",
    )
    reference_text_parser.add_argument("--output", help="Output PPTX path.")

    reference_file_parser = subparsers.add_parser(
        "generate-reference-pptx-from-file",
        help="Run recommendation from a source file, then generate a reference-style PPTX.",
    )
    reference_file_parser.add_argument("--file", required=True, help="Path to source content file.")
    reference_file_parser.add_argument("--goal", help="Optional presentation goal.")
    reference_file_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="deck",
        help="Requested output mode.",
    )
    reference_file_parser.add_argument("--output", help="Output PPTX path.")

    editable_parser = subparsers.add_parser(
        "generate-editable-reference-pptx",
        help="Generate a PPTX by cloning matched source slides where possible.",
    )
    editable_parser.add_argument(
        "--recommendation",
        required=True,
        help="Path to recommendation JSON. Use output/recommendations/latest_recommendation.json for the latest file.",
    )
    editable_parser.add_argument("--output", help="Output PPTX path.")

    editable_text_parser = subparsers.add_parser(
        "generate-editable-reference-pptx-from-text",
        help="Run recommendation from pasted text, then clone matched source slides where possible.",
    )
    editable_text_parser.add_argument("--text", required=True, help="Pasted source text.")
    editable_text_parser.add_argument("--goal", help="Optional presentation goal.")
    editable_text_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="deck",
        help="Requested output mode.",
    )
    editable_text_parser.add_argument("--output", help="Output PPTX path.")

    editable_file_parser = subparsers.add_parser(
        "generate-editable-reference-pptx-from-file",
        help="Run recommendation from a source file, then clone matched source slides where possible.",
    )
    editable_file_parser.add_argument("--file", required=True, help="Path to source content file.")
    editable_file_parser.add_argument("--goal", help="Optional presentation goal.")
    editable_file_parser.add_argument(
        "--mode",
        choices=["slide", "deck", "audit", "classify", "auto"],
        default="deck",
        help="Requested output mode.",
    )
    editable_file_parser.add_argument("--output", help="Output PPTX path.")

    review_rec_parser = subparsers.add_parser(
        "review-recommendation",
        help="Run QA on a recommendation JSON file.",
    )
    review_rec_parser.add_argument("--recommendation", required=True, help="Path to recommendation JSON.")
    review_rec_parser.add_argument("--output-json", help="Optional QA JSON output path.")
    review_rec_parser.add_argument("--output-md", help="Optional QA Markdown output path.")

    review_deck_parser = subparsers.add_parser(
        "review-generated-deck",
        help="Run QA on a generated PPTX deck.",
    )
    review_deck_parser.add_argument("--pptx", required=True, help="Path to generated PPTX.")
    review_deck_parser.add_argument("--metadata", help="Optional generation metadata JSON path.")
    review_deck_parser.add_argument("--notes", help="Optional speaker/build notes markdown path.")
    review_deck_parser.add_argument("--output-json", help="Optional QA JSON output path.")
    review_deck_parser.add_argument("--output-md", help="Optional QA Markdown output path.")

    subparsers.add_parser(
        "review-latest-generated-deck",
        help="Find and QA the latest generated PPTX deck.",
    )

    subparsers.add_parser(
        "qa-summary",
        help="Print QA report summary.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)
    ensure_project_directories()

    if args.command == "ingest":
        if not args.file and not args.folder:
            print("ERROR: provide either --file or --folder", file=sys.stderr)
            return 1

        if args.file and args.folder:
            print("ERROR: provide only one of --file or --folder", file=sys.stderr)
            return 1

        try:
            files = (
                [resolve_input_file(args.file)]
                if args.file
                else _deck_files_in_folder(resolve_input_file(args.folder))
            )
            if not files:
                print("ERROR: no PDF or PPTX decks found", file=sys.stderr)
                return 1

            summaries = [ingest_deck(file_path, dpi=args.dpi) for file_path in files]
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        _print_ingestion_summary(summaries)
        return 0

    if args.command == "db-init":
        initialize_database()
        print("Database initialized: data/slide_library.sqlite")
        return 0

    if args.command == "db-summary":
        _print_database_summary(get_database_summary())
        return 0

    if args.command == "classify":
        if not args.all and not args.deck and args.limit is None:
            print("ERROR: provide --limit, --deck, or --all", file=sys.stderr)
            return 1
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before running classification.",
                file=sys.stderr,
            )
            return 1

        results = classify_unclassified_slides(
            limit=args.limit,
            deck_name=args.deck,
            force=args.force,
        )
        _print_classification_results(results)
        return 0

    if args.command == "classification-summary":
        _print_classification_summary(get_classification_summary())
        return 0

    if args.command == "analyze-content":
        if not _validate_content_input(args.file, args.text):
            return 1
        try:
            analysis = analyze_content(
                file_path=args.file,
                text=args.text,
                user_goal=args.goal,
                mode=args.mode,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_content_analysis_result(analysis)
        return 0

    if args.command == "recommend":
        if not _validate_content_input(args.file, args.text):
            return 1
        try:
            recommendation = recommend_from_content(
                file_path=args.file,
                text=args.text,
                user_goal=args.goal,
                mode=args.mode,
                prompt_output=args.prompt,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_recommendation_result(recommendation)
        return 0

    if args.command == "content-summary":
        _print_content_summary(get_content_summary())
        return 0

    if args.command == "embed-slides":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating embeddings.",
                file=sys.stderr,
            )
            return 1
        summary = embed_classified_slides(force=args.force, limit=args.limit)
        _print_embedding_run_summary(summary)
        return 0

    if args.command == "search-slides":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before searching embeddings.",
                file=sys.stderr,
            )
            return 1
        try:
            results = search_similar_slides_by_text(args.query, top_k=args.top_k)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_slide_search_results(results)
        return 0

    if args.command == "embedding-summary":
        _print_embedding_summary(get_embedding_summary())
        return 0

    if args.command == "generate-pptx":
        try:
            metadata = generate_placeholder_deck_from_recommendation(
                recommendation_path=args.recommendation,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-pptx-from-text":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating PPTX from text.",
                file=sys.stderr,
            )
            return 1
        try:
            metadata = generate_content_first_deck_from_text(
                text=args.text,
                goal=args.goal,
                mode=args.mode,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-pptx-from-file":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating PPTX from a file.",
                file=sys.stderr,
            )
            return 1
        try:
            metadata = generate_content_first_deck_from_file(
                file_path=args.file,
                goal=args.goal,
                mode=args.mode,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generated-deck-summary":
        _print_generated_deck_summary()
        return 0

    if args.command == "generate-reference-pptx":
        try:
            metadata = generate_reference_deck_from_recommendation(
                recommendation_path=args.recommendation,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-reference-pptx-from-text":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating reference PPTX from text.",
                file=sys.stderr,
            )
            return 1
        try:
            metadata = generate_reference_deck_from_text(
                text=args.text,
                goal=args.goal,
                mode=args.mode,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-reference-pptx-from-file":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating reference PPTX from a file.",
                file=sys.stderr,
            )
            return 1
        try:
            metadata = generate_reference_deck_from_file(
                file_path=args.file,
                goal=args.goal,
                mode=args.mode,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-editable-reference-pptx":
        try:
            metadata = generate_editable_reference_deck_from_recommendation(
                recommendation_path=args.recommendation,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-editable-reference-pptx-from-text":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating editable reference PPTX from text.",
                file=sys.stderr,
            )
            return 1
        try:
            metadata = generate_editable_reference_deck_from_text(
                text=args.text,
                goal=args.goal,
                mode=args.mode,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "generate-editable-reference-pptx-from-file":
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print(
                "ERROR: OPENAI_API_KEY is missing. Add it to .env before generating editable reference PPTX from a file.",
                file=sys.stderr,
            )
            return 1
        try:
            metadata = generate_editable_reference_deck_from_file(
                file_path=args.file,
                goal=args.goal,
                mode=args.mode,
                output_path=args.output,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        _print_generated_deck_result(metadata)
        return 0

    if args.command == "review-recommendation":
        try:
            qa_result = review_recommendation(args.recommendation)
            _save_and_print_qa(qa_result, args.output_json, args.output_md)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "review-generated-deck":
        try:
            metadata_path = args.metadata or find_matching_metadata_for_deck(args.pptx)
            notes_path = args.notes or find_matching_notes_for_deck(args.pptx)
            qa_result = review_generated_deck(args.pptx, metadata_path, notes_path)
            _save_and_print_qa(qa_result, args.output_json, args.output_md)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "review-latest-generated-deck":
        latest = find_latest_generated_deck()
        if latest is None:
            print("ERROR: no generated PPTX decks found in output/generated_decks", file=sys.stderr)
            return 1
        try:
            qa_result = review_generated_deck(
                latest,
                find_matching_metadata_for_deck(latest),
                find_matching_notes_for_deck(latest),
            )
            _save_and_print_qa(qa_result)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "qa-summary":
        _print_qa_summary()
        return 0

    parser.print_help()
    return 1


def _deck_files_in_folder(folder_path: Path) -> list[Path]:
    if not folder_path.exists():
        raise FileNotFoundError(f"Input folder not found: {folder_path}")
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {folder_path}")

    return sorted(
        path.resolve()
        for path in folder_path.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".pdf", ".pptx"}
        and not any(part.startswith(".") for part in path.relative_to(folder_path).parts)
    )


def _print_ingestion_summary(summaries) -> None:
    total_slides = sum(summary.slide_count for summary in summaries)
    total_images = sum(summary.image_count for summary in summaries)
    total_text = sum(summary.text_count for summary in summaries)
    total_metadata = sum(summary.metadata_count for summary in summaries)

    print("Ingestion complete")
    print(f"Decks processed: {len(summaries)}")
    print(f"Slides processed: {total_slides}")
    print(f"Images written: {total_images}")
    print(f"Text files written: {total_text}")
    print(f"Metadata files written: {total_metadata}")

    for summary in summaries:
        print(
            f"- {summary.source_file} "
            f"({summary.source_type}, {summary.slide_count} slides, {summary.render_method})"
        )


def _print_database_summary(summary) -> None:
    print("Database summary")
    print(f"Decks: {summary.deck_count}")
    print(f"Slides: {summary.slide_count}")
    print("Slides by source type:")
    if summary.slides_by_source_type:
        for source_type, slide_count in summary.slides_by_source_type:
            print(f"- {source_type}: {slide_count}")
    else:
        print("- none: 0")

    print("Latest 5 ingested decks:")
    if summary.latest_decks:
        for deck in summary.latest_decks:
            print(
                f"- {deck['deck_name']} "
                f"({deck['source_type']}, {deck['slide_count']} slides) "
                f"{deck['created_at']}"
            )
    else:
        print("- none")


def _print_classification_results(results) -> None:
    classified = [row for row in results if row["status"] in {"classified", "reused_existing_json"}]
    failed = [row for row in results if row["status"] == "failed"]

    print("Classification complete")
    print(f"Slides selected: {len(results)}")
    print(f"Classified/reused: {len(classified)}")
    print(f"Failed: {len(failed)}")

    for row in results:
        if row["status"] == "failed":
            print(
                f"- FAILED {row['deck_name']} slide {row['slide_number']}: "
                f"{row.get('error', 'unknown error')}"
            )
        else:
            print(
                f"- {row['deck_name']} slide {row['slide_number']}: "
                f"{row['slide_type']} / {row['chart_type']} ({row['status']})"
            )


def _print_classification_summary(summary) -> None:
    average_quality = (
        f"{summary.average_quality_score:.1f}"
        if summary.average_quality_score is not None
        else "n/a"
    )

    print("Classification summary")
    print(f"Total slides: {summary.total_slides}")
    print(f"Classified slides: {summary.classified_slides}")
    print(f"Unclassified slides: {summary.unclassified_slides}")
    print(f"Average quality_score: {average_quality}")

    print("Slides by slide_type:")
    if summary.slides_by_slide_type:
        for slide_type, count in summary.slides_by_slide_type:
            print(f"- {slide_type}: {count}")
    else:
        print("- none: 0")

    print("Slides by chart_type:")
    if summary.slides_by_chart_type:
        for chart_type, count in summary.slides_by_chart_type:
            print(f"- {chart_type}: {count}")
    else:
        print("- none: 0")


def _validate_content_input(file_path: str | None, text: str | None) -> bool:
    if not file_path and text is None:
        print("ERROR: provide either --file or --text", file=sys.stderr)
        return False
    if file_path and text is not None:
        print("ERROR: provide only one of --file or --text", file=sys.stderr)
        return False
    return True


def _print_content_analysis_result(analysis) -> None:
    print("Content analysis complete")
    print(f"Content source id: {analysis['content_source_id']}")
    print(f"Source: {analysis['source_name']} ({analysis['source_type']})")
    print(f"Recommended mode: {analysis['recommended_output_mode']}")
    print(f"Primary analysis type: {analysis['primary_analysis_type']}")
    print(f"Likely audience: {analysis['likely_audience']}")
    print(f"Raw text: {analysis['raw_text_path']}")
    print(f"Analysis JSON: {analysis['analysis_json_path']}")
    print(f"Summary: {analysis['content_summary']}")


def _print_recommendation_result(recommendation) -> None:
    slide = recommendation.get("recommended_slide_structure", {})
    print("Recommendation complete")
    print(f"Content source id: {recommendation['content_source_id']}")
    print(f"Recommended mode: {recommendation.get('recommended_output_mode')}")
    print(f"Audience: {recommendation.get('recommended_audience_type')}")
    print(f"Title: {recommendation.get('recommended_slide_or_deck_title')}")
    print(f"Slide type: {slide.get('recommended_slide_type')}")
    print(f"Chart type: {slide.get('recommended_chart_type')}")
    print(f"Recommendation JSON: {recommendation.get('recommendation_json_path')}")
    if recommendation.get("prompt_txt_path"):
        print(f"Reusable prompt TXT: {recommendation['prompt_txt_path']}")
    print(f"Matching method: {recommendation.get('matching_method', 'metadata_match')}")
    print(f"Similar slide patterns found: {len(recommendation.get('similar_slide_patterns_found', []))}")


def _print_content_summary(summary) -> None:
    print("Content library summary")
    print(f"Total content sources: {summary.total_content_sources}")
    print("Sources by source_type:")
    if summary.sources_by_type:
        for source_type, count in summary.sources_by_type:
            print(f"- {source_type}: {count}")
    else:
        print("- none: 0")

    print("Sources by primary_analysis_type:")
    if summary.sources_by_primary_analysis_type:
        for analysis_type, count in summary.sources_by_primary_analysis_type:
            print(f"- {analysis_type}: {count}")
    else:
        print("- none: 0")

    print("Latest 5 content sources:")
    if summary.latest_sources:
        for source in summary.latest_sources:
            print(
                f"- {source['source_name']} "
                f"({source['source_type']}, {source['primary_analysis_type']}, "
                f"{source['recommended_output_mode']}) {source['created_at']}"
            )
    else:
        print("- none")

    print("Latest 5 recommendations:")
    if summary.latest_recommendations:
        for recommendation in summary.latest_recommendations:
            print(
                f"- {recommendation['source_name']} "
                f"({recommendation['output_mode']}, "
                f"{recommendation['recommended_slide_type']}) "
                f"{recommendation['created_at']}"
            )
    else:
        print("- none")


def _print_embedding_run_summary(summary) -> None:
    print("Embedding run complete")
    print(f"Total classified slides: {summary['total_classified_slides']}")
    print(f"Selected slides: {summary['selected_slides']}")
    print(f"Embedded slides: {summary['embedded_slides']}")
    print(f"Skipped slides: {summary['skipped_slides']}")
    print(f"Failed slides: {summary['failed_slides']}")
    print(f"Embedding model: {summary['embedding_model']}")
    for failure in summary.get("failures", [])[:10]:
        print(
            f"- FAILED slide {failure.get('slide_id')} "
            f"({failure.get('deck_name')} slide {failure.get('slide_number')}): "
            f"{failure.get('error')}"
        )


def _print_embedding_summary(summary) -> None:
    print("Embedding summary")
    print(f"Total classified slides: {summary.total_classified_slides}")
    print(f"Slides with text embeddings: {summary.slides_with_text_embeddings}")
    print(f"Slides without text embeddings: {summary.slides_without_text_embeddings}")
    print(f"Embedding model used: {summary.embedding_model or 'n/a'}")
    print(f"Index file path: {summary.index_file_path}")
    print("Latest 5 embedded slides:")
    if summary.latest_embedded_slides:
        for slide in summary.latest_embedded_slides:
            print(
                f"- {slide['deck_name']} slide {slide['slide_number']}: "
                f"{slide['slide_title']} ({slide['slide_type']}) "
                f"{slide['created_at']}"
            )
    else:
        print("- none")


def _print_slide_search_results(results) -> None:
    print("Slide search results")
    if not results:
        print("- no embedding results found")
        return
    for index, result in enumerate(results, start=1):
        print(
            f"{index}. score={result['similarity_score']:.4f} "
            f"{result['deck_name']} slide {result['slide_number']}"
        )
        print(f"   Title: {result.get('slide_title') or ''}")
        print(f"   Slide type: {result.get('slide_type') or ''}")
        print(f"   Chart type: {result.get('chart_type') or ''}")
        print(f"   Layout: {result.get('layout_pattern') or ''}")


def _print_generated_deck_result(metadata) -> None:
    if metadata.get("generation_mode") == "content_first_consultant":
        print("Content-first consultant PPTX generated")
    elif metadata.get("reference_background_mode"):
        print("Reference-style PPTX generated")
    else:
        print("Placeholder PPTX generated")
    print(f"Output PPTX: {metadata.get('output_path')}")
    print(f"Metadata JSON: {metadata.get('metadata_path')}")
    print(f"Speaker notes markdown: {metadata.get('speaker_notes_path')}")
    print(f"Slides: {metadata.get('number_of_slides')}")
    print(f"Content slides: {metadata.get('number_of_content_slides')}")
    print(f"Matching method: {metadata.get('matching_method')}")
    if metadata.get("generation_mode") == "content_first_consultant":
        print(f"Content sufficiency: {metadata.get('content_sufficiency_level')} ({metadata.get('content_sufficiency_score')}/100)")
        print(f"Template shells: {metadata.get('template_shell_count', 0)}")
        print(f"Custom layouts: {metadata.get('custom_layout_count', 0)}")
        if metadata.get("source_grounding_report_path"):
            print(f"Source grounding report: {metadata.get('source_grounding_report_path')}")
    if metadata.get("reference_background_mode"):
        print(f"Reference background mode: {metadata.get('reference_background_mode')}")
        if "content_slides_cloned_from_source_pptx" in metadata:
            print(
                "Cloned source slides: "
                f"{metadata.get('content_slides_cloned_from_source_pptx', 0)}/"
                f"{metadata.get('number_of_content_slides', 0)}"
            )
            print(f"Image fallbacks: {metadata.get('content_slides_with_image_fallback', 0)}")
        else:
            print(
                "Reference backgrounds: "
                f"{metadata.get('content_slides_with_reference_background', 0)}/"
                f"{metadata.get('number_of_content_slides', 0)}"
            )
    references = metadata.get("referenced_template_slides", [])
    print(f"Referenced template slides: {len(references)}")


def _print_generated_deck_summary() -> None:
    decks = list_generated_decks(limit=5)
    print("Generated deck summary")
    print(f"Generated decks: {len(list_generated_decks(limit=100000))}")
    print("Output folder: output/generated_decks")
    print(f"python-pptx available: {'yes' if python_pptx_available() else 'no'}")
    print("Latest generated decks:")
    if not decks:
        print("- none")
        print("Last generation status: n/a")
        return
    for deck in decks:
        metadata = deck.get("metadata") or {}
        print(
            f"- {deck['file_name']} "
            f"({metadata.get('number_of_content_slides', 'n/a')} content slides, "
            f"{metadata.get('matching_method', 'n/a')})"
        )
    latest_metadata = decks[0].get("metadata") or {}
    warnings = latest_metadata.get("warnings") or []
    status = "ok" if decks[0].get("metadata_path") else "missing metadata"
    if warnings:
        status += f"; {len(warnings)} warning(s)"
    print(f"Last generation status: {status}")


def _save_and_print_qa(
    qa_result,
    output_json: str | None = None,
    output_md: str | None = None,
) -> None:
    json_path = save_qa_json(qa_result, output_json)
    qa_result["qa_json_path"] = str(json_path)
    markdown = build_markdown_qa_report(qa_result)
    md_path = save_qa_markdown(markdown, output_md, qa_result)
    qa_result["qa_markdown_path"] = str(md_path)
    # Rewrite JSON after adding report output paths, so the report is self-locating.
    save_qa_json(qa_result, json_path)
    print(build_terminal_qa_summary(qa_result))


def _print_qa_summary() -> None:
    reports = list_qa_reports(limit=5)
    all_reports = list_qa_reports(limit=100000)
    print("QA summary")
    print(f"QA reports generated: {len(all_reports)}")
    print("Output folders:")
    print("- output/qa_reports/json")
    print("- output/qa_reports/markdown")
    latest_deck = find_latest_generated_deck()
    print(f"Latest reviewed deck: {Path(reports[0]['reviewed_path']).name if reports and reports[0].get('reviewed_path') else 'n/a'}")
    print(f"Latest generated deck: {latest_deck.name if latest_deck else 'n/a'}")
    print(f"Latest QA score: {reports[0].get('overall_score') if reports else 'n/a'}")
    print("Latest QA reports:")
    if not reports:
        print("- none")
        return
    for report in reports:
        reviewed = Path(str(report.get("reviewed_path") or "unknown")).name
        print(
            f"- {report['file_name']}: {report.get('overall_score', 'n/a')} "
            f"({report.get('rating', 'n/a')}) reviewed={reviewed}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
