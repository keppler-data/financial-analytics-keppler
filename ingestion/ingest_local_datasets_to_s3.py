"""Upload local credit-risk datasets to S3 or to a local S3-like mirror.

The local mirror mode is useful for validating file discovery, destination
keys, and manifests before running the same ingestion against AWS.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


DATASETS = {
    "data_archive": Path("data/archive"),
    "data_give_some_credit": Path("data/GiveMeSomeCredit"),
}


@dataclass(frozen=True)
class IngestionObject:
    dataset: str
    source_path: str
    destination: str
    size_bytes: int
    content_type: str


def iter_dataset_files(project_root: Path, datasets: dict[str, Path]) -> Iterable[tuple[str, Path]]:
    for dataset_name, relative_dir in datasets.items():
        source_dir = project_root / relative_dir
        if not source_dir.exists():
            raise FileNotFoundError(f"Dataset directory does not exist: {source_dir}")

        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                yield dataset_name, path


def build_destination_key(
    project_root: Path,
    dataset_name: str,
    source_path: Path,
    prefix: str,
    ingestion_date: str,
) -> str:
    relative_source = source_path.relative_to(project_root / DATASETS[dataset_name])
    clean_prefix = prefix.strip("/")
    return (
        f"{clean_prefix}/raw/{dataset_name}/ingestion_date={ingestion_date}/"
        f"{relative_source.as_posix()}"
    )


def guess_content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(path.name)
    return content_type or "application/octet-stream"


def collect_objects(project_root: Path, bucket: str, prefix: str, ingestion_date: str) -> list[IngestionObject]:
    objects: list[IngestionObject] = []
    for dataset_name, source_path in iter_dataset_files(project_root, DATASETS):
        key = build_destination_key(project_root, dataset_name, source_path, prefix, ingestion_date)
        objects.append(
            IngestionObject(
                dataset=dataset_name,
                source_path=str(source_path),
                destination=f"s3://{bucket}/{key}",
                size_bytes=source_path.stat().st_size,
                content_type=guess_content_type(source_path),
            )
        )
    return objects


def write_manifest(objects: list[IngestionObject], manifest_path: Path, mode: str) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "generated_at": datetime.now(UTC).isoformat(),
        "object_count": len(objects),
        "total_size_bytes": sum(obj.size_bytes for obj in objects),
        "objects": [asdict(obj) for obj in objects],
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def upload_to_local_mirror(objects: list[IngestionObject], bucket: str, mirror_root: Path) -> None:
    for obj in objects:
        relative_destination = obj.destination.removeprefix(f"s3://{bucket}/")
        target_path = mirror_root / bucket / relative_destination
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(obj.source_path, target_path)


def upload_to_s3(objects: list[IngestionObject], bucket: str) -> None:
    import boto3

    s3 = boto3.client("s3")
    for obj in objects:
        key = obj.destination.removeprefix(f"s3://{bucket}/")
        s3.upload_file(
            obj.source_path,
            bucket,
            key,
            ExtraArgs={
                "ContentType": obj.content_type,
                "Metadata": {
                    "dataset": obj.dataset,
                    "source_file": Path(obj.source_path).name,
                    "ingested_at": datetime.now(UTC).isoformat(),
                },
            },
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest data/archive and data/GiveMeSomeCredit into S3."
    )
    parser.add_argument("--bucket", required=True, help="Destination S3 bucket name.")
    parser.add_argument(
        "--prefix",
        default="financial-analytics/bronze",
        help="S3 prefix where raw files will be written.",
    )
    parser.add_argument(
        "--mode",
        choices=("dry-run", "local", "s3"),
        default="dry-run",
        help="dry-run only writes a manifest, local copies files to a mirror, s3 uploads to AWS.",
    )
    parser.add_argument(
        "--mirror-root",
        default="data/local_s3_mirror",
        help="Local directory used when --mode local is selected.",
    )
    parser.add_argument(
        "--manifest-path",
        default="data/local_s3_mirror/ingestion_manifest.json",
        help="Path where the ingestion manifest will be written.",
    )
    parser.add_argument(
        "--ingestion-date",
        default=datetime.now(UTC).date().isoformat(),
        help="Partition date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    objects = collect_objects(project_root, args.bucket, args.prefix, args.ingestion_date)

    if args.mode == "local":
        upload_to_local_mirror(objects, args.bucket, project_root / args.mirror_root)
    elif args.mode == "s3":
        upload_to_s3(objects, args.bucket)

    write_manifest(objects, project_root / args.manifest_path, args.mode)

    total_size_mb = sum(obj.size_bytes for obj in objects) / 1024 / 1024
    print(f"Mode: {args.mode}")
    print(f"Objects discovered: {len(objects)}")
    print(f"Total size: {total_size_mb:.2f} MB")
    print(f"Manifest: {project_root / args.manifest_path}")
    if objects:
        print("First destinations:")
        for obj in objects[:5]:
            print(f"  - {obj.destination}")


if __name__ == "__main__":
    main()
