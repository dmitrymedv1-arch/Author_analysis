"""
Author Profile Analysis - Streamlit Application
Analyzes researcher profiles using ORCID and OpenAlex data
Supports English and Russian languages
"""

# ============================================================
# CONFIGURATION & SETTINGS
# ============================================================

import streamlit as st
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from bs4 import BeautifulSoup
import requests
import json
import re
import time
import hashlib
import base64
from io import BytesIO
from datetime import datetime
from collections import Counter, defaultdict
from typing import List, Set, Dict, Tuple, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import nest_asyncio
from pathlib import Path
import os

# Apply nest_asyncio for Jupyter/Colab compatibility
nest_asyncio.apply()

# ============================================================
# LANGUAGE SUPPORT
# ============================================================

TRANSLATIONS = {
    'en': {
        'app_title': '🔬 Author Profile Analysis',
        'app_subtitle': 'Deep Analysis of Researcher Publications via ORCID',
        'sidebar_title': '⚙️ Analysis Settings',
        'orcid_label': 'ORCID ID',
        'orcid_placeholder': '0000-0002-1234-567X or https://orcid.org/...',
        'orcid_help': 'Enter ORCID in any format (with or without URL)',
        'logo_upload': 'Upload Journal Logo (Optional)',
        'logo_help': 'PNG, JPG, SVG supported',
        'advanced_settings': '⚙️ Advanced Settings',
        'batch_size': 'Batch Size',
        'max_publications': 'Max Publications to Analyze',
        'use_cache': 'Use Cache',
        'show_debug': 'Show Debug Logs',
        'analyze_button': '🔍 Analyze Profile',
        'analysis_complete': '✅ Analysis Complete!',
        'analyzing': '🔄 Analyzing Profile...',
        'fetching_orcid': '🔍 Fetching data from ORCID...',
        'fetching_openalex': '📚 Fetching metadata from OpenAlex...',
        'processing': '📊 Processing publications...',
        'generating_reports': '📄 Generating reports...',
        'no_data': '❌ No data found. Please check the ORCID.',
        'error': '❌ Error: {error}',
        'total_publications': '📚 Total Publications',
        'h_index': '📈 h-index',
        'total_citations': '📊 Total Citations',
        'oa_percentage': '🌐 Open Access',
        'g_index': '📊 g-index',
        'i10_index': '📊 i10-index',
        'avg_citations': '📊 Avg Citations',
        'median_citations': '📊 Median Citations',
        'tabs': ['📊 Visualizations', '📋 Publications', '🤝 Collaborations', '⚠️ Risk Assessment', '📑 Report'],
        'export_html': '📄 Export HTML Report',
        'export_pdf': '📑 Export PDF Report',
        'export_csv': '📊 Export CSV',
        'download': 'Download',
        'years_chart': 'Publication Activity Over Time',
        'journals_chart': 'Top Journals',
        'oa_chart': 'Open Access Status',
        'wordcloud_title': 'Research Concepts Word Cloud',
        'citations_chart': 'Most Cited Publications',
        'thematic_title': 'Thematic Structure',
        'collaborations_title': 'Collaboration Analysis',
        'domestic': '🇷🇺 Domestic Collaborations',
        'international': '🌐 International Collaborations',
        'mixed_papers': 'Mixed Papers',
        'collab_index': 'Collaboration Index',
        'country_diversity': 'Country Diversity',
        'most_collab_country': 'Most Collaborative Country',
        'top_coauthors': 'Top Co-authors',
        'risk_flags': '⚠️ Risk Flags',
        'recommendation': '💡 Editor Recommendation',
        'no_flags': '✅ No risk flags detected',
        'publications_table': 'Publications List',
        'title_col': 'Title',
        'year_col': 'Year',
        'journal_col': 'Journal',
        'citations_col': 'Citations',
        'oa_col': 'OA',
        'doi_col': 'DOI',
        'filter_publications': '🔍 Filter Publications',
        'year_range': 'Year Range',
        'min_citations': 'Min Citations',
        'journal_filter': 'Filter by Journal',
        'reset_filters': 'Reset Filters',
        'institution_homepages': '🏛️ Institution Homepages',
        'no_homepages': 'No institution homepages found'
    },
    'ru': {
        'app_title': '🔬 Анализ профиля ученого',
        'app_subtitle': 'Глубокий анализ публикаций исследователя через ORCID',
        'sidebar_title': '⚙️ Настройки анализа',
        'orcid_label': 'ORCID ID',
        'orcid_placeholder': '0000-0002-1234-567X или https://orcid.org/...',
        'orcid_help': 'Введите ORCID в любом формате (с URL или без)',
        'logo_upload': 'Загрузить логотип журнала (опционально)',
        'logo_help': 'Поддерживаются PNG, JPG, SVG',
        'advanced_settings': '⚙️ Расширенные настройки',
        'batch_size': 'Размер батча',
        'max_publications': 'Максимум статей для анализа',
        'use_cache': 'Использовать кэш',
        'show_debug': 'Показывать отладочные логи',
        'analyze_button': '🔍 Анализировать профиль',
        'analysis_complete': '✅ Анализ завершен!',
        'analyzing': '🔄 Выполняется анализ профиля...',
        'fetching_orcid': '🔍 Получение данных из ORCID...',
        'fetching_openalex': '📚 Получение метаданных из OpenAlex...',
        'processing': '📊 Обработка публикаций...',
        'generating_reports': '📄 Генерация отчетов...',
        'no_data': '❌ Данные не найдены. Проверьте правильность ORCID.',
        'error': '❌ Ошибка: {error}',
        'total_publications': '📚 Всего публикаций',
        'h_index': '📈 h-index',
        'total_citations': '📊 Всего цитирований',
        'oa_percentage': '🌐 Открытый доступ',
        'g_index': '📊 g-index',
        'i10_index': '📊 i10-index',
        'avg_citations': '📊 Среднее цитирований',
        'median_citations': '📊 Медиана цитирований',
        'tabs': ['📊 Визуализации', '📋 Публикации', '🤝 Коллаборации', '⚠️ Оценка рисков', '📑 Отчет'],
        'export_html': '📄 Экспорт HTML отчета',
        'export_pdf': '📑 Экспорт PDF отчета',
        'export_csv': '📊 Экспорт CSV',
        'download': 'Скачать',
        'years_chart': 'Динамика публикационной активности',
        'journals_chart': 'Топ журналов',
        'oa_chart': 'Статус открытого доступа',
        'wordcloud_title': 'Облако ключевых концептов',
        'citations_chart': 'Самые цитируемые публикации',
        'thematic_title': 'Тематическая структура',
        'collaborations_title': 'Анализ коллабораций',
        'domestic': '🇷🇺 Внутристрановые коллаборации',
        'international': '🌐 Международные коллаборации',
        'mixed_papers': 'Смешанные статьи',
        'collab_index': 'Индекс коллабораций',
        'country_diversity': 'Страновое разнообразие',
        'most_collab_country': 'Самая коллаборативная страна',
        'top_coauthors': 'Топ соавторов',
        'risk_flags': '⚠️ Флаги риска',
        'recommendation': '💡 Рекомендация редактора',
        'no_flags': '✅ Флаги риска не обнаружены',
        'publications_table': 'Список публикаций',
        'title_col': 'Название',
        'year_col': 'Год',
        'journal_col': 'Журнал',
        'citations_col': 'Цитаты',
        'oa_col': 'ОА',
        'doi_col': 'DOI',
        'filter_publications': '🔍 Фильтр публикаций',
        'year_range': 'Диапазон лет',
        'min_citations': 'Мин. цитирований',
        'journal_filter': 'Фильтр по журналу',
        'reset_filters': 'Сбросить фильтры',
        'institution_homepages': '🏛️ Сайты институтов',
        'no_homepages': 'Сайты институтов не найдены'
    }
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_text(key: str) -> str:
    """Get translated text based on current language setting"""
    lang = st.session_state.get('language', 'en')
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def clean_orcid(orcid_input: str) -> str:
    """Clean ORCID from extra characters and standardize format"""
    orcid = orcid_input.strip().upper()
    
    if 'orcid.org/' in orcid:
        orcid = orcid.split('orcid.org/')[-1]
    
    orcid = re.sub(r'[^0-9X-]', '', orcid)
    
    if re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid):
        return orcid
    
    if len(orcid) == 16 and orcid.isdigit():
        return f"{orcid[:4]}-{orcid[4:8]}-{orcid[8:12]}-{orcid[12:]}"
    
    return orcid

