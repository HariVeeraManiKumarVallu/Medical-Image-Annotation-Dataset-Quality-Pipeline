from pathlib import Path

from src.common.hashing import (
    sha256_file,
)


def test_sha256_same_content(
    tmp_path: Path,
):

    a = (
        tmp_path
        / "a.bin"
    )

    b = (
        tmp_path
        / "b.bin"
    )

    a.write_bytes(
        b"same content"
    )

    b.write_bytes(
        b"same content"
    )

    assert (
        sha256_file(a)
        ==
        sha256_file(b)
    )


def test_sha256_different_content(
    tmp_path: Path,
):

    a = (
        tmp_path
        / "a.bin"
    )

    b = (
        tmp_path
        / "b.bin"
    )

    a.write_bytes(
        b"a"
    )

    b.write_bytes(
        b"b"
    )

    assert (
        sha256_file(a)
        !=
        sha256_file(b)
    )