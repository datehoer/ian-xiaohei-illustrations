#!/usr/bin/env python3
"""Structural validation for the Ian Xiaohei Illustrations skill repo."""

from __future__ import annotations

import argparse
import os
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


SKILL_DIR = "ian-xiaohei-illustrations"
REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/style-dna.md",
    "references/xiaohei-ip.md",
    "references/composition-patterns.md",
    "references/prompt-template.md",
    "references/qa-checklist.md",
    "references/video-production.md",
    "references/dense-illustrated-video.md",
    "references/character-design.md",
    "references/annotations.md",
    "references/characters/corgi-minimal.md",
    "LICENSE",
    "EARTH-LICENSE",
    "NOTICE.md",
]
README_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
GENERATED_DIRS = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', 'outputs', 'work', 'episodes'}
DRAFT_MARKERS = (
    "TODO",
    "FIXME",
    "TBD",
    "PLACEHOLDER",
    "Lorem ipsum",
    "YOUR_",
)


class Validator:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def require_file(self, relative: str) -> Path:
        path = self.root / relative
        self.check(path.is_file(), f"missing file: {relative}")
        return path

    def require_dir(self, relative: str) -> Path:
        path = self.root / relative
        self.check(path.is_dir(), f"missing directory: {relative}")
        return path

    def validate(self) -> int:
        self.validate_root_files()
        self.validate_skill_files()
        self.validate_skill_frontmatter_and_routing()
        self.validate_readme_images()
        self.validate_example_images()
        self.validate_character_image()
        self.validate_local_links()
        self.validate_changelog()
        self.validate_no_draft_markers()

        if self.errors:
            print("quick_validate: failed")
            for error in self.errors:
                print(f"- {error}")
            return 1

        print("quick_validate: ok")
        return 0

    def validate_root_files(self) -> None:
        for relative in ("README.md", "LICENSE", "NOTICE.md", "CHANGELOG.md"):
            self.require_file(relative)
        self.require_dir(SKILL_DIR)
        self.require_file("scripts/quick_validate.py")
        # Second bundled skill: economics-of-owning script writer.
        self.require_file("economics-of-owning/SKILL.md")
        self.require_file("economics-of-owning/references/beat-sheet.md")
        self.require_file("economics-of-owning/references/numbers.md")

    def validate_skill_files(self) -> None:
        for relative in REQUIRED_SKILL_FILES:
            self.require_file(f"{SKILL_DIR}/{relative}")
        examples_dir = self.require_dir(f"{SKILL_DIR}/assets/examples")
        examples = sorted(examples_dir.glob("*.png"))
        self.check(len(examples) >= 8, "skill assets/examples should include calibration PNGs")

    def validate_skill_frontmatter_and_routing(self) -> None:
        skill_path = self.require_file(f"{SKILL_DIR}/SKILL.md")
        text = read_text(skill_path)
        self.check(text.startswith("---\n"), "SKILL.md must start with frontmatter")
        self.check("name: ian-xiaohei-illustrations" in text, "SKILL.md frontmatter missing expected name")
        self.check("description:" in text, "SKILL.md frontmatter missing description")
        self.check("## 任务路由" in text, "SKILL.md should include task routing")
        for reference in (item for item in REQUIRED_SKILL_FILES if item.startswith("references/")):
            self.check(reference in text, f"SKILL.md routing missing {reference}")

    def validate_readme_images(self) -> None:
        readme_path = self.require_file("README.md")
        readme = read_text(readme_path)
        image_refs = README_IMAGE_PATTERN.findall(readme)
        self.check(len(image_refs) >= 8, "README.md should reference the public example images")
        for ref in image_refs:
            if ref.startswith(("http://", "https://")):
                continue
            image_path = (readme_path.parent / ref).resolve()
            self.check(image_path.is_file(), f"README image target missing: {ref}")

    def validate_example_images(self) -> None:
        image_dirs = [
            self.root / SKILL_DIR / "assets/examples",
        ]
        for image_dir in image_dirs:
            self.check(image_dir.is_dir(), f"missing example image directory: {relative_to_root(self.root, image_dir)}")
            for path in sorted(image_dir.glob("*.png")):
                size = self.checked_png_size(path)
                if size is None:
                    continue
                width, height = size
                ratio = width / height
                self.check(
                    abs(ratio - (16 / 9)) < 0.015,
                    f"example image is not close to 16:9: {relative_to_root(self.root, path)} ({width}x{height})",
                )

    def validate_character_image(self) -> None:
        path = self.require_file(f"{SKILL_DIR}/assets/characters/corgi-minimal.png")
        if path.is_file():
            self.checked_png_size(path)

    def checked_png_size(self, path: Path) -> tuple[int, int] | None:
        try:
            return read_png_size(path)
        except (OSError, ValueError, struct.error) as error:
            self.errors.append(f"invalid PNG: {relative_to_root(self.root, path)} ({error})")
            return None

    def validate_local_links(self) -> None:
        skill_root = (self.root / SKILL_DIR).resolve()
        for path in sorted(source_files(self.root)):
            if path.suffix.lower() != '.md':
                continue
            for raw_target in MARKDOWN_LINK_PATTERN.findall(read_text(path)):
                # Inline links, including optional Markdown titles and angle brackets.
                raw_target = raw_target.strip()
                if not raw_target:
                    continue
                target = raw_target.split(">", 1)[0][1:] if raw_target.startswith("<") else raw_target.split()[0]
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                destination = (path.parent / unquote(parsed.path)).resolve()
                location = relative_to_root(self.root, path)
                self.check(destination.exists(), f"local link target missing in {location}: {target}")
                if path.resolve().is_relative_to(skill_root):
                    self.check(
                        destination.is_relative_to(skill_root),
                        f"installed skill link leaves its bundle in {location}: {target}",
                    )

    def validate_changelog(self) -> None:
        changelog = read_text(self.require_file("CHANGELOG.md"))
        self.check("# Changelog" in changelog, "CHANGELOG.md should have a top-level title")
        self.check("## Unreleased" in changelog, "CHANGELOG.md should include an Unreleased section")
        self.check("## v1.0.0" in changelog, "CHANGELOG.md should preserve the initial release entry")

    def validate_no_draft_markers(self) -> None:
        for path in source_files(self.root):
            if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py"}:
                continue
            if path.name == "quick_validate.py":
                continue
            text = read_text(path)
            for marker in DRAFT_MARKERS:
                self.check(marker not in text, f"draft marker {marker!r} found in {relative_to_root(self.root, path)}")


def source_files(root: Path):
    """Check authored files without scanning downloaded runtimes or generated output."""
    for directory, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in GENERATED_DIRS]
        for name in files:
            yield Path(directory) / name


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"not a PNG file: {path}")
        length = struct.unpack(">I", handle.read(4))[0]
        chunk_type = handle.read(4)
        if chunk_type != b"IHDR" or length < 8:
            raise ValueError(f"missing PNG IHDR: {path}")
        width, height = struct.unpack(">II", handle.read(8))
        if width == 0 or height == 0:
            raise ValueError("PNG dimensions must be positive")
        return width, height


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Ian Xiaohei Illustrations skill repository.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to validate.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    return Validator(root).validate()


if __name__ == "__main__":
    sys.exit(main())
