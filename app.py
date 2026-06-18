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
import ipywidgets as widgets
from IPython.display import display, HTML, IFrame
from tqdm.notebook import tqdm
import re
import time
from datetime import datetime
import json
from typing import List, Set, Dict, Tuple, Optional, Any
import nest_asyncio
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
import colorsys
import html
from tenacity import retry, stop_after_attempt, wait_exponential, wait_random
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
import math

# Для PDF отчета
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ ReportLab не установлен. PDF отчет будет недоступен.")
    print("Установите: pip install reportlab")

# Для asyncio в Colab
nest_asyncio.apply()

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
        # Шрифты
        'font.size': 11,
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif', 'Computer Modern Roman'],
        'mathtext.fontset': 'stix',
        
        # Оси
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
        
        # Метки
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
        
        # Легенда
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '#000000',
        'legend.fancybox': False,
        'legend.borderaxespad': 0.5,
        'legend.handlelength': 1.5,
        'legend.handletextpad': 0.8,
        
        # Фигура
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'figure.facecolor': 'white',
        'figure.constrained_layout.use': True,
        'figure.figsize': (8, 6),
        
        # Линии
        'lines.linewidth': 2,
        'lines.markersize': 7,
        'lines.markeredgewidth': 1.0,
        'errorbar.capsize': 3,
        
        # PDF для публикаций
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })

# Применяем стиль
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
        # Берем первую букву первого слова (имя или инициал)
        first_initial = parts[0][0].upper()
        # Берем последнее слово (фамилия)
        last_name = parts[-1]
        return f"{first_initial} {last_name}"
    elif len(parts) == 1:
        return parts[0]
    else:
        return name

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
# ФУНКЦИИ ДЛЯ РАБОТЫ С ЦВЕТАМИ (ИЗ ВТОРОГО КОДА)
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
    # Rotate hue by 0.5 (180 degrees)
    complementary_hue = (h + 0.5) % 1.0
    complementary_rgb = colorsys.hsv_to_rgb(complementary_hue, s, v)
    return rgb_to_hex(tuple(int(c * 255) for c in complementary_rgb))

def get_analogous_colors(hex_color: str, count: int = 2) -> List[str]:
    """
    Generate analogous colors (colors adjacent on color wheel)
    Useful for gradients and accents
    """
    rgb = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    
    colors = []
    step = 30 / 360.0  # 30 degrees in hue space
    
    for i in range(count):
        offset = (i + 1) * step
        new_hue = (h + offset) % 1.0
        new_rgb = colorsys.hsv_to_rgb(new_hue, s, v)
        colors.append(rgb_to_hex(tuple(int(c * 255) for c in new_rgb)))
    
    return colors

def get_gradient_colors(hex_color: str, steps: int = 5) -> List[str]:
    """
    Generate gradient colors from base color to lighter shades
    """
    rgb = hex_to_rgb(hex_color)
    colors = []
    
    for i in range(steps):
        factor = 0.3 + (i * 0.14)  # 0.3 to 0.86
        new_rgb = tuple(min(255, int(c * (1 + factor * 0.5))) for c in rgb)
        colors.append(rgb_to_hex(new_rgb))
    
    return colors

def get_contrast_color(hex_color: str) -> str:
    """
    Get contrasting color (black or white) for text on a colored background
    Uses luminance calculation for optimal readability
    """
    rgb = hex_to_rgb(hex_color)
    # Calculate relative luminance (WCAG formula)
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return '#FFFFFF' if luminance < 0.5 else '#000000'

def generate_css_variables(base_color: str, accent_color: str = None) -> Dict[str, str]:
    """
    Generate complete CSS variable set for the theme
    """
    if accent_color is None:
        accent_color = get_complementary_color(base_color)
    
    # Generate gradient colors
    gradient_start = base_color
    gradient_end = accent_color
    
    # Generate lighter shades for backgrounds
    lighter_base = get_gradient_colors(base_color, 1)[0]
    lighter_accent = get_gradient_colors(accent_color, 1)[0]
    
    # Get contrast colors for text
    base_contrast = get_contrast_color(base_color)
    accent_contrast = get_contrast_color(accent_color)
    
    # Generate analogous colors for accents
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

def hex_to_reportlab_color(hex_color: str):
    """Convert hex color to reportlab color object"""
    rgb = hex_to_rgb(hex_color)
    return colors.Color(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С МНОЖЕСТВЕННЫМИ ORCID (НОВОЕ)
# ============================================

def parse_orcids(text: str) -> List[str]:
    """
    Парсит ORCID из текста.
    Поддерживает форматы:
    - 0000-0002-1234-567X
    - https://orcid.org/0000-0002-1234-567X
    - 0000-0002-1234-567X, 0000-0002-5678-9012
    - разделители: запятая, точка с запятой, пробел, новая строка
    """
    if not text or not text.strip():
        return []
    
    # Заменяем разделители на пробелы
    text = text.replace(',', ' ').replace(';', ' ').replace('\n', ' ')
    
    # Ищем все ORCID в тексте
    orcid_pattern = r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX]|\d{16})'
    matches = re.findall(orcid_pattern, text, re.IGNORECASE)
    
    # Очищаем каждый ORCID
    orcids = []
    for match in matches:
        cleaned = clean_orcid(match)
        if cleaned:
            orcids.append(cleaned)
    
    return list(dict.fromkeys(orcids))  # Убираем дубликаты

def sort_authors_by_h_index(authors: List[Dict]) -> List[Dict]:
    """Сортирует авторов по убыванию h-index"""
    return sorted(authors, key=lambda x: x.get('h_index', 0), reverse=True)

# ============================================
# ФУНКЦИЯ ПАРСИНГА ПУБЛИКАЦИИ ИЗ OPENALEX
# ============================================

