#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║     AI MAGAZINE ENGINE 2026                                     ║
║     All Exams • All Students • Zero Manual Design               ║
║     Dell 8GB Local + GitHub Codespaces Cloud Fallback           ║
║     Brand details loaded from brand.json — see that file        ║
╚══════════════════════════════════════════════════════════════════╝

USAGE:
  python auto_smart_pdf.py today.txt output.pdf
  python auto_smart_pdf.py today.txt output.pdf --theme dark
  python auto_smart_pdf.py today.txt output.pdf --theme sepia
  python auto_smart_pdf.py today.txt output.pdf --no-ai

OPTIONAL ENV VARS (cloud fallback):
  export GROQ_API_KEY=your_key
  export GEMINI_API_KEY=your_key

TODAY.TXT HEADER FIELDS (optional, top 15 lines):
  title: BIOLOGY CAPSULE 2026
  subtitle: NEET Special Edition
  difficulty: 9
"""

import sys
import re
import os
import json
import random
import argparse
import time
from pathlib import Path
from datetime import datetime

import requests
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, TextStringObject
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("ℹ️  pypdf not installed. Run: pip install pypdf  (needed for --batch / --merge)")

# ── Ollama: optional, graceful fallback ───────────────────────
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("ℹ️  Ollama not installed. Run: pip install ollama")


# ══════════════════════════════════════════════════════════════
# BRAND CONFIG LOADER
# ══════════════════════════════════════════════════════════════
_BRAND_DEFAULTS = {
    "org_name":        "YOUR ORGANISATION NAME",
    "org_short":       "YOUR ORG",
    "tagline":         "YOUR TAGLINE HERE",
    "website":         "www.tryiteducations.net",
    "email":           "contact@tryiteducations.net",
    "phone":           "+91-XXXXXXXXXX",
    "address":         "Your City, India",
    "copyright":       f"© {datetime.now().year} Your Organisation. All rights reserved.",
    "social_youtube":  "",
    "social_telegram": "",
    "social_instagram":"",
    "logo_path":       "",
    "logo_alt_text":   "Organisation Logo",
    "editor_name":     "Editorial Team",
    "legal_line":      "This material is for educational purposes only.",
    "cover_series":    "PREMIUM EDITION",
    "header_line":     "INDIA'S PREMIER EXAM INTELLIGENCE MAGAZINE",
    "footer_left":     "YOUR TAGLINE",
    "footer_right":    "www.tryiteducations.net",
    "print_notice":    "Published by Your Organisation, India.",
    "disclaimer":      "All exam names are trademarks of their respective conducting bodies.",
}


def load_brand(brand_file='brand.json'):
    """
    Load brand.json from the same folder as the script.
    Falls back to defaults with a clear warning if file is missing.
    """
    brand_path = Path(__file__).parent / brand_file
    if not brand_path.exists():
        print(f"⚠️  brand.json not found at {brand_path}")
        print("   Create brand.json with your organisation details.")
        print("   Using placeholder defaults for now.\n")
        return dict(_BRAND_DEFAULTS)

    try:
        with open(brand_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # Merge with defaults so missing keys never cause KeyErrors
        merged = dict(_BRAND_DEFAULTS)
        merged.update({k: v for k, v in raw.items() if not k.startswith('_')})
        print(f"✅ Brand loaded: {merged['org_name']} | {merged['website']}")
        return merged
    except Exception as e:
        print(f"⚠️  brand.json parse error: {e}. Using defaults.")
        return dict(_BRAND_DEFAULTS)


# Load brand at module level — available everywhere in the script
BRAND = load_brand()


# ══════════════════════════════════════════════════════════════
# EXAM REGISTRY
# ══════════════════════════════════════════════════════════════
EXAM_REGISTRY = {
    'SSC':       {'color': '#1a3b5d', 'badge': 'SSC CGL/CHSL/MTS'},
    'UPSC':      {'color': '#2d6a4f', 'badge': 'UPSC CSE/IAS'},
    'BANKING':   {'color': '#6b21a8', 'badge': 'SBI/IBPS/RBI'},
    'RAILWAY':   {'color': '#b45309', 'badge': 'RRB NTPC/ALP'},
    'NEET':      {'color': '#be123c', 'badge': 'NEET UG/PG'},
    'JEE':       {'color': '#0e7490', 'badge': 'JEE Main/Advanced'},
    'STATE':     {'color': '#4d7c0f', 'badge': 'State PSC'},
    'DEFENCE':   {'color': '#1e3a5f', 'badge': 'NDA/CDS/AFCAT'},
    'TEACHING':  {'color': '#7c2d12', 'badge': 'CTET/TET/DSSSB'},
    'INSURANCE': {'color': '#374151', 'badge': 'LIC/NICL/OICL'},
}

# ══════════════════════════════════════════════════════════════
# COLOUR THEMES
# ══════════════════════════════════════════════════════════════
THEMES = {
    'light': {
        'bg':             '#ffffff',
        'text':           '#2d3748',
        'heading':        '#1a3b5d',
        'subheading':     '#2a6d9c',
        'table_head':     '#1a3b5d',
        'table_head_text':'#ffffff',
        'box_border':     '#2a6d9c',
        'box_bg':         '#f0f7ff',
        'accent':         '#2a6d9c',
        'accent2':        '#c9a84c',
        'muted':          '#718096',
        'rule':           '#e2e8f0',
        'highlight_bg':   '#fffbeb',
        'callout_bg':     '#f0fdf4',
    },
    'dark': {
        'bg':             '#0f172a',
        'text':           '#e2e8f0',
        'heading':        '#93c5fd',
        'subheading':     '#60a5fa',
        'table_head':     '#1e3a5f',
        'table_head_text':'#ffffff',
        'box_border':     '#3b82f6',
        'box_bg':         '#1e2d45',
        'accent':         '#60a5fa',
        'accent2':        '#fbbf24',
        'muted':          '#94a3b8',
        'rule':           '#1e3a5f',
        'highlight_bg':   '#1c1917',
        'callout_bg':     '#052e16',
    },
    'sepia': {
        'bg':             '#fdf8f0',
        'text':           '#44332a',
        'heading':        '#7c3d12',
        'subheading':     '#a0522d',
        'table_head':     '#7c3d12',
        'table_head_text':'#fdf8f0',
        'box_border':     '#cd853f',
        'box_bg':         '#fef9ee',
        'accent':         '#a0522d',
        'accent2':        '#2d6a4f',
        'muted':          '#8c7b6b',
        'rule':           '#e8d5bb',
        'highlight_bg':   '#fffdf5',
        'callout_bg':     '#f0faf0',
    },
}

MOTIVATIONAL_QUOTES = [
    ("உழைப்பே உயர்வு தரும்.",
     "Tamil — Hard work alone brings elevation."),
    ("मेहनत कभी बेकार नहीं जाती।",
     "Hindi — Hard work is never wasted."),
    ("Success is not final; failure is not fatal. It is the courage to continue that counts.",
     "Winston Churchill"),
    ("The secret of getting ahead is getting started.",
     "Mark Twain"),
    ("An investment in knowledge pays the best interest.",
     "Benjamin Franklin"),
    ("Education is the most powerful weapon to change the world.",
     "Nelson Mandela"),
    ("Arise, awake and do not stop until the goal is reached.",
     "Swami Vivekananda"),
    ("You are never too old to set another goal or dream a new dream.",
     "C.S. Lewis"),
]

SECTION_EMOJIS = {
    'current affairs': '🌐',
    'economy':         '📈',
    'history':         '🏛️',
    'geography':       '🗺️',
    'science':         '🔬',
    'polity':          '⚖️',
    'mathematics':     '🔢',
    'reasoning':       '🧠',
    'english':         '📖',
    'biology':         '🧬',
    'physics':         '⚡',
    'chemistry':       '⚗️',
    'default':         '📌',
}

# ══════════════════════════════════════════════════════════════
# AI ENRICHMENT — Ollama → Groq → Gemini → raw passthrough
# ══════════════════════════════════════════════════════════════
AI_SYSTEM_PROMPT = """
You are the Chief Editor of India's most premium competitive exam magazine.
Transform raw study notes into structured magazine content.

