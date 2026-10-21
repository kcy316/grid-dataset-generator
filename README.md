# gridgen — 그리드 생성 기반 객체 탐지 데이터셋 생성기

이미지 생성 API를 **한 번 호출할 때 N×N 그리드 이미지 1장**을 만들고, 이를 잘라 **N² 장의 학습용 이미지**를 얻는 도구입니다. YOLO 같은 객체 탐지 모델의 초기 학습 데이터를 적은 비용으로 빠르게 확보하는 것이 목표입니다.

```
"red apple" ──▶ [텍스트 모델] 배치별 촬영 방향 생성 ──▶ [이미지 모델] 4×4 그리드 1장
                                                              │
                                                              ▼
                                                 split ──▶ 640×640 타일 16장
```

## 특징

- **비용 효율**: 4×4 그리드면 API 호출 1번에 이미지 16장
- **배치별 다양성**: 배치마다 다른 조명 스타일을 배정하고, 텍스트 모델이 대상에 맞는 장소·각도·혼동 물체(distractor)를 제안
- **임의의 그리드 크기**: `--rows/--cols`로 3×3, 4×4, 5×5 등 자유롭게
- **안전한 재실행**: 기존 파일을 덮어쓰지 않고 다음 번호로 이어서 저장, 이미 분할된 그리드는 건너뜀
- **Dry run**: API 키 없이 프롬프트만 미리 확인
- **재현 가능한 기록**: 실행마다 사용한 프롬프트·모델·결과를 JSON manifest로 저장
- **테스트**: 분할 좌표 계산, 파일명 규칙, dry run을 pytest로 검증

## 설치

Python 3.10 이상.

```bash
git clone https://github.com/kcy316/grid-dataset-generator.git
cd grid-dataset-generator

python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

API 키 설정:

```bash
copy .env.example .env               # macOS/Linux: cp .env.example .env
# .env 를 열어 OPENAI_API_KEY 입력
```

`.env`는 `.gitignore`에 포함되어 있어 커밋되지 않습니다.

## 사용법

### 1. 프롬프트 미리보기 (API 호출 없음)

```bash
python -m gridgen generate --subject "red apple, whole and sliced" --batches 2 --dry-run
```

### 2. 생성 + 분할 한 번에

```bash
python -m gridgen run --subject "red apple" --batches 3
```

→ `output/grids/`에 그리드 3장, `output/tiles/`에 타일 48장

### 3. 여러 대상을 파일로 지정

```bash
python -m gridgen run --subjects-file subjects.example.txt
```

`subjects.example.txt` 형식 — 한 줄에 하나, `| N`으로 배치 수 지정:

```
red apple, whole and sliced | 2
glass bottle of water | 1
house key on a keyring
```

### 4. 단계별 실행

```bash
python -m gridgen generate --subject "glass bottle" --batches 2
python -m gridgen split
```

### 5. 5×5 그리드

```bash
python -m gridgen run --subject "coin" --rows 5 --cols 5
```

5×5는 `IMAGE_SIZE`를 3200×3200처럼 키워야 타일 해상도가 유지됩니다. 4×4와 5×5 그리드를 같은 폴더에서 분할할 때는 `--pattern`으로 대상을 나누세요.

```bash
python -m gridgen split --rows 5 --cols 5 --pattern "coin_*.png"
```

## 옵션

| CLI 옵션 | 환경 변수 | 기본값 | 설명 |
|----------|-----------|--------|------|
| `--subject` | | | 촬영 대상 설명 (여러 번 지정 가능) |
| `--subjects-file` | | | 대상 목록 파일 |
| `--batches` | | `1` | 대상당 그리드 수 |
| `--rows` / `--cols` | `GRID_ROWS` / `GRID_COLS` | `4` / `4` | 그리드 크기 |
| `--quality` | `IMAGE_QUALITY` | `medium` | `low` / `medium` / `high` / `auto` |
| `--no-llm-variation` | `USE_LLM_VARIATION=false` | | 텍스트 모델 대신 내장 스타일 프리셋 사용 (비용 절감) |
| `--tile-size` | `TILE_SIZE` | `640` | 타일 크기(px) |
| `--inner-crop` | `INNER_CROP` | `0.06` | 셀 가장자리 제거 비율 (구분선·옆 칸 침범 제거, 0~0.4) |
| `--output` | `OUTPUT_DIR` | `output` | 출력 폴더 |
| `--overwrite` | `OVERWRITE=true` | | 기존 파일 덮어쓰기 |
| `--dry-run` | | | 프롬프트만 출력하고 API는 호출 안 함 |
| | `IMAGE_MODEL` | `gpt-image-2` | 이미지 모델 |
| | `TEXT_MODEL` | `gpt-5.5` | 변형 문구용 텍스트 모델 |
| | `IMAGE_SIZE` | `2560x2560` | 그리드 해상도 |

우선순위: CLI 옵션 > 환경 변수(`.env`) > 기본값

## 출력 구조

```
output/
├── grids/      red_apple_grid_001.png
├── tiles/      red_apple_grid_001_r01_c01.png ... r04_c04.png
└── manifests/  20261021_153000_red_apple.json
```

manifest에는 배치별 프롬프트 전문, 변형 문구 출처(`llm` / `preset` / `default`), 성공 여부, 사용 모델이 기록됩니다.

## 프로젝트 구조

```
gridgen/
├── cli.py        # argparse 기반 CLI (generate / split / run)
├── config.py     # 환경 변수 → Settings dataclass
├── prompts.py    # 그리드·변형 프롬프트 템플릿, 스타일 프리셋
├── generate.py   # 이미지 생성, 재시도, manifest 기록
├── split.py      # 그리드 분할 (좌표 계산은 순수 함수로 분리)
└── naming.py     # 파일명 규칙, 배치 번호 자동 증가
tests/            # pytest
```

## 테스트

```bash
pip install pytest
pytest
```

API를 호출하지 않으므로 키 없이 실행됩니다.

## 한계와 다음 단계

- 이미지 모델이 그리드 경계를 항상 정확히 지키지는 않습니다. `--inner-crop`으로 완화하되, 분할 결과는 눈으로 검수하는 것을 권장합니다.
- 바운딩박스 라벨은 생성하지 않습니다. 분할된 타일을 [Label Studio](https://labelstud.io/), [CVAT](https://www.cvat.ai/), [Roboflow](https://roboflow.com/) 등으로 라벨링한 뒤 학습에 사용하세요.
- 합성 데이터만으로는 실제 환경 성능이 부족할 수 있으므로 실사 데이터와 섞어 쓰는 것을 권장합니다.

## License

MIT
