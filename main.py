#!/usr/bin/env python3
"""
AI Job Hunter

Application entry point.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from jobs.cli import _create_connector, _create_exporter, _get_extension, _print_summary
from jobs.engine import Engine
from jobs.profiles import build_search_plan, load_profile
from jobs.search import SearchRequest


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="AI Job Hunter - Search and export job listings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Keyword mode (existing)
  python main.py --keyword "software engineer" --location bangalore

  # Profile mode (new)
  python main.py --profile crm_manager --location bangalore --location gurgaon
        """,
    )

    # Search mode group (mutually exclusive)
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument(
        "-k", "--keyword",
        help="Search keyword (e.g., 'software engineer')",
    )
    search_group.add_argument(
        "-p", "--profile",
        help="Profile name (e.g., 'crm_manager')",
    )

    parser.add_argument(
        "-l", "--location",
        action="append",
        dest="locations",
        required=False,
        help=(
            "Location (can be specified multiple times). "
            "Optional in profile mode; profile-configured locations "
            "are used when omitted."
        ),
    )

    parser.add_argument(
        "-c", "--connector",
        default="naukri",
        choices=[
            "naukri",
            "iimjobs",
            "foundit",
            "linkedin",
            "indeed",
            "greenhouse",
            "all",
        ],
        help=(
            "Job portal connector to use. "
            "'all' runs all enabled connectors sequentially "
            "(profile mode only). Default: naukri"
        ),
    )

    parser.add_argument(
        "-e", "--exporter",
        default="duckdb",
        choices=["duckdb"],
        help="Master storage format (DuckDB only)",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output"),
        help="Master database directory (default: output/)",
    )

    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help=(
            "Maximum jobs to fetch per keyword. "
            "Default: unlimited."
        ),
    )

    args = parser.parse_args()

    # ------------------------------------------------------------
    # Resolve locations
    # ------------------------------------------------------------
    # Profile mode may use locations defined by the profile.
    # Keyword mode still requires --location.
    if args.profile and not args.locations:
        profile_for_locations = load_profile(args.profile)

        profile_locations = getattr(
            profile_for_locations,
            "locations",
            None,
        )

        if not profile_locations:
            raise ValueError(
                f"No locations configured for profile '{args.profile}'. "
                "Provide --location."
            )

        args.locations = profile_locations

    if not args.locations:
        parser.error(
            "--location is required when using --keyword"
        )

    with sync_playwright() as playwright:
        browser = None
        try:
            # Build output path
            output_dir: Path = args.output
            # Create browser and context
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()

            # Instantiate connector(s) and exporter.
            # "all" is the controlled multi-connector profile path.
            if args.connector == "all":
                if not args.profile:
                    parser.error(
                        "--connector all is supported only with --profile"
                    )

                connector_names = [
                    "naukri",
                    "iimjobs",
                    "foundit",
                    "linkedin",
                    "greenhouse",
                ]
            else:
                connector_names = [args.connector]

            exporter = _create_exporter(args.exporter)

            # ========================================================
            # DATABASE DESTINATION
            # ========================================================
            # Uses --output while preserving the default:
            # output/job_hunter.duckdb
            #
            # Examples:
            #   --output output
            #   --output /tmp/test_output
            output_dir = args.output.resolve()
            output_dir.mkdir(parents=True, exist_ok=True)

            destination: Path = (
                output_dir / "job_hunter.duckdb"
            )
            db_path: Path = destination

            if args.keyword:
                # Keyword mode - single request
                request = SearchRequest(
                    keyword=args.keyword,
                    location=args.locations[0],
                    max_jobs=args.max_jobs,
                )
                requests = [request]
            else:
                # Profile mode - build search plan
                profile = load_profile(args.profile)
                requests = build_search_plan(profile, args.locations)

                # SearchRequest is frozen, so never mutate max_jobs in-place.
                # Rebuild each request while preserving all existing fields.
                if args.max_jobs is not None:
                    requests = [
                        SearchRequest(
                            keyword=request.keyword,
                            location=request.location,
                            page=request.page,
                            per_page=request.per_page,
                            experience=request.experience,
                            salary_min=request.salary_min,
                            salary_max=request.salary_max,
                            work_mode=request.work_mode,
                            employment_type=request.employment_type,
                            company=request.company,
                            easy_apply_only=request.easy_apply_only,
                            posted_within_days=request.posted_within_days,
                            skills=list(request.skills),
                            page_size=request.page_size,
                            max_jobs=args.max_jobs,
                        )
                        for request in requests
                    ]

            if args.connector.lower() == "all":
                for connector_name in connector_names:
                    print(
                        f"\n{'=' * 60}\n"
                        f"▶ Running connector: {connector_name}\n"
                        f"{'=' * 60}"
                    )

                    connector = _create_connector(
                        connector_name,
                        context,
                    )
                    engine = Engine(
                        connectors=[connector],
                        exporter=exporter,
                        db_path=db_path,
                    )

                    try:
                        summary = engine.run(
                            requests,
                            destination,
                            profile_type=args.profile if not args.keyword else None,
                        )
                        _print_summary(summary, args.exporter)

                        if summary.errors:
                            print(
                                f"❌ {connector_name}: "
                                f"{len(summary.errors)} error(s).",
                                file=sys.stderr,
                            )
                            return 1
                    finally:
                        engine.close()

                return 0

            connector = _create_connector(
                connector_names[0],
                context,
            )
            engine = Engine(
                connectors=[connector],
                exporter=exporter,
                db_path=db_path,
            )

            try:
                summary = engine.run(
                    requests,
                    destination,
                    profile_type=args.profile if not args.keyword else None,
                )
                _print_summary(summary, args.exporter)

                if summary.errors:
                    print(
                        f"❌ Fetch completed with "
                        f"{len(summary.errors)} error(s).",
                        file=sys.stderr,
                    )
                    return 1

                return 0
            finally:
                engine.close()

        except Exception as exc:
            print(f"❌ Error: {exc}", file=sys.stderr)
            return 1

        finally:
            if browser:
                browser.close()


if __name__ == "__main__":
    sys.exit(main())


# =============================================================================
# END OF FILE
# =============================================================================