def extract_country_from_affiliation(affiliation: str) -> str:
    """Extract country from affiliation name"""
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
    """Normalize author name for comparison"""
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

def safe_get(data, *keys, default=None):
    """Safely get nested dictionary value"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def chunks(lst, n):
    """Split list into chunks of size n"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def apply_scientific_style():
    """Apply scientific style for matplotlib"""
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
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '#000000',
        'legend.fancybox': False,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'figure.facecolor': 'white',
        'figure.constrained_layout.use': True,
        'figure.figsize': (8, 6),
        'lines.linewidth': 2,
        'lines.markersize': 7,
    })

# ============================================================
# CACHE MANAGEMENT
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_cache_path(orcid: str) -> str:
    """Get cache file path for ORCID"""
    orcid_clean = clean_orcid(orcid)
    cache_dir = Path('cache')
    cache_dir.mkdir(exist_ok=True)
    return str(cache_dir / f"{orcid_clean}.json")

@st.cache_data(ttl=3600, show_spinner=False)
def load_from_cache(orcid: str) -> Optional[Dict]:
    """Load data from cache"""
    if not st.session_state.get('use_cache', True):
        return None
    
    cache_path = get_cache_path(orcid)
    if Path(cache_path).exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception:
            return None
    return None

def save_to_cache(orcid: str, data: Dict):
    """Save data to cache"""
    if not st.session_state.get('use_cache', True):
        return
    
    cache_path = get_cache_path(orcid)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ============================================================
# API FUNCTIONS
# ============================================================

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_with_retry(session, url, params=None, headers=None, method='GET'):
    """Fetch with retry mechanism"""
    timeout = st.session_state.get('timeout', 30)
    max_retries = st.session_state.get('max_retries', 3)
    
    for attempt in range(max_retries):
        try:
            async with session.request(method, url, params=params, headers=headers, timeout=timeout) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 2 * (attempt + 1)))
                    await asyncio.sleep(retry_after)
                    continue
                
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))
            else:
                return None
    return None

async def get_orcid_dois(orcid: str, session) -> Set[str]:
    """Get DOIs from ORCID profile"""
    orcid = clean_orcid(orcid)
    if not orcid:
        return set()
    
    headers = {'Accept': 'application/json'}
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    
    data = await fetch_with_retry(session, url, headers=headers)
    if not data:
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
    except Exception:
        pass
    
    return dois

async def get_openalex_metadata(dois: List[str], session) -> List[Dict]:
    """Get metadata from OpenAlex for DOIs"""
    if not dois:
        return []
    
    doi_query = '|'.join(dois[:50])
    params = {
        'filter': f'doi:{doi_query}',
        'per-page': len(dois)
    }
    url = "https://api.openalex.org/works"
    
    data = await fetch_with_retry(session, url, params=params)
    if not data:
        return []
    
    return data.get('results', [])

async def get_openalex_author(orcid: str, session) -> Dict:
    """Get author info from OpenAlex by ORCID"""
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
            'h_index': author.get('h_index', 0)
        }
    return {}

async def get_institution_homepages(institution_ids: List[str], session) -> Dict[str, str]:
    """Get homepages for institutions from OpenAlex"""
    if not institution_ids:
        return {}
    
    unique_ids = list(set([id for id in institution_ids if id]))
    if not unique_ids:
        return {}
    
    homepages = {}
    batch_size = st.session_state.get('batch_size', 50)
    
    for batch in chunks(unique_ids, batch_size):
        id_query = '|'.join([id.replace('https://openalex.org/', '') for id in batch])
        url = "https://api.openalex.org/institutions"
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
        
        await asyncio.sleep(0.5)
    
    return homepages

# ============================================================
# DATA PARSING
# ============================================================

def parse_openalex_publication(item: Dict) -> Dict:
    """Parse OpenAlex publication with extended information"""
    try:
        pub = {}
        
        pub['id'] = item.get('id', '')
        pub['doi'] = item.get('doi', '').replace('https://doi.org/', '')
        pub['title'] = item.get('title', 'No title')
        pub['publication_year'] = item.get('publication_year')
        pub['type'] = item.get('type', 'unknown')
        
        # Journal and publisher
        if item.get('primary_location'):
            source = item['primary_location'].get('source', {})
            pub['journal_name'] = source.get('display_name', 'Unknown')
            pub['publisher'] = source.get('host_organization_name') or source.get('publisher', 'Unknown')
            pub['issn'] = source.get('issn', [])
        else:
            pub['journal_name'] = 'Unknown'
            pub['publisher'] = 'Unknown'
            pub['issn'] = []
        
        # Open Access
        oa = item.get('open_access', {})
        pub['is_oa'] = oa.get('is_oa', False)
        pub['open_access_status'] = oa.get('oa_status', 'closed')
        pub['oa_url'] = oa.get('oa_url', None)
        
        # Affiliations and institutions
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
                            'type': inst.get('type', '')
                        })
        
        pub['affiliations'] = affiliations
        pub['affiliation_countries'] = affiliation_countries
        pub['institutions'] = institutions
        
        if affiliations:
            pub['country'] = extract_country_from_affiliation(affiliations[0])
        else:
            pub['country'] = 'Unknown'
        
        # Authors
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
        
        # Topics and concepts
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
        
        # Keywords
        keywords = item.get('keywords', [])
        pub['keywords'] = [k.get('display_name', '') for k in keywords if k.get('display_name')]
        
        # Concepts with levels
        concepts = []
        concept_levels = {}
        fields = []
        domains = []
        topics_old = []
        subtopics = []
        
        for concept in item.get('concepts', []):
            concept_name = concept.get('display_name', '')
            concept_level = concept.get('level', 0)
            
            if concept_name:
                concepts.append(concept_name)
                concept_levels[concept_name] = concept_level
            
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
        
        # Citations
        pub['cited_by_count'] = item.get('cited_by_count', 0)
        pub['cited_by_percentile'] = item.get('cited_by_percentile', {})
        
        # Retractions
        pub['is_retracted'] = item.get('is_retracted', False)
        pub['is_correction'] = item.get('is_correction', False)
        pub['is_paratext'] = item.get('is_paratext', False)
        
        pub['publication_date'] = item.get('publication_date')
        pub['created_date'] = item.get('created_date')
        pub['updated_date'] = item.get('updated_date')
        
        return pub
        
    except Exception:
        return None

