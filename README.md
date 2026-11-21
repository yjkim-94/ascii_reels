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

- `engine.py`: 글자 아틀라스, `Grid`(108x61 칸), 배경(`LetterRain`, `Snow`), 빛 번짐, 큰 글씨 자막,
  HUD, 코드 패널, mp4 인코딩. 주제와 무관한 것은 모두 여기.
- `themes/*.py`: 주제 하나 = 파일 하나. 이 파일이 그대로 영상 하단에 나온다.
  `christmas_tree.py`(2D 마스크 방식, 15초), `jellyfish_sample.py`(3D 점 구름 방식, 3초 렌더 시안).
- `render.py`: 명령줄 진입점.

## 주제 스크립트 규약 (LLM 자동 생성 시 이것만 지키게 한다)

1. 모듈 상수: `DURATION`(초, **최대 15**, 넘으면 엔진이 거부), 선택 `GLOW`(빛 번짐 세기, 0.9 안팎).
2. `draw(g, t)`를 구현한다. **t만으로 결정**되어야 한다(전역 상태 변경 금지, 난수는 모듈 로드 때 고정 시드로 미리 뽑기).
3. 반환: `{"hud": [줄, ...], "caption": (전체문구, 보일글자수, y, rgb, 크기, 자간, 커서여부)}` 또는 HUD 줄 목록만.
4. 그리기 API
   - 좌표: `g.X`(-1..1, 가운데 0), `g.Y`(0 위 .. 1 아래), `g.r`, `g.c`(칸 번호). 위쪽 화면은 거의 정사각형.
   - `g.put(mask, chars, color, alpha)`: 마스크 칸 칠하기. `chars`는 글자 번호(`CIDX["*"]`, `idx("ABC")`).
   - `g.put_cells(rows, cols, chars, colors)`: 점 찍기. `g.to_cell(x, y)`로 좌표 변환.
   - `g.text(row, col, "문자열", color)`.
   - 색은 RGB 0~1. 1을 넘기면 더 밝게 번진다(전구, 별 등 강조).
   - 3D: 점 (N,3)을 `rot_y`/`rot_x`로 돌리고 `splat(g, P, rgb, lum, chars)`로 찍는다.
     원근 투영, 칸마다 가장 앞 점만 남기기(z-buffer), 밝기 -> 잉크 면적 순 글자(`RAMP`)를 엔진이 한다.
     선(촉수, 빛줄기)은 `dir_chars(dx, dy)`로 `| / \ -` 글자를 쓴다.
5. 시간 도우미: `ramp(t, a, b)`, `ease`(빠르게 시작), `smooth`(고르게), `pop`(튀어나옴).
6. 플롯: `T_*` 구간 상수로 "바탕 → 형체가 자람 → 장식이 하나씩 → 마지막 한 방(별/꽃/문구) → 페이드아웃"을
   0~15초에 배치. 끝은 처음 화면(배경만)과 같게 해서 반복 재생이 이어지게 한다.
7. 화면에 나오는 파일이므로 **주석은 영어**(코드 글꼴에 한글이 없다), 한 줄 70자 안쪽, 읽히는 이름을 쓴다.
8. 쓸 수 있는 글자는 `engine.CHARS`(공백, `.,:;*+'`|-/\_~=#@%&o0O`, 대문자, 숫자)뿐이다.

## 다음 단계

- `themes/`에 식물(꽃 피기), 해파리(머리 → 다리 → 유영) 추가.
- 주제 문장 → LLM이 위 규약대로 스크립트 생성 → `--still`로 자동 점검(빈 화면, 예외) → 렌더.
