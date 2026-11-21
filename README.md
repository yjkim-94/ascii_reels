# ascii_reels

글자(아스키)로 무언가가 점점 완성되는 세로 릴스 영상(1080x1920, 30fps, H.264, 무음)을 만드는 엔진.
위쪽은 렌더 결과, 아래쪽은 그 주제 스크립트 코드가 스크롤된다. 배경음악은 인스타 업로드 때 고른다.

## 실행

```bash
pip install numpy pillow pygments     # pygments는 코드 색칠용(없으면 단색)
python render.py themes/christmas_tree.py                 # out/christmas_tree.mp4 (15초, 약 45초 걸림)
python render.py themes/christmas_tree.py --still 3 9 15  # 해당 초 PNG만 (검수용, 1~2초)
python render.py themes/christmas_tree.py --seconds 5     # 앞부분만
```

ffmpeg(libx264)와 DejaVu 글꼴(`/usr/share/fonts/truetype/dejavu/`)이 필요하다.

## 구조

- `engine.py`: 글자 아틀라스, `Grid`(108x61 칸), 3D 점 구름(`splat`), 배경(`LetterRain`, `Snow`), 빛 번짐,
  큰 글씨 자막, HUD, 코드 패널, mp4 인코딩. 주제와 무관한 것은 모두 여기.
- `themes/*.py`: 주제 하나 = 파일 하나. 이 파일이 그대로 영상 하단에 나온다.
  `christmas_tree.py`(2D 마스크, 15초), `jellyfish_sample.py`(3D 점 구름, 3초 시안),
  `crystal_sample.py`(조명·반짝임·바닥 반사, 3초 시안), `footage_sample.py`(실사 영상 글자화, 3초 시안).
- `storyboards/*.md`: 주제별 스토리보드. `_template.md`를 복사해 쓴다. `GUIDE.md`는 기획 기준, 인터뷰 4문항, 연출 패턴 목록.
- `sources/`: 실사 변환용 원본 영상(`test_fractal.mp4`는 ffmpeg로 만든 시험용).
- `render.py`: 영상/정지 화면. `check.py`: 자동 점검 + 점검 시트. `publish.py`: 갤러리 등록.
- `gallery/`: 웹사이트가 읽을 영상, 썸네일, `manifest.json`.

## 워크플로

1. 스토리보드 작성 -> **사람 승인**
2. 주제 스크립트 작성
3. `python check.py themes/<slug>.py` -> FAIL 수정, `out/<slug>_check.png`로 자체 검토
4. 점검 시트 + 미리보기 영상 -> **사람 검수**
5. `python publish.py themes/<slug>.py` -> 갤러리 등록, 커밋

Claude Code에서는 `/new-reel <주제>`가 이 순서를 따른다(`.claude/skills/new-reel/SKILL.md`).

`check.py`가 자동으로 보는 것: 길이 15초 이하, 필수 상수, 장면 구간, 렌더 중 예외, 같은 t면 같은 그림,
첫 1초 움직임, 장면 중간 정지, 첫/끝 프레임 이음새, 코드에 한글, 72자 넘는 줄, 예상 렌더 시간.

## 주제 스크립트 규약 (LLM 자동 생성 시 이것만 지키게 한다)

1. 모듈 상수: `TITLE`, `DURATION`(초, **최대 15**, 넘으면 엔진이 거부), `SCENES`(장면 이름과 구간, 점검에 씀),
   `POSTER_T`(썸네일 시각), 선택 `GLOW`(빛 번짐 세기, 0.9 안팎).
2. `draw(g, t)`를 구현한다. **t만으로 결정**되어야 한다(전역 상태 변경 금지, 난수는 모듈 로드 때 고정 시드로 미리 뽑기).
3. 반환: `{"hud": [줄, ...], "caption": (전체문구, 보일글자수, y, rgb, 크기, 자간, 커서여부)}` 또는 HUD 줄 목록만.
4. 그리기 API
   - 좌표: `g.X`(-1..1, 가운데 0), `g.Y`(0 위 .. 1 아래), `g.r`, `g.c`(칸 번호). 위쪽 화면은 거의 정사각형.
   - `g.put(mask, chars, color, alpha)`: 마스크 칸 칠하기. `chars`는 글자 번호(`CIDX["*"]`, `idx("ABC")`).
   - `g.put_cells(rows, cols, chars, colors)`: 점 찍기. `g.to_cell(x, y)`로 좌표 변환.
   - `g.text(row, col, "문자열", color)`.
   - 색은 RGB 0~1. 1을 넘기면 더 밝게 번진다(전구, 별 등 강조).
   - 칸에는 **더 밝은 글자만** 덮어쓴다. 사라지는 물체가 배경을 검게 가리지 않게 하기 위한 규칙이다.
   - 3D: 점 (N,3)을 `rot_y`/`rot_x`로 돌리고 `splat(g, P, rgb, lum, chars)`로 찍는다.
     원근 투영, 칸마다 가장 앞 점만 남기기(z-buffer), 밝기 -> 잉크 면적 순 글자(`RAMP`)를 엔진이 한다.
     선(촉수, 빛줄기)은 `dir_chars(dx, dy)`로 `| / \ -` 글자를 쓴다.
   - 조명: `light(n, t)` - 화면 기준 법선으로 주광, 회전 테두리광, 반사광, 반짝임(glint)을 계산해 (밝기, 반짝임 여부)를 준다.
   - 실사 영상: `clip = Footage("sources/x.mp4", start=, length=)`를 모듈에서 한 번 읽고, `draw_footage(g, clip.at(t), mask=...)`로 그린다.
     어두운 칸은 비우고 원본 색을 유지한다. 소스 규칙은 `storyboards/GUIDE.md` 4번.
   - 바닥 반사: `splat_reflection(g, P, rgb, lum, floor_y)`를 본체 `splat` 전에 부른다.
   - 코드 패널의 타이핑 커서와 오른쪽 위 경과 시간(`● t 1.23s`)은 엔진이 자동으로 그린다. 끄려면 `SHOW_CLOCK = False`.
5. 시간 도우미: `ramp(t, a, b)`, `ease`(빠르게 시작), `smooth`(고르게), `pop`(튀어나옴).
6. 플롯: `T_*` 구간 상수로 "바탕 → 형체가 자람 → 장식이 하나씩 → 마지막 한 방(별/꽃/문구) → 페이드아웃"을
   0~15초에 배치. 끝은 처음 화면(배경만)과 같게 해서 반복 재생이 이어지게 한다.
7. 화면에 나오는 파일이므로 **주석은 영어**(코드 글꼴에 한글이 없다), 한 줄 70자 안쪽, 읽히는 이름을 쓴다.
8. 쓸 수 있는 글자는 `engine.CHARS`(공백, `.,:;*+'`|-/\_~=#@%&o0O`, 대문자, 숫자)뿐이다.

## 다음 단계

- 해파리 15초 본편, 식물(꽃 피기) 주제를 워크플로대로 제작.
- 갤러리 웹(기획자 결정 2026-11-21):
  - 갤러리 카드에는 예시마다 **완성본 이미지(썸네일)만** 보인다.
  - 카드마다 **프롬프트 복사 버튼**. 방문자가 프롬프트를 복사해 자기 Claude Code(추천)나 Codex에 그대로 붙여 넣어 같은 영상을 만든다.
  - 프롬프트는 예시마다 manifest에 함께 둔다(이 저장소 사용법 + 해당 스토리보드 요약이 들어가야 단독으로 동작).
  - 하단 "직접 만들기": Claude Code 설치 -> 저장소 받기 -> `/new-reel`.