# ============================================================
# PROFILE ANALYZER
# ============================================================

class ScholarProfileAnalyzer:
    def __init__(self, orcid: str):
        self.orcid = clean_orcid(orcid)
        self.publications = []
        self.author_info = {}
        self.author_name = None
        self.author_affiliations = []
        self.author_countries = []
        self.profile = {}
        self.institution_homepages = {}
        self.collaborations = {
            'domestic': defaultdict(lambda: defaultdict(int)),
            'international': defaultdict(lambda: defaultdict(int)),
            'domestic_papers': 0,
            'international_papers': 0,
            'mixed_papers': 0
        }
    
    def add_publication(self, pub_data: Dict):
        self.publications.append(pub_data)
    
    def set_author_info(self, author_info: Dict):
        self.author_info = author_info
        self.author_name = author_info.get('display_name', 'Unknown')
        
        for aff in author_info.get('affiliations', []):
            inst_name = aff.get('institution', '')
            country = aff.get('country', '')
            if inst_name and inst_name not in self.author_affiliations:
                self.author_affiliations.append(inst_name)
                if country and country not in self.author_countries:
                    self.author_countries.append(country)
    
    def set_institution_homepages(self, homepages: Dict[str, str]):
        self.institution_homepages = homepages
    
    def analyze_publications(self):
        if not self.publications:
            return
        
        self.profile['total_publications'] = len(self.publications)
        self.profile['orcid'] = self.orcid
        self.profile['author_name'] = self.author_name or 'Unknown'
        self.profile['author_affiliations'] = self.author_affiliations
        self.profile['author_countries'] = self.author_countries
        
        # Years distribution
        years = [p.get('publication_year') for p in self.publications if p.get('publication_year')]
        self.profile['years_distribution'] = dict(Counter(years))
        self.profile['first_publication'] = min(years) if years else None
        self.profile['last_publication'] = max(years) if years else None
        self.profile['active_years'] = len(set(years)) if years else 0
        
        # Journals
        journals = [p.get('journal_name') for p in self.publications if p.get('journal_name')]
        self.profile['journals'] = dict(Counter(journals))
        self.profile['top_journals'] = dict(Counter(journals).most_common(10))
        
        # Publishers
        publishers = [p.get('publisher') for p in self.publications if p.get('publisher') and p.get('publisher') != 'Unknown']
        self.profile['publishers'] = dict(Counter(publishers))
        
        # Open Access
        oa_statuses = [p.get('open_access_status') for p in self.publications if p.get('open_access_status')]
        self.profile['open_access'] = dict(Counter(oa_statuses))
        self.profile['total_oa'] = sum(1 for p in self.publications if p.get('is_oa', False))
        self.profile['oa_percentage'] = (self.profile['total_oa'] / len(self.publications) * 100) if self.publications else 0
        
        # Affiliations
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
        
        # Countries
        countries = [p.get('country') for p in self.publications if p.get('country')]
        self.profile['countries'] = dict(Counter(countries))
        
        # Concepts
        all_concepts = []
        all_fields = []
        all_domains = []
        all_topics = []
        all_subtopics = []
        all_primary_topics = []
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
            
            if p.get('primary_topic') and p['primary_topic'].get('display_name'):
                all_primary_topics.append(p['primary_topic']['display_name'])
            
            if p.get('keywords'):
                all_keywords.extend(p['keywords'])
        
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
        self.profile['primary_topics'] = dict(Counter(all_primary_topics))
        self.profile['top_primary_topics'] = dict(Counter(all_primary_topics).most_common(10))
        self.profile['keywords'] = dict(Counter(all_keywords))
        self.profile['top_keywords'] = dict(Counter(all_keywords).most_common(20))
        
        # Retractions
        self.profile['retractions'] = sum(1 for p in self.publications if p.get('is_retracted', False))
        self.profile['corrections'] = sum(1 for p in self.publications if p.get('is_correction', False))
        
        # Coauthors
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
        
        # Author counts
        author_counts = [p.get('author_count', 0) for p in self.publications if p.get('author_count', 0) > 0]
        if author_counts:
            self.profile['avg_authors_per_paper'] = np.mean(author_counts)
            self.profile['median_authors_per_paper'] = np.median(author_counts)
        
        # Citations
        citations = [p.get('cited_by_count', 0) for p in self.publications]
        self.profile['total_citations'] = sum(citations)
        self.profile['average_citations'] = sum(citations) / len(citations) if citations else 0
        self.profile['median_citations'] = np.median(citations) if citations else 0
        self.profile['max_citations'] = max(citations) if citations else 0
        
        # Citation distribution
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
        
        # Most cited
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
        
        # Trend
        if years and len(years) >= 2:
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
        
        # Productivity
        self.profile['papers_per_year'] = len(self.publications) / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        
        # Thematic diversity
        if all_concepts:
            concept_counts = Counter(all_concepts)
            total = len(all_concepts)
            shannon_index = 0
            for count in concept_counts.values():
                p = count / total
                shannon_index -= p * np.log(p)
            self.profile['thematic_diversity_shannon'] = shannon_index
            self.profile['unique_concepts'] = len(concept_counts)
        
        # Collaborations
        self._analyze_collaborations()
        
        # Risk flags
        self.profile['risk_flags'] = self._assess_risks()
        
        # Recommendation
        self.profile['recommendation'] = self._generate_recommendation()
    
    def _analyze_collaborations(self):
        """Analyze collaborations with affiliations"""
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
            'mixed_papers': 0
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
        """Assess risks and return warnings"""
        flags = []
        
        if self.profile.get('papers_per_year', 0) > 30:
            flags.append("⚠️ Anomalously high productivity (>30 papers/year)")
        
        if self.profile.get('retractions', 0) > 1:
            flags.append(f"🔴 {self.profile['retractions']} retractions in profile")
        
        if self.profile.get('top_journals'):
            top_ratio = list(self.profile['top_journals'].values())[0] / self.profile['total_publications']
            if top_ratio > 0.3:
                flags.append("⚠️ >30% publications in one journal")
        
        suspicious_journals = ['Cureus', 'PLoS ONE', 'Scientific Reports']
        suspicious_pubs = [j for j in self.profile.get('journals', {}).keys() if any(s in j for s in suspicious_journals)]
        if suspicious_pubs:
            flags.append(f"⚠️ Publications in low-selectivity journals: {', '.join(suspicious_pubs[:3])}")
        
        if self.profile.get('unique_concepts', 0) < 5 and self.profile.get('total_publications', 0) > 10:
            flags.append("⚠️ Low thematic diversity")
        
        if self.profile.get('international_papers_ratio', 0) < 0.1 and self.profile.get('total_publications', 0) > 20:
            flags.append("⚠️ Low level of international collaboration")
        
        return flags
    
    def _generate_recommendation(self) -> str:
        """Generate editor recommendation"""
        risk_count = len(self.profile.get('risk_flags', []))
        total_pubs = self.profile.get('total_publications', 0)
        h_index = self.profile.get('h_index', 0)
        trend = self.profile.get('trend_direction', 'stable')
        
        if risk_count >= 3:
            return "🔴 Additional verification required. Multiple red flags detected."
        elif risk_count >= 1:
            return "🟡 Caution recommended. Some warnings present."
        elif total_pubs >= 30 and h_index >= 15 and trend in ['up', 'strong_up']:
            return "🟢 Outstanding researcher. High productivity and growing h-index."
        elif total_pubs >= 20 and h_index >= 10:
            return "🟢 Strong candidate. Stable publication activity."
        elif total_pubs >= 10 and h_index >= 5:
            return "🟢 Promising researcher. Recommended for consideration."
        elif total_pubs >= 5:
            return "🟢 Early-career researcher. Requires expert evaluation."
        else:
            return "🟢 Young scientist. Publications require thorough peer review."
    
    def get_profile_data(self) -> Dict:
        return self.profile
    
    def get_publications(self) -> List[Dict]:
        return self.publications

