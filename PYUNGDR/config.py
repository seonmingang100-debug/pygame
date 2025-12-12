import os

# =========================
# 기본 설정
# =========================
WIDTH, HEIGHT = 800, 600
FPS = 60

# 게임 상태
STATE_MENU  = 0   # 메인 메뉴
STATE_STORY = 1   # 시작 스토리
STATE_GAME  = 2   # 실제 게임
STATE_CLEAR = 3   # 엔딩 스토리

# 히트박스 축소 비율
PLAYER_HITBOX_SCALE = 0.35     # 플레이어
BUS_HITBOX_SCALE    = 0.30     # 버스
PROF_HITBOX_SCALE   = 0.50     # 교수(귀신 포함)

# 에셋 설정
ASSETS_DIR = "assets"
USE_PLACEHOLDER = True  # True면 이미지 없어도 사각형으로 대체해서 테스트 가능

# 섹션 개수
NUM_SECTIONS = 10

# BGM / 효과음 경로
BGM_MENU_PATH = os.path.join(ASSETS_DIR, "bgm_menu.mp3")
BGM_GAME_PATH = os.path.join(ASSETS_DIR, "bgm_game.mp3")
SCREAM_SFX_PATH = os.path.join(ASSETS_DIR, "scream.mp3")

# 버튼 위치
BTN_START_X = WIDTH - 600
BTN_START_Y = HEIGHT - 150
BTN_EXIT_X  = WIDTH - 200
BTN_EXIT_Y  = HEIGHT - 150

# 플레이어 / 교수 위치 및 속도
PLAYER_START_X = WIDTH // 2
PLAYER_START_Y = 500
PLAYER_SPEED   = 2

PROF_START_X   = WIDTH // 3
PROF_START_Y   = -120
PROF_TARGET_Y  = 550
PROF_SPEED     = 1
GHOST_SPEED    = 5

# 도로(언덕) 영역
ROAD_WIDTH = 300
ROAD_LEFT  = WIDTH // 2 - ROAD_WIDTH // 2
ROAD_RIGHT = WIDTH // 2 + ROAD_WIDTH // 2

# 섹션 번호 표지판 위치
SECTION_SIGN_X = 210
SECTION_SIGN_Y = 270

# 화면 진동(스크린 셰이크)
SHAKE_INTENSITY = 6   # 한 프레임당 최대 흔들림 픽셀 수

# 갑툭튀(표지판 점점 커짐) 관련
JUMPSCARE_DELAY      = 3000      # ms
JUMPSCARE_MAX_SCALE  = 4.0
JUMPSCARE_GROW_SPEED = 18.0      # scale/초
JUMPSCARE_DURATION   = 3000      # ms

# 트리거 영역 높이
TOP_TRIGGER_HEIGHT    = 10
BOTTOM_TRIGGER_HEIGHT = 10

# 섹션 전환(블랙아웃) 관련
TRANSITION_DURATION = 500  # ms

# 버스 이상현상 관련
BUS_START_X       = 500
BUS_START_Y       = 110
BUS_SHAKE_DURATION = 2000    # ms
BUS_FALL_SPEED     = 800     # px/sec
BUS_PRE_DELAY      = 2000    # ms
