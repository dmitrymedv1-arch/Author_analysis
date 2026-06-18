"""
🔬 Author Profile Analyzer
Полный анализ профиля ученого по ORCID с научными визуализациями

Автор: daM / Chimica Techno Acta
Версия: 2.0 (Streamlit)
"""

import streamlit as st
import pandas as pd
import numpy as np
import asyncio
import aiohttp
import json
import os
import re
import time
import hashlib
import base64
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Set, Optional, Tuple, Any
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import nest_asyncio

# Применяем nest_asyncio для работы в Jupyter/Streamlit
nest_asyncio.apply()

# ============================================
# КОНФИГУРАЦИЯ STREAMLIT
# ============================================

st.set_page_config(
    page_title="Author Profile Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# КАСТОМНЫЙ CSS (НАУЧНЫЙ СТИЛЬ)
# ============================================

st.markdown("""
<style>
    /* Основные стили */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .main-header h1 {
        color: white;
        font-family: 'Times New Roman', serif;
        font-weight: bold;
        margin: 0;
    }
    
    .main-header p {
        color: #a8d8ea;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Метрики */
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 4px solid #2C3E50;
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.12);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1a1a2e;
        font-family: 'Times New Roman', serif;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #7F8C8D;
        margin-top: 0.3rem;
        font-family: 'Times New Roman', serif;
    }
    
    .metric-icon {
        font-size: 1.8rem;
        float: right;
        opacity: 0.7;
    }
    
    /* Карточки коллабораций */
    .collab-box {
        background: #f8f9fa;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        margin: 0.5rem 0;
    }
    
    .collab-box h4 {
        color: #1a1a2e;
        margin: 0 0 0.5rem 0;
        font-family: 'Times New Roman', serif;
        font-weight: bold;
    }
    
    .collab-country {
        font-weight: bold;
        color: #2C3E50;
        margin-top: 0.5rem;
        font-size: 0.95rem;
    }
    
    .collab-affil {
        margin-left: 1.5rem;
        font-size: 0.9rem;
        color: #555;
        padding: 0.1rem 0;
    }
    
    .collab-affil strong {
        color: #1a1a2e;
    }
    
    /* Флаги риска */
    .risk-flag {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        margin: 0.3rem 0;
        font-family: 'Times New Roman', serif;
        font-size: 0.95rem;
    }
    
    .risk-danger {
        background-color: #FDEDEC;
        border-left: 4px solid #E74C3C;
    }
    
    .risk-warning {
        background-color: #FEF9E7;
        border-left: 4px solid #F39C12;
    }
    
    .risk-info {
        background-color: #EBF5FB;
        border-left: 4px solid #3498DB;
    }
    
    /* Рекомендация */
    .recommendation-box {
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 500;
        font-family: 'Times New Roman', serif;
        margin: 1rem 0;
        border: 1px solid rgba(0,0,0,0.1);
    }
    
    .rec-green {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
    }
    
    .rec-yellow {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 4px solid #ffc107;
    }
    
    .rec-red {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 4px solid #dc3545;
    }
    
    /* Информация об авторе */
    .author-info {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border: 1px solid #dee2e6;
    }
    
    .author-name {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1a1a2e;
        font-family: 'Times New Roman', serif;
    }
    
    .author-detail {
        color: #495057;
        font-size: 0.95rem;
        margin-top: 0.3rem;
    }
    
    .author-detail strong {
        color: #1a1a2e;
    }
    
    /* Таблицы */
    .stDataFrame {
        font-family: 'Times New Roman', serif;
    }
    
    /* Прогресс-бар */
    .stProgress > div > div {
        background-color: #2C3E50;
    }
    
    /* Кастомные кнопки */
    .stButton > button {
        background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
        color: white;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(44, 62, 80, 0.3);
    }
    
    /* Сайдбар */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Тематическая структура */
    .thematic-list {
        columns: 2;
        column-gap: 2rem;
    }
    
    .thematic-list li {
        break-inside: avoid;
        margin-bottom: 0.3rem;
        font-family: 'Times New Roman', serif;
    }
    
    /* Адаптивность */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 1.5rem;
        }
        .thematic-list {
            columns: 1;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ПАРАМЕТРЫ (из секции с возможностью настройки)
# ============================================

class Config:
    """Конфигурация приложения"""
    # API параметры
    BATCH_SIZE = 50
    MAX_RETRIES = 3
    TIMEOUT = 30
    DELAY_BETWEEN_BATCHES = 0.5
    MAX_CONCURRENT_REQUESTS = 10
    RETRY_DELAY = 2
    
    # Параметры анализа
    MAX_PUBLICATIONS_TO_ANALYZE = 1000
    MIN_YEAR_FOR_TREND = 5
    
    # Параметры отчета
    SHOW_DEBUG_LOGS = False
    GENERATE_HTML_REPORT = True
    GENERATE_PDF_REPORT = True
    USE_CACHE = True
    
    @classmethod
    def update_from_session(cls):
        """Обновляет конфигурацию из session state"""
        if 'config' in st.session_state:
            for key, value in st.session_state.config.items():
                if hasattr(cls, key):
                    setattr(cls, key, value)

# Инициализация конфига в session state
if 'config' not in st.session_state:
    st.session_state.config = {
        'BATCH_SIZE': 50,
        'MAX_RETRIES': 3,
        'TIMEOUT': 30,
        'USE_CACHE': True,
        'MAX_PUBLICATIONS_TO_ANALYZE': 1000,
        'SHOW_DEBUG_LOGS': False
    }

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def clean_orcid(orcid_input: str) -> str:
    """Очищает ORCID от лишних символов"""
    if not orcid_input:
        return ""
    
    orcid = orcid_input.strip().upper()
    
    if 'orcid.org/' in orcid:
        orcid = orcid.split('orcid.org/')[-1]
    
    orcid = re.sub(r'[^0-9X-]', '', orcid)
    
    if re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', orcid):
        return orcid
    
    if len(orcid) == 16 and orcid.isdigit():
        return f"{orcid[:4]}-{orcid[4:8]}-{orcid[8:12]}-{orcid[12:]}"
    
    return orcid

def normalize_author_name(name: str) -> str:
    """Нормализует имя автора"""
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

def extract_country_from_affiliation(affiliation: str) -> str:
    """Извлекает страну из аффилиации"""
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

def safe_get(data, *keys, default=None):
    """Безопасное получение значения из вложенного словаря"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def chunks(lst, n):
    """Разбивает список на куски"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ============================================
# КЭШИРОВАНИЕ (улучшенное)
# ============================================

class CacheManager:
    """Управление кэшированием с TTL и валидацией"""
    
    CACHE_DIR = "cache"
    CACHE_TTL = 7  # дней
    
    @classmethod
    def _ensure_cache_dir(cls):
        """Создает директорию для кэша"""
        if not os.path.exists(cls.CACHE_DIR):
            os.makedirs(cls.CACHE_DIR)
    
    @classmethod
    def _get_cache_path(cls, orcid: str) -> str:
        """Возвращает путь к файлу кэша"""
        cls._ensure_cache_dir()
        orcid_clean = clean_orcid(orcid)
        return f"{cls.CACHE_DIR}/{orcid_clean}.json"
    
    @classmethod
    def _get_cache_key(cls, orcid: str, params: dict = None) -> str:
        """Генерирует ключ для кэша"""
        key = clean_orcid(orcid)
        if params:
            key += "_" + hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
        return key
    
    @classmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_cached_profile(_cls, orcid: str) -> Optional[Dict]:
        """Загружает профиль из кэша с TTL"""
        cache_path = _cls._get_cache_path(orcid)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Проверяем валидность
                if _cls._is_cache_valid(data):
                    return data
                else:
                    # Кэш устарел
                    os.remove(cache_path)
                    return None
                    
            except Exception as e:
                return None
        
        return None
    
    @classmethod
    def save_to_cache(cls, orcid: str, data: Dict):
        """Сохраняет данные в кэш"""
        if not Config.USE_CACHE:
            return
        
        cache_path = cls._get_cache_path(orcid)
        try:
            # Добавляем метаданные
            data['_cache_metadata'] = {
                'timestamp': datetime.now().isoformat(),
                'orcid': clean_orcid(orcid),
                'version': '2.0'
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            pass  # Тихая ошибка кэша
    
    @classmethod
    def _is_cache_valid(cls, data: Dict) -> bool:
        """Проверяет валидность кэша"""
        if '_cache_metadata' not in data:
            return False
        
        metadata = data['_cache_metadata']
        if 'timestamp' not in metadata:
            return False
        
        try:
            cache_time = datetime.fromisoformat(metadata['timestamp'])
            age = (datetime.now() - cache_time).days
            return age < cls.CACHE_TTL
        except:
            return False
    
    @classmethod
    def clear_cache(cls, orcid: str = None):
        """Очищает кэш"""
        if orcid:
            cache_path = cls._get_cache_path(orcid)
            if os.path.exists(cache_path):
                os.remove(cache_path)
        else:
            import shutil
            if os.path.exists(cls.CACHE_DIR):
                shutil.rmtree(cls.CACHE_DIR)
            os.makedirs(cls.CACHE_DIR)

# ============================================
# API КЛИЕНТЫ
# ============================================

class ORCIDClient:
    """Клиент для работы с ORCID API"""
    
    BASE_URL = "https://pub.orcid.org/v3.0"
    
    @classmethod
    async def get_works(cls, orcid: str, session: aiohttp.ClientSession) -> Set[str]:
        """Получает список DOI из ORCID"""
        orcid = clean_orcid(orcid)
        
        if not orcid:
            return set()
        
        headers = {'Accept': 'application/json'}
        url = f"{cls.BASE_URL}/{orcid}/works"
        
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

class OpenAlexClient:
    """Клиент для работы с OpenAlex API"""
    
    BASE_URL = "https://api.openalex.org"
    
    @classmethod
    async def get_works_metadata(cls, dois: List[str], session: aiohttp.ClientSession) -> List[Dict]:
        """Получает метаданные по DOI"""
        if not dois:
            return []
        
        doi_query = '|'.join(dois[:50])
        
        params = {
            'filter': f'doi:{doi_query}',
            'per-page': len(dois)
        }
        
        url = f"{cls.BASE_URL}/works"
        data = await fetch_with_retry(session, url, params=params)
        
        if not data:
            return []
        
        return data.get('results', [])
    
    @classmethod
    async def get_author(cls, orcid: str, session: aiohttp.ClientSession) -> Dict:
        """Получает информацию об авторе"""
        if not orcid:
            return {}
        
        orcid_clean = clean_orcid(orcid)
        
        params = {
            'filter': f'orcid:{orcid_clean}',
            'per-page': 1
        }
        
        url = f"{cls.BASE_URL}/authors"
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

async def fetch_with_retry(session, url, params=None, headers=None, method='GET'):
    """Выполняет запрос с повторными попытками"""
    max_retries = Config.MAX_RETRIES
    retry_delay = Config.RETRY_DELAY
    timeout = Config.TIMEOUT
    
    for attempt in range(max_retries):
        try:
            async with session.request(method, url, params=params, headers=headers, timeout=timeout) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', retry_delay * (attempt + 1)))
                    await asyncio.sleep(retry_after)
                    continue
                
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                return None
    return None

# ============================================
# ПАРСИНГ ПУБЛИКАЦИЙ
# ============================================

def parse_openalex_publication(item: Dict) -> Optional[Dict]:
    """Парсит публикацию из OpenAlex"""
    try:
        pub = {}
        
        # Базовая информация
        pub['id'] = item.get('id', '')
        pub['doi'] = item.get('doi', '').replace('https://doi.org/', '')
        pub['title'] = item.get('title', 'No title')
        pub['publication_year'] = item.get('publication_year')
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
        
        # Аффилиации и институты
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
        
        # Авторы
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
        
        # Тематика
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
        
        # Топики
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
        
        # Концепты
        pub['keywords'] = [k.get('display_name', '') for k in item.get('keywords', []) if k.get('display_name')]
        
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
        
        # Цитаты
        pub['cited_by_count'] = item.get('cited_by_count', 0)
        pub['cited_by_percentile'] = item.get('cited_by_percentile', {})
        
        # Ретракции
        pub['is_retracted'] = item.get('is_retracted', False)
        pub['is_correction'] = item.get('is_correction', False)
        pub['is_paratext'] = item.get('is_paratext', False)
        
        if pub['is_retracted']:
            pub['retraction_info'] = item.get('retraction_info', {})
        
        return pub
        
    except Exception:
        return None

# ============================================
# КЛАСС АНАЛИЗАТОРА
# ============================================

class ScholarProfileAnalyzer:
    """Анализирует профиль ученого"""
    
    def __init__(self, orcid: str):
        self.orcid = clean_orcid(orcid)
        self.publications = []
        self.author_info = {}
        self.author_name = None
        self.author_affiliations = []
        self.author_countries = []
        self.profile = {}
        self.raw_data = {}
        self.collaborations = {
            'domestic': defaultdict(lambda: defaultdict(int)),
            'international': defaultdict(lambda: defaultdict(int)),
            'domestic_papers': 0,
            'international_papers': 0,
            'mixed_papers': 0,
            'total_collaborations': 0
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
    
    def analyze_publications(self):
        """Выполняет полный анализ публикаций"""
        if not self.publications:
            st.warning("Нет публикаций для анализа")
            return
        
        # Базовая информация
        self.profile['total_publications'] = len(self.publications)
        self.profile['orcid'] = self.orcid
        self.profile['author_name'] = self.author_name or 'Unknown'
        self.profile['author_affiliations'] = self.author_affiliations
        self.profile['author_countries'] = self.author_countries
        
        # Распределение по годам
        years = [p.get('publication_year') for p in self.publications if p.get('publication_year')]
        self.profile['years_distribution'] = dict(Counter(years))
        self.profile['first_publication'] = min(years) if years else None
        self.profile['last_publication'] = max(years) if years else None
        self.profile['active_years'] = len(set(years)) if years else 0
        
        # Журналы
        journals = [p.get('journal_name') for p in self.publications if p.get('journal_name')]
        self.profile['journals'] = dict(Counter(journals))
        self.profile['top_journals'] = dict(Counter(journals).most_common(10))
        
        # Издательства
        publishers = [p.get('publisher') for p in self.publications if p.get('publisher') and p.get('publisher') != 'Unknown']
        self.profile['publishers'] = dict(Counter(publishers))
        
        # Типы публикаций
        pub_types = [p.get('type') for p in self.publications if p.get('type')]
        self.profile['publication_types'] = dict(Counter(pub_types))
        
        # Открытый доступ
        oa_statuses = [p.get('open_access_status') for p in self.publications if p.get('open_access_status')]
        self.profile['open_access'] = dict(Counter(oa_statuses))
        self.profile['total_oa'] = sum(1 for p in self.publications if p.get('is_oa', False))
        self.profile['oa_percentage'] = (self.profile['total_oa'] / len(self.publications) * 100) if self.publications else 0
        
        # Аффилиации
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
        
        # Страны
        countries = [p.get('country') for p in self.publications if p.get('country')]
        self.profile['countries'] = dict(Counter(countries))
        
        # Концепты
        all_concepts = []
        all_fields = []
        all_domains = []
        all_topics = []
        all_subtopics = []
        concept_levels = {}
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
            
            if p.get('primary_topic'):
                pt = p['primary_topic']
                if pt.get('display_name'):
                    all_primary_topics.append(pt['display_name'])
            
            if p.get('topics'):
                for t in p['topics']:
                    if t.get('display_name'):
                        all_primary_topics.append(t['display_name'])
                    if t.get('subfield'):
                        all_fields.append(t['subfield'])
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
        self.profile['keywords'] = dict(Counter(all_keywords))
        self.profile['top_keywords'] = dict(Counter(all_keywords).most_common(20))
        
        # Ретракции
        self.profile['retractions'] = sum(1 for p in self.publications if p.get('is_retracted', False))
        self.profile['corrections'] = sum(1 for p in self.publications if p.get('is_correction', False))
        self.profile['paratexts'] = sum(1 for p in self.publications if p.get('is_paratext', False))
        
        # Соавторы
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
        
        # Количество авторов
        author_counts = [p.get('author_count', 0) for p in self.publications if p.get('author_count', 0) > 0]
        if author_counts:
            self.profile['avg_authors_per_paper'] = np.mean(author_counts)
            self.profile['median_authors_per_paper'] = np.median(author_counts)
            self.profile['max_authors_per_paper'] = max(author_counts)
            self.profile['min_authors_per_paper'] = min(author_counts)
        
        # Цитаты
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
        
        # Топ цитируемые
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
        
        # Тренд
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
        
        # Продуктивность
        self.profile['papers_per_year'] = len(self.publications) / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        self.profile['recent_productivity'] = len([y for y in years if y >= (datetime.now().year - 3)]) / 3 if years else 0
        self.profile['productivity_peak_year'] = max(year_counts.items(), key=lambda x: x[1])[0] if year_counts else None
        self.profile['productivity_peak_count'] = max(year_counts.values()) if year_counts else 0
        
        # Тематическое разнообразие
        if all_concepts:
            concept_counts = Counter(all_concepts)
            total = len(all_concepts)
            shannon_index = 0
            for count in concept_counts.values():
                p = count / total
                shannon_index -= p * np.log(p)
            self.profile['thematic_diversity_shannon'] = shannon_index
            self.profile['unique_concepts'] = len(concept_counts)
        
        # Анализ коллабораций
        self._analyze_collaborations()
        
        # Риски и рекомендации
        self.profile['risk_flags'] = self._assess_risks()
        self.profile['recommendation'] = self._generate_recommendation()
    
    def _analyze_collaborations(self):
        """Анализирует коллаборации"""
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
        
        for p in self.publications:
            institutions = p.get('institutions', [])
            if not institutions:
                continue
            
            paper_countries = set()
            
            for inst in institutions:
                country = inst.get('country_code', '')
                if country and country != 'Unknown':
                    paper_countries.add(country)
            
            if not paper_countries:
                continue
            
            has_author_country = any(c in author_countries_set for c in paper_countries)
            has_other_countries = any(c not in author_countries_set for c in paper_countries)
            
            if has_author_country and not has_other_countries:
                self.collaborations['domestic_papers'] += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country in author_countries_set and affil_name:
                        self.collaborations['domestic'][country][affil_name] += 1
                        
            elif has_author_country and has_other_countries:
                self.collaborations['mixed_papers'] += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country in author_countries_set and affil_name:
                        self.collaborations['domestic'][country][affil_name] += 1
                    elif country not in author_countries_set and country and affil_name:
                        self.collaborations['international'][country][affil_name] += 1
                        
            elif has_other_countries and not has_author_country:
                self.collaborations['international_papers'] += 1
                for inst in institutions:
                    country = inst.get('country_code', '')
                    affil_name = inst.get('display_name', '')
                    if country and country not in author_countries_set and affil_name:
                        self.collaborations['international'][country][affil_name] += 1
        
        self.collaborations['total_collaborations'] = (
            self.collaborations['domestic_papers'] + 
            self.collaborations['international_papers'] + 
            self.collaborations['mixed_papers']
        )
        
        self.profile['collaborations'] = self.collaborations
        self.profile['domestic_papers_ratio'] = self.collaborations['domestic_papers'] / len(self.publications) if self.publications else 0
        self.profile['international_papers_ratio'] = self.collaborations['international_papers'] / len(self.publications) if self.publications else 0
        self.profile['collaboration_index'] = self.profile.get('avg_authors_per_paper', 0) - 1 if self.profile.get('avg_authors_per_paper', 0) > 0 else 0
    
    def _assess_risks(self) -> List[str]:
        """Оценивает риски"""
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
        """Генерирует рекомендацию"""
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
        return self.profile
    
    def get_publications(self) -> List[Dict]:
        return self.publications

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ СБОРА ДАННЫХ
# ============================================

async def collect_scholar_data(orcid: str, progress_callback=None) -> Tuple[ScholarProfileAnalyzer, Dict, List[Dict]]:
    """Собирает все данные для профиля"""
    
    orcid_clean = clean_orcid(orcid)
    
    if not orcid_clean:
        st.error("❌ Неверный формат ORCID")
        return None, {}, []
    
    # Проверка кэша
    if Config.USE_CACHE:
        cached_data = CacheManager.get_cached_profile(orcid_clean)
        if cached_data:
            if progress_callback:
                progress_callback("📦 Использую данные из кэша...", 0.5)
            
            analyzer = ScholarProfileAnalyzer(orcid_clean)
            
            if 'publications' in cached_data:
                for pub in cached_data['publications']:
                    analyzer.add_publication(pub)
            
            if 'author_info' in cached_data:
                analyzer.set_author_info(cached_data['author_info'])
            
            if 'profile' in cached_data:
                analyzer.profile = cached_data['profile']
            
            return analyzer, analyzer.profile, analyzer.publications
    
    analyzer = ScholarProfileAnalyzer(orcid_clean)
    
    async with aiohttp.ClientSession() as session:
        
        # Шаг 1: Информация об авторе
        if progress_callback:
            progress_callback("🔍 Получение информации об авторе...", 0.1)
        
        author_info = await OpenAlexClient.get_author(orcid_clean, session)
        if author_info:
            analyzer.set_author_info(author_info)
        
        # Шаг 2: DOI из ORCID
        if progress_callback:
            progress_callback("📚 Получение списка публикаций из ORCID...", 0.2)
        
        orcid_dois = await ORCIDClient.get_works(orcid_clean, session)
        
        if not orcid_dois:
            st.warning("Не найдено DOI в профиле ORCID")
            return analyzer, {}, []
        
        all_dois = list(orcid_dois)
        total_dois = len(all_dois)
        
        if total_dois > Config.MAX_PUBLICATIONS_TO_ANALYZE:
            all_dois = all_dois[:Config.MAX_PUBLICATIONS_TO_ANALYZE]
        
        # Шаг 3: Метаданные из OpenAlex
        if progress_callback:
            progress_callback(f"📊 Получение метаданных из OpenAlex ({len(all_dois)} публикаций)...", 0.3)
        
        all_metadata = []
        doi_batches = list(chunks(all_dois, Config.BATCH_SIZE))
        
        for idx, batch in enumerate(doi_batches):
            batch_metadata = await OpenAlexClient.get_works_metadata(batch, session)
            all_metadata.extend(batch_metadata)
            
            if progress_callback:
                progress = 0.3 + (idx / len(doi_batches)) * 0.4
                progress_callback(
                    f"📊 Обработано {min((idx+1)*Config.BATCH_SIZE, len(all_dois))} из {len(all_dois)} публикаций...",
                    progress
                )
            
            await asyncio.sleep(Config.DELAY_BETWEEN_BATCHES)
        
        # Шаг 4: Парсинг
        if progress_callback:
            progress_callback("🔄 Обработка публикаций...", 0.7)
        
        for item in all_metadata:
            pub_data = parse_openalex_publication(item)
            if pub_data:
                analyzer.add_publication(pub_data)
        
        # Шаг 5: Анализ
        if progress_callback:
            progress_callback("📈 Выполнение анализа...", 0.85)
        
        analyzer.analyze_publications()
        
        # Шаг 6: Кэширование
        if Config.USE_CACHE:
            cache_data = {
                'publications': analyzer.publications,
                'author_info': analyzer.author_info,
                'profile': analyzer.profile,
                'timestamp': datetime.now().isoformat()
            }
            CacheManager.save_to_cache(orcid_clean, cache_data)
        
        if progress_callback:
            progress_callback("✅ Анализ завершен!", 1.0)
        
        return analyzer, analyzer.profile, analyzer.publications

# ============================================
# ВИЗУАЛИЗАЦИИ
# ============================================

def create_figure_publication_timeline(profile: Dict):
    """Создает интерактивный график публикаций"""
    if not profile.get('years_distribution'):
        return None
    
    years = sorted(profile['years_distribution'].keys())
    counts = [profile['years_distribution'][y] for y in years]
    
    fig = go.Figure()
    
    # Бары
    fig.add_trace(go.Bar(
        x=years,
        y=counts,
        name='Publications',
        marker=dict(
            color='#2E86AB',
            line=dict(color='black', width=1)
        ),
        hovertemplate='<b>Year:</b> %{x}<br><b>Publications:</b> %{y}<extra></extra>'
    ))
    
    # Тренд
    if len(years) >= 3:
        x = np.arange(len(years))
        z = np.polyfit(x, counts, 1)
        trend_line = z[0] * x + z[1]
        
        fig.add_trace(go.Scatter(
            x=years,
            y=trend_line,
            mode='lines',
            name='Trend',
            line=dict(color='#E74C3C', width=2.5, dash='dash'),
            hovertemplate='<b>Trend:</b> %{y:.1f}<extra></extra>'
        ))
        
        # Доверительный интервал
        if len(counts) > 3:
            std_err = np.std(counts - trend_line) / np.sqrt(len(counts))
            fig.add_trace(go.Scatter(
                x=years + years[::-1],
                y=(trend_line + 1.96*std_err).tolist() + (trend_line - 1.96*std_err)[::-1].tolist(),
                fill='toself',
                fillcolor='rgba(231, 76, 60, 0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Confidence interval',
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        title=dict(
            text='<b>Publication Activity Over Time</b>',
            font=dict(size=16, family='Times New Roman, serif')
        ),
        xaxis=dict(
            title='Year',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)',
            tickangle=-45
        ),
        yaxis=dict(
            title='Number of Publications',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)',
            dtick=1 if max(counts) < 10 else None
        ),
        template='plotly_white',
        hovermode='x unified',
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='black',
            borderwidth=1
        ),
        margin=dict(l=60, r=40, t=60, b=60),
        height=400
    )
    
    return fig

def create_figure_metric_cards(profile: Dict):
    """Создает метрики для отображения"""
    metrics = [
        ('📚', 'Total Publications', profile.get('total_publications', 0), 'publications'),
        ('📊', 'h-index', profile.get('h_index', 0), 'h-index'),
        ('📈', 'g-index', profile.get('g_index', 0), 'g-index'),
        ('⭐', 'i10-index', profile.get('i10_index', 0), 'i10-index'),
        ('📖', 'Total Citations', f"{profile.get('total_citations', 0):,}", 'citations'),
        ('📊', 'Avg Citations', f"{profile.get('average_citations', 0):.1f}", 'avg_citations'),
        ('🌐', 'Open Access', f"{profile.get('oa_percentage', 0):.1f}%", 'oa'),
        ('🤝', 'Coauthors', profile.get('unique_coauthors', 0), 'coauthors')
    ]
    
    return metrics

def create_figure_top_journals(profile: Dict):
    """Создает график топ журналов"""
    if not profile.get('top_journals'):
        return None
    
    journals = list(profile['top_journals'].keys())[:10]
    counts = list(profile['top_journals'].values())[:10]
    
    # Сортировка
    sorted_pairs = sorted(zip(counts, journals), reverse=True)
    counts, journals = zip(*sorted_pairs)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=journals,
        x=counts,
        orientation='h',
        marker=dict(
            color=counts,
            colorscale='Viridis',
            line=dict(color='black', width=0.5)
        ),
        text=counts,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Publications: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Top Journals by Publication Count</b>',
            font=dict(size=16, family='Times New Roman, serif')
        ),
        xaxis=dict(
            title='Number of Publications',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title='Journal',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)'
        ),
        template='plotly_white',
        margin=dict(l=120, r=60, t=60, b=40),
        height=400
    )
    
    return fig

def create_figure_open_access(profile: Dict):
    """Создает график открытого доступа"""
    if not profile.get('open_access'):
        return None
    
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
    labels = []
    values = []
    colors = []
    
    for oa_type in oa_order:
        if oa_type in oa_data:
            labels.append(oa_labels.get(oa_type, oa_type))
            values.append(oa_data[oa_type])
            colors.append(oa_colors.get(oa_type, '#95A5A6'))
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            textinfo='label+percent',
            textposition='outside',
            hoverinfo='label+value+percent',
            hole=0.3
        )
    ])
    
    fig.update_layout(
        title=dict(
            text='<b>Open Access Status</b>',
            font=dict(size=16, family='Times New Roman, serif')
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40),
        height=400
    )
    
    return fig

def create_figure_wordcloud(profile: Dict):
    """Создает облако слов"""
    if not profile.get('concepts'):
        return None
    
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        max_words=50,
        contour_width=1,
        contour_color='black',
        random_state=42
    ).generate_from_frequencies(profile['concepts'])
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Key Research Concepts', fontsize=14, fontweight='bold', pad=20, fontfamily='serif')
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    
    plt.close()
    
    return base64.b64encode(buf.getvalue()).decode()

def create_figure_citations_distribution(profile: Dict):
    """Создает распределение цитирований"""
    if not profile.get('citation_distribution'):
        return None
    
    dist = profile['citation_distribution']
    filtered_dist = {k: v for k, v in dist.items() if v > 0}
    
    ranges = list(filtered_dist.keys())
    counts = list(filtered_dist.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=ranges,
        y=counts,
        marker=dict(
            color='#8E44AD',
            line=dict(color='black', width=1)
        ),
        text=counts,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Papers: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Citation Distribution</b>',
            font=dict(size=16, family='Times New Roman, serif')
        ),
        xaxis=dict(
            title='Citation Range',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title='Number of Papers',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)'
        ),
        template='plotly_white',
        margin=dict(l=60, r=40, t=60, b=60),
        height=400
    )
    
    return fig

def create_figure_collaboration_countries(profile: Dict):
    """Создает график стран-участников коллабораций"""
    collaborations = profile.get('collaborations', {})
    
    if not collaborations:
        return None
    
    domestic = collaborations.get('domestic', {})
    international = collaborations.get('international', {})
    
    all_countries = {}
    for country in domestic:
        all_countries[country] = all_countries.get(country, 0) + sum(domestic[country].values())
    for country in international:
        all_countries[country] = all_countries.get(country, 0) + sum(international[country].values())
    
    if not all_countries:
        return None
    
    countries = list(all_countries.keys())
    counts = list(all_countries.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=countries,
        y=counts,
        marker=dict(
            color=counts,
            colorscale='Plasma',
            line=dict(color='black', width=0.5)
        ),
        text=counts,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Collaborations: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Collaborations by Country</b>',
            font=dict(size=16, family='Times New Roman, serif')
        ),
        xaxis=dict(
            title='Country',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title='Number of Collaborations',
            title_font=dict(size=13, family='Times New Roman, serif'),
            tickfont=dict(size=11, family='Times New Roman, serif'),
            gridcolor='rgba(0,0,0,0.05)'
        ),
        template='plotly_white',
        margin=dict(l=60, r=40, t=60, b=60),
        height=400
    )
    
    return fig

def create_figure_radar(profile: Dict):
    """Создает radar chart для тематического профиля"""
    if not profile.get('top_concepts'):
        return None
    
    top_concepts_items = list(profile['top_concepts'].items())[:6]
    if len(top_concepts_items) < 3:
        return None
    
    categories = [item[0][:20] for item in top_concepts_items]
    values = [item[1] for item in top_concepts_items]
    
    # Нормализация
    max_val = max(values) if values else 1
    normalized = [v / max_val * 100 for v in values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized + [normalized[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='Profile',
        line=dict(color='#2C3E50', width=2),
        fillcolor='rgba(52, 152, 219, 0.3)',
        hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=9, family='Times New Roman, serif'),
                gridcolor='rgba(0,0,0,0.1)'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, family='Times New Roman, serif', weight='bold'),
                gridcolor='rgba(0,0,0,0.1)'
            ),
            bgcolor='rgba(255,255,255,0)'
        ),
        title=dict(
            text='<b>Thematic Profile</b>',
            font=dict(size=16, family='Times New Roman, serif')
        ),
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=40),
        height=450
    )
    
    return fig

# ============================================
# ГЕНЕРАЦИЯ ОТЧЕТОВ
# ============================================

def generate_html_report(profile: Dict, publications: List[Dict], images: Dict[str, str]) -> str:
    """Генерирует HTML отчет"""
    
    total_pubs = profile.get('total_publications', 0)
    h_index = profile.get('h_index', 0)
    g_index = profile.get('g_index', 0)
    i10_index = profile.get('i10_index', 0)
    total_citations = profile.get('total_citations', 0)
    author_name = profile.get('author_name', 'Unknown')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Author Profile - {author_name}</title>
        <style>
            body {{ font-family: 'Times New Roman', serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .header {{ background: #1a1a2e; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
            .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #1a1a2e; }}
            .metric-label {{ font-size: 12px; color: #7F8C8D; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background: #1a1a2e; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7F8C8D; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 Author Profile Analysis</h1>
                <p><strong>{author_name}</strong> | ORCID: {profile.get('orcid', 'N/A')}</p>
                <p>Generated: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{total_pubs}</div>
                    <div class="metric-label">Publications</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{h_index}</div>
                    <div class="metric-label">h-index</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{g_index}</div>
                    <div class="metric-label">g-index</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{total_citations:,}</div>
                    <div class="metric-label">Total Citations</div>
                </div>
            </div>
            
            <h2>Recommendation</h2>
            <div style="padding: 15px; background: #d4edda; border-radius: 8px; margin: 10px 0;">
                {profile.get('recommendation', 'No recommendation')}
            </div>
            
            <h2>Publications</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Title</th>
                        <th>Year</th>
                        <th>Journal</th>
                        <th>Citations</th>
                        <th>OA</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"""
                        <tr>
                            <td>{i+1}</td>
                            <td>{pub.get('title', 'No title')[:80]}</td>
                            <td>{pub.get('publication_year', 'N/A')}</td>
                            <td>{pub.get('journal_name', 'Unknown')}</td>
                            <td>{pub.get('cited_by_count', 0)}</td>
                            <td>{'✅' if pub.get('is_oa', False) else '❌'}</td>
                        </tr>
                        """
                        for i, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)[:50])
                    ])}
                </tbody>
            </table>
            
            <div class="footer">
                <p>© Author Profile Analyzer | Created by daM</p>
                <p><a href="https://chimicatechnoacta.ru">https://chimicatechnoacta.ru</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_pdf_report(profile: Dict, publications: List[Dict], filename: str = "profile_report.pdf"):
    """Генерирует PDF отчет"""
    
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Times-Roman'
        )
        
        story.append(Paragraph("Author Profile Analysis", title_style))
        story.append(Spacer(1, 10))
        
        # Автор
        author_name = profile.get('author_name', 'Unknown')
        story.append(Paragraph(f"<b>{author_name}</b>", styles['Heading2']))
        story.append(Paragraph(f"ORCID: {profile.get('orcid', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Метрики в таблице
        metrics_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Total Publications', str(profile.get('total_publications', 0)), 
             'h-index', str(profile.get('h_index', 0))],
            ['g-index', str(profile.get('g_index', 0)), 
             'i10-index', str(profile.get('i10_index', 0))],
            ['Total Citations', f"{profile.get('total_citations', 0):,}", 
             'Avg Citations', f"{profile.get('average_citations', 0):.1f}"],
            ['Open Access', f"{profile.get('oa_percentage', 0):.1f}%", 
             'Unique Coauthors', str(profile.get('unique_coauthors', 0))]
        ]
        
        table = Table(metrics_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Рекомендация
        rec = profile.get('recommendation', 'No recommendation')
        rec_style = ParagraphStyle(
            'Recommendation',
            parent=styles['Normal'],
            fontSize=11,
            backColor=colors.HexColor('#d4edda'),
            borderPadding=10,
            borderRadius=5,
            fontName='Times-Roman'
        )
        story.append(Paragraph(f"<b>Recommendation:</b> {rec}", rec_style))
        story.append(Spacer(1, 20))
        
        # Список публикаций
        story.append(Paragraph("<b>Top Publications</b>", styles['Heading2']))
        
        for i, pub in enumerate(sorted(publications, key=lambda x: x.get('cited_by_count', 0), reverse=True)[:10], 1):
            story.append(Paragraph(
                f"{i}. {pub.get('title', 'No title')[:80]} "
                f"({pub.get('publication_year', 'N/A')}) - "
                f"{pub.get('journal_name', 'Unknown')} - "
                f"Citations: {pub.get('cited_by_count', 0)}",
                styles['Normal']
            ))
            story.append(Spacer(1, 5))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_CENTER,
            fontName='Times-Roman'
        )
        story.append(Paragraph("© Author Profile Analyzer | Created by daM", footer_style))
        story.append(Paragraph("https://chimicatechnoacta.ru", footer_style))
        
        doc.build(story)
        return filename
        
    except Exception as e:
        st.warning(f"PDF generation failed: {str(e)}")
        return None

# ============================================
# ОСНОВНОЙ ИНТЕРФЕЙС STREAMLIT
# ============================================

def main():
    """Главная функция приложения"""
    
    # Заголовок
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Author Profile Analyzer</h1>
        <p>Полный анализ профиля ученого по ORCID с научными визуализациями</p>
        <p style="font-size: 0.9rem; opacity: 0.7;">v2.0 | Developed by daM / Chimica Techno Acta</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Сайдбар с настройками
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        with st.expander("🔧 API Settings", expanded=True):
            st.session_state.config['USE_CACHE'] = st.checkbox(
                "Use cache",
                value=st.session_state.config['USE_CACHE'],
                help="Cache results for faster subsequent analysis"
            )
            
            st.session_state.config['MAX_PUBLICATIONS_TO_ANALYZE'] = st.number_input(
                "Max publications",
                min_value=100,
                max_value=5000,
                value=st.session_state.config['MAX_PUBLICATIONS_TO_ANALYZE'],
                step=100,
                help="Maximum number of publications to analyze"
            )
            
            st.session_state.config['BATCH_SIZE'] = st.slider(
                "Batch size",
                min_value=10,
                max_value=100,
                value=st.session_state.config['BATCH_SIZE'],
                step=10,
                help="Number of requests per batch"
            )
        
        with st.expander("📄 Report Settings"):
            st.session_state.config['SHOW_DEBUG_LOGS'] = st.checkbox(
                "Show debug logs",
                value=st.session_state.config['SHOW_DEBUG_LOGS'],
                help="Display detailed debug information"
            )
        
        if st.button("🗑️ Clear Cache", use_container_width=True):
            CacheManager.clear_cache()
            st.success("Cache cleared!")
        
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.8rem; color: #7F8C8D;">
            <b>About</b><br>
            Analyzes publication profiles using<br>
            ORCID and OpenAlex APIs.<br><br>
            <b>Features:</b><br>
            • 20+ research metrics<br>
            • Scientific visualizations<br>
            • Collaboration analysis<br>
            • Thematic profiling<br>
            • Risk assessment
        </div>
        """, unsafe_allow_html=True)
    
    # Основной контент
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        orcid_input = st.text_input(
            "🔍 Enter ORCID",
            placeholder="0000-0002-1234-567X or https://orcid.org/0000-0002-1234-567X",
            help="Enter ORCID in any format (with or without URL)"
        )
    
    with col2:
        analyze_btn = st.button(
            "🚀 Analyze Profile",
            type="primary",
            use_container_width=True,
            disabled=not orcid_input
        )
    
    with col3:
        if 'profile_data' in st.session_state and st.session_state.profile_data:
            if st.button("📥 Export Report", use_container_width=True):
                st.info("Use the download buttons below after analysis")
    
    # Состояние анализа
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = None
    
    # Запуск анализа
    if analyze_btn and orcid_input and not st.session_state.analysis_running:
        st.session_state.analysis_running = True
        
        # Прогресс
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        progress_bar = progress_placeholder.progress(0)
        
        def update_progress(message: str, value: float):
            status_placeholder.info(f"🔄 {message}")
            progress_bar.progress(value)
        
        try:
            # Запуск асинхронного сбора
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            analyzer, profile, publications = loop.run_until_complete(
                collect_scholar_data(orcid_input, update_progress)
            )
            
            if profile:
                st.session_state.profile_data = {
                    'analyzer': analyzer,
                    'profile': profile,
                    'publications': publications
                }
                st.success("✅ Analysis completed successfully!")
                
                # Очищаем прогресс
                progress_placeholder.empty()
                status_placeholder.empty()
                
                # Показываем результаты
                display_results(profile, publications)
            else:
                st.warning("⚠️ No data found. Please check the ORCID.")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if Config.SHOW_DEBUG_LOGS:
                import traceback
                st.code(traceback.format_exc())
        
        finally:
            st.session_state.analysis_running = False
    
    # Если данные уже загружены, показываем их
    elif st.session_state.profile_data:
        profile = st.session_state.profile_data['profile']
        publications = st.session_state.profile_data['publications']
        display_results(profile, publications)

def display_results(profile: Dict, publications: List[Dict]):
    """Отображает результаты анализа"""
    
    # Tabs
    tabs = st.tabs([
        "📊 Overview",
        "📈 Publications",
        "🌍 Collaborations",
        "🏷️ Topics",
        "📚 Publications List"
    ])
    
    with tabs[0]:
        display_overview(profile)
    
    with tabs[1]:
        display_publication_metrics(profile)
    
    with tabs[2]:
        display_collaborations(profile)
    
    with tabs[3]:
        display_topics(profile)
    
    with tabs[4]:
        display_publications_list(publications)
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download HTML Report", use_container_width=True):
            html_content = generate_html_report(profile, publications, {})
            st.download_button(
                label="Click to download HTML",
                data=html_content,
                file_name=f"profile_{clean_orcid(profile.get('orcid', ''))}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
    
    with col2:
        if st.button("📥 Download PDF Report", use_container_width=True):
            pdf_file = generate_pdf_report(profile, publications)
            if pdf_file and os.path.exists(pdf_file):
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
                st.download_button(
                    label="Click to download PDF",
                    data=pdf_data,
                    file_name=f"profile_{clean_orcid(profile.get('orcid', ''))}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

def display_overview(profile: Dict):
    """Отображает обзор профиля"""
    
    # Информация об авторе
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="author-info">
            <div class="author-name">{profile.get('author_name', 'Unknown')}</div>
            <div class="author-detail"><strong>ORCID:</strong> {profile.get('orcid', 'N/A')}</div>
            {f'<div class="author-detail"><strong>Affiliations:</strong> {", ".join(profile.get("author_affiliations", [])[:3])}</div>' if profile.get('author_affiliations') else ''}
            {f'<div class="author-detail"><strong>Countries:</strong> {", ".join(profile.get("author_countries", []))}</div>' if profile.get('author_countries') else ''}
            <div class="author-detail"><strong>Active Years:</strong> {profile.get('active_years', 0)} ({profile.get('first_publication', 'N/A')} - {profile.get('last_publication', 'N/A')})</div>
            <div class="author-detail"><strong>Analysis Date:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Рекомендация
        rec = profile.get('recommendation', 'No recommendation')
        rec_class = 'rec-green'
        if '🟡' in rec:
            rec_class = 'rec-yellow'
        elif '🔴' in rec:
            rec_class = 'rec-red'
        
        st.markdown(f"""
        <div class="recommendation-box {rec_class}">
            <strong>💡 Editor Recommendation</strong><br>
            {rec}
        </div>
        """, unsafe_allow_html=True)
        
        # Флаги риска
        risk_flags = profile.get('risk_flags', [])
        if risk_flags:
            st.markdown("**⚠️ Risk Flags**")
            for flag in risk_flags:
                flag_class = 'risk-danger' if '🔴' in flag else 'risk-warning'
                st.markdown(f'<div class="risk-flag {flag_class}">{flag}</div>', unsafe_allow_html=True)
    
    # Метрики
    st.markdown("### 📊 Key Metrics")
    
    metrics = [
        ('📚', 'Publications', profile.get('total_publications', 0)),
        ('📊', 'h-index', profile.get('h_index', 0)),
        ('📈', 'g-index', profile.get('g_index', 0)),
        ('⭐', 'i10-index', profile.get('i10_index', 0)),
        ('📖', 'Citations', f"{profile.get('total_citations', 0):,}"),
        ('📊', 'Avg Citations', f"{profile.get('average_citations', 0):.1f}"),
        ('🌐', 'Open Access', f"{profile.get('oa_percentage', 0):.1f}%"),
        ('🤝', 'Coauthors', profile.get('unique_coauthors', 0))
    ]
    
    cols = st.columns(4)
    for idx, (icon, label, value) in enumerate(metrics):
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Тренд
    st.markdown("### 📈 Publication Trend")
    trend = profile.get('trend_direction', 'unknown')
    trend_corr = profile.get('trend_correlation', 0)
    trend_text = {
        'strong_up': '🚀 Strongly increasing',
        'up': '📈 Increasing',
        'stable': '➡️ Stable',
        'down': '📉 Decreasing',
        'strong_down': '🔻 Strongly decreasing'
    }.get(trend, 'Unknown')
    
    st.info(f"**Trend:** {trend_text} (R² = {trend_corr**2:.3f})")
    
    # График публикаций по годам
    fig = create_figure_publication_timeline(profile)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

def display_publication_metrics(profile: Dict):
    """Отображает метрики публикаций"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Топ журналов
        fig = create_figure_top_journals(profile)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Открытый доступ
        fig = create_figure_open_access(profile)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Распределение цитирований
        fig = create_figure_citations_distribution(profile)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Самые цитируемые
        most_cited = profile.get('most_cited', [])
        if most_cited:
            st.markdown("### 📖 Most Cited Papers")
            for i, paper in enumerate(most_cited[:5], 1):
                st.markdown(f"""
                **{i}. {paper.get('title', 'No title')}**  
                *{paper.get('journal', 'Unknown')}* ({paper.get('year', 'N/A')})  
                📊 {paper.get('citations', 0)} citations
                """)

def display_collaborations(profile: Dict):
    """Отображает анализ коллабораций"""
    
    collaborations = profile.get('collaborations', {})
    
    if not collaborations:
        st.info("No collaboration data available")
        return
    
    # Статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Domestic Papers",
            collaborations.get('domestic_papers', 0)
        )
    
    with col2:
        st.metric(
            "International Papers",
            collaborations.get('international_papers', 0)
        )
    
    with col3:
        st.metric(
            "Mixed Papers",
            collaborations.get('mixed_papers', 0)
        )
    
    with col4:
        st.metric(
            "Collaboration Index",
            f"{profile.get('collaboration_index', 0):.2f}"
        )
    
    # График по странам
    fig = create_figure_collaboration_countries(profile)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Детальные коллаборации
    col1, col2 = st.columns(2)
    
    domestic = collaborations.get('domestic', {})
    international = collaborations.get('international', {})
    
    with col1:
        st.markdown("### 🇷🇺 Domestic Collaborations")
        if domestic:
            for country, affils in list(domestic.items())[:5]:
                st.markdown(f'<div class="collab-country">📍 {country}</div>', unsafe_allow_html=True)
                if isinstance(affils, dict):
                    for affil, count in list(affils.items())[:5]:
                        st.markdown(f'<div class="collab-affil">• <strong>{affil}</strong>: {count} papers</div>', unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No domestic collaborations found")
    
    with col2:
        st.markdown("### 🌐 International Collaborations")
        if international:
            for country, affils in list(international.items())[:5]:
                st.markdown(f'<div class="collab-country">📍 {country}</div>', unsafe_allow_html=True)
                if isinstance(affils, dict):
                    for affil, count in list(affils.items())[:5]:
                        st.markdown(f'<div class="collab-affil">• <strong>{affil}</strong>: {count} papers</div>', unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No international collaborations found")

def display_topics(profile: Dict):
    """Отображает тематическую структуру"""
    
    st.markdown("### 🏷️ Thematic Structure")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Domains
        if profile.get('top_domains'):
            st.markdown("**Domains (Top 5)**")
            for domain, count in list(profile['top_domains'].items())[:5]:
                st.markdown(f"• {domain}: {count}")
            st.markdown("---")
        
        # Fields
        if profile.get('top_fields'):
            st.markdown("**Fields (Top 10)**")
            for field, count in list(profile['top_fields'].items())[:10]:
                st.markdown(f"• {field}: {count}")
            st.markdown("---")
    
    with col2:
        # Topics
        if profile.get('top_primary_topics'):
            st.markdown("**Primary Topics (Top 10)**")
            for topic, count in list(profile['top_primary_topics'].items())[:10]:
                st.markdown(f"• {topic}: {count}")
            st.markdown("---")
        
        # Keywords
        if profile.get('top_keywords'):
            st.markdown("**Key Concepts (Top 20)**")
            keywords_html = " ".join([
                f'<span style="background: #f0f0f0; padding: 3px 8px; border-radius: 12px; margin: 3px; display: inline-block; font-size: 0.9rem;">{k} ({v})</span>'
                for k, v in list(profile['top_keywords'].items())[:20]
            ])
            st.markdown(keywords_html, unsafe_allow_html=True)
    
    # Radar chart
    fig = create_figure_radar(profile)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Shannon diversity
    if profile.get('thematic_diversity_shannon'):
        st.info(f"**Thematic Diversity (Shannon Index):** {profile['thematic_diversity_shannon']:.3f}")

def display_publications_list(publications: List[Dict]):
    """Отображает список публикаций"""
    
    if not publications:
        st.info("No publications found")
        return
    
    # Конвертируем в DataFrame для отображения
    df_data = []
    for pub in sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True):
        df_data.append({
            'Title': pub.get('title', 'No title')[:80],
            'Year': pub.get('publication_year', 'N/A'),
            'Journal': pub.get('journal_name', 'Unknown'),
            'Citations': pub.get('cited_by_count', 0),
            'OA': '✅' if pub.get('is_oa', False) else '❌',
            'DOI': pub.get('doi', '')
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Title': st.column_config.TextColumn('Title', width='medium'),
            'Year': st.column_config.NumberColumn('Year', width='small'),
            'Journal': st.column_config.TextColumn('Journal', width='medium'),
            'Citations': st.column_config.NumberColumn('Citations', width='small'),
            'OA': st.column_config.TextColumn('OA', width='small'),
            'DOI': st.column_config.LinkColumn('DOI', width='medium')
        }
    )
    
    st.caption(f"Total publications: {len(publications)}")

# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == "__main__":
    main()