def parse_openalex_publication(item: Dict) -> Dict:
    """Парсит публикацию из OpenAlex с расширенной информацией по темам и институтам"""
    try:
        pub = {}
        
        # Базовая информация
        pub['id'] = item.get('id', '')
        pub['doi'] = item.get('doi', '').replace('https://doi.org/', '')
        pub['title'] = item.get('title', 'No title')
        pub['publication_year'] = item.get('publication_year')
        
        # Тип
        pub['type'] = item.get('type', 'unknown')
        
        # Журнал и издательство
        if item.get('primary_location'):
            source = item['primary_location'].get('source', {})
            pub['journal_name'] = source.get('display_name', 'Unknown')
            pub['publisher'] = source.get('host_organization_name') or source.get('publisher', 'Unknown')
            pub['issn'] = source.get('issn', [])
        else:
            pub['journal_name'] = 'Unknown'
            pub['publisher'] = 'Unknown'
            pub['issn'] = []
        
        # Открытый доступ
        oa = item.get('open_access', {})
        pub['is_oa'] = oa.get('is_oa', False)
        pub['open_access_status'] = oa.get('oa_status', 'closed')
        pub['oa_url'] = oa.get('oa_url', None)
        
        # Аффилиации и ИНСТИТУТЫ (расширено для задачи 4)
        affiliations = []
        affiliation_countries = []
        institutions = []  # Новое поле для хранения детальной информации об институтах
        
        for auth in item.get('authorships', []):
            if auth.get('institutions'):
                for inst in auth['institutions']:
                    affil = inst.get('display_name', '')
                    if affil:
                        affiliations.append(affil)
                        country = extract_country_from_affiliation(affil)
                        if country:
                            affiliation_countries.append(country)
                        
                        # Сохраняем детальную информацию об институте
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
        pub['institutions'] = institutions  # Новое поле
        
        # Страна (из первой аффилиации)
        if affiliations:
            pub['country'] = extract_country_from_affiliation(affiliations[0])
        else:
            pub['country'] = 'Unknown'
        
        # Авторы с их ORCID
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
        
        # Количество авторов
        pub['author_count'] = len(authors)
        
        # ПЕРВИЧНАЯ ТЕМА
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
        
        # ТОПИКИ
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
        
        # КЛЮЧЕВЫЕ СЛОВА
        keywords = item.get('keywords', [])
        pub['keywords'] = [k.get('display_name', '') for k in keywords if k.get('display_name')]
        
        # Концепты с уровнями
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
            
            # Распределение по уровням
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
        
        # Цитаты
        pub['cited_by_count'] = item.get('cited_by_count', 0)
        pub['cited_by_percentile'] = item.get('cited_by_percentile', {})
        
        # Ретракции и коррекции
        pub['is_retracted'] = item.get('is_retracted', False)
        pub['is_correction'] = item.get('is_correction', False)
        pub['is_paratext'] = item.get('is_paratext', False)
        
        if pub['is_retracted']:
            pub['retraction_info'] = item.get('retraction_info', {})
        
        # Дополнительные метрики
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
    
    # Формируем запрос
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
    
    # Убираем дубликаты и пустые ID
    unique_ids = list(set([id for id in institution_ids if id]))
    
    if not unique_ids:
        return {}
    
    homepages = {}
    
    # Разбиваем на батчи по 50
    for batch in chunks(unique_ids, 50):
        # Формируем запрос к OpenAlex
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
        self.institution_homepages = {}  # Кэш для homepage институтов
        self.collaborations = {
            'domestic': defaultdict(lambda: defaultdict(int)),  # country -> affiliation -> count
            'international': defaultdict(lambda: defaultdict(int)),  # country -> affiliation -> count
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
        
        # Извлекаем аффилиации автора
        for aff in author_info.get('affiliations', []):
            inst_name = aff.get('institution', '')
            country = aff.get('country', '')
            if inst_name and inst_name not in self.author_affiliations:
                self.author_affiliations.append(inst_name)
                if country and country not in self.author_countries:
                    self.author_countries.append(country)
        
        # Если нет аффилиаций из OpenAlex, пробуем извлечь из публикаций
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
        
        # 1. Базовая информация
        self.profile['total_publications'] = len(self.publications)
        self.profile['orcid'] = self.orcid
        self.profile['author_name'] = self.author_name or 'Unknown'
        self.profile['author_affiliations'] = self.author_affiliations
        self.profile['author_countries'] = self.author_countries
        
        # 2. Распределение по годам
        years = [p.get('publication_year') for p in self.publications if p.get('publication_year')]
        self.profile['years_distribution'] = dict(Counter(years))
        self.profile['first_publication'] = min(years) if years else None
        self.profile['last_publication'] = max(years) if years else None
        self.profile['active_years'] = len(set(years)) if years else 0
        
        # 3. Журналы
        journals = [p.get('journal_name') for p in self.publications if p.get('journal_name')]
        self.profile['journals'] = dict(Counter(journals))
        self.profile['top_journals'] = dict(Counter(journals).most_common(10))
        
        # 4. Издательства
        publishers = [p.get('publisher') for p in self.publications if p.get('publisher') and p.get('publisher') != 'Unknown']
        self.profile['publishers'] = dict(Counter(publishers))
        
        # 5. Типы публикаций
        pub_types = [p.get('type') for p in self.publications if p.get('type')]
        self.profile['publication_types'] = dict(Counter(pub_types))
        
        # 6. Открытый доступ
        oa_statuses = [p.get('open_access_status') for p in self.publications if p.get('open_access_status')]
        self.profile['open_access'] = dict(Counter(oa_statuses))
        self.profile['total_oa'] = sum(1 for p in self.publications if p.get('is_oa', False))
        self.profile['oa_percentage'] = (self.profile['total_oa'] / len(self.publications) * 100) if self.publications else 0
        
        # 7. Аффилиации
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
        
        # 8. Страны (основная)
        countries = [p.get('country') for p in self.publications if p.get('country')]
        self.profile['countries'] = dict(Counter(countries))
        
        # 9. Концепты с детальной иерархией
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
        
        # 10. Ретракции и коррекции
        self.profile['retractions'] = sum(1 for p in self.publications if p.get('is_retracted', False))
        self.profile['corrections'] = sum(1 for p in self.publications if p.get('is_correction', False))
        self.profile['paratexts'] = sum(1 for p in self.publications if p.get('is_paratext', False))
        self.profile['retraction_details'] = [p.get('retraction_info') for p in self.publications if p.get('is_retracted')]
        
        # 11. Соавторы (исключаем автора через нормализацию - задача 2)
        coauthors = []
        coauthors_with_orcid = {}
        
        # Получаем нормализованное имя автора для сравнения
        author_name_normalized = normalize_author_name(self.author_name or '')
        author_orcid = self.orcid
        
        for p in self.publications:
            if p.get('authors'):
                authors_list = p['authors']
                orcids_list = p.get('author_orcids', [])
                
                for idx, name in enumerate(authors_list):
                    # Проверяем, не является ли этот автор анализируемым
                    is_self = False
                    
                    # Проверка по нормализованному имени (задача 2)
                    if author_name_normalized:
                        name_normalized = normalize_author_name(name)
                        if name_normalized == author_name_normalized:
                            is_self = True
                    
                    # Проверка по ORCID
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
        
        # 12. Количество авторов на статью
        author_counts = [p.get('author_count', 0) for p in self.publications if p.get('author_count', 0) > 0]
        if author_counts:
            self.profile['avg_authors_per_paper'] = np.mean(author_counts)
            self.profile['median_authors_per_paper'] = np.median(author_counts)
            self.profile['max_authors_per_paper'] = max(author_counts)
            self.profile['min_authors_per_paper'] = min(author_counts)
        
        # 13. Цитаты
        citations = [p.get('cited_by_count', 0) for p in self.publications]
        self.profile['total_citations'] = sum(citations)
        self.profile['average_citations'] = sum(citations) / len(citations) if citations else 0
        self.profile['median_citations'] = np.median(citations) if citations else 0
        self.profile['max_citations'] = max(citations) if citations else 0
        self.profile['citations_per_year'] = self.profile['total_citations'] / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        
        # Распределение цитирований
        citation_bins = [0, 1, 5, 10, 20, 50, 100, 500, 1000]
        citation_dist = {}
        for i in range(len(citation_bins)-1):
            lower = citation_bins[i]
            upper = citation_bins[i+1]
            citation_dist[f"{lower}-{upper}"] = sum(1 for c in citations if lower <= c < upper)
        citation_dist[f">{citation_bins[-1]}"] = sum(1 for c in citations if c >= citation_bins[-1])
        self.profile['citation_distribution'] = citation_dist
        
        # h-index
        citations_sorted = sorted([c for c in citations if c > 0], reverse=True)
        h_index = 0
        for i, c in enumerate(citations_sorted, 1):
            if c >= i:
                h_index = i
            else:
                break
        self.profile['h_index'] = h_index
        
        # i10-index
        self.profile['i10_index'] = sum(1 for c in citations if c >= 10)
        
        # g-index
        total_citations_sorted = 0
        g_index = 0
        for i, c in enumerate(citations_sorted, 1):
            total_citations_sorted += c
            if total_citations_sorted >= i**2:
                g_index = i
        self.profile['g_index'] = g_index
        
        # 14. Топ цитируемые статьи
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
        
        # 15. Тренд публикаций
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
        
        # 16. Оценка продуктивности
        self.profile['papers_per_year'] = len(self.publications) / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        self.profile['recent_productivity'] = len([y for y in years if y >= (datetime.now().year - 3)]) / 3 if years else 0
        self.profile['productivity_peak_year'] = max(year_counts.items(), key=lambda x: x[1])[0] if year_counts else None
        self.profile['productivity_peak_count'] = max(year_counts.values()) if year_counts else 0
        
        # 17. Статистика по типам доступа
        oa_types = {'gold': 0, 'green': 0, 'hybrid': 0, 'bronze': 0, 'closed': 0}
        for p in self.publications:
            status = p.get('open_access_status', 'closed')
            if status in oa_types:
                oa_types[status] += 1
        self.profile['oa_types'] = oa_types
        
        # 18. Тематическое разнообразие
        if all_concepts:
            concept_counts = Counter(all_concepts)
            total = len(all_concepts)
            shannon_index = 0
            for count in concept_counts.values():
                p = count / total
                shannon_index -= p * np.log(p)
            self.profile['thematic_diversity_shannon'] = shannon_index
            self.profile['unique_concepts'] = len(concept_counts)
        
        # 19. АНАЛИЗ КОЛЛАБОРАЦИЙ (задача 1 и 4 - исправлено)
        self._analyze_collaborations()
        
        # 20. Флаги риска
        self.profile['risk_flags'] = self._assess_risks()
        
        # 21. Рекомендация
        self.profile['recommendation'] = self._generate_recommendation()
        
        print("✅ Анализ завершен!")
    
    def _analyze_collaborations(self):
        """Анализирует коллаборации с детальным разбором по аффилиациям (задача 1 и 4)"""
        if not self.publications:
            return
        
        author_countries_set = set(self.author_countries) if self.author_countries else set()
        
        # Если у автора нет стран, пробуем извлечь из публикаций
        if not author_countries_set:
            for p in self.publications:
                if p.get('country') and p['country'] != 'Unknown':
                    author_countries_set.add(p['country'])
        
        # Если все еще нет стран, используем 'Unknown'
        if not author_countries_set:
            author_countries_set = {'Unknown'}
        
        # Сброс коллабораций
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
            
            # Собираем страны и аффилиации из публикации
            paper_countries = set()
            paper_affiliations = set()
            
            for inst in institutions:
                country = inst.get('country_code', '')
                if country:
                    paper_countries.add(country)
                affil_name = inst.get('display_name', '')
                if affil_name:
                    paper_affiliations.add(affil_name)
            
            # Убираем 'Unknown'
            paper_countries = {c for c in paper_countries if c and c != 'Unknown'}
            
            if not paper_countries:
                continue
            
            # Проверяем, есть ли страны автора среди стран публикации
            has_author_country = any(c in author_countries_set for c in paper_countries)
            has_other_countries = any(c not in author_countries_set for c in paper_countries)
            
            if has_author_country and not has_other_countries:
                # Только страны автора (domestic)
                domestic_papers += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country in author_countries_set and affil_name:
                        self.collaborations['domestic'][country][affil_name] += 1
                        
            elif has_author_country and has_other_countries:
                # Смешанные (есть страны автора и другие)
                mixed_papers += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country in author_countries_set and affil_name:
                        self.collaborations['domestic'][country][affil_name] += 1
                    elif country not in author_countries_set and country and affil_name:
                        self.collaborations['international'][country][affil_name] += 1
                        
            elif has_other_countries and not has_author_country:
                # Только другие страны (international)
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
        
        # Добавляем в профиль
        self.profile['collaborations'] = self.collaborations
        self.profile['domestic_papers_ratio'] = domestic_papers / len(self.publications) if self.publications else 0
        self.profile['international_papers_ratio'] = international_papers / len(self.publications) if self.publications else 0
        self.profile['collaboration_index'] = self.profile.get('avg_authors_per_paper', 0) - 1 if self.profile.get('avg_authors_per_paper', 0) > 0 else 0
        
        # Определяем самую коллаборативную страну
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
        
        # Очень высокая продуктивность
        if self.profile.get('papers_per_year', 0) > 30:
            flags.append("⚠️ Аномально высокая продуктивность (>30 статей в год)")
        
        # Много ретракций
        if self.profile.get('retractions', 0) > 1:
            flags.append(f"🔴 {self.profile['retractions']} ретракций в профиле")
        
        # Более 30% статей в одном журнале
        if self.profile.get('top_journals'):
            top_ratio = list(self.profile['top_journals'].values())[0] / self.profile['total_publications']
            if top_ratio > 0.3:
                flags.append("⚠️ >30% публикаций в одном журнале")
        
        # Подозрительные журналы
        suspicious_journals = ['Cureus', 'PLoS ONE', 'Scientific Reports']
        suspicious_pubs = [j for j in self.profile.get('journals', {}).keys() if any(s in j for s in suspicious_journals)]
        if suspicious_pubs:
            flags.append(f"⚠️ Публикации в журналах с низкой селективностью: {', '.join(suspicious_pubs[:3])}")
        
        # Низкое разнообразие тем
        if self.profile.get('unique_concepts', 0) < 5 and self.profile.get('total_publications', 0) > 10:
            flags.append("⚠️ Низкое тематическое разнообразие")
        
        # Отсутствие международного сотрудничества
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
    
    # Проверяем кэш
    cached_data = load_from_cache(orcid_clean)
    if cached_data:
        print("📦 Использую данные из кэша")
        analyzer = ScholarProfileAnalyzer(orcid_clean)
        
        # Восстанавливаем данные из кэша
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
        
        # Шаг 1: Получаем информацию об авторе из OpenAlex
        print("🔍 Получение информации об авторе...")
        author_info = await get_openalex_author(orcid_clean, session)
        if author_info:
            analyzer.set_author_info(author_info)
            print(f"👤 Автор: {author_info.get('display_name', 'Unknown')}")
            if analyzer.author_affiliations:
                print(f"🏛️ Аффилиации: {', '.join(analyzer.author_affiliations[:3])}")
        
        # Шаг 2: Получаем DOI из ORCID
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
        
        # Шаг 3: Получаем метаданные из OpenAlex
        all_metadata = []
        
        # Разбиваем на батчи
        doi_batches = list(chunks(all_dois, BATCH_SIZE))
        
        # Прогресс-бар
        for batch in doi_batches:
            batch_metadata = await get_openalex_metadata(batch, session)
            all_metadata.extend(batch_metadata)
            
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)
        
        print(f"✅ Собрано метаданных: {len(all_metadata)} записей")
        
        # Шаг 4: Парсим метаданные и добавляем в анализатор
        print("📊 Обработка публикаций...")
        
        for item in all_metadata:
            pub_data = parse_openalex_publication(item)
            if pub_data:
                analyzer.add_publication(pub_data)
        
        # Шаг 5: Получаем homepage для институтов (задача 4)
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
        
        # Шаг 6: Анализируем профиль
        analyzer.analyze_publications()
        
        # Шаг 7: Сохраняем в кэш
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
# ФУНКЦИЯ ДЛЯ АНАЛИЗА МНОЖЕСТВЕННЫХ ORCID (НОВОЕ)
# ============================================

