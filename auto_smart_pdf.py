#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║     TRYIT EDUCATIONS — WORLD CLASS  MAGAZINE 2026                ║
║     All Exams • All Students •                                   ║
║                                                                  ║
║     www.tryiteducations.net | LEARN. LEAD. SUCCEED.              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys, re, os, random, argparse, json, time
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
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# ══════════════════════════════════════════════════════════════
# BRAND CONFIG LOADER
# ══════════════════════════════════════════════════════════════
_BRAND_DEFAULTS = {
    "org_name":        "TRYIT EDUCATIONS",
    "org_short":       "TRYIT",
    "tagline":         "LEARN. LEAD. SUCCEED.",
    "website":         "www.tryiteducations.net",
    "email":           "tryiteducations@gmail.net",
    "phone":           "+91-9566698821",
    "address":         "karur, India",
    "copyright":       f"© {datetime.now().year} TryIT Educations. All rights reserved.",
    "cover_series":    "PREMIUM EDITION",
    "header_line":     "INDIA'S PREMIER EXAM INTELLIGENCE MAGAZINE",
    "footer_left":     "LEARN. LEAD. SUCCEED.",
    "footer_right":    "www.tryiteducations.net",
}

def load_brand(brand_file='brand.json'):
    brand_path = Path(__file__).parent / brand_file
    merged = dict(_BRAND_DEFAULTS)
    if brand_path.exists():
        try:
            with open(brand_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            merged.update({k: v for k, v in raw.items() if not k.startswith('_')})
        except:
            pass
    # Force mandatory website correction across runtime configurations
    merged['website'] = "www.tryiteducations.net"
    merged['footer_right'] = "www.tryiteducations.net"
    return merged

BRAND = load_brand()

EXAM_REGISTRY = {
    'SSC':      {'color': '#1a3b5d', 'badge': 'SSC CGL/CHSL/MTS'},
    'UPSC':     {'color': '#2d6a4f', 'badge': 'UPSC CSE/IAS'},
    'BANKING':  {'color': '#6b21a8', 'badge': 'SBI/IBPS/RBI'},
    'RAILWAY':  {'color': '#b45309', 'badge': 'RRB NTPC/ALP'},
    'NEET':     {'color': '#be123c', 'badge': 'NEET UG/PG'},
    'JEE':      {'color': '#0e7490', 'badge': 'JEE Main/Advanced'},
    'STATE':    {'color': '#4d7c0f', 'badge': 'State PSC'},
    'DEFENCE':  {'color': '#1e3a5f', 'badge': 'NDA/CDS/AFCAT'},
    'TEACHING': {'color': '#7c2d12', 'badge': 'CTET/TET/DSSSB'},
    'INSURANCE':{'color': '#374151', 'badge': 'LIC/NICL/OICL'},
}

THEMES = {
    'light': {
        'bg': '#ffffff',          'text': '#2d3748',
        'heading': '#1a3b5d',     'subheading': '#2a6d9c',
        'table_head': '#1a3b5d',  'table_head_text': '#ffffff',
        'box_border': '#2a6d9c',  'box_bg': '#f0f7ff',
        'accent': '#1a3b5d',      'accent2': '#c9a84c',
        'muted': '#718096',       'rule': '#e2e8f0',
        'highlight_bg': '#fffbeb','callout_bg': '#f0fdf4',
        'mcq_bg': '#111827',      'mcq_text': '#f9fafb',
    },
    'dark': {
        'bg': '#0f172a',          'text': '#e2e8f0',
        'heading': '#93c5fd',     'subheading': '#60a5fa',
        'table_head': '#1e3a5f',  'table_head_text': '#ffffff',
        'box_border': '#3b82f6',  'box_bg': '#1e2d45',
        'accent': '#60a5fa',      'accent2': '#fbbf24',
        'muted': '#94a3b8',       'rule': '#1e3a5f',
        'highlight_bg': '#1c1917','callout_bg': '#052e16',
        'mcq_bg': '#020617',      'mcq_text': '#f3f4f6',
    },
    'sepia': {
        'bg': '#fdf8f0',          'text': '#44332a',
        'heading': '#7c3d12',     'subheading': '#a0522d',
        'table_head': '#7c3d12',  'table_head_text': '#fdf8f0',
        'box_border': '#cd853f',  'box_bg': '#fef9ee',
        'accent': '#a0522d',      'accent2': '#2d6a4f',
        'muted': '#8c7b6b',       'rule': '#e8d5bb',
        'highlight_bg': '#fffdf5','callout_bg': '#f0faf0',
        'mcq_bg': '#1a120b',      'mcq_text': '#f5f5f5',
    }
}

MOTIVATIONAL_QUOTES = [
    ("Arise, awake and do not stop until the goal is reached.", "Swami Vivekananda"),
]

SECTION_EMOJIS = {
    'current affairs': '🌐', 'economy': '📈', 'history': '🏛️',
    'geography': '🗺️', 'science': '🔬', 'polity': '⚖️',
    'mathematics': '🔢', 'reasoning': '🧠', 'english': '📖',
    'biology': '🧬', 'physics': '⚡', 'chemistry': '⚗️', 'default': '📌'
}

def ai_enrich_raw_text(raw_text):
    system_prompt = """
You are the Chief Editor of TRYIT EDUCATIONS. Transform raw study notes into structured magazine content.
Output ONLY plain text. ZERO markdown syntax. Start directly with content.
Use ALL CAPS single lines for major section headings. Detect exam relevance and add exam tags like [SSC] [UPSC] inline.

VISUAL TRIGGER FORMATS — use EXACTLY as shown:
Image-Hero: Exact person or landmark name
Image-Inline: Exact concept or object name
3D-Bar: Chart Title | Label1: 45%, Label2: 30%
Donut-Chart: Chart Title | Label1: 45%, Label2: 30%
Timeline: Title
YEAR | Event Title | One clear description sentence
Table: Title
Column1 | Column2
Data1 | Data2
Mnemonic: Short Title | Full memory phrase here
Highlight: The exact key fact or formula to emphasize
Callout: EXAM ALERT | Key information students must not miss
Fact-Box: Title | Fact1 ;; Fact2
MCQ-Start
Q1. Full question text here?
A) Option one
B) Option two
C) Option three
D) Option four
Answer: A
Explanation: One precise explanatory sentence.
MCQ-End
"""
    if OLLAMA_AVAILABLE:
        try:
            response = ollama.chat(model='llama3', messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': raw_text}], options={'temperature': 0.2, 'num_predict': 4096})
            return response['message']['content']
        except: pass

    groq_key = os.environ.get('GROQ_API_KEY', '')
    if groq_key:
        try:
            resp = requests.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'}, json={'model': 'llama3-8b-8192', 'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': raw_text}], 'temperature': 0.2, 'max_tokens': 4096}, timeout=30)
            return resp.json()['choices'][0]['message']['content']
        except: pass
    return raw_text

def generate_placeholder_image(label, output_dir='.'):
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('#1a3b5d')
    ax.set_facecolor('#1a3b5d')
    ax.text(0.5, 0.58, label.upper(), transform=ax.transAxes, fontsize=14, color='white', ha='center', va='center', fontweight='bold')
    ax.text(0.5, 0.38, BRAND['org_name'], transform=ax.transAxes, fontsize=9, color='#90cdf4', ha='center', va='center', alpha=0.85)
    ax.text(0.5, 0.22, "www.tryiteducations.net", transform=ax.transAxes, fontsize=7, color='#63b3ed', ha='center', va='center', alpha=0.6)
    ax.axis('off')
    fname = f"placeholder_{random.randint(10000, 99999)}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=150, bbox_inches='tight', facecolor='#1a3b5d', edgecolor='none')
    plt.close()
    return fname

def fetch_magazine_media(query, output_dir='.'):
    return generate_placeholder_image(query, output_dir)

def generate_3d_chart(title, data_str, theme_name='light', output_dir='.'):
    labels, values = [], []
    try:
        for pair in data_str.split(','):
            if ':' not in pair: continue
            k, v = pair.split(':', 1)
            labels.append(k.strip())
            values.append(float(v.replace('%', '').strip()))
    except: return None
    if not labels: return None

    theme = THEMES.get(theme_name, THEMES['light'])
    fig = plt.figure(figsize=(7, 4.2), facecolor=theme['bg'])
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor(theme['bg'])
    xpos = np.arange(len(labels))
    ypos, zpos = np.zeros(len(labels)), np.zeros(len(labels))
    dx, dy = 0.6 * np.ones(len(labels)), 0.5 * np.ones(len(labels))
    ax.bar3d(xpos, ypos, zpos, dx, dy, values, color=['#1a3b5d', '#2a6d9c', '#c9a84c', '#2d6a4f'][:len(labels)], alpha=0.88, shade=True, edgecolor='white', linewidth=0.3)
    
    max_v = max(values) if values else 1
    for xi, zi in zip(xpos + 0.3, values):
        ax.text(xi, 0.25, zi + (max_v * 0.02), f'{zi:.0f}%', color=theme['text'], fontsize=7.5, ha='center', va='bottom', fontweight='600')

    ax.set_xticks(xpos + 0.3)
    ax.set_xticklabels(labels, color=theme['text'], fontsize=8.5, rotation=20, ha='right', fontweight='500')
    ax.set_yticks([])
    ax.set_zticks([])
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)
    plt.tight_layout(pad=1.5)
    fname = f"chart_{random.randint(10000, 99999)}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return fname

def generate_donut_chart(title, data_str, theme_name='light', output_dir='.'):
    labels, values = [], []
    try:
        for pair in data_str.split(','):
            if ':' not in pair: continue
            k, v = pair.split(':', 1)
            labels.append(k.strip())
            values.append(float(v.replace('%', '').strip()))
    except: return None
    if not labels: return None
    theme = THEMES.get(theme_name, THEMES['light'])
    fig, ax = plt.subplots(figsize=(5, 3.5), facecolor=theme['bg'])
    ax.set_facecolor(theme['bg'])
    wedges, _, autotexts = ax.pie(values, labels=None, autopct='%1.0f%%', colors=['#1a3b5d', '#2a6d9c', '#c9a84c', '#2d6a4f'], startangle=90, wedgeprops={'width': 0.55, 'edgecolor': theme['bg'], 'linewidth': 2}, pctdistance=0.75)
    for at in autotexts:
        at.set_color('white'); at.set_fontsize(8); at.set_fontweight('bold')
    ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(0.85, 0.5), fontsize=7.5, frameon=False, labelcolor=theme['text'])
    plt.tight_layout()
    fname = f"donut_{random.randint(10000, 99999)}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=200, facecolor=theme['bg'], edgecolor='none')
    plt.close()
    return fname

