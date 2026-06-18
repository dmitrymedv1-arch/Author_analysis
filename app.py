# ============================================
# app.py - ЕДИНЫЙ ФАЙЛ ПРИЛОЖЕНИЯ
# ============================================

# ============================================
# СЕКЦИЯ ПАРАМЕТРОВ (настройка запросов)
# ============================================

# Параметры API запросов
BATCH_SIZE = 50  # Размер батча для всех API
MAX_RETRIES = 3  # Количество попыток при ошибке
TIMEOUT = 30  # Таймаут на запрос в секундах
DELAY_BETWEEN_BATCHES = 0.5  # Задержка между батчами (сек)
MAX_CONCURRENT_REQUESTS = 10  # Максимум параллельных запросов
RETRY_DELAY = 2  # Задержка перед повторной попыткой (сек)

# Параметры вывода
SHOW_DEBUG_LOGS = True  # Показывать детальные логи
GENERATE_HTML_REPORT = True  # Генерировать HTML отчет
GENERATE_PDF_REPORT = True  # Генерировать PDF отчет
USE_CACHE = True  # Использовать кэширование результатов
LOGO_PATH = None  # Путь к логотипу журнала (устанавливается через виджет)

# Лимиты для анализа
MAX_PUBLICATIONS_TO_ANALYZE = 1000  # Максимум статей для анализа
MIN_YEAR_FOR_TREND = 5  # Сколько лет для тренда

# ============================================
# ИМПОРТЫ
# ============================================

import asyncio
import aiohttp
import pandas as pd
import streamlit as st
from streamlit import session_state as ss
import re
import time
from datetime import datetime
import json
from typing import List, Set, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from wordcloud import WordCloud
from io import BytesIO
import base64
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import os
import hashlib
from matplotlib.ticker import MaxNLocator
import html
import colorsys
from tenacity import retry, stop_after_attempt, wait_exponential, wait_random
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
from itertools import combinations
import difflib

# Для PDF отчета
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ============================================
# COLOR UTILITIES FOR DYNAMIC THEMES (из второго кода)
# ============================================

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def get_complementary_color(hex_color: str) -> str:
    """
    Generate complementary color by rotating hue by 180 degrees
    Returns a color that pairs well with the base color
    """
    rgb = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    complementary_hue = (h + 0.5) % 1.0
    complementary_rgb = colorsys.hsv_to_rgb(complementary_hue, s, v)
    return rgb_to_hex(tuple(int(c * 255) for c in complementary_rgb))

def get_analogous_colors(hex_color: str, count: int = 2) -> List[str]:
    """Generate analogous colors (colors adjacent on color wheel)"""
    rgb = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    
    colors_list = []
    step = 30 / 360.0
    
    for i in range(count):
        offset = (i + 1) * step
        new_hue = (h + offset) % 1.0
        new_rgb = colorsys.hsv_to_rgb(new_hue, s, v)
        colors_list.append(rgb_to_hex(tuple(int(c * 255) for c in new_rgb)))
    
    return colors_list

def get_gradient_colors(hex_color: str, steps: int = 5) -> List[str]:
    """Generate gradient colors from base color to lighter shades"""
    rgb = hex_to_rgb(hex_color)
    colors_list = []
    
    for i in range(steps):
        factor = 0.3 + (i * 0.14)
        new_rgb = tuple(min(255, int(c * (1 + factor * 0.5))) for c in rgb)
        colors_list.append(rgb_to_hex(new_rgb))
    
    return colors_list

def get_contrast_color(hex_color: str) -> str:
    """Get contrasting color (black or white) for text on a colored background"""
    rgb = hex_to_rgb(hex_color)
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return '#FFFFFF' if luminance < 0.5 else '#000000'

def generate_css_variables(base_color: str, accent_color: str = None) -> Dict[str, str]:
    """Generate complete CSS variable set for the theme"""
    if accent_color is None:
        accent_color = get_complementary_color(base_color)
    
    gradient_start = base_color
    gradient_end = accent_color
    
    lighter_base = get_gradient_colors(base_color, 1)[0]
    lighter_accent = get_gradient_colors(accent_color, 1)[0]
    
    base_contrast = get_contrast_color(base_color)
    accent_contrast = get_contrast_color(accent_color)
    
    analogous = get_analogous_colors(base_color, 2)
    
    return {
        '--primary-color': base_color,
        '--secondary-color': accent_color,
        '--primary-light': lighter_base,
        '--secondary-light': lighter_accent,
        '--primary-contrast': base_contrast,
        '--secondary-contrast': accent_contrast,
        '--gradient-start': gradient_start,
        '--gradient-end': gradient_end,
        '--accent-1': analogous[0] if len(analogous) > 0 else accent_color,
        '--accent-2': analogous[1] if len(analogous) > 1 else accent_color,
        '--hover-light': f"{base_color}20",
    }

def apply_theme_css(base_color: str, accent_color: str = None):
    """Apply dynamic CSS theme based on selected colors"""
    if accent_color is None:
        accent_color = get_complementary_color(base_color)
    
    css_vars = generate_css_variables(base_color, accent_color)
    
    theme_css = f"""
    <style>
        :root {{
            --primary: {css_vars['--primary-color']};
            --secondary: {css_vars['--secondary-color']};
            --primary-light: {css_vars['--primary-light']};
            --secondary-light: {css_vars['--secondary-light']};
            --primary-contrast: {css_vars['--primary-contrast']};
            --secondary-contrast: {css_vars['--secondary-contrast']};
            --gradient-start: {css_vars['--gradient-start']};
            --gradient-end: {css_vars['--gradient-end']};
            --accent-1: {css_vars['--accent-1']};
            --accent-2: {css_vars['--accent-2']};
            --hover-light: {css_vars['--hover-light']};
        }}
        
        .stApp {{
            background: linear-gradient(135deg, 
                rgba({int(hex_to_rgb(css_vars['--gradient-start'])[0])}, {int(hex_to_rgb(css_vars['--gradient-start'])[1])}, {int(hex_to_rgb(css_vars['--gradient-start'])[2])}, 0.05) 0%,
                rgba({int(hex_to_rgb(css_vars['--gradient-end'])[0])}, {int(hex_to_rgb(css_vars['--gradient-end'])[1])}, {int(hex_to_rgb(css_vars['--gradient-end'])[2])}, 0.08) 100%);
        }}
        
        .metric-number {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .section-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }}
        
        .rank-item {{
            border-left: 3px solid var(--primary);
        }}
        
        .rank-number {{
            color: var(--primary);
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }}
        
        .custom-tab-button.active {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }}
        
        .custom-tab-button:hover {{
            background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary-light) 100%);
        }}
        
        .colored-progress-bar {{
            background: linear-gradient(90deg, 
                var(--primary) 0%, 
                var(--secondary) 50%,
                var(--primary) 100%);
        }}
        
        .section-title {{
            border-bottom: 3px solid var(--primary);
        }}
        
        .concept-card {{
            background: linear-gradient(135deg, var(--hover-light) 0%, var(--secondary-light) 100%);
            border: 1px solid var(--primary-light);
        }}
        
        .concept-name {{
            color: var(--primary);
        }}
        
        .clickable-link {{
            color: var(--primary);
        }}
        
        .clickable-link:hover {{
            color: var(--secondary);
        }}
        
        .badge-success {{
            background: var(--primary-light);
            color: var(--primary-contrast);
        }}
        
        .custom-tab-button .custom-tab-title {{
            color: inherit;
        }}
        
        .metric-card:hover {{
            box-shadow: 0 6px 12px rgba({int(hex_to_rgb(css_vars['--primary-color'])[0])}, {int(hex_to_rgb(css_vars['--primary-color'])[1])}, {int(hex_to_rgb(css_vars['--primary-color'])[2])}, 0.15);
        }}
        
        * {{
            transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .color-preview {{
            display: inline-block;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            margin-left: 10px;
            vertical-align: middle;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .color-preview:hover {{
            transform: scale(1.1);
        }}
        
        .complementary-preview {{
            display: inline-block;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            margin-left: 10px;
            vertical-align: middle;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .theme-info {{
            background: var(--hover-light);
            border-radius: 10px;
            padding: 12px;
            margin-top: 15px;
            font-size: 12px;
            text-align: center;
        }}
        
        .reviewer-card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 4px solid var(--primary);
        }}
        
        .reviewer-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .reviewer-name {{
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 8px;
        }}
        
        .reviewer-orcid {{
            font-family: monospace;
            font-size: 12px;
            margin-bottom: 8px;
        }}
        
        .reviewer-section {{
            margin-top: 12px;
            padding-top: 8px;
            border-top: 1px solid #e0e0e0;
        }}
        
        .reviewer-section-title {{
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 8px;
            color: #555;
        }}
        
        .external-id-link {{
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 11px;
            margin: 3px;
            text-decoration: none;
            color: #333;
            transition: background 0.2s;
        }}
        
        .external-id-link:hover {{
            background: var(--primary);
            color: white;
        }}
        
        .reviewer-website {{
            display: inline-block;
            margin: 3px 6px 3px 0;
            font-size: 12px;
        }}
        
        .confidential-banner {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69e 100%);
            border-left: 4px solid #dc3545;
            padding: 12px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-weight: 500;
            text-align: center;
        }}
        
        /* Author card styles for multiple authors */
        .author-card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid var(--primary);
            transition: transform 0.2s;
        }}
        
        .author-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .author-card.best {{
            border-left-color: #FFD700;
            background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
        }}
        
        .author-rank {{
            font-size: 20px;
            font-weight: bold;
            color: var(--primary);
            display: inline-block;
            margin-right: 10px;
        }}
        
        .author-name-main {{
            font-size: 22px;
            font-weight: 600;
            color: var(--primary);
            display: inline-block;
        }}
        
        .author-hindex {{
            font-size: 18px;
            color: #666;
            margin-left: 10px;
        }}
        
        .best-badge {{
            background: #FFD700;
            color: #333;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            display: inline-block;
            margin-left: 15px;
        }}
        
        /* Color coding for author cards in reports */
        .author-section {{
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .author-section:last-child {{
            border-bottom: none;
        }}
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

def update_colored_progress(progress_percent: float, status_text: str = "", color: str = None, badge_text: str = None):
    """Update progress bar with theme colors"""
    if color is None:
        primary_color = st.session_state.get('primary_color', '#667eea')
        secondary_color = st.session_state.get('secondary_color', get_complementary_color(primary_color))
        color = primary_color
    
    if badge_text is None:
        if progress_percent >= 80:
            badge_text = "✅ Отлично"
        elif progress_percent >= 60:
            badge_text = "📊 Хорошо"
        elif progress_percent >= 40:
            badge_text = "⚠️ Средне"
        elif progress_percent >= 20:
            badge_text = "⚠️ Низко"
        else:
            badge_text = "❌ Критично"
    
    progress_html = f"""
    <style>
    @keyframes shimmer{{
        0% {{ background-position: -1000px 0; }}
        100% {{ background-position: 1000px 0; }}
    }}
    
    .colored-progress-container {{
        width: 100%;
        background-color: #f0f0f0;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
        margin: 10px 0;
    }}
    
    .colored-progress-bar {{
        width: {progress_percent:.1f}%;
        height: 32px;
        background: linear-gradient(90deg, 
            {color} 0%, 
            {color}DD 25%,
            {color} 50%,
            {color}DD 75%,
            {color} 100%);
        background-size: 200% 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 20px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 13px;
        text-shadow: 0 0 2px rgba(0,0,0,0.5);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .colored-progress-bar::after {{
        content: "{progress_percent:.1f}%";
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
    }}
    
    .progress-stats {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 8px;
        font-size: 12px;
    }}
    
    .progress-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        background: {color}20;
        color: {color};
        border: 1px solid {color}40;
    }}
    
    .progress-status {{
        font-size: 14px;
        font-weight: 500;
        color: #333;
    }}
    </style>
    
    <div class="colored-progress-container">
        <div class="colored-progress-bar"></div>
    </div>
    <div class="progress-stats">
        <span class="progress-status">{status_text}</span>
        <span class="progress-badge">{badge_text}</span>
    </div>
    """
    
    return progress_html

# ============================================
# НАСТРОЙКА НАУЧНОГО СТИЛЯ ДЛЯ ГРАФИКОВ
# ============================================

def apply_scientific_style():
    """Улучшенный научный стиль для matplotlib для материаловедческих публикаций"""
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        try:
            plt.style.use('seaborn-whitegrid')
        except:
            pass
    
    plt.rcParams.update({
        'font.size': 11,
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif', 'Computer Modern Roman'],
        'mathtext.fontset': 'stix',
        
        'axes.labelsize': 12,
        'axes.labelweight': 'bold',
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'axes.facecolor': '#FFFFFF',
        'axes.edgecolor': '#000000',
        'axes.linewidth': 1.5,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        
        'xtick.color': '#000000',
        'ytick.color': '#000000',
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.major.size': 7,
        'xtick.major.width': 1.5,
        'ytick.major.size': 7,
        'ytick.major.width': 1.5,
        'xtick.minor.size': 3,
        'xtick.minor.width': 1.0,
        'ytick.minor.size': 3,
        'ytick.minor.width': 1.0,
        
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '#000000',
        'legend.fancybox': False,
        'legend.borderaxespad': 0.5,
        'legend.handlelength': 1.5,
        'legend.handletextpad': 0.8,
        
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'figure.facecolor': 'white',
        'figure.constrained_layout.use': True,
        'figure.figsize': (8, 6),
        
        'lines.linewidth': 2,
        'lines.markersize': 7,
        'lines.markeredgewidth': 1.0,
        'errorbar.capsize': 3,
        
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })

apply_scientific_style()

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def clean_orcid(orcid_input: str) -> str:
    """Очищает ORCID от лишних символов и приводит к стандартному формату"""
    orcid = orcid_input.strip().upper()
    
    if 'orcid.org/' in orcid:
        orcid = orcid.split('orcid.org/')[-1]
    
    orcid = re.sub(r'[^0-9X-]', '', orcid)
    
    if re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid):
        return orcid
    
    if len(orcid) == 16 and orcid.isdigit():
        return f"{orcid[:4]}-{orcid[4:8]}-{orcid[8:12]}-{orcid[12:]}"
    
    return orcid

def format_boolean(value: bool) -> str:
    return "✅" if value else "❌"

def extract_country_from_affiliation(affiliation: str) -> str:
    """Извлекает страну из названия аффилиации"""
    countries = [
        'USA', 'UK', 'China', 'Germany', 'France', 'Japan', 'Russia', 'Italy', 
        'Canada', 'Australia', 'Spain', 'Brazil', 'India', 'Netherlands', 'Switzerland',
        'South Korea', 'Sweden', 'Belgium', 'Poland', 'Austria', 'Norway', 'Denmark',
        'Finland', 'Ireland', 'Portugal', 'Greece', 'Czech Republic', 'Hungary',
        'New Zealand', 'South Africa', 'Argentina', 'Mexico', 'Chile', 'Colombia',
        'United States', 'United Kingdom', 'England', 'Scotland', 'Wales'
    ]
    
    for country in countries:
        if country.lower() in affiliation.lower():
            return country
    return "Unknown"

def normalize_author_name(name: str) -> str:
    """Нормализует имя автора для сравнения (инициал + фамилия) - задача 2"""
    if not name:
        return name
    
    name = name.strip()
    parts = name.split()
    
    if len(parts) >= 2:
        first_initial = parts[0][0].upper()
        last_name = parts[-1]
        return f"{first_initial} {last_name}"
    elif len(parts) == 1:
        return parts[0]
    else:
        return name

def format_orcid_id(orcid: str) -> str:
    """Format ORCID ID to full URL"""
    if not orcid or not isinstance(orcid, str):
        return ""
    
    if orcid.startswith('https://orcid.org/'):
        return orcid
    
    clean_id = re.sub(r'[^\dXx-]', '', orcid.strip())
    
    if '-' in clean_id:
        if re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', clean_id, re.IGNORECASE):
            return f"https://orcid.org/{clean_id}"
    
    if len(clean_id) == 16:
        formatted = f"{clean_id[:4]}-{clean_id[4:8]}-{clean_id[8:12]}-{clean_id[12:]}"
        return f"https://orcid.org/{formatted}"
    elif len(clean_id) == 15 and clean_id[15] in ['X', 'x']:
        formatted = f"{clean_id[:4]}-{clean_id[4:8]}-{clean_id[8:12]}-{clean_id[12:15]}X"
        return f"https://orcid.org/{formatted}"
    else:
        return f"https://orcid.org/{clean_id}"

def parse_orcids(text: str) -> List[str]:
    """Парсит ORCID из текста. Поддерживает множественный ввод."""
    if not text or not text.strip():
        return []
    
    # Заменяем разделители на пробелы
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = text.replace(',', ' ').replace(';', ' ')
    
    # Ищем все ORCID в тексте
    orcid_pattern = r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]'
    matches = re.findall(orcid_pattern, text, re.IGNORECASE)
    
    # Также ищем URL с ORCID
    url_pattern = r'orcid\.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])'
    url_matches = re.findall(url_pattern, text, re.IGNORECASE)
    
    all_orcids = matches + url_matches
    
    # Очищаем и возвращаем уникальные
    cleaned = [clean_orcid(o) for o in all_orcids]
    return list(dict.fromkeys(cleaned))

async def fetch_with_retry(session, url, params=None, headers=None, method='GET'):
    """Выполняет запрос с повторными попытками при ошибке"""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.request(method, url, params=params, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', RETRY_DELAY * (attempt + 1)))
                    if SHOW_DEBUG_LOGS:
                        print(f"⚠️ Rate limit, ждем {retry_after} сек...")
                    await asyncio.sleep(retry_after)
                    continue
                
                if response.status == 200:
                    return await response.json()
                else:
                    if SHOW_DEBUG_LOGS:
                        print(f"⚠️ Ошибка {response.status} для {url}")
                    return None
        except Exception as e:
            if SHOW_DEBUG_LOGS:
                print(f"⚠️ Попытка {attempt+1}/{MAX_RETRIES} ошибка: {str(e)[:100]}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return None
    return None

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def safe_get(data, *keys, default=None):
    """Безопасное получение значения из вложенного словаря"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def get_cache_path(orcid: str) -> str:
    """Возвращает путь к файлу кэша для ORCID"""
    orcid_clean = clean_orcid(orcid)
    if not os.path.exists('cache'):
        os.makedirs('cache')
    return f"cache/{orcid_clean}.json"