async def analyze_multiple_authors(orcid_list: List[str]) -> List[Dict]:
    """Анализирует несколько авторов параллельно"""
    if not orcid_list:
        return []
    
    print(f"📊 Анализ {len(orcid_list)} авторов...")
    
    # Создаем задачи для каждого ORCID
    tasks = [collect_scholar_data(orcid) for orcid in orcid_list]
    
    # Выполняем все задачи параллельно с ограничением на количество одновременных
    results = []
    for i in range(0, len(tasks), MAX_CONCURRENT_REQUESTS):
        batch_tasks = tasks[i:i + MAX_CONCURRENT_REQUESTS]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
    
    # Формируем результат
    authors_data = []
    for analyzer, profile, publications in results:
        if analyzer and profile:
            authors_data.append({
                'orcid': analyzer.orcid,
                'author_name': profile.get('author_name', 'Unknown'),
                'h_index': profile.get('h_index', 0),
                'g_index': profile.get('g_index', 0),
                'i10_index': profile.get('i10_index', 0),
                'total_publications': profile.get('total_publications', 0),
                'total_citations': profile.get('total_citations', 0),
                'average_citations': profile.get('average_citations', 0),
                'profile': profile,
                'publications': publications,
                'analyzer': analyzer,
                'images': None  # Будет заполнено позже
            })
    
    return authors_data

# ============================================
# ФУНКЦИИ ДЛЯ ВИЗУАЛИЗАЦИИ (НАУЧНЫЙ СТИЛЬ)
# ============================================

