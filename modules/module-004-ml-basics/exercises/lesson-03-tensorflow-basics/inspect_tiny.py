
import os
import zipfile


def format_size(size):
    return f"{size:,} bytes ({size / 1024:.2f} KiB)"


def inspect_keras(path):
    print("\n===== tiny.keras =====")

    with zipfile.ZipFile(path, "r") as zf:
        total = 0

        print(f"{'File':<40} {'Size':>15}")
        print("-" * 58)

        for info in zf.infolist():
            print(
                f"{info.filename:<40} "
                f"{info.file_size:>15,}"
            )
            total += info.file_size

        print("-" * 58)
        print(f"Total uncompressed: {format_size(total)}")
        print(f"Archive size: {format_size(os.path.getsize(path))}")


def inspect_savedmodel(path):
    print("\n===== tiny_savedmodel =====")

    total = 0

    print(f"{'File':<55} {'Size':>15}")
    print("-" * 73)

    for root, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            size = os.path.getsize(filepath)

            relative = os.path.relpath(filepath, path)

            print(f"{relative:<55} {size:>15,}")
            total += size

    print("-" * 73)
    print(f"Total: {format_size(total)}")


if __name__ == "__main__":
    inspect_keras("tiny.keras")
    inspect_savedmodel("tiny_savedmodel")