def parse_mcq_block(block):
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if not lines: return None
    q_text = lines[0]
    q_text = re.sub(r'^(?:Q|Question)\s*\d+\s*[.:\)]\s*', '', q_text, flags=re.IGNORECASE).strip()
    q_text = re.sub(r'^\d+\s*[.:\)]\s*', '', q_text).strip()
    if not q_text: return None

    opt_re = re.compile(r'^([A-D])\s*[.)]\s*(.+)', re.IGNORECASE)
    options, answer, explanation, exam_tags = [], None, None, []
    for line in lines[1:]:
        m = opt_re.match(line)
        if m:
            options.append(f"{m.group(1).upper()}) {m.group(2).strip()}")
            continue
        if re.match(r'^(?:answer|ans)\s*[:.]?\s*[A-D]', line, re.IGNORECASE):
            hit = re.search(r'([A-D])', line, re.IGNORECASE)
            if hit: answer = hit.group(1).upper()
        elif re.match(r'^(?:explanation|exp)\s*[:.]', line, re.IGNORECASE):
            exp_hit = re.search(r'[:.]\s*(.+)', line)
            if exp_hit: explanation = exp_hit.group(1).strip()
        for exam in EXAM_REGISTRY:
            if f'[{exam}]' in line.upper(): exam_tags.append(exam)
    if len(options) >= 2:
        return {'question': q_text, 'options': options, 'answer': answer or '', 'explanation': explanation or '', 'exams': exam_tags or ['SSC', 'UPSC']}
    return None