def load_from_cache(orcid: str) -> Optional[Dict]:
    """Загружает данные из кэша"""
    if not USE_CACHE:
        return None
    
    cache_path = get_cache_path(orcid)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Загружено из кэша: {cache_path}")
            return data
        except Exception as e:
            print(f"⚠️ Ошибка загрузки кэша: {e}")
            return None
    return None

def save_to_cache(orcid: str, data: Dict):
    """Сохраняет данные в кэш"""
    if not USE_CACHE:
        return
    
    cache_path = get_cache_path(orcid)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Данные сохранены в кэш: {cache_path}")
    except Exception as e:
        print(f"⚠️ Ошибка сохранения кэша: {e}")

# ============================================
# ФУНКЦИЯ ПАРСИНГА ПУБЛИКАЦИИ ИЗ OPENALEX
# ============================================

def parse_openalex_publication(item: Dict) -> Dict:
    """Парсит публикацию из OpenAlex с расширенной информацией по темам и институтам"""
    try:
        pub = {}
        
        pub['id'] = item.get('id', '')
        pub['doi'] = item.get('doi', '').replace('https://doi.org/', '')
        pub['title'] = item.get('title', 'No title')
        pub['publication_year'] = item.get('publication_year')
        
        pub['type'] = item.get('type', 'unknown')
        
        if item.get('primary_location'):
            source = item['primary_location'].get('source', {})
            pub['journal_name'] = source.get('display_name', 'Unknown')
            pub['publisher'] = source.get('host_organization_name') or source.get('publisher', 'Unknown')
            pub['issn'] = source.get('issn', [])
        else:
            pub['journal_name'] = 'Unknown'
            pub['publisher'] = 'Unknown'
            pub['issn'] = []
        
        oa = item.get('open_access', {})
        pub['is_oa'] = oa.get('is_oa', False)
        pub['open_access_status'] = oa.get('oa_status', 'closed')
        pub['oa_url'] = oa.get('oa_url', None)
        
        affiliations = []
        affiliation_countries = []
        institutions = []
        
        for auth in item.get('authorships', []):
            if auth.get('institutions'):
                for inst in auth['institutions']:
                    affil = inst.get('display_name', '')
                    if affil:
                        affiliations.append(affil)
                        country = extract_country_from_affiliation(affil)
                        if country:
                            affiliation_countries.append(country)
                        
                        institutions.append({
                            'id': inst.get('id', ''),
                            'display_name': inst.get('display_name', ''),
                            'country_code': inst.get('country_code', ''),
                            'ror': inst.get('ror', ''),
                            'type': inst.get('type', ''),
                            'lineage': inst.get('lineage', [])
                        })
        
        pub['affiliations'] = affiliations
        pub['affiliation_countries'] = affiliation_countries
        pub['institutions'] = institutions
        
        if affiliations:
            pub['country'] = extract_country_from_affiliation(affiliations[0])
        else:
            pub['country'] = 'Unknown'
        
        authors = []
        author_orcids = []
        for auth in item.get('authorships', []):
            if auth.get('author'):
                author_name = auth['author'].get('display_name', '')
                author_orcid = auth['author'].get('orcid', '')
                if author_name:
                    authors.append(author_name)
                    if author_orcid:
                        author_orcids.append(author_orcid)
        pub['authors'] = authors
        pub['author_orcids'] = author_orcids
        
        pub['author_count'] = len(authors)
        
        primary_topic = item.get('primary_topic', {})
        if primary_topic:
            pub['primary_topic'] = {
                'display_name': primary_topic.get('display_name', ''),
                'subfield': primary_topic.get('subfield', {}).get('display_name', ''),
                'field': primary_topic.get('field', {}).get('display_name', ''),
                'domain': primary_topic.get('domain', {}).get('display_name', ''),
                'score': primary_topic.get('score', 0)
            }
        else:
            pub['primary_topic'] = None
        
        topics_list = item.get('topics', [])
        pub['topics'] = [
            {
                'display_name': t.get('display_name', ''),
                'subfield': t.get('subfield', {}).get('display_name', ''),
                'field': t.get('field', {}).get('display_name', ''),
                'domain': t.get('domain', {}).get('display_name', ''),
                'score': t.get('score', 0)
            }
            for t in topics_list
        ]
        
        keywords = item.get('keywords', [])
        pub['keywords'] = [k.get('display_name', '') for k in keywords if k.get('display_name')]
        
        concepts = []
        concept_levels = {}
        fields = []
        domains = []
        topics_old = []
        subtopics = []
        
        for concept in item.get('concepts', []):
            concept_name = concept.get('display_name', '')
            concept_level = concept.get('level', 0)
            concept_score = concept.get('score', 0)
            
            if concept_name:
                concepts.append(concept_name)
                concept_levels[concept_name] = {
                    'level': concept_level,
                    'score': concept_score
                }
            
            if concept_level >= 3:
                domains.append(concept_name)
            elif concept_level == 2:
                fields.append(concept_name)
            elif concept_level == 1:
                topics_old.append(concept_name)
            elif concept_level == 0:
                subtopics.append(concept_name)
        
        pub['concepts'] = concepts[:15]
        pub['concept_levels'] = concept_levels
        pub['fields'] = fields[:10]
        pub['domains'] = domains[:5]
        pub['topics_old'] = topics_old[:15]
        pub['subtopics'] = subtopics[:20]
        
        pub['cited_by_count'] = item.get('cited_by_count', 0)
        pub['cited_by_percentile'] = item.get('cited_by_percentile', {})
        
        pub['is_retracted'] = item.get('is_retracted', False)
        pub['is_correction'] = item.get('is_correction', False)
        pub['is_paratext'] = item.get('is_paratext', False)
        
        if pub['is_retracted']:
            pub['retraction_info'] = item.get('retraction_info', {})
        
        pub['publication_date'] = item.get('publication_date')
        pub['created_date'] = item.get('created_date')
        pub['updated_date'] = item.get('updated_date')
        
        return pub
        
    except Exception as e:
        if SHOW_DEBUG_LOGS:
            print(f"⚠️ Ошибка парсинга публикации: {e}")
        return None

# ============================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ДАННЫХ ИЗ API
# ============================================

async def get_orcid_dois(orcid: str, session) -> Set[str]:
    """Получает список DOI из профиля ORCID"""
    orcid = clean_orcid(orcid)
    
    if not orcid:
        return set()
    
    headers = {'Accept': 'application/json'}
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    
    if SHOW_DEBUG_LOGS:
        print(f"🔍 Запрос к ORCID: {orcid}")
    
    data = await fetch_with_retry(session, url, headers=headers)
    
    if not data:
        print(f"❌ Не удалось получить данные из ORCID для {orcid}")
        return set()
    
    dois = set()
    
    try:
        works = data.get('group', [])
        
        for work_group in works:
            work_summary = work_group.get('work-summary', [])
            for work in work_summary:
                external_ids = work.get('external-ids', {})
                if external_ids:
                    for ext_id in external_ids.get('external-id', []):
                        if ext_id.get('external-id-type') == 'doi':
                            doi = ext_id.get('external-id-value', '').lower()
                            if doi:
                                doi = doi.replace('http://dx.doi.org/', '').replace('https://doi.org/', '')
                                dois.add(doi)
    except Exception as e:
        print(f"⚠️ Ошибка парсинга ORCID: {e}")
    
    if SHOW_DEBUG_LOGS:
        print(f"✅ Найдено {len(dois)} DOI в ORCID")
    
    return dois

async def get_openalex_metadata(dois: List[str], session) -> List[Dict]:
    """Получает полные метаданные из OpenAlex для списка DOI"""
    if not dois:
        return []
    
    doi_query = '|'.join(dois[:50])
    
    params = {
        'filter': f'doi:{doi_query}',
        'per-page': len(dois)
    }
    
    url = "https://api.openalex.org/works"
    
    if SHOW_DEBUG_LOGS:
        print(f"📖 Запрос к OpenAlex: {len(dois)} DOI")
    
    data = await fetch_with_retry(session, url, params=params)
    
    if not data:
        return []
    
    results = data.get('results', [])
    
    if SHOW_DEBUG_LOGS:
        print(f"✅ Получено метаданных: {len(results)} записей")
    
    return results

async def get_openalex_author(orcid: str, session) -> Dict:
    """Получает информацию об авторе из OpenAlex по ORCID"""
    if not orcid:
        return {}
    
    orcid_clean = clean_orcid(orcid)
    
    params = {
        'filter': f'orcid:{orcid_clean}',
        'per-page': 1
    }
    
    url = "https://api.openalex.org/authors"
    data = await fetch_with_retry(session, url, params=params)
    
    if not data:
        return {}
    
    results = data.get('results', [])
    if results:
        author = results[0]
        return {
            'display_name': author.get('display_name', 'Unknown'),
            'orcid': author.get('orcid', '').replace('https://orcid.org/', ''),
            'affiliations': [
                {
                    'institution': aff.get('institution', {}).get('display_name', ''),
                    'country': aff.get('institution', {}).get('country_code', '')
                }
                for aff in author.get('affiliations', [])
            ],
            'works_count': author.get('works_count', 0),
            'cited_by_count': author.get('cited_by_count', 0),
            'h_index': author.get('h_index', 0),
            'last_known_institution': author.get('last_known_institution', {}).get('display_name', '')
        }
    
    return {}

async def get_openalex_author_by_name(author_name: str, session) -> Dict:
    """Ищет автора в OpenAlex по имени"""
    if not author_name:
        return {}
    
    params = {
        'filter': f'display_name.search:{author_name}',
        'per-page': 1
    }
    
    url = "https://api.openalex.org/authors"
    data = await fetch_with_retry(session, url, params=params)
    
    if not data:
        return {}
    
    results = data.get('results', [])
    return results[0] if results else {}

async def get_institution_homepages(institution_ids: List[str], session) -> Dict[str, str]:
    """Получает homepage для списка институтов из OpenAlex (задача 4)"""
    if not institution_ids:
        return {}
    
    unique_ids = list(set([id for id in institution_ids if id]))
    
    if not unique_ids:
        return {}
    
    homepages = {}
    
    for batch in chunks(unique_ids, 50):
        id_query = '|'.join([id.replace('https://openalex.org/', '') for id in batch])
        url = f"https://api.openalex.org/institutions"
        params = {
            'filter': f'openalex:{id_query}',
            'per-page': len(batch)
        }
        
        data = await fetch_with_retry(session, url, params=params)
        
        if data and data.get('results'):
            for inst in data['results']:
                inst_id = inst.get('id', '')
                homepage = inst.get('homepage_url', '')
                if inst_id and homepage:
                    homepages[inst_id] = homepage
        
        await asyncio.sleep(DELAY_BETWEEN_BATCHES)
    
    return homepages

# ============================================
# КЛАСС ДЛЯ АНАЛИЗА ПРОФИЛЯ УЧЕНОГО
# ============================================

