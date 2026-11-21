# CLAUDE.md - ascii_reels

글자(아스키)로 무언가가 점점 완성되는 15초 이내 세로 릴스를 만드는 저장소.
구조와 주제 스크립트 규약은 `README.md`, 새 영상을 만드는 절차는 `.claude/skills/new-reel/SKILL.md`.

## 지침

- 대답과 문서는 한국어. 단 `themes/*.py`는 영상에 그대로 나오므로 주석과 문자열을 영어/ASCII로 쓴다.
- 영상은 15초 이하로 구성한다(`engine.MAX_DURATION`). 넘으면 엔진이 거부한다.
- 화면의 계정 표기는 `@justmade.lab`(`HANDLE` 상수). 다른 이름을 쓰지 않는다.
- 새 주제는 반드시 스토리보드부터. 사람 승인 없이 코드로 넘어가지 않는다.
- 주제 스크립트를 고치면 `python check.py themes/<slug>.py`를 돌리고 `out/<slug>_check.png`를 직접 본다.
- 엔진(`engine.py`)을 고치면 모든 주제에 대해 `check.py`를 다시 돌린다.
- 분위기, 클라이맥스 강도 같은 감성 판단은 사람이 한다. 확인하지 않은 것을 확인했다고 말하지 않는다.
