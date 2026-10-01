#!/usr/bin/env python3
"""Generate resumable image notes and store them in data/ads.json.

Each ad is processed in a separate Codex CLI run. Successful results are
written atomically after every ad, so an interrupted batch can be resumed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NOTE_FIELD = "generated_note"
REQUIRED_RESPONSE_KEYS = {"note"}


class BatchError(RuntimeError):
    """A recoverable per-ad generation failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def load_ads(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, list):
        raise BatchError(f"{path} must contain a JSON array")

    ads: list[dict[str, Any]] = []
    seen_images: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise BatchError(f"ad {index + 1} is not a JSON object")
        for key in ("title", "image", "slug"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise BatchError(f"ad {index + 1} has no valid {key!r}")
        image = item["image"]
        if image in seen_images:
            raise BatchError(f"duplicate primary image in ads data: {image}")
        seen_images.add(image)
        ads.append(item)
    return ads


def load_batch_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "ads": {}}
    state = load_json(path)
    if (
        not isinstance(state, dict)
        or state.get("version") != 1
        or not isinstance(state.get("ads"), dict)
    ):
        raise BatchError(f"{path} is not a supported batch-state file")
    return state


def save_ad_state(
    path: Path, state: dict[str, Any], ad_id: str, update: dict[str, Any]
) -> None:
    records = state.setdefault("ads", {})
    current = records.get(ad_id, {})
    records[ad_id] = {**current, **update}
    atomic_write_json(path, state)


def validate_response(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["response is not a JSON object"]
    errors: list[str] = []
    missing = REQUIRED_RESPONSE_KEYS - value.keys()
    extra = value.keys() - REQUIRED_RESPONSE_KEYS
    if missing:
        errors.append(f"missing keys: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected keys: {', '.join(sorted(extra))}")
    note = value.get("note")
    if "note" in value and (not isinstance(note, str) or not note.strip()):
        errors.append("note must be a non-empty string")
    return errors


def resolve_image(repo: Path, relative_path: str) -> Path:
    static_dir = (repo / "static").resolve()
    image = (static_dir / relative_path).resolve()
    try:
        image.relative_to(static_dir)
    except ValueError as error:
        raise BatchError(f"image path escapes the static directory: {relative_path}") from error
    if not image.is_file():
        raise BatchError(f"image does not exist: {image}")
    return image


def ad_id(ad: dict[str, Any]) -> str:
    return Path(ad["image"]).stem


def image_attachments(
    repo: Path, ad: dict[str, Any], include_details: bool
) -> list[tuple[str, Path]]:
    attachments = [("primary_image", resolve_image(repo, ad["image"]))]
    if include_details:
        details = ad.get("details", [])
        if not isinstance(details, list):
            raise BatchError(f"details for {ad_id(ad)} must be an array")
        for index, relative_path in enumerate(details, start=1):
            if not isinstance(relative_path, str):
                raise BatchError(f"detail image {index} for {ad_id(ad)} is not a string")
            attachments.append(
                (f"detail_image_{index}", resolve_image(repo, relative_path))
            )
    return attachments


def build_prompt(
    template: str, ad: dict[str, Any], attachments: list[tuple[str, Path]]
) -> str:
    metadata = {
        "id": ad_id(ad),
        "title": ad["title"],
        "slug": ad["slug"],
        "existing_description": ad.get("description", ""),
        "tags": ad.get("tags", []),
        "primary_image": ad["image"],
    }
    attachment_lines = [
        f"{index}. {role}: {path.name}"
        for index, (role, path) in enumerate(attachments, start=1)
    ]
    return (
        template.rstrip()
        + "\n\n"
        + "AD METADATA:\n"
        + json.dumps(metadata, ensure_ascii=False, indent=2)
        + "\n\nATTACHED IMAGES IN ORDER:\n"
        + "\n".join(attachment_lines)
        + "\n\nReturn the requested note for the primary image. "
        + "Your response must match the supplied JSON schema.\n"
    )


def run_codex(
    args: argparse.Namespace,
    ad: dict[str, Any],
    attachments: list[tuple[str, Path]],
    prompt: str,
) -> dict[str, Any]:
    output_descriptor, output_name = tempfile.mkstemp(
        prefix=f"{ad_id(ad)}-", suffix=".json"
    )
    os.close(output_descriptor)
    output_path = Path(output_name)

    command = [
        args.codex,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--output-schema",
        str(args.schema),
        "--output-last-message",
        str(output_path),
        "--cd",
        str(args.repo),
    ]
    if args.model:
        command.extend(["--model", args.model])
    for _, image in attachments:
        command.extend(["--image", str(image)])
    command.append("-")

    try:
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
        )
        if completed.returncode != 0:
            diagnostic = (completed.stderr or completed.stdout).strip()
            raise BatchError(
                f"codex exec exited {completed.returncode}: {diagnostic[-4000:]}"
            )
        try:
            response = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BatchError(f"could not read structured Codex output: {error}") from error
        errors = validate_response(response)
        if errors:
            raise BatchError("invalid structured output: " + "; ".join(errors))
        return response
    except subprocess.TimeoutExpired as error:
        raise BatchError(f"codex exec timed out after {args.timeout} seconds") from error
    finally:
        output_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    repo_default = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ads", type=Path, default=repo_default / "data" / "ads.json",
        help="ad data file (default: data/ads.json)",
    )
    parser.add_argument("--repo", type=Path, default=repo_default)
    parser.add_argument(
        "--prompt", type=Path, default=repo_default / "docs" / "ad-note-prompt.md",
        help="prompt template; required except for --dry-run",
    )
    parser.add_argument(
        "--schema", type=Path, default=repo_default / "bin" / "ad-note.schema.json"
    )
    parser.add_argument(
        "--state", type=Path, default=repo_default / "data" / ".ad-note-batch-state.json"
    )
    parser.add_argument("--codex", default="codex", help="Codex executable")
    parser.add_argument("--model", help="optional Codex model override")
    parser.add_argument("--timeout", type=int, default=900, help="seconds per ad")
    parser.add_argument("--limit", type=int, help="maximum ads to consider")
    parser.add_argument(
        "--start-at", help="first image ID or image path to consider, e.g. SCN_0042"
    )
    parser.add_argument("--only", help="process one image ID, slug, or image path")
    parser.add_argument("--force", action="store_true", help="regenerate existing notes")
    parser.add_argument("--dry-run", action="store_true", help="print work without Codex")
    parser.add_argument(
        "--include-details", action="store_true",
        help="attach an ad's detail scans as context after its primary image",
    )
    parser.add_argument(
        "--retry-failures", action="store_true",
        help="consider only ads marked failed in the state file",
    )
    return parser.parse_args()