class ScholarProfileAnalyzer:
    def __init__(self, orcid: str):
        self.orcid = clean_orcid(orcid)
        self.publications = []
        self.author_info = {}
        self.author_name = None
        self.author_affiliations = []
        self.author_countries = []
        self.profile = {}
        self.raw_data = {}
        self.institution_homepages = {}
        self.collaborations = {
            'domestic': defaultdict(lambda: defaultdict(int)),
            'international': defaultdict(lambda: defaultdict(int)),
            'domestic_papers': 0,
            'international_papers': 0,
            'mixed_papers': 0,
            'total_collaborations': 0
        }
        
    def add_publication(self, pub_data: Dict):
        """Добавляет публикацию для анализа"""
        self.publications.append(pub_data)
    
    def set_author_info(self, author_info: Dict):
        """Устанавливает информацию об авторе"""
        self.author_info = author_info
        self.author_name = author_info.get('display_name', 'Unknown')
        
        for aff in author_info.get('affiliations', []):
            inst_name = aff.get('institution', '')
            country = aff.get('country', '')
            if inst_name and inst_name not in self.author_affiliations:
                self.author_affiliations.append(inst_name)
                if country and country not in self.author_countries:
                    self.author_countries.append(country)
        
        if not self.author_affiliations and self.publications:
            for pub in self.publications:
                if pub.get('affiliations'):
                    for aff in pub['affiliations']:
                        if aff not in self.author_affiliations:
                            self.author_affiliations.append(aff)
                    if pub.get('country') and pub['country'] not in self.author_countries:
                        self.author_countries.append(pub['country'])
    
    def set_institution_homepages(self, homepages: Dict[str, str]):
        """Устанавливает homepage для институтов"""
        self.institution_homepages = homepages
    
    def analyze_publications(self):
        """Анализирует все публикации и строит профиль"""
        if not self.publications:
            print("⚠️ Нет публикаций для анализа")
            return
        
        print(f"📊 Анализирую {len(self.publications)} публикаций...")
        
        self.profile['total_publications'] = len(self.publications)
        self.profile['orcid'] = self.orcid
        self.profile['author_name'] = self.author_name or 'Unknown'
        self.profile['author_affiliations'] = self.author_affiliations
        self.profile['author_countries'] = self.author_countries
        
        years = [p.get('publication_year') for p in self.publications if p.get('publication_year')]
        self.profile['years_distribution'] = dict(Counter(years))
        self.profile['first_publication'] = min(years) if years else None
        self.profile['last_publication'] = max(years) if years else None
        self.profile['active_years'] = len(set(years)) if years else 0
        
        journals = [p.get('journal_name') for p in self.publications if p.get('journal_name')]
        self.profile['journals'] = dict(Counter(journals))
        self.profile['top_journals'] = dict(Counter(journals).most_common(10))
        
        publishers = [p.get('publisher') for p in self.publications if p.get('publisher') and p.get('publisher') != 'Unknown']
        self.profile['publishers'] = dict(Counter(publishers))
        
        pub_types = [p.get('type') for p in self.publications if p.get('type')]
        self.profile['publication_types'] = dict(Counter(pub_types))
        
        oa_statuses = [p.get('open_access_status') for p in self.publications if p.get('open_access_status')]
        self.profile['open_access'] = dict(Counter(oa_statuses))
        self.profile['total_oa'] = sum(1 for p in self.publications if p.get('is_oa', False))
        self.profile['oa_percentage'] = (self.profile['total_oa'] / len(self.publications) * 100) if self.publications else 0
        
        affiliations = []
        affiliation_countries = []
        all_institutions = []
        
        for p in self.publications:
            if p.get('affiliations'):
                affiliations.extend(p['affiliations'])
            if p.get('affiliation_countries'):
                affiliation_countries.extend(p['affiliation_countries'])
            if p.get('institutions'):
                all_institutions.extend(p['institutions'])
        
        self.profile['affiliations'] = dict(Counter(affiliations))
        self.profile['top_affiliations'] = dict(Counter(affiliations).most_common(5))
        self.profile['countries_all'] = dict(Counter(affiliation_countries))
        self.profile['all_institutions'] = all_institutions
        
        countries = [p.get('country') for p in self.publications if p.get('country')]
        self.profile['countries'] = dict(Counter(countries))
        
        all_concepts = []
        all_fields = []
        all_domains = []
        all_topics = []
        all_subtopics = []
        concept_levels = {}
        
        all_primary_topics = []
        all_topics_new = []
        all_subfields = []
        all_keywords = []
        
        for p in self.publications:
            if p.get('concepts'):
                all_concepts.extend(p['concepts'])
            if p.get('fields'):
                all_fields.extend(p['fields'])
            if p.get('domains'):
                all_domains.extend(p['domains'])
            if p.get('topics_old'):
                all_topics.extend(p['topics_old'])
            if p.get('subtopics'):
                all_subtopics.extend(p['subtopics'])
            
            if p.get('primary_topic'):
                pt = p['primary_topic']
                if pt.get('display_name'):
                    all_primary_topics.append(pt['display_name'])
                if pt.get('subfield'):
                    all_subfields.append(pt['subfield'])
            
            if p.get('topics'):
                for t in p['topics']:
                    if t.get('display_name'):
                        all_topics_new.append(t['display_name'])
                    if t.get('subfield'):
                        all_subfields.append(t['subfield'])
                    if t.get('field'):
                        all_fields.append(t['field'])
                    if t.get('domain'):
                        all_domains.append(t['domain'])
            
            if p.get('keywords'):
                all_keywords.extend(p['keywords'])
            
            if p.get('concept_levels'):
                for concept, info in p['concept_levels'].items():
                    if concept not in concept_levels:
                        concept_levels[concept] = []
                    concept_levels[concept].append(info)
        
        self.profile['concepts'] = dict(Counter(all_concepts))
        self.profile['top_concepts'] = dict(Counter(all_concepts).most_common(15))
        self.profile['fields'] = dict(Counter(all_fields))
        self.profile['top_fields'] = dict(Counter(all_fields).most_common(10))
        self.profile['domains'] = dict(Counter(all_domains))
        self.profile['top_domains'] = dict(Counter(all_domains).most_common(5))
        self.profile['topics'] = dict(Counter(all_topics))
        self.profile['top_topics'] = dict(Counter(all_topics).most_common(15))
        self.profile['subtopics'] = dict(Counter(all_subtopics))
        self.profile['top_subtopics'] = dict(Counter(all_subtopics).most_common(20))
        self.profile['concept_levels'] = concept_levels
        
        self.profile['primary_topics'] = dict(Counter(all_primary_topics))
        self.profile['top_primary_topics'] = dict(Counter(all_primary_topics).most_common(10))
        self.profile['topics_new'] = dict(Counter(all_topics_new))
        self.profile['top_topics_new'] = dict(Counter(all_topics_new).most_common(15))
        self.profile['subfields'] = dict(Counter(all_subfields))
        self.profile['top_subfields'] = dict(Counter(all_subfields).most_common(10))
        self.profile['keywords'] = dict(Counter(all_keywords))
        self.profile['top_keywords'] = dict(Counter(all_keywords).most_common(20))
        
        self.profile['retractions'] = sum(1 for p in self.publications if p.get('is_retracted', False))
        self.profile['corrections'] = sum(1 for p in self.publications if p.get('is_correction', False))
        self.profile['paratexts'] = sum(1 for p in self.publications if p.get('is_paratext', False))
        self.profile['retraction_details'] = [p.get('retraction_info') for p in self.publications if p.get('is_retracted')]
        
        coauthors = []
        coauthors_with_orcid = {}
        
        author_name_normalized = normalize_author_name(self.author_name or '')
        author_orcid = self.orcid
        
        for p in self.publications:
            if p.get('authors'):
                authors_list = p['authors']
                orcids_list = p.get('author_orcids', [])
                
                for idx, name in enumerate(authors_list):
                    is_self = False
                    
                    if author_name_normalized:
                        name_normalized = normalize_author_name(name)
                        if name_normalized == author_name_normalized:
                            is_self = True
                    
                    if not is_self and orcids_list and idx < len(orcids_list):
                        orcid_val = orcids_list[idx]
                        if orcid_val and (orcid_val == author_orcid or orcid_val.replace('https://orcid.org/', '') == author_orcid):
                            is_self = True
                    
                    if not is_self:
                        coauthors.append(name)
                        if orcids_list and idx < len(orcids_list):
                            orcid_val = orcids_list[idx]
                            if orcid_val:
                                coauthors_with_orcid[name] = orcid_val.replace('https://orcid.org/', '')
        
        self.profile['coauthors'] = dict(Counter(coauthors))
        self.profile['top_coauthors'] = dict(Counter(coauthors).most_common(20))
        self.profile['coauthors_with_orcid'] = coauthors_with_orcid
        self.profile['unique_coauthors'] = len(set(coauthors))
        
        author_counts = [p.get('author_count', 0) for p in self.publications if p.get('author_count', 0) > 0]
        if author_counts:
            self.profile['avg_authors_per_paper'] = np.mean(author_counts)
            self.profile['median_authors_per_paper'] = np.median(author_counts)
            self.profile['max_authors_per_paper'] = max(author_counts)
            self.profile['min_authors_per_paper'] = min(author_counts)
        
        citations = [p.get('cited_by_count', 0) for p in self.publications]
        self.profile['total_citations'] = sum(citations)
        self.profile['average_citations'] = sum(citations) / len(citations) if citations else 0
        self.profile['median_citations'] = np.median(citations) if citations else 0
        self.profile['max_citations'] = max(citations) if citations else 0
        self.profile['citations_per_year'] = self.profile['total_citations'] / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        
        citation_bins = [0, 1, 5, 10, 20, 50, 100, 500, 1000]
        citation_dist = {}
        for i in range(len(citation_bins)-1):
            lower = citation_bins[i]
            upper = citation_bins[i+1]
            citation_dist[f"{lower}-{upper}"] = sum(1 for c in citations if lower <= c < upper)
        citation_dist[f">{citation_bins[-1]}"] = sum(1 for c in citations if c >= citation_bins[-1])
        self.profile['citation_distribution'] = citation_dist
        
        citations_sorted = sorted([c for c in citations if c > 0], reverse=True)
        h_index = 0
        for i, c in enumerate(citations_sorted, 1):
            if c >= i:
                h_index = i
            else:
                break
        self.profile['h_index'] = h_index
        
        self.profile['i10_index'] = sum(1 for c in citations if c >= 10)
        
        total_citations_sorted = 0
        g_index = 0
        for i, c in enumerate(citations_sorted, 1):
            total_citations_sorted += c
            if total_citations_sorted >= i**2:
                g_index = i
        self.profile['g_index'] = g_index
        
        sorted_pubs = sorted(self.publications, key=lambda x: x.get('cited_by_count', 0), reverse=True)
        self.profile['most_cited'] = [
            {
                'title': p.get('title', 'No title'),
                'citations': p.get('cited_by_count', 0),
                'year': p.get('publication_year', 'Unknown'),
                'journal': p.get('journal_name', 'Unknown'),
                'doi': p.get('doi', '')
            }
            for p in sorted_pubs[:10]
        ]
        
        if years:
            sorted_years = sorted(set(years))
            year_counts = Counter(years)
            years_range = range(min(sorted_years), max(sorted_years) + 1)
            counts = [year_counts.get(y, 0) for y in years_range]
            
            if len(counts) >= 3:
                x = np.arange(len(counts))
                z = np.polyfit(x, counts, 1)
                self.profile['trend_slope'] = z[0]
                self.profile['trend_intercept'] = z[1]
                
                if len(counts) > 1:
                    corr_matrix = np.corrcoef(x, counts)
                    self.profile['trend_correlation'] = corr_matrix[0, 1] if len(corr_matrix) > 1 else 0
                
                if z[0] > 1.0:
                    self.profile['trend_direction'] = 'strong_up'
                elif z[0] > 0.3:
                    self.profile['trend_direction'] = 'up'
                elif z[0] < -1.0:
                    self.profile['trend_direction'] = 'strong_down'
                elif z[0] < -0.3:
                    self.profile['trend_direction'] = 'down'
                else:
                    self.profile['trend_direction'] = 'stable'
            else:
                self.profile['trend_direction'] = 'stable'
                self.profile['trend_correlation'] = 0
        
        self.profile['papers_per_year'] = len(self.publications) / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        self.profile['recent_productivity'] = len([y for y in years if y >= (datetime.now().year - 3)]) / 3 if years else 0
        self.profile['productivity_peak_year'] = max(year_counts.items(), key=lambda x: x[1])[0] if year_counts else None
        self.profile['productivity_peak_count'] = max(year_counts.values()) if year_counts else 0
        
        oa_types = {'gold': 0, 'green': 0, 'hybrid': 0, 'bronze': 0, 'closed': 0}
        for p in self.publications:
            status = p.get('open_access_status', 'closed')
            if status in oa_types:
                oa_types[status] += 1
        self.profile['oa_types'] = oa_types
        
        if all_concepts:
            concept_counts = Counter(all_concepts)
            total = len(all_concepts)
            shannon_index = 0
            for count in concept_counts.values():
                p = count / total
                shannon_index -= p * np.log(p)
            self.profile['thematic_diversity_shannon'] = shannon_index
            self.profile['unique_concepts'] = len(concept_counts)
        
        self._analyze_collaborations()
        
        self.profile['risk_flags'] = self._assess_risks()
        
        self.profile['recommendation'] = self._generate_recommendation()
        
        print("✅ Анализ завершен!")
    
    def _analyze_collaborations(self):
        """Анализирует коллаборации с детальным разбором по аффилиациям (задача 1 и 4)"""
        if not self.publications:
            return
        
        author_countries_set = set(self.author_countries) if self.author_countries else set()
        
        if not author_countries_set:
            for p in self.publications:
                if p.get('country') and p['country'] != 'Unknown':
                    author_countries_set.add(p['country'])
        
        if not author_countries_set:
            author_countries_set = {'Unknown'}
        
        self.collaborations = {
            'domestic': defaultdict(lambda: defaultdict(int)),
            'international': defaultdict(lambda: defaultdict(int)),
            'domestic_papers': 0,
            'international_papers': 0,
            'mixed_papers': 0,
            'total_collaborations': 0
        }
        
        domestic_papers = 0
        international_papers = 0
        mixed_papers = 0
        
        for p in self.publications:
            institutions = p.get('institutions', [])
            if not institutions:
                continue
            
            paper_countries = set()
            paper_affiliations = set()
            
            for inst in institutions:
                country = inst.get('country_code', '')
                if country:
                    paper_countries.add(country)
                affil_name = inst.get('display_name', '')
                if affil_name:
                    paper_affiliations.add(affil_name)
            
            paper_countries = {c for c in paper_countries if c and c != 'Unknown'}
            
            if not paper_countries:
                continue
            
            has_author_country = any(c in author_countries_set for c in paper_countries)
            has_other_countries = any(c not in author_countries_set for c in paper_countries)
            
            if has_author_country and not has_other_countries:
                domestic_papers += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country in author_countries_set and affil_name:
                        self.collaborations['domestic'][country][affil_name] += 1
                        
            elif has_author_country and has_other_countries:
                mixed_papers += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country in author_countries_set and affil_name:
                        self.collaborations['domestic'][country][affil_name] += 1
                    elif country not in author_countries_set and country and affil_name:
                        self.collaborations['international'][country][affil_name] += 1
                        
            elif has_other_countries and not has_author_country:
                international_papers += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country and country not in author_countries_set and affil_name:
                        self.collaborations['international'][country][affil_name] += 1
        
        self.collaborations['domestic_papers'] = domestic_papers
        self.collaborations['international_papers'] = international_papers
        self.collaborations['mixed_papers'] = mixed_papers
        self.collaborations['total_collaborations'] = domestic_papers + international_papers + mixed_papers
        
        self.profile['collaborations'] = self.collaborations
        self.profile['domestic_papers_ratio'] = domestic_papers / len(self.publications) if self.publications else 0
        self.profile['international_papers_ratio'] = international_papers / len(self.publications) if self.publications else 0
        self.profile['collaboration_index'] = self.profile.get('avg_authors_per_paper', 0) - 1 if self.profile.get('avg_authors_per_paper', 0) > 0 else 0
        
        all_collab = {}
        for country, affils in self.collaborations['international'].items():
            total = sum(affils.values())
            all_collab[country] = total
        
        for country, affils in self.collaborations['domestic'].items():
            total = sum(affils.values())
            all_collab[country] = all_collab.get(country, 0) + total
        
        self.profile['most_collaborative_country'] = max(all_collab.items(), key=lambda x: x[1])[0] if all_collab else 'None'
        self.profile['country_diversity'] = len(set(self.author_countries) | set(all_collab.keys()))
    
    def _assess_risks(self) -> List[str]:
        """Оценивает риски и возвращает список предупреждений"""
        flags = []
        
        if self.profile.get('papers_per_year', 0) > 30:
            flags.append("⚠️ Аномально высокая продуктивность (>30 статей в год)")
        
        if self.profile.get('retractions', 0) > 1:
            flags.append(f"🔴 {self.profile['retractions']} ретракций в профиле")
        
        if self.profile.get('top_journals'):
            top_ratio = list(self.profile['top_journals'].values())[0] / self.profile['total_publications']
            if top_ratio > 0.3:
                flags.append("⚠️ >30% публикаций в одном журнале")
        
        suspicious_journals = ['Cureus', 'PLoS ONE', 'Scientific Reports']
        suspicious_pubs = [j for j in self.profile.get('journals', {}).keys() if any(s in j for s in suspicious_journals)]
        if suspicious_pubs:
            flags.append(f"⚠️ Публикации в журналах с низкой селективностью: {', '.join(suspicious_pubs[:3])}")
        
        if self.profile.get('unique_concepts', 0) < 5 and self.profile.get('total_publications', 0) > 10:
            flags.append("⚠️ Низкое тематическое разнообразие")
        
        if self.profile.get('international_papers_ratio', 0) < 0.1 and self.profile.get('total_publications', 0) > 20:
            flags.append("⚠️ Низкий уровень международного сотрудничества")
        
        return flags
    
    def _generate_recommendation(self) -> str:
        """Генерирует рекомендацию для редактора"""
        risk_count = len(self.profile.get('risk_flags', []))
        total_pubs = self.profile.get('total_publications', 0)
        h_index = self.profile.get('h_index', 0)
        trend = self.profile.get('trend_direction', 'stable')
        
        if risk_count >= 3:
            return "🔴 Требуется дополнительная проверка. Обнаружены множественные красные флаги."
        elif risk_count >= 1:
            return "🟡 Рекомендуется осторожность. Есть отдельные предупреждения."
        elif total_pubs >= 30 and h_index >= 15 and trend in ['up', 'strong_up']:
            return "🟢 Выдающийся ученый. Высокая продуктивность и растущий h-index."
        elif total_pubs >= 20 and h_index >= 10:
            return "🟢 Сильный кандидат. Стабильная публикационная активность."
        elif total_pubs >= 10 and h_index >= 5:
            return "🟢 Перспективный ученый. Рекомендуется к рассмотрению."
        elif total_pubs >= 5:
            return "🟢 Начинающий исследователь. Требуется экспертная оценка."
        else:
            return "🟢 Молодой ученый. Статьи требуют тщательного рецензирования."
    
    def get_profile_data(self) -> Dict:
        """Возвращает полный профиль"""
        return self.profile
    
    def get_publications(self) -> List[Dict]:
        """Возвращает список публикаций"""
        return self.publications

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ СБОРА ДАННЫХ
# ============================================

