import pygame
import sys
import os
import random
import math

from config import *
from anomalies import (
    init_section_anomalies,
    has_anomaly_in_section,
    section_sign_anomaly,
    section_bus_anomaly,
    section_bg_anomaly,
    section_bus_look_anomaly,
    section_control_flip_anomaly,
    section_ghost_prof_anomaly,
)
import assets

# =========================
# 0. 기본 초기 설정
# =========================
pygame.init()
pygame.mixer.init()   # 배경음악용

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("오르막길")

clock = pygame.time.Clock()

# 폰트 / 이미지 / 사운드 로드
fonts = assets.load_fonts()
FONT = fonts["main"]
SMALL_FONT = fonts["small"]

images = assets.load_images()
bg_img             = images["bg"]
back_img           = images["back"]
player_img         = images["player"]
prof_img           = images["prof"]
bus_img            = images["bus"]
bg_anom_img        = images["bg_anom"]
bus_look_img       = images["bus_look"]
ghost_prof_img     = images["ghost_prof"]
ghost_jumpscare_img = images["ghost_jumpscare"]
btn_start_img      = images["btn_start"]
btn_exit_img       = images["btn_exit"]
menu_bg_img        = images["menu_bg"]
section_sign_imgs  = images["section_signs"]
sign_anom_img      = images["sign_anom"]
jumpscare_img      = images["jumpscare"]

sounds = assets.load_sounds()
scream_sfx = sounds["scream"]

# =========================
# BGM 관련
# =========================
current_bgm = None  # "menu", "game", 또는 None


def play_scream():
    if scream_sfx is not None:
        scream_sfx.play()


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


# =========================
# 상태
# =========================
current_state = STATE_MENU

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

BUS_START_X = BUS_START_X  # config에서 가져온 값 (이름 그대로 사용)
BUS_START_Y = BUS_START_Y

# 버스 이상현상(2번 패턴) 관련 변수
bus_state = "idle"           # "idle", "waiting", "shaking", "falling"
bus_timer_ms = 0             # 현재 상태에서 경과 시간(ms)

bus1 = GameObject("bus1", BUS_START_X, BUS_START_Y, bus_img)
objects.append(bus1)

# 섹션 인덱스 (0 ~ NUM_SECTIONS-1)
current_section = 0

# =========================
# 4. 플레이어 / 트리거 / 기타 변수
# =========================
player_x, player_y = PLAYER_START_X, PLAYER_START_Y

# 교수님 변수
prof_x = PROF_START_X
prof_y = PROF_START_Y
prof_speed = PROF_SPEED
prof_target_y = PROF_TARGET_Y
prof_arrived = False

# 길(언덕) 영역
ROAD_LEFT_LOCAL  = ROAD_LEFT
ROAD_RIGHT_LOCAL = ROAD_RIGHT

# 화면 진동(스크린 셰이크) 관련 변수
shake_dx = 0
shake_dy = 0

# 갑툭튀(표지판 점점 커짐) 관련 변수
stay_time_ms = 0
jumpscare_active = False
jumpscare_scale = 1.0
jumpscare_elapsed_ms = 0
current_jumpscare_image = jumpscare_img

# 트리거 영역
top_trigger = pygame.Rect(0, 0, WIDTH, TOP_TRIGGER_HEIGHT)
bottom_trigger = pygame.Rect(0, HEIGHT - BOTTOM_TRIGGER_HEIGHT, WIDTH, BOTTOM_TRIGGER_HEIGHT)

game_over = False
message = " "
sub_message = ""
show_debug = False  # D 키로 트리거 박스 보기

# =========================
# 히트박스 조절 함수
# =========================
def shrink_player_rect(rect):
    return rect.inflate(
        -rect.width * PLAYER_HITBOX_SCALE * 2,
        -rect.height * PLAYER_HITBOX_SCALE
    )


def shrink_bus_rect(rect):
    return rect.inflate(
        -rect.width * BUS_HITBOX_SCALE * 2,
        -rect.height * BUS_HITBOX_SCALE
    )


def shrink_prof_rect(rect):
    return rect.inflate(
        -rect.width * PROF_HITBOX_SCALE * 1.2,
        -rect.height * PROF_HITBOX_SCALE
    )


# =========================
# 섹션 전환(블랙아웃) 관련 변수
# =========================
in_transition = False
transition_time = 0
next_section = 0   # 전환이 끝나고 이동할 섹션 번호


def start_transition(target_section: int):
    """섹션 전환 연출 시작 (검은 화면)"""
    global in_transition, transition_time, next_section
    global stay_time_ms, jumpscare_active, jumpscare_scale

    in_transition = True
    transition_time = 0
    next_section = target_section

    # 섹션이 바뀔 거니까 갑툭튀 관련 상태도 리셋
    stay_time_ms = 0
    jumpscare_active = False
    jumpscare_scale = 1.0


