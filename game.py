import pygame
import sys
import os
import random   # ★ 랜덤 이상현상용
import math

# =========================
# 0. 기본 초기 설정
# =========================
pygame.init()
pygame.mixer.init()   # ★ 배경음악용

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("오르막길")

clock = pygame.time.Clock()
FONT = pygame.font.SysFont("malgungothic", 24)
SMALL_FONT = pygame.font.SysFont("malgungothic", 18)

STATE_MENU  = 0   # 메인 메뉴
STATE_STORY = 1   # 시작 스토리
STATE_GAME  = 2   # 실제 게임
STATE_CLEAR = 3   # 엔딩 스토리

current_state = STATE_MENU



# =========================
# 히트박스 축소 비율 (0.0 ~ 0.9)
# 값이 클수록 히트박스가 작아짐(충돌 판정 느슨해짐)
# =========================
PLAYER_HITBOX_SCALE = 0.35     # 플레이어
BUS_HITBOX_SCALE    = 0.30     # 버스
PROF_HITBOX_SCALE   = 0.50     # 교수(귀신 포함)

# =========================
# 1. 이미지 로드 함수 & 리소스
# =========================
ASSETS_DIR = "assets"  # 이미지 폴더

USE_PLACEHOLDER = True  # ★ True면 이미지 없어도 사각형으로 대체해서 테스트 가능

def load_image(name, size=None, fallback_color=None):
    """
    assets 폴더에서 이미지 파일을 불러오는 함수
    - 파일이 없고 USE_PLACEHOLDER=True면 단색 사각형 Surface 반환
    """
    path = os.path.join(ASSETS_DIR, name)

    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        return img

    if USE_PLACEHOLDER:
        # 파일이 없어도 테스트할 수 있게 임시 사각형 생성
        if size is None:
            size = (50, 50)
        surf = pygame.Surface(size, pygame.SRCALPHA)
        color = fallback_color if fallback_color is not None else (255, 0, 255)
        surf.fill(color)
        return surf

    # 이미지가 반드시 있어야 할 경우엔 에러
    raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {path}")

# 섹션 개수 (언덕 구간 몇 번 반복할지)
NUM_SECTIONS = 10

# --- 여기서 네가 그린 이미지들을 불러온다 ---
bg_img      = load_image("bg.png",        size=(WIDTH, HEIGHT), fallback_color=(30, 30, 30))
back_img      = load_image("back.png",        size=(WIDTH, HEIGHT), fallback_color=(30, 30, 30))
player_img  = load_image("player.png",    size=(100, 100),      fallback_color=(255, 255, 0))
prof_img    = load_image("propesr.png",   size=(120, 120),      fallback_color=(255, 100, 100))
bus_img     = load_image("bus.png",       size=(160, 160),      fallback_color=(255, 0, 0))
bg_anom_img = load_image("bg_anom.png",   size=(WIDTH, HEIGHT), fallback_color=(60, 0, 60))
bus_look_img = load_image("bus_look.png", size=(160, 160),      fallback_color=(255, 0, 0))
ghost_prof_img = load_image("prof_ghost.png", size=(120, 120), fallback_color=(150, 0, 150))
ghost_jumpscare_img = load_image("ghost_jumpscare.png", fallback_color=(255, 0, 0))
btn_start_img = load_image("btn_start.png", size=(300, 120), fallback_color=(0, 200, 0))
btn_exit_img  = load_image("btn_exit.png",  size=(300, 120), fallback_color=(200, 0, 0))
menu_bg_img = load_image("menu_bg.png", size=(WIDTH, HEIGHT), fallback_color=(20, 20, 20))


BGM_MENU_PATH = os.path.join(ASSETS_DIR, "bgm_menu.mp3")
BGM_GAME_PATH = os.path.join(ASSETS_DIR, "bgm_game.mp3")

# =========================
# SFX (효과음)
# =========================
SCREAM_SFX_PATH = os.path.join(ASSETS_DIR, "scream.mp3")  # 파일명 맞게 수정 가능
scream_sfx = None
if os.path.exists(SCREAM_SFX_PATH):
    scream_sfx = pygame.mixer.Sound(SCREAM_SFX_PATH)
    scream_sfx.set_volume(0.8)   # 볼륨 0.0 ~ 1.0, 취향대로
else:
    print(f"[WARN] 비명 효과음 파일을 찾을 수 없음: {SCREAM_SFX_PATH}")