def create_visualizations(profile: Dict) -> Dict[str, str]:
    """Создает визуализации в научном стиле и возвращает их в виде base64 изображений"""
    images = {}
    
    # Применяем научный стиль
    apply_scientific_style()
    
    # 1. График публикаций по годам (с трендом и целыми числами на оси Y)
    if profile.get('years_distribution'):
        fig, ax = plt.subplots(figsize=(10, 6))
        years = sorted(profile['years_distribution'].keys())
        counts = [profile['years_distribution'][y] for y in years]
        
        # Столбцы с цветовой градиентной заливкой
        bars = ax.bar(years, counts, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.2)
        
        # Добавляем значения над столбцами
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('Год публикации', fontsize=12, fontweight='bold')
        ax.set_ylabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Динамика публикационной активности', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Устанавливаем целые числа на оси Y
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Устанавливаем целые числа на оси X
        ax.set_xticks(years)
        ax.set_xticklabels([str(int(y)) for y in years], rotation=45)
        
        # Добавляем тренд
        if len(years) >= 2:
            x = np.arange(len(years))
            z = np.polyfit(x, counts, 1)
            p = np.poly1d(z)
            
            # Экстраполируем тренд
            x_extended = np.arange(len(years) + 2)
            y_extended = p(x_extended)
            
            # Рисуем линию тренда
            ax.plot(years, p(x), 'r-', linewidth=2.5, alpha=0.8, label='Тренд')
            
            # Добавляем доверительный интервал (полоса)
            if len(counts) > 3:
                std_err = np.std(counts - p(x)) / np.sqrt(len(counts))
                ax.fill_between(years, p(x) - 1.96*std_err, p(x) + 1.96*std_err, 
                               alpha=0.15, color='red', label='Доверительный интервал')
            
            # Текст с коэффициентом корреляции
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
    
    # 2. Топ журналов (горизонтальная гистограмма)
    if profile.get('top_journals'):
        fig, ax = plt.subplots(figsize=(10, 8))
        journals = list(profile['top_journals'].keys())[:10]
        counts = list(profile['top_journals'].values())[:10]
        
        # Сортировка по убыванию
        sorted_pairs = sorted(zip(counts, journals), reverse=True)
        counts, journals = zip(*sorted_pairs)
        
        y_pos = np.arange(len(journals))
        bars = ax.barh(y_pos, counts, color='#A23B72', alpha=0.8, edgecolor='black', linewidth=1.2)
        
        # Добавляем значения на бар
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
    
    # 3. Открытый доступ (ГИСТОГРАММА)
    if profile.get('open_access'):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Сортируем типы доступа в логическом порядке
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
        
        # Подготавливаем данные
        oa_data = profile.get('open_access', {})
        sorted_labels = []
        sorted_counts = []
        sorted_colors = []
        
        for oa_type in oa_order:
            if oa_type in oa_data:
                sorted_labels.append(oa_labels.get(oa_type, oa_type))
                sorted_counts.append(oa_data[oa_type])
                sorted_colors.append(oa_colors.get(oa_type, '#95A5A6'))
        
        # Строим вертикальную гистограмму
        bars = ax.bar(sorted_labels, sorted_counts, color=sorted_colors, 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Добавляем значения над столбцами
        for bar, count in zip(bars, sorted_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                   f'{count}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('Тип открытого доступа', fontsize=12, fontweight='bold')
        ax.set_ylabel('Число публикаций', fontsize=12, fontweight='bold')
        ax.set_title('Статус открытого доступа', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        
        # Устанавливаем целые числа на оси Y
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['oa_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 4. Word Cloud концептов
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
    
    # 5. Распределение по издательствам
    if profile.get('publishers'):
        fig, ax = plt.subplots(figsize=(10, 6))
        publishers = list(profile['publishers'].keys())[:8]
        counts = [profile['publishers'][p] for p in publishers]
        
        # Сортировка
        sorted_pairs = sorted(zip(counts, publishers), reverse=True)
        counts, publishers = zip(*sorted_pairs)
        
        bars = ax.bar(range(len(publishers)), counts, color='#5E4B56', alpha=0.8, 
                      edgecolor='black', linewidth=1.2)
        
        # Добавляем значения
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
        
        # Устанавливаем целые числа на оси Y
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['publishers_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 6. Топ цитируемые статьи
    if profile.get('most_cited'):
        fig, ax = plt.subplots(figsize=(10, 8))
        top_pubs = profile['most_cited'][:8]
        titles = [f"{p['title'][:35]}..." for p in top_pubs]
        citations = [p['citations'] for p in top_pubs]
        
        # Сортировка по цитированиям
        sorted_pairs = sorted(zip(citations, titles), reverse=True)
        citations, titles = zip(*sorted_pairs)
        
        bars = ax.barh(range(len(titles)), citations, color='#F18F01', alpha=0.8,
                       edgecolor='black', linewidth=1.2)
        
        # Добавляем значения
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
    
    # 7. Топ аффилиаций
    if profile.get('top_affiliations'):
        fig, ax = plt.subplots(figsize=(10, 6))
        affils = list(profile['top_affiliations'].keys())
        counts = list(profile['top_affiliations'].values())
        
        y_pos = np.arange(len(affils))
        bars = ax.barh(y_pos, counts, color='#3498DB', alpha=0.8,
                       edgecolor='black', linewidth=1.2)
        
        # Добавляем значения
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
    
    # 8. Тематическая структура
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('Тематическая структура исследований', fontsize=14, fontweight='bold')
    
    # Domains
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
    
    # Fields
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
    
    # Topics
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
    
    # Subtopics
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
    
    # 9. Распределение цитирований (гистограмма)
    if profile.get('citation_distribution'):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Берем только короткие диапазоны для читаемости
        dist = profile['citation_distribution']
        filtered_dist = {k: v for k, v in dist.items() if v > 0}
        
        ranges = list(filtered_dist.keys())
        counts = list(filtered_dist.values())
        
        bars = ax.bar(range(len(ranges)), counts, color='#8E44AD', alpha=0.8,
                      edgecolor='black', linewidth=1.2)
        
        # Добавляем значения
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
    
    # 10. RADAR CHART для тематического профиля
    if profile.get('top_concepts'):
        top_concepts_items = list(profile['top_concepts'].items())[:6]
        if len(top_concepts_items) >= 3:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            concepts = [item[0][:20] for item in top_concepts_items]
            values = [item[1] for item in top_concepts_items]
            
            # Нормализуем значения для radar chart
            max_val = max(values) if values else 1
            normalized = [v / max_val for v in values]
            
            # Добавляем первое значение в конец для замыкания
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
# ФУНКЦИИ ДЛЯ ГЕНЕРАЦИИ ОТЧЕТОВ (ОБНОВЛЕНЫ)
# ============================================

def generate_html_report_with_authors(
    all_authors: List[Dict],
    show_all_authors: bool,
    journal_logo_base64: Optional[str] = None,
    program_logo_base64: Optional[str] = None,
    theme_colors: Optional[Dict] = None,
    images: Optional[Dict] = None
) -> str:
    """
    Генерирует HTML отчет с одним или несколькими авторами.
    Использует дизайн из второго кода.
    """
    
    if not all_authors:
        return "<html><body><p>Нет данных для отчета</p></body></html>"
    
    # Сортируем авторов по h-index
    sorted_authors = sort_authors_by_h_index(all_authors)
    best_author = sorted_authors[0]
    
    # Настройка темы
    if theme_colors is None:
        theme_colors = {
            'primary': '#667eea',
            'secondary': '#f39c12'
        }
    
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')
    
    # Генерируем CSS переменные
    css_vars = generate_css_variables(primary, secondary)
    
    # Формируем навигацию
    sections = []
    
    # Всегда добавляем секцию обзора
    sections.append(('overview', '📊 Обзор'))
    
    if show_all_authors:
        # Добавляем секцию для каждого автора
        for idx, author in enumerate(sorted_authors):
            author_name = author.get('author_name', 'Unknown')
            h_index = author.get('h_index', 0)
            section_id = f"author_{idx}"
            section_title = f"{idx+1}. {author_name} (h-index: {h_index})"
            sections.append((section_id, section_title))
    else:
        # Только лучший автор
        author_name = best_author.get('author_name', 'Unknown')
        h_index = best_author.get('h_index', 0)
        sections.append(('best_author', f"🏆 {author_name} (h-index: {h_index})"))
    
    # Строим сайдбар навигации
    sidebar_html = '<div class="sidebar">\n'
    sidebar_html += '<h3>📑 Навигация</h3>\n'
    for section_id, section_title in sections:
        sidebar_html += f'<a href="#{section_id}"><span>{section_title}</span></a>\n'
    sidebar_html += '</div>\n'
    
    # Строим основной контент
    content_html = '<div class="main-content">\n'
    
    # Заголовок
    content_html += '<div class="header">\n'
    
    # Программный логотип
    if program_logo_base64:
        content_html += f'<div style="display: flex; justify-content: center; margin-bottom: 15px;">\n'
        content_html += f'<img src="data:image/png;base64,{program_logo_base64}" style="height: 80px; width: auto;" alt="Program Logo">\n'
        content_html += '</div>\n'
    
    # Логотип журнала
    if journal_logo_base64:
        content_html += f'<div style="display: flex; justify-content: center; margin-bottom: 15px;">\n'
        content_html += f'<img src="data:image/png;base64,{journal_logo_base64}" style="height: 150px; width: auto;" alt="Journal Logo">\n'
        content_html += '</div>\n'
    
    content_html += f'<h1>Профиль ученого</h1>\n'
    content_html += f'<div class="date">Дата генерации: {datetime.now().strftime("%d.%m.%Y %H:%M")}</div>\n'
    
    if show_all_authors:
        content_html += f'<div style="margin-top: 10px;">👥 Всего авторов: {len(sorted_authors)}</div>\n'
    else:
        content_html += f'<div style="margin-top: 10px;">👤 Показан лучший автор из {len(sorted_authors)}</div>\n'
    
    content_html += '</div>\n'
    
    # Секция обзора
    content_html += '<div id="overview" class="section">\n'
    content_html += '<div class="section-title">📊 Обзор</div>\n'
    
    # Общая статистика
    content_html += '<div class="stats-grid">\n'
    
    total_pubs = sum(a.get('total_publications', 0) for a in sorted_authors)
    total_citations = sum(a.get('total_citations', 0) for a in sorted_authors)
    avg_h_index = sum(a.get('h_index', 0) for a in sorted_authors) / len(sorted_authors) if sorted_authors else 0
    
    content_html += f'''
    <div class="stat-card">
        <div class="stat-number">{len(sorted_authors)}</div>
        <div class="stat-label">👥 Всего авторов</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_pubs}</div>
        <div class="stat-label">📄 Всего публикаций</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_citations:,}</div>
        <div class="stat-label">📊 Всего цитирований</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{avg_h_index:.1f}</div>
        <div class="stat-label">📈 Средний h-index</div>
    </div>
    '''
    
    content_html += '</div>\n'
    
    # Топ авторов (кратко)
    content_html += '<h3>🏆 Рейтинг авторов по h-index</h3>\n'
    content_html += '<div>\n'
    for idx, author in enumerate(sorted_authors[:10], 1):
        author_name = author.get('author_name', 'Unknown')
        h_index = author.get('h_index', 0)
        pubs = author.get('total_publications', 0)
        citations = author.get('total_citations', 0)
        
        content_html += f'''
        <div class="rank-item">
            <span class="rank-number">{idx}</span>
            <span class="rank-name">{author_name}</span>
            <span class="rank-count">h-index: {h_index} | 📄 {pubs} | 📊 {citations}</span>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {h_index / (sorted_authors[0].get('h_index', 1)) * 100}%;"></div>
            </div>
        </div>
        '''
    content_html += '</div>\n'
    content_html += '</div>\n'
    
    # Секции для каждого автора
    if show_all_authors:
        for idx, author in enumerate(sorted_authors):
            section_id = f"author_{idx}"
            author_name = author.get('author_name', 'Unknown')
            h_index = author.get('h_index', 0)
            profile = author.get('profile', {})
            
            content_html += f'<div id="{section_id}" class="section">\n'
            content_html += f'<div class="section-title">👤 {idx+1}. {author_name} (h-index: {h_index})</div>\n'
            
            # Метрики автора
            content_html += '<div class="stats-grid">\n'
            content_html += f'''
            <div class="stat-card">
                <div class="stat-number">{profile.get('total_publications', 0)}</div>
                <div class="stat-label">📄 Публикаций</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('h_index', 0)}</div>
                <div class="stat-label">📈 h-index</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('g_index', 0)}</div>
                <div class="stat-label">📊 g-index</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('i10_index', 0)}</div>
                <div class="stat-label">📊 i10-index</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('total_citations', 0):,}</div>
                <div class="stat-label">📖 Всего цитирований</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('average_citations', 0):.1f}</div>
                <div class="stat-label">⭐ Среднее цитирований</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('oa_percentage', 0):.1f}%</div>
                <div class="stat-label">🌐 Открытый доступ</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{profile.get('unique_coauthors', 0)}</div>
                <div class="stat-label">🤝 Уникальных соавторов</div>
            </div>
            '''
            content_html += '</div>\n'
            
            # Рекомендация
            recommendation = profile.get('recommendation', 'Нет рекомендации')
            rec_class = 'rec-green' if '🟢' in recommendation else ('rec-yellow' if '🟡' in recommendation else 'rec-red')
            content_html += f'''
            <div class="recommendation-box {rec_class}">
                <strong>💡 Рекомендация:</strong> {recommendation}
            </div>
            '''
            
            # Флаги риска
            risk_flags = profile.get('risk_flags', [])
            if risk_flags:
                content_html += '<div style="margin-top: 15px;"><strong>⚠️ Флаги риска:</strong></div>\n'
                for flag in risk_flags:
                    flag_class = 'flag-danger' if '🔴' in flag else 'flag-warning'
                    content_html += f'<div class="flag {flag_class}">{flag}</div>\n'
            
            # Визуализации
            if images and idx == 0:  # Показываем визуализации только для лучшего автора
                content_html += '<h3>📊 Визуализации</h3>\n'
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("years_chart", "")}" alt="Публикации по годам"></div>\n'
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("wordcloud", "")}" alt="Word Cloud"></div>\n'
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("thematic_structure", "")}" alt="Тематическая структура"></div>\n'
            
            # ORCID
            content_html += f'<div style="margin-top: 15px;"><strong>ORCID:</strong> {profile.get("orcid", "N/A")}</div>\n'
            
            # Аффилиации
            affils = profile.get('author_affiliations', [])
            if affils:
                content_html += f'<div><strong>🏛️ Аффилиации:</strong> {", ".join(affils[:3])}</div>\n'
            
            content_html += '</div>\n'
    else:
        # Только лучший автор
        author = best_author
        profile = author.get('profile', {})
        
        content_html += '<div id="best_author" class="section">\n'
        content_html += f'<div class="section-title">🏆 {author.get("author_name", "Unknown")} (h-index: {author.get("h_index", 0)})</div>\n'
        
        # Метрики автора
        content_html += '<div class="stats-grid">\n'
        content_html += f'''
        <div class="stat-card">
            <div class="stat-number">{profile.get('total_publications', 0)}</div>
            <div class="stat-label">📄 Публикаций</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('h_index', 0)}</div>
            <div class="stat-label">📈 h-index</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('g_index', 0)}</div>
            <div class="stat-label">📊 g-index</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('i10_index', 0)}</div>
            <div class="stat-label">📊 i10-index</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('total_citations', 0):,}</div>
            <div class="stat-label">📖 Всего цитирований</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('average_citations', 0):.1f}</div>
            <div class="stat-label">⭐ Среднее цитирований</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('oa_percentage', 0):.1f}%</div>
            <div class="stat-label">🌐 Открытый доступ</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{profile.get('unique_coauthors', 0)}</div>
            <div class="stat-label">🤝 Уникальных соавторов</div>
        </div>
        '''
        content_html += '</div>\n'
        
        # Рекомендация
        recommendation = profile.get('recommendation', 'Нет рекомендации')
        rec_class = 'rec-green' if '🟢' in recommendation else ('rec-yellow' if '🟡' in recommendation else 'rec-red')
        content_html += f'''
        <div class="recommendation-box {rec_class}">
            <strong>💡 Рекомендация:</strong> {recommendation}
        </div>
        '''
        
        # Флаги риска
        risk_flags = profile.get('risk_flags', [])
        if risk_flags:
            content_html += '<div style="margin-top: 15px;"><strong>⚠️ Флаги риска:</strong></div>\n'
            for flag in risk_flags:
                flag_class = 'flag-danger' if '🔴' in flag else 'flag-warning'
                content_html += f'<div class="flag {flag_class}">{flag}</div>\n'
        
        # Визуализации
        if images:
            content_html += '<h3>📊 Визуализации</h3>\n'
            
            if images.get('years_chart'):
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("years_chart", "")}" alt="Публикации по годам"></div>\n'
            
            if images.get('journals_chart'):
                content_html += f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">\n'
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("journals_chart", "")}" alt="Топ журналов"></div>\n'
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("oa_chart", "")}" alt="Открытый доступ"></div>\n'
                content_html += '</div>\n'
            
            if images.get('wordcloud'):
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("wordcloud", "")}" alt="Word Cloud"></div>\n'
            
            if images.get('citations_chart'):
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("citations_chart", "")}" alt="Самые цитируемые"></div>\n'
            
            if images.get('thematic_structure'):
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("thematic_structure", "")}" alt="Тематическая структура"></div>\n'
            
            if images.get('radar_chart'):
                content_html += f'<div class="chart-container"><img src="data:image/png;base64,{images.get("radar_chart", "")}" alt="Radar Chart"></div>\n'
        
        # ORCID
        content_html += f'<div style="margin-top: 15px;"><strong>ORCID:</strong> {profile.get("orcid", "N/A")}</div>\n'
        
        # Аффилиации
        affils = profile.get('author_affiliations', [])
        if affils:
            content_html += f'<div><strong>🏛️ Аффилиации:</strong> {", ".join(affils[:3])}</div>\n'
        
        content_html += '</div>\n'
    
    # Footer
    content_html += '''
    <div class="footer">
        © Author Profile Analysis / Created by daM / Chimica Techno Acta<br>
        <a href="https://chimicatechnoacta.ru" target="_blank">https://chimicatechnoacta.ru</a>
    </div>
    '''
    
    content_html += '</div>\n'
    
    # Полный HTML с CSS
    css = f'''
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Times New Roman', 'DejaVu Serif', serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 0;
            margin: 0;
        }}
        .report-wrapper {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
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
        }}
        .sidebar a {{
            color: white;
            text-decoration: none;
            display: block;
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
            font-size: 32px;
            margin-bottom: 10px;
            color: white;
        }}
        .header .date {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .stat-label {{
            color: #666;
            margin-top: 8px;
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
        }}
        .rank-item {{
            background: white;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
            transition: all 0.3s;
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
            width: 300px;
            font-weight: 500;
        }}
        .rank-count {{
            float: right;
            color: #666;
        }}
        .progress-bar {{
            background: #e0e0e0;
            border-radius: 10px;
            height: 8px;
            margin-top: 8px;
            overflow: hidden;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, {primary}, {secondary});
            height: 100%;
            border-radius: 10px;
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
        }}
        .rec-green {{ background-color: #D5F5E3; border-left: 4px solid #2ECC71; }}
        .rec-yellow {{ background-color: #FEF9E7; border-left: 4px solid #F39C12; }}
        .rec-red {{ background-color: #FDEDEC; border-left: 4px solid #E74C3C; }}
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
        .flag-warning {{
            background-color: #FEF9E7;
            border-left-color: #F39C12;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #e0e0e0;
            margin-top: 30px;
        }}
        .footer a {{
            color: {primary};
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 768px) {{
            .sidebar {{ display: none; }}
            .main-content {{ margin-left: 0; padding: 20px; }}
        }}
    </style>
    '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Профиль ученого</title>
        {css}
    </head>
    <body>
        <div class="report-wrapper">
            {sidebar_html}
            {content_html}
        </div>
    </body>
    </html>
    '''
    
    return html

