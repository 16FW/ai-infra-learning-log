# Lesson 02 — 커스텀 예외와 경계에서의 에러 처리

## 핵심 개념
- Python 예외는 상속 계층구조다. `FileNotFoundError`와 `PermissionError`는 `OSError`의 자식이고, `OSError`는 `Exception`의 자식이다.
- except 절은 위에서부터 검사하고 처음 매치되는 곳에서 멈춘다. 그래서 구체적인 예외를 먼저, 넓은 예외를 나중에 둔다.
- 커스텀 예외는 "이 에러가 정확히 어떤 상황에서 났는지"를 타입으로 표현한다.
- Fail Fast, Handle at the Boundary: 함수 내부는 문제가 생기면 예외를 던지기만 하고, 처리는 진입점(main) 한 곳에서 한다.

## 동작 원리
- `except Exception`을 맨 위에 두면 모든 자손 예외를 먼저 가로채서, 아래 except들은 절대 실행되지 않는 dead code가 된다.
- `raise DiskCheckError(...) from e`는 원본 예외를 `__cause__`로 연결해서, 새 예외로 감싸도 원래 원인이 traceback에 남는다.
- 예외를 넓게 잡으면(`except Exception`) 코드 버그(TypeError 등)까지 "경로 없음"으로 둔갑한다. `OSError`로 좁혀야 진짜 파일/경로 문제만 변환된다.

## 실습에서 한 것
- `InfraCheckError`를 base로, `DiskCheckError`를 자식으로 하는 예외 계층을 만들었다.
- `get_disk_usage()`는 `OSError`만 잡아서 `DiskCheckError`로 다시 던지도록 바꿨다.
- main에서 try/except는 "데이터 채우기"만 담당하고, `print`와 `sys.exit`는 블록 밖에서 한 번만 호출하게 구조를 나눴다.
- except 순서를 일부러 뒤집어서 `Exception`이 모든 예외를 가로채는 것을 확인했다.
- `except InfraCheckError`가 지금 구조에서는 도달할 수 없는 코드라는 걸 확인하고, 다른 개발자가 오해할 수 있어서 지웠다.
- 리팩터링하다가 Lesson 1에서 고친 스키마 일관성을 다시 깨뜨렸다가 복구했다.

## Infrastructure 연결
- 에러 처리를 한 곳으로 모으는 패턴은 FastAPI의 `exception_handler`와 같은 개념이다. (→ Module 007, Project 01)
- 명확한 예외 타입은 로그와 알림에서 장애 원인을 빠르게 구분하게 해준다. (→ Module 009)

## 면접 포인트
- except 순서가 틀리면 무엇이 문제인가: 효율이 아니라 도달 가능성(reachability) 문제다.
- 예외를 왜 좁게 잡아야 하는가: 예상하지 못한 버그를 숨기지 않기 위해서다.

## 내 말로 3줄 요약
1. 예외는 상속 구조이므로 구체적인 예외를 위에 배치하고, 예상치 못한 버그를 숨기지 않도록 필요한 범위만 좁게 잡는다.
2. 내부 함수는 문제 발생 시 원인 예외를 엮어(`from e`) 커스텀 예외로 던지기만 하고, 처리는 진입점 한 곳에서 담당한다.
3. 한 번 고친 설계 원칙(출력 스키마 일관성)이 리팩터링 후에도 유지되는지 반드시 확인해야 한다.