# ============================================================
# DATA COLLECTION
# ============================================================

async def collect_scholar_data(orcid: str) -> Tuple[ScholarProfileAnalyzer, Dict, List[Dict]]:
    """Collect all data for scholar profile"""
    
    orcid_clean = clean_orcid(orcid)
    if not orcid_clean:
        return None, {}, []
    
    # Check cache
    cached_data = load_from_cache(orcid_clean)
    if cached_data:
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
        # Get author info
        author_info = await get_openalex_author(orcid_clean, session)
        if author_info:
            analyzer.set_author_info(author_info)
        
        # Get DOIs from ORCID
        orcid_dois = await get_orcid_dois(orcid_clean, session)
        if not orcid_dois:
            return analyzer, {}, []
        
        all_dois = list(orcid_dois)
        max_pubs = st.session_state.get('max_publications', 1000)
        
        if len(all_dois) > max_pubs:
            all_dois = all_dois[:max_pubs]
        
        # Get metadata from OpenAlex
        all_metadata = []
        batch_size = st.session_state.get('batch_size', 50)
        doi_batches = list(chunks(all_dois, batch_size))
        
        for batch in doi_batches:
            batch_metadata = await get_openalex_metadata(batch, session)
            all_metadata.extend(batch_metadata)
            await asyncio.sleep(0.5)
        
        # Parse publications
        for item in all_metadata:
            pub_data = parse_openalex_publication(item)
            if pub_data:
                analyzer.add_publication(pub_data)
        
        # Get institution homepages
        all_institution_ids = []
        for pub in analyzer.publications:
            for inst in pub.get('institutions', []):
                inst_id = inst.get('id', '')
                if inst_id:
                    all_institution_ids.append(inst_id)
        
        if all_institution_ids:
            homepages = await get_institution_homepages(all_institution_ids, session)
            analyzer.set_institution_homepages(homepages)
        
        # Analyze profile
        analyzer.analyze_publications()
        
        # Save to cache
        cache_data = {
            'publications': analyzer.publications,
            'author_info': analyzer.author_info,
            'profile': analyzer.profile,
            'institution_homepages': analyzer.institution_homepages,
            'timestamp': datetime.now().isoformat()
        }
        save_to_cache(orcid_clean, cache_data)
        
        return analyzer, analyzer.profile, analyzer.publications

# ============================================================
# VISUALIZATION FUNCTIONS
# ============================================================

