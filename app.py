import html
import os
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# The database lives as a file right next to app.py (or online in Turso, see get_conn)
DB_PATH = Path(__file__).parent / "habits.db"
TIMEZONE = "Europe/Berlin"


def now_local():
    """Current time in your time zone (cloud servers run on UTC)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    except Exception:
        return datetime.now()


def today_local():
    return now_local().date()
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Categories in the order they appear (name: icon)
CATEGORIES = {
    "Morning routine": "☀️",
    "After work routine": "🏡",
    "Night routine": "🌙",
    "Food stuff": "🍓",
    "Mental health": "🧠",
    "Body": "💪",
    "Other": "✨",
}
RULE_MIN_PER_CATEGORY = 2
CATEGORY_STYLE = {  # short name, ring color
    "Morning routine": ("Morning", "#f9a8d4"),
    "After work routine": ("After work", "#fdba74"),
    "Night routine": ("Night", "#a855f7"),
    "Food stuff": ("Food", "#ec4899"),
    "Mental health": ("Mind", "#c4b5fd"),
    "Body": ("Body", "#db2777"),
    "Other": ("Other", "#93c5fd"),
}

PALETTE = {
    "🩷 Rose": "#f9a8d4",
    "💗 Pink": "#ec4899",
    "🌺 Raspberry": "#db2777",
    "💜 Purple": "#a855f7",
    "🪻 Lavender": "#c4b5fd",
    "🔮 Lilac": "#d8b4fe",
    "🍑 Peach": "#fdba74",
    "🌿 Mint": "#6ee7b7",
    "🩵 Sky blue": "#93c5fd",
    "🍋 Lemon": "#fde68a",
}
EMOJIS = ["🌸", "💖", "🎀", "✨", "🦋", "🧘‍♀️", "🏃‍♀️", "🚶‍♀️", "💪", "💧", "📚", "📓", "📝",
          "📋", "🙏", "🛏️", "🥗", "🍳", "🍓", "💤", "🌙", "☕", "💅", "🧴", "🦷", "💊", "🎨",
          "🎶", "🪴", "📵"]

# Funny meme cards depending on today's progress
MEMES = {
    0: [("😴", "Me at 8 am", "The habits: 👁️👄👁️"),
        ("☀️", "Rise and shine, bestie", "The habits won't check themselves")],
    1: [("🐣", "Baby steps", "Are still steps, bestie"),
        ("☕", "One down", "Slay loading... please wait")],
    2: [("💅", "Halfway there", "And looking good doing it"),
        ("🚀", "Look at you go", "Main character energy")],
    3: [("👀", "Almost there", "Don't you dare stop now"),
        ("🔥", "She's on fire", "Just a few left, queen")],
    4: [("💃", "Go girl!", "That girl era: unlocked 👑"),
        ("👑", "All done", "Slay. Just slay.")],
}

st.set_page_config(page_title="Habit Tracker", page_icon="🌸", layout="wide")


# ============================================================
# Design (CSS)
# ============================================================
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Patrick+Hand&family=Quicksand:wght@500;600;700&display=swap');

html, body, .stMarkdown, .stButton button, input, label, p {
    font-family: 'Quicksand', sans-serif !important;
}
h1, h2, h3 { color: #c2185b !important; font-family: 'Quicksand', sans-serif !important; font-weight: 700 !important; }

[data-testid="stSidebar"] { background: linear-gradient(180deg, #fde7f3 0%, #efe3ff 100%); }

.habit-pill {
    padding: 9px 14px; border-radius: 16px; font-weight: 700; color: #5b2a4e;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.day-head {
    text-align: center; color: #9d4b83; font-size: 0.85rem; line-height: 1.25;
    padding: 5px 0; border-radius: 14px;
}
.day-head b { font-size: 1.05rem; }
.day-head.today { background: #ec4899; color: white; box-shadow: 0 3px 10px rgba(236,72,153,.35); }
.day-head.weekend { background: #f3e8ff; }
.streak { text-align: center; font-weight: 700; color: #9d4b83; line-height: 1.2; }
.streak small { font-weight: 600; color: #b77aa6; }
.week-label { text-align: center; font-size: 1.15rem; font-weight: 700; color: #9d4b83; padding-top: 6px; }

/* The round circles to check off */
div[class*="st-key-on-"], div[class*="st-key-off-"] { align-items: center; }
div[class*="st-key-on-"] button, div[class*="st-key-off-"] button {
    border-radius: 50% !important; width: 42px; height: 42px; min-height: 42px;
    padding: 0 !important; font-size: 1.15rem; transition: transform .15s ease;
}
div[class*="st-key-on-"] button:hover, div[class*="st-key-off-"] button:hover { transform: scale(1.15); }
div[class*="st-key-on-"] button p, div[class*="st-key-off-"] button p { font-size: 1.3rem; font-weight: 700; }
div[class*="st-key-off-"] button:disabled { opacity: .3; }

/* Rest days (habit not planned that day) */
div[class*="st-key-rest-"] button { background: transparent !important; border: 2px dashed #e9d5ff !important;
                                    color: #d8b4fe !important; }
.days-tag { display: inline-block; margin-left: 8px; font-size: .68rem; font-weight: 700; color: #9d4b83;
            background: #ffffffaa; border-radius: 99px; padding: 1px 7px; vertical-align: middle; }
.p.rest { opacity: .3; border-style: dashed; transform: scale(.7); animation: none; }

/* Sorting rows (Manage page) */
.sort-mark { display: none; }
@media (max-width: 640px) {
    div[data-testid="stHorizontalBlock"]:has(.sort-mark) { flex-wrap: nowrap !important; gap: .3rem !important; }
    div[data-testid="stHorizontalBlock"]:has(.sort-mark) > div { min-width: 0 !important; flex: 0 0 auto !important; width: auto !important; }
    div[data-testid="stHorizontalBlock"]:has(.sort-mark) > div:first-child { flex: 1 1 auto !important; }
}

/* Category headings in the week grid */
.cat-head { margin: 16px 0 2px; font-weight: 700; color: #c2185b; font-size: 1.05rem;
            display: flex; align-items: center; gap: 10px; }
.cat-head small { color: #9d4b83; font-weight: 700; font-size: .75rem; background: #fbe4f0;
                  border-radius: 99px; padding: 2px 10px; }
.cat-head small.ok { background: #ec4899; color: #fff; }

/* White boxes (rules, water) */
.box { background: #fff; border-radius: 22px; padding: 14px 18px; color: #5b2a4e;
       box-shadow: 0 6px 22px rgba(236,72,153,.13); }
.box-title { font-weight: 700; color: #c2185b; font-size: 1.05rem; margin-bottom: 4px; }
.rule { font-weight: 600; font-size: .9rem; margin: 10px 0 6px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { background: #fbe4f0; color: #9d4b83; border-radius: 99px; padding: 3px 10px;
        font-weight: 700; font-size: .8rem; }
.chip.ok { background: #ec4899; color: #fff; }
.risk { background: #fff1f6; border-left: 4px solid #ec4899; border-radius: 12px;
        padding: 7px 10px; font-size: .85rem; font-weight: 600; }
.safe { background: #f3e8ff; border-radius: 12px; padding: 7px 10px; font-size: .85rem; font-weight: 600; }

/* Water glass */
.water { display: flex; align-items: center; gap: 18px; }
.glass { position: relative; width: 92px; height: 128px; flex-shrink: 0; overflow: hidden;
         border-radius: 6px 6px 30px 30px; background: rgba(255,255,255,.8);
         border: 4px solid #e9d5ff; box-shadow: 0 6px 18px rgba(147,197,253,.35), inset 0 0 0 3px #fff; }
.liquid { position: absolute; left: 0; right: 0; bottom: 0;
          background: linear-gradient(180deg, #a5c8ff, #8b9cf7); }
.wave { position: absolute; left: 0; width: 200%; height: 14px; top: -13px;
        animation: waveMove 2.6s linear infinite; }
.wave path { fill: #a5c8ff; }
.wave.w2 { top: -10px; opacity: .6; animation-duration: 4.2s; animation-direction: reverse; }
.wave.w2 path { fill: #c4b5fd; }
.bubble { position: absolute; bottom: 0; width: 7px; height: 7px; border-radius: 50%;
          background: rgba(255,255,255,.8); animation: rise 3s ease-in infinite; }
.bubble.b1 { left: 22%; } .bubble.b2 { left: 55%; width: 5px; height: 5px; animation-delay: 1s; }
.bubble.b3 { left: 74%; animation-delay: 2s; }
.water-info b { font-size: 1.7rem; color: #5b2a4e; display: block; line-height: 1.1; }
.water-info small { color: #b77aa6; font-weight: 600; }
.water-info .hint { font-size: .82rem; color: #9d4b83; margin-top: 6px; font-weight: 600; }
@keyframes waveMove { from { transform: translateX(0) } to { transform: translateX(-50%) } }
@keyframes rise { 0% { bottom: 0; opacity: 0 } 20% { opacity: 1 } 100% { bottom: 92%; opacity: 0 } }
.wbtn-mark { display: none; }
div[data-testid="stElementContainer"]:has(.wbtn-mark), div.element-container:has(.wbtn-mark) { display: none; }
div[data-testid="stHorizontalBlock"]:has(.wbtn-mark) button { width: 100%; border-radius: 99px !important; }
div[data-testid="stHorizontalBlock"]:has(> div:nth-child(3)):has(.wbtn-mark) .stButton,
div[data-testid="stHorizontalBlock"]:has(> div:nth-child(3)):has(.wbtn-mark) [data-testid="stButton"] { width: 100%; }

/* Affirmation card */
.aff { position: relative; overflow: hidden; min-height: 196px;
       background: linear-gradient(135deg, #ffffff 0%, #fdf0f7 55%, #f3e8ff 100%); }
.aff::after { content: "❝"; position: absolute; right: 14px; bottom: -28px; font-size: 7rem;
              color: #f9a8d4; opacity: .35; font-family: Georgia, serif; }
.aff-kind { display: inline-block; background: #fbe4f0; color: #c2185b; font-weight: 700;
            font-size: .72rem; border-radius: 99px; padding: 2px 10px; margin: 2px 0 8px; }
.aff-text { font-size: 1.3rem; font-weight: 700; color: #5b2a4e; line-height: 1.35;
            animation: popIn .8s ease both; position: relative; z-index: 1; }
.aff-who { margin-top: 8px; color: #b77aa6; font-weight: 600; font-style: italic; position: relative; z-index: 1; }

/* Affirmation in the sidebar */
[data-testid="stSidebar"] .box { padding: 12px 14px; margin-top: 14px; }
[data-testid="stSidebar"] .aff { min-height: 0; padding-bottom: 22px; }
[data-testid="stSidebar"] .aff-text { font-size: 1.05rem; }
[data-testid="stSidebar"] .aff::after { font-size: 5rem; bottom: -22px; }

/* Reminders + golden rules */
.rem-item { display: flex; gap: 12px; align-items: flex-start; padding: 9px 0;
            border-top: 1px dashed #f5d0e6; animation: popIn .5s ease both; }
.rem .box-title + .rem-item { border-top: none; }
.rem-icon { width: 34px; height: 34px; flex-shrink: 0; border-radius: 50%; background: #fdf2f8;
            display: flex; align-items: center; justify-content: center; font-size: 1.05rem; }
.rem-title { font-weight: 700; font-size: .92rem; color: #5b2a4e; }
.rem-sub { font-size: .8rem; color: #9d4b83; font-weight: 600; }
.rpill { display: inline-block; padding: 3px 10px; border-radius: 99px; font-weight: 700;
         font-size: .78rem; color: #5b2a4e; margin: 5px 5px 0 0; }
.rem-empty { text-align: center; padding: 18px 0 8px; font-weight: 700; color: #9d4b83; }
.grule { display: flex; gap: 8px; align-items: flex-start; font-weight: 600; font-size: .85rem;
         margin-top: 8px; color: #5b2a4e; }

/* Reminder pinboard with sticky notes */
.box.rem { background-image: radial-gradient(#f9a8d455 1.2px, transparent 1.4px) !important;
           background-size: 16px 16px !important; }
.rem-top { display: flex !important; align-items: center; gap: 8px; }
.rem-top .rem-count { margin-left: auto; }
.rem-count { background: #ec4899; color: #fff; font-weight: 700; font-size: .72rem; border-radius: 99px;
             padding: 2px 10px; }
.rem-count.calm { background: #c4b5fd; }
.bell { display: inline-block; transform-origin: 50% 0; }
.bell.ringing { animation: bellring 2.8s ease-in-out infinite; }
.board { display: flex; flex-wrap: wrap; gap: 16px 14px; margin-top: 12px; padding: 4px 2px 6px; }
.note { position: relative; flex: 1 1 200px; padding: 18px 14px 12px; border-radius: 4px 4px 14px 4px;
        color: #5b2a4e; box-shadow: 0 6px 14px rgba(157,23,77,.16), 0 1px 0 rgba(0,0,0,.04);
        animation: noteIn .55s cubic-bezier(.34,1.56,.64,1) both; transition: transform .2s; }
.note::before { content: ""; position: absolute; top: -9px; left: 50%; width: 64px; height: 18px;
                transform: translateX(-50%) rotate(-3deg); border-radius: 2px;
                background: repeating-linear-gradient(45deg, #ffffffb0 0 6px, #fbcfe8b0 6px 12px);
                box-shadow: 0 1px 2px rgba(0,0,0,.08); }
.note.n0 { background: #ffe4ef; transform: rotate(-1.6deg); }
.note.n1 { background: #efe3ff; transform: rotate(1.3deg); }
.note.n2 { background: #ffedd5; transform: rotate(-0.8deg); }
.note.n3 { background: #dcfce7; transform: rotate(1.8deg); }
.note.n4 { background: #e0f2fe; transform: rotate(-1.2deg); }
.note:hover { transform: rotate(0) translateY(-4px) scale(1.02); z-index: 2; }
.note-head { font-family: 'Patrick Hand', 'Comic Sans MS', cursive; font-size: 1.25rem; line-height: 1.15;
             display: flex; align-items: center; gap: 8px; color: #5b2a4e; }
.note-icon { font-size: 1.3rem; }
.note-sub { font-size: .8rem; font-weight: 600; color: #9d4b83; margin-top: 4px; }
.note .rpill { background: #ffffffb3 !important; color: #5b2a4e !important; }
@keyframes bellring { 0%, 70%, 100% { transform: rotate(0) } 74% { transform: rotate(16deg) }
                  78% { transform: rotate(-14deg) } 82% { transform: rotate(10deg) }
                  86% { transform: rotate(-8deg) } 90% { transform: rotate(4deg) } }
@keyframes noteIn { from { opacity: 0; transform: translateY(-14px) rotate(-6deg) scale(.9) } }

/* Today's garden (category success) */
.garden { margin-top: 16px; background: #fff; border-radius: 22px; padding: 14px 18px 16px;
          box-shadow: 0 6px 22px rgba(236,72,153,.13); color: #5b2a4e; }
.garden.perfect { background: linear-gradient(120deg, #fff 0%, #fdf0f7 50%, #f3e8ff 100%);
                  box-shadow: 0 0 0 3px #f9a8d4, 0 8px 28px rgba(236,72,153,.3); }
.garden-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 4px 12px; }
.garden-sub { color: #9d4b83; font-weight: 700; font-size: .9rem; }
.beds { display: flex; flex-wrap: wrap; justify-content: space-around; gap: 14px 10px; margin-top: 10px; }
.bloom { position: relative; width: 104px; text-align: center; }
.bloom-ring { position: relative; width: 84px; height: 84px; margin: 0 auto; }
.bloom-ring svg { width: 84px; height: 84px; }
.bring-bg { fill: #fdf2f8; stroke: #fbe4f0; stroke-width: 7; }
.bring-fg { fill: none; stroke-width: 7; stroke-linecap: round; --full: 188.5; animation: ringIn 1.2s ease-out both; }
.bloom-icon { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
              font-size: 1.9rem; }
.bloom-stage { position: absolute; right: -2px; bottom: -2px; width: 30px; height: 30px; border-radius: 50%;
               background: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.05rem;
               box-shadow: 0 2px 8px rgba(194,24,91,.2); }
.bloom-name { margin-top: 6px; font-weight: 700; font-size: .85rem; color: #5b2a4e; }
.bloom-count { font-size: .78rem; font-weight: 700; color: #b77aa6; }
.bloom.done .bloom-count { color: #ec4899; }
.bloom.done .bloom-ring { animation: bloomPop .8s cubic-bezier(.34,1.56,.64,1) both; border-radius: 50%;
                          box-shadow: 0 0 18px rgba(236,72,153,.45); }
.bloom.done .bloom-stage { animation: bob2 1.8s ease-in-out infinite; }
.spark { position: absolute; font-size: .9rem; animation: twinkle 1.6s ease-in-out infinite; }
.spark.s1 { top: -6px; left: 8px; } .spark.s2 { top: 10px; right: 0; animation-delay: .5s; }
.spark.s3 { bottom: 34px; left: 0; animation-delay: 1s; }
.perfect-msg { margin-top: 12px; text-align: center; font-weight: 700; color: #c2185b;
               animation: popIn .6s ease both; }
@keyframes bloomPop { 0% { transform: scale(.7) } 60% { transform: scale(1.12) } 100% { transform: scale(1) } }
@keyframes bob2 { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-4px) } }
@keyframes twinkle { 0%,100% { opacity: 0; transform: scale(.5) } 50% { opacity: 1; transform: scale(1.1) } }
@keyframes ringIn { from { stroke-dashoffset: var(--full) } }
@media (max-width: 640px) {
    .bloom { width: 30%; }
    .bloom-ring, .bloom-ring svg { width: 70px; height: 70px; }
    .bloom-icon { font-size: 1.55rem; }
}

/* Meme card */
.meme { margin: 16px 0 8px; border-radius: 22px; padding: 14px 20px; color: #fff;
        background: linear-gradient(120deg, #ff9ac8, #c084fc); display: flex; align-items: center; gap: 18px;
        box-shadow: 0 8px 24px rgba(236,72,153,.3); animation: popIn .6s cubic-bezier(.34,1.56,.64,1) both; }
.meme-emoji { font-size: 3.2rem; display: inline-block; animation: wiggle 1.4s ease-in-out infinite; }
.meme-top, .meme-bottom { font-family: 'Anton', Impact, 'Arial Black', sans-serif; text-transform: uppercase;
        letter-spacing: 1px; line-height: 1.15;
        text-shadow: 2px 2px 0 #9d174d, -1px -1px 0 #9d174d, 1px -1px 0 #9d174d, -1px 1px 0 #9d174d; }
.meme-top { font-size: 1.7rem; }
.meme-bottom { font-size: 1.05rem; }
@keyframes wiggle { 0%, 100% { transform: rotate(-8deg) scale(1) } 50% { transform: rotate(8deg) scale(1.1) } }
@keyframes popIn { from { opacity: 0; transform: translateY(14px) scale(.97) } }
</style>
"""