def generate_pdf_report_with_authors(
    all_authors: List[Dict],
    show_all_authors: bool,
    journal_logo_base64: Optional[str] = None,
    program_logo_base64: Optional[str] = None,
    theme_colors: Optional[Dict] = None,
    images: Optional[Dict] = None,
    filename: str = "profile_report.pdf"
):
    """Генерирует PDF отчет с тем же дизайном, что и HTML"""
    
    if not PDF_AVAILABLE:
        print("❌ ReportLab не установлен. PDF отчет не может быть сгенерирован.")
        print("Установите: pip install reportlab")
        return
    
    if not all_authors:
        print("❌ Нет данных для отчета")
        return
    
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Настройка темы
    if theme_colors is None:
        theme_colors = {
            'primary': '#667eea',
            'secondary': '#f39c12'
        }
    
    primary_color = hex_to_reportlab_color(theme_colors.get('primary', '#667eea'))
    secondary_color = hex_to_reportlab_color(theme_colors.get('secondary', '#f39c12'))
    
    # Создаем стили
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
        fontSize=18,
        textColor=primary_color,
        spaceAfter=15,
        fontName='Times-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=secondary_color,
        spaceAfter=10,
        fontName='Times-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontName = 'Times-Roman'
    normal_style.fontSize = 11
    
    # Заголовок
    story.append(Paragraph("Профиль ученого", title_style))
    
    # Информация о дате
    date_style = ParagraphStyle(
        'DateStyle',
        parent=normal_style,
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.gray
    )
    story.append(Paragraph(f"Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
    story.append(Spacer(1, 20))
    
    # Общая статистика
    sorted_authors = sort_authors_by_h_index(all_authors)
    total_pubs = sum(a.get('total_publications', 0) for a in sorted_authors)
    total_citations = sum(a.get('total_citations', 0) for a in sorted_authors)
    avg_h_index = sum(a.get('h_index', 0) for a in sorted_authors) / len(sorted_authors) if sorted_authors else 0
    
    stats_data = [
        ['Показатель', 'Значение'],
        ['Всего авторов', str(len(sorted_authors))],
        ['Всего публикаций', str(total_pubs)],
        ['Всего цитирований', f"{total_citations:,}"],
        ['Средний h-index', f"{avg_h_index:.1f}"]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Рейтинг авторов
    story.append(Paragraph("Рейтинг авторов по h-index", heading_style))
    
    for idx, author in enumerate(sorted_authors[:10], 1):
        author_name = author.get('author_name', 'Unknown')
        h_index = author.get('h_index', 0)
        pubs = author.get('total_publications', 0)
        citations = author.get('total_citations', 0)
        
        story.append(Paragraph(
            f"{idx}. <b>{author_name}</b> — h-index: {h_index}, публикаций: {pubs}, цитирований: {citations}",
            normal_style
        ))
    
    story.append(Spacer(1, 20))
    
    # Секции для авторов
    if show_all_authors:
        for idx, author in enumerate(sorted_authors):
            story.append(PageBreak())
            author_name = author.get('author_name', 'Unknown')
            h_index = author.get('h_index', 0)
            profile = author.get('profile', {})
            
            story.append(Paragraph(f"{idx+1}. {author_name} (h-index: {h_index})", heading_style))
            
            # Метрики автора
            metrics_data = [
                ['Метрика', 'Значение'],
                ['Публикаций', str(profile.get('total_publications', 0))],
                ['h-index', str(profile.get('h_index', 0))],
                ['g-index', str(profile.get('g_index', 0))],
                ['i10-index', str(profile.get('i10_index', 0))],
                ['Всего цитирований', f"{profile.get('total_citations', 0):,}"],
                ['Среднее цитирований', f"{profile.get('average_citations', 0):.1f}"],
                ['Открытый доступ', f"{profile.get('oa_percentage', 0):.1f}%"],
                ['Уникальных соавторов', str(profile.get('unique_coauthors', 0))]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 10))
            
            # Рекомендация
            recommendation = profile.get('recommendation', 'Нет рекомендации')
            story.append(Paragraph(f"<b>Рекомендация:</b> {recommendation}", normal_style))
            story.append(Spacer(1, 5))
            
            # ORCID
            orcid = profile.get('orcid', 'N/A')
            story.append(Paragraph(f"<b>ORCID:</b> {orcid}", normal_style))
            
            # Аффилиации
            affils = profile.get('author_affiliations', [])
            if affils:
                story.append(Paragraph(f"<b>Аффилиации:</b> {', '.join(affils[:3])}", normal_style))
            
            story.append(Spacer(1, 10))
    else:
        # Только лучший автор
        author = sorted_authors[0]
        profile = author.get('profile', {})
        
        story.append(PageBreak())
        story.append(Paragraph(f"🏆 {author.get('author_name', 'Unknown')} (h-index: {author.get('h_index', 0)})", heading_style))
        
        # Метрики автора
        metrics_data = [
            ['Метрика', 'Значение'],
            ['Публикаций', str(profile.get('total_publications', 0))],
            ['h-index', str(profile.get('h_index', 0))],
            ['g-index', str(profile.get('g_index', 0))],
            ['i10-index', str(profile.get('i10_index', 0))],
            ['Всего цитирований', f"{profile.get('total_citations', 0):,}"],
            ['Среднее цитирований', f"{profile.get('average_citations', 0):.1f}"],
            ['Открытый доступ', f"{profile.get('oa_percentage', 0):.1f}%"],
            ['Уникальных соавторов', str(profile.get('unique_coauthors', 0))]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 10))
        
        # Рекомендация
        recommendation = profile.get('recommendation', 'Нет рекомендации')
        story.append(Paragraph(f"<b>Рекомендация:</b> {recommendation}", normal_style))
        story.append(Spacer(1, 5))
        
        # ORCID
        orcid = profile.get('orcid', 'N/A')
        story.append(Paragraph(f"<b>ORCID:</b> {orcid}", normal_style))
        
        # Аффилиации
        affils = profile.get('author_affiliations', [])
        if affils:
            story.append(Paragraph(f"<b>Аффилиации:</b> {', '.join(affils[:3])}", normal_style))
        
        story.append(Spacer(1, 10))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=normal_style,
        fontSize=10,
        textColor=colors.gray,
        alignment=TA_CENTER
    )
    story.append(Paragraph("© Author Profile Analysis / Created by daM / Chimica Techno Acta", footer_style))
    story.append(Paragraph("https://chimicatechnoacta.ru", footer_style))
    
    # Построение PDF
    try:
        doc.build(story)
        print(f"✅ PDF отчет сохранен: {filename}")
    except Exception as e:
        print(f"❌ Ошибка при создании PDF: {e}")

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ДЛЯ STREAMLIT
# ============================================

