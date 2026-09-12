#!/usr/bin/env python3
"""
File:
    cli.py

Version:
    5.0.0

Phase:
    7

Status:
    DEBUGGING

Purpose:
    Command-line interface for AI Job Hunter.

Responsibilities:
    - Parse command-line arguments
    - Load profile based search plans
    - Create SearchRequest objects
    - Initialize Playwright
    - Instantiate connector
    - Instantiate exporter
    - Execute Engine pipeline
    - Print execution summary
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import BrowserContext, sync_playwright

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.registry.connector_factory import ConnectorFactory
from jobs.engine import Engine, ExecutionSummary
from jobs.exporter.base import BaseExporter
from jobs.exporter.csv_exporter import CSVExporter
from jobs.exporter.duckdb_exporter import DuckDBExporter
from jobs.exporter.excel_exporter import ExcelExporter
from jobs.exporter.json_exporter import JSONExporter
from jobs.profiles import build_search_plan, load_profile
from jobs.search import SearchRequest


def main() -> int:
    """
    Main CLI entry point.
    """

    parser = argparse.ArgumentParser(
        description="AI Job Hunter - Search and export job listings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-k",
        "--keyword",
        required=False,
        help="Single search keyword",
    )

    parser.add_argument(
        "-p",
        "--profile",
        required=False,
        help="Profile name (example: crm_manager)",
    )

    parser.add_argument(
        "-l",
        "--location",
        required=False,
        help="Optional location override. Profile locations are used when omitted.",
    )

    parser.add_argument(
    "-c",
    "--connector",
    default="naukri",
    help="Connector name",
)

    parser.add_argument(
        "-e",
        "--exporter",
        default="csv",
        choices=["csv", "excel", "json", "duckdb"],
        help="Export format",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output")
        / datetime.now().strftime("%Y-%m-%d"),
        help="Output directory",
    )

    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Maximum number of jobs to fetch (for testing).",
    )

    args = parser.parse_args()

    if not args.profile and not args.keyword:
        parser.error(
            "Provide either --profile or --keyword"
        )

    with sync_playwright() as playwright:

        browser = None

        try:

            output_dir: Path = args.output

            timestamp = datetime.now().strftime("%H%M%S")

            filename = f"search_{timestamp}"

            #
            # Build Search Requests
            #
            requests: list[SearchRequest]

            profile_type: str | None = None

            if args.profile:

                profile_type = args.profile

                profile = load_profile(
                    args.profile
                )

                profile_locations = (
                    [args.location]
                    if args.location
                    else profile.locations
                )

                search_requests = build_search_plan(
                    profile,
                    profile_locations,
                )

                # Create SearchRequest objects with max_jobs
                requests = []
                for req in search_requests:
                    if isinstance(req, SearchRequest):
                        requests.append(
                            SearchRequest(
                                keyword=req.keyword,
                                location=req.location,
                                page_size=20,
                                max_jobs=args.max_jobs,
                            )
                        )
                    elif isinstance(req, dict):
                        requests.append(
                            SearchRequest(
                                keyword=req.get("keyword", ""),
                                location=req.get("location", args.location),
                                page_size=20,
                                max_jobs=args.max_jobs,
                            )
                        )
                    else:
                        requests.append(
                            SearchRequest(
                                keyword=str(req),
                                location=args.location,
                                page_size=20,
                                max_jobs=args.max_jobs,
                            )
                        )

                print(
                    f"Loaded profile: {args.profile}"
                )

                print(
                    f"Total searches: {len(requests)}"
                )

            else:

                requests = [
                    SearchRequest(
                        keyword=args.keyword,
                        location=args.location,
                        page_size=20,
                        max_jobs=args.max_jobs,
                    )
                ]

            if args.max_jobs:
                print(f"Max jobs per keyword: {args.max_jobs}")

            #
            # Browser
            #
            browser = playwright.chromium.launch(
                headless=True
            )

            context: BrowserContext = (
                browser.new_context()
            )


            #
            # Connectors
            #
            if args.connector.lower() == "all":
                if not args.profile:
                    raise RuntimeError(
                        "Connector 'all' requires --profile"
                    )

                connectors: list[BaseConnector] = [
                    _create_connector("naukri", context),
                    _create_connector("iimjobs", context),
                    _create_connector("foundit", context),
                    _create_connector("linkedin", context),
                    _create_connector("instahyre", context),
                ]
            else:
                connectors = [
                    _create_connector(
                        args.connector,
                        context,
                    )
                ]


            #
            # Exporter
            #
            exporter: BaseExporter = (
                _create_exporter(
                    args.exporter
                )
            )


            #
            # Destination
            #
            if args.exporter == "duckdb":

                destination = (
                    Path("output") / "job_hunter.duckdb"
                )

            else:

                destination = (
                    output_dir
                    / f"{filename}.{_get_extension(args.exporter)}"
                )


            db_path = (
                destination
                if args.exporter == "duckdb"
                else Path("output")
                / "job_hunter.duckdb"
            )


            #
            # Engine
            #
            engine = Engine(
                connectors=connectors,
                exporter=exporter,
                db_path=db_path,
            )


            summary: ExecutionSummary = (
                engine.run(
                    requests,
                    destination,
                    profile_type=profile_type,
                )
            )


            _print_summary(
                summary,
                args.exporter,
            )

            return 0


        except Exception as e:

            print(
                f"❌ Error: {e}",
                file=sys.stderr,
            )

            import traceback
            traceback.print_exc()

            return 1


        finally:

            if browser:

                browser.close()



def _create_connector(
    connector_name: str,
    context: BrowserContext,
) -> BaseConnector:
    """Create a connector through the generic ConnectorFactory."""

    ConnectorFactory.discover()

    try:
        portal = Portal(connector_name.lower())
    except ValueError as exc:
        raise RuntimeError(
            f"Connector '{connector_name}' not supported"
        ) from exc

    for connector_type in ConnectorType:
        if connector_type == ConnectorType.UNKNOWN:
            continue

        if ConnectorFactory.is_registered(
            portal,
            connector_type,
        ):
            connector, _version = ConnectorFactory.create(
                portal=portal,
                connector_type=connector_type,
                context=context,
            )
            return connector

    raise RuntimeError(
        f"Connector '{connector_name}' is not implemented"
    )



def _create_exporter(
    exporter_name: str,
) -> BaseExporter:

    exporters = {
        "csv": CSVExporter,
        "excel": ExcelExporter,
        "json": JSONExporter,
        "duckdb": DuckDBExporter,
    }

    if exporter_name not in exporters:

        raise RuntimeError(
            f"Exporter '{exporter_name}' not supported"
        )

    return exporters[exporter_name]()



def _get_extension(
    exporter_name: str,
) -> str:

    extensions = {
        "csv": "csv",
        "excel": "xlsx",
        "json": "json",
        "duckdb": "duckdb",
    }

    return extensions.get(
        exporter_name,
        "csv",
    )



def _print_summary(
    summary: ExecutionSummary,
    exporter_name: str,
) -> None:

    print("\n" + "=" * 60)
    print("AI JOB HUNTER - EXECUTION SUMMARY")
    print("=" * 60)

    print(
        f"\n📋 Connectors: {', '.join(summary.connectors_used)}"
    )

    print(
        f"📊 Total jobs: {summary.total_jobs}"
    )

    print(
        f"🗑️ Duplicates removed: {summary.duplicate_jobs_removed}"
    )

    print(
        f"✅ Valid jobs: {summary.valid_jobs}"
    )

    print(
        f"❌ Invalid jobs: {summary.invalid_jobs}"
    )

    print(
        f"📤 Exported jobs: {summary.exported_jobs}"
    )

    print(
        f"📁 Output: {summary.destination}"
    )

    print("\n" + "=" * 60)
    print("✅ Done.")
    print("=" * 60)



if __name__ == "__main__":
    sys.exit(main())