ABSOLUTE OUTPUT RULES — ZERO EXCEPTIONS:
1. Output ONLY plain text. ZERO markdown (no ##, **, ```, -, *, _).
2. ZERO introductory sentences. Start directly with content.
3. Use ALL CAPS single lines for section headings.
4. Detect exam relevance and add exam tags like [SSC] [UPSC] [NEET] inline.

VISUAL TRIGGER FORMATS — use EXACTLY as shown:
Image-Hero: Exact person or landmark name
Image-Inline: Exact concept or object name
3D-Bar: Chart Title | Label1: 45%, Label2: 30%, Label3: 25%
Donut-Chart: Chart Title | Label1: 45%, Label2: 30%, Label3: 25%
Timeline: Title
YEAR | Event Title | One clear description sentence
Table: Title
Column1 | Column2 | Column3
Data1 | Data2 | Data3
Mnemonic: Short Title | Full memory phrase here
Highlight: The exact key fact or formula to emphasize
Callout: EXAM ALERT | Key information students must not miss
Fact-Box: Title | Fact1 ;; Fact2 ;; Fact3
Crossword: Title Here
ACROSS: 1. Clue one (ANSWER) ;; 3. Clue three (ANSWER)
DOWN: 2. Clue two (ANSWER)
MCQ-Start
Q1. Full question text here?
A) Option one
B) Option two
C) Option three
D) Option four
Answer: A
Explanation: One precise explanatory sentence.
MCQ-End

CONTENT QUALITY RULES:
- Break every dense paragraph with at least one visual trigger.
- Every 3+ data points must become a 3D-Bar or Table.
- Every chronological sequence must become a Timeline.
- Every memory trick must use Mnemonic.
- Inject Image-Hero before any famous person, landmark, or record.
- Add [SSC] [UPSC] [BANKING] [NEET] [JEE] [RAILWAY] tags to every MCQ.
- MICRO-LEARNING RULE: prefer short, single-line, scannable points over
  thick paragraphs. Keep each sentence under ~18 words where possible.
  Do NOT add manual bullet characters (no ▪, •, -, *) — plain text lines
  only. The layout engine adds bullet markers automatically.

