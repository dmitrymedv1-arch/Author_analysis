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
USE_CACHE = False  # Кэширование результатов
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

# ============================================
# СЛОВАРЬ ПЕРЕВОДОВ
# ============================================

LANG = {
    'en': {
        'app_title': 'Author Profile Analysis',
        'app_icon': '🔬',
        'settings': '⚙️ Settings',
        'language': '🌐 Language',
        'language_en': 'English',
        'language_ru': 'Russian',
        'color_theme': '🎨 Color Theme',
        'preset_themes': '🎨 Theme Presets',
        'use_preset': 'Use preset',
        'select_color': '🎨 Select primary color',
        'primary': 'Primary',
        'secondary': 'Secondary',
        'analysis_params': '📊 Analysis Parameters',
        'use_cache': '💾 Use cache',
        'clear_cache': '🗑️ Clear cache',
        'cache_cleared': '✅ Cache cleared!',
        'load_data': '📥 Load Data',
        'profile': '📊 Scholar Profile',
        'reports': '📄 Reports',
        'orcid_input': 'Author ORCID(s)',
        'orcid_placeholder': '0000-0002-1234-567X\n0000-0002-5678-9012\nor: 0000-0002-1234-567X, 0000-0002-5678-9012\nor: https://orcid.org/0000-0002-1234-567X',
        'orcid_help': 'Enter one or more ORCIDs. Separators: comma, space, new line',
        'upload_logo': 'Upload journal logo (optional)',
        'logo_help': 'Logo will be displayed in reports',
        'show_all_authors': '👥 Show data for all co-authors',
        'show_all_help': 'When enabled, shows information about all authors sorted by h-index',
        'analyze_button': '🔍 Analyze profile(s)',
        'no_orcid': '⚠️ Enter at least one ORCID',
        'too_many_orcids': '⚠️ Found {count} ORCIDs. This may take a long time...',
        'analysis_complete': '✅ Analysis complete! Found {count} authors in {time:.1f} sec.',
        'best_author': '🏆 Best author: {name} (h-index: {h_index})',
        'single_author': '👤 Author: {name} (h-index: {h_index})',
        'showing_all': '👥 Showing all {count} authors (sorted by h-index)',
        'showing_single': '👤 Showing only the best author',
        'showing_single_only': '👤 Showing single author',
        'no_data': '👈 Load data in "Load Data" tab and click "Analyze profile(s)"',
        'no_data_reports': '👈 First run analysis in "Load Data" tab',
        'retraction_warning': '⚠️ ATTENTION: This author has {count} retracted publication(s).',
        'html_report': '📄 HTML Report Generation',
        'download_report': '💾 Download HTML Report',
        'report_preview': '📋 HTML Report Preview',
        'download_hint': 'Click "Download HTML Report" for full report',
        'generating_report': 'Generating HTML report...',
        'publications': 'Publications',
        'citations': 'Citations',
        'h_index': 'h-index',
        'g_index': 'g-index',
        'i10_index': 'i10-index',
        'i100_index': 'i100-index',
        'total_citations': 'Total citations',
        'avg_citations': 'Average citations',
        'median_citations': 'Median citations',
        'max_citations': 'Max citations',
        'open_access': 'Open Access',
        'active_years': 'Active years',
        'risk_flags': 'Risk flags',
        'collaborations': '🌍 Collaboration Analysis',
        'domestic': '🇷🇺 Domestic collaborations',
        'international': '🌐 International collaborations',
        'papers': 'Papers',
        'no_data_collab': 'No data',
        'collab_index': 'Collaboration index: {index:.2f}',
        'country_diversity': 'Country diversity: {count} countries',
        'most_collaborative': 'Most collaborative country: {country}',
        'top_coauthors': '🤝 Top co-authors',
        'joint_works': 'joint works',
        'publications_list': '📚 Publication list',
        'showing_limited': 'Showing {shown} of {total} publications',
        'title': 'Title',
        'year': 'Year',
        'journal': 'Journal',
        'doi': 'DOI',
        'no_publications': 'No publications',
        'orcid': 'ORCID',
        'affiliations': 'Affiliations',
        'countries': 'Countries',
        'total_analyzed': 'Total analyzed publications',
        'retractions': 'Retractions',
        'corrections': 'Corrections',
        'first_publication': 'First publication',
        'last_publication': 'Last publication',
        'papers_per_year': 'Papers per year',
        'trend': 'Trend',
        'unique_coauthors': 'Unique co-authors',
        'avg_authors_per_paper': 'Average authors per paper',
        'thematic_diversity': 'Thematic diversity (Shannon)',
        'domestic_ratio': 'Domestic collaboration ratio',
        'international_ratio': 'International collaboration ratio',
        'years_chart_title': 'Publication activity dynamics',
        'journals_chart_title': 'Top journals by publications',
        'oa_chart_title': 'Open access status',
        'publishers_chart_title': 'Distribution by publishers',
        'affiliations_chart_title': 'Top affiliations',
        'citations_chart_title': 'Most cited articles',
        'citation_distribution_title': 'Citation distribution',
        'thematic_structure_title': 'Thematic structure of research',
        'wordcloud_title': 'Key research concepts',
        'radar_title': 'Thematic profile (Radar Chart)',
        'concepts': 'Concepts',
        'fields': 'Fields',
        'domains': 'Domains',
        'topics': 'Topics',
        'subtopics': 'Subtopics',
        'year': 'Year',
        'publication_year': 'Publication year',
        'number': 'Number',
        'citation_range': 'Citation range',
        'articles': 'Articles',
        'x_label_pubs': 'Number of publications',
        'y_label_pubs': 'Number of publications',
        'trend_label': 'Trend',
        'confidence_interval': 'Confidence interval',
        'footer': '© Author Profile Analysis / Created by daM / Chimica Techno Acta',
        'journal_url': 'https://chimicatechnoacta.ru',
        'no_profile_data': 'No profile data available',
        'enter_orcid': 'Enter ORCID to analyze',
        'analyze_multiple': 'Analyze multiple authors',
        'profile_analysis': 'Comprehensive scholar profile analysis by ORCID',
        'select_language': 'Select language',
        'theme_presets_label': 'Theme presets',
        'primary_color_label': 'Primary color',
        'secondary_color_label': 'Secondary color',
        'analysis_progress': 'Analysis progress',
        'loading_data': 'Loading data',
        'analyzing_data': 'Analyzing data',
        'generating_viz': 'Generating visualizations',
        'orcid_format_error': 'Invalid ORCID format',
        'data_not_found': 'Data not found. Check ORCID correctness.',
        'error_occurred': 'Error occurred',
        'retracted_publications': 'retracted publications',
        'possible_unethical': 'Possible unethical practices detected!',
        'analyzing_authors': 'Analyzing {count} author(s)...',
        'starting_analysis': 'Starting analysis...',
        'fetching_data': 'Fetching data',
        'analysis_complete_text': 'Analysis complete',
        'creating_charts': 'Creating charts',
        'retractions_in_profile': 'retractions in profile',
        'source_types': '📚 Sources by Type',
        'source_journal_articles': 'Journal articles',
        'source_repositories': 'Preprints/Repositories',
        'source_ebooks': 'Electronic books',
        'source_proceedings': 'Proceedings',
        'source_other': 'Other items (non-DOI)',
        'source_count': 'Count',
        'source_examples': 'Examples',
        'source_no_doi': 'No DOI available',
        'source_view_link': 'View',
        'source_doi_available': 'DOI available',
        'source_no_link': 'No link available',
        'coauthor_orcid': 'ORCID',
        'coauthor_scopus': 'Scopus',
        'coauthor_researcherid': 'ResearcherID',
        'coauthor_website': 'Personal website',
        'coauthor_other': 'Other profiles',
        'no_orcid_found': 'No ORCID found',
        'coauthor_info': 'Co-author information',
        'coauthor_profiles': 'External profiles',
        'main_metrics': 'Main Metrics',
        'citations_per_year': 'Citations/year'
    },
    'ru': {
        'app_title': 'Анализ профиля ученого',
        'app_icon': '🔬',
        'settings': '⚙️ Настройки',
        'language': '🌐 Язык',
        'language_en': 'Английский',
        'language_ru': 'Русский',
        'color_theme': '🎨 Цветовая тема',
        'preset_themes': '🎨 Пресеты тем',
        'use_preset': 'Использовать пресет',
        'select_color': '🎨 Выберите основной цвет',
        'primary': 'Основной',
        'secondary': 'Дополнительный',
        'analysis_params': '📊 Параметры анализа',
        'use_cache': '💾 Использовать кэш',
        'clear_cache': '🗑️ Очистить кэш',
        'cache_cleared': '✅ Кэш очищен!',
        'load_data': '📥 Загрузка данных',
        'profile': '📊 Профиль ученого',
        'reports': '📄 Отчеты',
        'orcid_input': 'ORCID автора(ов)',
        'orcid_placeholder': '0000-0002-1234-567X\n0000-0002-5678-9012\nили: 0000-0002-1234-567X, 0000-0002-5678-9012\nили: https://orcid.org/0000-0002-1234-567X',
        'orcid_help': 'Введите один или несколько ORCID. Разделители: запятая, пробел, новая строка',
        'upload_logo': 'Загрузить логотип журнала (опционально)',
        'logo_help': 'Логотип будет отображаться в отчетах',
        'show_all_authors': '👥 Показать всех соавторов',
        'show_all_help': 'При включении показывает информацию о всех авторах, отсортированных по h-index',
        'analyze_button': '🔍 Анализировать профиль(и)',
        'no_orcid': '⚠️ Введите хотя бы один ORCID',
        'too_many_orcids': '⚠️ Найдено {count} ORCID. Это может занять много времени...',
        'analysis_complete': '✅ Анализ завершен! Найдено {count} авторов за {time:.1f} сек.',
        'best_author': '🏆 Лучший автор: {name} (h-index: {h_index})',
        'single_author': '👤 Автор: {name} (h-index: {h_index})',
        'showing_all': '👥 Показаны все {count} авторов (сортировка по h-index)',
        'showing_single': '👤 Показан только лучший автор',
        'showing_single_only': '👤 Показан единственный автор',
        'no_data': '👈 Загрузите данные на вкладке "Загрузка данных" и нажмите "Анализировать профиль(и)"',
        'no_data_reports': '👈 Сначала выполните анализ на вкладке "Загрузка данных"',
        'retraction_warning': '⚠️ ВНИМАНИЕ: У автора {count} ретрагированных публикаций.',
        'html_report': '📄 Генерация HTML отчета',
        'download_report': '💾 Скачать HTML отчет',
        'report_preview': '📋 Предпросмотр HTML отчета',
        'download_hint': 'Нажмите "Скачать HTML отчет" для полного отчета',
        'generating_report': 'Генерация HTML отчета...',
        'publications': 'Публикаций',
        'citations': 'Цитирований',
        'h_index': 'h-index',
        'g_index': 'g-index',
        'i10_index': 'i10-index',
        'i100_index': 'i100-index',
        'total_citations': 'Всего цитирований',
        'avg_citations': 'Среднее цитирований',
        'median_citations': 'Медиана цитирований',
        'max_citations': 'Максимум цитирований',
        'open_access': 'Открытый доступ',
        'active_years': 'Активных лет',
        'risk_flags': 'Флаги риска',
        'collaborations': '🌍 Анализ коллабораций',
        'domestic': '🇷🇺 Внутристрановые коллаборации',
        'international': '🌐 Международные коллаборации',
        'papers': 'Статей',
        'no_data_collab': 'Нет данных',
        'collab_index': 'Индекс коллабораций: {index:.2f}',
        'country_diversity': 'Страновое разнообразие: {count} стран',
        'most_collaborative': 'Самая коллаборативная страна: {country}',
        'top_coauthors': '🤝 Топ соавторы',
        'joint_works': 'совместных работ',
        'publications_list': '📚 Список публикаций',
        'showing_limited': 'Показано {shown} из {total} публикаций',
        'title': 'Название',
        'year': 'Год',
        'journal': 'Журнал',
        'doi': 'DOI',
        'no_publications': 'Нет публикаций',
        'orcid': 'ORCID',
        'affiliations': 'Аффилиации',
        'countries': 'Страны',
        'total_analyzed': 'Всего проанализировано публикаций',
        'retractions': 'Ретракций',
        'corrections': 'Коррекций',
        'first_publication': 'Первая публикация',
        'last_publication': 'Последняя публикация',
        'papers_per_year': 'Статей в год',
        'trend': 'Тренд',
        'unique_coauthors': 'Уникальных соавторов',
        'avg_authors_per_paper': 'Среднее авторов на статью',
        'thematic_diversity': 'Тематическое разнообразие (Shannon)',
        'domestic_ratio': 'Доля внутристрановых коллабораций',
        'international_ratio': 'Доля международных коллабораций',
        'years_chart_title': 'Динамика публикационной активности',
        'journals_chart_title': 'Топ журналов по числу публикаций',
        'oa_chart_title': 'Статус открытого доступа',
        'publishers_chart_title': 'Распределение по издательствам',
        'affiliations_chart_title': 'Топ аффилиаций',
        'citations_chart_title': 'Самые цитируемые статьи',
        'citation_distribution_title': 'Распределение статей по числу цитирований',
        'thematic_structure_title': 'Тематическая структура исследований',
        'wordcloud_title': 'Ключевые концепты исследований',
        'radar_title': 'Тематический профиль (Radar Chart)',
        'concepts': 'Концепты',
        'fields': 'Fields',
        'domains': 'Domains',
        'topics': 'Topics',
        'subtopics': 'Subtopics',
        'year': 'Год',
        'publication_year': 'Год публикации',
        'number': 'Число',
        'citation_range': 'Диапазон цитирований',
        'articles': 'Статей',
        'x_label_pubs': 'Число публикаций',
        'y_label_pubs': 'Число публикаций',
        'trend_label': 'Тренд',
        'confidence_interval': 'Доверительный интервал',
        'footer': '© Author Profile Analysis / Created by daM / Chimica Techno Acta',
        'journal_url': 'https://chimicatechnoacta.ru',
        'no_profile_data': 'Нет данных профиля',
        'enter_orcid': 'Введите ORCID для анализа',
        'analyze_multiple': 'Анализировать нескольких авторов',
        'profile_analysis': 'Комплексный анализ профиля ученого по ORCID',
        'select_language': 'Выберите язык',
        'theme_presets_label': 'Пресеты тем',
        'primary_color_label': 'Основной цвет',
        'secondary_color_label': 'Дополнительный цвет',
        'analysis_progress': 'Прогресс анализа',
        'loading_data': 'Загрузка данных',
        'analyzing_data': 'Анализ данных',
        'generating_viz': 'Генерация визуализаций',
        'orcid_format_error': 'Неверный формат ORCID',
        'data_not_found': 'Данные не найдены. Проверьте правильность ORCID.',
        'error_occurred': 'Произошла ошибка',
        'retracted_publications': 'ретрагированных публикаций',
        'possible_unethical': 'Обнаружены возможные неэтичные практики!',
        'analyzing_authors': 'Анализирую {count} авторов...',
        'starting_analysis': 'Начинаем анализ...',
        'fetching_data': 'Получение данных',
        'analysis_complete_text': 'Анализ завершен',
        'creating_charts': 'Создание графиков',
        'retractions_in_profile': 'ретракций в профиле',
        'source_types': '📚 Типы источников',
        'source_journal_articles': 'Статьи в журналах',
        'source_repositories': 'Препринты/Репозитории',
        'source_ebooks': 'Электронные книги',
        'source_proceedings': 'Материалы конференций',
        'source_other': 'Другие материалы (без DOI)',
        'source_count': 'Количество',
        'source_examples': 'Примеры',
        'source_no_doi': 'Нет DOI',
        'source_view_link': 'Смотреть',
        'source_doi_available': 'DOI доступен',
        'source_no_link': 'Нет ссылки',
        'coauthor_orcid': 'ORCID',
        'coauthor_scopus': 'Scopus',
        'coauthor_researcherid': 'ResearcherID',
        'coauthor_website': 'Персональный сайт',
        'coauthor_other': 'Другие профили',
        'no_orcid_found': 'ORCID не найден',
        'coauthor_info': 'Информация о соавторе',
        'coauthor_profiles': 'Внешние профили',
        'main_metrics': 'Основные метрики',
        'citations_per_year': 'Цитирований/год'
    }
}