def create_visualizations(profile: Dict) -> Dict[str, str]:
    """Create scientific-style visualizations"""
    images = {}
    apply_scientific_style()
    
    # 1. Years chart with trend
    if profile.get('years_distribution'):
        fig, ax = plt.subplots(figsize=(10, 6))
        years = sorted(profile['years_distribution'].keys())
        counts = [profile['years_distribution'][y] for y in years]
        
        bars = ax.bar(years, counts, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                    f'{count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('Year' if st.session_state.get('language', 'en') == 'en' else 'Год', fontsize=12, fontweight='bold')
        ax.set_ylabel('Publications' if st.session_state.get('language', 'en') == 'en' else 'Публикации', fontsize=12, fontweight='bold')
        ax.set_title(get_text('years_chart'), fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.set_xticks(years)
        ax.set_xticklabels([str(int(y)) for y in years], rotation=45)
        
        if len(years) >= 2:
            x = np.arange(len(years))
            z = np.polyfit(x, counts, 1)
            p = np.poly1d(z)
            ax.plot(years, p(x), 'r-', linewidth=2.5, alpha=0.8, label='Trend' if st.session_state.get('language', 'en') == 'en' else 'Тренд')
            
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
    
    # 2. Journals chart
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
        ax.set_xlabel('Publications' if st.session_state.get('language', 'en') == 'en' else 'Публикации', fontsize=12, fontweight='bold')
        ax.set_title(get_text('journals_chart'), fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['journals_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 3. Open Access chart
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
        
        ax.set_xlabel('OA Type' if st.session_state.get('language', 'en') == 'en' else 'Тип ОА', fontsize=12, fontweight='bold')
        ax.set_ylabel('Publications' if st.session_state.get('language', 'en') == 'en' else 'Публикации', fontsize=12, fontweight='bold')
        ax.set_title(get_text('oa_chart'), fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['oa_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 4. Word Cloud
    if profile.get('concepts'):
        try:
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
            ax.set_title(get_text('wordcloud_title'), fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            images['wordcloud'] = base64.b64encode(buf.getvalue()).decode()
            plt.close()
        except:
            pass
    
    # 5. Citations chart
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
        ax.set_xlabel('Citations' if st.session_state.get('language', 'en') == 'en' else 'Цитаты', fontsize=12, fontweight='bold')
        ax.set_title(get_text('citations_chart'), fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['citations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 6. Thematic structure
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(get_text('thematic_title'), fontsize=14, fontweight='bold')
    
    if profile.get('top_domains'):
        ax = axes[0, 0]
        domains = list(profile['top_domains'].keys())[:5]
        counts = [profile['top_domains'][d] for d in domains]
        ax.bar(range(len(domains)), counts, color='#E74C3C', alpha=0.8)
        ax.set_xticks(range(len(domains)))
        ax.set_xticklabels(domains, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title('Domains', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    if profile.get('top_fields'):
        ax = axes[0, 1]
        fields = list(profile['top_fields'].keys())[:5]
        counts = [profile['top_fields'][f] for f in fields]
        ax.bar(range(len(fields)), counts, color='#3498DB', alpha=0.8)
        ax.set_xticks(range(len(fields)))
        ax.set_xticklabels(fields, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title('Fields', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    if profile.get('top_topics'):
        ax = axes[1, 0]
        topics = list(profile['top_topics'].keys())[:5]
        counts = [profile['top_topics'][t] for t in topics]
        ax.barh(range(len(topics)), counts, color='#2ECC71', alpha=0.8)
        ax.set_yticks(range(len(topics)))
        ax.set_yticklabels(topics, fontsize=9)
        ax.set_xlabel('Count', fontsize=11)
        ax.set_title('Topics', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
    
    if profile.get('top_subtopics'):
        ax = axes[1, 1]
        subtopics = list(profile['top_subtopics'].keys())[:5]
        counts = [profile['top_subtopics'][s] for s in subtopics]
        ax.barh(range(len(subtopics)), counts, color='#F39C12', alpha=0.8)
        ax.set_yticks(range(len(subtopics)))
        ax.set_yticklabels(subtopics, fontsize=9)
        ax.set_xlabel('Count', fontsize=11)
        ax.set_title('Subtopics', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
    
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    images['thematic_structure'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    # 7. Radar chart
    if profile.get('top_concepts'):
        top_concepts_items = list(profile['top_concepts'].items())[:6]
        if len(top_concepts_items) >= 3:
            try:
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
                ax.set_title('Thematic Profile (Radar)' if st.session_state.get('language', 'en') == 'en' else 'Тематический профиль (Radar)', 
                            fontsize=13, fontweight='bold', pad=20)
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                buf.seek(0)
                images['radar_chart'] = base64.b64encode(buf.getvalue()).decode()
                plt.close()
            except:
                pass
    
    return images

# ============================================================
# REPORT GENERATION
# ============================================================

def generate_html_report(profile: Dict, publications: List[Dict], images: Dict[str, str], 
                         logo_base64: Optional[str] = None) -> str:
    """Generate HTML report"""
    
    total_pubs = profile.get('total_publications', 0)
    h_index = profile.get('h_index', 0)
    total_citations = profile.get('total_citations', 0)
    oa_percentage = profile.get('oa_percentage', 0)
    trend = profile.get('trend_direction', 'unknown')
    
    risk_flags = profile.get('risk_flags', [])
    recommendation = profile.get('recommendation', 'No recommendation')
    unique_coauthors = profile.get('unique_coauthors', 0)
    
    author_name = profile.get('author_name', 'Unknown')
    author_affiliations = profile.get('author_affiliations', [])
    
    collaborations = profile.get('collaborations', {})
    domestic_papers = collaborations.get('domestic_papers', 0)
    international_papers = collaborations.get('international_papers', 0)
    
    lang = st.session_state.get('language', 'en')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Author Profile Analysis - {profile.get('orcid', '')}</title>
        <style>
            body {{ font-family: 'Times New Roman', serif; margin: 0; padding: 20px; background-color: #f5f5f5; color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }}
            .header-left {{ flex: 1; }}
            .header h1 {{ color: white; border-bottom: none; margin: 0; }}
            .header-logo {{ max-height: 80px; max-width: 200px; margin-left: 20px; }}
            h1 {{ color: #2C3E50; border-bottom: 3px solid #2C3E50; padding-bottom: 10px; }}
            h2 {{ color: #34495E; margin-top: 30px; border-bottom: 2px solid #BDC3C7; padding-bottom: 8px; }}
            .author-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2C3E50; }}
            .author-name {{ font-size: 22px; font-weight: bold; color: #2C3E50; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #2C3E50; text-align: center; }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #2C3E50; }}
            .metric-label {{ font-size: 12px; color: #7F8C8D; margin-top: 5px; }}
            .flag {{ padding: 10px; margin: 5px 0; border-radius: 5px; background-color: #FEF9E7; border-left: 4px solid #F39C12; }}
            .flag-danger {{ background-color: #FDEDEC; border-left-color: #E74C3C; }}
            .chart-container {{ margin: 20px 0; text-align: center; }}
            .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .recommendation-box {{ padding: 15px; margin: 20px 0; border-radius: 8px; font-size: 16px; font-weight: 500; }}
            .rec-green {{ background-color: #D5F5E3; border-left: 4px solid #2ECC71; }}
            .rec-yellow {{ background-color: #FEF9E7; border-left: 4px solid #F39C12; }}
            .rec-red {{ background-color: #FDEDEC; border-left: 4px solid #E74C3C; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background-color: #2C3E50; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #BDC3C7; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .doi-link {{ color: #2980B9; text-decoration: none; font-size: 12px; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #BDC3C7; text-align: center; color: #7F8C8D; font-size: 12px; }}
            .collab-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .collab-box {{ background: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #ddd; }}
            .collab-box h4 {{ margin: 0 0 8px 0; color: #2C3E50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-left">
                    <h1 style="color: white; border-bottom: none;">📊 Author Profile Analysis</h1>
                </div>
                {f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Logo">' if logo_base64 else ''}
            </div>
            
            <div class="author-info">
                <div class="author-name">{author_name}</div>
                <div><strong>ORCID:</strong> {profile.get('orcid', 'N/A')}</div>
                {f'<div><strong>Affiliations:</strong> {", ".join(author_affiliations[:5])}</div>' if author_affiliations else ''}
                <div><strong>Generated:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
                <div><strong>Total Publications Analyzed:</strong> {total_pubs}</div>
            </div>
            
            <h2>📈 Key Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card"><div class="metric-value">{total_pubs}</div><div class="metric-label">Publications</div></div>
                <div class="metric-card"><div class="metric-value">{h_index}</div><div class="metric-label">h-index</div></div>
                <div class="metric-card"><div class="metric-value">{profile.get('g_index', 0)}</div><div class="metric-label">g-index</div></div>
                <div class="metric-card"><div class="metric-value">{profile.get('i10_index', 0)}</div><div class="metric-label">i10-index</div></div>
                <div class="metric-card"><div class="metric-value">{total_citations:,}</div><div class="metric-label">Total Citations</div></div>
                <div class="metric-card"><div class="metric-value">{profile.get('average_citations', 0):.1f}</div><div class="metric-label">Avg Citations</div></div>
                <div class="metric-card"><div class="metric-value">{oa_percentage:.1f}%</div><div class="metric-label">Open Access</div></div>
                <div class="metric-card"><div class="metric-value">{unique_coauthors}</div><div class="metric-label">Unique Co-authors</div></div>
            </div>
            
            <div class="recommendation-box {'rec-green' if '🟢' in recommendation else 'rec-yellow' if '🟡' in recommendation else 'rec-red'}">
                <strong>Editor Recommendation:</strong> {recommendation}
            </div>
            
            {'<h2>⚠️ Risk Flags</h2>' if risk_flags else ''}
            {''.join([f'<div class="flag {"flag-danger" if "🔴" in flag else ""}">{flag}</div>' for flag in risk_flags])}
            
            <h2>📊 Visualizations</h2>
            {''.join([f'<div class="chart-container"><img src="data:image/png;base64,{images.get(key, "")}" alt="{key}"></div>' 
                      for key in ['years_chart', 'journals_chart', 'oa_chart'] if images.get(key)])}
            {'<div class="chart-container"><img src="data:image/png;base64,' + images.get('wordcloud', '') + '" alt="WordCloud"></div>' if images.get('wordcloud') else ''}
            {''.join([f'<div class="chart-container"><img src="data:image/png;base64,{images.get(key, "")}" alt="{key}"></div>' 
                      for key in ['citations_chart', 'thematic_structure'] if images.get(key)])}
            
            <h2>🌍 Collaboration Analysis</h2>
            <div class="collab-grid">
                <div class="collab-box">
                    <h4>Domestic Collaborations</h4>
                    <p><strong>Papers:</strong> {domestic_papers}</p>
                </div>
                <div class="collab-box">
                    <h4>International Collaborations</h4>
                    <p><strong>Papers:</strong> {international_papers}</p>
                </div>
            </div>
            <p><strong>Collaboration Index:</strong> {profile.get('collaboration_index', 0):.2f}</p>
            <p><strong>Most Collaborative Country:</strong> {profile.get('most_collaborative_country', 'None')}</p>
            
            <h2>📚 Publications List</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead><tr><th>#</th><th>Title</th><th>Year</th><th>Journal</th><th>Citations</th><th>OA</th><th>DOI</th></tr></thead>
                    <tbody>
                        {''.join([
                            f"<tr><td>{i+1}</td><td>{pub.get('title', 'No title')[:100]}</td><td>{pub.get('publication_year', 'N/A')}</td>"
                            f"<td>{pub.get('journal_name', 'Unknown')}</td><td>{pub.get('cited_by_count', 0)}</td>"
                            f"<td>{'✅' if pub.get('is_oa', False) else '❌'}</td>"
                            f"<td><a href='https://doi.org/{pub.get('doi', '')}' target='_blank' class='doi-link'>{pub.get('doi', '')}</a></td></tr>"
                            for i, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)[:50])
                        ])}
                    </tbody>
                </table>
                <p><em>Showing 50 of {len(publications)} publications</em></p>
            </div>
            
            <div class="footer">
                <p>© Author Profile Analysis / Chimica Techno Acta</p>
                <p><a href="https://chimicatechnoacta.ru" target="_blank">https://chimicatechnoacta.ru</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_pdf_report(profile: Dict, publications: List[Dict], images: Dict[str, str], 
                        filename: str = "profile_report.pdf"):
    """Generate PDF report"""
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24,
                                     textColor=colors.HexColor('#2C3E50'), alignment=TA_CENTER,
                                     spaceAfter=30, fontName='Times-Roman')
        story.append(Paragraph("Author Profile Analysis", title_style))
        
        # Author info
        author_name = profile.get('author_name', 'Unknown')
        story.append(Paragraph(f"<b>{author_name}</b>", styles['Heading2']))
        story.append(Paragraph(f"ORCID: {profile.get('orcid', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Metrics table
        metrics_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Publications', str(profile.get('total_publications', 0)), 
             'h-index', str(profile.get('h_index', 0))],
            ['g-index', str(profile.get('g_index', 0)), 
             'i10-index', str(profile.get('i10_index', 0))],
            ['Total Citations', f"{profile.get('total_citations', 0):,}", 
             'Avg Citations', f"{profile.get('average_citations', 0):.1f}"],
            ['Open Access', f"{profile.get('oa_percentage', 0):.1f}%", 
             'Active Years', str(profile.get('active_years', 0))],
        ]
        
        table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Recommendation
        rec = profile.get('recommendation', 'No recommendation')
        rec_style = ParagraphStyle('Recommendation', parent=styles['Normal'], fontSize=13,
                                   textColor=colors.HexColor('#2C3E50'), backColor=colors.HexColor('#D5F5E3'),
                                   borderPadding=10, fontName='Times-Roman')
        story.append(Paragraph(f"<b>Recommendation:</b> {rec}", rec_style))
        story.append(Spacer(1, 20))
        
        # Add images
        for img_key in ['years_chart', 'journals_chart', 'oa_chart', 'wordcloud', 'citations_chart']:
            if img_key in images and images[img_key]:
                try:
                    img_data = base64.b64decode(images[img_key])
                    img = Image(BytesIO(img_data), width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 20))
                except:
                    pass
        
        # Publications table
        story.append(PageBreak())
        story.append(Paragraph("<b>Publications</b>", styles['Heading2']))
        
        pub_data = [['#', 'Title', 'Year', 'Journal', 'Citations']]
        for i, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)[:30]):
            pub_data.append([
                str(i+1),
                pub.get('title', 'No title')[:40],
                str(pub.get('publication_year', 'N/A')),
                pub.get('journal_name', 'Unknown')[:25],
                str(pub.get('cited_by_count', 0))
            ])
        
        pub_table = Table(pub_data, colWidths=[0.3*inch, 2*inch, 0.5*inch, 1.2*inch, 0.5*inch])
        pub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(pub_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10,
                                      textColor=colors.HexColor('#7F8C8D'), alignment=TA_CENTER,
                                      fontName='Times-Roman')
        story.append(Paragraph("© Author Profile Analysis / Chimica Techno Acta", footer_style))
        story.append(Paragraph("https://chimicatechnoacta.ru", footer_style))
        
        doc.build(story)
        return True
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return False

# ============================================================
# STREAMLIT UI
# ============================================================

def init_session_state():
    """Initialize Streamlit session state"""
    defaults = {
        'language': 'en',
        'orcid': '',
        'profile_data': None,
        'publications': [],
        'analysis_complete': False,
        'logo_base64': None,
        'batch_size': 50,
        'max_publications': 1000,
        'use_cache': True,
        'show_debug': False,
        'timeout': 30,
        'max_retries': 3,
        'filters': {'year_range': (1900, 2024), 'min_citations': 0, 'journal': ''}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def language_selector():
    """Language selector in sidebar"""
    lang = st.sidebar.selectbox(
        "🌐 Language / Язык",
        options=['English', 'Русский'],
        index=0 if st.session_state.get('language', 'en') == 'en' else 1
    )
    if lang == 'English' and st.session_state.get('language') != 'en':
        st.session_state.language = 'en'
        st.rerun()
    elif lang == 'Русский' and st.session_state.get('language') != 'ru':
        st.session_state.language = 'ru'
        st.rerun()

def sidebar_controls():
    """Sidebar controls"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### {get_text('sidebar_title')}")
        
        orcid = st.text_input(
            get_text('orcid_label'),
            value=st.session_state.get('orcid', ''),
            placeholder=get_text('orcid_placeholder'),
            help=get_text('orcid_help')
        )
        st.session_state.orcid = orcid
        
        # Logo upload
        logo_file = st.file_uploader(
            get_text('logo_upload'),
            type=['png', 'jpg', 'jpeg', 'svg'],
            help=get_text('logo_help')
        )
        if logo_file:
            st.session_state.logo_base64 = base64.b64encode(logo_file.read()).decode()
        
        # Advanced settings
        with st.expander(get_text('advanced_settings')):
            st.session_state.batch_size = st.slider(
                get_text('batch_size'), 10, 100, st.session_state.batch_size
            )
            st.session_state.max_publications = st.number_input(
                get_text('max_publications'), 50, 2000, st.session_state.max_publications
            )
            st.session_state.use_cache = st.checkbox(
                get_text('use_cache'), st.session_state.use_cache
            )
            st.session_state.show_debug = st.checkbox(
                get_text('show_debug'), st.session_state.show_debug
            )
        
        # Analyze button
        analyze_btn = st.button(
            get_text('analyze_button'),
            type='primary',
            use_container_width=True
        )
        
        return analyze_btn

def display_metrics(profile: Dict):
    """Display key metrics in columns"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            get_text('total_publications'),
            profile.get('total_publications', 0)
        )
    
    with col2:
        st.metric(
            get_text('h_index'),
            profile.get('h_index', 0)
        )
    
    with col3:
        st.metric(
            get_text('total_citations'),
            f"{profile.get('total_citations', 0):,}"
        )
    
    with col4:
        st.metric(
            get_text('oa_percentage'),
            f"{profile.get('oa_percentage', 0):.1f}%"
        )
    
    # Secondary metrics
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            get_text('g_index'),
            profile.get('g_index', 0)
        )
    
    with col6:
        st.metric(
            get_text('i10_index'),
            profile.get('i10_index', 0)
        )
    
    with col7:
        st.metric(
            get_text('avg_citations'),
            f"{profile.get('average_citations', 0):.1f}"
        )
    
    with col8:
        st.metric(
            get_text('median_citations'),
            f"{profile.get('median_citations', 0):.0f}"
        )

def display_visualizations_tab(images: Dict[str, str]):
    """Display visualizations tab"""
    if not images:
        st.info("No visualizations available")
        return
    
    # Main charts
    cols = st.columns(2)
    
    chart_order = ['years_chart', 'journals_chart', 'oa_chart', 'wordcloud', 
                   'citations_chart', 'thematic_structure', 'radar_chart']
    
    for i, key in enumerate(chart_order):
        if key in images and images[key]:
            with cols[i % 2]:
                st.image(
                    f"data:image/png;base64,{images[key]}",
                    use_column_width=True
                )
                st.caption(get_text(key.replace('_chart', '').replace('_title', '').replace('_', ' ').title()))

def display_publications_tab(publications: List[Dict]):
    """Display publications tab with filters"""
    if not publications:
        st.info("No publications found")
        return
    
    # Filters
    with st.expander(get_text('filter_publications')):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            years = [p.get('publication_year') for p in publications if p.get('publication_year')]
            if years:
                min_year, max_year = min(years), max(years)
                year_range = st.slider(
                    get_text('year_range'),
                    min_year, max_year,
                    (min_year, max_year)
                )
                st.session_state.filters['year_range'] = year_range
            else:
                year_range = (1900, 2024)
        
        with col2:
            min_citations = st.number_input(
                get_text('min_citations'),
                min_value=0,
                value=st.session_state.filters.get('min_citations', 0)
            )
            st.session_state.filters['min_citations'] = min_citations
        
        with col3:
            journals = sorted(set([p.get('journal_name', '') for p in publications if p.get('journal_name')]))
            if journals:
                journal_filter = st.selectbox(
                    get_text('journal_filter'),
                    ['All'] + journals,
                    index=0
                )
                st.session_state.filters['journal'] = journal_filter if journal_filter != 'All' else ''
        
        if st.button(get_text('reset_filters')):
            st.session_state.filters = {'year_range': (1900, 2024), 'min_citations': 0, 'journal': ''}
            st.rerun()
    
    # Apply filters
    filtered = publications
    year_range = st.session_state.filters.get('year_range', (1900, 2024))
    min_citations = st.session_state.filters.get('min_citations', 0)
    journal_filter = st.session_state.filters.get('journal', '')
    
    filtered = [p for p in filtered if p.get('publication_year', 0) >= year_range[0] and p.get('publication_year', 0) <= year_range[1]]
    filtered = [p for p in filtered if p.get('cited_by_count', 0) >= min_citations]
    if journal_filter:
        filtered = [p for p in filtered if p.get('journal_name', '') == journal_filter]
    
    # Sort and display
    filtered = sorted(filtered, key=lambda x: x.get('publication_year', 0), reverse=True)
    
    df = pd.DataFrame(filtered)
    
    # Select columns for display
    display_cols = ['title', 'publication_year', 'journal_name', 'cited_by_count', 'is_oa', 'doi']
    df_display = df[display_cols].copy()
    df_display.columns = [get_text(c) for c in ['title_col', 'year_col', 'journal_col', 'citations_col', 'oa_col', 'doi_col']]
    df_display[get_text('oa_col')] = df_display[get_text('oa_col')].apply(lambda x: '✅' if x else '❌')
    
    # Make DOI clickable
    def make_doi_link(doi):
        if doi and doi != '':
            return f'<a href="https://doi.org/{doi}" target="_blank">{doi[:20]}...</a>'
        return ''
    
    df_display[get_text('doi_col')] = df_display[get_text('doi_col')].apply(make_doi_link)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            get_text('title_col'): st.column_config.TextColumn(get_text('title_col'), width='large'),
            get_text('year_col'): st.column_config.NumberColumn(get_text('year_col'), width='small'),
            get_text('journal_col'): st.column_config.TextColumn(get_text('journal_col'), width='medium'),
            get_text('citations_col'): st.column_config.NumberColumn(get_text('citations_col'), width='small'),
            get_text('oa_col'): st.column_config.TextColumn(get_text('oa_col'), width='small'),
            get_text('doi_col'): st.column_config.TextColumn(get_text('doi_col'), width='medium'),
        }
    )
    
    st.caption(f"Showing {len(filtered)} of {len(publications)} publications")

def display_collaborations_tab(profile: Dict):
    """Display collaborations tab"""
    collaborations = profile.get('collaborations', {})
    if not collaborations:
        st.info("No collaboration data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(get_text('domestic'))
        st.metric("Papers", collaborations.get('domestic_papers', 0))
        
        domestic = collaborations.get('domestic', {})
        for country, affils in list(domestic.items())[:5]:
            st.markdown(f"**📍 {country}**")
            if isinstance(affils, dict):
                for affil, count in list(affils.items())[:3]:
                    st.markdown(f"• {affil}: {count} papers")
            st.markdown("---")
    
    with col2:
        st.subheader(get_text('international'))
        st.metric("Papers", collaborations.get('international_papers', 0))
        
        international = collaborations.get('international', {})
        for country, affils in list(international.items())[:5]:
            st.markdown(f"**📍 {country}**")
            if isinstance(affils, dict):
                for affil, count in list(affils.items())[:3]:
                    st.markdown(f"• {affil}: {count} papers")
            st.markdown("---")
    
    st.markdown("---")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.metric(get_text('mixed_papers'), collaborations.get('mixed_papers', 0))
    with col4:
        st.metric(get_text('collab_index'), f"{profile.get('collaboration_index', 0):.2f}")
    with col5:
        st.metric(get_text('most_collab_country'), profile.get('most_collaborative_country', 'None'))
    
    # Institution homepages
    institution_homepages = profile.get('institution_homepages', {})
    if institution_homepages:
        st.subheader(get_text('institution_homepages'))
        for inst_id, url in list(institution_homepages.items())[:10]:
            st.markdown(f"• [{inst_id.split('/')[-1]}]({url})")
    
    # Top co-authors
    top_coauthors = profile.get('top_coauthors', {})
    coauthors_with_orcid = profile.get('coauthors_with_orcid', {})
    
    if top_coauthors:
        st.subheader(get_text('top_coauthors'))
        
        coauthor_data = []
        for author, count in list(top_coauthors.items())[:20]:
            orcid_link = coauthors_with_orcid.get(author, '')
            coauthor_data.append({
                'Author': author,
                'Collaborations': count,
                'ORCID': f'[Link](https://orcid.org/{orcid_link})' if orcid_link else ''
            })
        
        if coauthor_data:
            st.dataframe(pd.DataFrame(coauthor_data), use_container_width=True)

def display_risk_tab(profile: Dict):
    """Display risk assessment tab"""
    risk_flags = profile.get('risk_flags', [])
    recommendation = profile.get('recommendation', 'No recommendation')
    
    if risk_flags:
        st.subheader(get_text('risk_flags'))
        for flag in risk_flags:
            if '🔴' in flag:
                st.error(flag)
            elif '⚠️' in flag:
                st.warning(flag)
            else:
                st.info(flag)
    else:
        st.success(get_text('no_flags'))
    
    st.markdown("---")
    st.subheader(get_text('recommendation'))
    
    if '🟢' in recommendation:
        st.success(recommendation)
    elif '🟡' in recommendation:
        st.warning(recommendation)
    else:
        st.error(recommendation)
    
    # Additional stats
    st.markdown("---")
    st.subheader("📊 Additional Statistics")
    
    stats_data = {
        'Active Years': profile.get('active_years', 0),
        'Papers per Year': f"{profile.get('papers_per_year', 0):.1f}",
        'Trend Direction': profile.get('trend_direction', 'unknown'),
        'Thematic Diversity (Shannon)': f"{profile.get('thematic_diversity_shannon', 0):.3f}",
        'Unique Concepts': profile.get('unique_concepts', 0),
        'Retractions': profile.get('retractions', 0),
        'Corrections': profile.get('corrections', 0),
        'Unique Co-authors': profile.get('unique_coauthors', 0),
        'Domestic Collaboration Ratio': f"{profile.get('domestic_papers_ratio', 0)*100:.1f}%",
        'International Collaboration Ratio': f"{profile.get('international_papers_ratio', 0)*100:.1f}%"
    }
    
    df_stats = pd.DataFrame(list(stats_data.items()), columns=['Metric', 'Value'])
    st.dataframe(df_stats, use_container_width=True, hide_index=True)

def display_report_tab(profile: Dict, publications: List[Dict], images: Dict[str, str]):
    """Display report generation tab"""
    st.subheader("📄 Generate Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(get_text('export_html'), use_container_width=True):
            with st.spinner("Generating HTML report..."):
                html_content = generate_html_report(
                    profile, publications, images, 
                    st.session_state.get('logo_base64')
                )
                st.download_button(
                    label=f"📥 {get_text('download')} HTML",
                    data=html_content,
                    file_name=f"profile_{profile.get('orcid', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
    
    with col2:
        if st.button(get_text('export_pdf'), use_container_width=True):
            with st.spinner("Generating PDF report..."):
                filename = f"profile_{profile.get('orcid', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                if generate_pdf_report(profile, publications, images, filename):
                    with open(filename, 'rb') as f:
                        st.download_button(
                            label=f"📥 {get_text('download')} PDF",
                            data=f,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
    
    with col3:
        if st.button(get_text('export_csv'), use_container_width=True):
            df = pd.DataFrame(publications)
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"📥 {get_text('download')} CSV",
                data=csv,
                file_name=f"publications_{profile.get('orcid', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

def main():
    """Main application"""
    # Page config
    st.set_page_config(
        page_title="Author Profile Analysis",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Language selector
    language_selector()
    
    # Sidebar
    analyze_btn = sidebar_controls()
    
    # Main content
    st.title(get_text('app_title'))
    st.caption(get_text('app_subtitle'))
    
    # Show info if no analysis yet
    if not st.session_state.analysis_complete:
        st.info("👈 Enter an ORCID in the sidebar and click 'Analyze Profile' to start")
        
        # Show example
        with st.expander("📖 Example ORCIDs to try"):
            st.markdown("""
            - **Nobel Laureate**: `0000-0003-2688-6636` (Robert Langer)
            - **Materials Scientist**: `0000-0002-8126-0675` (John Rogers)
            - **Chemist**: `0000-0002-7191-5904` (George Whitesides)
            - **Physicist**: `0000-0002-8089-1376` (Mildred Dresselhaus)
            """)
        
        # Features
        with st.expander("📌 Features"):
            st.markdown("""
            ✅ **Complete Profile Analysis**: 20+ metrics (h-index, g-index, i10-index)
            ✅ **Scientific Visualizations**: Publication trends, journals, OA status
            ✅ **Collaboration Analysis**: Domestic/international collaborations with affiliations
            ✅ **Risk Assessment**: Automated risk flags and editor recommendations
            ✅ **Thematic Structure**: Domains → Fields → Topics → Subtopics → Concepts
            ✅ **Multi-format Reports**: HTML, PDF, CSV export
            ✅ **Bilingual Interface**: English and Russian
            ✅ **Caching**: Fast subsequent analyses
            """)
        
        return
    
    # Analysis complete - display results
    profile = st.session_state.profile_data
    publications = st.session_state.publications
    
    if not profile:
        st.error(get_text('no_data'))
        return
    
    # Display metrics
    display_metrics(profile)
    
    # Show recommendation
    recommendation = profile.get('recommendation', '')
    if '🟢' in recommendation:
        st.success(recommendation)
    elif '🟡' in recommendation:
        st.warning(recommendation)
    elif '🔴' in recommendation:
        st.error(recommendation)
    
    # Create visualizations if not already done
    if 'images' not in st.session_state or not st.session_state.images:
        with st.spinner("Generating visualizations..."):
            st.session_state.images = create_visualizations(profile)
    
    images = st.session_state.images
    
    # Tabs
    tab_names = get_text('tabs')
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        display_visualizations_tab(images)
    
    with tabs[1]:
        display_publications_tab(publications)
    
    with tabs[2]:
        display_collaborations_tab(profile)
    
    with tabs[3]:
        display_risk_tab(profile)
    
    with tabs[4]:
        display_report_tab(profile, publications, images)
    
    # Cache info
    with st.expander("ℹ️ Cache Information"):
        st.markdown(f"""
        - **Cache Status**: {'Enabled' if st.session_state.use_cache else 'Disabled'}
        - **Total Publications**: {len(publications)}
        - **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)

# ============================================================
# ASYNC WRAPPER FOR STREAMLIT
# ============================================================

async def run_analysis_async(orcid: str):
    """Run analysis asynchronously"""
    try:
        analyzer, profile, publications = await collect_scholar_data(orcid)
        return analyzer, profile, publications
    except Exception as e:
        st.error(get_text('error').format(error=str(e)))
        return None, None, []

def run_analysis(orcid: str):
    """Run analysis with proper async handling"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        with st.spinner(get_text('analyzing')):
            status_text = st.empty()
            
            status_text.info(get_text('fetching_orcid'))
            analyzer, profile, publications = loop.run_until_complete(
                collect_scholar_data(orcid)
            )
            
            if not profile or not publications:
                st.error(get_text('no_data'))
                return
            
            status_text.success(get_text('analysis_complete'))
            
            # Store results
            st.session_state.profile_data = profile
            st.session_state.publications = publications
            st.session_state.analysis_complete = True
            st.session_state.images = None  # Will be regenerated
            
            # Save ORCID for future
            st.session_state.orcid = orcid
            
            st.rerun()
            
    except Exception as e:
        st.error(get_text('error').format(error=str(e)))
        if st.session_state.show_debug:
            st.exception(e)
    finally:
        loop.close()

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Check if analyze button was clicked
    if st.session_state.get('orcid') and st.sidebar.button(
        get_text('analyze_button'), 
        type='primary', 
        use_container_width=True,
        key='analyze_main'
    ):
        orcid = clean_orcid(st.session_state.orcid)
        if orcid:
            run_analysis(orcid)
        else:
            st.error("Invalid ORCID format")
    
    main()
