"""은행 이상형 월드컵 8강 — Streamlit 앱.

16개 은행 중 매 게임마다 무작위로 8곳이 뽑혀 8강 토너먼트를 치릅니다.

로컬 실행:
    streamlit run streamlit_bank_worldcup.py

이미지는 이 파일과 같은 위치의 images/ 폴더에 넣습니다.
파일명에 은행 이름(예: 신한.png, shinhan.jpg)이나 번호(예: 02.png)가
들어 있으면 자동으로 연결되고, 이미지가 없는 은행은 색상 카드로 대체됩니다.
"""

import io
import random
import re
from pathlib import Path

import streamlit as st
from PIL import Image


st.set_page_config(
    page_title="은행 이상형 월드컵",
    page_icon="🏦",
    layout="centered",
)

IMAGE_DIR = Path(__file__).parent / "images"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# 번호(no)는 images/ 폴더의 번호 파일명(01.png ~ 16.png)과 대응합니다.
# aliases 는 파일명에서 은행을 찾을 때 쓰는 키워드입니다.
BANKS = [
    {"no": 1, "name": "IBK기업은행", "color": "#0F4C9C", "aliases": ["기업", "ibk"]},
    {"no": 2, "name": "신한은행", "color": "#0046FF", "aliases": ["신한", "shinhan"]},
    {"no": 3, "name": "KB국민은행", "color": "#FFBC00", "aliases": ["국민", "kookmin", "kbstar"]},
    {"no": 4, "name": "우리은행", "color": "#0067AC", "aliases": ["우리", "woori"]},
    {"no": 5, "name": "NH농협은행", "color": "#00A651", "aliases": ["농협", "nonghyup", "nhbank"]},
    {"no": 6, "name": "하나은행", "color": "#008485", "aliases": ["하나", "hana"]},
    {"no": 7, "name": "제주은행", "color": "#00529B", "aliases": ["제주", "jeju"]},
    {"no": 8, "name": "케이뱅크", "color": "#1B1F5C", "aliases": ["케이", "kbank"]},
    {"no": 9, "name": "카카오뱅크", "color": "#FFE300", "aliases": ["카카오", "kakao"]},
    {"no": 10, "name": "토스뱅크", "color": "#0064FF", "aliases": ["토스", "toss"]},
    {"no": 11, "name": "Sh수협은행", "color": "#0072BC", "aliases": ["수협", "suhyup"]},
    {"no": 12, "name": "iM뱅크", "color": "#00B6AD", "aliases": ["아이엠", "im뱅크", "imbank", "대구", "daegu"]},
    {"no": 13, "name": "BNK부산은행", "color": "#D7191F", "aliases": ["부산", "busan"]},
    {"no": 14, "name": "BNK경남은행", "color": "#B5121B", "aliases": ["경남", "kyongnam", "gyeongnam"]},
    {"no": 15, "name": "광주은행", "color": "#1D4F9E", "aliases": ["광주", "gwangju", "kwangju"]},
    {"no": 16, "name": "전북은행", "color": "#16479D", "aliases": ["전북", "jeonbuk", "jbbank"]},
]

BRACKET_SIZE = 8  # 전체 16개 은행 중 한 게임에 출전하는 은행 수
ROUND_LABELS = {8: "8강", 4: "4강", 2: "결승"}