def translate(key: str, lang: str = 'en', **kwargs) -> str:
    """Get translated string by key and language"""
    if lang not in LANG:
        lang = 'en'
    text = LANG[lang].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

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

        .coauthor-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            border: 1px solid #e0e0e0;
            border-left: 4px solid var(--primary);
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .coauthor-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
            border-color: var(--primary);
        }}
        
        .coauthor-name {{
            font-size: 16px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 6px;
        }}
        
        .coauthor-joint {{
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
        }}
        
        .coauthor-profile-link {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s;
            margin: 2px;
        }}
        
        .coauthor-profile-link:hover {{
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .coauthor-profile-link.orcid {{
            background: #a6ce39;
            color: #1a1a1a;
        }}
        
        .coauthor-profile-link.orcid:hover {{
            background: #8cb82e;
        }}
        
        .coauthor-profile-link.website {{
            background: #6c757d;
            color: white;
        }}
        
        .coauthor-profile-link.website:hover {{
            background: #5a6268;
        }}
        
        .coauthor-profile-link.other {{
            background: #17a2b8;
            color: white;
        }}
        
        .coauthor-profile-link.other:hover {{
            background: #138496;
        }}
        
        .coauthor-no-orcid {{
            font-size: 12px;
            color: #999;
            font-style: italic;
        }}
        
        .no-links {{
            color: #999;
            font-style: italic;
            margin: 5px 0;
            font-size: 12px;
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
        
        /* Source types table styles */
        .source-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-family: 'Times New Roman', serif;
        }}
        .source-table th {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .source-table td {{
            padding: 10px;
            border-bottom: 1px solid #BDC3C7;
            vertical-align: top;
        }}
        .source-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .source-example-item {{
            margin: 3px 0;
            font-size: 13px;
        }}
        .source-example-link {{
            color: #2980B9;
            text-decoration: none;
            font-size: 12px;
        }}
        .source-example-link:hover {{
            text-decoration: underline;
        }}
        .source-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 5px;
        }}
        .source-badge-doi {{
            background: #d4edda;
            color: #155724;
        }}
        .source-badge-nodoi {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        /* Co-author card styles */
        .coauthor-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            border: 1px solid #e0e0e0;
            border-left: 4px solid var(--primary);
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .coauthor-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
            border-color: var(--primary);
        }}
        
        .coauthor-name {{
            font-size: 16px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 6px;
        }}
        
        .coauthor-joint {{
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
        }}
        
        .coauthor-profiles {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }}
        
        .coauthor-profile-link {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s;
            background: #f0f0f0;
            color: #333;
        }}
        
        .coauthor-profile-link:hover {{
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .coauthor-profile-link.orcid {{
            background: #a6ce39;
            color: #1a1a1a;
        }}
        
        .coauthor-profile-link.orcid:hover {{
            background: #8cb82e;
        }}
        
        .coauthor-profile-link.scopus {{
            background: #e97132;
            color: white;
        }}
        
        .coauthor-profile-link.scopus:hover {{
            background: #d45f24;
        }}
        
        .coauthor-profile-link.researcherid {{
            background: #005a9c;
            color: white;
        }}
        
        .coauthor-profile-link.researcherid:hover {{
            background: #004a82;
        }}
        
        .coauthor-profile-link.website {{
            background: #6c757d;
            color: white;
        }}
        
        .coauthor-profile-link.website:hover {{
            background: #5a6268;
        }}
        
        .coauthor-profile-link.other {{
            background: #17a2b8;
            color: white;
        }}
        
        .coauthor-profile-link.other:hover {{
            background: #138496;
        }}
        
        .coauthor-no-orcid {{
            font-size: 12px;
            color: #999;
            font-style: italic;
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
# ДОПОЛНИТЕЛЬНЫЕ СЛОВАРИ И УТИЛИТЫ
# ============================================

# Словарь для преобразования кодов стран в полные названия
COUNTRY_CODE_TO_NAME = {
    'GR': 'Greece',
    'CN': 'China',
    'PT': 'Portugal',
    'BY': 'Belarus',
    'PL': 'Poland',
    'SK': 'Slovakia',
    'SA': 'Saudi Arabia',
    'US': 'United States',
    'AU': 'Australia',
    'PK': 'Pakistan',
    'GB': 'United Kingdom',
    'HK': 'Hong Kong',
    'DE': 'Germany',
    'NO': 'Norway',
    'FR': 'France',
    'IN': 'India',
    'KR': 'South Korea',
    'RU': 'Russia',
    'UA': 'Ukraine',
    'IT': 'Italy',
    'ES': 'Spain',
    'NL': 'Netherlands',
    'CH': 'Switzerland',
    'SE': 'Sweden',
    'BE': 'Belgium',
    'AT': 'Austria',
    'DK': 'Denmark',
    'FI': 'Finland',
    'IE': 'Ireland',
    'NZ': 'New Zealand',
    'ZA': 'South Africa',
    'AR': 'Argentina',
    'MX': 'Mexico',
    'CL': 'Chile',
    'CO': 'Colombia',
    'BR': 'Brazil',
    'JP': 'Japan',
    'SG': 'Singapore',
    'TW': 'Taiwan',
    'IL': 'Israel',
    'TR': 'Turkey',
    'EG': 'Egypt',
    'NG': 'Nigeria',
    'KE': 'Kenya',
}

def get_full_country_name(country_code: str) -> str:
    """Преобразует код страны в полное название"""
    if not country_code:
        return 'Unknown'
    
    # Если уже полное название (длиннее 2 символов), возвращаем как есть
    if len(country_code) > 3:
        return country_code
    
    return COUNTRY_CODE_TO_NAME.get(country_code.upper(), country_code)

def is_author_affiliation(affiliation_name: str, author_affiliations: List[str]) -> bool:
    """Проверяет, является ли аффилиация аффилиацией самого ученого"""
    if not affiliation_name or not author_affiliations:
        return False
    
    # Нормализуем для сравнения (убираем лишние пробелы, приводим к нижнему регистру)
    aff_normalized = affiliation_name.strip().lower()
    
    for author_aff in author_affiliations:
        if not author_aff:
            continue
        author_aff_normalized = author_aff.strip().lower()
        # Проверяем полное совпадение или вхождение (если одна аффилиация является частью другой)
        if aff_normalized == author_aff_normalized:
            return True
        # Проверяем, не является ли аффилиация подразделением основной аффилиации
        if aff_normalized in author_aff_normalized or author_aff_normalized in aff_normalized:
            # Если одно название полностью содержит другое, считаем что это та же организация
            # но только если длина разницы не слишком большая (чтобы не перепутать разные организации)
            if len(aff_normalized) > 10 and len(author_aff_normalized) > 10:
                return True
    
    return False

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
# ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ КАТЕГОРИИ ИСТОЧНИКА
# ============================================

def determine_source_category(pub_data: Dict) -> str:
    """
    Определяет категорию источника публикации на основе полей OpenAlex.
    Возвращает одну из: 'articles', 'repositories', 'ebooks', 'proceedings', 'other'
    """
    source_type = pub_data.get('source_type', 'unknown')
    raw_type = pub_data.get('raw_type', '')
    pub_type = pub_data.get('type', '')
    
    # Приоритет: raw_type > source.type > type
    
    # Проверяем raw_type
    if raw_type:
        raw_lower = raw_type.lower()
        if 'journal-article' in raw_lower or 'journal article' in raw_lower:
            return 'articles'
        if 'posted-content' in raw_lower or 'preprint' in raw_lower:
            return 'repositories'
        if 'book-chapter' in raw_lower or 'book chapter' in raw_lower:
            return 'ebooks'
        if 'proceedings-article' in raw_lower or 'proceedings article' in raw_lower:
            return 'proceedings'
    
    # Проверяем source.type
    if source_type:
        source_lower = source_type.lower()
        if 'journal' in source_lower:
            return 'articles'
        if 'repository' in source_lower:
            return 'repositories'
        if 'ebook platform' in source_lower or 'ebook' in source_lower:
            return 'ebooks'
    
    # Проверяем pub_type
    if pub_type:
        pub_lower = pub_type.lower()
        if 'article' in pub_lower and 'journal' not in pub_lower:
            # Если просто article, но не journal-article - проверяем контекст
            pass
        if 'book-chapter' in pub_lower:
            return 'ebooks'
        if 'proceedings' in pub_lower:
            return 'proceedings'
    
    # Если ничего не подошло - определяем по наличию DOI
    if pub_data.get('doi'):
        # Есть DOI, но тип не определен - считаем статьей
        return 'articles'
    else:
        return 'other'

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
        pub['raw_type'] = item.get('raw_type', '')
        
        if item.get('primary_location'):
            source = item['primary_location'].get('source', {})
            pub['journal_name'] = source.get('display_name', 'Unknown')
            pub['publisher'] = source.get('host_organization_name') or source.get('publisher', 'Unknown')
            pub['issn'] = source.get('issn', [])
            pub['source_type'] = source.get('type', 'unknown')
        else:
            pub['journal_name'] = 'Unknown'
            pub['publisher'] = 'Unknown'
            pub['issn'] = []
            pub['source_type'] = 'unknown'
        
        oa = item.get('open_access', {})
        pub['is_oa'] = oa.get('is_oa', False)
        pub['open_access_status'] = oa.get('oa_status', 'closed')
        pub['oa_url'] = oa.get('oa_url', None)
        pub['any_repository_has_fulltext'] = oa.get('any_repository_has_fulltext', False)
        
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
        
        # ====== ИЗМЕНЕНИЕ: Сбор информации об авторах с ORCID ======
        authors = []
        author_orcids = []
        authors_with_orcids = []  # Новое поле для хранения пар имя-ORCID
        
        for auth in item.get('authorships', []):
            if auth.get('author'):
                author_name = auth['author'].get('display_name', '')
                author_orcid = auth['author'].get('orcid', '')
                if author_name:
                    authors.append(author_name)
                    if author_orcid:
                        author_orcids.append(author_orcid)
                    # Сохраняем пару имя-ORCID
                    authors_with_orcids.append({
                        'name': author_name,
                        'orcid': author_orcid.replace('https://orcid.org/', '') if author_orcid else None
                    })
        
        pub['authors'] = authors
        pub['author_orcids'] = author_orcids
        pub['authors_with_orcids'] = authors_with_orcids  # Новое поле
        
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
        
        # Определяем категорию источника
        pub['source_category'] = determine_source_category(pub)
        
        return pub
        
    except Exception as e:
        if SHOW_DEBUG_LOGS:
            print(f"⚠️ Ошибка парсинга публикации: {e}")
        return None

# ============================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ДАННЫХ ИЗ API# ============================================

async def get_orcid_dois(orcid: str, session) -> Set[str]:
    """
    Получает список DOI из профиля ORCID и OpenAlex API.
    Объединяет результаты из обоих источников для максимальной полноты данных.
    
    Args:
        orcid: ORCID идентификатор
        session: aiohttp сессия
        
    Returns:
        Set[str]: Множество уникальных DOI
    """
    orcid = clean_orcid(orcid)
    
    if not orcid:
        return set()
    
    all_dois = set()
    
    # ============================================================
    # ЧАСТЬ 1: Получение DOI из ORCID API (существующая логика)
    # ============================================================
    if SHOW_DEBUG_LOGS:
        print(f"🔍 Запрос к ORCID API: {orcid}")
    
    headers = {'Accept': 'application/json'}
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    
    data = await fetch_with_retry(session, url, headers=headers)
    
    if data:
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
                                    all_dois.add(doi)
            
            if SHOW_DEBUG_LOGS:
                print(f"✅ Из ORCID API получено {len(all_dois)} DOI")
                
        except Exception as e:
            if SHOW_DEBUG_LOGS:
                print(f"⚠️ Ошибка парсинга ORCID API: {e}")
    
    # ============================================================
    # ЧАСТЬ 2: Получение DOI из OpenAlex API (НОВАЯ ЛОГИКА)
    # ============================================================
    if SHOW_DEBUG_LOGS:
        print(f"🔍 Запрос к OpenAlex API для ORCID: {orcid}")
    
    openalex_dois = set()
    openalex_works_count = 0
    
    # Формируем URL для поиска работ по ORCID автора
    # Используем фильтр author.orcid и запрашиваем до 200 записей на страницу
    base_url = "https://api.openalex.org/works"
    params = {
        'filter': f'author.orcid:{orcid}',
        'per-page': 200
    }
    
    try:
        next_page_url = None
        page_count = 0
        
        while True:
            page_count += 1
            
            if next_page_url:
                # Используем URL следующей страницы
                data = await fetch_with_retry(session, next_page_url, method='GET')
            else:
                # Первый запрос с параметрами
                data = await fetch_with_retry(session, base_url, params=params)
            
            if not data:
                if SHOW_DEBUG_LOGS:
                    print(f"⚠️ OpenAlex API не вернул данные для страницы {page_count}")
                break
            
            # Получаем результаты
            results = data.get('results', [])
            
            if not results:
                if SHOW_DEBUG_LOGS:
                    print(f"ℹ️ OpenAlex API: страница {page_count} не содержит результатов")
                break
            
            # Извлекаем DOI из результатов
            for work in results:
                if 'doi' in work and work['doi']:
                    # Очищаем DOI от префикса https://doi.org/
                    doi = work['doi'].replace('https://doi.org/', '').lower()
                    if doi:
                        openalex_dois.add(doi)
                        openalex_works_count += 1
            
            if SHOW_DEBUG_LOGS and page_count % 5 == 0:
                print(f"📄 OpenAlex: обработано {page_count} страниц, найдено {len(openalex_dois)} DOI")
            
            # Проверяем наличие следующей страницы
            # OpenAlex возвращает ссылку на следующую страницу в meta.next_page_url
            meta = data.get('meta', {})
            next_page_url = meta.get('next_page_url')
            
            # Если следующей страницы нет - выходим из цикла
            if not next_page_url:
                if SHOW_DEBUG_LOGS:
                    print(f"✅ OpenAlex: все страницы обработаны (всего {page_count} страниц)")
                break
            
            # Небольшая задержка между запросами страниц для соблюдения лимитов API
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)
        
        # Добавляем DOI из OpenAlex в общий набор
        all_dois.update(openalex_dois)
        
        if SHOW_DEBUG_LOGS:
            print(f"✅ Из OpenAlex API получено {len(openalex_dois)} уникальных DOI (всего обработано {openalex_works_count} работ)")
            
    except Exception as e:
        if SHOW_DEBUG_LOGS:
            print(f"⚠️ Ошибка при запросе к OpenAlex API: {e}")
    
    # ============================================================
    # ИТОГОВЫЙ РЕЗУЛЬТАТ
    # ============================================================
    if SHOW_DEBUG_LOGS:
        print(f"📊 ИТОГО: {len(all_dois)} уникальных DOI (ORCID API + OpenAlex API)")
    
    return all_dois

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
# НОВАЯ ФУНКЦИЯ: Получение информации о персональных профилях из ORCID API
# ============================================

async def get_orcid_person_info(orcid: str, session) -> Dict:
    """
    Получает информацию о персональных профилях из API ORCID.
    Возвращает структурированный список ссылок из разделов:
    - Websites & Social Links (researcher-urls)
    - Other IDs (external-identifiers)
    """
    if not orcid:
        return {}
    
    orcid_clean = clean_orcid(orcid)
    if not orcid_clean:
        return {}
    
    headers = {'Accept': 'application/json'}
    url = f"https://pub.orcid.org/v3.0/{orcid_clean}/person"
    
    if SHOW_DEBUG_LOGS:
        print(f"🔍 Запрос персональной информации для ORCID: {orcid_clean}")
    
    try:
        data = await fetch_with_retry(session, url, headers=headers)
        
        if not data:
            if SHOW_DEBUG_LOGS:
                print(f"⚠️ Не удалось получить персональные данные для {orcid_clean}")
            return {}
        
        links = []
        
        # 1. Websites & Social Links → researcher-urls
        researcher_urls = data.get('researcher-urls', {}).get('researcher-url', [])
        if not isinstance(researcher_urls, list):
            researcher_urls = [researcher_urls] if researcher_urls else []
        
        if SHOW_DEBUG_LOGS:
            print(f"  Найдено researcher-urls: {len(researcher_urls)}")
        
        for item in researcher_urls:
            name = item.get('url-name') or 'Personal website'
            url_value = item.get('url', {}).get('value')
            if url_value:
                links.append({
                    'type': 'Websites & Social Links',
                    'name': name,
                    'url': url_value
                })
                if SHOW_DEBUG_LOGS:
                    print(f"    - Website: {name} -> {url_value}")
        
        # 2. Other IDs → external-identifiers
        external_ids = data.get('external-identifiers', {}).get('external-identifier', [])
        if not isinstance(external_ids, list):
            external_ids = [external_ids] if external_ids else []
        
        if SHOW_DEBUG_LOGS:
            print(f"  Найдено external-identifiers: {len(external_ids)}")
        
        for item in external_ids:
            id_type = item.get('external-id-type', 'Other ID')
            id_value = item.get('external-id-value', '')
            id_url = item.get('external-id-url', {}).get('value')
            
            if id_url:
                links.append({
                    'type': 'Other IDs',
                    'name': f"{id_type}: {id_value}",
                    'url': id_url
                })
                if SHOW_DEBUG_LOGS:
                    print(f"    - Other ID: {id_type}: {id_value} -> {id_url}")
            elif id_value:
                # Если нет прямой ссылки, но есть значение
                links.append({
                    'type': 'Other IDs',
                    'name': f"{id_type}: {id_value}",
                    'url': None
                })
                if SHOW_DEBUG_LOGS:
                    print(f"    - Other ID (no URL): {id_type}: {id_value}")
        
        if SHOW_DEBUG_LOGS:
            print(f"  Итого ссылок: {len(links)}")
        
        return {'links': links}
        
    except Exception as e:
        if SHOW_DEBUG_LOGS:
            print(f"⚠️ Ошибка получения персональной информации: {e}")
            import traceback
            traceback.print_exc()
        return {}

def generate_coauthor_links_html(links: List[Dict], lang: str = 'en') -> str:
    """
    Генерирует HTML таблицу для отображения ссылок соавтора.
    Структурирует ссылки по типам: Websites & Social Links и Other IDs.
    """
    if not links:
        return '<p class="no-links">No additional links found</p>'
    
    def t(key: str, **kwargs) -> str:
        return translate(key, lang, **kwargs)
    
    # Группируем ссылки по типам
    websites_links = []
    other_links = []
    
    for link in links:
        if link.get('type') == 'Websites & Social Links':
            websites_links.append(link)
        else:
            other_links.append(link)
    
    html = ""
    
    # Секция Websites & Social Links
    if websites_links:
        html += """
        <div style="margin-top: 8px; margin-bottom: 8px;">
            <div style="font-weight: 600; font-size: 12px; color: #555; margin-bottom: 4px;">🌐 Websites & Social Links:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        """
        
        for link in websites_links:
            link_name = link.get('name', 'Website')
            link_url = link.get('url')
            
            if link_url:
                # Определяем иконку на основе названия
                icon = "🌐"
                name_lower = link_name.lower()
                if "linkedin" in name_lower:
                    icon = "💼"
                elif "twitter" in name_lower or "x.com" in name_lower:
                    icon = "🐦"
                elif "facebook" in name_lower:
                    icon = "📘"
                elif "researchgate" in name_lower:
                    icon = "🔬"
                elif "academia" in name_lower:
                    icon = "📖"
                elif "github" in name_lower:
                    icon = "💻"
                elif "scholar" in name_lower:
                    icon = "🎓"
                
                html += f"""
                <a href="{link_url}" target="_blank" class="coauthor-profile-link website" 
                   style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;
                          font-size:11px;font-weight:500;text-decoration:none;background:#6c757d;color:white;
                          transition:all 0.2s;margin:2px;">
                    {icon} {html.escape(link_name[:30])}
                </a>
                """
            else:
                html += f"""
                <span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;
                             font-size:11px;font-weight:500;background:#e9ecef;color:#666;margin:2px;">
                    {html.escape(link_name[:30])} (no link)
                </span>
                """
        
        html += """
            </div>
        </div>
        """
    
    # Секция Other IDs
    if other_links:
        html += """
        <div style="margin-top: 8px;">
            <div style="font-weight: 600; font-size: 12px; color: #555; margin-bottom: 4px;">🔗 Other IDs:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        """
        
        for link in other_links:
            link_name = link.get('name', 'Other ID')
            link_url = link.get('url')
            
            # Определяем цвет для разных типов ID
            bg_color = "#17a2b8"  # default
            name_lower = link_name.lower()
            
            if "scopus" in name_lower:
                bg_color = "#e97132"
                icon = "📚"
            elif "researcherid" in name_lower or "researcher id" in name_lower:
                bg_color = "#005a9c"
                icon = "🆔"
            elif "orcid" in name_lower:
                bg_color = "#a6ce39"
                icon = "🆔"
            elif "linkedin" in name_lower:
                bg_color = "#0077b5"
                icon = "💼"
            elif "twitter" in name_lower:
                bg_color = "#1da1f2"
                icon = "🐦"
            elif "facebook" in name_lower:
                bg_color = "#1877f2"
                icon = "📘"
            elif "researchgate" in name_lower:
                bg_color = "#00ccbb"
                icon = "🔬"
            elif "academia" in name_lower:
                bg_color = "#8a2be2"
                icon = "📖"
            elif "mendeley" in name_lower:
                bg_color = "#9d1620"
                icon = "📑"
            elif "publons" in name_lower:
                bg_color = "#2a7de1"
                icon = "📝"
            elif "loop" in name_lower:
                bg_color = "#ff6b6b"
                icon = "🔄"
            elif "github" in name_lower:
                bg_color = "#333333"
                icon = "💻"
            else:
                icon = "🔗"
            
            if link_url:
                html += f"""
                <a href="{link_url}" target="_blank" class="coauthor-profile-link other" 
                   style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;
                          font-size:11px;font-weight:500;text-decoration:none;background:{bg_color};color:white;
                          transition:all 0.2s;margin:2px;">
                    {icon} {html.escape(link_name[:40])}
                </a>
                """
            else:
                html += f"""
                <span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;
                             font-size:11px;font-weight:500;background:#e9ecef;color:#666;margin:2px;">
                    {icon} {html.escape(link_name[:40])} (no link)
                </span>
                """
        
        html += """
            </div>
        </div>
        """
    
    if not html:
        html = '<p class="no-links">No additional links found</p>'
    
    return html


def _build_external_id_url(ext_type: str, ext_value: str) -> str:
    """Строит URL для внешнего идентификатора на основе типа"""
    ext_type_lower = ext_type.lower()
    
    # Карта типов идентификаторов и соответствующих URL
    url_templates = {
        'scopus': f"https://www.scopus.com/authid/detail.uri?authorId={ext_value}",
        'researcherid': f"https://www.researcherid.com/rid/{ext_value}",
        'orcid': f"https://orcid.org/{ext_value}",
        'linkedin': f"https://www.linkedin.com/in/{ext_value}",
        'twitter': f"https://twitter.com/{ext_value}",
        'facebook': f"https://www.facebook.com/{ext_value}",
        'researchgate': f"https://www.researchgate.net/profile/{ext_value}",
        'academia': f"https://independent.academia.edu/{ext_value}",
        'mendeley': f"https://www.mendeley.com/profiles/{ext_value}/",
        'publons': f"https://publons.com/researcher/{ext_value}/",
        'loop': f"https://loop.frontiersin.org/people/{ext_value}/",
        'impactstory': f"https://impactstory.org/u/{ext_value}",
        'google-scholar': f"https://scholar.google.com/citations?user={ext_value}",
        'github': f"https://github.com/{ext_value}",
        'orcid': f"https://orcid.org/{ext_value}"
    }
    
    # Ищем совпадение по частичному вхождению
    for key, url_template in url_templates.items():
        if key in ext_type_lower or ext_type_lower in key:
            return url_template
    
    # Если шаблон не найден, возвращаем пустую строку
    return ""

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
        self.coauthors_with_orcids = {}  # Новое поле: словарь {имя: {'count': N, 'orcid': ORCID}}
        self.coauthor_profiles = {}  # Новое поле: словарь {orcid: профиль}
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
    
    def _analyze_collaborations(self):
        """Анализирует коллаборации с детальным разбором по аффилиациям (задача 1 и 4)"""
        if not self.publications:
            return
        
        # Получаем страны автора из различных источников
        author_countries_set = set(self.author_countries) if self.author_countries else set()
        
        # Если страны не определены, пытаемся извлечь из публикаций
        if not author_countries_set:
            for p in self.publications:
                if p.get('country') and p['country'] != 'Unknown':
                    author_countries_set.add(p['country'])
        
        # Если все еще пусто, используем страны из аффилиаций в публикациях
        if not author_countries_set:
            for p in self.publications:
                for aff in p.get('affiliation_countries', []):
                    if aff and aff != 'Unknown':
                        author_countries_set.add(aff)
        
        # Если ничего не найдено, считаем что автор из 'Unknown'
        if not author_countries_set:
            author_countries_set = {'Unknown'}
        
        # Получаем аффилиации автора для исключения их из коллабораций
        author_affiliations_set = set(self.author_affiliations) if self.author_affiliations else set()
        
        # Если аффилиации не определены, пытаемся извлечь из публикаций
        if not author_affiliations_set:
            for p in self.publications:
                for aff in p.get('affiliations', []):
                    if aff and aff not in author_affiliations_set:
                        author_affiliations_set.add(aff)
        
        self.collaborations = {
            'domestic': defaultdict(lambda: defaultdict(int)),
            'international': defaultdict(lambda: defaultdict(int)),
            'domestic_papers': 0,
            'international_papers': 0,
            'total_collaborations': 0
        }
        
        domestic_papers = 0
        international_papers = 0
        
        for p in self.publications:
            institutions = p.get('institutions', [])
            if not institutions:
                continue
            
            paper_countries = set()
            paper_affiliations = set()
            
            # Собираем уникальные страны и аффилиации из публикации
            for inst in institutions:
                country = inst.get('country_code', '')
                if country:
                    paper_countries.add(country)
                affil_name = inst.get('display_name', '')
                if affil_name:
                    paper_affiliations.add(affil_name)
            
            # Фильтруем пустые и неизвестные страны
            paper_countries = {c for c in paper_countries if c and c != 'Unknown'}
            
            # Если в публикации нет стран, пропускаем её (не можем определить тип коллаборации)
            if not paper_countries:
                continue
            
            # ====== ЛОГИКА ПО СТРАНАМ (как в mixed версии) ======
            # Определяем, есть ли в публикации страны автора
            has_author_country = any(c in author_countries_set for c in paper_countries)
            has_other_countries = any(c not in author_countries_set for c in paper_countries)
            
            # Специальный случай: если author_countries_set содержит только 'Unknown'
            if author_countries_set == {'Unknown'}:
                # Все коллаборации считаем международными
                international_papers += 1
                # Добавляем уникальные аффилиации
                for affil_name in paper_affiliations:
                    if affil_name and affil_name not in author_affiliations_set:
                        country_name = 'Unknown'
                        for inst in institutions:
                            if inst.get('display_name', '') == affil_name:
                                country = inst.get('country_code', '')
                                country_name = get_full_country_name(country) if country else 'Unknown'
                                break
                        self.collaborations['international'][country_name][affil_name] += 1
            else:
                if has_author_country and not has_other_countries:
                    # Только страны автора - внутристрановые
                    domestic_papers += 1
                    # Добавляем уникальные аффилиации
                    for affil_name in paper_affiliations:
                        if affil_name and affil_name not in author_affiliations_set:
                            country_name = 'Unknown'
                            for inst in institutions:
                                if inst.get('display_name', '') == affil_name:
                                    country = inst.get('country_code', '')
                                    if country in author_countries_set:
                                        country_name = get_full_country_name(country) if country else 'Unknown'
                                        break
                            if country_name != 'Unknown':
                                self.collaborations['domestic'][country_name][affil_name] += 1
                            
                elif has_author_country and has_other_countries:
                    # Есть и страны автора, и другие страны - международные
                    international_papers += 1
                    # Добавляем уникальные аффилиации
                    for affil_name in paper_affiliations:
                        if affil_name and affil_name not in author_affiliations_set:
                            country_name = 'Unknown'
                            for inst in institutions:
                                if inst.get('display_name', '') == affil_name:
                                    country = inst.get('country_code', '')
                                    country_name = get_full_country_name(country) if country else 'Unknown'
                                    break
                            if country_name != 'Unknown':
                                # Определяем domestic или international по стране
                                author_country_names = {get_full_country_name(c) for c in author_countries_set if c and c != 'Unknown'}
                                if country_name in author_country_names:
                                    self.collaborations['domestic'][country_name][affil_name] += 1
                                else:
                                    self.collaborations['international'][country_name][affil_name] += 1
                                    
                elif has_other_countries and not has_author_country:
                    # Только другие страны - международные
                    international_papers += 1
                    # Добавляем уникальные аффилиации
                    for affil_name in paper_affiliations:
                        if affil_name and affil_name not in author_affiliations_set:
                            country_name = 'Unknown'
                            for inst in institutions:
                                if inst.get('display_name', '') == affil_name:
                                    country = inst.get('country_code', '')
                                    country_name = get_full_country_name(country) if country else 'Unknown'
                                    break
                            if country_name != 'Unknown':
                                self.collaborations['international'][country_name][affil_name] += 1
        
        self.collaborations['domestic_papers'] = domestic_papers
        self.collaborations['international_papers'] = international_papers
        self.collaborations['total_collaborations'] = domestic_papers + international_papers
        
        self.profile['collaborations'] = self.collaborations
        
        # Рассчитываем проценты от общего числа публикаций
        total_pubs = len(self.publications)
        if total_pubs > 0:
            self.profile['domestic_papers_ratio'] = domestic_papers / total_pubs
            self.profile['international_papers_ratio'] = international_papers / total_pubs
        else:
            self.profile['domestic_papers_ratio'] = 0
            self.profile['international_papers_ratio'] = 0
        
        # Индекс коллабораций
        self.profile['collaboration_index'] = self.profile.get('avg_authors_per_paper', 0) - 1 if self.profile.get('avg_authors_per_paper', 0) > 0 else 0
        
        # Подсчет коллабораций по странам
        all_collab = {}
        for country, affils in self.collaborations['international'].items():
            total = sum(affils.values())
            all_collab[country] = all_collab.get(country, 0) + total
        
        for country, affils in self.collaborations['domestic'].items():
            total = sum(affils.values())
            all_collab[country] = all_collab.get(country, 0) + total
        
        # Самая коллаборативная страна
        if all_collab:
            author_country_names = {get_full_country_name(c) for c in author_countries_set if c and c != 'Unknown'}
            filtered_collab = {k: v for k, v in all_collab.items() if k not in author_country_names}
            if filtered_collab:
                self.profile['most_collaborative_country'] = max(filtered_collab.items(), key=lambda x: x[1])[0]
            else:
                self.profile['most_collaborative_country'] = 'None'
        else:
            self.profile['most_collaborative_country'] = 'None'
        
        # Страновое разнообразие
        all_countries = set(author_countries_set) | set(all_collab.keys())
        self.profile['country_diversity'] = len(all_countries)
        
        # ====== ФИЛЬТРАЦИЯ: Удаляем аффилиации автора из коллабораций ======
        author_affils_final = set(self.author_affiliations) if self.author_affiliations else set()
        
        # Фильтруем domestic коллаборации
        for country in list(self.collaborations['domestic'].keys()):
            affils_dict = self.collaborations['domestic'][country]
            for affil in list(affils_dict.keys()):
                if affil in author_affils_final:
                    del affils_dict[affil]
            if not affils_dict:
                del self.collaborations['domestic'][country]
        
        # Фильтруем international коллаборации
        for country in list(self.collaborations['international'].keys()):
            affils_dict = self.collaborations['international'][country]
            for affil in list(affils_dict.keys()):
                if affil in author_affils_final:
                    del affils_dict[affil]
            if not affils_dict:
                del self.collaborations['international'][country]
        
        # Обновляем профиль с отфильтрованными данными
        self.profile['collaborations'] = self.collaborations
    
    def _get_retraction_flag(self) -> List[str]:
        """Возвращает флаг только если есть ретракции"""
        retractions = self.profile.get('retractions', 0)
        if retractions > 0:
            return [f"🔴 RETRACTION: {retractions} retracted publication(s)"]
        return []
    
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
        
        # Статистика по типам источников
        source_categories = {}
        
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
            
            # Сбор статистики по типам источников
            category = p.get('source_category', 'other')
            if category not in source_categories:
                source_categories[category] = []
            
            # Сохраняем информацию о публикации для отображения в отчете
            source_categories[category].append({
                'title': p.get('title', 'No title'),
                'doi': p.get('doi', ''),
                'id': p.get('id', ''),
                'year': p.get('publication_year', ''),
                'journal': p.get('journal_name', ''),
                'raw_type': p.get('raw_type', ''),
                'source_type': p.get('source_type', ''),
                'is_oa': p.get('is_oa', False),
                'any_repository_has_fulltext': p.get('any_repository_has_fulltext', False)
            })
        
        # Сохраняем статистику по типам источников
        self.profile['source_categories'] = {
            cat: {
                'count': len(items),
                'items': items[:3]  # Только топ-3 для отображения
            }
            for cat, items in source_categories.items()
        }
        
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
        
        # ====== ИЗМЕНЕНИЕ: Сбор соавторов с ORCID ======
        coauthors = []
        coauthors_with_orcids = defaultdict(lambda: {'count': 0, 'orcid': None})
        
        author_name_normalized = normalize_author_name(self.author_name or '')
        author_orcid = self.orcid
        
        for p in self.publications:
            if p.get('authors_with_orcids'):
                authors_list = p['authors_with_orcids']
                
                for author_data in authors_list:
                    name = author_data.get('name', '')
                    orcid = author_data.get('orcid', '')
                    
                    is_self = False
                    
                    if author_name_normalized:
                        name_normalized = normalize_author_name(name)
                        if name_normalized == author_name_normalized:
                            is_self = True
                    
                    if not is_self and orcid:
                        if orcid == author_orcid or orcid.replace('https://orcid.org/', '') == author_orcid:
                            is_self = True
                    
                    if not is_self and name:
                        coauthors.append(name)
                        if name not in coauthors_with_orcids:
                            coauthors_with_orcids[name] = {'count': 0, 'orcid': None}
                        coauthors_with_orcids[name]['count'] += 1
                        if orcid and not coauthors_with_orcids[name]['orcid']:
                            coauthors_with_orcids[name]['orcid'] = orcid
        
        self.coauthors_with_orcids = dict(coauthors_with_orcids)
        
        self.profile['coauthors'] = dict(Counter(coauthors))
        self.profile['top_coauthors'] = dict(Counter(coauthors).most_common(20))
        self.profile['top_coauthors_with_orcids'] = {
            name: data 
            for name, data in sorted(
                coauthors_with_orcids.items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            )[:20]
        }
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
        
        # ====== ДОБАВЛЕНИЕ: Расчет i100 индекса ======
        self.profile['i100_index'] = sum(1 for c in citations if c >= 100)
        
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
        
        # ====== ДОБАВЛЕНИЕ: Расчет среднегодового цитирования для каждой публикации ======
        current_year = datetime.now().year
        for p in self.publications:
            pub_year = p.get('publication_year')
            if pub_year:
                years_since = current_year - pub_year + 1  # +1 потому что текущий год считается
                citations_count = p.get('cited_by_count', 0)
                p['citations_per_year'] = citations_count / max(years_since, 1)
            else:
                p['citations_per_year'] = 0
        
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
        
        # Добавляем флаг ретракций в профиль (без других предупреждений)
        self.profile['risk_flags'] = self._get_retraction_flag()
        
        print("✅ Анализ завершен!")
    
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
        
        if 'coauthors_with_orcids' in cached_data:
            analyzer.coauthors_with_orcids = cached_data['coauthors_with_orcids']
        
        if 'coauthor_profiles' in cached_data:
            analyzer.coauthor_profiles = cached_data['coauthor_profiles']
            print(f"📊 Загружено профилей соавторов из кэша: {len(analyzer.coauthor_profiles)}")
        
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
        
        # ====== НОВОЕ: Получение персональной информации для соавторов ПАРАЛЛЕЛЬНО ======
        print("🔍 Получение персональной информации для соавторов...")
        coauthor_profiles = {}
        
        # Сначала анализируем публикации, чтобы собрать соавторов
        analyzer.analyze_publications()
        
        # Получаем список уникальных ORCID соавторов
        unique_coauthor_orcids = set()
        for name, data in analyzer.coauthors_with_orcids.items():
            if data.get('orcid'):
                # Очищаем ORCID от префикса https://orcid.org/
                orcid_clean_for_coauthor = data['orcid'].replace('https://orcid.org/', '').strip()
                if orcid_clean_for_coauthor:
                    unique_coauthor_orcids.add(orcid_clean_for_coauthor)
        
        if SHOW_DEBUG_LOGS:
            print(f"  Найдено уникальных ORCID соавторов: {len(unique_coauthor_orcids)}")
            for oc in list(unique_coauthor_orcids)[:5]:
                print(f"    - {oc}")
        
        if unique_coauthor_orcids:
            print(f"  Получение профилей для {len(unique_coauthor_orcids)} соавторов...")
            
            # Ограничиваем количество для производительности
            coauthor_orcids_list = list(unique_coauthor_orcids)[:50]
            
            # Создаем семафор для ограничения параллельных запросов
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            
            async def fetch_coauthor_profile(orcid_id: str):
                async with semaphore:
                    try:
                        person_info = await get_orcid_person_info(orcid_id, session)
                        return orcid_id, person_info
                    except Exception as e:
                        if SHOW_DEBUG_LOGS:
                            print(f"    ⚠️ Ошибка получения профиля для {orcid_id}: {e}")
                        return orcid_id, {}
            
            # Параллельные запросы через asyncio.gather
            tasks = [fetch_coauthor_profile(orcid_id) for orcid_id in coauthor_orcids_list]
            results = await asyncio.gather(*tasks)
            
            # Сохраняем результаты
            for orcid_id, person_info in results:
                if person_info:
                    coauthor_profiles[orcid_id] = person_info
                    if SHOW_DEBUG_LOGS:
                        print(f"    ✅ Получен профиль для {orcid_id}: {list(person_info.keys())}")
            
            print(f"  ✅ Получено профилей для {len(coauthor_profiles)} соавторов")
            
            # Если есть соавторы без ORCID, но с именем, можно попробовать поискать по имени
            # Но это会增加 сложность, оставляем как есть
        else:
            print("  ℹ️ Нет ORCID соавторов для запроса")
        
        # Сохраняем профили соавторов в analyzer
        analyzer.coauthor_profiles = coauthor_profiles
        
        # Повторно анализируем публикации с учетом профилей соавторов
        # (это нужно, чтобы добавить профили в топ соавторов)
        analyzer.analyze_publications()
        
        # Добавляем профили соавторов в профиль для кэширования
        analyzer.profile['coauthor_profiles'] = coauthor_profiles
        
        cache_data = {
            'publications': analyzer.publications,
            'author_info': analyzer.author_info,
            'profile': analyzer.profile,
            'institution_homepages': analyzer.institution_homepages,
            'coauthors_with_orcids': analyzer.coauthors_with_orcids,
            'coauthor_profiles': coauthor_profiles,
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
# ФУНКЦИИ ДЛЯ ВИЗУАЛИЗАЦИИ (НАУЧНЫЙ СТИЛЬ) - ОПТИМИЗИРОВАННЫЕ
# ============================================

@st.cache_data(ttl=3600, show_spinner=False)
def create_visualizations(profile: Dict, lang: str = 'en') -> Dict[str, str]:
    """Создает визуализации в научном стиле и возвращает их в виде base64 изображений"""
    images = {}
    
    apply_scientific_style()
    
    # Функция для перевода
    def t(key: str, **kwargs) -> str:
        return translate(key, lang, **kwargs)
    
    # Уменьшаем DPI для экономии места
    SAVE_DPI = 150  # вместо 300
    
    if profile.get('years_distribution'):
        fig, ax = plt.subplots(figsize=(8, 5))
        years = sorted(profile['years_distribution'].keys())
        counts = [profile['years_distribution'][y] for y in years]
        
        bars = ax.bar(years, counts, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.0)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{count}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel(t('publication_year'), fontsize=11, fontweight='bold')
        ax.set_ylabel(t('number'), fontsize=11, fontweight='bold')
        ax.set_title(t('years_chart_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        ax.set_xticks(years)
        ax.set_xticklabels([str(int(y)) for y in years], rotation=45)
        
        if len(years) >= 2:
            x = np.arange(len(years))
            z = np.polyfit(x, counts, 1)
            p = np.poly1d(z)
            
            ax.plot(years, p(x), 'r-', linewidth=2, alpha=0.8, label=t('trend_label'))
            
            if len(counts) > 3:
                std_err = np.std(counts - p(x)) / np.sqrt(len(counts))
                ax.fill_between(years, p(x) - 1.96*std_err, p(x) + 1.96*std_err, 
                               alpha=0.15, color='red', label=t('confidence_interval'))
            
            if profile.get('trend_correlation'):
                corr = profile['trend_correlation']
                ax.text(0.02, 0.95, f'R² = {corr**2:.3f}', transform=ax.transAxes,
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax.legend(loc='upper left', frameon=True, fancybox=False, edgecolor='black')
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['years_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('top_journals'):
        fig, ax = plt.subplots(figsize=(8, 6))
        journals = list(profile['top_journals'].keys())[:8]
        counts = list(profile['top_journals'].values())[:8]
        
        sorted_pairs = sorted(zip(counts, journals), reverse=True)
        counts, journals = zip(*sorted_pairs)
        
        y_pos = np.arange(len(journals))
        bars = ax.barh(y_pos, counts, color='#A23B72', alpha=0.8, edgecolor='black', linewidth=1.0)
        
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.3, bar.get_y() + bar.get_height()/2,
                   f'{count}', va='center', fontsize=9)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(journals, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel(t('number'), fontsize=11, fontweight='bold')
        ax.set_title(t('journals_chart_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['journals_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('open_access'):
        fig, ax = plt.subplots(figsize=(8, 5))
        
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
                      alpha=0.8, edgecolor='black', linewidth=1.2)
        
        for bar, count in zip(bars, sorted_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                   f'{count}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xlabel(t('open_access'), fontsize=11, fontweight='bold')
        ax.set_ylabel(t('number'), fontsize=11, fontweight='bold')
        ax.set_title(t('oa_chart_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['oa_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('concepts'):
        wordcloud = WordCloud(width=800, height=400, 
                              background_color='white',
                              colormap='viridis',
                              max_words=40,
                              contour_width=1,
                              contour_color='black',
                              random_state=42).generate_from_frequencies(profile['concepts'])
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(t('wordcloud_title'), fontsize=12, fontweight='bold', pad=15)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['wordcloud'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('publishers'):
        fig, ax = plt.subplots(figsize=(8, 5))
        publishers = list(profile['publishers'].keys())[:6]
        counts = [profile['publishers'][p] for p in publishers]
        
        sorted_pairs = sorted(zip(counts, publishers), reverse=True)
        counts, publishers = zip(*sorted_pairs)
        
        bars = ax.bar(range(len(publishers)), counts, color='#5E4B56', alpha=0.8, 
                      edgecolor='black', linewidth=1.0)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                   f'{count}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xticks(range(len(publishers)))
        ax.set_xticklabels(publishers, rotation=45, ha='right', fontsize=9)
        ax.set_xlabel(t('publishers_chart_title').split()[0] if t('publishers_chart_title') else 'Publisher', fontsize=11, fontweight='bold')
        ax.set_ylabel(t('number'), fontsize=11, fontweight='bold')
        ax.set_title(t('publishers_chart_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['publishers_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('most_cited'):
        fig, ax = plt.subplots(figsize=(8, 6))
        top_pubs = profile['most_cited'][:6]
        titles = [f"{p['title'][:30]}..." for p in top_pubs]
        citations = [p['citations'] for p in top_pubs]
        
        sorted_pairs = sorted(zip(citations, titles), reverse=True)
        citations, titles = zip(*sorted_pairs)
        
        bars = ax.barh(range(len(titles)), citations, color='#F18F01', alpha=0.8,
                       edgecolor='black', linewidth=1.0)
        
        for i, (bar, cit) in enumerate(zip(bars, citations)):
            ax.text(cit + 0.3, bar.get_y() + bar.get_height()/2,
                   f'{cit}', va='center', fontsize=9)
        
        ax.set_yticks(range(len(titles)))
        ax.set_yticklabels(titles, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel(t('citations'), fontsize=11, fontweight='bold')
        ax.set_title(t('citations_chart_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['citations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('top_affiliations'):
        fig, ax = plt.subplots(figsize=(8, 5))
        affils = list(profile['top_affiliations'].keys())
        counts = list(profile['top_affiliations'].values())
        
        y_pos = np.arange(len(affils))
        bars = ax.barh(y_pos, counts, color='#3498DB', alpha=0.8,
                       edgecolor='black', linewidth=1.0)
        
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.3, bar.get_y() + bar.get_height()/2,
                   f'{count}', va='center', fontsize=9)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(affils, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel(t('number'), fontsize=11, fontweight='bold')
        ax.set_title(t('affiliations_chart_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['affiliations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle(t('thematic_structure_title'), fontsize=12, fontweight='bold')
    
    if profile.get('top_domains'):
        ax = axes[0, 0]
        domains = list(profile['top_domains'].keys())[:4]
        counts = [profile['top_domains'][d] for d in domains]
        
        ax.bar(range(len(domains)), counts, color='#E74C3C', alpha=0.8)
        ax.set_xticks(range(len(domains)))
        ax.set_xticklabels(domains, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel(t('number'), fontsize=10)
        ax.set_title(t('domains'), fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    if profile.get('top_fields'):
        ax = axes[0, 1]
        fields = list(profile['top_fields'].keys())[:4]
        counts = [profile['top_fields'][f] for f in fields]
        
        ax.bar(range(len(fields)), counts, color='#3498DB', alpha=0.8)
        ax.set_xticks(range(len(fields)))
        ax.set_xticklabels(fields, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel(t('number'), fontsize=10)
        ax.set_title(t('fields'), fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    if profile.get('top_topics'):
        ax = axes[1, 0]
        topics = list(profile['top_topics'].keys())[:4]
        counts = [profile['top_topics'][t] for t in topics]
        
        ax.barh(range(len(topics)), counts, color='#2ECC71', alpha=0.8)
        ax.set_yticks(range(len(topics)))
        ax.set_yticklabels(topics, fontsize=8)
        ax.set_xlabel(t('number'), fontsize=10)
        ax.set_title(t('topics'), fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    if profile.get('top_subtopics'):
        ax = axes[1, 1]
        subtopics = list(profile['top_subtopics'].keys())[:4]
        counts = [profile['top_subtopics'][s] for s in subtopics]
        
        ax.barh(range(len(subtopics)), counts, color='#F39C12', alpha=0.8)
        ax.set_yticks(range(len(subtopics)))
        ax.set_yticklabels(subtopics, fontsize=8)
        ax.set_xlabel(t('number'), fontsize=10)
        ax.set_title(t('subtopics'), fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
    buf.seek(0)
    images['thematic_structure'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    if profile.get('citation_distribution'):
        fig, ax = plt.subplots(figsize=(8, 5))
        
        dist = profile['citation_distribution']
        filtered_dist = {k: v for k, v in dist.items() if v > 0}
        
        ranges = list(filtered_dist.keys())
        counts = list(filtered_dist.values())
        
        bars = ax.bar(range(len(ranges)), counts, color='#8E44AD', alpha=0.8,
                      edgecolor='black', linewidth=1.0)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                   f'{count}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xticks(range(len(ranges)))
        ax.set_xticklabels(ranges, rotation=45, ha='right', fontsize=9)
        ax.set_xlabel(t('citation_range'), fontsize=11, fontweight='bold')
        ax.set_ylabel(t('articles'), fontsize=11, fontweight='bold')
        ax.set_title(t('citation_distribution_title'), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
        buf.seek(0)
        images['citation_distribution'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    if profile.get('top_concepts'):
        top_concepts_items = list(profile['top_concepts'].items())[:6]
        if len(top_concepts_items) >= 3:
            fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(projection='polar'))
            
            concepts = [item[0][:15] for item in top_concepts_items]
            values = [item[1] for item in top_concepts_items]
            
            max_val = max(values) if values else 1
            normalized = [v / max_val for v in values]
            
            concepts_radar = concepts + [concepts[0]]
            values_radar = normalized + [normalized[0]]
            
            angles = np.linspace(0, 2 * np.pi, len(concepts), endpoint=False).tolist()
            angles_radar = angles + [angles[0]]
            
            ax.plot(angles_radar, values_radar, 'o-', linewidth=2, color='#2C3E50', markersize=6)
            ax.fill(angles_radar, values_radar, alpha=0.25, color='#3498DB')
            
            ax.set_xticks(angles)
            ax.set_xticklabels(concepts, fontsize=9, fontweight='bold')
            ax.set_ylim(0, 1.1)
            ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
            ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=7)
            ax.set_title(t('radar_title'), fontsize=12, fontweight='bold', pad=15)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=SAVE_DPI, bbox_inches='tight')
            buf.seek(0)
            images['radar_chart'] = base64.b64encode(buf.getvalue()).decode()
            plt.close()
    
    return images

# ============================================
# ФУНКЦИИ ДЛЯ ГЕНЕРАЦИИ ОТЧЕТОВ
# ============================================

def generate_html_report(profile: Dict, publications: List[Dict], images: Dict[str, str], 
                         logo_base64: Optional[str] = None, app_logo_base64: Optional[str] = None, 
                         institution_homepages: Optional[Dict[str, str]] = None, 
                         theme_colors: Optional[Dict] = None, lang: str = 'en', 
                         coauthor_profiles: Optional[Dict] = None) -> str:
    """Генерирует HTML отчет с расширенной информацией и дизайном из второго кода"""
    
    if theme_colors is None:
        theme_colors = {
            'primary': '#667eea',
            'secondary': '#f39c12'
        }
    
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')
    
    total_pubs = profile.get('total_publications', 0)
    h_index = profile.get('h_index', 0)
    g_index = profile.get('g_index', 0)
    i10_index = profile.get('i10_index', 0)
    i100_index = profile.get('i100_index', 0)
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
    
    source_categories = profile.get('source_categories', {})
    
    category_labels = {
        'articles': {'en': 'source_journal_articles', 'ru': 'source_journal_articles'},
        'repositories': {'en': 'source_repositories', 'ru': 'source_repositories'},
        'ebooks': {'en': 'source_ebooks', 'ru': 'source_ebooks'},
        'proceedings': {'en': 'source_proceedings', 'ru': 'source_proceedings'},
        'other': {'en': 'source_other', 'ru': 'source_other'}
    }
    
    author_affils = set(profile.get('author_affiliations', []))
    
    domestic_collab_filtered = {}
    for country, affils_dict in collaborations.get('domestic', {}).items():
        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
        if filtered_affils:
            domestic_collab_filtered[country] = filtered_affils
    
    international_collab_filtered = {}
    for country, affils_dict in collaborations.get('international', {}).items():
        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
        if filtered_affils:
            international_collab_filtered[country] = filtered_affils
    
    most_collab_country = profile.get('most_collaborative_country', 'None')
    collab_index = profile.get('collaboration_index', 0)
    country_diversity = profile.get('country_diversity', 0)
    
    top_coauthors_with_orcids = profile.get('top_coauthors_with_orcids', {})
    
    def t(key: str, **kwargs) -> str:
        return translate(key, lang, **kwargs)
    
    # ====== Генерация карточек соавторов ======
    coauthors_html = ""
    
    if coauthor_profiles is None:
        coauthor_profiles = profile.get('coauthor_profiles', {})
    
    if SHOW_DEBUG_LOGS:
        print(f"📊 Генерация HTML для соавторов: найдено {len(top_coauthors_with_orcids)} соавторов, профилей: {len(coauthor_profiles)}")
    
    if top_coauthors_with_orcids:
        for name, data in list(top_coauthors_with_orcids.items())[:15]:
            count = data.get('count', 0)
            orcid = data.get('orcid', '')
            
            clean_orcid_for_lookup = orcid.replace('https://orcid.org/', '').strip() if orcid else ''
            
            # Получаем ссылки для соавтора
            person_info = {}
            if clean_orcid_for_lookup and clean_orcid_for_lookup in coauthor_profiles:
                person_info = coauthor_profiles.get(clean_orcid_for_lookup, {})
            elif orcid and orcid in coauthor_profiles:
                person_info = coauthor_profiles.get(orcid, {})
            
            # Извлекаем ссылки из person_info
            links = person_info.get('links', [])
            
            if SHOW_DEBUG_LOGS and links:
                print(f"    👤 {name}: найдено {len(links)} ссылок")
            
            coauthors_html += f"""
            <div class="coauthor-card">
                <div class="coauthor-name">{html.escape(name)}</div>
                <div class="coauthor-joint">{count} {t('joint_works')}</div>
            """
            
            # ORCID ссылка
            if orcid:
                orcid_clean = orcid.replace('https://orcid.org/', '').strip()
                orcid_url = f"https://orcid.org/{orcid_clean}"
                coauthors_html += f"""
                <div style="margin-bottom: 8px;">
                    <a href="{orcid_url}" target="_blank" class="coauthor-profile-link orcid">
                        🆔 ORCID: {orcid_clean}
                    </a>
                </div>
                """
            
            # Дополнительные ссылки из ORCID API
            if links:
                coauthors_html += generate_coauthor_links_html(links, lang)
            else:
                coauthors_html += '<p class="no-links">No additional links found</p>'
            
            coauthors_html += """
            </div>
            """
    else:
        coauthors_html = f'<p>{t("no_publications")}</p>'
    
    # ====== Генерация секции типов источников ======
    source_section_html = ""
    if source_categories:
        source_section_html = f"""
        <div id="sources" class="section">
            <div class="section-title">{t('source_types')}</div>
            <table class="source-table">
                <thead>
                    <tr>
                        <th>{t('source_count')}</th>
                        <th>{t('source_examples')}</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        category_order = ['repositories', 'ebooks', 'proceedings', 'other']
        
        for cat in category_order:
            if cat in source_categories:
                cat_data = source_categories[cat]
                count = cat_data.get('count', 0)
                items = cat_data.get('items', [])
                
                label_key = category_labels.get(cat, {}).get(lang, cat)
                label = t(label_key) if label_key else cat
                
                examples_html = ""
                if items:
                    for item in items[:3]:
                        title = item.get('title', 'No title')[:60]
                        doi = item.get('doi', '')
                        item_id = item.get('id', '')
                        
                        if doi:
                            link = f'https://doi.org/{doi}'
                            link_text = f'DOI: {doi[:20]}...' if len(doi) > 20 else f'DOI: {doi}'
                            examples_html += f'<div class="source-example-item">• {html.escape(title)} — <a href="{link}" target="_blank" class="source-example-link">{link_text}</a> <span class="source-badge source-badge-doi">✅ {t("source_doi_available")}</span></div>'
                        elif item_id:
                            link = item_id
                            examples_html += f'<div class="source-example-item">• {html.escape(title)} — <a href="{link}" target="_blank" class="source-example-link">{t("source_view_link")}</a> <span class="source-badge source-badge-nodoi">⚠️ {t("source_no_doi")}</span></div>'
                        else:
                            examples_html += f'<div class="source-example-item">• {html.escape(title)} <span class="source-badge source-badge-nodoi">⚠️ {t("source_no_link")}</span></div>'
                else:
                    examples_html = f'<em>{t("no_publications")}</em>'
                
                source_section_html += f"""
                    <tr>
                        <td><strong>{label}</strong><br><span style="font-size:12px;color:#666;">{count} {t("articles") if count > 1 else t("article") if "article" in label else ""}</span></td>
                        <td>{examples_html}</td>
                    </tr>
                """
        
        source_section_html += """
                </tbody>
            </table>
        </div>
        """
    
    retraction_flag_html = ""
    if retractions > 0:
        retraction_flag_html = f"""
        <div class="flag-retraction">⚠️ {t('retraction_warning', count=retractions)}</div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{t('app_title')} - ORCID {profile.get('orcid', '')}</title>
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
            .header-logo-app {{
                max-height: 120px;
                max-width: 360px;
                margin-bottom: 10px;
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
            .flag-retraction {{
                background-color: #FFE5E5;
                border-left: 4px solid #FF0000;
                color: #CC0000;
                font-weight: bold;
                padding: 12px 15px;
                border-radius: 5px;
                margin: 10px 0;
                font-size: 16px;
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
            
            .thematic-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
                gap: 15px;
                margin: 15px 0;
            }}
            .thematic-card {{
                background: linear-gradient(135deg, {primary}10 0%, {secondary}10 100%);
                border-radius: 12px;
                padding: 16px 20px;
                border-left: 4px solid {primary};
                transition: transform 0.2s, box-shadow 0.2s;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .thematic-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 16px rgba(0,0,0,0.08);
                background: linear-gradient(135deg, {primary}15 0%, {secondary}15 100%);
            }}
            .thematic-name {{
                font-weight: 600;
                color: {primary};
                font-size: 14px;
                font-family: 'Times New Roman', serif;
            }}
            .thematic-count {{
                color: #555;
                font-size: 13px;
                margin-top: 4px;
                font-family: 'Times New Roman', serif;
            }}
            .thematic-badge {{
                display: inline-block;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                background: {primary}20;
                color: {primary};
                margin-left: 8px;
            }}
            
            /* Source table styles */
            .source-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: 'Times New Roman', serif;
            }}
            .source-table th {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 12px;
                text-align: left;
            }}
            .source-table td {{
                padding: 10px;
                border-bottom: 1px solid #BDC3C7;
                vertical-align: top;
            }}
            .source-table tr:hover {{
                background-color: #f5f5f5;
            }}
            .source-example-item {{
                margin: 3px 0;
                font-size: 13px;
            }}
            .source-example-link {{
                color: #2980B9;
                text-decoration: none;
                font-size: 12px;
            }}
            .source-example-link:hover {{
                text-decoration: underline;
            }}
            .source-badge {{
                display: inline-block;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 5px;
            }}
            .source-badge-doi {{
                background: #d4edda;
                color: #155724;
            }}
            .source-badge-nodoi {{
                background: #f8d7da;
                color: #721c24;
            }}
            
            /* Co-author card styles */
            .coauthor-card {{
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 12px;
                border: 1px solid #e0e0e0;
                border-left: 4px solid {primary};
                transition: transform 0.2s, box-shadow 0.2s;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            
            .coauthor-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(0,0,0,0.1);
                border-color: {primary};
            }}
            
            .coauthor-name {{
                font-size: 16px;
                font-weight: 600;
                color: {primary};
                margin-bottom: 6px;
            }}
            
            .coauthor-joint {{
                font-size: 13px;
                color: #666;
                margin-bottom: 8px;
            }}
            
            .coauthor-profile-link {{
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 11px;
                font-weight: 500;
                text-decoration: none;
                transition: all 0.2s;
                margin: 2px;
            }}
            
            .coauthor-profile-link:hover {{
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }}
            
            .coauthor-profile-link.orcid {{
                background: #a6ce39;
                color: #1a1a1a;
            }}
            
            .coauthor-profile-link.orcid:hover {{
                background: #8cb82e;
            }}
            
            .coauthor-profile-link.website {{
                background: #6c757d;
                color: white;
            }}
            
            .coauthor-profile-link.website:hover {{
                background: #5a6268;
            }}
            
            .coauthor-profile-link.other {{
                background: #17a2b8;
                color: white;
            }}
            
            .coauthor-profile-link.other:hover {{
                background: #138496;
            }}
            
            .coauthor-no-orcid {{
                font-size: 12px;
                color: #999;
                font-style: italic;
            }}
            
            .no-links {{
                color: #999;
                font-style: italic;
                margin: 5px 0;
                font-size: 12px;
            }}
            
            .link-type-badge {{
                display: inline-block;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
            }}
            
            .link-type-websites-social-links {{
                background: #d1ecf1;
                color: #0c5460;
            }}
            
            .link-type-other-ids {{
                background: #fff3cd;
                color: #856404;
            }}
            
            @media print {{
                .sidebar {{ display: none; }}
                .main-content {{ margin-left: 0; }}
            }}
            @media (max-width: 768px) {{
                .sidebar {{ display: none; }}
                .main-content {{ margin-left: 0; padding: 20px; }}
                .thematic-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h3>📑 {t('app_title')}</h3>
            <a href="#overview"><span>📊 {t('profile')}</span></a>
            <a href="#metrics"><span>📈 {t('main_metrics')}</span></a>
            <a href="#visualizations"><span>📊 {t('citations')}</span></a>
            <a href="#thematic"><span>🏷️ {t('topics')}</span></a>
            <a href="#collaborations"><span>🌍 {t('collaborations')}</span></a>
            <a href="#coauthors"><span>🤝 {t('top_coauthors')}</span></a>
            <a href="#publications"><span>📚 {t('publications')}</span></a>
            {f'<a href="#sources"><span>📚 {t("source_types")}</span></a>' if source_categories else ''}
        </div>
        
        <div class="main-content">
            <div class="header">
                {f'<img src="data:image/png;base64,{app_logo_base64}" class="header-logo-app" alt="App Logo">' if app_logo_base64 else ''}
                {f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Journal Logo">' if logo_base64 else ''}
                <div class="date">{t('report_preview')}: {datetime.now().strftime('%d.%m.%Y')}</div>
            </div>
            
            <div id="overview" class="section">
                <div class="section-title">📋 {t('profile')}</div>
                <div class="author-info">
                    <div class="author-name">{author_name}</div>
                    <div class="author-affil"><strong>{t('orcid')}:</strong> <a href="https://orcid.org/{profile.get('orcid', '')}" target="_blank">{profile.get('orcid', 'N/A')}</a></div>
                    {f'<div class="author-affil"><strong>{t("affiliations")}:</strong> {", ".join(author_affiliations[:5])}</div>' if author_affiliations else ''}
                    {f'<div class="author-affil"><strong>{t("countries")}:</strong> {", ".join(author_countries)}</div>' if author_countries else ''}
                    <div class="author-affil"><strong>{t('total_analyzed')}:</strong> {total_pubs}</div>
                </div>
                
                {retraction_flag_html}
            </div>
            
            <div id="metrics" class="section">
                <div class="section-title">📈 {t('main_metrics')}</div>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{total_pubs}</div>
                        <div class="metric-label">{t('publications')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{h_index}</div>
                        <div class="metric-label">{t('h_index')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{g_index}</div>
                        <div class="metric-label">{t('g_index')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{i10_index}</div>
                        <div class="metric-label">{t('i10_index')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{i100_index}</div>
                        <div class="metric-label">{t('i100_index')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_citations:,}</div>
                        <div class="metric-label">{t('total_citations')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{avg_citations:.1f}</div>
                        <div class="metric-label">{t('avg_citations')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{median_citations:.0f}</div>
                        <div class="metric-label">{t('median_citations')}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{oa_percentage:.1f}%</div>
                        <div class="metric-label">{t('open_access')}</div>
                    </div>
                </div>
            </div>
            
            <div id="visualizations" class="section">
                <div class="section-title">📊 {t('citations')}</div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('years_chart', '')}" alt="{t('years_chart_title')}">
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="{t('journals_chart_title')}">
                    </div>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="{t('oa_chart_title')}">
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('publishers_chart', '')}" alt="{t('publishers_chart_title')}">
                    </div>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('affiliations_chart', '')}" alt="{t('affiliations_chart_title')}">
                    </div>
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="{t('wordcloud_title')}">
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('citations_chart', '')}" alt="{t('citations_chart_title')}">
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('citation_distribution', '')}" alt="{t('citation_distribution_title')}">
                </div>
                
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('thematic_structure', '')}" alt="{t('thematic_structure_title')}">
                </div>
                
                {'<div class="chart-container"><img src="data:image/png;base64,' + images.get('radar_chart', '') + '" alt="' + t('radar_title') + '"></div>' if images.get('radar_chart') else ''}
            </div>
            
            <div id="thematic" class="section">
                <div class="section-title">🏷️ {t('topics')}</div>
                
                <h3 style="color: {primary}; margin-top: 20px;">{t('topics')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([
                        f'<div class="thematic-card">'
                        f'<div class="thematic-name">{html.escape(topic)}</div>'
                        f'<div class="thematic-count">📄 {count} {t("articles")}</div>'
                        f'</div>'
                        for topic, count in list(top_primary_topics.items())[:5]
                    ])}
                </div>
                
                <h3 style="color: {primary}; margin-top: 20px;">{t('subtopics')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([
                        f'<div class="thematic-card">'
                        f'<div class="thematic-name">{html.escape(subfield)}</div>'
                        f'<div class="thematic-count">📄 {count} {t("articles")}</div>'
                        f'</div>'
                        for subfield, count in list(top_subfields.items())[:5]
                    ])}
                </div>
                
                <h3 style="color: {primary}; margin-top: 20px;">{t('fields')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([
                        f'<div class="thematic-card">'
                        f'<div class="thematic-name">{html.escape(field)}</div>'
                        f'<div class="thematic-count">📄 {count} {t("articles")}</div>'
                        f'</div>'
                        for field, count in list(top_fields_new.items())[:5]
                    ])}
                </div>
                
                <h3 style="color: {primary}; margin-top: 20px;">{t('domains')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([
                        f'<div class="thematic-card">'
                        f'<div class="thematic-name">{html.escape(domain)}</div>'
                        f'<div class="thematic-count">📄 {count} {t("articles")}</div>'
                        f'</div>'
                        for domain, count in list(top_domains_new.items())[:5]
                    ])}
                </div>
                
                <h3 style="color: {primary}; margin-top: 20px;">{t('concepts')} (Top 10)</h3>
                <div class="thematic-grid">
                    {''.join([
                        f'<div class="thematic-card">'
                        f'<div class="thematic-name">{html.escape(concept)}</div>'
                        f'<div class="thematic-count">📄 {count} {t("articles")}</div>'
                        f'</div>'
                        for concept, count in list(top_keywords.items())[:10]
                    ])}
                </div>
            </div>
            
            <div id="collaborations" class="section">
                <div class="section-title">{t('collaborations')}</div>
                
                <div class="collab-grid">
                    <div class="collab-box">
                        <h4>{t('domestic')}</h4>
                        <p><strong>{t('papers')}:</strong> {domestic_papers}</p>
                        {''.join([
                            f'<div class="collab-country">📍 {country}</div>' +
                            (''.join([
                                f'<div class="collab-affil-item">• <strong>{html.escape(affil)}</strong>: {count} {t("articles")}</div>'
                                for affil, count in list(affils.items())[:10]
                            ]) if isinstance(affils, dict) else f'<div class="collab-affil-item">• {affils} {t("articles")}</div>')
                            for country, affils in list(domestic_collab_filtered.items())
                        ]) if domestic_collab_filtered else f'<p>{t("no_data_collab")}</p>'}
                    </div>
                    <div class="collab-box">
                        <h4>{t('international')}</h4>
                        <p><strong>{t('papers')}:</strong> {international_papers}</p>
                        {''.join([
                            f'<div class="collab-country">📍 {country}</div>' +
                            (''.join([
                                f'<div class="collab-affil-item">• <strong>{html.escape(affil)}</strong>: {count} {t("articles")}</div>'
                                for affil, count in list(affils.items())[:10]
                            ]) if isinstance(affils, dict) else f'<div class="collab-affil-item">• {affils} {t("articles")}</div>')
                            for country, affils in list(international_collab_filtered.items())
                        ]) if international_collab_filtered else f'<p>{t("no_data_collab")}</p>'}
                    </div>
                </div>
                
                <div class="collab-box" style="margin-top: 10px;">
                    <p><strong>{t('collab_index', index=collab_index)}</strong></p>
                    <p><strong>{t('country_diversity', count=country_diversity)}</strong></p>
                    <p><strong>{t('most_collaborative', country=most_collab_country)}</strong></p>
                </div>
            </div>
            
            <div id="coauthors" class="section">
                <div class="section-title">{t('top_coauthors')}</div>
                {coauthors_html if coauthors_html else f'<p>{t("no_publications")}</p>'}
            </div>
            
            {source_section_html}
            
            <div class="section">
                <div class="section-title">📋 {t('h_index')}</div>
                <div class="stats-grid">
                    <div class="stat-item"><strong>{t('first_publication')}:</strong> {profile.get('first_publication', 'N/A')} - {profile.get('last_publication', 'N/A')}</div>
                    <div class="stat-item"><strong>{t('active_years')}:</strong> {active_years}</div>
                    <div class="stat-item"><strong>{t('papers_per_year')}:</strong> {papers_per_year:.1f}</div>
                    <div class="stat-item"><strong>{t('trend')}:</strong> {trend} (R² = {trend_corr**2:.3f})</div>
                    <div class="stat-item"><strong>{t('retractions')}:</strong> {retractions}</div>
                    <div class="stat-item"><strong>{t('corrections')}:</strong> {corrections}</div>
                    <div class="stat-item"><strong>{t('unique_coauthors')}:</strong> {unique_coauthors}</div>
                    <div class="stat-item"><strong>{t('avg_authors_per_paper')}:</strong> {avg_authors:.1f}</div>
                    <div class="stat-item"><strong>{t('max_citations')}:</strong> {max_citations}</div>
                    <div class="stat-item"><strong>{t('thematic_diversity')}:</strong> {profile.get('thematic_diversity_shannon', 0):.3f}</div>
                    <div class="stat-item"><strong>{t('domestic_ratio')}:</strong> {profile.get('domestic_papers_ratio', 0)*100:.1f}%</div>
                    <div class="stat-item"><strong>{t('international_ratio')}:</strong> {profile.get('international_papers_ratio', 0)*100:.1f}%</div>
                </div>
            </div>
            
            <div id="publications" class="section">
                <div class="section-title">{t('publications_list')}</div>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{t('title')}</th>
                                <th>{t('year')}</th>
                                <th>{t('journal')}</th>
                                <th>{t('citations')}</th>
                                <th>{t('citations_per_year')}</th>
                                <th>OA</th>
                                <th>{t('doi')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([
                                f"""
                                <tr>
                                    <td>{i+1}</td>
                                    <td>{html.escape(pub.get('title') or 'No title')[:100]}</td>
                                    <td>{pub.get('publication_year', 'N/A')}</td>
                                    <td>{html.escape(pub.get('journal_name') or 'Unknown')}</td>
                                    <td>{pub.get('cited_by_count', 0)}</td>
                                    <td>{pub.get('citations_per_year', 0):.1f}</td>
                                    <td>{'✅' if pub.get('is_oa', False) else '❌'}</td>
                                    <td><a href="https://doi.org/{html.escape(pub.get('doi', ''))}" target="_blank" class="doi-link">{html.escape(pub.get('doi', ''))}</a></td>
                                </tr>
                                """
                                for i, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True))
                            ])}
                        </tbody>
                    </table>
                    <p><em>{t('publications')}: {len(publications)}</em></p>
                </div>
            </div>
            
            <div class="footer">
                <p>{t('footer')}</p>
                <p><a href="{t('journal_url')}" target="_blank">{t('journal_url')}</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_html_report_with_multiple_authors(all_authors: List[Dict], show_all: bool, journal_logo_base64: Optional[str] = None, app_logo_base64: Optional[str] = None, theme_colors: Optional[Dict] = None, lang: str = 'en') -> str:
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
    
    def t(key: str, **kwargs) -> str:
        return translate(key, lang, **kwargs)
    
    html_parts = []
    
    if not show_all and len(authors_to_show) == 1:
        author_data = authors_to_show[0]
        profile = author_data.get('profile', {})
        publications = author_data.get('publications', [])
        images = author_data.get('images', {})
        analyzer = author_data.get('analyzer')
        institution_homepages = analyzer.institution_homepages if analyzer else {}
        
        coauthor_profiles = {}
        if analyzer and hasattr(analyzer, 'coauthor_profiles'):
            coauthor_profiles = analyzer.coauthor_profiles
        if not coauthor_profiles:
            coauthor_profiles = profile.get('coauthor_profiles', {})
        
        return generate_html_report(
            profile, 
            publications, 
            images, 
            journal_logo_base64, 
            app_logo_base64, 
            institution_homepages, 
            theme_colors, 
            lang,
            coauthor_profiles
        )
    
    html_parts.append(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{t('app_title')} - {t('profile_analysis')}</title>
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
            .header-logo-app {{
                max-height: 120px;
                max-width: 360px;
                margin-bottom: 10px;
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
            .flag-retraction {{
                background-color: #FFE5E5;
                border-left: 4px solid #FF0000;
                color: #CC0000;
                font-weight: bold;
                padding: 12px 15px;
                border-radius: 5px;
                margin: 10px 0;
                font-size: 16px;
            }}
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
            
            .source-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: 'Times New Roman', serif;
            }}
            .source-table th {{
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white;
                padding: 12px;
                text-align: left;
            }}
            .source-table td {{
                padding: 10px;
                border-bottom: 1px solid #BDC3C7;
                vertical-align: top;
            }}
            .source-table tr:hover {{
                background-color: #f5f5f5;
            }}
            .source-example-item {{
                margin: 3px 0;
                font-size: 13px;
            }}
            .source-example-link {{
                color: #2980B9;
                text-decoration: none;
                font-size: 12px;
            }}
            .source-example-link:hover {{
                text-decoration: underline;
            }}
            .source-badge {{
                display: inline-block;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 5px;
            }}
            .source-badge-doi {{
                background: #d4edda;
                color: #155724;
            }}
            .source-badge-nodoi {{
                background: #f8d7da;
                color: #721c24;
            }}
            
            .coauthor-card {{
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 12px;
                border: 1px solid #e0e0e0;
                border-left: 4px solid {primary};
                transition: transform 0.2s, box-shadow 0.2s;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            
            .coauthor-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(0,0,0,0.1);
                border-color: {primary};
            }}
            
            .coauthor-name {{
                font-size: 16px;
                font-weight: 600;
                color: {primary};
                margin-bottom: 6px;
            }}
            
            .coauthor-joint {{
                font-size: 13px;
                color: #666;
                margin-bottom: 8px;
            }}
            
            .coauthor-profiles {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-top: 8px;
            }}
            
            .coauthor-profile-link {{
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 11px;
                font-weight: 500;
                text-decoration: none;
                transition: all 0.2s;
                background: #f0f0f0;
                color: #333;
            }}
            
            .coauthor-profile-link:hover {{
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }}
            
            .coauthor-profile-link.orcid {{
                background: #a6ce39;
                color: #1a1a1a;
            }}
            
            .coauthor-profile-link.orcid:hover {{
                background: #8cb82e;
            }}
            
            .coauthor-profile-link.scopus {{
                background: #e97132;
                color: white;
            }}
            
            .coauthor-profile-link.scopus:hover {{
                background: #d45f24;
            }}
            
            .coauthor-profile-link.researcherid {{
                background: #005a9c;
                color: white;
            }}
            
            .coauthor-profile-link.researcherid:hover {{
                background: #004a82;
            }}
            
            .coauthor-profile-link.website {{
                background: #6c757d;
                color: white;
            }}
            
            .coauthor-profile-link.website:hover {{
                background: #5a6268;
            }}
            
            .coauthor-profile-link.linkedin {{
                background: #0077b5;
                color: white;
            }}
            
            .coauthor-profile-link.linkedin:hover {{
                background: #005e8c;
            }}
            
            .coauthor-profile-link.twitter {{
                background: #1da1f2;
                color: white;
            }}
            
            .coauthor-profile-link.twitter:hover {{
                background: #0d8bdb;
            }}
            
            .coauthor-profile-link.facebook {{
                background: #1877f2;
                color: white;
            }}
            
            .coauthor-profile-link.facebook:hover {{
                background: #0d65d4;
            }}
            
            .coauthor-profile-link.researchgate {{
                background: #00ccbb;
                color: white;
            }}
            
            .coauthor-profile-link.researchgate:hover {{
                background: #00a898;
            }}
            
            .coauthor-profile-link.academia {{
                background: #8a2be2;
                color: white;
            }}
            
            .coauthor-profile-link.academia:hover {{
                background: #7a1fcb;
            }}
            
            .coauthor-profile-link.mendeley {{
                background: #9d1620;
                color: white;
            }}
            
            .coauthor-profile-link.mendeley:hover {{
                background: #7a1118;
            }}
            
            .coauthor-profile-link.publons {{
                background: #2a7de1;
                color: white;
            }}
            
            .coauthor-profile-link.publons:hover {{
                background: #1d66b8;
            }}
            
            .coauthor-profile-link.loop {{
                background: #ff6b00;
                color: white;
            }}
            
            .coauthor-profile-link.loop:hover {{
                background: #cc5500;
            }}
            
            .coauthor-profile-link.impactstory {{
                background: #993366;
                color: white;
            }}
            
            .coauthor-profile-link.impactstory:hover {{
                background: #7a2950;
            }}
            
            .coauthor-profile-link.google-scholar {{
                background: #4285f4;
                color: white;
            }}
            
            .coauthor-profile-link.google-scholar:hover {{
                background: #3367d6;
            }}
            
            .coauthor-profile-link.github {{
                background: #24292e;
                color: white;
            }}
            
            .coauthor-profile-link.github:hover {{
                background: #1a1d21;
            }}
            
            .coauthor-profile-link.other {{
                background: #17a2b8;
                color: white;
            }}
            
            .coauthor-profile-link.other:hover {{
                background: #138496;
            }}
            
            .coauthor-no-orcid {{
                font-size: 12px;
                color: #999;
                font-style: italic;
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
            <h3>📑 {t('app_title')}</h3>
            <a href="#overview"><span>📊 {t('profile')}</span></a>
    """)
    
    for i, author in enumerate(authors_to_show):
        author_name = author.get('author_name', f'Автор {i+1}')
        h_index = author.get('h_index', 0)
        anchor = f"author_{i}"
        html_parts.append(f'<a href="#{anchor}"><span>👤 {html.escape(author_name)} (h-index: {h_index})</span></a>')
    
    html_parts.append("""
        </div>
        <div class="main-content">
            <div class="header">
    """)
    
    if app_logo_base64:
        html_parts.append(f'<img src="data:image/png;base64,{app_logo_base64}" class="header-logo-app" alt="App Logo">')
    
    if journal_logo_base64:
        html_parts.append(f'<img src="data:image/png;base64,{journal_logo_base64}" class="header-logo" alt="Логотип журнала">')
    
    html_parts.append(f"""
                <h1>📊 {t('app_title')}</h1>
                <div class="date">{t('report_preview')}: {datetime.now().strftime('%d.%m.%Y')}</div>
                <div style="margin-top: 15px;">
                    <span class="badge badge-info">{t('publications')}: {len(all_authors)}</span>
    """)
    
    if len(all_authors) > 1:
        html_parts.append(f'<span class="badge badge-success">{t("best_author", name=best_author.get("author_name", "Unknown"), h_index=best_author.get("h_index", 0))}</span>')
    
    if show_all:
        html_parts.append(f'<span class="badge badge-info">{t("showing_all", count=len(all_authors))}</span>')
    else:
        html_parts.append(f'<span class="badge badge-info">{t("showing_single")}</span>')
    
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
            images = create_visualizations(profile, lang) if profile else {}
            
            analyzer = author_data.get('analyzer')
            coauthor_profiles = {}
            if analyzer and hasattr(analyzer, 'coauthor_profiles'):
                coauthor_profiles = analyzer.coauthor_profiles
            if not coauthor_profiles:
                coauthor_profiles = profile.get('coauthor_profiles', {})
            
            h_index = profile.get('h_index', 0)
            total_pubs = profile.get('total_publications', 0)
            total_citations = profile.get('total_citations', 0)
            avg_citations = profile.get('average_citations', 0)
            oa_percentage = profile.get('oa_percentage', 0)
            retractions = profile.get('retractions', 0)
            
            top_journals = profile.get('top_journals', {})
            top_coauthors_with_orcids = profile.get('top_coauthors_with_orcids', {})
            
            coauthors_html = ""
            if top_coauthors_with_orcids:
                for name, data in list(top_coauthors_with_orcids.items())[:15]:
                    count = data.get('count', 0)
                    orcid = data.get('orcid', '')
                    
                    clean_orcid_for_lookup = orcid.replace('https://orcid.org/', '').strip() if orcid else ''
                    
                    person_info = {}
                    if clean_orcid_for_lookup and clean_orcid_for_lookup in coauthor_profiles:
                        person_info = coauthor_profiles.get(clean_orcid_for_lookup, {})
                    elif orcid and orcid in coauthor_profiles:
                        person_info = coauthor_profiles.get(orcid, {})
                    
                    coauthors_html += f"""
                    <div class="coauthor-card">
                        <div class="coauthor-name">{html.escape(name)}</div>
                        <div class="coauthor-joint">{count} {t('joint_works')}</div>
                        <div class="coauthor-profiles">
                    """
                    
                    if orcid:
                        orcid_clean = orcid.replace('https://orcid.org/', '').strip()
                        orcid_url = f"https://orcid.org/{orcid_clean}"
                        coauthors_html += f"""
                            <a href="{orcid_url}" target="_blank" class="coauthor-profile-link orcid">
                                🆔 {t('coauthor_orcid')}
                            </a>
                        """
                    else:
                        coauthors_html += f"""
                            <span class="coauthor-no-orcid">{t('no_orcid_found')}</span>
                        """
                    
                    if person_info:
                        if 'scopus' in person_info:
                            scopus_data = person_info['scopus']
                            scopus_url = scopus_data.get('url', '')
                            scopus_value = scopus_data.get('value', '')
                            if scopus_url:
                                coauthors_html += f"""
                                    <a href="{scopus_url}" target="_blank" class="coauthor-profile-link scopus">
                                        📚 {t('coauthor_scopus')}
                                    </a>
                                """
                            elif scopus_value:
                                coauthors_html += f"""
                                    <a href="https://www.scopus.com/authid/detail.uri?authorId={scopus_value}" target="_blank" class="coauthor-profile-link scopus">
                                        📚 {t('coauthor_scopus')}
                                    </a>
                                """
                        
                        if 'researcherid' in person_info:
                            rid_data = person_info['researcherid']
                            rid_url = rid_data.get('url', '')
                            rid_value = rid_data.get('value', '')
                            if rid_url:
                                coauthors_html += f"""
                                    <a href="{rid_url}" target="_blank" class="coauthor-profile-link researcherid">
                                        🆔 {t('coauthor_researcherid')}
                                    </a>
                                """
                            elif rid_value:
                                coauthors_html += f"""
                                    <a href="https://www.researcherid.com/rid/{rid_value}" target="_blank" class="coauthor-profile-link researcherid">
                                        🆔 {t('coauthor_researcherid')}
                                    </a>
                                """
                        
                        if 'websites' in person_info:
                            websites_list = person_info['websites']
                            if isinstance(websites_list, list):
                                for website in websites_list[:3]:
                                    website_url = website.get('url', '')
                                    website_name = website.get('name', '🌐 Website')
                                    if website_url:
                                        coauthors_html += f"""
                                            <a href="{website_url}" target="_blank" class="coauthor-profile-link website">
                                                🌐 {html.escape(website_name[:20])}
                                            </a>
                                        """
                        elif 'website' in person_info:
                            website_data = person_info['website']
                            website_url = website_data.get('url', '')
                            if website_url:
                                coauthors_html += f"""
                                    <a href="{website_url}" target="_blank" class="coauthor-profile-link website">
                                        🌐 {t('coauthor_website')}
                                    </a>
                                """
                        
                        social_profiles = [
                            ('linkedin', '🔗 LinkedIn', 'linkedin'),
                            ('twitter', '🐦 Twitter', 'twitter'),
                            ('facebook', '📘 Facebook', 'facebook'),
                            ('researchgate', '🔬 ResearchGate', 'researchgate'),
                            ('academia', '📖 Academia', 'academia'),
                            ('mendeley', '📑 Mendeley', 'mendeley'),
                            ('publons', '📝 Publons', 'publons'),
                            ('loop', '🔄 Loop', 'loop'),
                            ('impactstory', '📊 ImpactStory', 'impactstory'),
                            ('google-scholar', '🎓 Google Scholar', 'google-scholar'),
                            ('github', '💻 GitHub', 'github')
                        ]
                        
                        for social_key, social_label, social_class in social_profiles:
                            if social_key in person_info:
                                social_data = person_info[social_key]
                                social_url = social_data.get('url', '')
                                social_value = social_data.get('value', '')
                                
                                if not social_url and social_value:
                                    social_url = _build_external_id_url(social_key, social_value)
                                
                                if social_url:
                                    coauthors_html += f"""
                                        <a href="{social_url}" target="_blank" class="coauthor-profile-link {social_class}">
                                            {social_label}
                                        </a>
                                    """
                        
                        other_ids = set(person_info.keys()) - {'scopus', 'researcherid', 'website', 'websites', 
                                                               'linkedin', 'twitter', 'facebook', 'researchgate', 
                                                               'academia', 'mendeley', 'publons', 'loop', 
                                                               'impactstory', 'google-scholar', 'github'}
                        
                        if other_ids:
                            for other_id in other_ids:
                                other_data = person_info[other_id]
                                other_url = other_data.get('url', '')
                                if other_url:
                                    coauthors_html += f"""
                                        <a href="{other_url}" target="_blank" class="coauthor-profile-link other">
                                            🔗 {html.escape(other_id)}
                                        </a>
                                    """
                    
                    coauthors_html += """
                        </div>
                    </div>
                    """
            else:
                coauthors_html = f'<p>{t("no_publications")}</p>'
            
            source_categories = profile.get('source_categories', {})
            
            category_labels = {
                'articles': {'en': 'source_journal_articles', 'ru': 'source_journal_articles'},
                'repositories': {'en': 'source_repositories', 'ru': 'source_repositories'},
                'ebooks': {'en': 'source_ebooks', 'ru': 'source_ebooks'},
                'proceedings': {'en': 'source_proceedings', 'ru': 'source_proceedings'},
                'other': {'en': 'source_other', 'ru': 'source_other'}
            }
            
            source_section_html = ""
            if source_categories:
                source_section_html = f"""
                <h3>{t('source_types')}</h3>
                <table class="source-table">
                    <thead>
                        <tr>
                            <th>{t('source_count')}</th>
                            <th>{t('source_examples')}</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                category_order = ['repositories', 'ebooks', 'proceedings', 'other']
                
                for cat in category_order:
                    if cat in source_categories:
                        cat_data = source_categories[cat]
                        count = cat_data.get('count', 0)
                        items = cat_data.get('items', [])
                        
                        label_key = category_labels.get(cat, {}).get(lang, cat)
                        label = t(label_key) if label_key else cat
                        
                        examples_html = ""
                        if items:
                            for item in items[:3]:
                                title = item.get('title', 'No title')[:60]
                                doi = item.get('doi', '')
                                item_id = item.get('id', '')
                                
                                if doi:
                                    link = f'https://doi.org/{doi}'
                                    link_text = f'DOI: {doi[:20]}...' if len(doi) > 20 else f'DOI: {doi}'
                                    examples_html += f'<div class="source-example-item">• {html.escape(title)} — <a href="{link}" target="_blank" class="source-example-link">{link_text}</a> <span class="source-badge source-badge-doi">✅ {t("source_doi_available")}</span></div>'
                                elif item_id:
                                    link = item_id
                                    examples_html += f'<div class="source-example-item">• {html.escape(title)} — <a href="{link}" target="_blank" class="source-example-link">{t("source_view_link")}</a> <span class="source-badge source-badge-nodoi">⚠️ {t("source_no_doi")}</span></div>'
                                else:
                                    examples_html += f'<div class="source-example-item">• {html.escape(title)} <span class="source-badge source-badge-nodoi">⚠️ {t("source_no_link")}</span></div>'
                        else:
                            examples_html = f'<em>{t("no_publications")}</em>'
                        
                        source_section_html += f"""
                            <tr>
                                <td><strong>{label}</strong><br><span style="font-size:12px;color:#666;">{count} {t("articles") if count > 1 else t("article") if "article" in label else ""}</span></td>
                                <td>{examples_html}</td>
                            </tr>
                        """
                
                source_section_html += """
                    </tbody>
                </table>
                """
            
            html_parts.append(f"""
            <div id="author_{i}" class="author-section">
                <div class="author-card {'best' if is_best and len(all_authors) > 1 else ''}">
                    <div>
                        <span class="author-rank">{i+1}.</span>
                        <span class="author-name-main">{html.escape(author_name)}</span>
                        <span class="author-hindex">(h-index: {h_index})</span>
                        {'<span class="best-badge">🏆 ' + t("best_author", name="", h_index="") + '</span>' if is_best and len(all_authors) > 1 else ''}
                    </div>
                    
                    {'<div class="flag-retraction">⚠️ ' + t("retraction_warning", count=retractions) + '</div>' if retractions > 0 else ''}
                    
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{total_pubs}</div>
                            <div class="metric-label">{t('publications')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{h_index}</div>
                            <div class="metric-label">{t('h_index')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{total_citations:,}</div>
                            <div class="metric-label">{t('total_citations')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{avg_citations:.1f}</div>
                            <div class="metric-label">{t('avg_citations')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{oa_percentage:.1f}%</div>
                            <div class="metric-label">{t('open_access')}</div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('years_chart', '')}" alt="{t('years_chart_title')}">
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="chart-container">
                            <img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="{t('journals_chart_title')}">
                        </div>
                        <div class="chart-container">
                            <img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="{t('oa_chart_title')}">
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="{t('wordcloud_title')}">
                    </div>
                    
                    <h3>{t('top_coauthors')}</h3>
                    {coauthors_html}
                    
                    {source_section_html}
                    
                    <h3>{t('publications_list')} ({len(publications)})</h3>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{t('title')}</th>
                                    <th>{t('year')}</th>
                                    <th>{t('journal')}</th>
                                    <th>{t('citations')}</th>
                                    <th>{t('citations_per_year')}</th>
                                    <th>{t('doi')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([
                                    f"""
                                    <tr>
                                        <td>{j+1}</td>
                                        <td>{html.escape(pub.get('title') or 'No title')[:80]}</td>
                                        <td>{pub.get('publication_year', 'N/A')}</td>
                                        <td>{html.escape(pub.get('journal_name') or 'Unknown')}</td>
                                        <td>{pub.get('cited_by_count', 0)}</td>
                                        <td>{pub.get('citations_per_year', 0):.1f}</td>
                                        <td><a href="https://doi.org/{html.escape(pub.get('doi', ''))}" target="_blank" class="doi-link">{html.escape(pub.get('doi', ''))}</a></td>
                                    </tr>
                                    """
                                    for j, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)[:20])
                                ])}
                            </tbody>
                        </table>
                        {f'<p><em>{t("showing_limited", shown=20, total=len(publications))}</em></p>' if len(publications) > 20 else ''}
                    </div>
                </div>
            </div>
            """)
    
    else:
        author_data = authors_to_show[0]
        author_name = author_data.get('author_name', 'Unknown')
        profile = author_data.get('profile', {})
        publications = author_data.get('publications', [])
        analyzer = author_data.get('analyzer')
        institution_homepages = analyzer.institution_homepages if analyzer else {}
        
        coauthor_profiles = {}
        if analyzer and hasattr(analyzer, 'coauthor_profiles'):
            coauthor_profiles = analyzer.coauthor_profiles
        if not coauthor_profiles:
            coauthor_profiles = profile.get('coauthor_profiles', {})
        
        images = create_visualizations(profile, lang) if profile else {}
        
        html_parts.append(generate_html_report(
            profile, 
            publications, 
            images, 
            journal_logo_base64, 
            app_logo_base64, 
            institution_homepages, 
            theme_colors, 
            lang,
            coauthor_profiles
        ))
    
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

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ДЛЯ STREAMLIT
# ============================================

def run_profile_analysis(orcid_list: List[str], show_all_authors: bool, journal_logo: Optional[Dict] = None):
    """Запускает полный анализ профиля ученого для одного или нескольких ORCID"""
    
    # Get current language for translations
    current_lang = st.session_state.get('language', 'en')
    def t(key: str, **kwargs) -> str:
        return translate(key, current_lang, **kwargs)
    
    if not orcid_list:
        st.error("⚠️ " + t('no_orcid'))
        return
        
    st.cache_data.clear()
    
    st.info(f"🔍 " + t('analyzing_authors', count=len(orcid_list)))
    
    progress_container = st.empty()
    status_container = st.empty()
    analysis_progress = st.progress(0, text=t('starting_analysis'))
    
    try:
        # Загружаем логотип приложения
        app_logo_base64 = None
        if os.path.exists("icon.png"):
            try:
                with open("icon.png", "rb") as f:
                    app_logo_base64 = base64.b64encode(f.read()).decode()
            except Exception as e:
                print(f"⚠️ Ошибка загрузки логотипа приложения: {e}")
        
        journal_logo_base64 = None
        if journal_logo:
            try:
                for filename, file_info in journal_logo.items():
                    content = file_info['content'] if hasattr(file_info, 'get') else file_info
                    if hasattr(content, 'read'):
                        content = content.read()
                    journal_logo_base64 = base64.b64encode(content).decode()
                    st.success(f"✅ Логотип журнала загружен: {filename}")
                    break
            except Exception as e:
                st.warning(f"⚠️ Ошибка загрузки логотипа журнала: {e}")
        
        total_authors = len(orcid_list)
        stage_weights = {
            'api': 0.6,  # 60% времени на API запросы
            'analysis': 0.25,  # 25% на анализ данных
            'visualization': 0.15  # 15% на генерацию графиков
        }
        
        def progress_callback(current, total, orcid):
            api_progress = (current / total) * stage_weights['api'] * 100
            analysis_progress.progress(api_progress / 100, text=f"📡 {t('loading_data')}: {orcid} ({current}/{total})")
            status_container.info(f"📡 {t('fetching_data')} {current}/{total}: {orcid}")
        
        start_time = time.time()
        
        all_authors_data = asyncio.run(
            analyze_multiple_authors(orcid_list, progress_callback)
        )
        
        analysis_progress.progress(stage_weights['api'], text=f"📊 {t('analyzing_data')}...")
        
        elapsed = time.time() - start_time
        
        if not all_authors_data:
            st.error(f"❌ {t('data_not_found')}")
            analysis_progress.empty()
            return
        
        sorted_authors = sort_authors_by_h_index(all_authors_data)
        
        analysis_progress.progress(stage_weights['api'] + stage_weights['analysis'] * 0.5, text=f"🎨 {t('generating_viz')}...")
        
        for idx, author_data in enumerate(sorted_authors):
            profile = author_data.get('profile', {})
            if profile:
                images = create_visualizations(profile, current_lang)
                author_data['images'] = images
                progress_percent = stage_weights['api'] + stage_weights['analysis'] + (idx + 1) / len(sorted_authors) * stage_weights['visualization']
                analysis_progress.progress(progress_percent, text=f"🎨 {t('creating_charts')} {idx+1}/{len(sorted_authors)}...")
        
        st.session_state['all_authors'] = sorted_authors
        st.session_state['show_all_authors'] = show_all_authors
        st.session_state['journal_logo_base64'] = journal_logo_base64
        st.session_state['app_logo_base64'] = app_logo_base64
        st.session_state['analysis_complete'] = True
        
        analysis_progress.progress(1.0, text=f"✅ {t('analysis_complete_text')}!")
        
        st.success(t('analysis_complete', count=len(sorted_authors), time=elapsed))
        
        if len(sorted_authors) > 1:
            best_author = sorted_authors[0]
            st.info(t('best_author', name=best_author.get('author_name', 'Unknown'), h_index=best_author.get('h_index', 0)))
        else:
            st.info(t('single_author', name=sorted_authors[0].get('author_name', 'Unknown'), h_index=sorted_authors[0].get('h_index', 0)))
        
        if show_all_authors and len(sorted_authors) > 1:
            st.info(t('showing_all', count=len(sorted_authors)))
        elif len(sorted_authors) == 1:
            st.info(t('showing_single_only'))
        else:
            st.info(t('showing_single'))
        
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ {t('error_occurred')}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        analysis_progress.empty()

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
    if 'app_logo_base64' not in st.session_state:
        st.session_state.app_logo_base64 = None
    if 'language' not in st.session_state:
        st.session_state.language = 'en'  # По умолчанию английский
    
    # Apply theme
    primary = st.session_state.primary_color
    secondary = st.session_state.secondary_color
    apply_theme_css(primary, secondary)
    
    # Get current language
    current_lang = st.session_state.language
    
    # Helper function for translations
    def t(key: str, **kwargs) -> str:
        return translate(key, current_lang, **kwargs)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"## {t('settings')}")
        
        # Language selector
        lang_option = st.selectbox(
            t('language'),
            options=['en', 'ru'],
            format_func=lambda x: t('language_en') if x == 'en' else t('language_ru'),
            index=0 if current_lang == 'en' else 1
        )
        if lang_option != current_lang:
            st.session_state.language = lang_option
            st.rerun()
        
        st.markdown("---")
        
        # Color theme
        st.markdown(f"## {t('color_theme')}")
        
        preset_themes = {
            "Default (Blue-Purple)": {"primary": "#667eea", "secondary": "#a9019b"},
            "Emerald (Green-Teal)": {"primary": "#2ecc71", "secondary": "#27ae60"},
            "Sunset (Orange-Coral)": {"primary": "#e74c3c", "secondary": "#c0392b"},
            "Ocean (Deep Blue)": {"primary": "#3498db", "secondary": "#2980b9"},
            "Royal (Purple-Pink)": {"primary": "#9b59b6", "secondary": "#e84393"},
            "Forest (Dark Green)": {"primary": "#27ae60", "secondary": "#2ecc71"},
            "Cherry (Red-Pink)": {"primary": "#e84393", "secondary": "#9b59b6"},
            "Amber (Yellow-Orange)": {"primary": "#f39c12", "secondary": "#e67e22"},
        }
        
        theme_option = st.selectbox(
            t('preset_themes'),
            options=list(preset_themes.keys()),
            index=0
        )
        
        use_preset = st.checkbox(t('use_preset'), value=True)
        
        if use_preset:
            selected_theme = preset_themes[theme_option]
            st.session_state.primary_color = selected_theme["primary"]
            st.session_state.secondary_color = selected_theme["secondary"]
        else:
            selected_color = st.color_picker(
                t('select_color'),
                value=st.session_state.primary_color
            )
            st.session_state.primary_color = selected_color
            st.session_state.secondary_color = get_complementary_color(selected_color)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div style="text-align: center;">'
                f'<div class="color-preview" style="background: {st.session_state.primary_color};"></div>'
                f'<div style="font-size: 11px; margin-top: 5px;">{t("primary")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f'<div style="text-align: center;">'
                f'<div class="color-preview" style="background: {st.session_state.secondary_color};"></div>'
                f'<div style="font-size: 11px; margin-top: 5px;">{t("secondary")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        st.markdown(
            f'<div class="complementary-preview" style="height: 8px; width: 100%; margin: 10px 0;"></div>',
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        st.markdown(f"## {t('analysis_params')}")
        
        global USE_CACHE
        use_cache = st.checkbox(t('use_cache'), value=USE_CACHE)
        USE_CACHE = use_cache
        
        if st.button(t('clear_cache')):
            import shutil
            if os.path.exists('cache'):
                shutil.rmtree('cache')
                st.cache_data.clear()
                st.success(t('cache_cleared'))
        
        st.markdown("---")
        
        st.markdown(f"""
        <div style="font-size: 11px; color: #666; text-align: center;">
            © daM / Chimica Techno Acta \ https://chimicatechnoacta.ru
        </div>
        """, unsafe_allow_html=True)
    
    
    st.markdown("---")
    if os.path.exists("icon.png"):
        col_logo, col_text = st.columns([1, 3])
        with col_logo:
            st.image("icon.png", width=400)
    else:
        st.markdown(f"### {t('profile_analysis')}")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        t('load_data'),
        t('profile'),
        t('reports')
    ])
    
    with tab1:
        st.markdown('<div class="custom-tab fade-in">', unsafe_allow_html=True)
        st.header(t('load_data'))
        
        orcid_text = st.text_area(
            t('orcid_input'),
            placeholder=t('orcid_placeholder'),
            help=t('orcid_help'),
            height=100
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            journal_logo_upload = st.file_uploader(
                t('upload_logo'),
                type=['png', 'jpg', 'jpeg', 'svg'],
                help=t('logo_help')
            )
        
        with col2:
            show_all_authors = st.checkbox(
                t('show_all_authors'),
                value=st.session_state.show_all_authors,
                help=t('show_all_help')
            )
            st.session_state.show_all_authors = show_all_authors
        
        if st.button(t('analyze_button'), type="primary", width='stretch'):
            orcids = parse_orcids(orcid_text)
            
            if not orcids:
                st.error(t('no_orcid'))
            elif len(orcids) > 20:
                st.warning(t('too_many_orcids', count=len(orcids)))
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
            
            st.markdown(f"## {t('profile')}")
            
            if show_all and len(authors) > 1:
                st.info(t('showing_all', count=len(authors)))
                st.markdown("---")
                
                for idx, author_data in enumerate(authors, 1):
                    is_best = (idx == 1)
                    author_name = author_data.get('author_name', f'Автор {idx}')
                    profile = author_data.get('profile', {})
                    publications = author_data.get('publications', [])
                    analyzer = author_data.get('analyzer')
                    images = author_data.get('images', {})
                    
                    h_index = profile.get('h_index', 0)
                    total_pubs = profile.get('total_publications', 0)
                    total_citations = profile.get('total_citations', 0)
                    avg_citations = profile.get('average_citations', 0)
                    oa_percentage = profile.get('oa_percentage', 0)
                    retractions = profile.get('retractions', 0)
                    
                    author_class = "author-card best" if is_best else "author-card"
                    st.markdown(f"""
                    <div class="{author_class}">
                        <div>
                            <span class="author-rank">{idx}.</span>
                            <span class="author-name-main">{author_name}</span>
                            <span class="author-hindex">(h-index: {h_index})</span>
                            {'<span class="best-badge">🏆 ' + t("best_author", name="", h_index="") + '</span>' if is_best and len(authors) > 1 else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if retractions > 0:
                        st.error(t('retraction_warning', count=retractions))
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric(t('publications'), total_pubs)
                    with col2:
                        st.metric(t('h_index'), h_index)
                    with col3:
                        st.metric(t('total_citations'), f"{total_citations:,}")
                    with col4:
                        st.metric(t('avg_citations'), f"{avg_citations:.1f}")
                    with col5:
                        st.metric(t('open_access'), f"{oa_percentage:.1f}%")
                    
                    if images.get('years_chart'):
                        st.image(f"data:image/png;base64,{images['years_chart']}", width='stretch')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if images.get('journals_chart'):
                            st.image(f"data:image/png;base64,{images['journals_chart']}", width='stretch')
                    with col2:
                        if images.get('oa_chart'):
                            st.image(f"data:image/png;base64,{images['oa_chart']}", width='stretch')
                    
                    if images.get('wordcloud'):
                        st.image(f"data:image/png;base64,{images['wordcloud']}", width='stretch')
                    
                    # ====== СЕКЦИЯ КОЛЛАБОРАЦИЙ С ФИЛЬТРАЦИЕЙ ======
                    collaborations = profile.get('collaborations', {})
                    domestic_papers = collaborations.get('domestic_papers', 0)
                    international_papers = collaborations.get('international_papers', 0)
                    
                    # ====== ФИЛЬТРАЦИЯ: Удаляем аффилиации автора из коллабораций при отображении ======
                    author_affils = set(profile.get('author_affiliations', []))
                    
                    # Фильтруем domestic коллаборации для отображения
                    domestic_collab_filtered = {}
                    for country, affils_dict in collaborations.get('domestic', {}).items():
                        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
                        if filtered_affils:
                            domestic_collab_filtered[country] = filtered_affils
                    
                    # Фильтруем international коллаборации для отображения
                    international_collab_filtered = {}
                    for country, affils_dict in collaborations.get('international', {}).items():
                        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
                        if filtered_affils:
                            international_collab_filtered[country] = filtered_affils
                    
                    st.markdown(f"### {t('collaborations')}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"#### {t('domestic')}")
                        st.metric(t('papers'), domestic_papers)
                        if domestic_collab_filtered:
                            for country, affils_dict in domestic_collab_filtered.items():
                                st.markdown(f"**📍 {country}**")
                                for affil, count in list(affils_dict.items())[:10]:
                                    st.markdown(f"• {affil}: {count} {t('articles')}")
                        else:
                            st.info(t('no_data_collab'))
                    
                    with col2:
                        st.markdown(f"#### {t('international')}")
                        st.metric(t('papers'), international_papers)
                        if international_collab_filtered:
                            for country, affils_dict in international_collab_filtered.items():
                                st.markdown(f"**📍 {country}**")
                                for affil, count in list(affils_dict.items())[:10]:
                                    st.markdown(f"• {affil}: {count} {t('articles')}")
                        else:
                            st.info(t('no_data_collab'))
                    
                    st.markdown(f"""
                    **{t('collab_index', index=profile.get('collaboration_index', 0))}**  
                    **{t('country_diversity', count=profile.get('country_diversity', 0))}**  
                    **{t('most_collaborative', country=profile.get('most_collaborative_country', 'None'))}**
                    """)
                    
                    # ====== СЕКЦИЯ ТИПОВ ИСТОЧНИКОВ ======
                    source_categories = profile.get('source_categories', {})
                    if source_categories:
                        st.markdown(f"### {t('source_types')}")
                        
                        category_labels = {
                            'articles': 'source_journal_articles',
                            'repositories': 'source_repositories',
                            'ebooks': 'source_ebooks',
                            'proceedings': 'source_proceedings',
                            'other': 'source_other'
                        }
                        
                        category_order = ['repositories', 'ebooks', 'proceedings', 'other']
                        
                        for cat in category_order:
                            if cat in source_categories:
                                cat_data = source_categories[cat]
                                count = cat_data.get('count', 0)
                                items = cat_data.get('items', [])
                                label_key = category_labels.get(cat, cat)
                                label = t(label_key) if label_key else cat
                                
                                with st.expander(f"{label} ({count})"):
                                    if items:
                                        for item in items[:3]:
                                            title = item.get('title', 'No title')
                                            doi = item.get('doi', '')
                                            item_id = item.get('id', '')
                                            
                                            if doi:
                                                st.markdown(f"• **{title[:80]}** — [DOI: {doi}](https://doi.org/{doi}) ✅")
                                            elif item_id:
                                                st.markdown(f"• **{title[:80]}** — [🔗 {t('source_view_link')}]({item_id}) ⚠️ {t('source_no_doi')}")
                                            else:
                                                st.markdown(f"• **{title[:80]}** ⚠️ {t('source_no_link')}")
                                    else:
                                        st.info(t('no_publications'))
                    
                    # ====== СЕКЦИЯ ТОП СОАВТОРОВ С ORCID ======
                    top_coauthors_with_orcids = profile.get('top_coauthors_with_orcids', {})
                    
                    # Получаем coauthor_profiles из analyzer или из профиля
                    analyzer = author_data.get('analyzer')
                    coauthor_profiles = {}
                    if analyzer and hasattr(analyzer, 'coauthor_profiles'):
                        coauthor_profiles = analyzer.coauthor_profiles
                    if not coauthor_profiles:
                        coauthor_profiles = profile.get('coauthor_profiles', {})
                    
                    if top_coauthors_with_orcids:
                        st.markdown(f"### {t('top_coauthors')}")
                        
                        for name, data in list(top_coauthors_with_orcids.items())[:15]:
                            count = data.get('count', 0)
                            orcid = data.get('orcid', '')
                            
                            # Очищаем ORCID для поиска в coauthor_profiles
                            clean_orcid_for_lookup = orcid.replace('https://orcid.org/', '').strip() if orcid else ''
                            
                            # Получаем персональные профили для этого соавтора
                            person_info = {}
                            if clean_orcid_for_lookup and clean_orcid_for_lookup in coauthor_profiles:
                                person_info = coauthor_profiles.get(clean_orcid_for_lookup, {})
                            elif orcid and orcid in coauthor_profiles:
                                person_info = coauthor_profiles.get(orcid, {})
                            
                            # Извлекаем ссылки из person_info
                            links = person_info.get('links', [])
                            
                            st.markdown(f"""
                            <div class="coauthor-card">
                                <div class="coauthor-name">{html.escape(name)}</div>
                                <div class="coauthor-joint">{count} {t('joint_works')}</div>
                            """, unsafe_allow_html=True)
                            
                            # Добавляем ORCID если есть
                            if orcid:
                                orcid_clean = orcid.replace('https://orcid.org/', '').strip()
                                orcid_url = f"https://orcid.org/{orcid_clean}"
                                st.markdown(f"""
                                <div style="margin-bottom: 8px;">
                                    <a href="{orcid_url}" target="_blank" class="coauthor-profile-link orcid" 
                                       style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;
                                              border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;
                                              background:#a6ce39;color:#1a1a1a;">
                                        🆔 ORCID: {orcid_clean}
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <span class="coauthor-no-orcid">{t('no_orcid_found')}</span>
                                """, unsafe_allow_html=True)
                            
                            # Добавляем все ссылки из ORCID API
                            if links:
                                st.markdown(generate_coauthor_links_html(links, current_lang), unsafe_allow_html=True)
                            else:
                                st.markdown('<p class="no-links">No additional links found</p>', unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    with st.expander(f"{t('publications_list')} ({len(publications)})"):
                        if publications:
                            pub_data = []
                            for pub in sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True):
                                pub_data.append({
                                    t('title'): ((pub.get('title') or 'No title')[:80] + '...') if len(pub.get('title') or 'No title') > 80 else (pub.get('title') or 'No title'),
                                    t('year'): pub.get('publication_year', 'N/A'),
                                    t('journal'): (pub.get('journal_name') or 'Unknown')[:40],
                                    t('citations'): pub.get('cited_by_count', 0),
                                    t('citations_per_year'): pub.get('citations_per_year', 0),
                                    'DOI': pub.get('doi', ''),
                                    'Type': pub.get('source_category', 'unknown')
                                })
                            df = pd.DataFrame(pub_data[:20])
                            st.dataframe(df, width='stretch')
                            if len(publications) > 20:
                                st.caption(t('showing_limited', shown=20, total=len(publications)))
                    
                    st.markdown("---")
            
            else:
                if len(authors) == 1:
                    author_data = authors[0]
                    author_name = author_data.get('author_name', 'Unknown')
                    profile = author_data.get('profile', {})
                    publications = author_data.get('publications', [])
                    analyzer = author_data.get('analyzer')
                    images = author_data.get('images', {})
                    coauthor_profiles = profile.get('coauthor_profiles', {})
                    
                    st.markdown(f"### {t('single_author', name=author_name, h_index=profile.get('h_index', 0))}")
                    
                    if profile.get('retractions', 0) > 0:
                        st.error(t('retraction_warning', count=profile.get('retractions', 0)))
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric(t('publications'), profile.get('total_publications', 0))
                    with col2:
                        st.metric(t('h_index'), profile.get('h_index', 0))
                    with col3:
                        st.metric(t('g_index'), profile.get('g_index', 0))
                    with col4:
                        st.metric(t('i10_index'), profile.get('i10_index', 0))
                    with col5:
                        st.metric(t('i100_index'), profile.get('i100_index', 0))
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(t('total_citations'), f"{profile.get('total_citations', 0):,}")
                    with col2:
                        st.metric(t('avg_citations'), f"{profile.get('average_citations', 0):.1f}")
                    with col3:
                        st.metric(t('open_access'), f"{profile.get('oa_percentage', 0):.1f}%")
                    with col4:
                        st.metric(t('active_years'), profile.get('active_years', 0))
                    
                    if images.get('years_chart'):
                        st.image(f"data:image/png;base64,{images['years_chart']}", width='stretch')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if images.get('journals_chart'):
                            st.image(f"data:image/png;base64,{images['journals_chart']}", width='stretch')
                        if images.get('publishers_chart'):
                            st.image(f"data:image/png;base64,{images['publishers_chart']}", width='stretch')
                    with col2:
                        if images.get('oa_chart'):
                            st.image(f"data:image/png;base64,{images['oa_chart']}", width='stretch')
                        if images.get('affiliations_chart'):
                            st.image(f"data:image/png;base64,{images['affiliations_chart']}", width='stretch')
                    
                    if images.get('wordcloud'):
                        st.image(f"data:image/png;base64,{images['wordcloud']}", width='stretch')
                    
                    if images.get('citations_chart'):
                        st.image(f"data:image/png;base64,{images['citations_chart']}", width='stretch')
                    
                    if images.get('citation_distribution'):
                        st.image(f"data:image/png;base64,{images['citation_distribution']}", width='stretch')
                    
                    if images.get('thematic_structure'):
                        st.image(f"data:image/png;base64,{images['thematic_structure']}", width='stretch')
                    
                    if images.get('radar_chart'):
                        st.image(f"data:image/png;base64,{images['radar_chart']}", width='stretch')
                    
                    # ====== СЕКЦИЯ КОЛЛАБОРАЦИЙ С ФИЛЬТРАЦИЕЙ ======
                    collaborations = profile.get('collaborations', {})
                    domestic_papers = collaborations.get('domestic_papers', 0)
                    international_papers = collaborations.get('international_papers', 0)
                    
                    # ====== ФИЛЬТРАЦИЯ: Удаляем аффилиации автора из коллабораций при отображении ======
                    author_affils = set(profile.get('author_affiliations', []))
                    
                    # Фильтруем domestic коллаборации для отображения
                    domestic_collab_filtered = {}
                    for country, affils_dict in collaborations.get('domestic', {}).items():
                        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
                        if filtered_affils:
                            domestic_collab_filtered[country] = filtered_affils
                    
                    # Фильтруем international коллаборации для отображения
                    international_collab_filtered = {}
                    for country, affils_dict in collaborations.get('international', {}).items():
                        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
                        if filtered_affils:
                            international_collab_filtered[country] = filtered_affils
                    
                    st.markdown(f"### {t('collaborations')}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"#### {t('domestic')}")
                        st.metric(t('papers'), domestic_papers)
                        if domestic_collab_filtered:
                            for country, affils_dict in domestic_collab_filtered.items():
                                st.markdown(f"**📍 {country}**")
                                for affil, count in list(affils_dict.items())[:10]:
                                    st.markdown(f"• {affil}: {count} {t('articles')}")
                        else:
                            st.info(t('no_data_collab'))
                    
                    with col2:
                        st.markdown(f"#### {t('international')}")
                        st.metric(t('papers'), international_papers)
                        if international_collab_filtered:
                            for country, affils_dict in international_collab_filtered.items():
                                st.markdown(f"**📍 {country}**")
                                for affil, count in list(affils_dict.items())[:10]:
                                    st.markdown(f"• {affil}: {count} {t('articles')}")
                        else:
                            st.info(t('no_data_collab'))
                    
                    st.markdown(f"""
                    **{t('collab_index', index=profile.get('collaboration_index', 0))}**  
                    **{t('country_diversity', count=profile.get('country_diversity', 0))}**  
                    **{t('most_collaborative', country=profile.get('most_collaborative_country', 'None'))}**
                    """)
                    
                    # ====== СЕКЦИЯ ТИПОВ ИСТОЧНИКОВ ======
                    source_categories = profile.get('source_categories', {})
                    if source_categories:
                        st.markdown(f"### {t('source_types')}")
                        
                        category_labels = {
                            'articles': 'source_journal_articles',
                            'repositories': 'source_repositories',
                            'ebooks': 'source_ebooks',
                            'proceedings': 'source_proceedings',
                            'other': 'source_other'
                        }
                        
                        category_order = ['repositories', 'ebooks', 'proceedings', 'other']
                        
                        for cat in category_order:
                            if cat in source_categories:
                                cat_data = source_categories[cat]
                                count = cat_data.get('count', 0)
                                items = cat_data.get('items', [])
                                label_key = category_labels.get(cat, cat)
                                label = t(label_key) if label_key else cat
                                
                                with st.expander(f"{label} ({count})"):
                                    if items:
                                        for item in items[:3]:
                                            title = item.get('title', 'No title')
                                            doi = item.get('doi', '')
                                            item_id = item.get('id', '')
                                            
                                            if doi:
                                                st.markdown(f"• **{title[:80]}** — [DOI: {doi}](https://doi.org/{doi}) ✅")
                                            elif item_id:
                                                st.markdown(f"• **{title[:80]}** — [🔗 {t('source_view_link')}]({item_id}) ⚠️ {t('source_no_doi')}")
                                            else:
                                                st.markdown(f"• **{title[:80]}** ⚠️ {t('source_no_link')}")
                                    else:
                                        st.info(t('no_publications'))
                    
                    # ====== СЕКЦИЯ ТОП СОАВТОРОВ С ORCID ======
                    top_coauthors_with_orcids = profile.get('top_coauthors_with_orcids', {})
                    
                    if top_coauthors_with_orcids:
                        st.markdown(f"### {t('top_coauthors')}")
                        
                        for name, data in list(top_coauthors_with_orcids.items()):
                            count = data.get('count', 0)
                            orcid = data.get('orcid', '')
                            
                            # Получаем персональные профили для этого соавтора
                            person_info = coauthor_profiles.get(orcid, {}) if orcid else {}
                            
                            st.markdown(f"""
                            <div class="coauthor-card">
                                <div class="coauthor-name">{html.escape(name)}</div>
                                <div class="coauthor-joint">{count} {t('joint_works')}</div>
                            """, unsafe_allow_html=True)
                            
                            # Добавляем ORCID если есть
                            if orcid:
                                st.markdown(f"""
                                <a href="https://orcid.org/{orcid}" target="_blank" class="coauthor-profile-link orcid" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#a6ce39;color:#1a1a1a;margin-right:6px;">
                                    🆔 {t('coauthor_orcid')}
                                </a>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <span class="coauthor-no-orcid">{t('no_orcid_found')}</span>
                                """, unsafe_allow_html=True)
                            
                            # Добавляем внешние профили из ORCID API
                            if person_info:
                                # Scopus
                                if 'scopus' in person_info:
                                    scopus_data = person_info['scopus']
                                    scopus_url = scopus_data.get('url', '')
                                    scopus_value = scopus_data.get('value', '')
                                    if scopus_url:
                                        st.markdown(f"""
                                        <a href="{scopus_url}" target="_blank" class="coauthor-profile-link scopus" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#e97132;color:white;margin-right:6px;">
                                            📚 {t('coauthor_scopus')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                    elif scopus_value:
                                        st.markdown(f"""
                                        <a href="https://www.scopus.com/authid/detail.uri?authorId={scopus_value}" target="_blank" class="coauthor-profile-link scopus" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#e97132;color:white;margin-right:6px;">
                                            📚 {t('coauthor_scopus')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                
                                # ResearcherID
                                if 'researcherid' in person_info:
                                    rid_data = person_info['researcherid']
                                    rid_url = rid_data.get('url', '')
                                    rid_value = rid_data.get('value', '')
                                    if rid_url:
                                        st.markdown(f"""
                                        <a href="{rid_url}" target="_blank" class="coauthor-profile-link researcherid" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#005a9c;color:white;margin-right:6px;">
                                            🆔 {t('coauthor_researcherid')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                    elif rid_value:
                                        st.markdown(f"""
                                        <a href="https://www.researcherid.com/rid/{rid_value}" target="_blank" class="coauthor-profile-link researcherid" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#005a9c;color:white;margin-right:6px;">
                                            🆔 {t('coauthor_researcherid')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                
                                # Personal website
                                if 'website' in person_info:
                                    website_data = person_info['website']
                                    website_url = website_data.get('url', '')
                                    if website_url:
                                        st.markdown(f"""
                                        <a href="{website_url}" target="_blank" class="coauthor-profile-link website" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#6c757d;color:white;margin-right:6px;">
                                            🌐 {t('coauthor_website')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                
                                # Другие идентификаторы
                                other_ids = ['linkedin', 'twitter', 'facebook', 'researchgate', 'academia', 'mendeley', 'publons']
                                found_other = False
                                for other_id in other_ids:
                                    if other_id in person_info:
                                        other_data = person_info[other_id]
                                        other_url = other_data.get('url', '')
                                        if other_url and not found_other:
                                            st.markdown(f"""
                                            <a href="{other_url}" target="_blank" class="coauthor-profile-link other" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#17a2b8;color:white;margin-right:6px;">
                                                🔗 {t('coauthor_other')}
                                            </a>
                                            """, unsafe_allow_html=True)
                                            found_other = True
                                            break
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    with st.expander(f"{t('publications_list')}"):
                        if publications:
                            pub_data = []
                            for pub in sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True):
                                pub_data.append({
                                    t('title'): (pub.get('title') or 'No title')[:80] + '...' if len(pub.get('title') or 'No title') > 80 else (pub.get('title') or 'No title'),
                                    t('year'): pub.get('publication_year', 'N/A'),
                                    t('journal'): pub.get('journal_name', 'Unknown')[:40],
                                    t('citations'): pub.get('cited_by_count', 0),
                                    t('citations_per_year'): pub.get('citations_per_year', 0),
                                    'OA': '✅' if pub.get('is_oa', False) else '❌',
                                    'DOI': pub.get('doi', ''),
                                    'Type': pub.get('source_category', 'unknown')
                                })
                            df = pd.DataFrame(pub_data)
                            st.dataframe(df, width='stretch')
                else:
                    best_author = authors[0]
                    author_name = best_author.get('author_name', 'Unknown')
                    profile = best_author.get('profile', {})
                    publications = best_author.get('publications', [])
                    analyzer = best_author.get('analyzer')
                    images = best_author.get('images', {})
                    coauthor_profiles = profile.get('coauthor_profiles', {})
                    
                    st.markdown(f"### {t('best_author', name=author_name, h_index=profile.get('h_index', 0))}")
                    
                    if profile.get('retractions', 0) > 0:
                        st.error(t('retraction_warning', count=profile.get('retractions', 0)))
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric(t('publications'), profile.get('total_publications', 0))
                    with col2:
                        st.metric(t('h_index'), profile.get('h_index', 0))
                    with col3:
                        st.metric(t('g_index'), profile.get('g_index', 0))
                    with col4:
                        st.metric(t('i10_index'), profile.get('i10_index', 0))
                    with col5:
                        st.metric(t('i100_index'), profile.get('i100_index', 0))
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(t('total_citations'), f"{profile.get('total_citations', 0):,}")
                    with col2:
                        st.metric(t('avg_citations'), f"{profile.get('average_citations', 0):.1f}")
                    with col3:
                        st.metric(t('open_access'), f"{profile.get('oa_percentage', 0):.1f}%")
                    with col4:
                        st.metric(t('active_years'), profile.get('active_years', 0))
                    
                    if images.get('years_chart'):
                        st.image(f"data:image/png;base64,{images['years_chart']}", width='stretch')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if images.get('journals_chart'):
                            st.image(f"data:image/png;base64,{images['journals_chart']}", width='stretch')
                        if images.get('publishers_chart'):
                            st.image(f"data:image/png;base64,{images['publishers_chart']}", width='stretch')
                    with col2:
                        if images.get('oa_chart'):
                            st.image(f"data:image/png;base64,{images['oa_chart']}", width='stretch')
                        if images.get('affiliations_chart'):
                            st.image(f"data:image/png;base64,{images['affiliations_chart']}", width='stretch')
                    
                    if images.get('wordcloud'):
                        st.image(f"data:image/png;base64,{images['wordcloud']}", width='stretch')
                    
                    if images.get('citations_chart'):
                        st.image(f"data:image/png;base64,{images['citations_chart']}", width='stretch')
                    
                    if images.get('citation_distribution'):
                        st.image(f"data:image/png;base64,{images['citation_distribution']}", width='stretch')
                    
                    if images.get('thematic_structure'):
                        st.image(f"data:image/png;base64,{images['thematic_structure']}", width='stretch')
                    
                    if images.get('radar_chart'):
                        st.image(f"data:image/png;base64,{images['radar_chart']}", width='stretch')
                    
                    # ====== СЕКЦИЯ КОЛЛАБОРАЦИЙ С ФИЛЬТРАЦИЕЙ ======
                    collaborations = profile.get('collaborations', {})
                    domestic_papers = collaborations.get('domestic_papers', 0)
                    international_papers = collaborations.get('international_papers', 0)
                    
                    # ====== ФИЛЬТРАЦИЯ: Удаляем аффилиации автора из коллабораций при отображении ======
                    author_affils = set(profile.get('author_affiliations', []))
                    
                    # Фильтруем domestic коллаборации для отображения
                    domestic_collab_filtered = {}
                    for country, affils_dict in collaborations.get('domestic', {}).items():
                        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
                        if filtered_affils:
                            domestic_collab_filtered[country] = filtered_affils
                    
                    # Фильтруем international коллаборации для отображения
                    international_collab_filtered = {}
                    for country, affils_dict in collaborations.get('international', {}).items():
                        filtered_affils = {k: v for k, v in affils_dict.items() if k not in author_affils}
                        if filtered_affils:
                            international_collab_filtered[country] = filtered_affils
                    
                    st.markdown(f"### {t('collaborations')}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"#### {t('domestic')}")
                        st.metric(t('papers'), domestic_papers)
                        if domestic_collab_filtered:
                            for country, affils_dict in domestic_collab_filtered.items():
                                st.markdown(f"**📍 {country}**")
                                for affil, count in list(affils_dict.items())[:10]:
                                    st.markdown(f"• {affil}: {count} {t('articles')}")
                        else:
                            st.info(t('no_data_collab'))
                    
                    with col2:
                        st.markdown(f"#### {t('international')}")
                        st.metric(t('papers'), international_papers)
                        if international_collab_filtered:
                            for country, affils_dict in international_collab_filtered.items():
                                st.markdown(f"**📍 {country}**")
                                for affil, count in list(affils_dict.items())[:10]:
                                    st.markdown(f"• {affil}: {count} {t('articles')}")
                        else:
                            st.info(t('no_data_collab'))
                    
                    st.markdown(f"""
                    **{t('collab_index', index=profile.get('collaboration_index', 0))}**  
                    **{t('country_diversity', count=profile.get('country_diversity', 0))}**  
                    **{t('most_collaborative', country=profile.get('most_collaborative_country', 'None'))}**
                    """)
                    
                    # ====== СЕКЦИЯ ТИПОВ ИСТОЧНИКОВ ======
                    source_categories = profile.get('source_categories', {})
                    if source_categories:
                        st.markdown(f"### {t('source_types')}")
                        
                        category_labels = {
                            'articles': 'source_journal_articles',
                            'repositories': 'source_repositories',
                            'ebooks': 'source_ebooks',
                            'proceedings': 'source_proceedings',
                            'other': 'source_other'
                        }
                        
                        category_order = ['repositories', 'ebooks', 'proceedings', 'other']
                        
                        for cat in category_order:
                            if cat in source_categories:
                                cat_data = source_categories[cat]
                                count = cat_data.get('count', 0)
                                items = cat_data.get('items', [])
                                label_key = category_labels.get(cat, cat)
                                label = t(label_key) if label_key else cat
                                
                                with st.expander(f"{label} ({count})"):
                                    if items:
                                        for item in items[:3]:
                                            title = item.get('title', 'No title')
                                            doi = item.get('doi', '')
                                            item_id = item.get('id', '')
                                            
                                            if doi:
                                                st.markdown(f"• **{title[:80]}** — [DOI: {doi}](https://doi.org/{doi}) ✅")
                                            elif item_id:
                                                st.markdown(f"• **{title[:80]}** — [🔗 {t('source_view_link')}]({item_id}) ⚠️ {t('source_no_doi')}")
                                            else:
                                                st.markdown(f"• **{title[:80]}** ⚠️ {t('source_no_link')}")
                                    else:
                                        st.info(t('no_publications'))
                    
                    # ====== СЕКЦИЯ ТОП СОАВТОРОВ С ORCID ======
                    top_coauthors_with_orcids = profile.get('top_coauthors_with_orcids', {})
                    
                    if top_coauthors_with_orcids:
                        st.markdown(f"### {t('top_coauthors')}")
                        
                        for name, data in list(top_coauthors_with_orcids.items()):
                            count = data.get('count', 0)
                            orcid = data.get('orcid', '')
                            
                            # Получаем персональные профили для этого соавтора
                            person_info = coauthor_profiles.get(orcid, {}) if orcid else {}
                            
                            st.markdown(f"""
                            <div class="coauthor-card">
                                <div class="coauthor-name">{html.escape(name)}</div>
                                <div class="coauthor-joint">{count} {t('joint_works')}</div>
                            """, unsafe_allow_html=True)
                            
                            # Добавляем ORCID если есть
                            if orcid:
                                st.markdown(f"""
                                <a href="https://orcid.org/{orcid}" target="_blank" class="coauthor-profile-link orcid" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#a6ce39;color:#1a1a1a;margin-right:6px;">
                                    🆔 {t('coauthor_orcid')}
                                </a>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <span class="coauthor-no-orcid">{t('no_orcid_found')}</span>
                                """, unsafe_allow_html=True)
                            
                            # Добавляем внешние профили из ORCID API
                            if person_info:
                                # Scopus
                                if 'scopus' in person_info:
                                    scopus_data = person_info['scopus']
                                    scopus_url = scopus_data.get('url', '')
                                    scopus_value = scopus_data.get('value', '')
                                    if scopus_url:
                                        st.markdown(f"""
                                        <a href="{scopus_url}" target="_blank" class="coauthor-profile-link scopus" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#e97132;color:white;margin-right:6px;">
                                            📚 {t('coauthor_scopus')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                    elif scopus_value:
                                        st.markdown(f"""
                                        <a href="https://www.scopus.com/authid/detail.uri?authorId={scopus_value}" target="_blank" class="coauthor-profile-link scopus" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#e97132;color:white;margin-right:6px;">
                                            📚 {t('coauthor_scopus')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                
                                # ResearcherID
                                if 'researcherid' in person_info:
                                    rid_data = person_info['researcherid']
                                    rid_url = rid_data.get('url', '')
                                    rid_value = rid_data.get('value', '')
                                    if rid_url:
                                        st.markdown(f"""
                                        <a href="{rid_url}" target="_blank" class="coauthor-profile-link researcherid" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#005a9c;color:white;margin-right:6px;">
                                            🆔 {t('coauthor_researcherid')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                    elif rid_value:
                                        st.markdown(f"""
                                        <a href="https://www.researcherid.com/rid/{rid_value}" target="_blank" class="coauthor-profile-link researcherid" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#005a9c;color:white;margin-right:6px;">
                                            🆔 {t('coauthor_researcherid')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                
                                # Personal website
                                if 'website' in person_info:
                                    website_data = person_info['website']
                                    website_url = website_data.get('url', '')
                                    if website_url:
                                        st.markdown(f"""
                                        <a href="{website_url}" target="_blank" class="coauthor-profile-link website" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#6c757d;color:white;margin-right:6px;">
                                            🌐 {t('coauthor_website')}
                                        </a>
                                        """, unsafe_allow_html=True)
                                
                                # Другие идентификаторы
                                other_ids = ['linkedin', 'twitter', 'facebook', 'researchgate', 'academia', 'mendeley', 'publons']
                                found_other = False
                                for other_id in other_ids:
                                    if other_id in person_info:
                                        other_data = person_info[other_id]
                                        other_url = other_data.get('url', '')
                                        if other_url and not found_other:
                                            st.markdown(f"""
                                            <a href="{other_url}" target="_blank" class="coauthor-profile-link other" style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;font-size:11px;font-weight:500;text-decoration:none;background:#17a2b8;color:white;margin-right:6px;">
                                                🔗 {t('coauthor_other')}
                                            </a>
                                            """, unsafe_allow_html=True)
                                            found_other = True
                                            break
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    with st.expander(f"{t('publications_list')}"):
                        if publications:
                            pub_data = []
                            for pub in sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True):
                                pub_data.append({
                                    t('title'): (pub.get('title') or 'No title')[:80] + '...' if len(pub.get('title') or 'No title') > 80 else (pub.get('title') or 'No title'),
                                    t('year'): pub.get('publication_year', 'N/A'),
                                    t('journal'): pub.get('journal_name', 'Unknown')[:40],
                                    t('citations'): pub.get('cited_by_count', 0),
                                    t('citations_per_year'): pub.get('citations_per_year', 0),
                                    'OA': '✅' if pub.get('is_oa', False) else '❌',
                                    'DOI': pub.get('doi', ''),
                                    'Type': pub.get('source_category', 'unknown')
                                })
                            df = pd.DataFrame(pub_data)
                            st.dataframe(df, width='stretch')
        else:
            st.info(t('no_data'))
    
    with tab3:
        if st.session_state.analysis_complete and st.session_state.all_authors:
            authors = st.session_state.all_authors
            show_all = st.session_state.show_all_authors
            journal_logo_base64 = st.session_state.journal_logo_base64
            app_logo_base64 = st.session_state.app_logo_base64
            
            theme_colors = {
                'primary': st.session_state.primary_color,
                'secondary': st.session_state.secondary_color
            }
            
            st.markdown(f"## {t('html_report')}")
            
            best_author = authors[0]
            
            if len(authors) > 1:
                st.info(t('best_author', name=best_author.get('author_name', 'Unknown'), h_index=best_author.get('h_index', 0)))
            else:
                st.info(t('single_author', name=best_author.get('author_name', 'Unknown'), h_index=best_author.get('h_index', 0)))
            
            if show_all and len(authors) > 1:
                st.info(t('showing_all', count=len(authors)))
            else:
                st.info(t('showing_single'))
            
            if st.button(t('download_report'), type="primary", width='stretch'):
                with st.spinner(t('generating_report')):
                    html_report = generate_html_report_with_multiple_authors(
                        authors,
                        show_all,
                        journal_logo_base64,
                        app_logo_base64,
                        theme_colors,
                        current_lang
                    )
                    
                    if show_all and len(authors) > 1:
                        filename = f"profiles_{len(authors)}_authors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    else:
                        filename = f"profile_{best_author.get('author_name', 'unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    
                    st.download_button(
                        label="📥 " + t('download_report'),
                        data=html_report.encode('utf-8'),
                        file_name=filename,
                        mime="text/html",
                        width='stretch'
                    )
            
            if show_all and len(authors) > 1:
                st.markdown("---")
                st.markdown(f"### {t('report_preview')}")
                st.info(t('download_hint'))
        else:
            st.info(t('no_data_reports'))

if __name__ == "__main__":
    main()
