import platform
import os
import shutil
import json
import sys

class InfraCheckError(Exception):
    pass
class DiskCheckError(InfraCheckError):
    pass

def get_os_info() -> dict:
    return {"os" : platform.system(), "kernel_release" : platform.release()}

def get_cpu_count() -> dict:
    return {"cpu_count" : os.cpu_count()}

def get_disk_usage(path: str) -> dict :
    try:
        total,used,free = shutil.disk_usage(path)
        return{
                "path" : path,
                "total_gb": round(total / (1000**3), 2),
                "used_gb": round(used / (1000**3), 2),
                "free_gb": round(free / (1000**3), 2),
                "error" : None,     
        }
    except PermissionError as e:
            raise DiskCheckError(f"Permission denied for path : '{path}'") from e
    except FileNotFoundError as e:
        raise DiskCheckError(f"Path not found : '{path}'") from e
    except OSError as e:
        raise DiskCheckError(f"OS error checking path '{path}': {e}") from e

def main() :
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else :
        target_path = "/"
    
    result = {}
    result.update(get_os_info())
    result.update(get_cpu_count())

    has_error = False
    
    try:
        result["disk"] = get_disk_usage(target_path)

    except DiskCheckError as e:
        has_error = True
        result["disk"] = {
            "path": target_path,
            "total_gb": None,
            "used_gb": None,
            "free_gb": None,
            "error": str(e),
        }

    except Exception as e:
        has_error = True
        result["disk"] = {
            "path": target_path,
            "total_gb": None,
            "used_gb": None,
            "free_gb": None,
            "error": f"Unexpected error: {e}",
        }

    print(json.dumps(result, indent=2))

    if has_error:
        sys.exit(1)

if __name__ == "__main__":
    main()