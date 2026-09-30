import tempfile
import pytest
from Lesson01 import (
    DiskCheckError,
    get_cpu_count,
    get_disk_usage,
    get_os_info,
)

def test_get_os_info_keys():
    info = get_os_info()
    assert "os" in info
    assert "kernel_release" in info

def test_get_cpu_count_positive():
    cpu_info = get_cpu_count()
    cpu_count = cpu_info.get("cpu_count")

    assert isinstance(cpu_count, int)
    assert cpu_count>=1

def test_get_disk_usage_success():
    with tempfile.TemporaryDirectory() as temp_dir:
        disk_info = get_disk_usage(temp_dir)
        assert disk_info["error"] is None
        assert disk_info["total_gb"] > 0
        assert disk_info["path"] == temp_dir

def test_get_disk_usage_invalid_path_raises():
    with pytest.raises(DiskCheckError):
        get_disk_usage("no/such/path")