def play_scream():
    if scream_sfx is not None:
        scream_sfx.play()


current_bgm = None  # "menu", "game", 또는 None

def play_bgm(mode: str | None):
    """
    mode: "menu", "game", 또는 None
    같은 곡이 이미 재생 중이면 다시 로드하지 않음.
    """
    global current_bgm

    # 꺼 달라는 경우
    if mode is None:
        pygame.mixer.music.stop()
        current_bgm = None
        return

    # 이미 그 모드의 BGM이 재생 중이면 아무 것도 안 함
    if current_bgm == mode:
        return

    # 모드에 따라 파일 선택
    if mode == "menu":
        path = BGM_MENU_PATH
    elif mode == "game":
        path = BGM_GAME_PATH
    else:
        return  # 이상한 값이면 무시

    # 파일이 없으면 조용히 실패 (에러 안 터지게)
    if not os.path.exists(path):
        print(f"[WARN] BGM 파일을 찾을 수 없음: {path}")
        current_bgm = None
        return

    # 실제 재생
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(0.5)  # 볼륨(0.0~1.0) 취향대로 조절
    pygame.mixer.music.play(-1)         # -1 = 무한 반복
    current_bgm = mode



#==================== 버튼
BTN_START_X = WIDTH - 600
BTN_START_Y = HEIGHT -150
BTN_EXIT_X  = WIDTH -200
BTN_EXIT_Y  = HEIGHT -150




#=====================================
# 섹션 번호 표지판 (정상 1~5)
#=====================================
section_sign_imgs = []
for i in range(1, NUM_SECTIONS + 1):  # 1~5
    fname = f"sign_section_{i}.png"
    img = load_image(fname, size=(180, 180), fallback_color=(200, 200, 200))
    section_sign_imgs.append(img)

# ★ 이상 표지판(공용 1개)
sign_anom_img = load_image("sign_section_anom.png", size=(180, 180), fallback_color=(255, 0, 255))
# 갑툭튀 표지판
jumpscare_img = load_image("sign_jumpscare.png", fallback_color=(255, 0, 255))

current_jumpscare_image = jumpscare_img

# =========================
# 2. 오브젝트 클래스 정의 (버스용)
# =========================
class GameObject:
    """
    게임에 등장하는 오브젝트(버스 등)를 관리하는 클래스.
    지금은 버스만 사용하고, 이상현상에는 참여하지 않음.
    """
    def __init__(self, name, x, y, img_normal):
        self.name = name
        self.x = x
        self.y = y
        self.img_normal = img_normal

    def draw(self, surface):
        rect = self.img_normal.get_rect(center=(self.x, self.y))
        surface.blit(self.img_normal, rect)

# =========================
# 3. 오브젝트 생성 (버스만 사용)
# =========================
objects = []

# 버스: 기본적으로 멈춰 있는 오브젝트 (항상 정상)

# =========================
# 버스 이상현상(2번 패턴) 관련 변수
# =========================
BUS_START_X = 500      # 버스 기본 x (지금 bus1 만든 위치랑 맞추기)
BUS_START_Y = 110      # 버스 기본 y

BUS_SHAKE_DURATION = 2000    # 흔들리는 시간(ms) → 2초
BUS_FALL_SPEED = 800         # 아래로 떨어지는 속도 (px/sec, 상황 봐서 조절)
BUS_PRE_DELAY = 2000         # ★ 섹션 진입 후, 흔들리기 시작하기 전 대기 시간(ms)

bus_state = "idle"           # "idle", "shaking", "falling"
bus_timer_ms = 0             # 현재 상태에서 경과 시간(ms)
#버스 ====
bus1 = GameObject("bus1", BUS_START_X, BUS_START_Y, bus_img)
objects.append(bus1)

# 섹션 인덱스 (0 ~ NUM_SECTIONS-1)
current_section = 0

# 이상현상여부
section_sign_anomaly = [False] * NUM_SECTIONS   # 표지판 이상
section_bus_anomaly  = [False] * NUM_SECTIONS   # 버스 이상
section_bg_anomaly   = [False] * NUM_SECTIONS   # ★ 배경 이상 (3번 째 패턴)
section_bus_look_anomaly = [False] * NUM_SECTIONS   # ★ 4번째 이상현상: 버스 시선 반전
section_control_flip_anomaly = [False] * NUM_SECTIONS #5번쨰 방향키반전
section_ghost_prof_anomaly = [False] * NUM_SECTIONS  # 6번쨰 귀신 교수 이상