def run_profile_analysis_streamlit(orcid_input: str, show_all_authors: bool, journal_logo_base64: Optional[str] = None):
    """Запускает полный анализ профиля ученого в Streamlit"""
    
    try:
        # Парсим ORCID
        orcid_list = parse_orcids(orcid_input)
        
        if not orcid_list:
            st.error("⚠️ Введите хотя бы один корректный ORCID")
            return
        
        st.info(f"📊 Найдено {len(orcid_list)} ORCID для анализа")
        
        if len(orcid_list) > 10:
            st.warning(f"⚠️ Найдено {len(orcid_list)} ORCID. Это может занять время...")
        
        # Запускаем анализ
        with st.spinner(f"🔄 Анализ {len(orcid_list)} авторов..."):
            # Используем asyncio для запуска
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            all_authors = loop.run_until_complete(analyze_multiple_authors(orcid_list))
            loop.close()
        
        if not all_authors:
            st.error("❌ Не удалось получить данные ни для одного автора")
            return
        
        # Сортируем авторов
        sorted_authors = sort_authors_by_h_index(all_authors)
        best_author = sorted_authors[0]
        
        st.success(f"✅ Проанализировано {len(sorted_authors)} авторов")
        st.info(f"🏆 Лучший автор: {best_author.get('author_name', 'Unknown')} (h-index: {best_author.get('h_index', 0)})")
        
        # Сохраняем в session_state
        ss.all_authors = sorted_authors
        ss.best_author = best_author
        ss.show_all_authors = show_all_authors
        ss.journal_logo_base64 = journal_logo_base64
        
        # Создаем визуализации для лучшего автора
        with st.spinner("🎨 Создание визуализаций..."):
            best_profile = best_author.get('profile', {})
            images = create_visualizations(best_profile)
            ss.images = images
        
        st.success("✅ Анализ завершен! Перейдите на вкладку 'Профиль ученого' для просмотра результатов")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ ОТОБРАЖЕНИЯ ПРОФИЛЯ