Output the complete structured text now. Zero preamble.
"""


def ai_enrich_raw_text(raw_text):
    """
    Attempt enrichment in order:
      1. Local Ollama Llama3 (Dell 8GB)
      2. Groq API free tier   (GROQ_API_KEY env var)
      3. Gemini API           (GEMINI_API_KEY env var)
      4. Return raw text unchanged
    """
    # ── 1. Local Ollama ───────────────────────────────────────
    if OLLAMA_AVAILABLE:
        try:
            print("🧠 [1/3] Trying local Ollama Llama3...")
            resp = ollama.chat(
                model='llama3',
                messages=[
                    {'role': 'system', 'content': AI_SYSTEM_PROMPT},
                    {'role': 'user',   'content': raw_text},
                ],
                options={'temperature': 0.3, 'num_predict': 4096},
            )
            print("✅ Local AI enrichment complete.")
            return resp['message']['content']
        except Exception as e:
            print(f"⚠️  Ollama failed: {e}")

    # ── 2. Groq API ───────────────────────────────────────────
    groq_key = os.environ.get('GROQ_API_KEY', '')
    if groq_key:
        try:
            print("🌐 [2/3] Trying Groq cloud API...")
            resp = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {groq_key}',
                    'Content-Type':  'application/json',
                },
                json={
                    'model': 'llama3-8b-8192',
                    'messages': [
                        {'role': 'system', 'content': AI_SYSTEM_PROMPT},
                        {'role': 'user',   'content': raw_text},
                    ],
                    'temperature': 0.3,
                    'max_tokens':  4096,
                },
                timeout=30,
            )
            print("✅ Groq cloud enrichment complete.")
            return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"⚠️  Groq failed: {e}")

    # ── 3. Gemini API ─────────────────────────────────────────
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            print("🌐 [3/3] Trying Gemini API...")
            url = (
                'https://generativelanguage.googleapis.com'
                f'/v1beta/models/gemini-pro:generateContent?key={gemini_key}'
            )
            resp = requests.post(
                url,
                json={'contents': [{'parts': [
                    {'text': AI_SYSTEM_PROMPT + '\n\n' + raw_text}
                ]}]},
                timeout=30,
            )
            print("✅ Gemini enrichment complete.")
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"⚠️  Gemini failed: {e}")

    print("📋 All AI bridges offline. Running direct parse mode.")
    return raw_text


# ══════════════════════════════════════════════════════════════
# PLACEHOLDER IMAGE (offline-safe branded card)
# ══════════════════════════════════════════════════════════════
def generate_placeholder_image(label, output_dir='.'):
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('#1a3b5d')
    ax.set_facecolor('#1a3b5d')
    ax.text(0.5, 0.58, label.upper(),
            transform=ax.transAxes, fontsize=14, color='white',
            ha='center', va='center', fontweight='bold')
    ax.text(0.5, 0.38, BRAND['org_name'],
            transform=ax.transAxes, fontsize=9, color='#90cdf4',
            ha='center', va='center', alpha=0.85)
    ax.text(0.5, 0.22, BRAND['website'],
            transform=ax.transAxes, fontsize=7, color='#63b3ed',
            ha='center', va='center', alpha=0.6)
    ax.axis('off')
    fname = f"placeholder_{random.randint(10000, 99999)}.png"
    plt.savefig(
        os.path.join(output_dir, fname),
        dpi=150, bbox_inches='tight',
        facecolor='#1a3b5d', edgecolor='none',
    )
    plt.close()
    return fname


# ══════════════════════════════════════════════════════════════
# MEDIA FETCH — keyword map + picsum fallback + placeholder
# ══════════════════════════════════════════════════════════════
# NOTE: All URLs below are plain strings — no markdown wrapping.
KEYWORD_MAP = {
    'bolt':         'https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?auto=format&fit=crop&w=800&q=80',
    'sprint':       'https://images.unsplash.com/photo-1530549387789-4c1017266635?auto=format&fit=crop&w=800&q=80',
    'oscar':        'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=800&q=80',
    'award':        'https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80',
    'space':        'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=800&q=80',
    'science':      'https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&w=800&q=80',
    'economy':      'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80',
    'india':        'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80',
    'constitution': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80',
    'exam':         'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=800&q=80',
    'math':         'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80',
    'history':      'https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=800&q=80',
    'technology':   'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
    'biology':      'https://images.unsplash.com/photo-1530026405186-ed1f139313f8?auto=format&fit=crop&w=800&q=80',
    'physics':      'https://images.unsplash.com/photo-1636466497217-26a8cbeaf0aa?auto=format&fit=crop&w=800&q=80',
    'chemistry':    'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=800&q=80',
    'railway':      'https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=800&q=80',
    'bank':         'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?auto=format&fit=crop&w=800&q=80',
    'defence':      'https://images.unsplash.com/photo-1547483238-2cbf881a559f?auto=format&fit=crop&w=800&q=80',
    'court':        'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80',
    'geography':    'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80',
    'environment':  'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=800&q=80',
    'health':       'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=800&q=80',
    'agriculture':  'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80',
}


# Module-level cache: same query across multiple batch files
# re-uses the already-downloaded image instead of re-fetching.
_IMAGE_CACHE = {}


def fetch_magazine_media(query, output_dir='.'):
    """Fetch image from Unsplash keyword map, picsum seed, or branded placeholder.
    Caches by (query, output_dir) so repeated topics in batch runs don't
    re-download the same photo over and over."""
    cache_key = (query.lower().strip(), output_dir)
    if cache_key in _IMAGE_CACHE:
        cached_path = os.path.join(output_dir, _IMAGE_CACHE[cache_key])
        if os.path.exists(cached_path):
            return _IMAGE_CACHE[cache_key]

    try:
        clean = query.lower().strip()
        url = next((v for k, v in KEYWORD_MAP.items() if k in clean), None)
        if not url:
            seed = abs(hash(clean)) % 1000
            url = f"https://picsum.photos/seed/{seed}/800/500"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            fname = f"media_{random.randint(10000, 99999)}.jpg"
            with open(os.path.join(output_dir, fname), 'wb') as f:
                f.write(r.content)
            _IMAGE_CACHE[cache_key] = fname
            return fname
    except Exception as e:
        print(f"⚠️  Image fetch failed for '{query}': {e}")

    placeholder = generate_placeholder_image(query, output_dir)
    _IMAGE_CACHE[cache_key] = placeholder
    return placeholder


# ══════════════════════════════════════════════════════════════
# 3D BAR CHART
# ══════════════════════════════════════════════════════════════
BAR_COLORS = ['#1a3b5d', '#2a6d9c', '#c9a84c', '#2d6a4f', '#be123c', '#7c3d12']


def generate_3d_chart(title, data_str, theme_name='light', output_dir='.'):
    """Parse 'Label1: 45%, Label2: 30%' and render a 3D bar chart."""
    labels, values = [], []
    try:
        for pair in data_str.split(','):
            if ':' not in pair:
                continue
            k, v = pair.split(':', 1)
            labels.append(k.strip())
            values.append(float(v.replace('%', '').replace(' ', '').strip()))
    except Exception as e:
        print(f"⚠️  Chart parse error: {e}")
        return None
    if not labels:
        return None

    theme = THEMES.get(theme_name, THEMES['light'])
    fig = plt.figure(figsize=(7, 4.2), facecolor=theme['bg'])
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor(theme['bg'])

    xpos = np.arange(len(labels))
    ypos = np.zeros(len(labels))
    zpos = np.zeros(len(labels))
    dx   = 0.6 * np.ones(len(labels))
    dy   = 0.5 * np.ones(len(labels))
    bar_colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(len(labels))]

    ax.bar3d(xpos, ypos, zpos, dx, dy, values,
             color=bar_colors, alpha=0.88, shade=True,
             edgecolor='white', linewidth=0.3)

    # FIX: Labels sit directly on top of bars (y=0.25, not 0.6)
    max_v = max(values) if values else 1
    for xi, zi in zip(xpos + 0.3, values):
        ax.text(xi, 0.25, zi + (max_v * 0.02),
                f'{zi:.0f}%',
                color=theme['text'], fontsize=7.5,
                ha='center', va='bottom', fontweight='600')

    ax.set_xticks(xpos + 0.3)
    ax.set_xticklabels(labels, color=theme['text'],
                       fontsize=8.5, rotation=20, ha='right', fontweight='500')
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_title(title.upper(), fontsize=10, color=theme['heading'],
                 fontweight='700', pad=18, loc='left')
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)
    ax.grid(False)

    plt.tight_layout(pad=1.5)
    fname = f"chart_{random.randint(10000, 99999)}.png"
    plt.savefig(os.path.join(output_dir, fname),
                dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return fname


# ══════════════════════════════════════════════════════════════
# DONUT CHART
# ══════════════════════════════════════════════════════════════
def generate_donut_chart(title, data_str, theme_name='light', output_dir='.'):
    """Parse 'Label1: 45%, Label2: 30%' and render a donut chart."""
    labels, values = [], []
    try:
        for pair in data_str.split(','):
            if ':' not in pair:
                continue
            k, v = pair.split(':', 1)
            labels.append(k.strip())
            values.append(float(v.replace('%', '').strip()))
    except Exception as e:
        print(f"⚠️  Donut parse error: {e}")
        return None
    if not labels:
        return None

    theme = THEMES.get(theme_name, THEMES['light'])
    fig, ax = plt.subplots(figsize=(5, 3.5))
    fig.patch.set_facecolor(theme['bg'])
    ax.set_facecolor(theme['bg'])

    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        autopct='%1.0f%%',
        colors=BAR_COLORS[:len(labels)],
        startangle=90,
        wedgeprops={'width': 0.55, 'edgecolor': theme['bg'], 'linewidth': 2},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_color('white')
        at.set_fontsize(8)
        at.set_fontweight('bold')

    ax.legend(wedges, labels,
              loc='center left', bbox_to_anchor=(0.85, 0.5),
              fontsize=7.5, frameon=False, labelcolor=theme['text'])
    ax.set_title(title.upper(), fontsize=9, color=theme['heading'],
                 fontweight='700', pad=10)
    plt.tight_layout()
    fname = f"donut_{random.randint(10000, 99999)}.png"
    plt.savefig(os.path.join(output_dir, fname),
                dpi=200, facecolor=theme['bg'], edgecolor='none')
    plt.close()
    return fname


# ══════════════════════════════════════════════════════════════
# MCQ PARSER
# ══════════════════════════════════════════════════════════════
def parse_mcq_block(block):
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if not lines:
        return None

    q_text = lines[0]
    q_text = re.sub(r'^(?:Q|Question)\s*\d+\s*[.:\)]\s*', '', q_text, flags=re.IGNORECASE).strip()
    q_text = re.sub(r'^\d+\s*[.:\)]\s*', '', q_text).strip()
    if not q_text:
        return None

    opt_re = re.compile(r'^([A-D])\s*[.)]\s*(.+)', re.IGNORECASE)
    options, answer, explanation, exam_tags = [], None, None, []

    for line in lines[1:]:
        m = opt_re.match(line)
        if m:
            options.append(f"{m.group(1).upper()}) {m.group(2).strip()}")
            continue
        if re.match(r'^(?:answer|ans)\s*[:.]?\s*[A-D]', line, re.IGNORECASE):
            hit = re.search(r'([A-D])', line, re.IGNORECASE)
            if hit:
                answer = hit.group(1).upper()
        elif re.match(r'^(?:explanation|exp)\s*[:.]', line, re.IGNORECASE):
            exp_hit = re.search(r'[:.]\s*(.+)', line)
            if exp_hit:
                explanation = exp_hit.group(1).strip()
        for exam in EXAM_REGISTRY:
            if f'[{exam}]' in line.upper():
                exam_tags.append(exam)

    if len(options) >= 2:
        return {
            'question':    q_text,
            'options':     options[:4],
            'answer':      answer or '',
            'explanation': explanation or '',
            'exams':       exam_tags or ['SSC', 'UPSC'],
        }
    return None


# ══════════════════════════════════════════════════════════════
# FACT-BOX PARSER
# ══════════════════════════════════════════════════════════════
def parse_fact_box(line):
    content = line.replace('Fact-Box:', '').strip()
    if '|' not in content:
        return None
    title, facts_raw = content.split('|', 1)
    facts = [f.strip() for f in facts_raw.split(';;') if f.strip()]
    return {'title': title.strip(), 'facts': facts}


def parse_crossword_clue_line(line, label):
    """
    Parse a single 'ACROSS: 1. Clue (ANSWER) ;; 3. Clue (ANSWER)' line.
    Returns a list of {'num': str, 'clue': str, 'answer': str} dicts.
    """
    content = line.split(':', 1)[1].strip() if ':' in line else line.strip()
    clues = []
    for raw in content.split(';;'):
        raw = raw.strip()
        if not raw:
            continue
        # Match: "1. Clue text (ANSWER)"
        m = re.match(r'^(\d+)\s*[.)]\s*(.+?)\s*\(([A-Za-z\s]+)\)\s*$', raw)
        if m:
            clues.append({
                'num':    m.group(1).strip(),
                'clue':   m.group(2).strip(),
                'answer': m.group(3).strip().upper(),
            })
        else:
            # Fallback: no parenthesised answer found — keep clue, blank answer
            num_m = re.match(r'^(\d+)\s*[.)]\s*(.+)$', raw)
            if num_m:
                clues.append({
                    'num':    num_m.group(1).strip(),
                    'clue':   num_m.group(2).strip(),
                    'answer': '',
                })
    return clues


def build_crossword_html(title, across_clues, down_clues, grid_size=9):
    """
    Renders a crossword block: a simple placeholder square grid on the left,
    ACROSS/DOWN clue columns listed on the right.
    """
    grid_cells = ''.join(
        '<div class="xw-cell"></div>' for _ in range(grid_size * grid_size)
    )
    grid_html = (
        f'<div class="xw-grid" style="grid-template-columns: repeat({grid_size}, 1fr);">'
        f'{grid_cells}</div>'
    )

    def render_clue_list(clues, label):
        if not clues:
            return ''
        items = ''.join(
            f'<li><span class="xw-num">{c["num"]}.</span> {c["clue"]}</li>'
            for c in clues
        )
        return (
            f'<div class="xw-clue-group">'
            f'<div class="xw-clue-label">{label}</div>'
            f'<ul class="xw-clue-list">{items}</ul>'
            f'</div>'
        )

    clues_html = (
        render_clue_list(across_clues, 'ACROSS')
        + render_clue_list(down_clues, 'DOWN')
    )

    return (
        f'<div class="crossword-container">'
        f'<div class="xw-header">🧩 {title.upper()}</div>'
        f'<div class="xw-body">'
        f'<div class="xw-grid-pane">{grid_html}</div>'
        f'<div class="xw-clues-pane">{clues_html}</div>'
        f'</div>'
        f'</div>'
    )


# ══════════════════════════════════════════════════════════════
# MASTER PARSER
# ══════════════════════════════════════════════════════════════
TRIGGER_PREFIXES = [
    '3D-Bar:', 'Donut-Chart:', 'Table:', 'Timeline:',
    'Image-', 'Mnemonic:', 'Highlight:', 'Callout:',
    'Fact-Box:', 'Crossword:', 'MCQ-Start', 'MCQ-End',
]


def auto_parse(text, theme_name='light', output_dir='.'):
    lines        = text.splitlines()
    mcqs         = []
    sections     = []
    raw_body     = []
    in_mcq_block = False
    mcq_buffer   = []
    i            = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # ── MCQ block delimiters ───────────────────────────────
        if line == 'MCQ-Start':
            in_mcq_block = True
            mcq_buffer   = []
            i += 1
            continue

        if line == 'MCQ-End':
            in_mcq_block = False
            if mcq_buffer:
                block_text = '\n'.join(mcq_buffer)
                chunks = re.split(
                    r'(?=(?:Q|Question)\s*\d+)', block_text, flags=re.IGNORECASE
                )
                for chunk in chunks:
                    chunk = chunk.strip()
                    if chunk:
                        q = parse_mcq_block(chunk)
                        if q:
                            mcqs.append(q)
            i += 1
            continue

        if in_mcq_block:
            mcq_buffer.append(line)
            i += 1
            continue

        # ── Image-Hero ─────────────────────────────────────────
        if line.startswith('Image-Hero:'):
            query = line.replace('Image-Hero:', '').strip()
            img   = fetch_magazine_media(query, output_dir)
            if img:
                raw_body.append(
                    f'<div class="hero-banner">'
                    f'<img src="{img}" alt="{query}" />'
                    f'<div class="hero-caption-bar">'
                    f'<span class="hero-caption-text">📷 {query.upper()}</span>'
                    f'</div></div>'
                )
            i += 1
            continue

        # ── Image-Inline ───────────────────────────────────────
        if line.startswith('Image-Inline:'):
            query = line.replace('Image-Inline:', '').strip()
            img   = fetch_magazine_media(query, output_dir)
            if img:
                raw_body.append(
                    f'<div class="inline-media">'
                    f'<img src="{img}" alt="{query}" />'
                    f'<span class="inline-caption">{query.upper()}</span>'
                    f'</div>'
                )
            i += 1
            continue

        # ── 3D Bar Chart ───────────────────────────────────────
        if line.startswith('3D-Bar:'):
            content = line.replace('3D-Bar:', '').strip()
            if '|' in content:
                parts = content.split('|', 1)
                try:
                    img = generate_3d_chart(
                        parts[0].strip(), parts[1].strip(), theme_name, output_dir
                    )
                    if img:
                        raw_body.append(
                            f'<div class="chart-wrap"><img src="{img}" /></div>'
                        )
                except Exception as e:
                    print(f"⚠️  3D chart error: {e}")
            i += 1
            continue

        # ── Donut Chart ────────────────────────────────────────
        if line.startswith('Donut-Chart:'):
            content = line.replace('Donut-Chart:', '').strip()
            if '|' in content:
                parts = content.split('|', 1)
                try:
                    img = generate_donut_chart(
                        parts[0].strip(), parts[1].strip(), theme_name, output_dir
                    )
                    if img:
                        raw_body.append(
                            f'<div class="chart-wrap"><img src="{img}" /></div>'
                        )
                except Exception as e:
                    print(f"⚠️  Donut chart error: {e}")
            i += 1
            continue

        # ── Timeline ───────────────────────────────────────────
        if line.startswith('Timeline:'):
            title   = line.replace('Timeline:', '').strip()
            t_lines = []
            j       = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if '|' not in nxt:
                    break
                if any(nxt.startswith(p) for p in TRIGGER_PREFIXES):
                    break
                t_lines.append(nxt)
                j += 1

            if t_lines:
                nodes = ''
                for idx_t, item in enumerate(t_lines):
                    parts  = item.split('|')
                    marker = parts[0].strip()
                    hdr    = parts[1].strip() if len(parts) >= 3 else 'KEY EVENT'
                    desc   = parts[-1].strip()
                    conn   = ('' if idx_t == len(t_lines) - 1
                              else '<div class="tl-line"></div>')
                    nodes += (
                        f'<div class="tl-node">'
                        f'<div class="tl-left">'
                        f'<span class="tl-badge">{marker}</span>{conn}'
                        f'</div>'
                        f'<div class="tl-right">'
                        f'<h4 class="tl-title">{hdr.upper()}</h4>'
                        f'<p class="tl-desc">{desc}</p>'
                        f'</div>'
                        f'</div>'
                    )
                raw_body.append(
                    f'<div class="timeline-wrap">'
                    f'<div class="timeline-header">📅 {title.upper()}</div>'
                    f'<div class="tl-track">{nodes}</div>'
                    f'</div>'
                )
                i = j
                continue

        # ── Table ──────────────────────────────────────────────
        if line.startswith('Table:'):
            title   = line.replace('Table:', '').strip()
            t_lines = []
            j       = i + 1
            while j < len(lines) and '|' in lines[j]:
                t_lines.append(lines[j].strip())
                j += 1

            if t_lines:
                heads = ''.join(
                    f'<th>{h.strip()}</th>' for h in t_lines[0].split('|')
                )
                # FIX: r is a plain string from t_lines — .split('|') is correct
                rows = ''.join(
                    f'<tr>{"".join(f"<td>{c.strip()}</td>" for c in r.split("|"))}</tr>'
                    for r in t_lines[1:]
                )
                raw_body.append(
                    f'<div class="table-wrap">'
                    f'<div class="table-title">📊 {title.upper()}</div>'
                    f'<table>'
                    f'<thead><tr>{heads}</tr></thead>'
                    f'<tbody>{rows}</tbody>'
                    f'</table>'
                    f'</div>'
                )
                i = j
                continue

        # ── Mnemonic ───────────────────────────────────────────
        if line.lower().startswith('mnemonic:'):
            parts   = line.split(':', 1)[1].split('|')
            title_m = parts[0].strip() if len(parts) >= 2 else 'Memory Key'
            body_m  = parts[-1].strip()
            raw_body.append(
                f'<div class="mnemonic-box">'
                f'<div class="mnemonic-badge">🧠 MNEMONIC</div>'
                f'<h4 class="mnemonic-title">{title_m.upper()}</h4>'
                f'<p class="mnemonic-body">{body_m}</p>'
                f'</div>'
            )
            i += 1
            continue

        # ── Highlight ──────────────────────────────────────────
        if line.lower().startswith('highlight:'):
            body_h = line.split(':', 1)[1].strip()
            raw_body.append(
                f'<div class="highlight-box">'
                f'<span class="hl-mark">❝</span>'
                f'<p class="hl-text">{body_h}</p>'
                f'</div>'
            )
            i += 1
            continue

        # ── Callout ────────────────────────────────────────────
        if line.lower().startswith('callout:'):
            parts  = line.split(':', 1)[1].split('|')
            tag_c  = parts[0].strip() if len(parts) >= 2 else 'IMPORTANT'
            body_c = parts[-1].strip()
            raw_body.append(
                f'<div class="callout-box">'
                f'<div class="callout-tag">⚡ {tag_c.upper()}</div>'
                f'<p class="callout-body">{body_c}</p>'
                f'</div>'
            )
            i += 1
            continue

        # ── Fact-Box ───────────────────────────────────────────
        if line.lower().startswith('fact-box:'):
            fb = parse_fact_box(line)
            if fb:
                facts_html = ''.join(f'<li>✦ {f}</li>' for f in fb['facts'])
                raw_body.append(
                    f'<div class="fact-box">'
                    f'<div class="fact-box-title">📌 {fb["title"].upper()}</div>'
                    f'<ul class="fact-list">{facts_html}</ul>'
                    f'</div>'
                )
            i += 1
            continue

        # ── Crossword ──────────────────────────────────────────
        # Format:
        #   Crossword: Title Here
        #   ACROSS: 1. Clue one (ANSWER) ;; 3. Clue three (ANSWER)
        #   DOWN: 2. Clue two (ANSWER)
        if line.startswith('Crossword:'):
            xw_title = line.replace('Crossword:', '').strip()
            across, down = [], []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt:
                    j += 1
                    continue
                if nxt.upper().startswith('ACROSS:'):
                    across = parse_crossword_clue_line(nxt, 'ACROSS')
                    j += 1
                    continue
                if nxt.upper().startswith('DOWN:'):
                    down = parse_crossword_clue_line(nxt, 'DOWN')
                    j += 1
                    continue
                # Stop at the next trigger or section heading
                break
            if across or down:
                raw_body.append(build_crossword_html(xw_title, across, down))
            i = j
            continue

        # ── Inline MCQ (without MCQ-Start/MCQ-End block) ──────
        # FIX: Pipe guard prevents timeline rows being swallowed
        is_q_prefix = bool(re.match(r'^\s*(?:Q|Question)\s*\d+', line, re.IGNORECASE))
        is_numbered_q = bool(
            re.match(r'^\s*\d+[.)]\s+.+\?', line) and '|' not in line
        )
        if is_q_prefix or is_numbered_q:
            m_lines = [line]
            j       = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt:
                    j += 1
                    continue
                stop = (
                    re.match(r'^\s*(?:Q|Question)\s*\d+', nxt, re.IGNORECASE)
                    or (len(nxt) < 60 and nxt.isupper())
                    or any(nxt.startswith(p) for p in TRIGGER_PREFIXES)
                )
                if stop:
                    break
                m_lines.append(nxt)
                j += 1
            q = parse_mcq_block('\n'.join(m_lines))
            if q:
                mcqs.append(q)
            i = j
            continue

        # ── Section heading detection ──────────────────────────
        is_heading = (
            len(line) < 80
            and line.isupper()
            and not any(line.upper().startswith(p.upper().rstrip(':')) for p in TRIGGER_PREFIXES)
        )
        if is_heading:
            emoji = next(
                (v for k, v in SECTION_EMOJIS.items() if k in line.lower()),
                SECTION_EMOJIS['default'],
            )
            sections.append(line)
            raw_body.append(f'<h1><span class="sec-emoji">{emoji}</span> {line}</h1>')
            i += 1
            continue

        # ── Regular paragraph with inline exam tags ────────────
        para = line

        # Strip any incoming manual bullet markers the AI/user may have typed
        # (▪, •, -, *, plus optional whitespace) so we never double them up.
        bullet_stripped = re.sub(r'^[▪•▶◆●○\-\*]\s+', '', para).strip()
        had_bullet_marker = bullet_stripped != para

        for exam, info in EXAM_REGISTRY.items():
            bullet_stripped = bullet_stripped.replace(
                f'[{exam}]',
                f'<span class="exam-tag" style="background:{info["color"]}">{exam}</span>',
            )

        # Treat as a micro-bullet point if it either had a manual marker,
        # or it's short enough to be a scannable one-liner (not a full paragraph).
        word_count = len(bullet_stripped.split())
        is_micro_point = had_bullet_marker or word_count <= 18

        if is_micro_point:
            raw_body.append(f'<p class="micro-bullet">{bullet_stripped}</p>')
        else:
            raw_body.append(f'<p>{bullet_stripped}</p>')
        i += 1

    return '\n'.join(raw_body), mcqs, sections


# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
def build_css(theme):
    # IMPORTANT: @import URL is a plain string — no markdown brackets
    google_fonts = (
        "https://fonts.googleapis.com/css2?"
        "family=Cinzel:wght@500;700"
        "&family=Inter:wght@300;400;500;600;700"
        "&family=Playfair+Display:ital,wght@0,500;0,700;1,400"
        "&display=swap"
    )
    return f"""