# =========================
# 4. 플레이어 / 트리거 / 기타 변수
# =========================

PLAYER_START_X = WIDTH // 2
PLAYER_START_Y = 500          # ← 지금 교수님 멈추는 y좌표랑 비슷하게

player_x, player_y = PLAYER_START_X, PLAYER_START_Y
PLAYER_SPEED = 2


# 교수님 변수
PROF_START_X = WIDTH // 3
PROF_START_Y = -120
PROF_TARGET_Y = 550

prof_x = PROF_START_X
prof_y = PROF_START_Y
prof_speed = 1
prof_target_y = PROF_TARGET_Y
prof_arrived = False

# 섹션 번호 표지판 위치
SECTION_SIGN_X = 210
SECTION_SIGN_Y = 270

# 길(언덕) 영역
ROAD_WIDTH = 300
ROAD_LEFT = WIDTH // 2 - ROAD_WIDTH // 2
ROAD_RIGHT = WIDTH // 2 + ROAD_WIDTH // 2




# =========================
# 화면 진동(스크린 셰이크) 관련 변수
# =========================
SHAKE_INTENSITY = 6   # 한 프레임당 최대 흔들림 픽셀 수 (5~10 사이에서 마음에 드는 값 찾기)
shake_dx = 0          # x 방향 오프셋
shake_dy = 0          # y 방향 오프셋


# =========================
# 갑툭튀(표지판 점점 커짐) 관련 변수
# =========================
JUMPSCARE_DELAY = 3000      # 몇 ms 후 발동할지 (10초 = 10000)
JUMPSCARE_MAX_SCALE = 4.0    # 최대 몇 배까지 커질지
JUMPSCARE_GROW_SPEED = 18.0   # 1초에 scale이 얼마나 늘어날지 (대략적인 속도)

stay_time_ms = 0             # 현재 섹션에 머무른 시간(ms)
jumpscare_active = False     # 갑툭튀 발동 상태 여부
jumpscare_scale = 1.0        # 현재 배율 (1.0부터 시작해서 점점 커짐)

JUMPSCARE_DURATION = 3000    # 점프스퀘어가 유지되는 시간 (3초 = 3000ms)
jumpscare_elapsed_ms = 0     # 점프스퀘어가 켜진 이후 지난 시간

# 트리거 영역
TOP_TRIGGER_HEIGHT = 10
BOTTOM_TRIGGER_HEIGHT = 10

top_trigger = pygame.Rect(0, 0, WIDTH, TOP_TRIGGER_HEIGHT)  # 위: 이상 없음 선택
bottom_trigger = pygame.Rect(0, HEIGHT - BOTTOM_TRIGGER_HEIGHT, WIDTH, BOTTOM_TRIGGER_HEIGHT)  # 아래: 이상 있음 선택

game_over = False
message = " "
sub_message = ""

show_debug = False  # D 키로 트리거 박스 보기

#===========================
#히트박스 조절 함수
#==============================
def shrink_player_rect(rect):
    return rect.inflate(
        -rect.width * PLAYER_HITBOX_SCALE*2,
        -rect.height * PLAYER_HITBOX_SCALE
    )

def shrink_bus_rect(rect):
    return rect.inflate(
        -rect.width * BUS_HITBOX_SCALE *2,
        -rect.height * BUS_HITBOX_SCALE
    )

def shrink_prof_rect(rect):
    return rect.inflate(
        -rect.width * PROF_HITBOX_SCALE*1.2,
        -rect.height * PROF_HITBOX_SCALE
    )