def reset_game():
    """게임 전체를 초기 상태로 리셋"""
    global current_section, player_x, player_y, game_over, message, sub_message
    global prof_x, prof_y, prof_arrived
    global bus_state, bus_timer_ms
    global bus1, BUS_START_X, BUS_START_Y
    global stay_time_ms, jumpscare_active, jumpscare_scale

    current_section = 0
    player_x, player_y = PLAYER_START_X, PLAYER_START_Y
    game_over = False
    sub_message = ""

    # 교수님도 처음부터 다시
    prof_x = PROF_START_X
    prof_y = PROF_START_Y
    prof_arrived = False

    # 버스 상태 리셋
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
# 스토리 / 클리어 텍스트
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

CLEAR_LINES = [
    "그렇게 평소와 다른 오르막길의 여러가지 이상현상들을 찾아내",
    "무사히 교실로 도착한 민진이는 무사히 시험을 칠 수 있게되었다.",
    "얏호!",
    "",
    "[아무 키나 눌러서 메인 메뉴로 돌아가기]"
]


# =========================
# 그리기 함수들
# =========================
def draw_story():
    screen.blit(back_img, (0, 0))
    screen.blit(player_img, (WIDTH // 2, HEIGHT - 200))

    title = FONT.render("Story", True, (255, 255, 255))
    rect_t = title.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title, rect_t)

    start_y = 160
    line_gap = 40
    for i, line in enumerate(STORY_LINES):
        text_surf = SMALL_FONT.render(line, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, start_y + i * line_gap))
        screen.blit(text_surf, text_rect)


def draw_clear():
    screen.blit(back_img, (0, 0))
    screen.blit(player_img, (WIDTH // 2, HEIGHT - 200))

    title = FONT.render("Clear", True, (255, 255, 255))
    rect_t = title.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title, rect_t)

    start_y = 160
    line_gap = 40
    for i, line in enumerate(CLEAR_LINES):
        text_surf = SMALL_FONT.render(line, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, start_y + i * line_gap))
        screen.blit(text_surf, text_rect)