@import url('{google_fonts}');

@page {{
    size: A4;
    margin: 2.2cm 2cm 2.5cm 2cm;
    @bottom-center {{
        content: "✦  " counter(page) "  ✦";
        font-family: 'Playfair Display', serif;
        font-size: 9pt;
        color: {theme['muted']};
    }}
    @top-right {{
        content: "{BRAND['org_name']}  |  {BRAND['tagline']}";
        font-size: 6.5pt;
        letter-spacing: 1.5px;
        color: {theme['muted']};
        font-family: 'Inter', sans-serif;
    }}
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    background: {theme['bg']};
    color: {theme['text']};
    font-family: 'Inter', sans-serif;
    font-weight: 300;
    font-size: 10.5pt;
    line-height: 1.7;
}}

h1 {{
    font-family: 'Cinzel', serif;
    font-size: 16pt;
    font-weight: 700;
    letter-spacing: 2.5px;
    color: {theme['heading']};
    border-bottom: 2px solid {theme['accent']};
    padding-bottom: 8px;
    margin: 2em 0 0.8em 0;
    column-span: all;
    text-transform: uppercase;
}}
h1 .sec-emoji {{ margin-right: 8px; font-size: 14pt; }}

h2 {{
    font-family: 'Playfair Display', serif;
    font-size: 14pt;
    font-weight: 700;
    color: {theme['heading']};
    margin: 1.5em 0 0.6em 0;
    column-span: all;
    border-left: 4px solid {theme['accent2']};
    padding-left: 12px;
}}