def matches_selector(ad: dict[str, Any], selector: str) -> bool:
    return selector in {ad_id(ad), ad["slug"], ad["image"]}


def main() -> int:
    args = parse_args()
    args.repo = args.repo.resolve()
    args.ads = args.ads.resolve()
    args.prompt = args.prompt.resolve()
    args.schema = args.schema.resolve()
    args.state = args.state.resolve()
    failure_log = args.state.with_name(".ad-note-failures.jsonl")

    required = [args.ads, args.schema]
    if not args.dry_run:
        required.append(args.prompt)
    for path in required:
        if not path.is_file():
            print(f"error: required file does not exist: {path}", file=sys.stderr)
            return 2

    try:
        ads = load_ads(args.ads)
        state = load_batch_state(args.state)
    except (BatchError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.only:
        ads = [ad for ad in ads if matches_selector(ad, args.only)]
    if args.start_at:
        start_index = next(
            (index for index, ad in enumerate(ads) if matches_selector(ad, args.start_at)),
            None,
        )
        if start_index is None:
            print(f"error: --start-at did not match an ad: {args.start_at}", file=sys.stderr)
            return 2
        ads = ads[start_index:]
    if args.retry_failures:
        retry_ids = {
            key for key, value in state["ads"].items()
            if isinstance(value, dict) and value.get("status") == "failed"
        }
        ads = [ad for ad in ads if ad_id(ad) in retry_ids]
    if args.limit is not None:
        if args.limit < 0:
            print("error: --limit must be non-negative", file=sys.stderr)
            return 2
        ads = ads[: args.limit]

    if not ads:
        print("No matching ads found.")
        return 0

    prompt_template = "" if args.dry_run else args.prompt.read_text(encoding="utf-8")
    failures = 0
    saved = 0

    for ad in ads:
        identifier = ad_id(ad)
        existing = ad.get(NOTE_FIELD)
        if not args.force and isinstance(existing, str) and existing.strip():
            print(f"SKIP {identifier}: valid note exists")
            continue

        try:
            attachments = image_attachments(args.repo, ad, args.include_details)
        except BatchError as error:
            print(f"FAIL {identifier}: {error}", file=sys.stderr)
            failures += 1
            continue

        attachment_summary = ", ".join(
            f"{role}={path.name}" for role, path in attachments
        )
        print(f"RUN  {identifier}: {ad['title']} ({attachment_summary})")
        if args.dry_run:
            continue

        previous_state = state["ads"].get(identifier, {})
        attempts = int(previous_state.get("attempts", 0)) + 1
        try:
            prompt = build_prompt(prompt_template, ad, attachments)
            response = run_codex(args, ad, attachments, prompt)
            ad[NOTE_FIELD] = response["note"].strip()
            atomic_write_json(args.ads, merge_updated_ad(args.ads, ad))
            save_ad_state(
                args.state,
                state,
                identifier,
                {
                    "status": "complete",
                    "updated_at": utc_now(),
                    "prompt_version": "1",
                    "model": args.model or "codex-config-default",
                    "attempts": attempts,
                    "source_image": ad["image"],
                    "context_images": [str(path) for _, path in attachments],
                    "error": None,
                },
            )
            saved += 1
            print(f"SAVE {identifier}: {args.ads}#{NOTE_FIELD}")
        except (BatchError, OSError, json.JSONDecodeError) as error:
            append_jsonl(
                failure_log,
                {
                    "at": utc_now(), "ad_id": identifier, "stage": "generate",
                    "attempt": attempts, "source_image": ad["image"], "error": str(error),
                },
            )
            save_ad_state(
                args.state,
                state,
                identifier,
                {
                    "status": "failed", "updated_at": utc_now(),
                    "attempts": attempts,
                    "model": args.model or "codex-config-default",
                    "source_image": ad["image"], "error": str(error),
                },
            )
            print(f"FAIL {identifier}: {error}", file=sys.stderr)
            failures += 1

    print(f"Done: {saved} saved, {failures} failed.")
    return 1 if failures else 0


def merge_updated_ad(
    ads_path: Path, updated_ad: dict[str, Any]
) -> list[dict[str, Any]]:
    """Merge one selected record into the complete on-disk array by image path."""
    complete = load_ads(ads_path)
    for index, candidate in enumerate(complete):
        if candidate["image"] == updated_ad["image"]:
            complete[index] = updated_ad
            return complete
    raise BatchError(f"ad disappeared from {ads_path}: {updated_ad['image']}")


if __name__ == "__main__":
    raise SystemExit(main())