async def collect_scholar_data(orcid: str) -> Tuple[ScholarProfileAnalyzer, Dict, List[Dict]]:
    """Собирает все данные для профиля ученого"""
    
    orcid_clean = clean_orcid(orcid)
    
    if not orcid_clean:
        print(f"❌ Неверный формат ORCID: {orcid}")
        return None, {}, []
    
    print(f"🚀 Начинаем сбор данных для ORCID: {orcid_clean}")
    
    cached_data = load_from_cache(orcid_clean)
    if cached_data:
        print("📦 Использую данные из кэша")
        analyzer = ScholarProfileAnalyzer(orcid_clean)
        
        if 'publications' in cached_data:
            for pub in cached_data['publications']:
                analyzer.add_publication(pub)
        
        if 'author_info' in cached_data:
            analyzer.set_author_info(cached_data['author_info'])
        
        if 'profile' in cached_data:
            analyzer.profile = cached_data['profile']
        
        if 'institution_homepages' in cached_data:
            analyzer.set_institution_homepages(cached_data['institution_homepages'])
        
        return analyzer, analyzer.profile, analyzer.publications
    
    analyzer = ScholarProfileAnalyzer(orcid_clean)
    
    async with aiohttp.ClientSession() as session:
        
        print("🔍 Получение информации об авторе...")
        author_info = await get_openalex_author(orcid_clean, session)
        if author_info:
            analyzer.set_author_info(author_info)
            print(f"👤 Автор: {author_info.get('display_name', 'Unknown')}")
            if analyzer.author_affiliations:
                print(f"🏛️ Аффилиации: {', '.join(analyzer.author_affiliations[:3])}")
        
        orcid_dois = await get_orcid_dois(orcid_clean, session)
        
        if not orcid_dois:
            print("❌ Не найдено DOI в профиле ORCID")
            return analyzer, {}, []
        
        all_dois = list(orcid_dois)
        total_dois = len(all_dois)
        
        if total_dois > MAX_PUBLICATIONS_TO_ANALYZE:
            print(f"⚠️ Найдено {total_dois} статей. Анализирую только последние {MAX_PUBLICATIONS_TO_ANALYZE}...")
            all_dois = all_dois[:MAX_PUBLICATIONS_TO_ANALYZE]
        
        print(f"📝 Всего DOI для анализа: {len(all_dois)}")
        
        all_metadata = []
        
        doi_batches = list(chunks(all_dois, BATCH_SIZE))
        
        # Вместо tqdm используем простой вывод прогресса
        print(f"📚 Обработка {len(doi_batches)} батчей метаданных OpenAlex...")
        
        for batch_idx, batch in enumerate(doi_batches, 1):
            print(f"  Батч {batch_idx}/{len(doi_batches)} (найдено {len(all_metadata)}/{len(all_dois)} DOI)...")
            batch_metadata = await get_openalex_metadata(batch, session)
            all_metadata.extend(batch_metadata)
            
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)
        
        print(f"✅ Собрано метаданных: {len(all_metadata)} записей")
        
        print("📊 Обработка публикаций...")
        
        for idx, item in enumerate(all_metadata, 1):
            if idx % 10 == 0 or idx == len(all_metadata):
                print(f"  Обработано {idx}/{len(all_metadata)} публикаций...")
            pub_data = parse_openalex_publication(item)
            if pub_data:
                analyzer.add_publication(pub_data)
        
        print("🏛️ Получение homepage для институтов...")
        all_institution_ids = []
        for pub in analyzer.publications:
            for inst in pub.get('institutions', []):
                inst_id = inst.get('id', '')
                if inst_id:
                    all_institution_ids.append(inst_id)
        
        if all_institution_ids:
            homepages = await get_institution_homepages(all_institution_ids, session)
            analyzer.set_institution_homepages(homepages)
            print(f"✅ Получено homepage для {len(homepages)} институтов")
        
        analyzer.analyze_publications()
        
        cache_data = {
            'publications': analyzer.publications,
            'author_info': analyzer.author_info,
            'profile': analyzer.profile,
            'institution_homepages': analyzer.institution_homepages,
            'timestamp': datetime.now().isoformat()
        }
        save_to_cache(orcid_clean, cache_data)
        
        return analyzer, analyzer.profile, analyzer.publications

# ============================================
# ФУНКЦИИ ДЛЯ АНАЛИЗА МНОЖЕСТВЕННЫХ АВТОРОВ
# ============================================

async def analyze_multiple_authors(orcid_list: List[str], progress_callback=None) -> List[Dict]:
    """Анализирует несколько авторов параллельно"""
    results = []
    total = len(orcid_list)
    
    for idx, orcid in enumerate(orcid_list):
        if progress_callback:
            progress_callback(idx + 1, total, orcid)
        
        analyzer, profile, publications = await collect_scholar_data(orcid)
        if profile:
            results.append({
                'orcid': orcid,
                'analyzer': analyzer,
                'profile': profile,
                'publications': publications,
                'author_name': profile.get('author_name', 'Unknown'),
                'h_index': profile.get('h_index', 0),
                'total_publications': profile.get('total_publications', 0),
                'total_citations': profile.get('total_citations', 0),
                'author_affiliations': profile.get('author_affiliations', [])
            })
    
    return results

def sort_authors_by_h_index(authors: List[Dict]) -> List[Dict]:
    """Сортирует авторов по убыванию h-index"""
    return sorted(authors, key=lambda x: x.get('h_index', 0), reverse=True)

# ============================================
# ФУНКЦИИ ДЛЯ ВИЗУАЛИЗАЦИИ (НАУЧНЫЙ СТИЛЬ)
# ============================================