h3 {{
    font-family: 'Inter', sans-serif;
    font-size: 10.5pt;
    font-weight: 600;
    color: {theme['subheading']};
    margin: 1.2em 0 0.4em 0;
}}

p {{
    text-align: justify;
    margin-bottom: 1em;
    line-height: 1.75;
    orphans: 2;
    widows: 2;
}}

/* Long-form paragraphs: keep them tight and scannable (~4 lines max feel) */
p:not(.micro-bullet) {{
    max-width: 100%;
}}

/* Micro-bullet one-liners: single clean ▪ marker, never doubled */
p.micro-bullet {{
    text-align: left;
    list-style: none;
    padding-left: 1.3em;
    position: relative;
    margin-bottom: 0.65em;
    line-height: 1.5;
}}
p.micro-bullet::before {{
    content: "▪";
    color: {theme['accent2']};
    position: absolute;
    left: 0;
    font-size: 0.9em;
}}

/* ── TWO-COLUMN BODY ── */
.magazine-columns {{
    column-count: 2;
    column-gap: 2.8em;
    column-fill: balance;
    column-rule: 1px solid {theme['rule']};
}}

/* ── PAGE-BREAK PROTECTION ── */
.hero-banner, .inline-media, .chart-wrap,
.timeline-wrap, .table-wrap, .mnemonic-box,
.highlight-box, .callout-box, .fact-box, .mcq-card {{
    break-inside: avoid;
    page-break-inside: avoid;
}}

/* ── HERO IMAGE ── */
.hero-banner {{
    column-span: all;
    margin: 2em 0 1em 0;
}}
.hero-banner img {{
    display: block;
    width: 100%;
    max-height: 360px;
    object-fit: cover;
    border-radius: 6px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}}
.hero-caption-bar {{
    margin-top: 6px;
    border-left: 3px solid {theme['accent']};
    padding-left: 8px;
}}
.hero-caption-text {{
    font-size: 7.5pt;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: {theme['muted']};
}}

/* ── INLINE IMAGE ── */
.inline-media img {{
    display: block;
    width: 100%;
    border-radius: 5px;
    margin: 1em 0 0.3em 0;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}}
.inline-caption {{
    font-size: 7pt;
    letter-spacing: 1px;
    color: {theme['muted']};
    display: block;
    margin-bottom: 1em;
}}

/* ── CHART ── */
.chart-wrap {{
    margin: 1.5em 0;
    text-align: center;
    column-span: all;
}}
.chart-wrap img {{
    width: 100%;
    max-width: 560px;
    height: auto;
    border-radius: 6px;
}}

/* ── TIMELINE ── */
.timeline-wrap {{
    margin: 2em 0;
    column-span: all;
    border: 1px solid {theme['rule']};
    border-radius: 8px;
    overflow: hidden;
}}
.timeline-header {{
    background: {theme['heading']};
    color: white;
    font-family: 'Cinzel', serif;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 10px 18px;
}}
.tl-track {{ padding: 16px 18px; }}
.tl-node  {{ display: flex; align-items: flex-start; gap: 16px; }}
.tl-left  {{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 72px;
}}
.tl-badge {{
    font-family: 'Cinzel', serif;
    font-size: 8pt;
    font-weight: 700;
    color: {theme['heading']};
    background: {theme['box_bg']};
    border: 1.5px solid {theme['accent']};
    border-radius: 4px;
    padding: 3px 8px;
    text-align: center;
    white-space: nowrap;
    width: 100%;
}}
.tl-line {{
    width: 1.5px;
    height: 36px;
    background: {theme['accent']};
    opacity: 0.3;
    margin: 4px 0;
}}
.tl-right  {{ padding-top: 2px; flex: 1; }}
.tl-title  {{
    font-size: 9pt;
    font-weight: 700;
    color: {theme['heading']};
    margin-bottom: 2px;
}}
.tl-desc {{
    font-size: 9.5pt;
    color: {theme['text']};
    margin-bottom: 14px;
    text-align: left;
}}

/* ── TABLE ── */
.table-wrap  {{ margin: 1.8em 0; column-span: all; }}
.table-title {{
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {theme['accent']};
    margin-bottom: 6px;
}}
table {{ width: 100%; border-collapse: collapse; font-size: 9.5pt; }}
th {{
    background: {theme['table_head']};
    color: {theme['table_head_text']};
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 10px 12px;
    text-align: left;
}}
td {{
    padding: 9px 12px;
    border-bottom: 1px solid {theme['rule']};
    vertical-align: top;
}}
tr:nth-child(even) td {{ background: {theme['box_bg']}; }}

/* ── MNEMONIC ── */
.mnemonic-box {{
    background: {theme['box_bg']};
    border-left: 4px solid {theme['accent']};
    border-radius: 0 6px 6px 0;
    padding: 16px 20px;
    margin: 1.5em 0;
}}
.mnemonic-badge {{
    font-size: 7pt;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {theme['accent']};
    margin-bottom: 5px;
}}
.mnemonic-title {{
    font-family: 'Playfair Display', serif;
    font-size: 10.5pt;
    color: {theme['heading']};
    margin-bottom: 5px;
}}
.mnemonic-body {{ font-size: 10pt; text-align: left; margin: 0; }}

/* ── HIGHLIGHT ── */
.highlight-box {{
    border-left: 3px solid {theme['accent2']};
    background: {theme['highlight_bg']};
    padding: 14px 20px;
    margin: 1.5em 0;
    border-radius: 0 6px 6px 0;
}}
.hl-mark {{
    font-family: 'Playfair Display', serif;
    font-size: 28pt;
    color: {theme['accent2']};
    line-height: 0;
    vertical-align: -12px;
    opacity: 0.45;
    margin-right: 4px;
}}
.hl-text {{
    display: inline;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 11pt;
    color: {theme['heading']};
    text-align: left;
}}