def draw_menu():
    screen.blit(menu_bg_img, (0, 0))

    start_rect = btn_start_img.get_rect(center=(BTN_START_X, BTN_START_Y))
    screen.blit(btn_start_img, start_rect)

    exit_rect = btn_exit_img.get_rect(center=(BTN_EXIT_X, BTN_EXIT_Y))
    screen.blit(btn_exit_img, exit_rect)

    return start_rect, exit_rect


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

    current_bus_img = bus_img
    if section_bus_look_anomaly[current_section]:
        current_bus_img = bus_look_img

    bus_rect_draw = current_bus_img.get_rect(center=(bus1.x + bus_offset_x + shake_dx,
                                                     bus1.y + bus_offset_y + shake_dy))
    screen.blit(current_bus_img, bus_rect_draw)

    # 3) 교수님
    if section_ghost_prof_anomaly[current_section]:
        prof_image = ghost_prof_img
    else:
        prof_image = prof_img

    rect_prof = prof_image.get_rect(center=(prof_x + shake_dx, prof_y + shake_dy))
    screen.blit(prof_image, rect_prof)

    # 4) 섹션 번호 표지판
    if 0 <= current_section < len(section_sign_imgs):
        if section_sign_anomaly[current_section]:
            sign_img = sign_anom_img
        else:
            sign_img = section_sign_imgs[current_section]
    else:
        sign_img = section_sign_imgs[-1]

    rect_sign = sign_img.get_rect(center=(SECTION_SIGN_X, SECTION_SIGN_Y))
    screen.blit(sign_img, rect_sign)

    # 5) 갑툭튀 연출
    if jumpscare_active:
        base_w, base_h = current_jumpscare_image.get_size()
        w = int(base_w * jumpscare_scale)
        h = int(base_h * jumpscare_scale)
        if w < 10: w = 10
        if h < 10: h = 10

        big_img = pygame.transform.smoothscale(current_jumpscare_image, (w, h))
        big_rect = big_img.get_rect(center=(WIDTH // 2 + shake_dx, HEIGHT // 2 + shake_dy))
        screen.blit(big_img, big_rect)


def draw_player():
    rect = player_img.get_rect(center=(player_x + shake_dx, player_y + shake_dy))
    screen.blit(player_img, rect)


def draw_ui():
    msg_surface = FONT.render(message, True, (255, 255, 255))
    screen.blit(msg_surface, (20, HEIGHT - 60))

    if sub_message:
        sub_surface = FONT.render(sub_message, True, (255, 255, 255))
        screen.blit(sub_surface, (20, HEIGHT - 30))

    real_has_anom = has_anomaly_in_section(current_section)
    real_text = f"실제 상태: {'이상 있음' if real_has_anom else '이상 없음'}"
    real_color = (255, 100, 100) if real_has_anom else (100, 255, 100)
    real_surface = SMALL_FONT.render(real_text, True, real_color)
    # 필요하면 화면에 띄우기
    # screen.blit(real_surface, (20, 45))

    if show_debug:
        dbg_surface = SMALL_FONT.render("DEBUG: 트리거 박스 표시 중 (D키로 토글)", True, (200, 200, 200))
        screen.blit(dbg_surface, (20, HEIGHT - 90))


def draw_debug():
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


# 처음엔 메뉴 BGM
play_bgm("menu")

# =========================
# 7. 메인 게임 루프
# =========================
running = True
while running:
    dt = clock.tick(FPS)  # 60 FPS

    # 상태에 따른 BGM 전환
    if current_state in (STATE_MENU, STATE_STORY, STATE_CLEAR):
        play_bgm("menu")
    elif current_state == STATE_GAME:
        play_bgm("game")
    else:
        play_bgm(None)

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
                    current_state = STATE_STORY
                elif exit_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

        elif current_state == STATE_STORY:
            if event.type == pygame.KEYDOWN:
                current_state = STATE_GAME
                reset_game()

        elif current_state == STATE_GAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                if event.key == pygame.K_d:
                    show_debug = not show_debug

        elif current_state == STATE_CLEAR:
            if event.type == pygame.KEYDOWN:
                game_over = False
                current_state = STATE_MENU

    # -------------------------
    # 상태별 처리
    # -------------------------
    if current_state == STATE_MENU:
        draw_menu()
        pygame.display.flip()
        continue

    if current_state == STATE_STORY:
        draw_story()
        pygame.display.flip()
        continue

    if current_state == STATE_CLEAR:
        draw_clear()
        pygame.display.flip()
        continue

    # 섹션 전환 중(블랙아웃)
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
        old_x, old_y = player_x, player_y

        if not jumpscare_active:
            # 방향키 반전 이상 여부에 따라
            if section_control_flip_anomaly[current_section]:
                if keys[pygame.K_UP]:
                    player_x -= PLAYER_SPEED    # ↑ = 왼쪽
                if keys[pygame.K_DOWN]:
                    player_x += PLAYER_SPEED    # ↓ = 오른쪽
                if keys[pygame.K_LEFT]:
                    player_y += PLAYER_SPEED    # ← = 아래
                if keys[pygame.K_RIGHT]:
                    player_y -= PLAYER_SPEED * 15 # → = 위 (원래 코드 유지)
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
            if player_x < ROAD_LEFT_LOCAL:
                player_x = ROAD_LEFT_LOCAL
            if player_x > ROAD_RIGHT_LOCAL:
                player_x = ROAD_RIGHT_LOCAL
            if player_y < 0:
                player_y = 0
            if player_y > HEIGHT:
                player_y = HEIGHT

        # 교수 이동
        if section_ghost_prof_anomaly[current_section]:
            dx = player_x - prof_x
            dy = player_y - prof_y
            dist = math.hypot(dx, dy)
            if dist > 1:
                prof_x += GHOST_SPEED * (dx / dist)
                prof_y += GHOST_SPEED * (dy / dist)
        else:
            if not prof_arrived:
                prof_y += prof_speed
                if prof_y >= prof_target_y:
                    prof_y = prof_target_y
                    prof_arrived = True

        # 표지판 이상 → 점프스케어 시작 타이머
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

        # 점프스케어 확대 & 3초 후 섹션 1로 귀환
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

        # 버스 이상현상
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

        # 히트박스 계산
        player_rect = player_img.get_rect(center=(player_x, player_y))
        player_hit_rect = shrink_player_rect(player_rect)

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

        bus_image = bus_look_img if section_bus_look_anomaly[current_section] else bus_img
        bus_rect = bus_image.get_rect(center=(bus1.x, bus1.y))
        bus_hit_rect = shrink_bus_rect(bus_rect)

        if player_hit_rect.colliderect(bus_hit_rect):
            if bus_state == "falling" and section_bus_anomaly[current_section]:
                init_section_anomalies()
                start_transition(0)
            else:
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
                    game_over = True
                    current_state = STATE_CLEAR
                else:
                    start_transition(next_sec)
            else:
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

pygame.quit()
sys.exit()