# Week page only: round circles in the grid + phone layout
GRID_CSS = """
<style>
div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) .stButton { display: flex; justify-content: center; }
div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) .stButton button,
div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) [data-testid="stPopover"] button {
    border-radius: 50% !important; width: 42px; height: 42px; min-height: 42px; padding: 0 !important;
}

@media (max-width: 640px) {
    .block-container, [data-testid="stMainBlockContainer"] { padding: 1.2rem 0.6rem 3rem !important; }
    h1 { font-size: 1.7rem !important; }

    /* Navigation (4 columns) and water buttons stay in one row */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)):not(:has(> div:nth-child(5))),
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(3)):has(.wbtn-mark) {
        flex-wrap: nowrap !important; gap: 0.3rem !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)):not(:has(> div:nth-child(5))) > div,
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(3)):has(.wbtn-mark) > div {
        min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }

    /* Water box and rules box: on top of each other */
    div[data-testid="stHorizontalBlock"]:has(.wbtn-mark):not(:has(> div:nth-child(3))) {
        flex-direction: column !important; gap: 1rem !important; }
    div[data-testid="stHorizontalBlock"]:has(.wbtn-mark):not(:has(> div:nth-child(3))) > div {
        width: 100% !important; flex: 1 1 auto !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)):not(:has(> div:nth-child(5))) button {
        padding: 0.3rem 0.55rem !important; white-space: nowrap; font-size: 0.85rem;
    }

    /* Grid: name on top across the full width, below it 7 circles + streak */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) {
        flex-wrap: wrap !important; gap: 0.3rem !important; row-gap: 0.4rem !important; margin-bottom: 0.7rem;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) > div {
        flex: 1 1 0 !important; width: auto !important; min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) > div:first-child { flex: 0 0 100% !important; }
    div[data-testid="stHorizontalBlock"] > div:has(.grid-label) { display: none !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) .stButton button,
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) [data-testid="stPopover"] button {
        width: 34px; height: 34px; min-height: 34px;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(9)) button p { font-size: 1rem !important; }

    .habit-pill { padding: 6px 12px; font-size: 0.95rem; border-left-width: 5px !important; margin-bottom: 1.1rem; }
    .day-head { font-size: 0.68rem; padding: 3px 0; border-radius: 10px; }
    .day-head b { font-size: 0.9rem; }
    .streak { font-size: 0.78rem; }
    .streak small { font-size: 0.7rem; }
    .week-label { font-size: 0.9rem; padding-top: 4px; }
    .meme-top { font-size: 1.3rem; } .meme-bottom { font-size: .9rem; } .meme-emoji { font-size: 2.6rem; }
}
</style>
"""

# Vertical "Today" bar on the right + overview cards
FUN_CSS = """
<style>
.tbar { position: fixed; right: 26px; top: 52%; transform: translateY(-50%); z-index: 999;
        display: flex; flex-direction: column; align-items: center; gap: 10px; }
.tbar-label { font-weight: 700; color: #c2185b; font-size: .85rem; }
.tbar-track { width: 34px; height: 56vh; background: #fbe4f0; border-radius: 99px; position: relative;
              border: 3px solid #fff;
              box-shadow: inset 0 2px 6px rgba(194,24,91,.18), 0 6px 18px rgba(236,72,153,.25); }
.tbar-fill { position: absolute; bottom: 0; left: 0; right: 0; border-radius: 99px;
             background: linear-gradient(0deg, #ec4899, #f472b6 55%, #c084fc); }
.tbar-fill.full { box-shadow: 0 0 18px rgba(236,72,153,.7); }
.tbar-heart { position: absolute; top: -16px; left: 50%; font-size: 1.45rem;
              animation: bob 1.6s ease-in-out infinite; filter: drop-shadow(0 2px 3px rgba(194,24,91,.4)); }
.tbar-count { font-weight: 700; color: #9d4b83; font-size: .9rem; }
@keyframes bob { 0%,100% { transform: translate(-50%, 0) } 50% { transform: translate(-50%, -6px) } }
@media (max-width: 640px) {
    .tbar { right: 6px; gap: 6px; }
    .tbar-label { display: none; }
    .tbar-track { width: 16px; height: 42vh; border-width: 2px; }
    .tbar-heart { font-size: 1.05rem; top: -12px; }
    .tbar-count { font-size: .7rem; }
}

.summary { background: linear-gradient(120deg, #fde7f3, #efe3ff); border-radius: 22px;
           padding: 16px 20px; color: #5b2a4e; font-weight: 600; margin: 6px 0 8px;
           display: flex; flex-wrap: wrap; gap: 8px 28px; }
.summary b { color: #c2185b; font-size: 1.15rem; }
.sec { font-weight: 700; color: #c2185b; font-size: 1.3rem; margin: 22px 0 10px; }
.hgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 18px; }
.hcard { background: #fff; border-radius: 24px; padding: 16px 18px 18px;
         box-shadow: 0 6px 22px rgba(236,72,153,.13); border-top: 6px solid var(--c);
         animation: popIn .55s ease both; }
.hhead { display: flex; align-items: center; gap: 12px; font-weight: 700; font-size: 1.15rem; color: #5b2a4e; }
.hemoji { width: 46px; height: 46px; border-radius: 50%; display: flex; align-items: center;
          justify-content: center; font-size: 1.5rem; background: var(--cl); flex-shrink: 0; }
.hbody { display: flex; align-items: center; gap: 16px; margin: 12px 0 14px; }
.ring { width: 88px; height: 88px; flex-shrink: 0; }
.ring-bg { fill: none; stroke: #fbe4f0; stroke-width: 9; }
.ring-fg { fill: none; stroke-width: 9; stroke-linecap: round; --full: 226.2; animation: ringIn 1.3s ease-out both; }
.ring-txt { font: 700 18px 'Quicksand', sans-serif; fill: #5b2a4e; }
.hstats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; flex: 1; }
.hstat b { display: block; font-size: 1.2rem; color: #5b2a4e; }
.hstat small { color: #b77aa6; font-size: .72rem; font-weight: 600; }
.pearls { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.pearls.s26 { --s: 26px; } .pearls.s17 { --s: 17px; } .pearls.s11 { --s: 11px; }
.p { width: var(--s); height: var(--s); border-radius: 50%; border: 2px solid var(--c);
     background: #fff; opacity: .5; display: inline-flex; align-items: center; justify-content: center;
     font-size: calc(var(--s) * .55); line-height: 1; color: var(--t); box-sizing: border-box;
     animation: pearlIn .45s cubic-bezier(.34,1.56,.64,1) both; transition: transform .15s; }
.p.on { background: var(--c); opacity: 1; }
.p.part { background: linear-gradient(0deg, var(--c) 50%, #fff 50%); opacity: .85; }
.p.today { box-shadow: 0 0 0 2px #fff, 0 0 0 4px var(--c); opacity: 1; }
.p:hover { transform: scale(1.35); }
.mlabel { font-size: .72rem; font-weight: 700; color: #b77aa6; padding: 0 2px 0 6px; }
.legend { --c: #ec4899; --t: #fff; --s: 12px; font-size: .75rem; color: #b77aa6; margin-top: 14px;
          display: flex; gap: 14px; align-items: center; }
.legend .p { animation: none; opacity: 1; }
.rank { background: #fff; border-radius: 24px; padding: 18px 20px; margin-top: 22px;
        box-shadow: 0 6px 22px rgba(236,72,153,.13); }
.rrow { display: flex; align-items: center; gap: 12px; margin: 12px 0; }
.rname { width: 200px; font-weight: 700; color: #5b2a4e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rtrack { flex: 1; height: 24px; background: #fbe4f0; border-radius: 99px; overflow: hidden; }
.rfill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--cl2), var(--c));
         animation: grow 1.3s cubic-bezier(.22,1,.36,1) both; }
.rpct { width: 50px; text-align: right; font-weight: 700; color: #9d4b83; }
@keyframes ringIn { from { stroke-dashoffset: var(--full) } }
@keyframes pearlIn { from { transform: scale(0) } }
@keyframes grow { from { width: 0 } }
@media (max-width: 640px) {
    .hgrid { grid-template-columns: 1fr; }
    .rname { width: 120px; font-size: .9rem; }
    .ring { width: 74px; height: 74px; }
}
</style>
"""