# =========================
# 5. 섹션별 이상 상태 랜덤 설정
# =========================
def init_section_anomalies():
    """
    섹션별 이상현상 설정
    - 0번 섹션: 항상 정상
    - 1~4번 섹션: 한 섹션당 아래 중 하나만 선택 (겹치지 않음)
        "none"      : 아무 이상 없음
        "sign"      : 표지판 이상
        "bus_move"  : 버스 흔들리고 떨어지는 이상(2번 현상)
        "bg"        : 배경 이상(3번 현상)
        "bus_look"  : 버스 시선 반전(4번 현상)
    """
    global section_sign_anomaly, section_bus_anomaly, section_bg_anomaly, section_bus_look_anomaly ,section_control_flip_anomaly, section_ghost_prof_anomaly

    section_sign_anomaly      = [False] * NUM_SECTIONS
    section_bus_anomaly       = [False] * NUM_SECTIONS
    section_bg_anomaly        = [False] * NUM_SECTIONS
    section_bus_look_anomaly  = [False] * NUM_SECTIONS
    section_ghost_prof_anomaly = [False] * NUM_SECTIONS
    section_control_flip_anomaly = [False] * NUM_SECTIONS
    

    # 0번 섹션은 항상 정상
    section_sign_anomaly[0]     = False
    section_bus_anomaly[0]      = False
    section_bg_anomaly[0]       = False
    section_bus_look_anomaly[0] = False
    section_ghost_prof_anomaly[0] = False
    section_control_flip_anomaly[0] = False

    for i in range(1, NUM_SECTIONS):
        if i == 8:
            continue

        pattern = random.choice(["none", "sign", "bus_move", "bg", "bus_look","control_flip"])

        if pattern == "sign":
            section_sign_anomaly[i] = True
        elif pattern == "bus_move":
            section_bus_anomaly[i] = True
        elif pattern == "bg":
            section_bg_anomaly[i] = True
        elif pattern == "bus_look":
            section_bus_look_anomaly[i] = True
        elif pattern == "control_flip":
            section_control_flip_anomaly[i] = True
    
        # "none"이면 아무 것도 True 안 됨

    # ★ 9번 섹션(인덱스 8)을 귀신 교수 섹션으로 고정
    section_ghost_prof_anomaly[8] = True



def has_anomaly_in_section(section_index: int) -> bool:
    """
    해당 섹션에 실제로 이상이 있는지 여부.
    정답 판정에서 사용.
    """
    return (
        section_control_flip_anomaly[section_index] or
        section_sign_anomaly[section_index] or
        section_bus_anomaly[section_index] or
        section_bg_anomaly[section_index] or
        section_bus_look_anomaly[section_index] or
        section_ghost_prof_anomaly[section_index]
    )

def reset_game():
    """게임 전체를 초기 상태로 리셋"""
    global current_section, player_x, player_y, game_over, message, sub_message
    global prof_y, prof_arrived
    global bus_state, bus_timer_ms   # ★ 추가
    global prof_x, prof_y, prof_arrived
    global BUS_START_X, BUS_START_Y  

    current_section = 0
    player_x, player_y = PLAYER_START_X, PLAYER_START_Y
    game_over = False
    
    sub_message = ""

    # 교수님도 처음부터 다시
    prof_x = PROF_START_X
    prof_y = PROF_START_Y
    prof_arrived = False

    # ★ 버스 상태 리셋
    bus_state = "idle"
    bus_timer_ms = 0
    bus1.x = BUS_START_X
    bus1.y = BUS_START_Y

    stay_time_ms = 0
    jumpscare_active = False
    jumpscare_scale = 1.0

    # 섹션별 이상현상 다시 랜덤 설정
    init_section_anomalies()

# 게임 시작 시 한 번 초기화
init_section_anomalies()

# =========================
# 5.5 섹션 전환(블랙아웃) 관련 변수
# =========================
TRANSITION_DURATION = 500  # 0.5초 (1초로 하고 싶으면 1000으로)
in_transition = False
transition_time = 0
next_section = 0   # 전환이 끝나고 이동할 섹션 번호

def start_transition(target_section: int):
    """섹션 전환 연출 시작 (검은 화면)"""
    global in_transition, transition_time, next_section
    in_transition = True
    transition_time = 0
    next_section = target_section

     # 섹션이 바뀔 거니까 갑툭튀 관련 상태도 리셋
    stay_time_ms = 0
    jumpscare_active = False
    jumpscare_scale = 1.0