# ============================================

def display_author_profile_streamlit(author: Dict, show_all: bool, idx: int = 0):
    """Отображает профиль одного автора в Streamlit"""
    
    profile = author.get('profile', {})
    author_name = author.get('author_name', 'Unknown')
    h_index = author.get('h_index', 0)
    
    if show_all:
        st.markdown(f"## {idx+1}. {author_name} (h-index: {h_index})")
    else:
        st.markdown(f"## 🏆 Лучший автор: {author_name} (h-index: {h_index})")
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Публикаций", profile.get('total_publications', 0))
    with col2:
        st.metric("📈 h-index", profile.get('h_index', 0))
    with col3:
        st.metric("📊 g-index", profile.get('g_index', 0))
    with col4:
        st.metric("📊 i10-index", profile.get('i10_index', 0))
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("📖 Цитирований", f"{profile.get('total_citations', 0):,}")
    with col6:
        st.metric("⭐ Среднее", f"{profile.get('average_citations', 0):.1f}")
    with col7:
        st.metric("🌐 Открытый доступ", f"{profile.get('oa_percentage', 0):.1f}%")
    with col8:
        st.metric("🤝 Соавторов", profile.get('unique_coauthors', 0))
    
    # Рекомендация
    recommendation = profile.get('recommendation', 'Нет рекомендации')
    if '🟢' in recommendation:
        st.success(f"💡 {recommendation}")
    elif '🟡' in recommendation:
        st.warning(f"💡 {recommendation}")
    else:
        st.error(f"💡 {recommendation}")
    
    # Флаги риска
    risk_flags = profile.get('risk_flags', [])
    if risk_flags:
        with st.expander("⚠️ Флаги риска"):
            for flag in risk_flags:
                if '🔴' in flag:
                    st.error(flag)
                else:
                    st.warning(flag)
    
    # Визуализации
    if ss.get('images'):
        st.markdown("### 📊 Визуализации")
        
        images = ss.images
        
        if images.get('years_chart'):
            st.image(BytesIO(base64.b64decode(images['years_chart'])), use_column_width=True)
        
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            if images.get('journals_chart'):
                st.image(BytesIO(base64.b64decode(images['journals_chart'])), use_column_width=True)
        with col_img2:
            if images.get('oa_chart'):
                st.image(BytesIO(base64.b64decode(images['oa_chart'])), use_column_width=True)
        
        if images.get('wordcloud'):
            st.image(BytesIO(base64.b64decode(images['wordcloud'])), use_column_width=True)
        
        if images.get('thematic_structure'):
            st.image(BytesIO(base64.b64decode(images['thematic_structure'])), use_column_width=True)
        
        if images.get('radar_chart'):
            st.image(BytesIO(base64.b64decode(images['radar_chart'])), use_column_width=True)
    
    # ORCID
    st.markdown(f"**ORCID:** {profile.get('orcid', 'N/A')}")
    
    # Аффилиации
    affils = profile.get('author_affiliations', [])
    if affils:
        st.markdown(f"**🏛️ Аффилиации:** {', '.join(affils[:3])}")
    
    # Топ соавторы
    top_coauthors = profile.get('top_coauthors', {})
    if top_coauthors:
        with st.expander("🤝 Топ соавторы"):
            for author_name, count in list(top_coauthors.items())[:10]:
                st.text(f"{author_name}: {count} совместных работ")
    
    st.divider()

# ============================================
# ПОЛНОСТЬЮ НОВЫЙ STREAMLIT ИНТЕРФЕЙС
# ============================================