def create_visualizations(profile: Dict) -> Dict[str, str]:
    """Создает визуализации в научном стиле и возвращает их в виде base64 изображений"""
    images = {}
    
    apply_scientific_style()
    
    if profile.get('years_distribution'):
        fig, ax = plt.subplots(figsize=(10, 6))
        years = sorted(profile['years_distribution'].keys())
        counts = [profile['years_distribution'][y] for y in years]
        
        bars = ax.bar(years, counts, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('Год публикации', fontsize=12, fontweight='bold')
        ax.set_ylabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Динамика публикационной активности', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        ax.set_xticks(years)
        ax.set_xticklabels([str(int(y)) for y in years], rotation=45)
        
        if len(years) >= 2:
            x = np.arange(len(years))
            z = np.polyfit(x, counts, 1)
            p = np.poly1d(z)
            
            x_extended = np.arange(len(years) + 2)
            y_extended = p(x_extended)
            
            ax.plot(years, p(x), 'r-', linewidth=2.5, alpha=0.8, label='Тренд')
            
            if len(counts) > 3:
                std_err = np.std(counts - p(x)) / np.sqrt(len(counts))
                ax.fill_between(years, p(x) - 1.96*std_err, p(x) + 1.96*std_err, 
                               alpha=0.15, color='red', label='Доверительный интервал')
            
            if profile.get('trend_correlation'):
                corr = profile['trend_correlation']
                ax.text(0.02, 0.95, f'R² = {corr**2:.3f}', transform=ax.transAxes,
                       fontsize=11, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax.legend(loc='upper left', frameon=True, fancybox=False, edgecolor='black')
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['years_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('top_journals'):
        fig, ax = plt.subplots(figsize=(10, 8))
        journals = list(profile['top_journals'].keys())[:10]
        counts = list(profile['top_journals'].values())[:10]
        
        sorted_pairs = sorted(zip(counts, journals), reverse=True)
        counts, journals = zip(*sorted_pairs)
        
        y_pos = np.arange(len(journals))
        bars = ax.barh(y_pos, counts, color='#A23B72', alpha=0.8, edgecolor='black', linewidth=1.2)
        
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{count}', va='center', fontsize=10)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(journals, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Топ журналов по числу публикаций', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['journals_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('open_access'):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        oa_order = ['gold', 'green', 'hybrid', 'bronze', 'closed']
        oa_labels = {
            'gold': 'Gold OA',
            'green': 'Green OA',
            'hybrid': 'Hybrid OA',
            'bronze': 'Bronze OA',
            'closed': 'Closed Access'
        }
        oa_colors = {
            'gold': '#2ECC71',
            'green': '#3498DB',
            'hybrid': '#F1C40F',
            'bronze': '#E67E22',
            'closed': '#95A5A6'
        }
        
        oa_data = profile.get('open_access', {})
        sorted_labels = []
        sorted_counts = []
        sorted_colors = []
        
        for oa_type in oa_order:
            if oa_type in oa_data:
                sorted_labels.append(oa_labels.get(oa_type, oa_type))
                sorted_counts.append(oa_data[oa_type])
                sorted_colors.append(oa_colors.get(oa_type, '#95A5A6'))
        
        bars = ax.bar(sorted_labels, sorted_counts, color=sorted_colors, 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        
        for bar, count in zip(bars, sorted_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                   f'{count}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('Тип открытого доступа', fontsize=12, fontweight='bold')
        ax.set_ylabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Статус открытого доступа', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['oa_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('concepts'):
        wordcloud = WordCloud(width=1000, height=500, 
                              background_color='white',
                              colormap='viridis',
                              max_words=50,
                              contour_width=1,
                              contour_color='black',
                              random_state=42).generate_from_frequencies(profile['concepts'])
        
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('Ключевые концепты исследований', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['wordcloud'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('publishers'):
        fig, ax = plt.subplots(figsize=(10, 6))
        publishers = list(profile['publishers'].keys())[:8]
        counts = [profile['publishers'][p] for p in publishers]
        
        sorted_pairs = sorted(zip(counts, publishers), reverse=True)
        counts, publishers = zip(*sorted_pairs)
        
        bars = ax.bar(range(len(publishers)), counts, color='#5E4B56', alpha=0.8, 
                      edgecolor='black', linewidth=1.2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xticks(range(len(publishers)))
        ax.set_xticklabels(publishers, rotation=45, ha='right', fontsize=10)
        ax.set_xlabel('Издательство', fontsize=12, fontweight='bold')
        ax.set_ylabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Распределение публикаций по издательствам', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['publishers_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('most_cited'):
        fig, ax = plt.subplots(figsize=(10, 8))
        top_pubs = profile['most_cited'][:8]
        titles = [f"{p['title'][:35]}..." for p in top_pubs]
        citations = [p['citations'] for p in top_pubs]
        
        sorted_pairs = sorted(zip(citations, titles), reverse=True)
        citations, titles = zip(*sorted_pairs)
        
        bars = ax.barh(range(len(titles)), citations, color='#F18F01', alpha=0.8,
                       edgecolor='black', linewidth=1.2)
        
        for i, (bar, cit) in enumerate(zip(bars, citations)):
            ax.text(cit + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{cit}', va='center', fontsize=10)
        
        ax.set_yticks(range(len(titles)))
        ax.set_yticklabels(titles, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel('Число цитирований', fontsize=12, fontweight='bold')
        ax.set_title('Самые цитируемые статьи', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['citations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('top_affiliations'):
        fig, ax = plt.subplots(figsize=(10, 6))
        affils = list(profile['top_affiliations'].keys())
        counts = list(profile['top_affiliations'].values())
        
        y_pos = np.arange(len(affils))
        bars = ax.barh(y_pos, counts, color='#3498DB', alpha=0.8,
                       edgecolor='black', linewidth=1.2)
        
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{count}', va='center', fontsize=10)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(affils, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Топ аффилиаций', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['affiliations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('Тематическая структура исследований', fontsize=14, fontweight='bold')
    
    if profile.get('top_domains'):
        ax = axes[0, 0]
        domains = list(profile['top_domains'].keys())[:5]
        counts = [profile['top_domains'][d] for d in domains]
        
        ax.bar(range(len(domains)), counts, color='#E74C3C', alpha=0.8)
        ax.set_xticks(range(len(domains)))
        ax.set_xticklabels(domains, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Число', fontsize=11)
        ax.set_title('Domains', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    if profile.get('top_fields'):
        ax = axes[0, 1]
        fields = list(profile['top_fields'].keys())[:5]
        counts = [profile['top_fields'][f] for f in fields]
        
        ax.bar(range(len(fields)), counts, color='#3498DB', alpha=0.8)
        ax.set_xticks(range(len(fields)))
        ax.set_xticklabels(fields, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Число', fontsize=11)
        ax.set_title('Fields', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    if profile.get('top_topics'):
        ax = axes[1, 0]
        topics = list(profile['top_topics'].keys())[:5]
        counts = [profile['top_topics'][t] for t in topics]
        
        ax.barh(range(len(topics)), counts, color='#2ECC71', alpha=0.8)
        ax.set_yticks(range(len(topics)))
        ax.set_yticklabels(topics, fontsize=9)
        ax.set_xlabel('Число', fontsize=11)
        ax.set_title('Topics', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    if profile.get('top_subtopics'):
        ax = axes[1, 1]
        subtopics = list(profile['top_subtopics'].keys())[:5]
        counts = [profile['top_subtopics'][s] for s in subtopics]
        
        ax.barh(range(len(subtopics)), counts, color='#F39C12', alpha=0.8)
        ax.set_yticks(range(len(subtopics)))
        ax.set_yticklabels(subtopics, fontsize=9)
        ax.set_xlabel('Число', fontsize=11)
        ax.set_title('Subtopics', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    images['thematic_structure'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    if profile.get('citation_distribution'):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        dist = profile['citation_distribution']
        filtered_dist = {k: v for k, v in dist.items() if v > 0}
        
        ranges = list(filtered_dist.keys())
        counts = list(filtered_dist.values())
        
        bars = ax.bar(range(len(ranges)), counts, color='#8E44AD', alpha=0.8,
                      edgecolor='black', linewidth=1.2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xticks(range(len(ranges)))
        ax.set_xticklabels(ranges, rotation=45, ha='right', fontsize=10)
        ax.set_xlabel('Диапазон цитирований', fontsize=12, fontweight='bold')
        ax.set_ylabel('Число статей', fontsize=12, fontweight='bold')
        ax.set_title('Распределение статей по числу цитирований', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['citation_distribution'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('top_concepts'):
        top_concepts_items = list(profile['top_concepts'].items())[:6]
        if len(top_concepts_items) >= 3:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            concepts = [item[0][:20] for item in top_concepts_items]
            values = [item[1] for item in top_concepts_items]
            
            max_val = max(values) if values else 1
            normalized = [v / max_val for v in values]
            
            concepts_radar = concepts + [concepts[0]]
            values_radar = normalized + [normalized[0]]
            
            angles = np.linspace(0, 2 * np.pi, len(concepts), endpoint=False).tolist()
            angles_radar = angles + [angles[0]]
            
            ax.plot(angles_radar, values_radar, 'o-', linewidth=2, color='#2C3E50', markersize=8)
            ax.fill(angles_radar, values_radar, alpha=0.25, color='#3498DB')
            
            ax.set_xticks(angles)
            ax.set_xticklabels(concepts, fontsize=10, fontweight='bold')
            ax.set_ylim(0, 1.1)
            ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
            ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8)
            ax.set_title('Тематический профиль (Radar Chart)', fontsize=13, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            images['radar_chart'] = base64.b64encode(buf.getvalue()).decode()
            plt.close()
    
    return images

# ============================================
# ФУНКЦИИ ДЛЯ ГЕНЕРАЦИИ ОТЧЕТОВ
# ============================================

def generate_html_report(profile: Dict, publications: List[Dict], images: Dict[str, str], logo_base64: Optional[str] = None, institution_homepages: Optional[Dict[str, str]] = None, theme_colors: Optional[Dict] = None) -> str:
    """Генерирует HTML отчет с расширенной информацией и дизайном из второго кода"""
    
    if theme_colors is None:
        theme_colors = {
            'primary': '#667eea',
            'secondary': '#f39c12'
        }
    
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')
    analogous = get_analogous_colors(primary, 2)
    
    total_pubs = profile.get('total_publications', 0)
    h_index = profile.get('h_index', 0)
    g_index = profile.get('g_index', 0)
    i10_index = profile.get('i10_index', 0)
    total_citations = profile.get('total_citations', 0)
    avg_citations = profile.get('average_citations', 0)
    median_citations = profile.get('median_citations', 0)
    max_citations = profile.get('max_citations', 0)
    oa_percentage = profile.get('oa_percentage', 0)
    
    top_journals = profile.get('top_journals', {})
    top_concepts = profile.get('top_concepts', {})
    top_domains = profile.get('top_domains', {})
    top_fields = profile.get('top_fields', {})
    top_topics = profile.get('top_topics', {})
    top_subtopics = profile.get('top_subtopics', {})
    trend = profile.get('trend_direction', 'unknown')
    trend_corr = profile.get('trend_correlation', 0)
    
    risk_flags = profile.get('risk_flags', [])
    recommendation = profile.get('recommendation', 'No recommendation')
    
    unique_coauthors = profile.get('unique_coauthors', 0)
    avg_authors = profile.get('avg_authors_per_paper', 0)
    papers_per_year = profile.get('papers_per_year', 0)
    active_years = profile.get('active_years', 0)
    
    retractions = profile.get('retractions', 0)
    corrections = profile.get('corrections', 0)
    
    author_name = profile.get('author_name', 'Unknown')
    author_affiliations = profile.get('author_affiliations', [])
    author_countries = profile.get('author_countries', [])
    
    top_primary_topics = profile.get('top_primary_topics', {})
    top_subfields = profile.get('top_subfields', {})
    top_fields_new = profile.get('top_fields', {})
    top_domains_new = profile.get('top_domains', {})
    top_keywords = profile.get('top_keywords', {})
    
    collaborations = profile.get('collaborations', {})
    domestic_papers = collaborations.get('domestic_papers', 0)
    international_papers = collaborations.get('international_papers', 0)
    mixed_papers = collaborations.get('mixed_papers', 0)
    domestic_collab = collaborations.get('domestic', {})
    international_collab = collaborations.get('international', {})
    most_collab_country = profile.get('most_collaborative_country', 'None')
    collab_index = profile.get('collaboration_index', 0)
    country_diversity = profile.get('country_diversity', 0)
    
    top_coauthors = profile.get('top_coauthors', {})
    coauthors_with_orcid = profile.get('coauthors_with_orcid', {})
    
    css_vars = generate_css_variables(primary, secondary)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Профиль ученого - ORCID {profile.get('orcid', '')}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Times New Roman', 'DejaVu Serif', serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #333;
            }}
            .report-wrapper {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                border-radius: 10px;
                overflow: hidden;
            }}
            .sidebar {{
                position: fixed;
                left: 0;
                top: 0;
                width: 260px;
                height: 100vh;
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 30px 20px;
                overflow-y: auto;
                z-index: 1000;
            }}
            .sidebar h3 {{
                margin-bottom: 20px;
                font-size: 18px;
                font-weight: 600;
                color: white;
            }}
            .sidebar a {{
                color: white;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px 15px;
                margin: 5px 0;
                border-radius: 8px;
                transition: all 0.3s;
            }}
            .sidebar a:hover {{
                background: rgba(255,255,255,0.2);
                transform: translateX(5px);
            }}
            .sidebar-icon {{
                width: 22px;
                height: 22px;
                display: inline-block;
                vertical-align: middle;
            }}
            .main-content {{
                margin-left: 260px;
                padding: 30px 40px;
            }}
            .header {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 40px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                border-bottom: none;
                margin: 0;
                font-size: 32px;
            }}
            .header .date {{
                opacity: 0.9;
                margin-top: 10px;
            }}
            .header-logo {{
                max-height: 150px;
                max-width: 300px;
                margin-bottom: 15px;
            }}
            .author-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-left: 4px solid {primary};
            }}
            .author-name {{
                font-size: 22px;
                font-weight: bold;
                color: #2C3E50;
            }}
            .author-affil {{
                color: #555;
                font-size: 14px;
                margin-top: 5px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {primary};
                text-align: center;
                transition: transform 0.3s;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .metric-value {{
                font-size: 28px;
                font-weight: bold;
                color: #2C3E50;
                font-family: 'Times New Roman', serif;
            }}
            .metric-label {{
                font-size: 12px;
                color: #7F8C8D;
                margin-top: 5px;
                font-family: 'Times New Roman', serif;
            }}
            .flag {{
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                background-color: #FEF9E7;
                border-left: 4px solid #F39C12;
                font-family: 'Times New Roman', serif;
            }}
            .flag-danger {{
                background-color: #FDEDEC;
                border-left-color: #E74C3C;
            }}
            .chart-container {{
                margin: 20px 0;
                text-align: center;
            }}
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .recommendation-box {{
                padding: 15px;
                margin: 20px 0;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                font-family: 'Times New Roman', serif;
            }}
            .rec-green {{ background-color: #D5F5E3; border-left: 4px solid #2ECC71; }}
            .rec-yellow {{ background-color: #FEF9E7; border-left: 4px solid #F39C12; }}
            .rec-red {{ background-color: #FDEDEC; border-left: 4px solid #E74C3C; }}
            .collab-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 15px 0;
            }}
            .collab-box {{
                background: #f8f9fa;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #ddd;
            }}
            .collab-box h4 {{
                margin: 0 0 8px 0;
                color: #2C3E50;
            }}
            .collab-box ul {{
                margin: 5px 0;
                padding-left: 20px;
            }}
            .collab-box li {{
                margin-bottom: 3px;
            }}
            .collab-affil {{
                font-size: 13px;
                color: #555;
            }}
            .collab-site {{
                font-size: 11px;
                color: #2980B9;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: 'Times New Roman', serif;
            }}
            th {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #BDC3C7;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .doi-link {{
                color: #2980B9;
                text-decoration: none;
                font-size: 12px;
                word-break: break-all;
            }}
            .doi-link:hover {{
                text-decoration: underline;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #BDC3C7;
                text-align: center;
                color: #7F8C8D;
                font-size: 12px;
            }}
            .footer a {{
                color: #2980B9;
                text-decoration: none;
            }}
            .footer a:hover {{
                text-decoration: underline;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 15px 0;
            }}
            .stat-item {{
                padding: 8px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .thematic-list {{
                columns: 2;
                column-gap: 30px;
            }}
            .thematic-list li {{
                break-inside: avoid;
                margin-bottom: 5px;
            }}
            .collab-country {{
                font-weight: bold;
                color: #2C3E50;
                margin-top: 8px;
                font-size: 14px;
            }}
            .collab-affil-item {{
                margin-left: 15px;
                font-size: 13px;
            }}
            .section {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .section-title {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid {primary};
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .section-icon {{
                width: 28px;
                height: 28px;
                vertical-align: middle;
                display: inline-block;
            }}
            .rank-item {{
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 10px;
                transition: all 0.3s;
                background: #f8f9fa;
                border-left: 3px solid {primary};
            }}
            .rank-item:hover {{
                transform: translateX(5px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .rank-number {{
                font-weight: bold;
                color: {primary};
                font-size: 18px;
                display: inline-block;
                width: 40px;
            }}
            .rank-name {{
                display: inline-block;
                font-weight: 500;
            }}
            .rank-count {{
                float: right;
                color: #666;
            }}
            .badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin: 2px;
            }}
            .badge-success {{ background: #d4edda; color: #155724; }}
            .badge-warning {{ background: #fff3cd; color: #856404; }}
            .badge-danger {{ background: #f8d7da; color: #721c24; }}
            .badge-info {{ background: #d1ecf1; color: #0c5460; }}
            .badge-repository {{ background: #e2d5f8; color: #5e2a9e; }}
            .badge-book {{ background: #bbecde; color: #0e6b5e; }}
            .badge-proceedings {{ background: #fff2c9; color: #b26b00; }}
            .concepts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            .concept-card {{
                background: linear-gradient(135deg, {primary}15 0%, {secondary}15 100%);
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                border: 1px solid {primary}30;
            }}
            .concept-name {{
                font-weight: 600;
                color: {primary};
            }}
            .concept-score {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }}
            
            @media print {{
                .sidebar {{ display: none; }}
                .main-content {{ margin-left: 0; }}
            }}
            @media (max-width: 768px) {{
                .sidebar {{ display: none; }}
                .main-content {{ margin-left: 0; padding: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h3>📑 Навигация</h3>
            <a href="#overview"><span>📊 Обзор</span></a>
            <a href="#metrics"><span>📈 Метрики</span></a>
            <a href="#visualizations"><span>📊 Визуализации</span></a>
            <a href="#thematic"><span>🏷️ Тематика</span></a>
            <a href="#collaborations"><span>🌍 Коллаборации</span></a>
            <a href="#coauthors"><span>🤝 Соавторы</span></a>
            <a href="#publications"><span>📚 Публикации</span></a>
        </div>
        
        <div class="main-content">
            <div class="header">
                {f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Логотип">' if logo_base64 else ''}
                <h1>📊 Профиль ученого</h1>
                <div class="date">Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
            </div>
            
            <div id="overview" class="section">
                <div class="section-title">📋 Обзор</div>
                <div class="author-info">
                    <div class="author-name">{author_name}</div>
                    <div class="author-affil"><strong>ORCID:</strong> {profile.get('orcid', 'N/A')}</div>
                    {f'<div class="author-affil"><strong>Аффилиации:</strong> {", ".join(author_affiliations[:5])}</div>' if author_affiliations else ''}
                    {f'<div class="author-affil"><strong>Страны:</strong> {", ".join(author_countries)}</div>' if author_countries else ''}
                    <div class="author-affil"><strong>Всего проанализировано публикаций:</strong> {total_pubs}</div>
                </div>
                
                <div class="recommendation-box rec-green">
                    <strong>Рекомендация редактора:</strong> {recommendation}
                </div>
                
                {'<div class="flag flag-danger">' + '</div><div class="flag flag-danger">'.join(risk_flags) + '</div>' if risk_flags else ''}
            </div>
            
            <div id="metrics" class="section">
                <div class="section-title">📈 Ключевые метрики</div>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{total_pubs}</div>
                        <div class="metric-label">Всего публикаций</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{h_index}</div>
                        <div class="metric-label">h-index</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{g_index}</div>
                        <div class="metric-label">g-index</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{i10_index}</div>
                        <div class="metric-label">i10-index</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_citations:,}</div>
                        <div class="metric-label">Всего цитирований</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{avg_citations:.1f}</div>
                        <div class="metric-label">Среднее цитирований</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{median_citations:.0f}</div>
                        <div class="metric-label">Медиана цитирований</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{oa_percentage:.1f}%</div>
                        <div class="metric-label">Открытый доступ</div>
                    </div>
                </div>
            </div>
            
            <div id="visualizations" class="section">
                <div class="section-title">📊 Визуализации</div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('years_chart', '')}" alt="Публикации по годам">
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="Топ журналов">
                    </div>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="Открытый доступ">
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('publishers_chart', '')}" alt="Издательства">
                    </div>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('affiliations_chart', '')}" alt="Аффилиации">
                    </div>
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="Word Cloud">
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('citations_chart', '')}" alt="Самые цитируемые">
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('citation_distribution', '')}" alt="Распределение цитирований">
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('thematic_structure', '')}" alt="Тематическая структура">
                </div>
                
                {'<div class="chart-container"><img src="data:image/png;base64,' + images.get('radar_chart', '') + '" alt="Radar Chart"></div>' if images.get('radar_chart') else ''}
            </div>
            
            <div id="thematic" class="section">
                <div class="section-title">🏷️ Детальная тематическая структура</div>
                
                <h3>Topics (Топ 10)</h3>
                <ul class="thematic-list">
                    {''.join([f'<li><strong>{topic}</strong>: {count} статей</li>' for topic, count in list(top_primary_topics.items())[:10]])}
                </ul>
                
                <h3>Subfields (Топ 10)</h3>
                <ul class="thematic-list">
                    {''.join([f'<li><strong>{subfield}</strong>: {count} статей</li>' for subfield, count in list(top_subfields.items())[:10]])}
                </ul>
                
                <h3>Fields (Топ 10)</h3>
                <ul class="thematic-list">
                    {''.join([f'<li><strong>{field}</strong>: {count} статей</li>' for field, count in list(top_fields_new.items())[:10]])}
                </ul>
                
                <h3>Domains (Топ 5)</h3>
                <ul>
                    {''.join([f'<li><strong>{domain}</strong>: {count} статей</li>' for domain, count in list(top_domains_new.items())[:5]])}
                </ul>
                
                <h3>Key Concepts (Топ 20)</h3>
                <ul class="thematic-list">
                    {''.join([f'<li>{concept} ({count})</li>' for concept, count in list(top_keywords.items())[:20]])}
                </ul>
            </div>
            
            <div id="collaborations" class="section">
                <div class="section-title">🌍 Анализ коллабораций</div>
                
                <div class="collab-grid">
                    <div class="collab-box">
                        <h4>🇷🇺 Внутристрановые коллаборации</h4>
                        <p><strong>Статей:</strong> {domestic_papers}</p>
                        {''.join([
                            f'<div class="collab-country">📍 {country}</div>' +
                            (''.join([
                                f'<div class="collab-affil-item">• <strong>{affil}</strong>: {count} статей</div>'
                                for affil, count in list(affils.items())[:10]
                            ]) if isinstance(affils, dict) else f'<div class="collab-affil-item">• {affils} статей</div>')
                            for country, affils in list(domestic_collab.items())
                        ]) if domestic_collab else '<p>Нет данных</p>'}
                    </div>
                    <div class="collab-box">
                        <h4>🌐 Международные коллаборации</h4>
                        <p><strong>Статей:</strong> {international_papers}</p>
                        {''.join([
                            f'<div class="collab-country">📍 {country}</div>' +
                            (''.join([
                                f'<div class="collab-affil-item">• <strong>{affil}</strong>: {count} статей</div>'
                                for affil, count in list(affils.items())[:10]
                            ]) if isinstance(affils, dict) else f'<div class="collab-affil-item">• {affils} статей</div>')
                            for country, affils in list(international_collab.items())
                        ]) if international_collab else '<p>Нет данных</p>'}
                    </div>
                </div>
                
                <div class="collab-box" style="margin-top: 10px;">
                    <p><strong>Смешанных статей:</strong> {mixed_papers}</p>
                    <p><strong>Индекс коллабораций:</strong> {collab_index:.2f} (среднее число соавторов на статью - 1)</p>
                    <p><strong>Страновое разнообразие:</strong> {country_diversity} стран</p>
                    <p><strong>Самая коллаборативная страна:</strong> {most_collab_country}</p>
                </div>
            </div>
            
            <div id="coauthors" class="section">
                <div class="section-title">🤝 Топ соавторы</div>
                <ul>
                    {''.join([
                        f'<li>'
                        f'<strong>{author}</strong>'
                        f' ({count} совместных работ)'
                        f'{" — <a href=\"https://orcid.org/' + coauthors_with_orcid.get(author, '') + '\" target=\"_blank\">ORCID</a>" if coauthors_with_orcid.get(author) else ""}'
                        f'</li>'
                        for author, count in list(top_coauthors.items())[:20]
                    ])}
                </ul>
            </div>
            
            <div class="section">
                <div class="section-title">📋 Расширенная статистика</div>
                <div class="stats-grid">
                    <div class="stat-item"><strong>Период активности:</strong> {profile.get('first_publication', 'N/A')} - {profile.get('last_publication', 'N/A')}</div>
                    <div class="stat-item"><strong>Активных лет:</strong> {active_years}</div>
                    <div class="stat-item"><strong>Статей в год:</strong> {papers_per_year:.1f}</div>
                    <div class="stat-item"><strong>Тренд:</strong> {trend} (R² = {trend_corr**2:.3f})</div>
                    <div class="stat-item"><strong>Ретракций:</strong> {retractions}</div>
                    <div class="stat-item"><strong>Коррекций:</strong> {corrections}</div>
                    <div class="stat-item"><strong>Уникальных соавторов:</strong> {unique_coauthors}</div>
                    <div class="stat-item"><strong>Среднее авторов на статью:</strong> {avg_authors:.1f}</div>
                    <div class="stat-item"><strong>Максимум цитирований на статью:</strong> {max_citations}</div>
                    <div class="stat-item"><strong>Тематическое разнообразие (Shannon):</strong> {profile.get('thematic_diversity_shannon', 0):.3f}</div>
                    <div class="stat-item"><strong>Доля внутристрановых коллабораций:</strong> {profile.get('domestic_papers_ratio', 0)*100:.1f}%</div>
                    <div class="stat-item"><strong>Доля международных коллабораций:</strong> {profile.get('international_papers_ratio', 0)*100:.1f}%</div>
                </div>
            </div>
            
            <div id="publications" class="section">
                <div class="section-title">📚 Список публикаций</div>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Название</th>
                                <th>Год</th>
                                <th>Журнал</th>
                                <th>Цитаты</th>
                                <th>OA</th>
                                <th>DOI</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([
                                f"""
                                <tr>
                                    <td>{i+1}</td>
                                    <td>{pub.get('title', 'No title')[:100]}</td>
                                    <td>{pub.get('publication_year', 'N/A')}</td>
                                    <td>{pub.get('journal_name', 'Unknown')}</td>
                                    <td>{pub.get('cited_by_count', 0)}</td>
                                    <td>{'✅' if pub.get('is_oa', False) else '❌'}</td>
                                    <td><a href="https://doi.org/{pub.get('doi', '')}" target="_blank" class="doi-link">{pub.get('doi', '')}</a></td>
                                </tr>
                                """
                                for i, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True))
                            ])}
                        </tbody>
                    </table>
                    <p><em>Всего публикаций: {len(publications)}</em></p>
                </div>
            </div>
            
            <div class="footer">
                <p>© Author Profile Analysis / Created by daM / Chimica Techno Acta</p>
                <p><a href="https://chimicatechnoacta.ru" target="_blank">https://chimicatechnoacta.ru</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_html_report_with_multiple_authors(all_authors: List[Dict], show_all: bool, journal_logo_base64: Optional[str] = None, theme_colors: Optional[Dict] = None) -> str:
    """Генерирует HTML отчет с множественными авторами"""
    
    if theme_colors is None:
        theme_colors = {
            'primary': '#667eea',
            'secondary': '#f39c12'
        }
    
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')
    
    if not all_authors:
        return "<html><body><h1>Нет данных для отображения</h1></body></html>"
    
    best_author = all_authors[0]
    
    if show_all:
        authors_to_show = all_authors
    else:
        authors_to_show = [best_author]
    
    html_parts = []
    
    html_parts.append(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Профили ученых - Анализ {len(all_authors)} авторов</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Times New Roman', 'DejaVu Serif', serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #333;
            }}
            .report-wrapper {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                border-radius: 10px;
                overflow: hidden;
            }}
            .sidebar {{
                position: fixed;
                left: 0;
                top: 0;
                width: 260px;
                height: 100vh;
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 30px 20px;
                overflow-y: auto;
                z-index: 1000;
            }}
            .sidebar h3 {{
                margin-bottom: 20px;
                font-size: 18px;
                font-weight: 600;
                color: white;
            }}
            .sidebar a {{
                color: white;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px 15px;
                margin: 5px 0;
                border-radius: 8px;
                transition: all 0.3s;
            }}
            .sidebar a:hover {{
                background: rgba(255,255,255,0.2);
                transform: translateX(5px);
            }}
            .main-content {{
                margin-left: 260px;
                padding: 30px 40px;
            }}
            .header {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 40px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                border-bottom: none;
                margin: 0;
                font-size: 32px;
            }}
            .header .date {{
                opacity: 0.9;
                margin-top: 10px;
            }}
            .header-logo {{
                max-height: 150px;
                max-width: 300px;
                margin-bottom: 15px;
            }}
            .author-card {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-left: 5px solid {primary};
                transition: transform 0.2s;
            }}
            .author-card:hover {{
                transform: translateX(5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }}
            .author-card.best {{
                border-left-color: #FFD700;
                background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
            }}
            .author-rank {{
                font-size: 20px;
                font-weight: bold;
                color: {primary};
                display: inline-block;
                margin-right: 10px;
            }}
            .author-name-main {{
                font-size: 22px;
                font-weight: 600;
                color: {primary};
                display: inline-block;
            }}
            .author-hindex {{
                font-size: 18px;
                color: #666;
                margin-left: 10px;
            }}
            .best-badge {{
                background: #FFD700;
                color: #333;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
                display: inline-block;
                margin-left: 15px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {primary};
                text-align: center;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2C3E50;
            }}
            .metric-label {{
                font-size: 12px;
                color: #7F8C8D;
                margin-top: 5px;
            }}
            .chart-container {{
                margin: 20px 0;
                text-align: center;
            }}
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .author-section {{
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #e0e0e0;
            }}
            .author-section:last-child {{
                border-bottom: none;
            }}
            .flag {{
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                background-color: #FEF9E7;
                border-left: 4px solid #F39C12;
            }}
            .flag-danger {{
                background-color: #FDEDEC;
                border-left-color: #E74C3C;
            }}
            .recommendation-box {{
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
            }}
            .rec-green {{ background-color: #D5F5E3; border-left: 4px solid #2ECC71; }}
            .rec-yellow {{ background-color: #FEF9E7; border-left: 4px solid #F39C12; }}
            .rec-red {{ background-color: #FDEDEC; border-left: 4px solid #E74C3C; }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #BDC3C7;
                text-align: center;
                color: #7F8C8D;
                font-size: 12px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #BDC3C7;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .doi-link {{
                color: #2980B9;
                text-decoration: none;
                font-size: 12px;
            }}
            .doi-link:hover {{
                text-decoration: underline;
            }}
            @media print {{
                .sidebar {{ display: none; }}
                .main-content {{ margin-left: 0; }}
            }}
            @media (max-width: 768px) {{
                .sidebar {{ display: none; }}
                .main-content {{ margin-left: 0; padding: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h3>📑 Навигация</h3>
            <a href="#overview"><span>📊 Обзор</span></a>
    """)
    
    for i, author in enumerate(authors_to_show):
        author_name = author.get('author_name', f'Автор {i+1}')
        h_index = author.get('h_index', 0)
        anchor = f"author_{i}"
        html_parts.append(f'<a href="#{anchor}"><span>👤 {author_name} (h-index: {h_index})</span></a>')
    
    html_parts.append("""
        </div>
        <div class="main-content">
            <div class="header">
    """)
    
    if journal_logo_base64:
        html_parts.append(f'<img src="data:image/png;base64,{journal_logo_base64}" class="header-logo" alt="Логотип журнала">')
    
    html_parts.append(f"""
                <h1>📊 Анализ профилей ученых</h1>
                <div class="date">Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
                <div style="margin-top: 15px;">
                    <span class="badge badge-info">Всего авторов: {len(all_authors)}</span>
                    <span class="badge badge-success">Лучший: {best_author.get('author_name', 'Unknown')} (h-index: {best_author.get('h_index', 0)})</span>
    """)
    
    if show_all:
        html_parts.append('<span class="badge badge-info">Показаны все авторы</span>')
    else:
        html_parts.append('<span class="badge badge-info">Показан только лучший автор</span>')
    
    html_parts.append("""
                </div>
            </div>
    """)
    
    if show_all:
        for i, author_data in enumerate(authors_to_show):
            is_best = (i == 0)
            author_name = author_data.get('author_name', f'Автор {i+1}')
            profile = author_data.get('profile', {})
            publications = author_data.get('publications', [])
            images = create_visualizations(profile) if profile else {}
            
            h_index = profile.get('h_index', 0)
            total_pubs = profile.get('total_publications', 0)
            total_citations = profile.get('total_citations', 0)
            avg_citations = profile.get('average_citations', 0)
            oa_percentage = profile.get('oa_percentage', 0)
            recommendation = profile.get('recommendation', 'Нет рекомендации')
            risk_flags = profile.get('risk_flags', [])
            
            top_journals = profile.get('top_journals', {})
            top_coauthors = profile.get('top_coauthors', {})
            coauthors_with_orcid = profile.get('coauthors_with_orcid', {})
            
            html_parts.append(f"""
            <div id="author_{i}" class="author-section">
                <div class="author-card {'best' if is_best else ''}">
                    <div>
                        <span class="author-rank">{i+1}.</span>
                        <span class="author-name-main">{author_name}</span>
                        <span class="author-hindex">(h-index: {h_index})</span>
                        {'<span class="best-badge">🏆 Лучший</span>' if is_best else ''}
                    </div>
                    
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{total_pubs}</div>
                            <div class="metric-label">Публикаций</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{h_index}</div>
                            <div class="metric-label">h-index</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{total_citations:,}</div>
                            <div class="metric-label">Цитирований</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{avg_citations:.1f}</div>
                            <div class="metric-label">Среднее цитирований</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{oa_percentage:.1f}%</div>
                            <div class="metric-label">Открытый доступ</div>
                        </div>
                    </div>
                    
                    <div class="recommendation-box rec-green">
                        <strong>Рекомендация:</strong> {recommendation}
                    </div>
                    
                    {'<div class="flag flag-danger">' + '</div><div class="flag flag-danger">'.join(risk_flags) + '</div>' if risk_flags else ''}
                    
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('years_chart', '')}" alt="Публикации по годам">
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="chart-container">
                            <img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="Топ журналов">
                        </div>
                        <div class="chart-container">
                            <img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="Открытый доступ">
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="Word Cloud">
                    </div>
                    
                    <h3>🤝 Топ соавторы</h3>
                    <ul>
                        {''.join([
                            f'<li><strong>{author}</strong> ({count} совместных работ)'
                            f'{" — <a href=\"https://orcid.org/' + coauthors_with_orcid.get(author, '') + '\" target=\"_blank\">ORCID</a>" if coauthors_with_orcid.get(author) else ""}'
                            f'</li>'
                            for author, count in list(top_coauthors.items())[:10]
                        ])}
                    </ul>
                    
                    <h3>📚 Публикации ({len(publications)})</h3>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Название</th>
                                    <th>Год</th>
                                    <th>Журнал</th>
                                    <th>Цитаты</th>
                                    <th>DOI</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([
                                    f"""
                                    <tr>
                                        <td>{j+1}</td>
                                        <td>{pub.get('title', 'No title')[:80]}</td>
                                        <td>{pub.get('publication_year', 'N/A')}</td>
                                        <td>{pub.get('journal_name', 'Unknown')}</td>
                                        <td>{pub.get('cited_by_count', 0)}</td>
                                        <td><a href="https://doi.org/{pub.get('doi', '')}" target="_blank" class="doi-link">{pub.get('doi', '')}</a></td>
                                    </tr>
                                    """
                                    for j, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)[:20])
                                ])}
                            </tbody>
                        </table>
                        {f'<p><em>Показано 20 из {len(publications)} публикаций</em></p>' if len(publications) > 20 else ''}
                    </div>
                </div>
            </div>
            """)
    
    else:
        author_data = authors_to_show[0]
        author_name = author_data.get('author_name', 'Unknown')
        profile = author_data.get('profile', {})
        publications = author_data.get('publications', [])
        institution_homepages = author_data.get('analyzer', {}).institution_homepages if author_data.get('analyzer') else {}
        images = create_visualizations(profile) if profile else {}
        
        html_parts.append(generate_html_report(profile, publications, images, journal_logo_base64, institution_homepages, theme_colors))
    
    html_parts.append("""
            <div class="footer">
                <p>© Author Profile Analysis / Created by daM / Chimica Techno Acta</p>
                <p><a href="https://chimicatechnoacta.ru" target="_blank">https://chimicatechnoacta.ru</a></p>
            </div>
        </div>
    </body>
    </html>
    """)
    
    return '\n'.join(html_parts)

def generate_pdf_report(profile: Dict, publications: List[Dict], images: Dict[str, str], filename: str = "profile_report.pdf", logo_path: Optional[str] = None, institution_homepages: Optional[Dict[str, str]] = None, theme_colors: Optional[Dict] = None):
    """Генерирует PDF отчет с расширенной информацией и дизайном из второго кода"""
    
    if not PDF_AVAILABLE:
        print("❌ ReportLab не установлен. PDF отчет не может быть сгенерирован.")
        return
    
    if theme_colors is None:
        theme_colors = {
            'primary': '#667eea',
            'secondary': '#f39c12'
        }
    
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')
    
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    primary_color = colors.HexColor(primary.lstrip('#'))
    secondary_color = colors.HexColor(secondary.lstrip('#'))
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName='Times-Roman'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=primary_color,
        spaceAfter=12,
        fontName='Times-Bold'
    )
    
    story.append(Paragraph("Профиль ученого", title_style))
    
    author_name = profile.get('author_name', 'Unknown')
    story.append(Paragraph(f"<b>{author_name}</b>", styles['Heading2']))
    story.append(Paragraph(f"ORCID: {profile.get('orcid', 'N/A')}", styles['Normal']))
    
    author_affiliations = profile.get('author_affiliations', [])
    if author_affiliations:
        story.append(Paragraph(f"Аффилиации: {', '.join(author_affiliations[:3])}", styles['Normal']))
    
    author_countries = profile.get('author_countries', [])
    if author_countries:
        story.append(Paragraph(f"Страны: {', '.join(author_countries)}", styles['Normal']))
    
    story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    metrics_data = [
        ['Метрика', 'Значение', 'Метрика', 'Значение'],
        ['Всего публикаций', str(profile.get('total_publications', 0)), 
         'h-index', str(profile.get('h_index', 0))],
        ['g-index', str(profile.get('g_index', 0)), 
         'i10-index', str(profile.get('i10_index', 0))],
        ['Всего цитирований', f"{profile.get('total_citations', 0):,}", 
         'Среднее цитирований', f"{profile.get('average_citations', 0):.1f}"],
        ['Медиана цитирований', f"{profile.get('median_citations', 0):.0f}", 
         'Открытый доступ', f"{profile.get('oa_percentage', 0):.1f}%"],
        ['Ретракций', str(profile.get('retractions', 0)), 
         'Коррекций', str(profile.get('corrections', 0))],
        ['Активных лет', str(profile.get('active_years', 0)), 
         'Статей в год', f"{profile.get('papers_per_year', 0):.1f}"],
        ['Уникальных соавторов', str(profile.get('unique_coauthors', 0)), 
         'Тренд', profile.get('trend_direction', 'unknown')]
    ]
    
    table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    rec = profile.get('recommendation', 'No recommendation')
    rec_style = ParagraphStyle(
        'Recommendation',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.HexColor('#2C3E50'),
        backColor=colors.HexColor('#D5F5E3'),
        borderPadding=10,
        borderRadius=5,
        fontName='Times-Roman'
    )
    story.append(Paragraph(f"<b>Рекомендация:</b> {rec}", rec_style))
    story.append(Spacer(1, 20))
    
    image_names = {
        'years_chart': 'Динамика публикационной активности',
        'journals_chart': 'Топ журналов',
        'oa_chart': 'Статус открытого доступа',
        'publishers_chart': 'Распределение по издательствам',
        'affiliations_chart': 'Топ аффилиаций',
        'wordcloud': 'Ключевые концепты',
        'citations_chart': 'Самые цитируемые статьи',
        'citation_distribution': 'Распределение цитирований',
        'thematic_structure': 'Тематическая структура'
    }
    
    for img_key, img_title in image_names.items():
        if img_key in images and images[img_key]:
            story.append(PageBreak())
            story.append(Paragraph(f"<b>{img_title}</b>", heading_style))
            try:
                img_data = base64.b64decode(images[img_key])
                img = Image(BytesIO(img_data), width=6*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 20))
            except Exception as e:
                print(f"⚠️ Не удалось добавить изображение {img_key}: {e}")
    
    if 'radar_chart' in images and images['radar_chart']:
        story.append(PageBreak())
        story.append(Paragraph("<b>Тематический профиль (Radar Chart)</b>", heading_style))
        try:
            img_data = base64.b64decode(images['radar_chart'])
            img = Image(BytesIO(img_data), width=6*inch, height=6*inch)
            story.append(img)
            story.append(Spacer(1, 20))
        except Exception as e:
            print(f"⚠️ Не удалось добавить radar chart: {e}")
    
    story.append(PageBreak())
    story.append(Paragraph("<b>Детальная тематическая структура</b>", heading_style))
    
    top_primary_topics = profile.get('top_primary_topics', {})
    if top_primary_topics:
        story.append(Paragraph("Topics (Топ 10):", styles['Heading3']))
        for topic, count in list(top_primary_topics.items())[:10]:
            story.append(Paragraph(f"• {topic}: {count} статей", styles['Normal']))
        story.append(Spacer(1, 10))
    
    top_subfields = profile.get('top_subfields', {})
    if top_subfields:
        story.append(Paragraph("Subfields (Топ 10):", styles['Heading3']))
        for subfield, count in list(top_subfields.items())[:10]:
            story.append(Paragraph(f"• {subfield}: {count} статей", styles['Normal']))
        story.append(Spacer(1, 10))
    
    top_fields = profile.get('top_fields', {})
    if top_fields:
        story.append(Paragraph("Fields (Топ 10):", styles['Heading3']))
        for field, count in list(top_fields.items())[:10]:
            story.append(Paragraph(f"• {field}: {count} статей", styles['Normal']))
        story.append(Spacer(1, 10))
    
    top_domains = profile.get('top_domains', {})
    if top_domains:
        story.append(Paragraph("Domains (Топ 5):", styles['Heading3']))
        for domain, count in list(top_domains.items())[:5]:
            story.append(Paragraph(f"• {domain}: {count} статей", styles['Normal']))
        story.append(Spacer(1, 10))
    
    top_keywords = profile.get('top_keywords', {})
    if top_keywords:
        story.append(Paragraph("Key Concepts (Топ 20):", styles['Heading3']))
        for concept, count in list(top_keywords.items())[:20]:
            story.append(Paragraph(f"• {concept} ({count})", styles['Normal']))
        story.append(Spacer(1, 20))
    
    collaborations = profile.get('collaborations', {})
    domestic_papers = collaborations.get('domestic_papers', 0)
    international_papers = collaborations.get('international_papers', 0)
    mixed_papers = collaborations.get('mixed_papers', 0)
    domestic_collab = collaborations.get('domestic', {})
    international_collab = collaborations.get('international', {})
    
    if domestic_papers > 0 or international_papers > 0 or mixed_papers > 0:
        story.append(PageBreak())
        story.append(Paragraph("<b>Анализ коллабораций</b>", heading_style))
        story.append(Paragraph(f"Внутристрановые коллаборации: {domestic_papers} статей", styles['Normal']))
        for country, affils in list(domestic_collab.items()):
            story.append(Paragraph(f"  📍 {country}:", styles['Normal']))
            if isinstance(affils, dict):
                for affil, count in list(affils.items())[:5]:
                    story.append(Paragraph(f"    • {affil}: {count} статей", styles['Normal']))
            else:
                story.append(Paragraph(f"    • {affils} статей", styles['Normal']))
        story.append(Spacer(1, 5))
        
        story.append(Paragraph(f"Международные коллаборации: {international_papers} статей", styles['Normal']))
        for country, affils in list(international_collab.items()):
            story.append(Paragraph(f"  📍 {country}:", styles['Normal']))
            if isinstance(affils, dict):
                for affil, count in list(affils.items())[:5]:
                    story.append(Paragraph(f"    • {affil}: {count} статей", styles['Normal']))
            else:
                story.append(Paragraph(f"    • {affils} статей", styles['Normal']))
        story.append(Spacer(1, 5))
        
        story.append(Paragraph(f"Смешанных статей: {mixed_papers}", styles['Normal']))
        story.append(Paragraph(f"Индекс коллабораций: {profile.get('collaboration_index', 0):.2f}", styles['Normal']))
        story.append(Paragraph(f"Страновое разнообразие: {profile.get('country_diversity', 0)} стран", styles['Normal']))
        story.append(Spacer(1, 20))
    
    top_coauthors = profile.get('top_coauthors', {})
    coauthors_with_orcid = profile.get('coauthors_with_orcid', {})
    
    if top_coauthors:
        story.append(Paragraph("<b>Топ соавторы</b>", heading_style))
        for author, count in list(top_coauthors.items())[:20]:
            orcid_link = coauthors_with_orcid.get(author, '')
            if orcid_link:
                story.append(Paragraph(f"• {author}: {count} совместных работ (ORCID: {orcid_link})", styles['Normal']))
            else:
                story.append(Paragraph(f"• {author}: {count} совместных работ", styles['Normal']))
        story.append(Spacer(1, 20))
    
    story.append(PageBreak())
    story.append(Paragraph("<b>Список публикаций</b>", heading_style))
    
    sorted_pubs = sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)
    
    pub_table_data = [['#', 'Название', 'Год', 'Журнал', 'Цитаты', 'DOI']]
    for i, pub in enumerate(sorted_pubs[:50]):
        pub_table_data.append([
            str(i+1),
            pub.get('title', 'No title')[:50],
            str(pub.get('publication_year', 'N/A')),
            pub.get('journal_name', 'Unknown')[:30],
            str(pub.get('cited_by_count', 0)),
            pub.get('doi', '')
        ])
    
    if pub_table_data:
        pub_table = Table(pub_table_data, colWidths=[0.3*inch, 2*inch, 0.5*inch, 1.2*inch, 0.5*inch, 1.2*inch])
        pub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(pub_table)
        story.append(Spacer(1, 10))
        if len(publications) > 50:
            story.append(Paragraph(f"<i>Показано 50 из {len(publications)} публикаций</i>", styles['Normal']))
    
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7F8C8D'),
        alignment=TA_CENTER,
        fontName='Times-Roman'
    )
    story.append(Paragraph("© Author Profile Analysis / Created by daM / Chimica Techno Acta", footer_style))
    story.append(Paragraph("https://chimicatechnoacta.ru", footer_style))
    
    try:
        doc.build(story)
        print(f"✅ PDF отчет сохранен: {filename}")
    except Exception as e:
        print(f"❌ Ошибка при создании PDF: {e}")

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ДЛЯ STREAMLIT
# ============================================

def run_profile_analysis(orcid_list: List[str], show_all_authors: bool, journal_logo: Optional[Dict] = None):
    """Запускает полный анализ профиля ученого для одного или нескольких ORCID"""
    
    if not orcid_list:
        st.error("⚠️ Введите хотя бы один ORCID")
        return
    
    st.info(f"🔍 Анализирую {len(orcid_list)} авторов...")
    
    progress_container = st.empty()
    status_container = st.empty()
    
    try:
        journal_logo_base64 = None
        if journal_logo:
            try:
                for filename, file_info in journal_logo.items():
                    content = file_info['content'] if hasattr(file_info, 'get') else file_info
                    if hasattr(content, 'read'):
                        content = content.read()
                    journal_logo_base64 = base64.b64encode(content).decode()
                    st.success(f"✅ Логотип загружен: {filename}")
                    break
            except Exception as e:
                st.warning(f"⚠️ Ошибка загрузки логотипа: {e}")
        
        def progress_callback(current, total, orcid):
            progress_percent = (current / total) * 100
            progress_html = update_colored_progress(
                progress_percent, 
                f"Анализ {orcid} ({current}/{total})"
            )
            progress_container.markdown(progress_html, unsafe_allow_html=True)
            status_container.info(f"📊 Обработка {current}/{total}: {orcid}")
        
        start_time = time.time()
        
        all_authors_data = asyncio.run(
            analyze_multiple_authors(orcid_list, progress_callback)
        )
        
        elapsed = time.time() - start_time
        
        if not all_authors_data:
            st.error("❌ Данные не найдены. Проверьте правильность ORCID.")
            return
        
        sorted_authors = sort_authors_by_h_index(all_authors_data)
        
        st.session_state['all_authors'] = sorted_authors
        st.session_state['show_all_authors'] = show_all_authors
        st.session_state['journal_logo_base64'] = journal_logo_base64
        st.session_state['analysis_complete'] = True
        
        st.success(f"✅ Анализ завершен! Найдено {len(sorted_authors)} авторов за {elapsed:.1f} сек.")
        
        best_author = sorted_authors[0]
        st.info(f"🏆 Лучший автор: {best_author.get('author_name', 'Unknown')} (h-index: {best_author.get('h_index', 0)})")
        
        if show_all_authors:
            st.info(f"👥 Показаны все {len(sorted_authors)} авторов (сортировка по h-index)")
        else:
            st.info("👤 Показан только лучший автор")
        
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# ============================================
# СОЗДАНИЕ WIDGET-ИНТЕРФЕЙСА STREAMLIT
# ============================================

def main():
    # Page configuration
    st.set_page_config(
        page_title="Author Profile Analysis",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'primary_color' not in st.session_state:
        st.session_state.primary_color = '#667eea'
    if 'secondary_color' not in st.session_state:
        st.session_state.secondary_color = '#f39c12'
    if 'show_all_authors' not in st.session_state:
        st.session_state.show_all_authors = False
    if 'all_authors' not in st.session_state:
        st.session_state.all_authors = []
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'journal_logo_base64' not in st.session_state:
        st.session_state.journal_logo_base64 = None
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    # Apply theme
    primary = st.session_state.primary_color
    secondary = st.session_state.secondary_color
    apply_theme_css(primary, secondary)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Настройки")
        
        # Language selector
        lang_option = st.selectbox(
            "🌐 Язык",
            options=['en', 'ru'],
            format_func=lambda x: 'English' if x == 'en' else 'Русский',
            index=0 if st.session_state.language == 'en' else 1
        )
        if lang_option != st.session_state.language:
            st.session_state.language = lang_option
            st.rerun()
        
        st.markdown("---")
        
        # Color theme
        st.markdown("## 🎨 Цветовая тема")
        
        preset_themes = {
            "Default (Blue-Purple)": {"primary": "#667eea", "secondary": "#f39c12"},
            "Emerald (Green-Teal)": {"primary": "#2ecc71", "secondary": "#27ae60"},
            "Sunset (Orange-Coral)": {"primary": "#e74c3c", "secondary": "#c0392b"},
            "Ocean (Deep Blue)": {"primary": "#3498db", "secondary": "#2980b9"},
            "Royal (Purple-Pink)": {"primary": "#9b59b6", "secondary": "#e84393"},
            "Forest (Dark Green)": {"primary": "#27ae60", "secondary": "#2ecc71"},
            "Cherry (Red-Pink)": {"primary": "#e84393", "secondary": "#9b59b6"},
            "Amber (Yellow-Orange)": {"primary": "#f39c12", "secondary": "#e67e22"},
        }
        
        theme_option = st.selectbox(
            "🎨 Пресеты тем",
            options=list(preset_themes.keys()),
            index=0
        )
        
        use_preset = st.checkbox("Использовать пресет", value=True)
        
        if use_preset:
            selected_theme = preset_themes[theme_option]
            st.session_state.primary_color = selected_theme["primary"]
            st.session_state.secondary_color = selected_theme["secondary"]
        else:
            selected_color = st.color_picker(
                "🎨 Выберите основной цвет",
                value=st.session_state.primary_color
            )
            st.session_state.primary_color = selected_color
            st.session_state.secondary_color = get_complementary_color(selected_color)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div style="text-align: center;">'
                f'<div class="color-preview" style="background: {st.session_state.primary_color};"></div>'
                f'<div style="font-size: 11px; margin-top: 5px;">Основной</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f'<div style="text-align: center;">'
                f'<div class="color-preview" style="background: {st.session_state.secondary_color};"></div>'
                f'<div style="font-size: 11px; margin-top: 5px;">Дополнительный</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        st.markdown(
            f'<div class="complementary-preview" style="height: 8px; width: 100%; margin: 10px 0;"></div>',
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        st.markdown("## 📊 Параметры анализа")
        
        global USE_CACHE
        use_cache = st.checkbox("💾 Использовать кэш", value=USE_CACHE)
        USE_CACHE = use_cache
        
        if st.button("🗑️ Очистить кэш"):
            import shutil
            if os.path.exists('cache'):
                shutil.rmtree('cache')
                st.cache_data.clear()
                st.success("✅ Кэш очищен!")
        
        st.markdown("---")
        
        st.markdown("""
        <div style="font-size: 11px; color: #666; text-align: center;">
            🔬 Author Profile Analysis v2.0<br>
            © daM / Chimica Techno Acta
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    st.image("logo.png", width=250) if os.path.exists("logo.png") else None
    
    st.markdown("---")
    st.markdown("### 📊 Комплексный анализ профиля ученого по ORCID")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📥 Загрузка данных",
        "📊 Профиль ученого",
        "📄 Отчеты"
    ])
    
    with tab1:
        st.markdown('<div class="custom-tab fade-in">', unsafe_allow_html=True)
        st.header("Загрузка ORCID и параметры анализа")
        
        orcid_text = st.text_area(
            "ORCID автора(ов)",
            placeholder="0000-0002-1234-567X\n0000-0002-5678-9012\nили: 0000-0002-1234-567X, 0000-0002-5678-9012\nили: https://orcid.org/0000-0002-1234-567X",
            help="Введите один или несколько ORCID. Разделители: запятая, пробел, новая строка",
            height=100
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            journal_logo_upload = st.file_uploader(
                "Загрузить логотип журнала (опционально)",
                type=['png', 'jpg', 'jpeg', 'svg'],
                help="Логотип будет отображаться в отчетах"
            )
        
        with col2:
            show_all_authors = st.checkbox(
                "👥 Show data for all co-authors",
                value=st.session_state.show_all_authors,
                help="При включении показывает информацию о всех авторах, отсортированных по h-index"
            )
            st.session_state.show_all_authors = show_all_authors
        
        if st.button("🔍 Анализировать профиль(и)", type="primary", use_container_width=True):
            orcids = parse_orcids(orcid_text)
            
            if not orcids:
                st.error("⚠️ Введите хотя бы один ORCID")
            elif len(orcids) > 20:
                st.warning(f"⚠️ Найдено {len(orcids)} ORCID. Это может занять много времени...")
            else:
                journal_logo_data = None
                if journal_logo_upload:
                    journal_logo_data = {
                        journal_logo_upload.name: {
                            'content': journal_logo_upload.read()
                        }
                    }
                
                run_profile_analysis(orcids, show_all_authors, journal_logo_data)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if st.session_state.analysis_complete and st.session_state.all_authors:
            authors = st.session_state.all_authors
            show_all = st.session_state.show_all_authors
            journal_logo_base64 = st.session_state.journal_logo_base64
            
            st.markdown("## 📊 Профили ученых")
            
            if show_all:
                st.info(f"👥 Показаны все {len(authors)} авторов, отсортированных по h-index")
                st.markdown("---")
                
                for idx, author_data in enumerate(authors, 1):
                    is_best = (idx == 1)
                    author_name = author_data.get('author_name', f'Автор {idx}')
                    profile = author_data.get('profile', {})
                    publications = author_data.get('publications', [])
                    analyzer = author_data.get('analyzer')
                    
                    h_index = profile.get('h_index', 0)
                    total_pubs = profile.get('total_publications', 0)
                    total_citations = profile.get('total_citations', 0)
                    avg_citations = profile.get('average_citations', 0)
                    oa_percentage = profile.get('oa_percentage', 0)
                    recommendation = profile.get('recommendation', 'Нет рекомендации')
                    risk_flags = profile.get('risk_flags', [])
                    
                    author_class = "author-card best" if is_best else "author-card"
                    st.markdown(f"""
                    <div class="{author_class}">
                        <div>
                            <span class="author-rank">{idx}.</span>
                            <span class="author-name-main">{author_name}</span>
                            <span class="author-hindex">(h-index: {h_index})</span>
                            {'<span class="best-badge">🏆 Лучший</span>' if is_best else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("📄 Публикаций", total_pubs)
                    with col2:
                        st.metric("📈 h-index", h_index)
                    with col3:
                        st.metric("📊 Цитирований", f"{total_citations:,}")
                    with col4:
                        st.metric("⭐ Среднее", f"{avg_citations:.1f}")
                    with col5:
                        st.metric("🌐 OA", f"{oa_percentage:.1f}%")
                    
                    rec_color = "🟢" if "🟢" in recommendation else ("🟡" if "🟡" in recommendation else "🔴")
                    st.info(f"{rec_color} {recommendation}")
                    
                    if risk_flags:
                        for flag in risk_flags:
                            st.warning(flag)
                    
                    images = create_visualizations(profile) if profile else {}
                    
                    if images.get('years_chart'):
                        st.image(f"data:image/png;base64,{images['years_chart']}", use_column_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if images.get('journals_chart'):
                            st.image(f"data:image/png;base64,{images['journals_chart']}", use_column_width=True)
                    with col2:
                        if images.get('oa_chart'):
                            st.image(f"data:image/png;base64,{images['oa_chart']}", use_column_width=True)
                    
                    if images.get('wordcloud'):
                        st.image(f"data:image/png;base64,{images['wordcloud']}", use_column_width=True)
                    
                    with st.expander(f"📚 Публикации ({len(publications)})"):
                        if publications:
                            pub_data = []
                            for pub in sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True):
                                pub_data.append({
                                    'Название': pub.get('title', 'No title')[:80] + '...' if len(pub.get('title', '')) > 80 else pub.get('title', 'No title'),
                                    'Год': pub.get('publication_year', 'N/A'),
                                    'Журнал': pub.get('journal_name', 'Unknown')[:40],
                                    'Цитаты': pub.get('cited_by_count', 0),
                                    'DOI': pub.get('doi', '')
                                })
                            df = pd.DataFrame(pub_data[:20])
                            st.dataframe(df, use_container_width=True)
                            if len(publications) > 20:
                                st.caption(f"Показано 20 из {len(publications)} публикаций")
                    
                    st.markdown("---")
            
            else:
                best_author = authors[0]
                author_name = best_author.get('author_name', 'Unknown')
                profile = best_author.get('profile', {})
                publications = best_author.get('publications', [])
                analyzer = best_author.get('analyzer')
                
                st.markdown(f"### 🏆 Лучший автор: {author_name} (h-index: {profile.get('h_index', 0)})")
                
                images = create_visualizations(profile) if profile else {}
                
                # Display full profile using the original format
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📄 Публикаций", profile.get('total_publications', 0))
                with col2:
                    st.metric("📈 h-index", profile.get('h_index', 0))
                with col3:
                    st.metric("📊 g-index", profile.get('g_index', 0))
                with col4:
                    st.metric("📊 i10-index", profile.get('i10_index', 0))
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📖 Цитирований", f"{profile.get('total_citations', 0):,}")
                with col2:
                    st.metric("⭐ Среднее", f"{profile.get('average_citations', 0):.1f}")
                with col3:
                    st.metric("🌐 OA", f"{profile.get('oa_percentage', 0):.1f}%")
                with col4:
                    st.metric("📅 Активных лет", profile.get('active_years', 0))
                
                st.info(f"💡 {profile.get('recommendation', 'Нет рекомендации')}")
                
                if profile.get('risk_flags'):
                    for flag in profile['risk_flags']:
                        st.warning(flag)
                
                if images.get('years_chart'):
                    st.image(f"data:image/png;base64,{images['years_chart']}", use_column_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if images.get('journals_chart'):
                        st.image(f"data:image/png;base64,{images['journals_chart']}", use_column_width=True)
                    if images.get('publishers_chart'):
                        st.image(f"data:image/png;base64,{images['publishers_chart']}", use_column_width=True)
                with col2:
                    if images.get('oa_chart'):
                        st.image(f"data:image/png;base64,{images['oa_chart']}", use_column_width=True)
                    if images.get('affiliations_chart'):
                        st.image(f"data:image/png;base64,{images['affiliations_chart']}", use_column_width=True)
                
                if images.get('wordcloud'):
                    st.image(f"data:image/png;base64,{images['wordcloud']}", use_column_width=True)
                
                if images.get('citations_chart'):
                    st.image(f"data:image/png;base64,{images['citations_chart']}", use_column_width=True)
                
                if images.get('citation_distribution'):
                    st.image(f"data:image/png;base64,{images['citation_distribution']}", use_column_width=True)
                
                if images.get('thematic_structure'):
                    st.image(f"data:image/png;base64,{images['thematic_structure']}", use_column_width=True)
                
                if images.get('radar_chart'):
                    st.image(f"data:image/png;base64,{images['radar_chart']}", use_column_width=True)
                
                with st.expander("📚 Список публикаций"):
                    if publications:
                        pub_data = []
                        for pub in sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True):
                            pub_data.append({
                                'Название': pub.get('title', 'No title')[:80] + '...' if len(pub.get('title', '')) > 80 else pub.get('title', 'No title'),
                                'Год': pub.get('publication_year', 'N/A'),
                                'Журнал': pub.get('journal_name', 'Unknown')[:40],
                                'Цитаты': pub.get('cited_by_count', 0),
                                'OA': '✅' if pub.get('is_oa', False) else '❌',
                                'DOI': pub.get('doi', '')
                            })
                        df = pd.DataFrame(pub_data)
                        st.dataframe(df, use_container_width=True)
        else:
            st.info("👈 Загрузите данные на вкладке 'Загрузка данных' и нажмите 'Анализировать профиль(и)'")
    
    with tab3:
        if st.session_state.analysis_complete and st.session_state.all_authors:
            authors = st.session_state.all_authors
            show_all = st.session_state.show_all_authors
            journal_logo_base64 = st.session_state.journal_logo_base64
            
            theme_colors = {
                'primary': st.session_state.primary_color,
                'secondary': st.session_state.secondary_color
            }
            
            st.markdown("## 📄 Генерация отчетов")
            
            best_author = authors[0]
            
            st.info(f"🏆 Лучший автор: {best_author.get('author_name', 'Unknown')} (h-index: {best_author.get('h_index', 0)})")
            
            if show_all:
                st.info(f"👥 Отчет будет содержать информацию о всех {len(authors)} авторах")
            else:
                st.info("👤 Отчет будет содержать информацию только о лучшем авторе")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Скачать HTML отчет", use_container_width=True, type="primary"):
                    with st.spinner("Генерация HTML отчета..."):
                        html_report = generate_html_report_with_multiple_authors(
                            authors,
                            show_all,
                            journal_logo_base64,
                            theme_colors
                        )
                        
                        if show_all:
                            filename = f"profiles_{len(authors)}_authors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        else:
                            filename = f"profile_{best_author.get('author_name', 'unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        
                        st.download_button(
                            label="📥 Скачать HTML",
                            data=html_report.encode('utf-8'),
                            file_name=filename,
                            mime="text/html",
                            use_container_width=True
                        )
            
            with col2:
                if PDF_AVAILABLE:
                    if st.button("📄 Скачать PDF отчет", use_container_width=True, type="primary"):
                        with st.spinner("Генерация PDF отчета..."):
                            if not show_all:
                                profile = best_author.get('profile', {})
                                publications = best_author.get('publications', [])
                                images = create_visualizations(profile) if profile else {}
                                
                                pdf_filename = f"profile_{best_author.get('author_name', 'unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                
                                generate_pdf_report(
                                    profile,
                                    publications,
                                    images,
                                    pdf_filename,
                                    None,
                                    None,
                                    theme_colors
                                )
                                
                                with open(pdf_filename, 'rb') as f:
                                    st.download_button(
                                        label="📥 Скачать PDF",
                                        data=f.read(),
                                        file_name=pdf_filename,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                            else:
                                st.warning("⚠️ PDF отчет для множественных авторов пока недоступен. Используйте HTML отчет.")
                else:
                    st.warning("⚠️ ReportLab не установлен. PDF отчет недоступен.")
            
            if show_all:
                st.markdown("---")
                st.markdown("### 📋 Предпросмотр HTML отчета")
                st.info("Нажмите 'Скачать HTML отчет' для полного отчета")
        else:
            st.info("👈 Сначала выполните анализ на вкладке 'Загрузка данных'")

if __name__ == "__main__":
    main()