def auto_parse(text, theme_name='light', output_dir='.'):
    lines = text.splitlines()
    mcqs, sections, raw_body = [], [], []
    in_mcq_block = False
    mcq_buffer = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue

        if line == 'MCQ-Start':
            in_mcq_block = True; mcq_buffer = []; i += 1; continue
        if line == 'MCQ-End':
            in_mcq_block = False
            if mcq_buffer:
                chunks = re.split(r'(?=(?:Q|Question)\s*\d+)', '\n'.join(mcq_buffer), flags=re.IGNORECASE)
                for chunk in chunks:
                    if chunk.strip():
                        q = parse_mcq_block(chunk.strip())
                        if q: mcqs.append(q)
            i += 1; continue
        if in_mcq_block:
            mcq_buffer.append(line); i += 1; continue

        if line.startswith('Image-Hero:'):
            query = line.replace('Image-Hero:', '').strip()
            img = fetch_magazine_media(query, output_dir)
            if img: raw_body.append(f'<div class="hero-banner"><img src="{img}" /><div class="hero-caption-bar"><span class="hero-caption-text">📷 {query.upper()}</span></div></div>')
            i += 1; continue

        if line.startswith('Image-Inline:'):
            query = line.replace('Image-Inline:', '').strip()
            img = fetch_magazine_media(query, output_dir)
            if img: raw_body.append(f'<div class="inline-media"><img src="{img}" /><span class="inline-caption">{query.upper()}</span></div>')
            i += 1; continue

        if line.startswith('3D-Bar:'):
            content = line.replace('3D-Bar:', '').strip()
            if '|' in content:
                parts = content.split('|', 1)
                img = generate_3d_chart(parts[0].strip(), parts[1].strip(), theme_name, output_dir)
                if img: raw_body.append(f'<div class="chart-wrap"><img src="{img}" /></div>')
            i += 1; continue

        if line.startswith('Donut-Chart:'):
            content = line.replace('Donut-Chart:', '').strip()
            if '|' in content:
                parts = content.split('|', 1)
                img = generate_donut_chart(parts[0].strip(), parts[1].strip(), theme_name, output_dir)
                if img: raw_body.append(f'<div class="chart-wrap"><img src="{img}" /></div>')
            i += 1; continue

        if line.startswith('Timeline:'):
            title = line.replace('Timeline:', '').strip()
            t_lines, j = [], i + 1
            while j < len(lines) and '|' in lines[j]:
                t_lines.append(lines[j].strip()); j += 1
            if t_lines:
                nodes = ''
                for idx_t, item in enumerate(t_lines):
                    parts = item.split('|')
                    marker = parts[0].strip()
                    hdr = parts[1].strip() if len(parts) >= 3 else 'KEY EVENT'
                    desc = parts[-1].strip()
                    conn = '' if idx_t == len(t_lines) - 1 else '<div class="tl-line"></div>'
                    nodes += f'<div class="tl-node"><div class="tl-left"><span class="tl-badge">{marker}</span>{conn}</div><div class="tl-right"><h4 class="tl-title">{hdr.upper()}</h4><p class="tl-desc">{desc}</p></div></div>'
                raw_body.append(f'<div class="timeline-wrap"><div class="timeline-header">📅 {title.upper()}</div><div class="tl-track">{nodes}</div></div>')
                i = j; continue

        if line.startswith('Table:'):
            title = line.replace('Table:', '').strip()
            t_lines, j = [], i + 1
            while j < len(lines) and '|' in lines[j]:
                t_lines.append(lines[j].strip()); j += 1
            if t_lines:
                heads = ''.join(f'<th>{h.strip()}</th>' for h in t_lines[0].split('|'))
                rows = ''.join(f'<tr>{"".join(f"<td>{c.strip()}</td>" for c in r.split("|"))}</tr>' for r in t_lines[1:])
                raw_body.append(f'<div class="table-wrap"><div class="table-title">📊 {title.upper()}</div><table><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div>')
                i = j; continue

        if line.lower().startswith('mnemonic:'):
            parts = line.split(':', 1)[1].split('|')
            t_m = parts[0].strip() if len(parts) >= 2 else 'Memory Key'
            raw_body.append(f'<div class="mnemonic-box"><div class="mnemonic-badge">🧠 MNEMONIC</div><h4 class="mnemonic-title">{t_m.upper()}</h4><p class="mnemonic-body">{parts[-1].strip()}</p></div>')
            i += 1; continue

        if line.lower().startswith('highlight:'):
            raw_body.append(f'<div class="highlight-box"><span class="hl-mark">❝</span><p class="hl-text">{line.split(":", 1)[1].strip()}</p></div>')
            i += 1; continue

        if line.lower().startswith('callout:'):
            parts = line.split(':', 1)[1].split('|')
            t_c = parts[0].strip() if len(parts) >= 2 else 'IMPORTANT'
            raw_body.append(f'<div class="callout-box"><div class="callout-tag">⚡ {t_c.upper()}</div><p class="callout-body">{parts[-1].strip()}</p></div>')
            i += 1; continue

        if line.lower().startswith('fact-box:'):
            fb = parse_fact_box(line)
            if fb:
                facts_html = ''.join(f'<li>✦ {f}</li>' for f in fb['facts'])
                raw_body.append(f'<div class="fact-box"><div class="fact-box-title">📌 {fb["title"].upper()}</div><ul class="fact-list">{facts_html}</ul></div>')
            i += 1; continue

        if re.match(r'^\s*(?:Q|Question)\s*\d+', line, re.IGNORECASE) or (re.match(r'^\s*\d+[.)]\s+.+\?', line) and '|' not in line):
            m_lines = [line]; j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt: j += 1; continue
                if re.match(r'^\s*(?:Q|Question)\s*\d+', nxt, re.IGNORECASE) or (len(nxt) < 60 and nxt.isupper()) or any(nxt.startswith(p) for p in ['3D-Bar:', 'Table:', 'Timeline:', 'Mnemonic:', 'Highlight:', 'Callout:', 'Fact-Box:', 'MCQ-Start', 'MCQ-End']):
                    break
                m_lines.append(nxt); j += 1
            q = parse_mcq_block('\n'.join(m_lines))
            if q: mcqs.append(q)
            i = j; continue

        if len(line) < 80 and line.isupper() and not any(line.startswith(p.upper().rstrip(':')) for p in ['3D-Bar:', 'Table:', 'Timeline:', 'Mnemonic:', 'Highlight:', 'Callout:', 'Fact-Box:']):
            emoji = next((v for k, v in SECTION_EMOJIS.items() if k in line.lower()), SECTION_EMOJIS['default'])
            sections.append(line)
            raw_body.append(f'<h1><span class="sec-emoji">{emoji}</span> {line}</h1>')
            i += 1; continue

        para = line
        for exam, info in EXAM_REGISTRY.items():
            para = para.replace(f'[{exam}]', f'<span class="exam-tag" style="background:{info["color"]}">{exam}</span>')
        raw_body.append(f'<p>{para}</p>')
        i += 1

    return '\n'.join(raw_body), mcqs, sections

