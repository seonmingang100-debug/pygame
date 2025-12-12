import os
import pygame

from config import (
    WIDTH, HEIGHT,
    ASSETS_DIR, USE_PLACEHOLDER,
    NUM_SECTIONS,
    SCREAM_SFX_PATH,
)

# =========================
# 공용 이미지 로드 함수
# =========================
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


# =========================
# 에셋 일괄 로드
# =========================
def load_images():
    images = {}

    # 배경/기본 이미지
    images["bg"]    = load_image("bg.png",      size=(WIDTH, HEIGHT), fallback_color=(30, 30, 30))
    images["back"]  = load_image("back.png",    size=(WIDTH, HEIGHT), fallback_color=(30, 30, 30))
    images["player"] = load_image("player.png", size=(100, 100),      fallback_color=(255, 255, 0))
    images["prof"]   = load_image("propesr.png", size=(120, 120),     fallback_color=(255, 100, 100))
    images["bus"]    = load_image("bus.png",    size=(160, 160),      fallback_color=(255, 0, 0))

    # 이상 배경 / 이상 버스 / 귀신 교수 / 점프스케어
    images["bg_anom"]          = load_image("bg_anom.png",   size=(WIDTH, HEIGHT), fallback_color=(60, 0, 60))
    images["bus_look"]         = load_image("bus_look.png",  size=(160, 160),      fallback_color=(255, 0, 0))
    images["ghost_prof"]       = load_image("prof_ghost.png", size=(120, 120),     fallback_color=(150, 0, 150))
    images["ghost_jumpscare"]  = load_image("ghost_jumpscare.png",                 fallback_color=(255, 0, 0))

    # 버튼 / 메뉴 배경
    images["btn_start"] = load_image("btn_start.png", size=(300, 120), fallback_color=(0, 200, 0))
    images["btn_exit"]  = load_image("btn_exit.png",  size=(300, 120), fallback_color=(200, 0, 0))
    images["menu_bg"]   = load_image("menu_bg.png",   size=(WIDTH, HEIGHT), fallback_color=(20, 20, 20))

    # 섹션 번호 표지판들
    section_sign_imgs = []
    for i in range(1, NUM_SECTIONS + 1):
        fname = f"sign_section_{i}.png"
        img = load_image(fname, size=(180, 180), fallback_color=(200, 200, 200))
        section_sign_imgs.append(img)
    images["section_signs"] = section_sign_imgs

    # 이상 표지판 / 갑툭튀 표지판
    images["sign_anom"] = load_image("sign_section_anom.png", size=(180, 180), fallback_color=(255, 0, 255))
    images["jumpscare"] = load_image("sign_jumpscare.png",    fallback_color=(255, 0, 255))

    return images


def load_fonts():
    """
    폰트 로드
    """
    font = pygame.font.SysFont("malgungothic", 24)
    small_font = pygame.font.SysFont("malgungothic", 18)
    return {
        "main": font,
        "small": small_font,
    }


def load_sounds():
    """
    효과음 로드 (현재는 비명 SFX만)
    """
    sounds = {"scream": None}

    if os.path.exists(SCREAM_SFX_PATH):
        scream = pygame.mixer.Sound(SCREAM_SFX_PATH)
        scream.set_volume(0.8)
        sounds["scream"] = scream
    else:
        print(f"[WARN] 비명 효과음 파일을 찾을 수 없음: {SCREAM_SFX_PATH}")

    return sounds