# Dark mode: deep plum background, pink and lilac accents
DARK_CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main { background: #1c1027 !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div { background: linear-gradient(180deg, #2b1438 0%, #1f1230 100%) !important; }
.stApp p, .stApp label, .stApp li, .stApp span, .stMarkdown, .stCaption, small { color: #f8e1f4; }
h1, h2, h3 { color: #f9a8d4 !important; }
[data-testid="stCaptionContainer"], .stCaption p { color: #c9a3d9 !important; }

.box, .hcard, .garden, .rank { background: #2a1a3a !important; color: #f8e1f4 !important;
                                box-shadow: 0 6px 22px rgba(0,0,0,.35) !important; }
.aff { background: linear-gradient(135deg, #2a1a3a 0%, #35204a 100%) !important; }
.aff::after { color: #f472b6 !important; opacity: .25 !important; }
.garden.perfect { box-shadow: 0 0 0 3px #f472b6, 0 8px 28px rgba(236,72,153,.35) !important; }
.summary { background: linear-gradient(120deg, #3a1d45, #2b1e4a) !important; color: #f8e1f4 !important; }
.summary b, .box-title, .sec, .cat-head, .perfect-msg, .tbar-label { color: #f9a8d4 !important; }
.habit-pill, .rem-title, .aff-text, .hhead, .hstat b, .water-info b, .bloom-name, .rname, .grule, .rpill
    { color: #f8e1f4 !important; }
.rem-sub, .water-info small, .water-info .hint, .hstat small, .bloom-count, .streak, .streak small,
.day-head, .week-label, .aff-who, .mlabel, .legend, .rpct, .garden-sub, .tbar-count, .rem-empty
    { color: #d8b4fe !important; }
.bloom.done .bloom-count { color: #f472b6 !important; }
.day-head.today { color: #fff !important; }
.day-head.weekend { background: #35204a !important; }
.rem-icon, .bloom-stage, .aff-kind, .cat-head small, .days-tag { background: #3b2352 !important; }
.aff-kind, .cat-head small, .days-tag { color: #f9a8d4 !important; }
.cat-head small.ok { background: #ec4899 !important; color: #fff !important; }
.rem-item { border-top-color: #4a2d63 !important; }
.glass { background: rgba(255,255,255,.05) !important; border-color: #6b4a8a !important;
         box-shadow: 0 6px 18px rgba(0,0,0,.4), inset 0 0 0 3px #2a1a3a !important; }
.tbar-track, .rtrack { background: #35204a !important; border-color: #2a1a3a !important; }
.bring-bg { fill: #241532 !important; stroke: #3b2352 !important; }
.ring-bg { stroke: #3b2352 !important; }
.ring-txt { fill: #f8e1f4 !important; }
.p:not(.on):not(.part) { background: #2a1a3a !important; }
div[data-testid="column"]:has(.pin-mark), div[data-testid="stColumn"]:has(.pin-mark) {
    background-color: #3a2337 !important; border-color: #5b2a4e !important;
    background-image: radial-gradient(#5b3a55 1px, transparent 1.3px) !important; }
div[data-testid="column"]:has(.todo-mark), div[data-testid="stColumn"]:has(.todo-mark) {
    background: linear-gradient(160deg, #3b1d3f, #2a1a3a 60%, #2e1f4d) !important; }
div[data-testid="column"]:has(.weekend-mark), div[data-testid="stColumn"]:has(.weekend-mark) {
    background: linear-gradient(160deg, #3d2530, #3a1d3f 50%, #2e1f4d) !important; }
div[data-testid="column"]:has(.tomorrow-mark), div[data-testid="stColumn"]:has(.tomorrow-mark) {
    background: linear-gradient(160deg, #1e1b4b, #2e1f4d 55%, #3b1d3f) !important; }
.stApp .tomorrow-date { color: #c4b5fd !important; }
.stApp div[data-testid="stHorizontalBlock"]:has(.add-mark) input { background: #2a1a3a !important; color: #f8e1f4 !important; }
div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)) { background: #ffffff14 !important; }
.board-title { color: #f9a8d4 !important; } .board-empty { color: #d8b4fe !important; }
.wdot { background: #ffffff20 !important; }
.day-date { color: #f9a8d4 !important; } .todo-meta { color: #d8b4fe !important; }
.todo-bar { background: #35204a !important; }
.weekend { background: linear-gradient(135deg, #3a2337, #2b1e4a) !important; }
.weekend-count { color: #fdba74 !important; }
.pin-text { color: #5b2a4e !important; }
.lazy-strip { background: linear-gradient(120deg, #2e1f4d, #3a1d45) !important; }
.lazy-strip, .lazy-strip small { color: #d8b4fe !important; }
.box.rem { background-image: radial-gradient(#f472b630 1.2px, transparent 1.4px) !important; }
.note { filter: saturate(1.1) brightness(.95); }
.note .note-head, .note .rpill { color: #5b2a4e !important; }
.note .note-sub { color: #9d4b83 !important; }

.stApp .stButton button { background: #2a1a3a; color: #f8e1f4; border-color: #4a2d63; }
.stApp div[class*="st-key-off-"] button { background: #2a1a3a !important; }
.stApp div[class*="st-key-rest-"] button { border-color: #4a2d63 !important; color: #6b4a8a !important; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="input"] input, input, textarea,
[data-baseweb="base-input"] { background: #2a1a3a !important; color: #f8e1f4 !important; border-color: #4a2d63 !important; }
[data-testid="stExpander"] details, [data-testid="stExpander"] summary, [data-testid="stForm"]
    { background: #241532 !important; border-color: #4a2d63 !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: #2a1a3a !important; }
[data-baseweb="popover"] li { color: #f8e1f4 !important; }
</style>
"""


def text_color_on(hex_color):
    """Dark text on light colors, white text on dark ones."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#5b2a4e" if (0.299 * r + 0.587 * g + 0.114 * b) > 170 else "#ffffff"


def habit_css(habits):
    rules = []
    for h in habits.itertuples():
        rules.append(
            f'div[class*="st-key-on-{h.id}-"] button {{ background:{h.color} !important;'
            f' border:2px solid {h.color} !important; color:{text_color_on(h.color)} !important; }}'
            f'div[class*="st-key-off-{h.id}-"] button {{ background:#ffffff !important;'
            f' border:2px solid {h.color} !important; color:{h.color} !important; }}'
        )
    return "<style>" + "".join(rules) + "</style>"


def fmt_liters(ml):
    return f"{ml / 1000:.2f}".rstrip("0").rstrip(".")


# ============================================================
# Compatibility with older Streamlit versions
# ============================================================
def columns(spec, **kwargs):
    try:
        return st.columns(spec, vertical_alignment="center", **kwargs)
    except TypeError:  # before Streamlit 1.36
        return st.columns(spec, **kwargs)


def cell_container(key):
    """Container with a name (for the colors via CSS). Returns (container, ok)."""
    try:
        return st.container(key=key), True
    except TypeError:  # older versions don't know key= yet
        return st.container(), False


HEARTS = {"#f9a8d4": "💓", "#ec4899": "💗", "#db2777": "💖", "#a855f7": "💜",
          "#c4b5fd": "💜", "#d8b4fe": "💜", "#fdba74": "🧡", "#6ee7b7": "💚",
          "#93c5fd": "💙", "#fde68a": "💛"}


# ============================================================
# Database
# ============================================================
def cloud_settings():
    """Online database (Turso) if configured via environment variables or Streamlit secrets."""
    url, token = os.environ.get("TURSO_DATABASE_URL"), os.environ.get("TURSO_AUTH_TOKEN")
    if not url and _secrets_file_exists():
        try:
            url, token = st.secrets.get("TURSO_DATABASE_URL"), st.secrets.get("TURSO_AUTH_TOKEN")
        except Exception:
            pass
    return url, token


def _secrets_file_exists():
    """Only look at st.secrets if a secrets file exists (otherwise Streamlit shows an error box)."""
    try:
        from streamlit import config
        paths = config.get_option("secrets.files")
    except Exception:
        paths = getattr(st.secrets, "_file_paths", None) or []
    return any(os.path.exists(p) for p in paths)


CLOUD_URL, CLOUD_TOKEN = cloud_settings()
# Streamlit Cloud runs apps from /mount/src. There a local file would be wiped on every restart,
# so the app must never run there without the online database.
ON_STREAMLIT_CLOUD = str(Path(__file__).resolve()).startswith("/mount/src")


def _plain(params):
    """numpy numbers (from pandas) -> plain Python values the database drivers understand."""
    return tuple(p.item() if hasattr(p, "item") else p for p in params)
_CACHE = {}  # read cache for one page load, cleared after every write


def get_conn():
    if CLOUD_URL:
        import turso_serverless
        return turso_serverless.connect(CLOUD_URL, auth_token=CLOUD_TOKEN)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_READ = {"conn": None, "used": 0.0}  # one reused online connection for reading


def _run_read(sql, params):
    import time
    if not CLOUD_URL:
        conn = get_conn()
        try:
            cur = conn.execute(sql, _plain(params))
            return [d[0] for d in cur.description or []], cur.fetchall()
        finally:
            conn.close()
    for attempt in (1, 2):
        if _READ["conn"] is None or time.time() - _READ["used"] > 5:
            _READ["conn"] = get_conn()
        try:
            cur = _READ["conn"].execute(sql, _plain(params))
            _READ["used"] = time.time()
            return [d[0] for d in cur.description or []], cur.fetchall()
        except Exception:
            _READ["conn"] = None  # connection expired -> retry once with a fresh one
            if attempt == 2:
                raise


def query(sql, params=()):
    key = (sql, tuple(params))
    if key in _CACHE:
        return _CACHE[key].copy()
    cols, rows = _run_read(sql, params)
    df = pd.DataFrame(rows, columns=cols)
    _CACHE[key] = df
    return df.copy()


def execute(sql, params=()):
    _CACHE.clear()
    conn = get_conn()
    try:
        conn.execute(sql, _plain(params))
        conn.commit()
    finally:
        conn.close()


def get_setting(key, default=None):
    df = query("SELECT value FROM settings WHERE key = ?", (key,))
    return df["value"].iloc[0] if len(df) else default


def set_setting(key, value):
    execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))


def guess_category(name):
    n = name.lower()
    rules = [
        ("Morning routine", ["bed", "to do", "todo", "morning"]),
        ("Night routine", ["skin", "read", "book", "journal", "night"]),
        ("After work routine", ["walk", "after work"]),
        ("Food stuff", ["kitchen", "cook", "food", "eat", "meal", "water", "drink"]),
        ("Mental health", ["medit", "pray", "gratitude", "mental", "therapy"]),
        ("Body", ["workout", "sport", "lymph", "yoga", "gym", "run", "stretch",
                  "rebound", "massage", "pilates"]),
    ]
    for cat, words in rules:
        if any(w in n for w in words):
            return cat
    return "Other"


def migrate_to_english():
    """Runs once: English names, categories, new habits."""
    if get_setting("migrated_v2"):
        return
    rename = {"Bett machen": "Make bed", "Buch lesen": "Read a book",
              "Lymphdrainage": "Lymphatic drainage", "Wasser": "Water"}
    new_habits = [("Journaling", "📓", "#c4b5fd"), ("Go for a walk", "🚶‍♀️", "#6ee7b7"),
                  ("Praying", "🙏", "#fde68a")]
    conn = get_conn()
    try:
        for old, new in rename.items():
            conn.execute("UPDATE habits SET name = ? WHERE name = ?", (new, old))
        existing = {r[0].lower() for r in conn.execute("SELECT name FROM habits")}
        for name, emoji, color in new_habits:
            if name.lower() not in existing:
                conn.execute(
                    "INSERT INTO habits (name, kind, unit, target, color, created, emoji, category) "
                    "VALUES (?, 'binary', '', 1, ?, ?, ?, ?)",
                    (name, color, today_local().isoformat(), emoji, guess_category(name)))
        for hid, name in conn.execute(
                "SELECT id, name FROM habits WHERE category IS NULL OR category IN ('', 'Other')").fetchall():
            conn.execute("UPDATE habits SET category = ? WHERE id = ?", (guess_category(name), hid))
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('migrated_v2', '1')")
        conn.commit()
    finally:
        conn.close()
        _CACHE.clear()


@st.cache_resource(show_spinner=False)
def init_db_once():
    """Create/upgrade the tables once per app start (not on every click)."""
    init_db()
    return True


def init_db():
    execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            kind     TEXT NOT NULL DEFAULT 'binary',   -- 'binary' or 'amount'
            unit     TEXT DEFAULT '',
            target   REAL NOT NULL DEFAULT 1,          -- daily goal
            color    TEXT NOT NULL DEFAULT '#ec4899',
            created  TEXT NOT NULL,
            archived INTEGER NOT NULL DEFAULT 0
        )""")
    execute("""
        CREATE TABLE IF NOT EXISTS entries (
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            day      TEXT NOT NULL,
            value    REAL NOT NULL,
            PRIMARY KEY (habit_id, day)
        )""")
    execute("CREATE TABLE IF NOT EXISTS water (day TEXT PRIMARY KEY, ml REAL NOT NULL)")
    execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    execute("CREATE TABLE IF NOT EXISTS pauses (day TEXT PRIMARY KEY, kind TEXT NOT NULL)")
    execute("""CREATE TABLE IF NOT EXISTS todos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL DEFAULT 'day',
                   day TEXT NOT NULL, text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)""")
    execute("""CREATE TABLE IF NOT EXISTS pins (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, day TEXT,
                   time TEXT DEFAULT '', color INTEGER DEFAULT 0, created TEXT NOT NULL)""")
    cols = query("PRAGMA table_info(habits)")["name"].tolist()
    if "emoji" not in cols:
        execute("ALTER TABLE habits ADD COLUMN emoji TEXT DEFAULT '🌸'")
    if "category" not in cols:
        execute("ALTER TABLE habits ADD COLUMN category TEXT DEFAULT 'Other'")
    if "days" not in cols:  # which weekdays a habit is planned for: "0123456" = every day
        execute("ALTER TABLE habits ADD COLUMN days TEXT DEFAULT '0123456'")
    if "position" not in cols:  # manual order inside a category
        execute("ALTER TABLE habits ADD COLUMN position INTEGER")
    migrate_to_english()
    execute("UPDATE habits SET position = id WHERE position IS NULL")
    execute("UPDATE habits SET days = '0123456' WHERE days IS NULL OR days = ''")


def load_habits(include_archived=False):
    sql = "SELECT * FROM habits"
    if not include_archived:
        sql += " WHERE archived = 0"
    df = query(sql)
    df["emoji"] = df["emoji"].fillna("🌸").replace("", "🌸")
    df["category"] = df["category"].where(df["category"].isin(list(CATEGORIES)), "Other")
    order = {c: i for i, c in enumerate(CATEGORIES)}
    df["_order"] = df["category"].map(order)
    df["days"] = df["days"].fillna("0123456").replace("", "0123456")
    df["position"] = df["position"].fillna(df["id"])
    return df.sort_values(["_order", "position", "id"]).drop(columns="_order").reset_index(drop=True)


def load_entries():
    df = query("SELECT habit_id, day, value FROM entries")
    df["day"] = pd.to_datetime(df["day"]).dt.date
    return df


def save_value(habit_id, day, value):
    if value is None or value <= 0:
        execute("DELETE FROM entries WHERE habit_id = ? AND day = ?",
                (habit_id, day.isoformat()))
    else:
        execute("INSERT OR REPLACE INTO entries (habit_id, day, value) VALUES (?, ?, ?)",
                (habit_id, day.isoformat(), float(value)))


def water_goal():
    return float(get_setting("water_goal_ml", 2000))


def load_water():
    df = query("SELECT day, ml FROM water")
    return {date.fromisoformat(d): ml for d, ml in zip(df["day"], df["ml"])}


def get_water(day):
    return load_water().get(day, 0.0)


def add_water(delta):
    today = today_local()
    ml = max(0.0, get_water(today) + delta)
    execute("INSERT OR REPLACE INTO water (day, ml) VALUES (?, ?)", (today.isoformat(), ml))


# ============================================================
# Calculations
# ============================================================
def done_days(entries, habit):
    """All days on which the daily goal was reached."""
    e = entries[(entries["habit_id"] == habit.id) & (entries["value"] >= habit.target)]
    return set(e["day"])


def habit_start(habit, entries):
    """When a habit starts counting: creation or first entry, whichever is earlier."""
    start = date.fromisoformat(habit.created)
    own = entries.loc[entries["habit_id"] == habit.id, "day"]
    if len(own):
        start = min(start, own.min())
    return start


PAUSED = {}  # day -> "lazy" / "sick" / "vacation", filled at start


def load_pauses():
    df = query("SELECT day, kind FROM pauses")
    return {date.fromisoformat(d): k for d, k in zip(df["day"], df["kind"])}


def is_on(habit, day):
    """Is this habit planned for this day? (Not on rest days and not on lazy/sick/vacation days.)"""
    return day not in PAUSED and str(day.weekday()) in (habit.days or "0123456")


def days_label(days):
    days = days or "0123456"
    if days == "0123456":
        return ""
    if days == "01234":
        return "Weekdays"
    if days == "56":
        return "Weekends"
    return " · ".join(WEEKDAYS[int(c)] for c in days)


def current_streak(days, today, habit=None):
    """Days done in a row. Rest days (not planned) don't break the streak."""
    d = today if today in days else today - timedelta(days=1)
    n = 0
    for _ in range(4000):
        if d in days:
            n += 1
        elif habit is None or is_on(habit, d):
            break
        d -= timedelta(days=1)
    return n


def longest_streak(days, habit=None):
    best = run = 0
    prev = None
    for d in sorted(days):
        if prev is None:
            run = 1
        else:
            gap = [prev + timedelta(days=k) for k in range(1, (d - prev).days)]
            run = run + 1 if not any(habit is None or is_on(habit, g) for g in gap) else 1
        best = max(best, run)
        prev = d
    return best


def category_status(habits, values, day):
    """Per category: (done today, needed) for rule 1."""
    status = {}
    for cat in CATEGORIES:
        sub = [h for h in habits.itertuples() if h.category == cat and is_on(h, day)]
        if not sub:
            continue
        need = min(RULE_MIN_PER_CATEGORY, len(sub))
        got = sum(1 for h in sub if values.get((h.id, day), 0) >= h.target)
        status[cat] = (got, need)
    return status


# ============================================================
# Callbacks
# ============================================================
def toggle(habit_id, day, value):
    save_value(habit_id, day, value)


def on_amount(habit_id, day, key):
    save_value(habit_id, day, st.session_state[key])


def shift_week(n):
    st.session_state.week_offset += n


def reset_week():
    st.session_state.week_offset = 0


# ============================================================
# Page 1 pieces: water, rules, meme, today bar
# ============================================================
def water_card():
    goal = water_goal()
    ml = get_water(today_local())
    first = "water_prev" not in st.session_state
    prev = st.session_state.get("water_prev", 0.0)
    st.session_state.water_prev = ml
    a, b = round(min(prev / goal, 1) * 100), round(min(ml / goal, 1) * 100)
    anim = f"water_{a}_{b}"
    waves = ""
    if b > 0:
        path = '<path d="M0 10 Q 25 0 50 10 T 100 10 T 150 10 T 200 10 V 20 H 0 Z"/>'
        waves = (f'<svg class="wave" viewBox="0 0 200 20" preserveAspectRatio="none">{path}</svg>'
                 f'<svg class="wave w2" viewBox="0 0 200 20" preserveAspectRatio="none">{path}</svg>'
                 '<span class="bubble b1"></span><span class="bubble b2"></span><span class="bubble b3"></span>')
    left = goal - ml
    hint = ("Hydrated queen! 💧👑" if left <= 0 else
            f"{fmt_liters(left)} L to go · about {int(-(-left // 250))} glasses 🥤")
    st.markdown(
        f'<style>@keyframes {anim} {{ from {{ height: {a}% }} to {{ height: {b}% }} }}</style>'
        f'<div class="box"><div class="box-title">💧 Water today</div><div class="water">'
        f'<div class="glass"><div class="liquid" style="height:{b}%;'
        f'animation:{anim} 1.2s cubic-bezier(.34,1.56,.64,1) both">{waves}</div></div>'
        f'<div class="water-info"><b>{fmt_liters(ml)} L</b><small>of {fmt_liters(goal)} L</small>'
        f'<div class="hint">{hint}</div></div></div></div>',
        unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, delta, label in [(c1, 250, "+250 ml"), (c2, 500, "+500 ml"), (c3, -250, "−250 ml")]:
        with col:
            st.markdown('<span class="wbtn-mark"></span>', unsafe_allow_html=True)
            st.button(label, key=f"water{delta}", on_click=add_water, args=(delta,))
    if ml >= goal > prev and not first:
        st.toast("2 liters done! Hydrated queen 💧👑")


def rules_box():
    """The golden rules (in the sidebar)."""
    st.markdown(
        '<div class="box"><div class="box-title">💎 Golden rules</div>'
        f'<div class="grule"><span>🌷</span>At least {RULE_MIN_PER_CATEGORY} habits in every category, every day</div>'
        '<div class="grule"><span>🔁</span>Never miss a habit 2 days in a row</div></div>',
        unsafe_allow_html=True)


def pills(items):
    return "".join(
        f'<span class="rpill" style="background:{h.color}30;border-left:4px solid {h.color}">'
        f'{h.emoji} {html.escape(h.name)}{extra}</span>' for h, extra in items)


def reminders_box(habits, entries, values, today):
    """Smart reminders for today. Each one disappears as soon as it's done."""
    now = now_local()
    yesterday = today - timedelta(days=1)
    done_today = {h.id for h in habits.itertuples() if values.get((h.id, today), 0) >= h.target}
    items = own_reminders(today)
    if today in PAUSED:
        items.append(("💤", "Habit reminders are napping",
                      "It's your " + LAZY[PAUSED[today]][1].lower() + ". No pressure at all today 🫶", ""))
        render_reminders(items)
        return

    # 1. Missed yesterday -> do it today (never miss twice)
    missed = [(h, "") for h in habits.itertuples()
              if habit_start(h, entries) <= yesterday and h.id not in done_today
              and is_on(h, yesterday) and is_on(h, today)
              and values.get((h.id, yesterday), 0) < h.target]
    if missed:
        items.append(("🚨", "Missed yesterday, do it today",
                      "Never miss twice, bestie!", pills(missed)))

    # 2. Streaks in danger (3+ days, not done today yet)
    missed_ids = {h.id for h, _ in missed}
    in_danger = []
    for h in habits.itertuples():
        if h.id in done_today or h.id in missed_ids or not is_on(h, today):
            continue
        streak = current_streak(done_days(entries, h), today, h)
        if streak >= 3:
            in_danger.append((h, f" · {streak} days"))
    if in_danger:
        items.append(("🔥", "Keep your streaks alive", "Don't let them break today", pills(in_danger)))

    # 3. Water check: are you on track for the time of day?
    goal, ml = water_goal(), get_water(today)
    if 9 <= now.hour < 23 and ml < goal:
        expected = goal * min(1, (now.hour - 8) / 13)
        if ml < expected - 250:
            items.append(("💧", "Water check",
                          f"By now about {fmt_liters(expected)} L would be great, you're at "
                          f"{fmt_liters(ml)} L. Grab a glass!", ""))

    # 4. Time of day: morning routine before noon, everything open in the evening
    open_habits = [h for h in habits.itertuples() if h.id not in done_today and is_on(h, today)]
    if now.hour < 12:
        morning = [(h, "") for h in open_habits if h.category == "Morning routine"]
        if morning:
            items.append(("☀️", "Morning routine", "Start your day strong", pills(morning)))
    elif now.hour >= 18 and open_habits:
        night = [(h, "") for h in open_habits if h.category == "Night routine"]
        items.append(("🌙", f"{len(open_habits)} habit{'s' if len(open_habits) != 1 else ''} still open tonight",
                      "Your night routine is waiting:" if night else "There's still time!",
                      pills(night)))

    # 5. Categories that still need something for the golden rule
    short = [f"{CATEGORIES[c]} {need - got} more" for c, (got, need)
             in category_status(habits, values, today).items() if got < need]
    if short and now.hour >= 15:
        items.append(("🌷", "Garden check", " · ".join(short), ""))

    render_reminders(items)


def render_reminders(items):
    if not items:
        items = [("🎀", "All clear!", "Nothing to remind you of right now. You're doing amazing, bestie 💅", "")]
        count = '<span class="rem-count calm">all done</span>'
        bell = '<span class="bell">🔕</span>'
    else:
        count = f'<span class="rem-count">{len(items)} note{"s" if len(items) != 1 else ""}</span>'
        bell = '<span class="bell ringing">🔔</span>'
    notes = "".join(
        f'<div class="note n{i % 5}" style="animation-delay:{i * 90}ms">'
        f'<div class="note-head"><span class="note-icon">{icon}</span>{title}</div>'
        f'<div class="note-sub">{sub}</div>'
        f'{"<div class=note-pills>" + extra + "</div>" if extra else ""}</div>'
        for i, (icon, title, sub, extra) in enumerate(items))
    st.markdown(f'<div class="box rem"><div class="box-title rem-top">{bell}<span>Reminders for today</span>'
                f'{count}</div><div class="board">{notes}</div></div>', unsafe_allow_html=True)


def success_garden(habits, values, today):
    """Today's success: one blooming badge per category."""
    status = category_status(habits, values, today)
    if not status:
        return
    beds, blooming = [], 0
    for i, (cat, (got, need)) in enumerate(status.items()):
        short, color = CATEGORY_STYLE.get(cat, (cat, "#ec4899"))
        rate = min(got / need, 1) if need else 0
        done = got >= need
        blooming += done
        stage = "🌸" if done else ("🌷" if got else "🌱")
        circ = 188.5
        sparks = ('<span class="spark s1">✨</span><span class="spark s2">✨</span>'
                  '<span class="spark s3">💖</span>') if done else ""
        beds.append(
            f'<div class="bloom{" done" if done else ""}" style="animation-delay:{i * 80}ms">'
            f'<div class="bloom-ring"><svg viewBox="0 0 84 84">'
            f'<circle cx="42" cy="42" r="30" class="bring-bg"/>'
            f'<circle cx="42" cy="42" r="30" class="bring-fg" transform="rotate(-90 42 42)" '
            f'style="stroke:{color};stroke-dasharray:{circ};stroke-dashoffset:{circ * (1 - rate):.1f}"/>'
            f'</svg><span class="bloom-icon">{CATEGORIES[cat]}</span>'
            f'<span class="bloom-stage">{stage}</span>{sparks}</div>'
            f'<div class="bloom-name">{short}</div>'
            f'<div class="bloom-count">{got}/{need}{" ✓" if done else ""}</div></div>')
    total = len(status)
    perfect = blooming == total
    msg = ('<div class="perfect-msg">🌸 Perfect day! Every category is in full bloom 👑</div>'
           if perfect else "")
    st.markdown(
        f'<div class="garden{" perfect" if perfect else ""}"><div class="garden-head">'
        f'<div class="box-title">🌷 Today\'s garden</div>'
        f'<div class="garden-sub">{blooming} of {total} categories blooming</div></div>'
        f'<div class="beds">{"".join(beds)}</div>{msg}</div>',
        unsafe_allow_html=True)


def meme_card(done, total, today):
    rate = done / total if total else 0
    level = 0 if done == 0 else 4 if done == total else 1 if rate < 0.34 else 2 if rate < 0.67 else 3
    emoji, top, bottom = random.Random(f"{today}-{level}").choice(MEMES[level])
    st.markdown(
        f'<div class="meme"><span class="meme-emoji">{emoji}</span><div>'
        f'<div class="meme-top">{html.escape(top)}</div>'
        f'<div class="meme-bottom">{html.escape(bottom)}</div></div></div>',
        unsafe_allow_html=True)


def today_bar(done, total):
    """Pink bar that grows with an animation from old to new when you check something."""
    rate = done / total if total else 0
    first = "bar_prev" not in st.session_state
    prev = st.session_state.get("bar_prev", 0)
    st.session_state.bar_prev = rate
    a, b = round(prev * 100), round(rate * 100)
    anim = f"fill_{a}_{b}"
    icon = "💤" if total == 0 else ("👑" if rate >= 1 else "💖")
    st.markdown(
        f'<style>@keyframes {anim} {{ from {{ height: {a}% }} to {{ height: {b}% }} }}'
        f'.block-container, [data-testid="stMainBlockContainer"] {{ padding-right: 6.5rem !important }}'
        f'@media (max-width: 640px) {{ .block-container, [data-testid="stMainBlockContainer"] '
        f'{{ padding-right: 2.1rem !important }} }}</style>'
        f'<div class="tbar"><div class="tbar-label">Today</div><div class="tbar-track">'
        f'<div class="tbar-fill{" full" if rate >= 1 else ""}" style="height:{b}%;'
        f'animation:{anim} 1.1s cubic-bezier(.34,1.56,.64,1) both">'
        f'<span class="tbar-heart">{icon}</span></div></div>'
        f'<div class="tbar-count">{f"{done}/{total}" if total else "zzz"}</div></div>',
        unsafe_allow_html=True)
    if rate >= 1 and prev < 1 and not first:
        st.balloons()
        st.toast("All habits done for today! 👑💖")


# ============================================================
# Affirmations of the day (shown in a shuffled order, one per day,
# so nothing repeats until the whole list has been shown)
# ============================================================
A, M, T, Q = "✨ Affirmation", "🔥 Motivation", "💡 Tip", "📖 Quote"
AFFIRMATIONS = [
    (A, "I am becoming the woman I want to be, one habit at a time.", ""),
    (A, "I am allowed to take up space.", ""),
    (A, "My consistency is my superpower.", ""),
    (A, "I choose progress over perfection.", ""),
    (A, "I am proud of how far I've come.", ""),
    (A, "My body deserves rest, water and kindness.", ""),
    (A, "I am worthy of good things.", ""),
    (A, "I can do hard things.", ""),
    (A, "Today I treat myself like someone I love.", ""),
    (A, "I am calm, grounded and in control.", ""),
    (A, "My future self is cheering for me.", ""),
    (A, "I am growing, even when I can't see it yet.", ""),
    (A, "I don't need to be perfect to be amazing.", ""),
    (A, "I keep the promises I make to myself.", ""),
    (A, "I am the main character of my life.", ""),
    (A, "Every day I get a little bit stronger.", ""),
    (A, "I am enough, exactly as I am today.", ""),
    (A, "I release what I can't control.", ""),
    (A, "My energy is precious and I protect it.", ""),
    (A, "I glow from the inside out.", ""),
    (A, "I trust the timing of my life.", ""),
    (A, "I am building a life I don't need a vacation from.", ""),
    (A, "Small steps still move me forward.", ""),
    (A, "I give myself permission to rest without guilt.", ""),
    (A, "I am disciplined, soft and strong at the same time.", ""),
    (A, "My habits are love letters to my future self.", ""),
    (A, "I deserve the same effort I give to others.", ""),
    (A, "I am open to new beginnings.", ""),
    (A, "I believe in the woman I am becoming.", ""),
    (A, "Today is full of possibilities.", ""),
    (A, "I am grateful for my body and everything it does for me.", ""),
    (A, "My mind is clear and my heart is light.", ""),
    (A, "I radiate confidence and kindness.", ""),
    (A, "I don't compare my chapter one to someone else's chapter twenty.", ""),
    (A, "I am in charge of how I feel today.", ""),
    (A, "Hard days don't erase my progress.", ""),
    (A, "I show up for myself, even on lazy days.", ""),
    (A, "Good things are coming my way.", ""),
    (A, "I am exactly where I need to be.", ""),
    (A, "My peace matters more than being right.", ""),
    (A, "I am gentle with myself when I fall behind.", ""),
    (A, "Taking care of myself is not selfish.", ""),
    (A, "I am capable of amazing things.", ""),
    (A, "I turn my dreams into plans and my plans into habits.", ""),
    (A, "I am safe, loved and supported.", ""),
    (A, "I let go of yesterday and welcome today.", ""),
    (A, "I am a work of art and a work in progress.", ""),
    (A, "I choose joy on purpose.", ""),
    (A, "I celebrate my small wins.", ""),
    (A, "I am patient with my growth.", ""),
    (A, "My standards are high and my heart is soft.", ""),
    (A, "I trust myself to figure it out.", ""),
    (A, "I am becoming 1% better every day.", ""),
    (A, "My worth is not measured by my productivity.", ""),
    (A, "I fill my own cup first.", ""),
    (A, "I deserve a life that feels good on the inside.", ""),
    (A, "I am resilient. I always bounce back.", ""),
    (A, "Today I choose me.", ""),
    (A, "I bring light into every room I walk into.", ""),
    (A, "What is meant for me will find me.", ""),
    (A, "I am thankful for today, for the good moments and for the lessons.", ""),
    (A, "I speak to myself with love.", ""),
    (A, "I am allowed to change, grow and start again.", ""),
    (A, "My calm is my power.", ""),
    (A, "Today I choose habits over excuses.", ""),
    (A, "I am proud of the girl who keeps going.", ""),
    (A, "I make healthy choices because I love myself.", ""),
    (A, "I am the author of my own story.", ""),
    (A, "Little things done with love become big things.", ""),
    (A, "My routine is self-respect in action.", ""),
    (A, "I let my light shine without dimming it for anyone.", ""),
    (A, "I am thriving, not just surviving.", ""),
    (A, "Peace begins with one deep breath.", ""),
    (A, "My potential is endless.", ""),
    (A, "I trust my journey, even when it's slow.", ""),
    (A, "I'm not lucky, I'm consistent.", ""),
    (A, "I water my own garden.", ""),
    (A, "Soft life, strong habits.", ""),
    (A, "I deserve to feel good in my body and in my mind.", ""),
    (A, "I am becoming my own safe place.", ""),
    (A, "My dreams are valid and my effort is enough.", ""),
    (A, "I am learning to love the process.", ""),
    (M, "Done is better than perfect.", ""),
    (M, "You don't have to feel motivated. You just have to start.", ""),
    (M, "Two minutes is enough to begin.", ""),
    (M, "Don't break the chain, bestie.", ""),
    (M, "Slow progress is still progress.", ""),
    (M, "Your only competition is who you were yesterday.", ""),
    (M, "Discipline is choosing what you want most over what you want now.", ""),
    (M, "One day or day one. You decide.", ""),
    (M, "The best time to start was yesterday. The next best time is now.", ""),
    (M, "A little progress every day adds up to big results.", ""),
    (M, "Show up, even if it's messy.", ""),
    (M, "Make your future self proud.", ""),
    (M, "Be the energy you want to attract.", ""),
    (M, "Consistency beats intensity.", ""),
    (M, "You've survived 100% of your bad days so far.", ""),
    (M, "It's okay to start small. It's not okay to never start.", ""),
    (M, "You are one habit away from a different life.", ""),
    (M, "Romanticize your routines.", ""),
    (M, "Missing once is an accident. Missing twice is the start of a new habit.", ""),
    (M, "Fall in love with the process and the results will follow.", ""),
    (M, "Dream big, start small, act now.", ""),
    (M, "Your vibe today: unbothered and unstoppable.", ""),
    (M, "Don't wait for Monday. Today is a great day to start.", ""),
    (M, "You're not behind. You're on your own timeline.", ""),
    (M, "Tiny steps, big glow-up.", ""),
    (M, "Start where you are, not where you think you should be.", ""),
    (M, "Energy flows where attention goes.", ""),
    (M, "Do it for the girl you'll be in one year.", ""),
    (M, "Be stubborn about your goals and flexible about your methods.", ""),
    (M, "Some days you bloom, some days you grow roots. Both count.", ""),
    (M, "Pretty girls drink water and check their habits.", ""),
    (M, "You didn't come this far to only come this far.", ""),
    (M, "Discomfort is the price of growth.", ""),
    (M, "Be so consistent they think it's luck.", ""),
    (M, "Your habits today are your results tomorrow.", ""),
    (M, "Make it so easy you can't say no.", ""),
    (M, "Rest if you must, but don't quit.", ""),
    (M, "Nobody is coming to do it for you, and that's the good news: you get to.", ""),
    (M, "Choose the hard thing today so tomorrow gets easier.", ""),
    (M, "Fake it till you make it a habit.", ""),
    (M, "A walk, a glass of water and a deep breath fix more than you think.", ""),
    (M, "You're the CEO of your own glow-up.", ""),
    (M, "Every check mark counts.", ""),
    (M, "Let your actions speak louder than your plans.", ""),
    (M, "Your comfort zone is cozy, but nothing grows there.", ""),
    (M, "Plot twist: you actually do the thing today.", ""),
    (M, "Main character move: doing your habits without anyone asking.", ""),
    (M, "Hydrate, stretch, slay.", ""),
    (M, "The girl who does her habits on bad days becomes unstoppable.", ""),
    (M, "You are your best investment.", ""),
    (M, "Just do the next right thing.", ""),
    (M, "Today counts. Make it a good one.", ""),
    (M, "Motivation fades. Habits stay.", ""),
    (M, "Be the girl who finishes what she starts.", ""),
    (T, "Stack a new habit onto an old one: after I brush my teeth, I write one line in my journal.", ""),
    (T, "Drink a glass of water before your first coffee.", ""),
    (T, "Lay out tomorrow's clothes tonight.", ""),
    (T, "Keep your phone in another room for the first 30 minutes of your day.", ""),
    (T, "Make your bed first thing. It's your first win of the day.", ""),
    (T, "Write down three things you're grateful for before you sleep.", ""),
    (T, "Too tired for the full workout? Do 5 minutes. It still counts.", ""),
    (T, "Put your book on your pillow so it's waiting for you at bedtime.", ""),
    (T, "Keep a water bottle where you can always see it.", ""),
    (T, "Prepare a healthy snack before you get hungry.", ""),
    (T, "Take a 10 minute walk after lunch or dinner.", ""),
    (T, "Two-minute rule: if it takes less than two minutes, do it right now.", ""),
    (T, "Dim the lights an hour before bed.", ""),
    (T, "Box breathing: in for 4, hold for 4, out for 4, hold for 4. Repeat 4 times.", ""),
    (T, "Put on your favorite playlist to make chores more fun.", ""),
    (T, "Plan your top 3 tasks for tomorrow before you finish today.", ""),
    (T, "Stretch for two minutes right after you wake up.", ""),
    (T, "Swap one scrolling session for one chapter of your book.", ""),
    (T, "Plan a small reward for a full week of habits.", ""),
    (T, "Keep your skincare where you'll see it, not hidden in a drawer.", ""),
    (T, "Get some daylight in the morning. It helps you sleep better at night.", ""),
    (T, "Add one more colorful vegetable to your plate today.", ""),
    (T, "Set a 10 minute timer and tidy up. It's surprisingly satisfying.", ""),
    (T, "Send a sweet message to someone you love today.", ""),
    (T, "Say no to one thing that drains you.", ""),
    (T, "Every hour, look at something far away for 20 seconds to rest your eyes.", ""),
    (T, "Fill tomorrow's water bottle tonight.", ""),
    (T, "Feeling stuck? Change your environment: new room, new café, fresh air.", ""),
    (T, "On busy days, one sentence in your journal is enough.", ""),
    (T, "Go to bed 15 minutes earlier tonight.", ""),
    (T, "Turn putting on lip balm or lotion into a tiny self-care moment.", ""),
    (T, "Take the stairs whenever you can.", ""),
    (T, "Cook a little extra tonight for tomorrow's lunch.", ""),
    (T, "Head too full? Do a 5 minute brain dump on paper.", ""),
    (T, "Make your environment the reminder: put your walking shoes by the door.", ""),
    (T, "Take one quiet minute to pray or reflect before your day begins.", ""),
    (T, "Notice one beautiful thing on your walk today.", ""),
    (T, "Keep a done list, not just a to-do list.", ""),
    (T, "Put fruit at eye level in the fridge.", ""),
    (T, "Charge your phone outside the bedroom.", ""),
    (T, "Replace \"I have to\" with \"I get to\".", ""),
    (T, "Low energy day? Do your two easiest habits first.", ""),
    (T, "Drink a glass of water with every meal.", ""),
    (T, "Write today's intention on a sticky note and put it on your mirror.", ""),
    (T, "Prepare your morning: coffee mug out, outfit ready, phone on silent.", ""),
    (T, "Pair something you need to do with something you love: podcast + walk.", ""),
    (Q, "The journey of a thousand miles begins with a single step.", "Lao Tzu"),
    (Q, "We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Will Durant"),
    (Q, "You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    (Q, "Every action you take is a vote for the type of person you wish to become.", "James Clear"),
    (Q, "Habits are the compound interest of self-improvement.", "James Clear"),
    (Q, "What you do every day matters more than what you do once in a while.", "Gretchen Rubin"),
    (Q, "Fall seven times, stand up eight.", "Japanese proverb"),
    (Q, "Little by little, one travels far.", "Spanish proverb"),
    (Q, "Well done is better than well said.", "Benjamin Franklin"),
    (Q, "Knowing is not enough; we must apply. Willing is not enough; we must do.", "Johann Wolfgang von Goethe"),
    (Q, "Rome wasn't built in a day.", "Proverb"),
    (Q, "This too shall pass.", "Proverb"),
    (Q, "Bloom where you are planted.", "Proverb"),
    (Q, "Fortune favors the bold.", "Latin proverb"),
    (Q, "A smooth sea never made a skilled sailor.", "Proverb"),
    (Q, "Where there's a will, there's a way.", "Proverb"),
    (Q, "The best way out is always through.", "Robert Frost"),
    (Q, "Hope is the thing with feathers that perches in the soul.", "Emily Dickinson"),
    (Q, "Make each day your masterpiece.", "John Wooden"),
    (Q, "Courage is grace under pressure.", "Ernest Hemingway"),
    (Q, "No rain, no flowers.", "Proverb"),
    (Q, "Health is wealth.", "Proverb"),
    (Q, "Drop by drop, the bucket fills.", "Proverb"),
    (Q, "Patience is bitter, but its fruit is sweet.", "Proverb"),
]
_AFF_ORDER = list(range(len(AFFIRMATIONS)))
random.Random(2026).shuffle(_AFF_ORDER)


def affirmation_of_the_day(day):
    return AFFIRMATIONS[_AFF_ORDER[day.toordinal() % len(AFFIRMATIONS)]]


def affirmation_card(day):
    kind, text, author = affirmation_of_the_day(day)
    who = f'<div class="aff-who">— {html.escape(author)}</div>' if author else ""
    st.markdown(
        f'<div class="box aff"><div class="box-title">🌸 Affirmation of the day</div>'
        f'<span class="aff-kind">{kind}</span>'
        f'<div class="aff-text">{html.escape(text)}</div>{who}</div>',
        unsafe_allow_html=True)


# ============================================================
# Lazy Day mode 🦥 (lazy / sick / vacation)
# ============================================================
LAZY = {  # kind: (emoji, name, message, gradient, accent, page background)
    "lazy": ("🦥", "Lazy day",
             "No pressure today. Blanket, snacks and your comfort show are officially on the schedule.",
             "linear-gradient(120deg, #c7d2fe, #e9d5ff 55%, #fbcfe8)", "#7c3aed",
             "linear-gradient(180deg, #eef2ff 0%, #f5f3ff 60%, #fdf2f8 100%)"),
    "sick": ("🤒", "Sick day",
             "Tea, sleep and cuddles are your only habits today. Get well soon, bestie 💕",
             "linear-gradient(120deg, #a7f3d0, #bae6fd 60%, #e9d5ff)", "#0f766e",
             "linear-gradient(180deg, #ecfdf5 0%, #f0f9ff 60%, #f5f3ff 100%)"),
    "vacation": ("🏖️", "Vacation mode",
                 "Out of office! Sun, fun and zero guilt. Your streaks are safe and wait for you.",
                 "linear-gradient(120deg, #fed7aa, #fde68a 45%, #a5f3fc)", "#c2410c",
                 "linear-gradient(180deg, #fff7ed 0%, #fefce8 50%, #ecfeff 100%)"),
}

LAZY_CSS = """
<style>
.lazy-strip { display: flex; align-items: center; gap: 12px; padding: 10px 18px; border-radius: 99px;
              background: linear-gradient(120deg, #f5f3ff, #fdf2f8); color: #6d28d9; font-weight: 700;
              box-shadow: 0 4px 14px rgba(124,58,237,.12); }
.lazy-strip .sloth { font-size: 1.6rem; display: inline-block; animation: sway 3s ease-in-out infinite; }
.lazy-strip small { display: block; font-weight: 600; color: #8b5cf6; }
.lazy-banner { position: relative; overflow: hidden; border-radius: 26px; padding: 22px 26px; color: #3b0764;
               box-shadow: 0 10px 30px rgba(124,58,237,.25); animation: popIn .7s ease both;
               display: flex; align-items: center; gap: 22px; }
.lazy-emoji { font-size: 4.2rem; display: inline-block; animation: sway 3.2s ease-in-out infinite;
              transform-origin: 50% 90%; }
.lazy-title { font-family: 'Anton', Impact, sans-serif; font-size: 2rem; text-transform: uppercase; letter-spacing: 1px; }
.lazy-msg { font-weight: 600; margin-top: 2px; max-width: 560px; }
.lazy-until { margin-top: 8px; display: inline-block; background: #ffffffaa; border-radius: 99px;
              padding: 3px 12px; font-weight: 700; font-size: .85rem; }
.zzz { position: absolute; font-family: 'Anton', Impact, sans-serif; color: #ffffffcc; font-size: 1.6rem;
       animation: floatZ 4s ease-in infinite; }
.zzz.z1 { left: 78%; bottom: 10px; } .zzz.z2 { left: 84%; bottom: 10px; animation-delay: 1.3s; font-size: 1.2rem; }
.zzz.z3 { left: 90%; bottom: 10px; animation-delay: 2.6s; font-size: 2rem; }
@keyframes sway { 0%, 100% { transform: rotate(-7deg) } 50% { transform: rotate(7deg) } }

/* the Lazy mode button */
.lazybtn-mark, .backbtn-mark { display: none; }
div[data-testid="stElementContainer"]:has(.lazybtn-mark), div.element-container:has(.lazybtn-mark),
div[data-testid="stElementContainer"]:has(.backbtn-mark), div.element-container:has(.backbtn-mark) { display: none; }
.lazy-hint { font-weight: 700; color: #8b5cf6; padding: 10px 4px; }
div[data-testid="column"]:has(.lazybtn-mark) button, div[data-testid="stColumn"]:has(.lazybtn-mark) button {
    border: none !important; border-radius: 99px !important; padding: .6rem 1.2rem !important;
    background: linear-gradient(120deg, #a5b4fc, #c084fc 50%, #f9a8d4) !important; background-size: 200% 200% !important;
    color: #fff !important; font-weight: 800 !important; letter-spacing: .5px;
    box-shadow: 0 6px 18px rgba(139,92,246,.35), inset 0 -3px 0 rgba(0,0,0,.08) !important;
    animation: shimmer 4s ease infinite; transition: transform .2s ease; }
div[data-testid="column"]:has(.lazybtn-mark) button p, div[data-testid="stColumn"]:has(.lazybtn-mark) button p {
    font-size: 1.05rem !important; font-weight: 800 !important; color: #fff !important; }
div[data-testid="column"]:has(.lazybtn-mark) button:hover, div[data-testid="stColumn"]:has(.lazybtn-mark) button:hover {
    transform: translateY(-2px) rotate(-1.5deg) scale(1.03); }
div[data-testid="column"]:has(.backbtn-mark) button, div[data-testid="stColumn"]:has(.backbtn-mark) button {
    border: none !important; border-radius: 99px !important; color: #fff !important; font-weight: 800 !important;
    background: linear-gradient(120deg, #f472b6, #fb923c) !important; box-shadow: 0 6px 16px rgba(236,72,153,.35) !important; }
div[data-testid="column"]:has(.backbtn-mark) button p, div[data-testid="stColumn"]:has(.backbtn-mark) button p { color: #fff !important; font-weight: 800 !important; }
@keyframes shimmer { 0%, 100% { background-position: 0% 50% } 50% { background-position: 100% 50% } }

/* the one-time "lazy party" overlay */
.lazy-party { position: fixed; inset: 0; z-index: 10000; pointer-events: none; overflow: hidden;
              background: radial-gradient(circle at 50% 45%, #ede9fecc, #c7d2fe99 60%, #fbcfe866);
              animation: lpFade 5.2s ease forwards; }
.lp-float { position: absolute; left: -12%; animation-name: lpDrift; animation-timing-function: ease-in-out;
            animation-fill-mode: both; filter: drop-shadow(0 4px 6px rgba(91,33,182,.2)); }
.lp-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;
             animation: lpPop 1.2s cubic-bezier(.34,1.56,.64,1) both; }
.lp-sloth { font-size: 6rem; display: inline-block; animation: sway 1.6s ease-in-out infinite; transform-origin: 50% 10%; }
.lp-text { font-family: 'Anton', Impact, sans-serif; font-size: 3rem; color: #6d28d9; text-transform: uppercase;
           letter-spacing: 2px; text-shadow: 0 3px 0 #fff; }
.lp-sub { font-weight: 700; color: #7c3aed; font-size: 1.1rem; }
@keyframes lpDrift { 0% { transform: translateX(0) translateY(0) rotate(-10deg); opacity: 0 }
                     15% { opacity: 1 } 50% { transform: translateX(60vw) translateY(-30px) rotate(8deg) }
                     100% { transform: translateX(125vw) translateY(10px) rotate(-6deg); opacity: 0 } }
@keyframes lpFade { 0% { opacity: 0 } 10% { opacity: 1 } 75% { opacity: 1 } 100% { opacity: 0; visibility: hidden } }
@keyframes lpPop { from { transform: translate(-50%, -50%) scale(.3); opacity: 0 } }
@media (max-width: 640px) { .lp-text { font-size: 2rem; } .lp-sloth { font-size: 4.5rem; } }
@keyframes floatZ { 0% { transform: translateY(0) rotate(0); opacity: 0 } 20% { opacity: 1 }
                    100% { transform: translateY(-110px) rotate(20deg); opacity: 0 } }
@media (max-width: 640px) {
    .lazy-banner { padding: 16px 16px; gap: 12px; }
    .lazy-emoji { font-size: 3rem; } .lazy-title { font-size: 1.35rem; }
    .lazy-strip { border-radius: 22px; }
}
</style>
"""


def lazy_theme_css(kind):
    _e, _n, _m, _grad, accent, page_bg = LAZY[kind]
    return (f"<style>.stApp, [data-testid='stAppViewContainer'] {{ background: {page_bg} !important; }}"
            f".stApp h1, .stApp h2, .stApp h3, .box-title, .sec, .cat-head {{ color: {accent} !important; }}"
            f".day-head.today {{ background: {accent} !important; }}"
            f".tbar-fill {{ background: linear-gradient(0deg, {accent}, #c4b5fd) !important; }}</style>")


def start_lazy():
    start_pause("lazy", today_local())
    st.session_state.lazy_party = True


def end_lazy():
    end_pause()
    st.session_state.welcome_back = True


def lazy_party():
    """One-time animation: sloths, clouds and z's drift across the whole app."""
    import random as _r
    rnd = _r.Random()
    things = ["🦥", "☁️", "💤", "☁️", "🌙", "🦥", "☁️", "✨", "💤", "🛋️", "☁️", "🦥", "🍿", "☁️", "💜", "💤"]
    floaters = "".join(
        f'<span class="lp-float" style="top:{rnd.randint(4, 88)}%;font-size:{rnd.uniform(1.6, 3.6):.1f}rem;'
        f'animation-delay:{rnd.uniform(0, 1.6):.2f}s;animation-duration:{rnd.uniform(3.2, 5):.2f}s">{t}</span>'
        for t in things)
    st.markdown(f'<div class="lazy-party">{floaters}<div class="lp-center"><div class="lp-sloth">🦥</div>'
                f'<div class="lp-text">Lazy mode ON</div><div class="lp-sub">shhh… the habits are sleeping too 💤</div>'
                f'</div></div>', unsafe_allow_html=True)


def start_pause(kind, until):
    d = today_local()
    while d <= until:
        execute("INSERT OR REPLACE INTO pauses (day, kind) VALUES (?, ?)", (d.isoformat(), kind))
        d += timedelta(days=1)


def end_pause():
    execute("DELETE FROM pauses WHERE day >= ?", (today_local().isoformat(),))


def lazy_top(today):
    st.markdown(LAZY_CSS, unsafe_allow_html=True)
    if today in PAUSED:
        kind = PAUSED[today]
        emoji, name, msg, grad, _a, _bg = LAZY[kind]
        last = today
        while last + timedelta(days=1) in PAUSED:
            last += timedelta(days=1)
        back = last + timedelta(days=1)
        until = (f'<div class="lazy-until">Back on {WEEKDAYS[back.weekday()]}, {MONTHS[back.month - 1]} {back.day} ✨</div>'
                 if last > today else "")
        zzz = ('<span class="zzz z1">z</span><span class="zzz z2">z</span><span class="zzz z3">Z</span>'
               if kind != "vacation" else
               '<span class="zzz z1">☀️</span><span class="zzz z2">🌴</span><span class="zzz z3">🍹</span>')
        st.markdown(f'<div class="lazy-banner" style="background:{grad}"><span class="lazy-emoji">{emoji}</span>'
                    f'<div><div class="lazy-title">{name} activated</div><div class="lazy-msg">{msg}</div>'
                    f'{until}</div>{zzz}</div>', unsafe_allow_html=True)
        if st.session_state.pop("lazy_party", False):
            lazy_party()
        c1, _ = columns([1, 3])
        with c1:
            st.markdown('<span class="backbtn-mark"></span>', unsafe_allow_html=True)
            st.button("✨ I'm back!", on_click=end_lazy, key="end_pause", use_container_width=True)
        return
    if st.session_state.pop("welcome_back", False):
        st.toast("Welcome back, queen! Let's glow ✨👑")
        st.balloons()

    _, c2 = columns([3, 1.2])
    with c2:
        st.markdown('<span class="lazybtn-mark"></span>', unsafe_allow_html=True)
        st.button("🦥  Lazy day today?", key="start_lazy", on_click=start_lazy, use_container_width=True,
                  help="Your streaks stay safe 🫶")


# ============================================================
# My Day: to-dos, pinboard, weekend corner
# ============================================================
PIN_COLORS = ["🩷 Pink", "💜 Lilac", "🍑 Peach", "🌿 Mint", "🩵 Blue"]

MYDAY_CSS = """
<style>
.nowrap-mark, .pin-mark, .todo-mark, .weekend-mark, .tomorrow-mark { display: none; }
div[data-testid="stElementContainer"]:has(.tomorrow-mark), div.element-container:has(.tomorrow-mark) { display: none; }
div[data-testid="stElementContainer"]:has(.nowrap-mark), div.element-container:has(.nowrap-mark),
div[data-testid="stElementContainer"]:has(.pin-mark), div.element-container:has(.pin-mark),
div[data-testid="stElementContainer"]:has(.todo-mark), div.element-container:has(.todo-mark),
div[data-testid="stElementContainer"]:has(.weekend-mark), div.element-container:has(.weekend-mark) { display: none; }
@media (max-width: 640px) {
    div[data-testid="stHorizontalBlock"]:has(.nowrap-mark) { flex-wrap: nowrap !important; gap: .3rem !important; }
    div[data-testid="stHorizontalBlock"]:has(.nowrap-mark) > div { min-width: 0 !important; flex: 0 0 auto !important; width: auto !important; }
    div[data-testid="stHorizontalBlock"]:has(.nowrap-mark) > div:first-child { flex: 1 1 auto !important; }
}

/* ---------- colored boxes (the columns that contain a marker) ---------- */
div[data-testid="column"]:has(.pin-mark), div[data-testid="stColumn"]:has(.pin-mark),
div[data-testid="column"]:has(.todo-mark), div[data-testid="stColumn"]:has(.todo-mark),
div[data-testid="column"]:has(.weekend-mark), div[data-testid="stColumn"]:has(.weekend-mark),
div[data-testid="column"]:has(.tomorrow-mark), div[data-testid="stColumn"]:has(.tomorrow-mark) {
    border-radius: 26px; padding: 18px 20px 14px !important; animation: popIn .6s ease both; }

/* Pinboard: soft cork board in pink tones */
div[data-testid="column"]:has(.pin-mark), div[data-testid="stColumn"]:has(.pin-mark) {
    background-color: #fbe3d6;
    background-image: radial-gradient(#e8b4a0 1px, transparent 1.3px), radial-gradient(#f4c7b5 1px, transparent 1.3px);
    background-size: 18px 18px, 18px 18px; background-position: 0 0, 9px 9px;
    border: 6px solid #f9c9dc; box-shadow: inset 0 0 0 2px #fff6, 0 10px 28px rgba(219,39,119,.18); }
.board-head { display: flex; align-items: center; gap: 10px; }
.board-title { font-family: 'Patrick Hand', cursive; font-size: 1.8rem; color: #9d174d; }
.board-empty { text-align: center; padding: 18px 0 10px; font-family: 'Patrick Hand', cursive;
               font-size: 1.25rem; color: #9d4b83; }
div[data-testid="column"]:has(.pin-mark) [data-testid="stExpander"] details,
div[data-testid="stColumn"]:has(.pin-mark) [data-testid="stExpander"] details {
    background: linear-gradient(120deg, #fff 0%, #fdf2f8 60%, #f5f3ff 100%) !important;
    border: 2px dashed #f472b6 !important; border-radius: 18px !important;
    box-shadow: 0 4px 14px rgba(236,72,153,.15); }
div[data-testid="column"]:has(.pin-mark) [data-testid="stExpander"] summary p,
div[data-testid="stColumn"]:has(.pin-mark) [data-testid="stExpander"] summary p {
    font-weight: 700 !important; color: #db2777 !important; font-size: 1.02rem; }
.pin-note { position: relative; padding: 22px 14px 12px; border-radius: 3px 3px 16px 3px; min-height: 92px;
            color: #5b2a4e; box-shadow: 0 8px 16px rgba(120,40,60,.18);
            animation: noteIn .55s cubic-bezier(.34,1.56,.64,1) both; transition: transform .2s; }
.pin-note.n0 { background: #ffd6e7; transform: rotate(-2deg); }
.pin-note.n1 { background: #e9dcff; transform: rotate(1.5deg); }
.pin-note.n2 { background: #ffe2c2; transform: rotate(-1deg); }
.pin-note.n3 { background: #d3f8e2; transform: rotate(2deg); }
.pin-note.n4 { background: #d6eeff; transform: rotate(-1.5deg); }
.pin-note:hover { transform: rotate(0) translateY(-4px) scale(1.03); }
.pin-note.soon { box-shadow: 0 0 0 3px #ec4899, 0 10px 22px rgba(236,72,153,.35); }
.pin-note.past { opacity: .55; filter: grayscale(.4); }
.pin-head { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); font-size: 1.5rem;
            filter: drop-shadow(0 2px 2px rgba(0,0,0,.25)); }
.pin-text { font-family: 'Patrick Hand', cursive; font-size: 1.3rem; line-height: 1.2; color: #5b2a4e;
            word-wrap: break-word; }
.pin-when { display: inline-block; font-size: .72rem; font-weight: 700; border-radius: 99px; padding: 2px 9px;
            background: #ffffffc0; color: #9d4b83; margin-top: 8px; }
.pin-when.soon { background: #ec4899; color: #fff; }

/* To-do box: pink */
div[data-testid="column"]:has(.todo-mark), div[data-testid="stColumn"]:has(.todo-mark) {
    background: linear-gradient(160deg, #ffe4f1 0%, #fdf2f8 45%, #f3e8ff 100%);
    box-shadow: 0 10px 28px rgba(236,72,153,.18); }
.day-date { font-family: 'Patrick Hand', cursive; font-size: 1.7rem; color: #c2185b; line-height: 1.1; }
.todo-bar { height: 12px; background: #ffffffb0; border-radius: 99px; overflow: hidden; margin: 8px 0 4px; }
.todo-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #f9a8d4, #ec4899);
             animation: grow 1s cubic-bezier(.22,1,.36,1) both; }
.todo-meta { font-size: .82rem; font-weight: 700; color: #9d4b83; margin-bottom: 8px; }

/* Tomorrow box: dreamy night sky */
div[data-testid="column"]:has(.tomorrow-mark), div[data-testid="stColumn"]:has(.tomorrow-mark) {
    position: relative; background: linear-gradient(160deg, #e0e7ff 0%, #ede9fe 45%, #fce7f3 100%);
    box-shadow: 0 10px 28px rgba(99,102,241,.18); }
.tomorrow-date { color: #6d28d9 !important; }
.star { position: absolute; color: #a78bfa; animation: twinkle 2.4s ease-in-out infinite; }
.star.s1 { top: 18px; right: 34px; font-size: 1.2rem; }
.star.s2 { top: 44px; right: 70px; font-size: .9rem; animation-delay: .8s; }
.star.s3 { top: 14px; right: 110px; font-size: .75rem; animation-delay: 1.6s; }

/* Weekend box: sunset */
div[data-testid="column"]:has(.weekend-mark), div[data-testid="stColumn"]:has(.weekend-mark) {
    background: linear-gradient(160deg, #ffedd5 0%, #fed7e2 50%, #e9d5ff 100%);
    box-shadow: 0 10px 28px rgba(249,115,22,.18); }
.weekend-count { font-family: 'Patrick Hand', cursive; font-size: 1.55rem; color: #c2410c; line-height: 1.15; }
.wdots { display: flex; gap: 6px; margin: 8px 0 10px; }
.wdot { width: 14px; height: 14px; border-radius: 50%; background: #ffffffb0; border: 2px solid #fdba74; }
.wdot.on { background: #fb923c; border-color: #fb923c; }

/* Smooth task rows inside both boxes */
div[data-testid="column"]:has(.todo-mark) div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)),
div[data-testid="stColumn"]:has(.todo-mark) div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)),
div[data-testid="column"]:has(.weekend-mark) div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)),
div[data-testid="column"]:has(.tomorrow-mark) div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)),
div[data-testid="stColumn"]:has(.tomorrow-mark) div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)),
div[data-testid="stColumn"]:has(.weekend-mark) div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)) {
    background: #ffffffd9; border-radius: 16px; padding: 6px 8px 6px 14px; margin-bottom: 2px;
    align-items: center; box-shadow: 0 2px 8px rgba(157,23,77,.08); transition: transform .18s, box-shadow .18s;
    animation: popIn .4s ease both; }
div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)):hover {
    transform: translateX(4px); box-shadow: 0 4px 14px rgba(157,23,77,.15); }
div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)) .stCheckbox { min-height: 0; }
div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)) del { opacity: .5; }
div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)) button {
    border: none !important; background: transparent !important; color: #d8a3c4 !important; }
div[data-testid="stHorizontalBlock"]:has(.nowrap-mark:not(.add-mark)) button:hover { color: #ec4899 !important; }
div[data-testid="stHorizontalBlock"]:has(.add-mark) input { background: #ffffffd9 !important; border-radius: 14px !important; }
div[data-testid="stHorizontalBlock"]:has(.add-mark) button { border-radius: 14px !important; background: #ec4899 !important;
                                                            color: #fff !important; border: none !important; }
div[data-testid="column"]:has(.todo-mark) [data-testid="stVerticalBlock"],
div[data-testid="stColumn"]:has(.todo-mark) [data-testid="stVerticalBlock"],
div[data-testid="column"]:has(.weekend-mark) [data-testid="stVerticalBlock"],
div[data-testid="stColumn"]:has(.weekend-mark) [data-testid="stVerticalBlock"],
div[data-testid="column"]:has(.tomorrow-mark) [data-testid="stVerticalBlock"],
div[data-testid="stColumn"]:has(.tomorrow-mark) [data-testid="stVerticalBlock"] { gap: .55rem !important; }
@media (max-width: 640px) {
    .board-title { font-size: 1.5rem; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):has(.pin-note) { flex-wrap: wrap !important; gap: .9rem .6rem !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):has(.pin-note) > div { flex: 0 0 calc(50% - .3rem) !important;
                                                                 width: calc(50% - .3rem) !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):has(.pin-note) > div:not(:has(.pin-note)) { display: none !important; }
    .pin-note { min-height: 80px; padding: 20px 10px 10px; }
    .pin-text { font-size: 1.1rem; }
}
</style>
"""


def nice_day(d, today):
    if d == today:
        return "Today"
    if d == today + timedelta(days=1):
        return "Tomorrow"
    if d == today - timedelta(days=1):
        return "Yesterday"
    label = f"{WEEKDAYS[d.weekday()]}, {MONTHS[d.month - 1]} {d.day}"
    if today < d <= today + timedelta(days=6):
        label += f" · in {(d - today).days} days"
    return label


def load_todos(kind, day):
    return query("SELECT * FROM todos WHERE kind = ? AND day = ? ORDER BY done, id", (kind, day.isoformat()))


def add_todo(kind, day, key):
    text = (st.session_state.get(key) or "").strip()
    if text:
        execute("INSERT INTO todos (kind, day, text) VALUES (?, ?, ?)", (kind, day.isoformat(), text))
    st.session_state[key] = ""


def toggle_todo(todo_id, key):
    execute("UPDATE todos SET done = ? WHERE id = ?", (int(st.session_state[key]), todo_id))


def delete_row(table, row_id):
    execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))


def move_to_tomorrow(today):
    execute("UPDATE todos SET day = ? WHERE kind = 'day' AND done = 0 AND day = ?",
            ((today + timedelta(days=1)).isoformat(), today.isoformat()))


def carry_over(today):
    execute("UPDATE todos SET day = ? WHERE kind = 'day' AND done = 0 AND day < ?",
            (today.isoformat(), today.isoformat()))


def todo_list(kind, day, empty_text):
    todos = load_todos(kind, day)
    for t in todos.itertuples():
        c1, c2 = columns([10, 1])
        with c1:
            st.markdown('<span class="nowrap-mark"></span>', unsafe_allow_html=True)
            key = f"todo_{t.id}"
            label = f"~~{t.text}~~ ✓" if t.done else t.text
            st.checkbox(label, value=bool(t.done), key=key, on_change=toggle_todo, args=(t.id, key))
        with c2:
            st.markdown('<span class="nowrap-mark"></span>', unsafe_allow_html=True)
            st.button("✕", key=f"del_todo_{t.id}", on_click=delete_row, args=("todos", t.id), help="Delete")
    if todos.empty:
        st.caption(empty_text)
    akey = f"new_{kind}_{day.isoformat()}"
    c1, c2 = columns([10, 2])
    with c1:
        st.markdown('<span class="nowrap-mark add-mark"></span>', unsafe_allow_html=True)
        st.text_input("New task", key=akey, placeholder="Add something…", label_visibility="collapsed",
                      on_change=add_todo, args=(kind, day, akey))
    with c2:
        st.markdown('<span class="nowrap-mark"></span>', unsafe_allow_html=True)
        st.button("➕", key=f"add_{akey}", on_click=add_todo, args=(kind, day, akey))
    return todos


def add_pin():
    text = (st.session_state.get("pin_text") or "").strip()
    if not text:
        return
    day = st.session_state.get("pin_day") if st.session_state.get("pin_has_day") else None
    execute("INSERT INTO pins (text, day, time, color, created) VALUES (?, ?, ?, ?, ?)",
            (text, day.isoformat() if day else None, (st.session_state.get("pin_time") or "").strip(),
             PIN_COLORS.index(st.session_state.get("pin_color", PIN_COLORS[0])), today_local().isoformat()))
    st.session_state.pin_text = ""
    st.session_state.pin_time = ""


def load_pins():
    df = query("SELECT * FROM pins")
    df["d"] = [date.fromisoformat(x) if isinstance(x, str) and x else None for x in df["day"]]
    df["time"] = df["time"].fillna("").astype(str)
    df["color"] = df["color"].fillna(0).astype(int)
    df["_sort"] = [x.toordinal() if x else 10 ** 7 for x in df["d"]]
    return df.sort_values(["_sort", "id"])


def own_reminders(today):
    """Open to-dos (and the evening 'plan tomorrow' nudge), shown on the reminder board of page 1."""
    items = []
    if now_local().hour >= 18 and load_todos("day", today + timedelta(days=1)).empty:
        items.append(("🌙", "Plan tomorrow", "Write tomorrow's to-dos tonight (Daily Planner) ✨", ""))
    todos = load_todos("day", today)
    open_todos = todos[todos["done"] == 0]
    if len(open_todos):
        names = ", ".join(html.escape(t) for t in open_todos["text"].head(3))
        more = f" +{len(open_todos) - 3}" if len(open_todos) > 3 else ""
        items.append(("📝", f"{len(open_todos)} to-do{'s' if len(open_todos) != 1 else ''} open",
                      names + more, ""))
    return items


def col_box(marker):
    """A single full-width column that gets styled as a colored box (via a hidden marker)."""
    col = st.columns([1])[0]
    col.markdown(f'<span class="{marker}"></span>', unsafe_allow_html=True)
    return col


def page_day():
    today = today_local()
    st.title("📝 Daily Planner")
    st.markdown(MYDAY_CSS, unsafe_allow_html=True)

    # ---------- Pinboard (top, full width) ----------
    pins = load_pins()
    with col_box("pin-mark"):
        soon_n = sum(1 for d in pins["d"] if d is not None and today <= d <= today + timedelta(days=1))
        badge = f'<span class="rem-count">{soon_n} coming up</span>' if soon_n else ""
        st.markdown(f'<div class="board-head"><span class="board-title">📌 My pinboard</span>{badge}</div>',
                    unsafe_allow_html=True)
        with st.expander("➕ Pin a new note"):
            st.text_input("Note", key="pin_text", placeholder="e.g. Doctor appointment, Mom's birthday 🎂")
            c1, c2, c3 = st.columns([1.2, 1, 1])
            c1.date_input("Date", value=today, key="pin_day", format="DD.MM.YYYY")
            c2.text_input("Time (optional)", key="pin_time", placeholder="10:00")
            c3.selectbox("Color", PIN_COLORS, key="pin_color")
            st.checkbox("📅 This note has a date", value=True, key="pin_has_day")
            st.button("📌 Pin it", on_click=add_pin)
        if pins.empty:
            st.markdown('<div class="board-empty">Nothing pinned yet. Appointments, ideas, little love notes… '
                        'pin them here 💌</div>', unsafe_allow_html=True)
        else:
            per_row = 4
            rows = [pins.iloc[i:i + per_row] for i in range(0, len(pins), per_row)]
            for row in rows:
                cols = st.columns(per_row)
                for col, p in zip(cols, row.itertuples()):
                    with col:
                        past = p.d is not None and p.d < today
                        soon = p.d is not None and today <= p.d <= today + timedelta(days=1)
                        when = ""
                        if p.d is not None:
                            when = (f'<div class="pin-when{" soon" if soon else ""}">📅 {nice_day(p.d, today)}'
                                    f'{" · " + html.escape(p.time) if p.time else ""}</div>')
                        st.markdown(f'<div class="pin-note n{int(p.color) % 5}{" past" if past else ""}'
                                    f'{" soon" if soon else ""}"><span class="pin-head">📍</span>'
                                    f'<div class="pin-text">{html.escape(p.text)}</div>{when}</div>',
                                    unsafe_allow_html=True)
                        st.button("✓ Done", key=f"del_pin_{p.id}", on_click=delete_row, args=("pins", p.id))

    st.write("")

    # ---------- To-do list (pink box) ----------
    with col_box("todo-mark"):
        todos = load_todos("day", today)
        n, done = len(todos), int(todos["done"].sum()) if len(todos) else 0
        msg = ("Fresh page, fresh start ✨" if n == 0 else
               "All done! You absolute legend 🎉" if done == n else
               f"{done} of {n} done · keep going 💪")
        st.markdown(f'<div class="box-title">✅ To-do list</div>'
                    f'<div class="day-date">{WEEKDAYS[today.weekday()]}, {MONTHS[today.month - 1]} {today.day}</div>'
                    f'<div class="todo-bar"><div class="todo-fill" style="width:{(done / n * 100) if n else 0:.0f}%">'
                    f'</div></div><div class="todo-meta">{msg}</div>', unsafe_allow_html=True)
        todo_list("day", today, "Nothing planned yet. Add your first task below ✨")
        old_open = query("SELECT COUNT(*) AS n FROM todos WHERE kind = 'day' AND done = 0 AND day < ?",
                         (today.isoformat(),))["n"].iloc[0]
        if old_open:
            st.button(f"📦 Move {old_open} unfinished task{'s' if old_open != 1 else ''} from earlier to today",
                      on_click=carry_over, args=(today,))
        still_open = int((todos["done"] == 0).sum()) if len(todos) else 0
        if still_open and now_local().hour >= 17:
            st.button(f"➡️ Move {still_open} unfinished task{'s' if still_open != 1 else ''} to tomorrow",
                      on_click=move_to_tomorrow, args=(today,), key="to_tomorrow")

    # ---------- Tomorrow (night-sky box) ----------
    st.write("")
    tomorrow = today + timedelta(days=1)
    with col_box("tomorrow-mark"):
        planned = load_todos("day", tomorrow)
        n_t = len(planned)
        sub = (f"{n_t} task{'s' if n_t != 1 else ''} ready · future you says thank you 💜" if n_t else
               "Plan tonight, glide through tomorrow ✨")
        st.markdown(f'<div class="box-title">🌙 Tomorrow</div>'
                    f'<div class="day-date tomorrow-date">{WEEKDAYS[tomorrow.weekday()]}, '
                    f'{MONTHS[tomorrow.month - 1]} {tomorrow.day}</div>'
                    f'<div class="todo-meta">{sub}</div>'
                    f'<span class="star s1">✦</span><span class="star s2">✧</span><span class="star s3">✦</span>',
                    unsafe_allow_html=True)
        todo_list("day", tomorrow, "Nothing planned for tomorrow yet. What do you want to get done?")

    # ---------- Weekend corner (sunset box, at the bottom) ----------
    st.write("")
    with col_box("weekend-mark"):
        sat = (today + timedelta(days=5 - today.weekday()) if today.weekday() < 5
               else today - timedelta(days=today.weekday() - 5))
        days_left = (sat - today).days
        count = ("It's the weekend! Enjoy every second 🎉" if today.weekday() >= 5 else
                 "Tomorrow is the weekend! 🥳" if days_left == 1 else
                 f"{days_left} more days until the weekend ✨")
        dots = "".join(f'<span class="wdot{" on" if i < 5 - days_left else ""}"></span>' for i in range(5)) \
            if today.weekday() < 5 else ""
        st.markdown(f'<div class="box-title">🌴 Weekend corner</div>'
                    f'<div class="weekend-count">{count}</div><div class="wdots">{dots}</div>',
                    unsafe_allow_html=True)
        todo_list("weekend", sat, "Brunch? Movie night? Spa day? Plan something nice 💅")


# ============================================================
# Page: My Week
# ============================================================
def page_week():
    st.title("🌷 Daily Habit Garden")
    habits = load_habits()
    entries = load_entries()
    today = today_local()

    if habits.empty:
        st.info("No habits yet. Add your first one under **🎀 Manage habits**. 💕")
        return

    st.markdown(habit_css(habits), unsafe_allow_html=True)
    st.markdown(GRID_CSS, unsafe_allow_html=True)
    values = dict(zip(zip(entries["habit_id"], entries["day"]), entries["value"]))
    planned_today = [h for h in habits.itertuples() if is_on(h, today)]
    today_done = sum(1 for h in planned_today if values.get((h.id, today), 0) >= h.target)

    # --- Lazy mode strip/banner, garden, water + reminders, meme ---
    lazy_top(today)
    if today not in PAUSED:
        success_garden(habits, values, today)
    st.write("")
    left, right = st.columns([1, 1.35])
    with left:
        water_card()
    with right:
        reminders_box(habits, entries, values, today)
    if today not in PAUSED:
        meme_card(today_done, len(planned_today), today)

    # --- Week navigation ---
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.week_offset)
    days = [monday + timedelta(days=i) for i in range(7)]

    st.write("")
    n1, n2, n3, n4 = columns([1, 4, 1, 1.6])
    n1.button("◀", on_click=shift_week, args=(-1,), help="Previous week")
    n2.markdown(f'<div class="week-label">{MONTHS[days[0].month - 1]} {days[0].day} – '
                f'{MONTHS[days[-1].month - 1]} {days[-1].day}</div>',
                unsafe_allow_html=True)
    n3.button("▶", on_click=shift_week, args=(1,), help="Next week",
              disabled=st.session_state.week_offset >= 0)
    n4.button("Today", on_click=reset_week, disabled=st.session_state.week_offset == 0)

    st.write("")
    widths = [3.2] + [1] * 7 + [1.3]

    # --- Header row with weekdays ---
    head = columns(widths)
    head[0].markdown('<div class="grid-label"><b>Habit</b></div>', unsafe_allow_html=True)
    for i, d in enumerate(days):
        css = "today" if d == today else ("weekend" if d.weekday() >= 5 else "")
        head[i + 1].markdown(
            f'<div class="day-head {css}">{WEEKDAYS[d.weekday()]}<br><b>{d.day}</b></div>',
            unsafe_allow_html=True)
    head[-1].markdown('<div class="streak">Streak</div>', unsafe_allow_html=True)

    possible = done_total = 0
    status = category_status(habits, values, today)

    # --- One block per category, one row per habit ---
    for cat, icon in CATEGORIES.items():
        sub = habits[habits["category"] == cat]
        if sub.empty:
            continue
        if cat in status:
            got, need = status[cat]
            badge = f'<small class="{"ok" if got >= need else ""}">today {got}/{need}</small>'
        else:
            badge = '<small>rest day today 😴</small>'
        st.markdown(f'<div class="cat-head">{icon} {cat}{badge}</div>', unsafe_allow_html=True)

        for h in sub.itertuples():
            cols = columns(widths)
            cols[0].markdown(
                f'<div class="habit-pill" style="background:{h.color}33;'
                f' border-left:7px solid {h.color};">{h.emoji} {html.escape(h.name)}'
                f'{f"<small class=days-tag>{days_label(h.days)}</small>" if days_label(h.days) else ""}</div>',
                unsafe_allow_html=True)

            week_done = 0
            week_target = sum(1 for d in days if is_on(h, d))
            for i, d in enumerate(days):
                v = values.get((h.id, d), 0)
                done = v >= h.target
                future = d > today
                planned = is_on(h, d)
                if not future and planned:
                    possible += 1
                    done_total += int(done)
                if planned:
                    week_done += int(done)
                iso = d.isoformat()
                state = "on" if done else ("off" if planned else "rest")
                with cols[i + 1]:
                    box, styled = cell_container(f"{state}-{h.id}-{iso}")
                    on_label = "♥" if styled else HEARTS.get(h.color, "💗")
                    off_label = "♡" if planned else "·"
                    with box:
                        if h.kind == "binary" or future or not hasattr(st, "popover"):
                            st.button(on_label if done else off_label, key=f"b-{h.id}-{iso}",
                                      on_click=toggle, args=(h.id, d, 0 if done else 1),
                                      disabled=future)
                        else:
                            with st.popover(f"{v:g}" if v else off_label):
                                akey = f"a-{h.id}-{iso}"
                                st.number_input(f"{h.emoji} {h.name} on {d:%d.%m.}",
                                                min_value=0.0, value=float(v), step=1.0,
                                                key=akey, on_change=on_amount,
                                                args=(h.id, d, akey))
                                st.caption(f"Goal: {h.target:g} {h.unit}")

            streak = current_streak(done_days(entries, h), today, h)
            cols[-1].markdown(
                f'<div class="streak">🔥 {streak}<br><small>{week_done}/{week_target}</small></div>',
                unsafe_allow_html=True)

    st.write("")
    if possible:
        rate = done_total / possible
        msg = ("You're on fire, queen! 👑" if rate >= 0.8 else
               "Going really well! ✨" if rate >= 0.5 else
               "Every day is a fresh start 🌷")
        st.progress(rate, text=f"💖 {rate:.0%} of this week done · {msg}")

    today_bar(today_done, len(planned_today))


# ============================================================
# Page: Overview
# ============================================================
def ring_svg(rate, color):
    r = 36
    circ = 2 * 3.14159 * r
    off = circ * (1 - rate)
    return (f'<svg class="ring" viewBox="0 0 88 88">'
            f'<circle cx="44" cy="44" r="{r}" class="ring-bg"/>'
            f'<circle cx="44" cy="44" r="{r}" class="ring-fg" transform="rotate(-90 44 44)" '
            f'style="stroke:{color};stroke-dasharray:{circ:.1f};stroke-dashoffset:{off:.1f}"/>'
            f'<text x="44" y="50" text-anchor="middle" class="ring-txt">{rate:.0%}</text></svg>')


def pearl_chain(start, today, state):
    """A pearl necklace: every pearl is one day. state(d) -> (class, tooltip, inner)."""
    n = (today - start).days + 1
    size = 26 if n <= 35 else (17 if n <= 100 else 11)
    parts = []
    d, i = start, 0
    while d <= today:
        if d == start or d.day == 1:
            parts.append(f'<span class="mlabel">{MONTHS[d.month - 1]}</span>')
        cls, tip, inner = state(d)
        if d == today:
            cls += " today"
        delay = f"animation-delay:{min(i * 18, 900)}ms" if n <= 100 else ""
        parts.append(f'<span class="{cls}" title="{tip}" style="{delay}">'
                     f'{inner if size > 11 else ""}</span>')
        d += timedelta(days=1)
        i += 1
    return f'<div class="pearls s{size}">{"".join(parts)}</div>'


def card(css_class, emoji, name, rate, color, stats, chain, delay):
    stat_html = "".join(f'<div class="hstat"><b>{b}</b><small>{s}</small></div>' for b, s in stats)
    return (f'<div class="hcard {css_class}" style="animation-delay:{delay}ms">'
            f'<div class="hhead"><span class="hemoji">{emoji}</span>{name}</div>'
            f'<div class="hbody">{ring_svg(rate, color)}<div class="hstats">{stat_html}</div></div>'
            f'{chain}</div>')


def page_overview():
    st.title("📊 Overview")
    habits = load_habits()
    entries = load_entries()
    today = today_local()

    if habits.empty:
        st.info("No habits yet.")
        return

    c1, c2 = st.columns([1, 2])
    period = c1.selectbox("Time range",
                          ["Last 7 days", "Last 30 days", "Last 90 days", "Last year", "All time"],
                          index=1)
    selected = c2.multiselect("Habits", habits["name"].tolist(),
                              default=habits["name"].tolist())
    habits = habits[habits["name"].isin(selected)]
    if habits.empty:
        return

    first_start = min(habit_start(h, entries) for h in habits.itertuples())
    start = {
        "Last 7 days": today - timedelta(days=6),
        "Last 30 days": today - timedelta(days=29),
        "Last 90 days": today - timedelta(days=89),
        "Last year": today - timedelta(days=364),
        "All time": first_start,
    }[period]

    values = dict(zip(zip(entries["habit_id"], entries["day"]), entries["value"]))
    sections, stats = {}, []
    for h in habits.itertuples():
        days = done_days(entries, h)
        h_start = max(start, habit_start(h, entries))
        planned = [h_start + timedelta(days=i) for i in range((today - h_start).days + 1)]
        planned = [d for d in planned if is_on(h, d)]
        total = len(planned)
        done_in = sum(1 for d in planned if d in days)
        rate = done_in / total if total > 0 else 0
        cur = current_streak(days, today, h)
        stats.append((h, rate, cur, done_in, total))

        def state(d, h=h):
            v = values.get((h.id, d), 0)
            if v >= h.target:
                return "p on", f"{d:%d.%m.%Y}: done 💖", "♥"
            if d in PAUSED:
                return "p rest", f"{d:%d.%m.%Y}: {LAZY[PAUSED[d]][1]} {LAZY[PAUSED[d]][0]}", ""
            if not is_on(h, d):
                return "p rest", f"{d:%d.%m.%Y}: rest day", ""
            if v:
                return "p part", f"{d:%d.%m.%Y}: {v:g} of {h.target:g} {html.escape(h.unit or '')}", ""
            return "p", f"{d:%d.%m.%Y}: not done", ""

        sections.setdefault(h.category, []).append(card(
            f"hc-{h.id}", h.emoji, html.escape(h.name), rate, h.color,
            [(f"🔥 {cur}", "current streak"), (f"🏅 {longest_streak(days, h)}", "longest streak"),
             (f"{done_in}/{total}", "days done")],
            pearl_chain(h_start, today, state), len(stats) * 70))

    # --- Summary on top ---
    all_done = sum(s[3] for s in stats)
    all_total = sum(s[4] for s in stats)
    best = max(stats, key=lambda s: s[2])
    st.markdown(
        f'<div class="summary"><span>💖 Overall <b>{all_done / all_total:.0%}</b> done</span>'
        f'<span>🔥 Best current streak: <b>{best[0].emoji} {html.escape(best[0].name)}</b> ({best[2]} days)</span>'
        f'<span>✨ <b>{all_done}</b> check marks collected</span></div>',
        unsafe_allow_html=True)

    colors = "".join(f".hc-{h.id}{{--c:{h.color};--cl:{h.color}30;--cl2:{h.color}55;"
                     f"--t:{text_color_on(h.color)}}}" for h in habits.itertuples())
    colors += ".hc-water{--c:#93c5fd;--cl:#93c5fd30;--cl2:#93c5fd55;--t:#5b2a4e}"
    body = ""
    for cat, icon in CATEGORIES.items():
        if cat in sections:
            body += f'<div class="sec">{icon} {cat}</div><div class="hgrid">{"".join(sections[cat])}</div>'

    # --- Water card ---
    water = load_water()
    goal = water_goal()
    if water:
        w_start = max(start, min(water))
        total = (today - w_start).days + 1
        in_range = [water.get(w_start + timedelta(days=i), 0) for i in range(total)]
        hit = sum(1 for ml in in_range if ml >= goal)
        streak, d = 0, today if water.get(today, 0) >= goal else today - timedelta(days=1)
        while water.get(d, 0) >= goal:
            streak += 1
            d -= timedelta(days=1)

        def wstate(d):
            ml = water.get(d, 0)
            if ml >= goal:
                return "p on", f"{d:%d.%m.%Y}: {fmt_liters(ml)} L 💧", "💧"
            if ml:
                return "p part", f"{d:%d.%m.%Y}: {fmt_liters(ml)} L", ""
            return "p", f"{d:%d.%m.%Y}: no water logged", ""

        body += ('<div class="sec">💧 Water</div><div class="hgrid">' + card(
            "hc-water", "💧", f"Water ({fmt_liters(goal)} L a day)", hit / total, "#93c5fd",
            [(f"🔥 {streak}", "days in a row"), (f"{fmt_liters(sum(in_range) / total)} L", "average a day"),
             (f"{hit}/{total}", "goal reached")],
            pearl_chain(w_start, today, wstate), 0) + "</div>")

    legend = ('<div class="legend"><span><span class="p on">♥</span> done</span>'
              '<span><span class="p part"></span> partly</span>'
              '<span><span class="p"></span> not done</span>'
              '<span><span class="p rest"></span> rest day</span></div>')
    st.markdown(f'<style>{colors}</style>{body}{legend}', unsafe_allow_html=True)

    # --- Ranking ---
    medals = ["🥇", "🥈", "🥉"]
    rows = []
    for i, (h, rate, *_rest) in enumerate(sorted(stats, key=lambda s: -s[1])):
        rows.append(
            f'<div class="rrow hc-{h.id}"><span>{medals[i] if i < 3 else "🌷"}</span>'
            f'<span class="rname">{h.emoji} {html.escape(h.name)}</span>'
            f'<div class="rtrack"><div class="rfill" style="width:{rate * 100:.0f}%;'
            f'animation-delay:{i * 120}ms"></div></div>'
            f'<span class="rpct">{rate:.0%}</span></div>')
    st.markdown(f'<div class="rank"><div class="sec" style="margin-top:0">🏆 Your habit ranking</div>'
                f'{"".join(rows)}</div>', unsafe_allow_html=True)


# ============================================================
# Page: Manage habits
# ============================================================
def color_choice(label, current=None, key=None):
    """Choose from the palette; an older custom color stays selectable."""
    options = dict(PALETTE)
    if current and current not in options.values():
        options["🎨 Current color"] = current
    names = list(options)
    index = names.index(next(n for n, c in options.items() if c == current)) if current else 1
    choice = st.selectbox(label, names, index=index, key=key)
    return options[choice]


def emoji_choice(label, current=None, key=None):
    options = list(EMOJIS)
    if current and current not in options:
        options.insert(0, current)
    return st.selectbox(label, options, index=options.index(current) if current else 0, key=key)


def category_choice(label, current="Other", key=None):
    names = list(CATEGORIES)
    return st.selectbox(label, names, index=names.index(current) if current in names else len(names) - 1,
                        format_func=lambda c: f"{CATEGORIES[c]} {c}", key=key)


def days_code(picked):
    """["Mon", "Wed"] -> "02"; nothing picked means every day."""
    code = "".join(str(WEEKDAYS.index(d)) for d in WEEKDAYS if d in picked)
    return code or "0123456"


def move_habit(habit_id, direction):
    habits = load_habits(include_archived=True)
    cat = habits.loc[habits["id"] == habit_id, "category"].iloc[0]
    order = habits.loc[habits["category"] == cat, "id"].tolist()
    i = order.index(habit_id)
    j = i + direction
    if 0 <= j < len(order):
        order[i], order[j] = order[j], order[i]
        for pos, hid in enumerate(order):
            execute("UPDATE habits SET position = ? WHERE id = ?", (pos, int(hid)))


def page_manage():
    st.title("🎀 Manage habits")

    st.subheader("✨ New habit")
    with st.form("new_habit", clear_on_submit=True):
        c0, c1, c2 = st.columns([1, 2, 2])
        with c0:
            emoji = emoji_choice("Emoji", key="new_emoji")
        name = c1.text_input("Name", placeholder="e.g. Yoga, Reading, Stretching")
        with c2:
            category = category_choice("Category", key="new_cat")
        kind = st.radio("Type", ["Yes/No", "Amount"], horizontal=True)
        c3, c4, c5 = st.columns(3)
        target = c3.number_input("Daily goal (amount only)", min_value=0.1, value=1.0)
        unit = c4.text_input("Unit (amount only)", placeholder="e.g. minutes")
        with c5:
            color = color_choice("Color", key="new_color")
        picked = st.multiselect("Days", WEEKDAYS, default=WEEKDAYS, key="new_days",
                                help="Only on these days. Other days are rest days and never count as missed.")
        if st.form_submit_button("💖 Add"):
            if name.strip():
                is_binary = kind == "Yes/No"
                execute(
                    "INSERT INTO habits (name, kind, unit, target, color, created, emoji, category, days, position) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(position), 0) + 1 FROM habits))",
                    (name.strip(), "binary" if is_binary else "amount",
                     "" if is_binary else unit.strip(),
                     1 if is_binary else target, color, today_local().isoformat(), emoji, category,
                     days_code(picked)))
                st.success(f"{emoji} \"{name.strip()}\" added!")
            else:
                st.warning("Please enter a name.")

    st.subheader("🌷 Your habits")
    habits = load_habits(include_archived=True)
    if habits.empty:
        st.caption("No habits yet.")
    for h in habits.itertuples():
        title = (f"{CATEGORIES[h.category]} {h.emoji} {h.name}"
                 + (f"  ·  {days_label(h.days)}" if days_label(h.days) else "")
                 + ("  (archived)" if h.archived else ""))
        with st.expander(title):
            with st.form(f"edit_{h.id}"):
                c0, c1, c2 = st.columns([1, 2, 2])
                with c0:
                    new_emoji = emoji_choice("Emoji", h.emoji, key=f"emoji_{h.id}")
                new_name = c1.text_input("Name", h.name)
                with c2:
                    new_cat = category_choice("Category", h.category, key=f"cat_{h.id}")
                c3, c4, c5 = st.columns(3)
                with c5:
                    new_color = color_choice("Color", h.color, key=f"color_{h.id}")
                if h.kind == "amount":
                    new_target = c3.number_input("Daily goal", min_value=0.1, value=float(h.target))
                    new_unit = c4.text_input("Unit", h.unit or "")
                else:
                    new_target, new_unit = 1, ""
                    c3.caption("Type: Yes/No")
                new_days = st.multiselect("Days", WEEKDAYS, key=f"days_{h.id}",
                                          default=[WEEKDAYS[int(c)] for c in h.days])
                archived = st.checkbox("Archived (hidden, data is kept)", value=bool(h.archived))
                if st.form_submit_button("💾 Save"):
                    execute("UPDATE habits SET name=?, target=?, unit=?, color=?, archived=?, "
                            "emoji=?, category=?, days=? WHERE id=?",
                            (new_name.strip() or h.name, new_target, new_unit,
                             new_color, int(archived), new_emoji, new_cat, days_code(new_days), h.id))
                    st.rerun()

            confirm = st.checkbox("I want to delete this habit and all its entries for good",
                                  key=f"confirm_{h.id}")
            if st.button("🗑️ Delete", key=f"del_{h.id}", disabled=not confirm):
                execute("DELETE FROM entries WHERE habit_id = ?", (h.id,))
                execute("DELETE FROM habits WHERE id = ?", (h.id,))
                st.rerun()

    st.subheader("↕️ Order of your habits")
    st.caption("Use the arrows to move a habit up or down inside its category.")
    active = load_habits()
    for cat, icon in CATEGORIES.items():
        sub = active[active["category"] == cat]
        if sub.empty:
            continue
        st.markdown(f'<div class="cat-head">{icon} {cat}</div>', unsafe_allow_html=True)
        for i, h in enumerate(sub.itertuples()):
            c1, c2, c3 = columns([6, 1, 1])
            c1.markdown(f'<div class="habit-pill sort-row" style="background:{h.color}33;'
                        f'border-left:7px solid {h.color};">{h.emoji} {html.escape(h.name)}'
                        f'<span class="sort-mark"></span></div>', unsafe_allow_html=True)
            c2.button("↑", key=f"up_{h.id}", on_click=move_habit, args=(h.id, -1), disabled=i == 0)
            c3.button("↓", key=f"down_{h.id}", on_click=move_habit, args=(h.id, 1),
                      disabled=i == len(sub) - 1)

    st.subheader("💧 Water goal")
    with st.form("water_goal"):
        liters = st.number_input("Daily goal in liters", min_value=0.5, max_value=6.0, step=0.25,
                                 value=water_goal() / 1000)
        if st.form_submit_button("💾 Save"):
            set_setting("water_goal_ml", liters * 1000)
            st.success("Saved!")

    st.subheader("💾 Backup")
    export = query("""
        SELECT h.name AS habit, h.category, e.day AS date, e.value AS value
        FROM entries e JOIN habits h ON h.id = e.habit_id
        ORDER BY e.day, h.name""")
    st.download_button("⬇️ Download all habit entries (CSV)",
                       export.to_csv(index=False).encode("utf-8"),
                       file_name=f"habits_backup_{today_local().isoformat()}.csv",
                       mime="text/csv")
    water_export = query("SELECT day AS date, ml FROM water ORDER BY day")
    st.download_button("⬇️ Download water log (CSV)",
                       water_export.to_csv(index=False).encode("utf-8"),
                       file_name=f"water_backup_{today_local().isoformat()}.csv",
                       mime="text/csv")


def phone_url():
    """The address your phone can use (same Wi-Fi as this PC)."""
    import socket
    try:
        s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_.connect(("8.8.8.8", 80))  # no data is sent, this only finds the Wi-Fi address
        ip = s_.getsockname()[0]
        s_.close()
    except OSError:
        return None
    port = st.get_option("server.port") or 8501
    return f"http://{ip}:{port}"


def tailscale_url():
    """Tailscale gives this PC a private address (100.64.x.x - 100.127.x.x) reachable from anywhere."""
    import socket
    try:
        ips = {info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
    except OSError:
        return None
    for ip in ips:
        parts = ip.split(".")
        if parts[0] == "100" and 64 <= int(parts[1]) <= 127:
            return f"http://{ip}:{st.get_option('server.port') or 8501}"
    return None


def qr_svg(url):
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        return None
    svg = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=8).to_string().decode("utf-8")
    svg = svg[svg.find("<svg"):].replace("<svg", '<svg style="width:170px;height:170px;background:#fff;'
                                           'border-radius:14px;padding:6px"', 1)
    return f'<div style="text-align:center">{svg}</div>'


def phone_box():
    home, anywhere = phone_url(), tailscale_url()
    if not home and not anywhere:
        return
    with st.expander("📱 Open on your phone"):
        for title, hint, url in [("🏡 At home", "Phone in the same Wi-Fi as this PC:", home),
                                 ("🌍 Anywhere", "With Tailscale switched on on your phone:", anywhere)]:
            if not url:
                continue
            st.markdown(f"**{title}**")
            st.caption(hint)
            svg = qr_svg(url)
            if svg:
                st.markdown(svg, unsafe_allow_html=True)
            st.code(url, language=None)
        if not anywhere:
            st.caption("🌍 Want to use it outside too? Install Tailscale on this PC and your phone.")
        if not qr_svg("x"):
            st.caption("(For QR codes: pip install qrcode)")


# ============================================================
# Start
# ============================================================
if ON_STREAMLIT_CLOUD and not CLOUD_URL:
    st.error("⚠️ The online database is not connected, so nothing would be saved. "
             "Please add TURSO_DATABASE_URL and TURSO_AUTH_TOKEN under Manage app → Settings → Secrets.")
    st.stop()
if CLOUD_URL:
    try:
        init_db_once()
    except Exception as e:
        st.error(f"⚠️ Could not reach the online database ({type(e).__name__}). "
                 "Please check the URL and token in the secrets, then reload.")
        st.stop()   # online: only once per app start, keeps it fast
else:
    init_db()
PAUSED.update(load_pauses())
st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(FUN_CSS, unsafe_allow_html=True)

st.sidebar.title("🌸 Habit Tracker")
page = st.sidebar.radio("Navigation", ["🌷 Daily Habit Garden", "📝 Daily Planner", "📊 Overview", "🎀 Manage habits"],
                        label_visibility="collapsed")
st.sidebar.caption("Small steps, big glow-up ✨")
st.sidebar.caption("☁️ Saved online (Turso)" if CLOUD_URL else "💻 Saved on this PC only")
with st.sidebar:
    affirmation_card(today_local())
    rules_box()
    st.write("")
    themes = ["☀️ Light", "🌙 Dark", "✨ Auto (dark in the evening)"]
    if st.session_state.get("theme") not in themes:
        saved = get_setting("theme", themes[2])
        st.session_state.theme = saved if saved in themes else themes[2]
    st.selectbox("Look", themes, key="theme",
                 on_change=lambda: set_setting("theme", st.session_state.theme))
    theme = st.session_state.theme
    hour = now_local().hour
    is_dark = theme == themes[1] or (theme == themes[2] and (hour >= 19 or hour < 7))
    if is_dark:
        st.markdown(DARK_CSS, unsafe_allow_html=True)
    elif today_local() in PAUSED:
        st.markdown(lazy_theme_css(PAUSED[today_local()]), unsafe_allow_html=True)
    if not CLOUD_URL:
        phone_box()

if page == "🌷 Daily Habit Garden":
    page_week()
elif page == "📝 Daily Planner":
    page_day()
elif page == "📊 Overview":
    page_overview()
else:
    page_manage()