# ══════════════════════════════════════════════════════════════
# CSS GENERATOR
# ══════════════════════════════════════════════════════════════
def build_css(theme):
    google_fonts = "https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,700;1,400&display=swap"
    return f"""
@import url('{google_fonts}');
@page {{
    size: A4; margin: 2.2cm 2cm 2.5cm 2cm;
    @bottom-center {{ content: "✦  " counter(page) "  ✦"; font-family: 'Playfair Display', serif; font-size: 9pt; color: {theme['muted']}; }}
    @top-right {{ content: "{BRAND['org_name']}  |  {BRAND['tagline']}"; font-size: 6.5pt; letter-spacing: 1.5px; color: {theme['muted']}; font-family: 'Inter', sans-serif; }}
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: {theme['bg']}; color: {theme['text']}; font-family: 'Inter', sans-serif; font-weight: 300; font-size: 10.5pt; line-height: 1.7;
    column-count: 2; column-gap: 2.8em; column-fill: balance; column-rule: 1px solid {theme['rule']};
}}
.cover-page, .mcq-section-title, .mcq-card, .end-page {{ column-span: all; }}
h1 {{
    font-family: 'Cinzel', serif; font-size: 16pt; font-weight: 700; letter-spacing: 2.5px; color: {theme['heading']};
    border-bottom: 2px solid {theme['accent']}; padding-bottom: 8px; margin: 2em 0 0.8em 0; text-transform: uppercase;
}}
h1 .sec-emoji {{ margin-right: 8px; font-size: 14pt; }}
p {{ text-align: justify; margin-bottom: 1em; line-height: 1.75; }}
p strong, p b {{ color: {theme['heading']}; font-weight: 700; }} /* Topic highlighting features */

.hero-banner, .inline-media, .chart-wrap, .timeline-wrap, .table-wrap, .mnemonic-box, .highlight-box, .callout-box, .fact-box, .mcq-card {{ break-inside: avoid; page-break-inside: avoid; }}
.hero-banner {{ margin: 2em 0 1em 0; }}
.hero-banner img {{ display: block; width: 100%; max-height: 360px; object-fit: cover; border-radius: 6px; }}
.hero-caption-bar {{ margin-top: 6px; border-left: 3px solid {theme['accent']}; padding-left: 8px; }}
.hero-caption-text {{ font-size: 7.5pt; font-weight: 600; letter-spacing: 1.5px; color: {theme['muted']}; }}
.inline-media img {{ display: block; width: 100%; border-radius: 5px; margin: 1em 0 0.3em 0; }}
.inline-caption {{ font-size: 7pt; letter-spacing: 1px; color: {theme['muted']}; display: block; margin-bottom: 1em; }}
.chart-wrap {{ margin: 1.5em 0; text-align: center; }}
.chart-wrap img {{ width: 100%; max-width: 560px; height: auto; border-radius: 6px; }}

.timeline-wrap {{ margin: 2em 0; border: 1px solid {theme['rule']}; border-radius: 8px; overflow: hidden; }}
.timeline-header {{ background: {theme['heading']}; color: white; font-family: 'Cinzel', serif; font-size: 9pt; font-weight: 700; letter-spacing: 2px; padding: 10px 18px; }}
.tl-track {{ padding: 16px 18px; }}
.tl-node {{ display: flex; align-items: flex-start; gap: 16px; }}
.tl-left {{ display: flex; flex-direction: column; align-items: center; min-width: 72px; }}
.tl-badge {{ font-family: 'Cinzel', serif; font-size: 8pt; font-weight: 700; color: {theme['heading']}; background: {theme['box_bg']}; border: 1.5px solid {theme['accent']}; border-radius: 4px; padding: 3px 8px; text-align: center; width: 100%; }}
.tl-line {{ width: 1.5px; height: 36px; background: {theme['accent']}; opacity: 0.3; margin: 4px 0; }}
.tl-title {{ font-size: 9pt; font-weight: 700; color: {theme['heading']}; margin-bottom: 2px; }}
.tl-desc {{ font-size: 9.5pt; color: {theme['text']}; margin-bottom: 14px; }}

.table-wrap {{ margin: 1.8em 0; }}
.table-title {{ font-size: 8pt; font-weight: 700; letter-spacing: 1.5px; color: {theme['accent']}; margin-bottom: 6px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9.5pt; }}
th {{ background: {theme['table_head']}; color: {theme['table_head_text']}; font-size: 8pt; font-weight: 700; text-transform: uppercase; padding: 10px 12px; }}
td {{ padding: 9px 12px; border-bottom: 1px solid {theme['rule']}; }}
tr:nth-child(even) td {{ background-color: {theme['box_bg']}; }}

.mnemonic-box {{ background: {theme['box_bg']}; border-left: 4px solid {theme['accent']}; border-radius: 0 6px 6px 0; padding: 16px 20px; margin: 1.5em 0; }}
.mnemonic-badge {{ font-size: 7pt; font-weight: 700; letter-spacing: 1.5px; color: {theme['accent']}; margin-bottom: 5px; }}
.mnemonic-title {{ font-family: 'Playfair Display', serif; font-size: 10.5pt; color: {theme['heading']}; margin-bottom: 5px; }}
.mnemonic-body {{ font-size: 10pt; }}
.highlight-box {{ border-left: 3px solid {theme['accent2']}; background: {theme['highlight_bg']}; padding: 14px 20px; margin: 1.5em 0; }}
.hl-mark {{ font-family: 'Playfair Display', serif; font-size: 28pt; color: {theme['accent2']}; line-height: 0; vertical-align: -12px; opacity: 0.45; }}
.hl-text {{ display: inline; font-family: 'Playfair Display', serif; font-style: italic; font-size: 11pt; color: {theme['heading']}; }}
.callout-box {{ background: {theme['callout_bg']}; border: 1.5px solid {theme['box_border']}; padding: 14px 18px; margin: 1.5em 0; border-radius: 6px; }}
.callout-tag {{ font-size: 7.5pt; font-weight: 700; color: {theme['accent']}; margin-bottom: 5px; }}
.fact-box {{ border: 1px solid {theme['rule']}; border-top: 3px solid {theme['accent']}; padding: 14px 18px; margin: 1.5em 0; background: {theme['box_bg']}; border-radius: 6px; }}
.fact-box-title {{ font-size: 8pt; font-weight: 700; color: {theme['accent']}; margin-bottom: 8px; }}
.fact-list li {{ font-size: 9.5pt; padding: 3px 0; border-bottom: 1px solid {theme['rule']}; }}

/* ── RE-ENGINEERED MCQ ARCHITECTURE ── */
.mcq-section-title {{ font-family: 'Cinzel', serif; font-size: 15pt; color: {theme['heading']}; border-bottom: 2px solid {theme['accent']}; padding-bottom: 8px; margin-top: 3em; margin-bottom: 1.5em; letter-spacing: 2px; text-transform: uppercase; }}
.mcq-card {{ border: 1px solid {theme['rule']}; border-radius: 8px; padding: 22px 26px; margin-top: 3.5em; margin-bottom: 3.5em; background: {theme['mcq_bg']}; color: {theme['mcq_text']}; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}
.mcq-header {{ display: flex; align-items: flex-start; gap: 14px; margin-bottom: 16px; }}
.mcq-number {{ font-family: 'Cinzel', serif; font-size: 11pt; font-weight: 700; color: white; background: {theme['accent2']}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.mcq-question {{ font-size: 11pt; font-weight: 600; color: {theme['mcq_text']}; line-height: 1.6; flex: 1; margin: 0; }}
.mcq-options {{ list-style: none; padding: 0; margin: 12px 0 16px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.mcq-options li {{ font-size: 9.5pt; padding: 8px 12px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: {theme['mcq_text']}; }}
.mcq-answer-block {{ background: rgba(0,0,0,0.25); border-left: 3px solid #2d6a4f; border-radius: 4px; padding: 10px 14px; margin-top: 12px; }}
.mcq-answer {{ font-size: 9.5pt; font-weight: 700; color: #4ade80; margin-bottom: 4px; }}
.mcq-explanation {{ font-size: 9pt; color: rgba(255,255,255,0.75); font-style: italic; }}
.exam-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }}
.exam-tag {{ font-size: 6.5pt; font-weight: 700; color: white; padding: 3px 8px; border-radius: 3px; }}

/* ── COVER PAGE ── */
.cover-page {{ height: 25.7cm; display: flex; flex-direction: column; padding: 0; overflow: hidden; }}
.cover-top-bar {{ background: {theme['heading']}; color: white; padding: 14px 30px; display: flex; justify-content: space-between; align-items: center; }}
.cover-top-brand {{ font-family: 'Cinzel', serif; font-size: 11pt; letter-spacing: 3px; font-weight: 700; }}
.cover-top-meta {{ font-size: 7.5pt; letter-spacing: 2px; opacity: 0.9; font-weight: 500; }}
.cover-hero-strip {{ background: linear-gradient(135deg, {theme['heading']} 0%, {theme['subheading']} 100%); flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 40px 50px; text-align: center; }}
.cover-issue-label {{ font-size: 7.5pt; letter-spacing: 4px; color: rgba(255,255,255,0.6); margin-bottom: 20px; text-transform: uppercase; }}
.cover-main-title {{ font-family: 'Cinzel', serif; font-size: 44pt; font-weight: 700; color: white; letter-spacing: 8px; line-height: 1.1; margin-bottom: 16px; }}
.cover-gold-rule {{ width: 80px; height: 3px; background: {theme['accent2']}; margin: 0 auto 20px auto; }}
.cover-subtitle {{ font-family: 'Playfair Display', serif; font-style: italic; font-size: 15pt; color: rgba(255,255,255,0.85); margin-bottom: 30px; }}
.cover-tagline {{ font-size: 8.5pt; letter-spacing: 4px; color: #ffffff; text-transform: uppercase; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }}

/* ⚡ CLEAN RE-ENGINEERED COVER BOTTOM BOXES ⚡ */
.cover-info-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 30px; background: transparent; border-top: 1px solid rgba(255,255,255,0.15); width: 85%; margin: 0 auto; }}
.cover-info-item {{ text-align: center; color: white; }}
.cover-info-label {{ font-size: 6.5pt; letter-spacing: 2px; opacity: 0.6; display: block; margin-bottom: 2px; text-transform: uppercase; }}
.cover-info-value {{ font-family: 'Cinzel', serif; font-size: 10.5pt; font-weight: 500; color: rgba(255,255,255,0.95); }}
.cover-exam-strip {{ padding: 16px 30px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; background: rgba(255,255,255,0.03); border-top: 1px solid rgba(255,255,255,0.1); width: 100%; }}
.cover-exam-pill {{ font-size: 7pt; font-weight: 700; color: white; padding: 5px 14px; border-radius: 20px; letter-spacing: 0.5px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }}
.cover-bottom-bar {{ background: {theme['heading']}; color: white; padding: 12px 30px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.1); }}
.cover-motto {{ font-size: 8.5pt; letter-spacing: 3px; font-weight: 600; color: {theme['accent2']}; text-transform: uppercase; }}
.cover-website {{ font-size: 8pt; font-weight: 600; letter-spacing: 1px; color: #ffffff; }}

.gauge-block {{ display: flex; flex-direction: column; align-items: center; gap: 6px; }}
.gauge-ring {{ width: 72px; height: 72px; border-radius: 50%; display: flex; justify-content: center; align-items: center; }}
.gauge-inner {{ width: 54px; height: 54px; background: {theme['heading']}; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.gauge-num {{ font-family: 'Cinzel', serif; font-size: 14pt; font-weight: 700; color: white; line-height: 1; }}
.gauge-denom {{ font-size: 7pt; color: rgba(255,255,255,0.6); }}
.gauge-label {{ font-size: 6pt; letter-spacing: 1.5px; color: rgba(255,255,255,0.5); text-align: center; }}

.toc-box {{ background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 16px 20px; min-width: 210px; }}
.toc-header {{ font-size: 7pt; letter-spacing: 2px; color: rgba(255,255,255,0.5); border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 10px; text-transform: uppercase; }}
.toc-item {{ font-size: 8.5pt; color: rgba(255,255,255,0.8); padding: 3px 0; display: flex; gap: 8px; align-items: center; }}
.toc-dot {{ color: {theme['accent2']}; font-size: 7pt; }}

/* ── BEAUTIFULLY THEMED END CLOSING PAGE ── */
.end-page {{ text-align: center; padding: 6cm 2cm 2cm 2cm; background: linear-gradient(180deg, {theme['bg']} 0%, {theme['box_bg']} 100%); height: 25.7cm; margin: -2.2cm -2cm -2.5cm -2cm; }}
.end-quote {{ font-family: 'Playfair Display', serif; font-style: italic; font-size: 16pt; font-weight: 700; color: {theme['heading']}; line-height: 1.8; max-width: 85%; margin: 0 auto 0.6em auto; text-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
.end-quote-src {{ font-size: 10pt; font-weight: 600; letter-spacing: 2px; color: {theme['accent2']}; text-transform: uppercase; margin-bottom: 2em; }}
.end-rule {{ width: 80px; height: 3px; background: {theme['accent']}; margin: 2.5em auto; border-radius: 2px; }}
.end-logo {{ font-family: 'Cinzel', serif; font-size: 16pt; letter-spacing: 5px; font-weight: 700; color: {theme['heading']}; text-transform: uppercase; }}
.end-tagline {{ font-size: 9pt; font-weight: 600; letter-spacing: 4px; color: {theme['muted']}; margin-top: 6px; text-transform: uppercase; }}
.end-close {{ margin-top: 3em; font-size: 8.5pt; font-weight: 500; letter-spacing: 2px; color: {theme['muted']}; opacity: 0.7; }}
"""

