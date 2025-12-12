import random
from config import NUM_SECTIONS

# 섹션별 이상 여부 플래그 (한 번만 생성)
section_sign_anomaly         = [False] * NUM_SECTIONS   # 표지판 이상
section_bus_anomaly          = [False] * NUM_SECTIONS   # 버스 이상
section_bg_anomaly           = [False] * NUM_SECTIONS   # 배경 이상
section_bus_look_anomaly     = [False] * NUM_SECTIONS   # 버스 시선 반전
section_control_flip_anomaly = [False] * NUM_SECTIONS   # 방향키 반전
section_ghost_prof_anomaly   = [False] * NUM_SECTIONS   # 귀신 교수 이상


def init_section_anomalies():
    """
    섹션별 이상현상 설정
    - 0번 섹션: 항상 정상
    - 1~(NUM_SECTIONS-1) 섹션: 각 섹션당 아래 중 하나만 선택 (겹치지 않음)
        "none"        : 아무 이상 없음
        "sign"        : 표지판 이상
        "bus_move"    : 버스 흔들리고 떨어지는 이상(2번 현상)
        "bg"          : 배경 이상(3번 현상)
        "bus_look"    : 버스 시선 반전(4번 현상)
        "control_flip": 방향키 반전(5번 현상)
    - 9번 섹션(인덱스 8): 귀신 교수 고정
    """

    # ✅ 새 리스트를 만들지 말고, 기존 리스트를 "자리 그대로" 내용만 싹 갈아끼우기
    section_sign_anomaly[:]         = [False] * NUM_SECTIONS
    section_bus_anomaly[:]          = [False] * NUM_SECTIONS
    section_bg_anomaly[:]           = [False] * NUM_SECTIONS
    section_bus_look_anomaly[:]     = [False] * NUM_SECTIONS
    section_control_flip_anomaly[:] = [False] * NUM_SECTIONS
    section_ghost_prof_anomaly[:]   = [False] * NUM_SECTIONS

    # 0번 섹션은 항상 정상 (기본값이 False라 사실상 생략 가능하지만 의미를 살려둠)
    section_sign_anomaly[0]         = False
    section_bus_anomaly[0]          = False
    section_bg_anomaly[0]           = False
    section_bus_look_anomaly[0]     = False
    section_control_flip_anomaly[0] = False
    section_ghost_prof_anomaly[0]   = False

    # 1 ~ NUM_SECTIONS-1까지 랜덤 패턴 설정
    for i in range(1, NUM_SECTIONS):
        # 9번째 섹션(인덱스 8)은 귀신 교수 전용
        if i == 8:
            continue

        pattern = random.choice([
            "none",
            "sign",
            "bus_move",
            "bg",
            "bus_look",
            "control_flip"
        ])

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

    # 9번 섹션(인덱스 8)을 귀신 교수 섹션으로 고정
    if NUM_SECTIONS > 8:
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
