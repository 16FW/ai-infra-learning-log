# AI Infra Learning Log

[ai-infra-junior-engineer-learning](https://github.com/ai-infra-curriculum/ai-infra-junior-engineer-learning)
커리큘럼을 따라가며 남기는 학습 기록입니다. 모듈별 노트와 실습 코드를 모았습니다.

## 진도

| Module | 주제 | 상태 | 노트 |
|---|---|---|---|
| 001 | Python Fundamentals for Infrastructure | ✅ 완료 | [notes](modules/module-001-python-fundamentals/notes) |
| 002 | Linux Essentials | 🔄 진행 중 (6/8) | [notes](modules/module-002-linux-essentials/notes) |
| 003 | Git & Version Control | ⬜ | |
| 004 | ML Basics (PyTorch/TensorFlow) | ⬜ | |
| 005 | Docker & Containerization | ⬜ | |
| 006 | Kubernetes Introduction | ⬜ | |
| 007 | APIs & Web Services | ⬜ | |
| 008 | Databases & SQL | ⬜ | |
| 009 | Monitoring & Logging Basics | ⬜ | |
| 010 | Cloud Platforms (AWS/GCP/Azure) | ⬜ | |

## Module 002 — Linux Essentials

| Lesson | 주제 | 노트 |
|---|---|---|
| 01 | 파일시스템 계층과 링크 | [lesson-01](modules/module-002-linux-essentials/notes/lesson-01-filesystem-and-links.md) |
| 02 | 권한과 소유권 | [lesson-02](modules/module-002-linux-essentials/notes/lesson-02-permissions.md) |
| 03 | 프로세스와 시그널 | [lesson-03](modules/module-002-linux-essentials/notes/lesson-03-processes-and-signals.md) |
| 04 | systemd와 로그 | [lesson-04](modules/module-002-linux-essentials/notes/lesson-04-systemd-and-logs.md) |
| 05 | Bash 스크립팅 기초 | [lesson-05](modules/module-002-linux-essentials/notes/lesson-05-bash-basics.md) |
| 06 | Bash 스크립팅 심화 | [lesson-06](modules/module-002-linux-essentials/notes/lesson-06-bash-advanced.md) |
| 07 | grep / sed / awk, 로그 분석 | 예정 |
| 08 | 네트워킹과 종합 트러블슈팅 | 예정 |

## 구조

```
ai-infra-learning-log/
├── README.md
└── modules/
    └── module-00X-<주제>/
        ├── notes/        레슨별 노트
        └── exercises/    실습 코드
```

## 환경

- WSL2 (Ubuntu) / Python 3.12 / Docker Desktop