# ══════════════════════════════════════════════════════════════
# COVER PAGE HTML
# ══════════════════════════════════════════════════════════════
def build_cover(meta, theme, sections):
    diff = meta.get('difficulty', 8)
    gauge_deg = int((diff / 10) * 360)

    toc_items = ''
    for s in sections[:8]:
        emoji = next((v for k, v in SECTION_EMOJIS.items() if k in s.lower()), '📌')
        # FIXED: Removed internal split pipe syntax breaking layout rendering characters right before the letter 'C'
        toc_items += f'<div class="toc-item"><span class="toc-dot">✦</span>{emoji} {s[:40]}</div>'
    if not toc_items:
        toc_items = '<div class="toc-item"><span class="toc-dot">✦</span>📌 COMPLETE STUDY BRIEFING</div>'

    exam_pills = ''.join(f'<span class="cover-exam-pill" style="background:{info["color"]}">{info["badge"]}</span>' for info in EXAM_REGISTRY.values())
    title = meta.get('title', 'TRYIT BRIEFINGS')
    subtitle = meta.get('subtitle', 'Curated Knowledge Compendium')
    
    # FIXED: Hardcoded 'ISSUE ' string token dropped; now prints clean issue indicator values directly
    issue_lbl = datetime.now().strftime('%m/%Y')
    month = datetime.now().strftime('%B %Y').upper()
    dated = datetime.now().strftime('%d %b %Y').upper()

    return f"""
<div class="cover-page">
  <div class="cover-top-bar">
    <div class="cover-top-brand">TRYIT EDUCATIONS</div>
    <div class="cover-top-meta">{issue_lbl} &nbsp;•&nbsp; {month} &nbsp;•&nbsp; PREMIUM EDITION</div>
  </div>

  <div class="cover-hero-strip">
    <div class="cover-issue-label">◈ &nbsp; INDIA'S PREMIER EXAM INTELLIGENCE MAGAZINE &nbsp; ◈</div>
    <div class="cover-main-title">{title}</div>
    <div class="cover-gold-rule"></div>
    <div class="cover-subtitle">{subtitle}</div>
    <div class="cover-tagline">LEARN &nbsp;•&nbsp; LEAD &nbsp;•&nbsp; SUCCEED</div>

    <div style="display:flex; gap:40px; margin-top:32px; align-items:flex-start;">
      <div class="gauge-block">
        <div class="gauge-ring" style="background: conic-gradient(#c9a84c {gauge_deg}deg, rgba(255,255,255,0.1) 0deg);">
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

    <!-- FIXED: Hardcoded yellow highlight tags removed; clean borderless premium layout grid deployed -->
    <div class="cover-info-bar">
        <div class="cover-info-item">
          <span class="cover-info-label">EDITION DATE</span>
          <span class="cover-info-value">{dated}</span>
        </div>
        <div class="cover-info-item">
          <span class="cover-info-label">DISTRIBUTION</span>
          <span class="cover-info-value">EXECUTIVE</span>
        </div>
    </div>
  </div>

  <div class="cover-exam-strip">{exam_pills}</div>

  <div class="cover-bottom-bar">
    <div class="cover-motto">LEARN. LEAD. SUCCEED.</div>
    <div class="cover-website">www.tryiteducations.net</div>
  </div>
</div>
<div style="page-break-after: always;"></div>
"""