/* ── CALLOUT ── */
.callout-box {{
    background: {theme['callout_bg']};
    border: 1.5px solid {theme['box_border']};
    border-radius: 6px;
    padding: 14px 18px;
    margin: 1.5em 0;
}}
.callout-tag {{
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {theme['accent']};
    margin-bottom: 5px;
}}
.callout-body {{ font-size: 10pt; color: {theme['text']}; text-align: left; margin: 0; }}

/* ── FACT BOX ── */
.fact-box {{
    border: 1px solid {theme['rule']};
    border-top: 3px solid {theme['accent']};
    border-radius: 6px;
    padding: 14px 18px;
    margin: 1.5em 0;
    background: {theme['box_bg']};
}}
.fact-box-title {{
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {theme['accent']};
    margin-bottom: 8px;
}}
.fact-list {{ list-style: none; padding: 0; margin: 0; }}
.fact-list li {{
    font-size: 9.5pt;
    padding: 3px 0;
    border-bottom: 1px solid {theme['rule']};
    color: {theme['text']};
}}
.fact-list li:last-child {{ border-bottom: none; }}

/* ── CROSSWORD ── */
.crossword-container {{
    column-span: all;
    margin: 1.8em 0;
    border: 1px solid {theme['rule']};
    border-radius: 8px;
    overflow: hidden;
    break-inside: avoid;
    page-break-inside: avoid;
}}
.xw-header {{
    background: {theme['heading']};
    color: white;
    font-family: 'Cinzel', serif;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 10px 18px;
}}
.xw-body {{
    display: flex;
    gap: 20px;
    padding: 16px 18px;
}}
.xw-grid-pane {{ flex: 0 0 38%; }}
.xw-grid {{
    display: grid;
    gap: 1px;
    background: {theme['rule']};
    border: 1.5px solid {theme['accent']};
    aspect-ratio: 1 / 1;
}}
.xw-cell {{
    background: {theme['bg']};
    aspect-ratio: 1 / 1;
}}
.xw-clues-pane {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
}}
.xw-clue-label {{
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: {theme['accent']};
    margin-bottom: 4px;
}}
.xw-clue-list {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.xw-clue-list li {{
    font-size: 8.8pt;
    color: {theme['text']};
    padding: 2px 0;
    text-align: left;
}}
.xw-num {{
    font-weight: 700;
    color: {theme['heading']};
}}

/* ── MCQ CARDS ── */
.mcq-section-title {{
    font-family: 'Cinzel', serif;
    font-size: 15pt;
    color: {theme['heading']};
    border-bottom: 2px solid {theme['accent']};
    padding-bottom: 8px;
    margin-bottom: 1.5em;
    letter-spacing: 2px;
    column-span: all;
}}

/* High-contrast midnight workbook card — fixed dark palette,
   independent of page theme, so it always pops. */
.mcq-card {{
    column-span: all;
    background: #0f1729;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 22px 26px;
    margin: 0 0 1.4em 0;
    box-shadow: 0 6px 20px rgba(0,0,0,0.18);
}}
.mcq-header {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}}
.mcq-number {{
    font-family: 'Cinzel', serif;
    font-size: 11pt;
    font-weight: 700;
    color: #0f1729;
    background: #fbbf24;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}
.mcq-question {{
    font-size: 11pt;
    font-weight: 500;
    color: #f1f5f9;
    line-height: 1.65;
    flex: 1;
    margin: 0;
}}
.mcq-options {{
    list-style: none;
    padding: 0;
    margin: 0 0 14px 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}}
.mcq-options li {{
    font-size: 9.8pt;
    padding: 7px 12px;
    border-radius: 5px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.03);
    color: #cbd5e1;
    line-height: 1.5;
}}
.mcq-answer-block {{
    background: rgba(45,106,79,0.18);
    border-left: 3px solid #4ade80;
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin-top: 10px;
}}
.mcq-answer      {{ font-size: 9.5pt; font-weight: 700; color: #4ade80; margin-bottom: 4px; }}
.mcq-explanation {{ font-size: 9.5pt; color: #cbd5e1; font-style: italic; margin: 0; line-height: 1.55; }}
.exam-tags       {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }}
.exam-tag {{
    font-size: 6.5pt;
    font-weight: 700;
    color: white;
    padding: 3px 8px;
    border-radius: 3px;
    letter-spacing: 0.5px;
}}

/* ── COVER PAGE ── */
.cover-page {{
    height: 25.7cm;
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
}}
.cover-top-bar {{
    background: {theme['heading']};
    color: white;
    padding: 14px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.cover-top-brand {{
    font-family: 'Cinzel', serif;
    font-size: 11pt;
    letter-spacing: 3px;
    font-weight: 700;
}}
.cover-top-meta {{ font-size: 7.5pt; letter-spacing: 2px; opacity: 0.8; }}
.cover-hero-strip {{
    background: linear-gradient(135deg, {theme['heading']} 0%, {theme['subheading']} 100%);
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 40px 50px;
    text-align: center;
}}
.cover-issue-label {{
    font-size: 7.5pt;
    letter-spacing: 4px;
    color: rgba(255,255,255,0.6);
    margin-bottom: 20px;
    text-transform: uppercase;
}}
.cover-main-title {{
    font-family: 'Cinzel', serif;
    font-size: 44pt;
    font-weight: 700;
    color: white;
    letter-spacing: 8px;
    line-height: 1.1;
    margin-bottom: 16px;
    text-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.cover-gold-rule {{
    width: 80px;
    height: 3px;
    background: {theme['accent2']};
    margin: 0 auto 20px auto;
}}
.cover-subtitle {{
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 15pt;
    color: rgba(255,255,255,0.85);
    margin-bottom: 30px;
}}
.cover-tagline {{
    font-size: 8pt;
    letter-spacing: 3px;
    color: rgba(255,255,255,0.55);
    text-transform: uppercase;
}}
.cover-info-bar {{
    background: {theme['heading']};
    border-top: 1px solid rgba(255,255,255,0.1);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 16px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.cover-info-item {{ text-align: center; color: rgba(255,255,255,0.9); }}
.cover-info-label {{
    font-size: 6.5pt;
    letter-spacing: 2px;
    opacity: 0.8;
    display: block;
    margin-bottom: 2px;
}}
.cover-info-value {{
    font-family: 'Cinzel', serif;
    font-size: 11pt;
    font-weight: 700;
}}
.cover-exam-strip {{
    background: {theme['box_bg']};
    padding: 12px 30px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    justify-content: center;
    border-top: 2px solid {theme['rule']};
}}
.cover-exam-pill {{
    font-size: 7pt;
    font-weight: 700;
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}}
.cover-bottom-bar {{
    background: {theme['text']};
    color: white;
    padding: 10px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.cover-motto  {{ font-size: 8pt; letter-spacing: 2px; opacity: 0.7; }}
.cover-website {{ font-size: 8pt; font-weight: 600; letter-spacing: 1px; color: {theme['accent2']}; }}

/* ── GAUGE ── */
.gauge-block {{ display: flex; flex-direction: column; align-items: center; gap: 6px; }}
.gauge-ring {{
    width: 72px; height: 72px;
    border-radius: 50%;
    display: flex; justify-content: center; align-items: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}}
.gauge-inner {{
    width: 54px; height: 54px;
    background: {theme['heading']};
    border-radius: 50%;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
}}
.gauge-num   {{ font-family: 'Cinzel', serif; font-size: 14pt; font-weight: 700; color: white; line-height: 1; }}
.gauge-denom {{ font-size: 7pt; color: rgba(255,255,255,0.6); }}
.gauge-label {{ font-size: 6pt; letter-spacing: 1.5px; color: rgba(255,255,255,0.5); text-align: center; }}

/* ── TOC BOX ── */
.toc-box {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 6px;
    padding: 16px 20px;
    min-width: 200px;
}}
.toc-header {{
    font-size: 7pt; letter-spacing: 2px;
    color: rgba(255,255,255,0.5);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px; margin-bottom: 10px;
}}
.toc-item {{
    font-size: 8.5pt;
    color: rgba(255,255,255,0.8);
    padding: 3px 0;
    display: flex; gap: 8px; align-items: center;
}}
.toc-dot {{ color: {theme['accent2']}; font-size: 7pt; }}

/* ── END PAGE ── */
.end-page    {{ text-align: center; padding-top: 7cm; }}
.end-quote   {{
    font-family: 'Playfair Display', serif;
    font-style: italic; font-size: 14pt;
    color: {theme['accent']}; line-height: 1.7;
    max-width: 80%; margin: 0 auto 0.5em auto;
}}
.end-quote-src {{ font-size: 9pt; color: {theme['muted']}; margin-bottom: 2em; }}
.end-rule    {{ width: 60px; height: 1px; background: {theme['accent2']}; margin: 2em auto; }}
.end-logo    {{ font-family: 'Cinzel', serif; font-size: 14pt; letter-spacing: 4px; color: {theme['heading']}; }}
.end-tagline {{ font-size: 8pt; letter-spacing: 3px; color: {theme['muted']}; margin-top: 4px; }}
.end-close   {{ margin-top: 2em; font-size: 8pt; letter-spacing: 2px; color: {theme['muted']}; opacity: 0.5; }}
.end-contact {{ font-size: 9pt; color: {theme['accent']}; margin-top: 0.8em; font-weight: 600; }}
.end-copyright {{ font-size: 8pt; color: {theme['muted']}; margin-top: 1.5em; }}
.end-legal {{ font-size: 7pt; color: {theme['muted']}; opacity: 0.7; margin-top: 0.4em; max-width: 70%; margin-left: auto; margin-right: auto; line-height: 1.5; }}
"""


# ══════════════════════════════════════════════════════════════
# COVER PAGE HTML
# ══════════════════════════════════════════════════════════════
def build_cover(meta, theme, sections):
    diff      = meta.get('difficulty', 8)
    gauge_deg = int((diff / 10) * 360)

    toc_items = ''
    for s in sections[:8]:
        emoji = next(
            (v for k, v in SECTION_EMOJIS.items() if k in s.lower()),
            '📌',
        )
        toc_items += (
            f'<div class="toc-item">'
            f'<span class="toc-dot">✦</span>'
            f'{emoji} {s[:40]}'
            f'</div>'
        )
    if not toc_items:
        toc_items = (
            '<div class="toc-item">'
            '<span class="toc-dot">✦</span>📌 COMPLETE STUDY BRIEFING'
            '</div>'
        )

    exam_pills = ''.join(
        f'<span class="cover-exam-pill" style="background:{info["color"]}">'
        f'{info["badge"]}</span>'
        for info in EXAM_REGISTRY.values()
    )

    title    = meta.get('title', 'TRYIT BRIEFINGS')
    subtitle = meta.get('subtitle', 'Curated Knowledge Compendium')
    issue    = datetime.now().strftime('%m/%Y')
    month    = datetime.now().strftime('%B %Y').upper()
    dated    = datetime.now().strftime('%d %b %Y').upper()
    n_exams  = len(EXAM_REGISTRY)

    # Logo: use real image if provided in brand.json, else text wordmark
    logo_html = (
        f'<img src="{BRAND["logo_path"]}" alt="{BRAND["logo_alt_text"]}" '
        f'style="height:28px;" />'
        if BRAND.get('logo_path') else
        f'{BRAND["org_name"]}'
    )

    return f"""
<div class="cover-page">

  <div class="cover-top-bar">
    <div class="cover-top-brand">{logo_html}</div>
    <div class="cover-top-meta">
      {issue} &nbsp;•&nbsp; {month} &nbsp;•&nbsp; {BRAND['cover_series']}
    </div>
  </div>

  <div class="cover-hero-strip">
    <div class="cover-issue-label">
      ◈ &nbsp; {BRAND['header_line']} &nbsp; ◈
    </div>
    <div class="cover-main-title">{title}</div>
    <div class="cover-gold-rule"></div>
    <div class="cover-subtitle">{subtitle}</div>
    <div class="cover-tagline">{BRAND['tagline']}</div>

    <div style="display:flex; gap:40px; margin-top:32px; align-items:flex-start;">
      <div class="gauge-block">
        <div class="gauge-ring"
             style="background: conic-gradient(#c9a84c {gauge_deg}deg, rgba(255,255,255,0.1) 0deg);">
          <div class="gauge-inner">
            <span class="gauge-num">{diff}</span>
            <span class="gauge-denom">/10</span>
          </div>
        </div>
        <span class="gauge-label">DEPTH<br>RATING</span>
      </div>
      <div class="toc-box">
        <div class="toc-header">IN THIS EDITION</div>
        {toc_items}
      </div>
    </div>
  </div>

  <div class="cover-info-bar">
    <div class="cover-info-item">
      <span class="cover-info-label">PLATFORM</span>
      <span class="cover-info-value">AI-POWERED</span>
    </div>
    <div class="cover-info-item">
      <span class="cover-info-label">EXAMS COVERED</span>
      <span class="cover-info-value">{n_exams}+ STREAMS</span>
    </div>
    <div class="cover-info-item">
      <span class="cover-info-label">EDITION DATE</span>
      <span class="cover-info-value">{dated}</span>
    </div>
    <div class="cover-info-item">
      <span class="cover-info-label">FORMAT</span>
      <span class="cover-info-value">PRINT-GRADE</span>
    </div>
  </div>

  <div class="cover-exam-strip">{exam_pills}</div>

  <div class="cover-bottom-bar">
    <div class="cover-motto">{BRAND['footer_left']}</div>
    <div class="cover-website">{BRAND['website']} &nbsp;•&nbsp; {BRAND['email']}</div>
  </div>

</div>
<div style="page-break-after: always;"></div>
"""


# ══════════════════════════════════════════════════════════════
# MCQ SECTION HTML
# ══════════════════════════════════════════════════════════════
def build_mcq_section(mcqs, theme):
    if not mcqs:
        return ''

    html  = '<div style="page-break-before: always;"></div>'
    html += '<h2 class="mcq-section-title">📚 Practice Questions Bank</h2>'
    html += '<div class="magazine-columns">'

    for idx, q in enumerate(mcqs, 1):
        opts_html = ''.join(f'<li>{o}</li>' for o in q['options'])

        ans_html = ''
        if q['answer'] or q['explanation']:
            inner = ''
            if q['answer']:
                inner += f'<div class="mcq-answer">✅ Answer: {q["answer"]}</div>'
            if q['explanation']:
                inner += f'<p class="mcq-explanation">💡 {q["explanation"]}</p>'
            ans_html = f'<div class="mcq-answer-block">{inner}</div>'

        tags_html = ''
        if q.get('exams'):
            pills = ''.join(
                f'<span class="exam-tag"'
                f' style="background:{EXAM_REGISTRY.get(e, {"color": "#374151"})["color"]}">'
                f'{e}</span>'
                for e in q['exams']
            )
            tags_html = f'<div class="exam-tags">{pills}</div>'

        html += (
            f'<div class="mcq-card">'
            f'<div class="mcq-header">'
            f'<div class="mcq-number">{idx}</div>'
            f'<p class="mcq-question">{q["question"]}</p>'
            f'</div>'
            f'<ul class="mcq-options">{opts_html}</ul>'
            f'{ans_html}'
            f'{tags_html}'
            f'</div>'
        )

    html += '</div>'
    return html


# ══════════════════════════════════════════════════════════════
# MASTER PIPELINE
# ══════════════════════════════════════════════════════════════
def generate_pdf_from_raw(raw_file, output_pdf=None, theme_name='light', skip_ai=False):
    start = time.time()
    print(f"\n{'=' * 60}")
    print(f"  {BRAND['org_name']} — AI MAGAZINE ENGINE")
    print(f"  Input : {raw_file}")
    print(f"  Theme : {theme_name.upper()}")
    print(f"{'=' * 60}\n")

    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Step 1 — AI enrichment
    enriched = raw_text if skip_ai else ai_enrich_raw_text(raw_text)
    if skip_ai:
        print("⏩ Skipping AI enrichment (--no-ai flag)")

    # Step 2 — Dynamic metadata from top-15 lines of RAW text
    meta = {
        'difficulty': 8,
        'title':      'TRYIT BRIEFINGS',
        'subtitle':   'Curated Knowledge Compendium',
        'theme':      theme_name,
    }
    skip_keys = ['3D-Bar:', 'Table:', 'Timeline:', 'Image-', 'Mnemonic:',
                 'Highlight:', 'Callout:', 'Fact-Box:']
    for raw_line in raw_text.splitlines()[:15]:
        if ':' not in raw_line:
            continue
        if any(raw_line.startswith(sk) for sk in skip_keys):
            continue
        k_raw, v_raw = raw_line.split(':', 1)
        k = k_raw.strip().lower()
        v = v_raw.strip()
        if k in ('title', 'subtitle'):
            meta[k] = v
        elif k == 'difficulty':
            try:
                meta['difficulty'] = max(1, min(10, int(v)))
            except ValueError:
                pass

    # Step 3 — Parse enriched text into HTML components
    theme    = THEMES[theme_name]
    work_dir = str(Path(raw_file).parent)
    processed_body, mcqs, sections = auto_parse(enriched, theme_name, work_dir)
    print(f"📊 Parsed: {len(sections)} sections | {len(mcqs)} MCQs")

    # Step 4 — Assemble full HTML
    cover       = build_cover(meta, theme, sections)
    mcq_section = build_mcq_section(mcqs, theme)
    quote, src  = random.choice(MOTIVATIONAL_QUOTES)

    end_page = (
        '<div style="page-break-before: always;"></div>'
        '<div class="end-page">'
        f'<div class="end-quote">{quote}</div>'
        f'<div class="end-quote-src">— {src}</div>'
        '<div class="end-rule"></div>'
        f'<div class="end-logo">{BRAND["org_name"]}</div>'
        f'<div class="end-tagline">{BRAND["tagline"]}</div>'
        f'<div class="end-contact">'
        f'{BRAND["website"]} &nbsp;•&nbsp; {BRAND["email"]}'
        + (f' &nbsp;•&nbsp; {BRAND["phone"]}' if BRAND.get("phone") and "X" not in BRAND["phone"] else '')
        + '</div>'
        f'<div class="end-copyright">{BRAND["copyright"]}</div>'
        f'<div class="end-legal">{BRAND["legal_line"]}</div>'
        f'<div class="end-legal">{BRAND["disclaimer"]}</div>'
        '<div class="end-close">END OF EDITION</div>'
        '</div>'
    )

    css = build_css(theme)

    full_html = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        f'  <title>{BRAND["org_name"]} — Magazine Edition</title>\n'
        f'  <style>{css}</style>\n'
        '</head>\n'
        '<body>\n'
        f'  {cover}\n'
        f'  <div class="magazine-columns">{processed_body}</div>\n'
        f'  {mcq_section}\n'
        f'  {end_page}\n'
        '</body>\n'
        '</html>'
    )

    # Step 5 — Compile PDF
    if not output_pdf:
        output_pdf = str(Path(raw_file).with_suffix('.pdf'))

    print("🖨️  Compiling PDF with WeasyPrint...")
    font_config = FontConfiguration()
    doc = HTML(string=full_html, base_url=work_dir).render(font_config=font_config)
    page_count = len(doc.pages)
    doc.write_pdf(str(output_pdf))

    elapsed = time.time() - start
    print(f"\n✅ Done in {elapsed:.1f}s")
    print(f"📄 Output: {output_pdf}  ({page_count} pages)\n")

    return {
        'output_pdf':  str(output_pdf),
        'page_count':  page_count,
        'mcq_count':   len(mcqs),
        'sections':    sections,
        'title':       meta.get('title', 'Untitled'),
        'elapsed_sec': elapsed,
    }


# ══════════════════════════════════════════════════════════════
# BATCH / MERGE ENGINE
# For weekly→monthly mega compilations and 200+ MCQ all-exam packs.
# Generates each input file separately (isolating failures), then
# merges into one PDF with a clickable master TOC and continuous
# page numbering.
# ══════════════════════════════════════════════════════════════
def build_master_toc_pdf(entries, brand, theme_name='light'):
    """
    entries: list of dicts with 'title', 'page_count', 'mcq_count', 'start_page'
    Returns a path to a small standalone TOC PDF to prepend to the merge.
    """
    theme = THEMES[theme_name]
    rows = ''
    for e in entries:
        rows += (
            f'<tr>'
            f'<td>{e["title"]}</td>'
            f'<td style="text-align:center;">{e["mcq_count"]}</td>'
            f'<td style="text-align:center;">{e["page_count"]}</td>'
            f'<td style="text-align:center;">{e["start_page"]}</td>'
            f'</tr>'
        )

    css = build_css(theme)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
<div style="padding: 1cm;">
  <h1>📑 MASTER TABLE OF CONTENTS</h1>
  <p>This compilation contains {len(entries)} merged sections.
  Use the page numbers below to navigate directly.</p>
  <table>
    <thead>
      <tr><th>Section / File</th><th>MCQs</th><th>Pages</th><th>Starts At Page</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
</body></html>"""

    font_config = FontConfiguration()
    return HTML(string=html).render(font_config=font_config)


def run_batch(input_files, output_pdf, theme_name='light', skip_ai=False,
              brand_file='brand.json'):
    """
    Generates a PDF for each input file (failures isolated — one bad file
    doesn't stop the others), then merges everything into one mega PDF
    with continuous page numbers and a master TOC up front.
    """
    if not PYPDF_AVAILABLE:
        print("❌ pypdf is required for batch mode. Run: pip install pypdf")
        return

    print(f"\n{'=' * 60}")
    print(f"  BATCH MODE — {len(input_files)} file(s) to process")
    print(f"{'=' * 60}\n")

    results   = []
    failures  = []
    temp_pdfs = []

    for idx, fpath in enumerate(input_files, 1):
        print(f"\n--- [{idx}/{len(input_files)}] Processing: {fpath} ---")
        temp_out = f"{Path(fpath).stem}_batch_{idx}.pdf"
        try:
            meta = generate_pdf_from_raw(fpath, temp_out, theme_name, skip_ai)
            results.append(meta)
            temp_pdfs.append(temp_out)
        except Exception as e:
            print(f"❌ FAILED on {fpath}: {e}")
            print(f"   Skipping this file — continuing with the rest of the batch.")
            failures.append((fpath, str(e)))
            continue

    if not temp_pdfs:
        print("\n❌ All files failed. No PDF was produced.")
        return

    # Build TOC entries with running page offsets
    toc_entries  = []
    running_page = 2  # page 1 reserved for the TOC itself
    for meta in results:
        toc_entries.append({
            'title':      meta['title'],
            'mcq_count':  meta['mcq_count'],
            'page_count': meta['page_count'],
            'start_page': running_page,
        })
        running_page += meta['page_count']

    print(f"\n🧩 Merging {len(temp_pdfs)} PDFs into final mega compilation...")
    writer = PdfWriter()

    # TOC first
    toc_doc = build_master_toc_pdf(toc_entries, BRAND, theme_name)
    toc_bytes = toc_doc.write_pdf()
    import io
    toc_reader = PdfReader(io.BytesIO(toc_bytes))
    for page in toc_reader.pages:
        writer.add_page(page)

    # Then each generated PDF, in order, with a bookmark per section
    for meta, temp_pdf in zip(results, temp_pdfs):
        reader = PdfReader(temp_pdf)
        start_index = len(writer.pages)
        for page in reader.pages:
            writer.add_page(page)
        writer.add_outline_item(meta['title'], start_index)

    with open(output_pdf, 'wb') as f:
        writer.write(f)

    total_pages = len(writer.pages)

    # Cleanup temp files
    for tp in temp_pdfs:
        try:
            os.remove(tp)
        except OSError:
            pass

    print(f"\n{'=' * 60}")
    print(f"✅ BATCH COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Files succeeded : {len(results)}/{len(input_files)}")
    if failures:
        print(f"  Files failed    : {len(failures)}")
        for fpath, err in failures:
            print(f"    - {fpath}: {err}")
    print(f"  Total MCQs      : {sum(m['mcq_count'] for m in results)}")
    print(f"  Total pages     : {total_pages}")
    print(f"  Output          : {output_pdf}")
    print(f"{'=' * 60}\n")


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='AI Magazine Engine — single file or batch mega-compilation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SINGLE FILE:
  python auto_smart_pdf.py today.txt output.pdf
  python auto_smart_pdf.py today.txt output.pdf --theme dark
  python auto_smart_pdf.py today.txt output.pdf --no-ai

BATCH / MEGA COMPILATION (weekly -> monthly, multi-file MCQ packs):
  python auto_smart_pdf.py --batch week1.txt week2.txt week3.txt week4.txt -o monthly.pdf
  python auto_smart_pdf.py --batch day*.txt -o monthly_mega.pdf --theme dark

today.txt optional header (first 15 lines):
  title: BIOLOGY CAPSULE 2026
  subtitle: NEET Special Edition
  difficulty: 9
        """,
    )
    parser.add_argument('input',   nargs='*', help='Input plain-text file(s) (.txt)')
    parser.add_argument('output',  nargs='?', help='Output PDF file (.pdf) — single-file mode only')
    parser.add_argument('-o', '--output-file', dest='output_file',
                        help='Output PDF file — used with --batch')
    parser.add_argument('--batch', action='store_true',
                        help='Batch mode: process multiple files, merge into one mega PDF')
    parser.add_argument('--theme', choices=['light', 'dark', 'sepia'],
                        default='light', help='Visual theme (default: light)')
    parser.add_argument('--no-ai', action='store_true',
                        help='Skip AI enrichment — parse directly')
    args = parser.parse_args()

    if args.batch:
        files = list(args.input)
        if args.output and args.output not in files:
            files.append(args.output)
        out = args.output_file or 'mega_compilation.pdf'
        if not files:
            print("❌ --batch requires at least one input .txt file")
            sys.exit(1)
        run_batch(files, out, args.theme, args.no_ai)
    else:
        if not args.input:
            print("❌ Provide an input .txt file. Use --batch for multiple files.")
            sys.exit(1)
        generate_pdf_from_raw(args.input[0], args.output, args.theme, args.no_ai)