# =========================
# 6. 그리기 함수들
# =========================
def draw_world():
    """배경 + 오브젝트들을 그리는 함수"""
    # 1) 배경
    if section_bg_anomaly[current_section]:
        screen.blit(bg_anom_img, (0, 0))
    else:
        screen.blit(bg_img, (0, 0))

     # 2) 버스 그리기
    bus_offset_x = 0
    bus_offset_y = 0

    if bus_state == "shaking":
        bus_offset_x += random.randint(-3, 3)
        bus_offset_y += random.randint(-3, 3)

    # ★ 기본은 아래를 보는 버스 이미지
    current_bus_img = bus_img

    # ★ 이 섹션이 '버스 시선 이상' 섹션이면, 위를 보는 버스 이미지로 교체
    if section_bus_look_anomaly[current_section]:
        current_bus_img = bus_look_img

    bus_rect = current_bus_img.get_rect(center=(bus1.x + bus_offset_x, bus1.y + bus_offset_y))
    screen.blit(current_bus_img, bus_rect)

    # 3) 교수님
    if section_ghost_prof_anomaly[current_section]:
        prof_image = ghost_prof_img   # 👻
    else:
        prof_image = prof_img         # 일반 교수님

    rect_prof = prof_image.get_rect(center=(prof_x, prof_y))
    screen.blit(prof_image, rect_prof)

    # 4) 섹션 번호 표지판 (여기에 이상현상 적용)
    if 0 <= current_section < len(section_sign_imgs):
        if section_sign_anomaly[current_section]:
            # 이 섹션은 '표지판 이상' 상태 → 이상한 표지판 이미지
            sign_img = sign_anom_img
        else:
            # 표지판은 정상 → 섹션 번호가 적힌 표지판 이미지
            sign_img = section_sign_imgs[current_section]
    else:
        sign_img = section_sign_imgs[-1]


    rect_sign = sign_img.get_rect(center=(SECTION_SIGN_X, SECTION_SIGN_Y))
    screen.blit(sign_img, rect_sign)

    # 5) 갑툭튀 연출: 이상 표지판이 화면 정중앙에서 빠르게 커지면서 등장
    if jumpscare_active:
        # 기본 이미지 크기
        base_w, base_h = jumpscare_img.get_size()

        # 현재 배율 적용
        w = int(base_w * jumpscare_scale)
        h = int(base_h * jumpscare_scale)

        # 혹시라도 너무 작게 나오면 최소값 보호
        if w < 10: w = 10
        if h < 10: h = 10

        big_img = pygame.transform.smoothscale(current_jumpscare_image, (w, h))
        big_rect = big_img.get_rect(center=(WIDTH // 2 + shake_dx, HEIGHT // 2 + shake_dy))
        screen.blit(big_img, big_rect)

# =========================
# 스토리 화면용 텍스트
# =========================
STORY_LINES = [
    "학기말 종강을 앞두고 마지막 파이썬응용 기말시험을 보러 아침 일찍 등교하는 민진이",
    "설레는 마음으로 강남대의 머리띠를 지나 지옥의 오르막길을 오르기 시작하는데..",
    "평소랑 크게 다르지는 않지만 이상하게도 한참을 올라가도 끝나지 않는 오르막길",
    "민진이는 이 오르막길을 무사히 올라가 시험을 치를 수 있을까?",
    "배경을 관찰한 뒤, 위로 가면 '이상 없음', 아래로 가면 '이상 있음'으로 선택됩니다.",
    "",
    "[아무 키나 눌러서 계속하기]"
]

def draw_story():
    # 스토리 화면 배경 (메뉴 배경 그대로 사용하거나 bg_img 써도 됨)
    screen.blit(back_img, (0, 0))
    screen.blit(player_img, (WIDTH // 2, HEIGHT - 200 ))

    # 제목
    title = FONT.render("Story", True, (255, 255, 255))
    rect_t = title.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title, rect_t)

    # 스토리 텍스트 출력
    start_y = 160
    line_gap = 40

    for i, line in enumerate(STORY_LINES):
        text_surf = SMALL_FONT.render(line, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, start_y + i * line_gap))
        screen.blit(text_surf, text_rect)

# =========================
# 클리어 스토리 화면용 텍스트
# =========================
CLEAR_LINES = [
    "그렇게 평소와 다른 오르막길의 여러가지 이상현상들을 찾아내",
    "무사히 교실로 도착한 민진이는 무사히 시험을 칠 수 있게되었다.",
    "얏호!",
    "",
    "[아무 키나 눌러서 메인 메뉴로 돌아가기]"
]

def draw_clear():
    # 배경은 메뉴 배경 재사용 (원하면 bg_img로 바꿔도 됨)
    screen.blit(back_img, (0, 0))
    screen.blit(player_img, (WIDTH // 2, HEIGHT -200))

    # 제목
    title = FONT.render("Clear", True, (255, 255, 255))
    rect_t = title.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title, rect_t)

    # 텍스트 출력
    start_y = 160
    line_gap = 40

    for i, line in enumerate(CLEAR_LINES):
        text_surf = SMALL_FONT.render(line, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, start_y + i * line_gap))
        screen.blit(text_surf, text_rect)

def draw_menu():
    # 배경 이미지 그리기
    screen.blit(menu_bg_img, (0, 0))
    

    

    # 시작 버튼
    start_rect = btn_start_img.get_rect(center=(BTN_START_X, BTN_START_Y))
    screen.blit(btn_start_img, start_rect)

    # 종료 버튼
    exit_rect = btn_exit_img.get_rect(center=(BTN_EXIT_X, BTN_EXIT_Y))
    screen.blit(btn_exit_img, exit_rect)

    return start_rect, exit_rect


def draw_player():
    """플레이어를 그리는 함수"""
    rect = player_img.get_rect(center=(player_x + shake_dx, player_y + shake_dy))
    screen.blit(player_img, rect)

def draw_ui():
    """현재 섹션, 안내 문구, 디버그 표시 등 UI를 그리는 함수"""
    # 메인 메시지
    msg_surface = FONT.render(message, True, (255, 255, 255))
    screen.blit(msg_surface, (20, HEIGHT - 60))

    if sub_message:
        sub_surface = FONT.render(sub_message, True, (255, 255, 255))
        screen.blit(sub_surface, (20, HEIGHT - 30))

    # 섹션 정보
    section_text = f"섹션: {current_section + 1} / {NUM_SECTIONS}"
    section_surface = SMALL_FONT.render(section_text, True, (255, 255, 0))
    #screen.blit(section_surface, (20, 20))

    # 현재 섹션에 실제로 이상이 있는지 디버그용 텍스트
    real_has_anom = has_anomaly_in_section(current_section)
    real_text = f"실제 상태: {'이상 있음' if real_has_anom else '이상 없음'}"
    real_color = (255, 100, 100) if real_has_anom else (100, 255, 100)
    real_surface = SMALL_FONT.render(real_text, True, real_color)
    #screen.blit(real_surface, (20, 45))

    # 디버그 정보
    if show_debug:
        dbg_surface = SMALL_FONT.render("DEBUG: 트리거 박스 표시 중 (D키로 토글)", True, (200, 200, 200))
        screen.blit(dbg_surface, (20, HEIGHT - 90))

def draw_debug():
    """디버그용: 트리거 + 플레이어 + 버스 + 교수(귀신) 히트박스 표시"""
    # 1) 위/아래 트리거 박스
    pygame.draw.rect(screen, (0, 0, 255), top_trigger, 1)
    pygame.draw.rect(screen, (255, 0, 0), bottom_trigger, 1)

    # 2) 플레이어 히트박스
    player_rect = player_img.get_rect(center=(player_x, player_y))
    player_hit_rect = shrink_player_rect(player_rect)
    pygame.draw.rect(screen, (0, 255, 255), player_hit_rect, 1)

    # 3) 버스 히트박스
    bus_image = bus_look_img if section_bus_look_anomaly[current_section] else bus_img
    bus_rect = bus_image.get_rect(center=(bus1.x, bus1.y))
    bus_hit_rect = shrink_bus_rect(bus_rect)
    pygame.draw.rect(screen, (255, 255, 0), bus_hit_rect, 1)

    # 4) 교수 / 귀신 교수 히트박스
    prof_image = ghost_prof_img if section_ghost_prof_anomaly[current_section] else prof_img
    prof_rect = prof_image.get_rect(center=(prof_x, prof_y))
    prof_hit_rect = shrink_prof_rect(prof_rect)
    pygame.draw.rect(screen, (0, 255, 0), prof_hit_rect, 1)


play_bgm("menu")

# =========================
# 7. 메인 게임 루프
# =========================
running = True
while running:
    dt = clock.tick(60)  # 60 FPS 기준 (dt는 ms 단위)

    # =========================
    # 상태에 따른 BGM 전환
    # =========================
    if current_state in (STATE_MENU, STATE_STORY, STATE_CLEAR):
        play_bgm("menu")
    elif current_state == STATE_GAME:
        play_bgm("game")
    else:
        play_bgm(None)  # 혹시 모를 기타 상태


    # -------------------------
    # 이벤트 처리
    # -------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 메뉴 상태: 버튼 클릭 처리
        if current_state == STATE_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                start_rect = btn_start_img.get_rect(center=(BTN_START_X, BTN_START_Y))
                exit_rect  = btn_exit_img.get_rect(center=(BTN_EXIT_X,  BTN_EXIT_Y))

                if start_rect.collidepoint(mx, my):
                    # ▶ 메뉴 → 스토리 화면으로 이동
                    current_state = STATE_STORY

                elif exit_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

        # 스토리 상태: 아무 키나 누르면 게임 시작
        elif current_state == STATE_STORY:
            if event.type == pygame.KEYDOWN:
                # ▶ 스토리 → 게임 시작
                current_state = STATE_GAME
                reset_game()

        # 게임 상태: 키보드 입력 (R, D 등)
        elif current_state == STATE_GAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                if event.key == pygame.K_d:
                    show_debug = not show_debug

        
        elif current_state == STATE_CLEAR:
            # 클리어 스토리 화면: 아무 키나 누르면 다시 메뉴로
            if event.type == pygame.KEYDOWN:
                game_over = False      # 다시 플레이 가능하게
                current_state = STATE_MENU


    # -------------------------
    # 상태별로 화면 그리기 & 로직 처리
    # -------------------------

    # 1) 메뉴 상태: 메뉴만 그리고 다음 프레임
    if current_state == STATE_MENU:
        draw_menu()
        pygame.display.flip()
        continue

    # 2) 스토리 상태: 스토리만 그리고 다음 프레임
    if current_state == STATE_STORY:
        draw_story()
        pygame.display.flip()
        continue

    if current_state == STATE_CLEAR:
        draw_clear()
        pygame.display.flip()
        continue

    # 3) 게임 상태: 아래부터는 기존 게임 로직 그대로
    # =========================
    # 전환 연출 모드 처리 (블랙아웃)
    # =========================
    if in_transition:
        transition_time += dt
        screen.fill((0, 0, 0))

        txt = SMALL_FONT.render("...", True, (255, 255, 255))
        rect = txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(txt, rect)

        if transition_time >= TRANSITION_DURATION:
            current_section = next_section

            # 플레이어 / 교수님 리셋
            player_x, player_y = PLAYER_START_X, PLAYER_START_Y
            prof_x = PROF_START_X
            prof_y = PROF_START_Y
            prof_arrived = False

            # 갑툭튀 / 버스 상태 리셋
            stay_time_ms = 0
            jumpscare_active = False
            jumpscare_scale = 1.0

            bus_state = "idle"
            bus_timer_ms = 0
            bus1.x = BUS_START_X
            bus1.y = BUS_START_Y

            in_transition = False

        pygame.display.flip()
        continue

    # =========================
    # 평소 게임 진행 로직
    # =========================
    if not game_over:
        keys = pygame.key.get_pressed()

        if not jumpscare_active:
            old_x, old_y = player_x, player_y

            # 플레이어 이동
            if section_control_flip_anomaly[current_section]:
                if keys[pygame.K_UP]:
                    player_x -= PLAYER_SPEED    # ↑ = 왼쪽
                if keys[pygame.K_DOWN]:
                    player_x += PLAYER_SPEED    # ↓ = 오른쪽
                if keys[pygame.K_LEFT]:
                    player_y += PLAYER_SPEED    # ← = 아래
                if keys[pygame.K_RIGHT]:
                    player_y -= PLAYER_SPEED*15 # → = 위
            else:
                if keys[pygame.K_LEFT]:
                    player_x -= PLAYER_SPEED
                if keys[pygame.K_RIGHT]:
                    player_x += PLAYER_SPEED
                if keys[pygame.K_UP]:
                    player_y -= PLAYER_SPEED
                if keys[pygame.K_DOWN]:
                    player_y += PLAYER_SPEED

            # 도로/화면 경계 처리
            if player_x < ROAD_LEFT:
                player_x = ROAD_LEFT
            if player_x > ROAD_RIGHT:
                player_x = ROAD_RIGHT
            if player_y < 0:
                player_y = 0
            if player_y > HEIGHT:
                player_y = HEIGHT

        # ----- 교수 이동 -----
        if section_ghost_prof_anomaly[current_section]:
            dx = player_x - prof_x
            dy = player_y - prof_y
            dist = math.hypot(dx, dy)

            if dist > 1:
                ghost_speed = 5
                prof_x += ghost_speed * (dx / dist)
                prof_y += ghost_speed * (dy / dist)
        else:
            if not prof_arrived:
                prof_y += prof_speed
                if prof_y >= prof_target_y:
                    prof_y = prof_target_y
                    prof_arrived = True

        # ----- 표지판 이상 → 점프스퀘어 -----
        if section_sign_anomaly[current_section]:
            if not jumpscare_active:
                stay_time_ms += dt
                if stay_time_ms >= JUMPSCARE_DELAY:
                    jumpscare_active = True
                    current_jumpscare_image = jumpscare_img
                    jumpscare_scale = 1.0
                    jumpscare_elapsed_ms = 0

                    play_scream()
        else:
            stay_time_ms = 0

        # 점프스퀘어 확대 & 3초 후 섹션 1로 귀환
        if jumpscare_active:
            jumpscare_scale += JUMPSCARE_GROW_SPEED * (dt / 1000.0)
            if jumpscare_scale > JUMPSCARE_MAX_SCALE:
                jumpscare_scale = JUMPSCARE_MAX_SCALE

            jumpscare_elapsed_ms += dt
            if jumpscare_elapsed_ms >= JUMPSCARE_DURATION:
                init_section_anomalies()
                start_transition(0)
                jumpscare_active = False
                jumpscare_scale = 1.0
                stay_time_ms = 0
                jumpscare_elapsed_ms = 0

        # 화면 흔들림
        if jumpscare_active:
            shake_dx = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
            shake_dy = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
        else:
            shake_dx = 0
            shake_dy = 0

        # ----- 버스 이상현상 -----
        if section_bus_anomaly[current_section]:
            if bus_state == "idle":
                bus_state = "waiting"
                bus_timer_ms = 0
            elif bus_state == "waiting":
                bus_timer_ms += dt
                if bus_timer_ms >= BUS_PRE_DELAY:
                    bus_state = "shaking"
                    bus_timer_ms = 0
            elif bus_state == "shaking":
                bus_timer_ms += dt
                if bus_timer_ms >= BUS_SHAKE_DURATION:
                    bus_state = "falling"
            elif bus_state == "falling":
                bus1.y += BUS_FALL_SPEED * (dt / 1000.0)
        else:
            bus_state = "idle"
            bus_timer_ms = 0
            bus1.x = BUS_START_X
            bus1.y = BUS_START_Y

        # ----- 히트박스 계산 -----
        player_rect = player_img.get_rect(center=(player_x, player_y))
        player_hit_rect = shrink_player_rect(player_rect)

        # 교수 충돌
        prof_image = ghost_prof_img if section_ghost_prof_anomaly[current_section] else prof_img
        prof_rect = prof_image.get_rect(center=(prof_x, prof_y))
        prof_hit_rect = shrink_prof_rect(prof_rect)

        if section_ghost_prof_anomaly[current_section]:
            if player_hit_rect.colliderect(prof_hit_rect) and not jumpscare_active:
                jumpscare_active = True
                current_jumpscare_image = ghost_jumpscare_img
                jumpscare_scale = 1.0
                jumpscare_elapsed_ms = 0
                stay_time_ms = 0
                play_scream()
        else:
            if player_hit_rect.colliderect(prof_hit_rect):
                player_x, player_y = old_x, old_y

        # 버스 충돌
        bus_image = bus_look_img if section_bus_look_anomaly[current_section] else bus_img
        bus_rect = bus_image.get_rect(center=(bus1.x, bus1.y))
        bus_hit_rect = shrink_bus_rect(bus_rect)

        if player_hit_rect.colliderect(bus_hit_rect):
            if bus_state == "falling" and section_bus_anomaly[current_section]:
                init_section_anomalies()
                start_transition(0)
                continue
            player_x, player_y = old_x, old_y

        # 위/아래 트리거 선택
        chosen = None
        if player_rect.colliderect(top_trigger):
            chosen = "no_anomaly"
        elif player_rect.colliderect(bottom_trigger):
            chosen = "anomaly"

        if chosen is not None:
            real = "anomaly" if has_anomaly_in_section(current_section) else "no_anomaly"

            if chosen == real:
                
                next_sec = current_section + 1

                if next_sec >= NUM_SECTIONS:
                    # ★ 모든 섹션 클리어 → 클리어 스토리 화면으로
                    game_over = True
                    current_state = STATE_CLEAR
                else:
                    # 다음 섹션으로 전환
                    start_transition(next_sec)

            else:
                # ❌ 오답일 때: 1섹션으로 회귀 + 이상현상 재추첨
                init_section_anomalies()
                start_transition(0)
                

    # =====================
    # 화면 그리기
    # =====================
    draw_world()
    draw_player()
    draw_ui()
    if show_debug:
        draw_debug()

    pygame.display.flip()

# 종료
pygame.quit()
sys.exit()