# ══════════════════════════════════════════════════════════════
# MCQ SECTION HTML
# ══════════════════════════════════════════════════════════════
def build_mcq_section(mcqs, theme):
    if not mcqs: return ''
    html = '<div style="page-break-before: always;"></div>'
    html += '<h2 class="mcq-section-title">📚 Practice Questions Bank</h2>'

    for idx, q in enumerate(mcqs, 1):
        opts_html = ''.join(f'<li>{o}</li>' for o in q['options'])
        ans_html = ''
        if q['answer'] or q['explanation']:
            inner = ''
            if q['answer']: inner += f'<div class="mcq-answer">✅ Verified Objective Answer Key: {q["answer"]}</div>'
            if q['explanation']: inner += f'<p class="mcq-explanation">💡 Logic Framework: {q["explanation"]}</p>'
            ans_html = f'<div class="mcq-answer-block">{inner}</div>'

        tags_html = ''
        if q.get('exams'):
            pills = ''.join(f'<span class="exam-tag" style="background:{EXAM_REGISTRY.get(e, {"color": "#374151"})["color"]}">{e}</span>' for e in q['exams'])
            tags_html = f'<div class="exam-tags">{pills}</div>'

        html += f"""
        <div class="mcq-card">
            <div class="mcq-header">
                <div class="mcq-number">{idx}</div>
                <p class="mcq-question">{q['question']}</p>
            </div>
            <ul class="mcq-options">{opts_html}</ul>
            {ans_html}
            {tags_html}
        </div>
        """
    return html