def main():
    """Главная функция Streamlit приложения"""
    
    # Настройка страницы
    st.set_page_config(
        page_title="Author Profile Analysis",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Инициализация session_state
    if 'all_authors' not in ss:
        ss.all_authors = []
    if 'best_author' not in ss:
        ss.best_author = None
    if 'show_all_authors' not in ss:
        ss.show_all_authors = False
    if 'journal_logo_base64' not in ss:
        ss.journal_logo_base64 = None
    if 'images' not in ss:
        ss.images = {}
    if 'primary_color' not in ss:
        ss.primary_color = '#667eea'
    if 'secondary_color' not in ss:
        ss.secondary_color = '#f39c12'
    if 'use_cache' not in ss:
        ss.use_cache = True
    if 'language' not in ss:
        ss.language = 'ru'
    
    # ========== БОКОВАЯ ПАНЕЛЬ ==========
    with st.sidebar:
        st.markdown("## ⚙️ Настройки")
        
        # Язык
        st.markdown("### 🌐 Язык")
        lang_option = st.selectbox(
            "",
            options=['ru', 'en'],
            format_func=lambda x: 'Русский' if x == 'ru' else 'English',
            index=0 if ss.language == 'ru' else 1
        )
        if lang_option != ss.language:
            ss.language = lang_option
            st.rerun()
        
        st.markdown("---")
        
        # Цветовая тема (из второго кода)
        st.markdown("### 🎨 Цветовая тема")
        
        preset_themes = {
            "По умолчанию (Сине-фиолетовый)": {"primary": "#667eea", "secondary": "#9b59b6"},
            "Изумруд (Зелено-бирюзовый)": {"primary": "#2ecc71", "secondary": "#27ae60"},
            "Закат (Оранжево-коралловый)": {"primary": "#e74c3c", "secondary": "#c0392b"},
            "Океан (Темно-синий)": {"primary": "#3498db", "secondary": "#2980b9"},
            "Королевский (Фиолетово-розовый)": {"primary": "#9b59b6", "secondary": "#e84393"},
            "Лес (Темно-зеленый)": {"primary": "#27ae60", "secondary": "#2ecc71"},
            "Вишня (Красно-розовый)": {"primary": "#e84393", "secondary": "#9b59b6"},
            "Янтарь (Желто-оранжевый)": {"primary": "#f39c12", "secondary": "#e67e22"},
        }
        
        theme_option = st.selectbox(
            "Пресеты тем",
            options=list(preset_themes.keys()),
            index=0
        )
        
        use_preset = st.checkbox("Использовать пресет", value=True)
        
        if use_preset:
            selected_theme = preset_themes[theme_option]
            ss.primary_color = selected_theme["primary"]
            ss.secondary_color = selected_theme["secondary"]
        else:
            selected_color = st.color_picker(
                "Выберите основной цвет",
                value=ss.primary_color
            )
            ss.primary_color = selected_color
            ss.secondary_color = get_complementary_color(selected_color)
        
        # Превью цветов
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div style="background: {ss.primary_color}; height: 30px; border-radius: 8px; text-align: center; color: white; padding: 5px;">Primary</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f'<div style="background: {ss.secondary_color}; height: 30px; border-radius: 8px; text-align: center; color: white; padding: 5px;">Secondary</div>',
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
        # Настройки кэша
        st.markdown("### 💾 Кэширование")
        ss.use_cache = st.checkbox("Использовать кэш", value=ss.use_cache)
        
        if st.button("🗑️ Очистить кэш", use_container_width=True):
            if os.path.exists('cache'):
                shutil.rmtree('cache')
                os.makedirs('cache')
            st.cache_data.clear()
            st.success("✅ Кэш очищен!")
        
        st.markdown("---")
        
        # Информация
        st.markdown("### 📌 Инструкция")
        st.markdown("""
        1. Введите ORCID авторов        2. Загрузите логотип журнала (опционально)
        3. Выберите режим отображения
        4. Нажмите 'Анализировать'
        5. Просмотрите результаты на вкладках
        """)
        
        st.markdown("---")
        st.markdown("© Chimica Techno Acta")
        st.markdown("[chimicatechnoacta.ru](https://chimicatechnoacta.ru)")
    
    # ========== ОСНОВНОЙ ИНТЕРФЕЙС ==========
    
    # Заголовок
    st.image("assets/logo.png", width=200) if os.path.exists("assets/logo.png") else None
    st.title("🔬 Author Profile Analysis")
    st.caption("Анализ профиля ученого по ORCID с расширенными метриками")
    st.markdown("---")
    
    # Вкладки
    tab1, tab2, tab3 = st.tabs(["📥 Загрузка данных", "📊 Профиль ученого", "📄 Отчеты"])
    
    # ========== ВКЛАДКА 1: ЗАГРУЗКА ДАННЫХ ==========
    with tab1:
        st.markdown("### 📥 Введите ORCID автора(ов)")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            orcid_input = st.text_area(
                "ORCID (один или несколько)",
                placeholder="0000-0002-1234-567X\n0000-0002-5678-9012\nили через запятую: 0000-0002-1234-567X, 0000-0002-5678-9012",
                help="Введите один или несколько ORCID. Разделители: запятая, пробел, новая строка",
                height=100
            )
        
        with col2:
            st.markdown("### 📎 Логотип журнала")
            journal_logo = st.file_uploader(
                "Загрузить логотип (опционально)",
                type=['png', 'jpg', 'jpeg', 'svg'],
                key="journal_logo_uploader"
            )
            
            journal_logo_base64 = None
            if journal_logo:
                try:
                    journal_logo_base64 = base64.b64encode(journal_logo.read()).decode()
                    st.success("✅ Логотип загружен")
                except Exception as e:
                    st.error(f"Ошибка загрузки: {e}")
        
        # Настройки
        st.markdown("### ⚙️ Настройки анализа")
        
        show_all_authors = st.checkbox(
            "👥 Show data for all co-authors",
            value=ss.show_all_authors,
            help="При включении показывает информацию о всех авторах, отсортированных по h-index"
        )
        ss.show_all_authors = show_all_authors
        
        # Кнопка анализа
        if st.button("🔍 Анализировать профиль(и)", type="primary", use_container_width=True):
            if not orcid_input or not orcid_input.strip():
                st.error("⚠️ Введите хотя бы один ORCID")
            else:
                # Запускаем анализ
                run_profile_analysis_streamlit(orcid_input, show_all_authors, journal_logo_base64)
    
    # ========== ВКЛАДКА 2: ПРОФИЛЬ УЧЕНОГО ==========
    with tab2:
        if not ss.all_authors:
            st.info("👈 Загрузите данные на вкладке 'Загрузка данных'")
        else:
            show_all = ss.show_all_authors
            
            if show_all:
                st.markdown(f"### 👥 Все авторы (отсортированы по h-index)")
                st.markdown(f"*Всего авторов: {len(ss.all_authors)}*")
                
                for idx, author in enumerate(ss.all_authors):
                    display_author_profile_streamlit(author, True, idx)
            else:
                st.markdown(f"### 🏆 Лучший автор")
                st.markdown(f"*Всего проанализировано авторов: {len(ss.all_authors)}*")
                
                if ss.best_author:
                    display_author_profile_streamlit(ss.best_author, False)
                else:
                    st.warning("⚠️ Нет данных о лучшем авторе")
    
    # ========== ВКЛАДКА 3: ОТЧЕТЫ ==========
    with tab3:
        if not ss.all_authors:
            st.info("👈 Загрузите данные на вкладке 'Загрузка данных'")
        else:
            st.markdown("### 📄 Генерация отчетов")
            
            st.info(f"📊 Доступно отчетов: {len(ss.all_authors)} авторов")
            
            if ss.show_all_authors:
                st.markdown("👥 **Режим:** Показаны все авторы")
            else:
                best = ss.best_author
                st.markdown(f"🏆 **Режим:** Показан лучший автор — {best.get('author_name', 'Unknown')} (h-index: {best.get('h_index', 0)})")
            
            # Кнопки скачивания
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Скачать HTML отчет", use_container_width=True):
                    with st.spinner("Генерация HTML отчета..."):
                        # Получаем тему
                        theme = {
                            'primary': ss.primary_color,
                            'secondary': ss.secondary_color
                        }
                        
                        # Получаем логотип программы (если есть)
                        program_logo_base64 = None
                        if os.path.exists("assets/logo.png"):
                            with open("assets/logo.png", "rb") as f:
                                program_logo_base64 = base64.b64encode(f.read()).decode()
                        
                        # Генерируем HTML
                        html_report = generate_html_report_with_authors(
                            ss.all_authors,
                            ss.show_all_authors,
                            ss.journal_logo_base64,
                            program_logo_base64,
                            theme,
                            ss.images
                        )
                        
                        # Скачиваем
                        st.download_button(
                            label="📥 Скачать HTML",
                            data=html_report.encode('utf-8'),
                            file_name=f"profile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html",
                            use_container_width=True
                        )
            
            with col2:
                if st.button("📄 Скачать PDF отчет", use_container_width=True):
                    if PDF_AVAILABLE:
                        with st.spinner("Генерация PDF отчета..."):
                            # Получаем тему
                            theme = {
                                'primary': ss.primary_color,
                                'secondary': ss.secondary_color
                            }
                            
                            # Получаем логотип программы (если есть)
                            program_logo_base64 = None
                            if os.path.exists("assets/logo.png"):
                                with open("assets/logo.png", "rb") as f:
                                    program_logo_base64 = base64.b64encode(f.read()).decode()
                            
                            # Генерируем PDF
                            filename = f"profile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            generate_pdf_report_with_authors(
                                ss.all_authors,
                                ss.show_all_authors,
                                ss.journal_logo_base64,
                                program_logo_base64,
                                theme,
                                ss.images,
                                filename
                            )
                            
                            # Читаем файл для скачивания
                            with open(filename, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="📥 Скачать PDF",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                            
                            # Удаляем временный файл
                            if os.path.exists(filename):
                                os.remove(filename)
                    else:
                        st.error("❌ ReportLab не установлен. Установите: pip install reportlab")

# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == "__main__":
    main()