st.markdown(
    """
    <style>
    div[data-testid="stImage"] img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(31, 41, 55, 0.14);
    }
    .bank-card {
        aspect-ratio: 1 / 1;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 12px;
        color: #ffffff;
        font-weight: 800;
        font-size: clamp(1rem, 4vw, 1.8rem);
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
        box-shadow: 0 6px 18px rgba(31, 41, 55, 0.14);
    }
    .bank-card.small { font-size: 0.85rem; border-radius: 12px; }
    .vs {
        text-align: center;
        font-size: 2rem;
        font-weight: 900;
        color: #ef4444;
        margin-top: 120%;
    }
    .round-title { text-align: center; margin-bottom: 0; }
    .match-count { text-align: center; color: #6b7280; margin-top: 0; }
    div[data-testid="stButton"] button {
        border-radius: 14px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _normalize(text: str) -> str:
    return re.sub(r"[\s_\-()]+", "", text.lower())


def find_image(bank: dict) -> Path | None:
    """images/ 폴더에서 은행에 해당하는 이미지 파일을 찾습니다."""
    if not IMAGE_DIR.is_dir():
        return None
    files = sorted(p for p in IMAGE_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTS)

    # 1순위: 파일명에 은행 키워드가 포함된 경우
    for path in files:
        stem = _normalize(path.stem)
        if any(_normalize(alias) in stem for alias in bank["aliases"]):
            return path

    # 2순위: 파일명이 번호로 시작하는 경우 (1.png, 01_xxx.png 등)
    for path in files:
        leading = re.match(r"\d+", path.stem.strip())
        if leading and int(leading.group()) == bank["no"]:
            return path
    return None


@st.cache_data(show_spinner=False)
def load_image(path: str, size: int, mtime: float) -> bytes:
    """원본(장당 약 2MB)을 화면 크기에 맞게 줄여 전송량을 낮춥니다."""
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


def show_bank(bank: dict, small: bool = False) -> None:
    """은행 이미지를 표시하고, 이미지가 없으면 색상 카드로 대체합니다."""
    image = find_image(bank)
    if image:
        size = 320 if small else 800
        st.image(load_image(str(image), size, image.stat().st_mtime), width="stretch")
    else:
        size = " small" if small else ""
        st.markdown(
            f'<div class="bank-card{size}" style="background: linear-gradient(145deg, '
            f'{bank["color"]}, #111827);">{bank["name"]}</div>',
            unsafe_allow_html=True,
        )


def start_game() -> None:
    players = random.sample(range(len(BANKS)), BRACKET_SIZE)
    st.session_state.players = players  # 현재 라운드 참가자 (BANKS 인덱스)
    st.session_state.winners = []  # 현재 라운드 승자
    st.session_state.match = 0  # 현재 라운드에서 몇 번째 경기인지
    st.session_state.history = []  # (라운드, 승자, 패자) 기록
    st.session_state.champion = None
    st.session_state.started = True


def reset_game() -> None:
    st.session_state.started = False


def pick(winner: int, loser: int) -> None:
    ss = st.session_state
    ss.history.append((ROUND_LABELS[len(ss.players)], winner, loser))
    ss.winners.append(winner)
    ss.match += 1

    # 라운드의 모든 경기가 끝나면 다음 라운드로 넘어갑니다.
    if ss.match * 2 >= len(ss.players):
        if len(ss.winners) == 1:
            ss.champion = ss.winners[0]
        else:
            ss.players = ss.winners
            ss.winners = []
            ss.match = 0


def render_intro() -> None:
    st.title("🏦 은행 이상형 월드컵")
    st.write("16개 은행 중 무작위로 뽑힌 8곳이 맞붙습니다. 두 은행 중 더 끌리는 쪽을 골라 주세요.")
    st.button("8강 시작하기", type="primary", width="stretch", on_click=start_game)

    st.divider()
    st.subheader("후보 은행 16곳")
    for row in range(0, len(BANKS), 4):
        for col, bank in zip(st.columns(4), BANKS[row : row + 4]):
            with col:
                show_bank(bank, small=True)
                st.caption(bank["name"])

    missing = [f'{b["no"]:02d} {b["name"]}' for b in BANKS if find_image(b) is None]
    if missing:
        with st.expander(f"이미지가 연결되지 않은 은행 {len(missing)}곳"):
            st.write(
                "`images/` 폴더에 은행 이름이나 번호가 들어간 파일명으로 저장하면 "
                "자동으로 연결됩니다. (예: `신한.png`, `02.png`)"
            )
            st.write(" · ".join(missing))


def render_match() -> None:
    ss = st.session_state
    total_matches = len(ss.players) // 2
    label = ROUND_LABELS[len(ss.players)]
    left = ss.players[ss.match * 2]
    right = ss.players[ss.match * 2 + 1]

    st.markdown(f'<h2 class="round-title">{label}</h2>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="match-count">{ss.match + 1} / {total_matches} 경기</p>',
        unsafe_allow_html=True,
    )
    st.progress(len(ss.history) / (BRACKET_SIZE - 1))

    col_left, col_vs, col_right = st.columns([5, 1, 5])
    with col_left:
        show_bank(BANKS[left])
        st.button(
            BANKS[left]["name"],
            key="pick_left",
            type="primary",
            width="stretch",
            on_click=pick,
            args=(left, right),
        )
    with col_vs:
        st.markdown('<div class="vs">VS</div>', unsafe_allow_html=True)
    with col_right:
        show_bank(BANKS[right])
        st.button(
            BANKS[right]["name"],
            key="pick_right",
            type="primary",
            width="stretch",
            on_click=pick,
            args=(right, left),
        )

    st.divider()
    st.button("처음으로", on_click=reset_game)


def render_result() -> None:
    ss = st.session_state
    champion = BANKS[ss.champion]
    runner_up = BANKS[ss.history[-1][2]]
    semifinalists = [BANKS[loser] for label, _, loser in ss.history if label == "4강"]

    st.balloons()
    st.title("🏆 나의 최애 은행")
    _, center, _ = st.columns([1, 3, 1])
    with center:
        show_bank(champion)
        st.markdown(
            f'<h2 style="text-align:center;">{champion["name"]}</h2>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("최종 순위")
    for col, (rank, bank) in zip(
        st.columns(3),
        [("🥈 준우승", runner_up)] + [("🥉 4강", b) for b in semifinalists],
    ):
        with col:
            show_bank(bank, small=True)
            st.caption(f'{rank} · {bank["name"]}')

    with st.expander("전체 대진 기록"):
        for label in ROUND_LABELS.values():
            st.markdown(f"**{label}**")
            for round_label, winner, loser in ss.history:
                if round_label == label:
                    st.write(f'✅ {BANKS[winner]["name"]}  vs  {BANKS[loser]["name"]}')

    st.button("다시 하기", type="primary", width="stretch", on_click=start_game)


if not st.session_state.get("started"):
    render_intro()
elif st.session_state.champion is None:
    render_match()
else:
    render_result()