# ══════════════════════════════════════════════════════════════
# MASTER PIPELINE
# ══════════════════════════════════════════════════════════════
def generate_pdf_from_raw(raw_file, output_pdf=None, theme_name='light', skip_ai=False):
    start = time.time()
    print(f"\n{'=' * 60}\n  TRYIT EDUCATIONS — PRODUCTION PIPELINE RUN\n{'=' * 60}\n")

    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    enriched = raw_text if skip_ai else ai_enrich_raw_text(raw_text)

    meta = {
        'difficulty': 8,
        'title':      'TRYIT BRIEFINGS',
        'subtitle':   'Curated Knowledge Compendium',
        'theme':      theme_name,
    }
    skip_keys = ['3D-Bar:', 'Table:', 'Timeline:', 'Image-', 'Mnemonic:', 'Highlight:', 'Callout:', 'Fact-Box:']
    for raw_line in raw_text.splitlines()[:15]:
        if ':' not in raw_line or any(raw_line.startswith(sk) for sk in skip_keys): continue
        k_raw, v_raw = raw_line.split(':', 1)
        k, v = k_raw.strip().lower(), v_raw.strip()
        if k in ('title', 'subtitle'): meta[k] = v
        elif k == 'difficulty':
            try: meta['difficulty'] = max(1, min(10, int(v)))
            except: pass

    theme = THEMES[theme_name]
    work_dir = str(Path(raw_file).parent)
    processed_body, mcqs, sections = auto_parse(enriched, theme_name, work_dir)

    cover = build_cover(meta, theme, sections)
    mcq_section = build_mcq_section(mcqs, theme)
    quote, src = random.choice(MOTIVATIONAL_QUOTES)

    # FIXED: Closing page elements adapt dynamic styling architectures based on theme parameters
    end_page = f"""
    <div style="page-break-before: always;"></div>
    <div class="end-page">
        <div class="end-quote">"{quote}"</div>
        <div class="end-quote-src">— {src}</div>
        <div class="end-rule"></div>
        <div class="end-logo">TRYIT EDUCATIONS</div>
        <div class="end-tagline">LEARN  •  LEAD  •  SUCCEED</div>
        <div class="end-close">www.tryiteducations.net  •  END OF EDITION</div>
    </div>
    """

    css = build_css(theme)
    full_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>TryIT Magazine</title><style>{css}</style></head>
<body>
    {cover}
    {processed_body}
    {mcq_section}
    {end_page}
</body></html>"""

    if not output_pdf: output_pdf = str(Path(raw_file).with_suffix('.pdf'))
    font_config = FontConfiguration()
    HTML(string=full_html, base_url=work_dir).write_pdf(str(output_pdf), font_config=font_config)
    print(f"\n✅ Build Finished in {time.time() - start:.1f}s\n📄 Target Asset Pathway: {output_pdf}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TryIT Educations — Premium Magazine Engine')
    parser.add_argument('input', help='Input plain-text file (.txt)')
    parser.add_argument('output', nargs='?', help='Output PDF file (.pdf)')
    parser.add_argument('--theme', choices=['light', 'dark', 'sepia'], default='light')
    parser.add_argument('--no-ai', action='store_true')
    args = parser.parse_args()
    generate_pdf_from_raw(args.input, args.output, args.theme, args.no_ai)