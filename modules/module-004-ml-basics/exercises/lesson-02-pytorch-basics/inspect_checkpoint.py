from pathlib import Path
import zipfile


path = Path("tiny.pt")

with zipfile.ZipFile(path) as archive:
    entries = archive.infolist()

    print("[내부 항목별 크기]")
    print("원본(bytes) | 저장(bytes) | 이름")

    for entry in entries:
        print(
            f"{entry.file_size:>11} | "
            f"{entry.compress_size:>11} | "
            f"{entry.filename}"
        )

    # data/ 바로 아래 항목을 텐서 저장소로 분류합니다.
    storage_entries = [
        entry
        for entry in entries
        if not entry.is_dir()
        and Path(entry.filename).parent.name == "data"
    ]

    tensor_bytes = sum(
        entry.compress_size for entry in storage_entries
    )

    all_entry_bytes = sum(
        entry.compress_size for entry in entries
    )

    metadata_bytes = all_entry_bytes - tensor_bytes
    file_bytes = path.stat().st_size
    zip_overhead = file_bytes - all_entry_bytes

    print("\n[전체 크기 구성]")
    print("텐서 숫자 저장소:", tensor_bytes, "bytes")
    print("그 외 항목 내용:", metadata_bytes, "bytes")
    print("ZIP 헤더·색인·패딩 등:", zip_overhead, "bytes")
    print("전체 파일:", file_bytes, "bytes")

    print("\n[검산]")
    print(
        tensor_bytes,
        "+",
        metadata_bytes,
        "+",
        zip_overhead,
        "=",
        file_bytes,
    )

    print(
        "숫자 데이터 외 크기:",
        file_bytes - tensor_bytes,
        "bytes",
    )
