# app.py
# ============================================
# AUTHOR PROFILE ANALYSIS - STREAMLIT APPLICATION
# ============================================
# Full-featured application for analyzing researcher profiles
# using ORCID and OpenAlex APIs with advanced analytics
# ============================================

import streamlit as st
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from wordcloud import WordCloud
from io import BytesIO
import base64
import re
import time
from datetime import datetime
import json
from typing import List, Set, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import hashlib
import os
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from matplotlib.ticker import MaxNLocator
import nest_asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# PDF support
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

# Apply asyncio for Colab/Jupyter compatibility
nest_asyncio.apply()

# ============================================
# CONFIGURATION
# ============================================

# Default settings
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
DEFAULT_DELAY_BETWEEN_BATCHES = 0.5
DEFAULT_MAX_PUBLICATIONS = 1000
DEFAULT_USE_CACHE = True

# Language strings
LANGUAGES = {
    'en': {
        'app_title': '🔬 Author Profile Analysis',
        'app_subtitle': 'Advanced ORCID-based Researcher Analytics',
        'sidebar_title': '⚙️ Analysis Settings',
        'orcid_label': 'ORCID ID',
        'orcid_placeholder': '0000-0002-1234-567X or https://orcid.org/...',
        'orcid_help': 'Enter ORCID in any format (with or without URL)',
        'upload_logo': 'Upload Journal Logo',
        'upload_logo_help': 'Optional logo for reports (PNG, JPG, SVG)',
        'advanced_settings': '⚙️ Advanced Settings',
        'batch_size': 'Batch Size',
        'max_publications': 'Max Publications',
        'use_cache': 'Use Cache',
        'analyze_button': '🔍 Analyze Profile',
        'analyzing': '🔄 Analyzing profile...',
        'analysis_complete': '✅ Analysis Complete!',
        'error': '❌ Error',
        'no_data': 'No data found. Please check ORCID.',
        'total_publications': '📚 Publications',
        'h_index': '📈 h-index',
        'citations': '📊 Citations',
        'oa_percentage': '🌐 Open Access',
        'tabs': {
            'overview': '📊 Overview',
            'publications': '📋 Publications',
            'collaborations': '🤝 Collaborations',
            'visualizations': '📈 Visualizations',
            'risk_assessment': '⚠️ Risk Assessment',
            'export': '📄 Export'
        },
        'metrics': {
            'total_pubs': 'Total Publications',
            'h_index': 'h-index',
            'g_index': 'g-index',
            'i10_index': 'i10-index',
            'total_citations': 'Total Citations',
            'avg_citations': 'Avg Citations',
            'median_citations': 'Median Citations',
            'oa_percentage': 'Open Access',
            'active_years': 'Active Years',
            'papers_per_year': 'Papers/Year',
            'unique_coauthors': 'Unique Coauthors',
            'trend': 'Trend',
            'retractions': 'Retractions',
            'corrections': 'Corrections',
            'domestic_collab': 'Domestic Collaboration',
            'international_collab': 'International Collaboration',
            'collaboration_index': 'Collaboration Index',
            'thematic_diversity': 'Thematic Diversity (Shannon)'
        },
        'risk_flags': 'Risk Flags',
        'recommendation': 'Editor Recommendation',
        'export_html': '📄 Export HTML',
        'export_pdf': '📑 Export PDF',
        'export_csv': '📊 Export CSV',
        'download': 'Download',
        'close': 'Close'
    },
    'ru': {
        'app_title': '🔬 Анализ профиля ученого',
        'app_subtitle': 'Продвинутая аналитика исследователей на основе ORCID',
        'sidebar_title': '⚙️ Настройки анализа',
        'orcid_label': 'ORCID ID',
        'orcid_placeholder': '0000-0002-1234-567X или https://orcid.org/...',
        'orcid_help': 'Введите ORCID в любом формате (с URL или без)',
        'upload_logo': 'Загрузить логотип журнала',
        'upload_logo_help': 'Опциональный логотип для отчетов (PNG, JPG, SVG)',
        'advanced_settings': '⚙️ Расширенные настройки',
        'batch_size': 'Размер батча',
        'max_publications': 'Макс. публикаций',
        'use_cache': 'Использовать кэш',
        'analyze_button': '🔍 Анализировать профиль',
        'analyzing': '🔄 Выполняется анализ...',
        'analysis_complete': '✅ Анализ завершен!',
        'error': '❌ Ошибка',
        'no_data': 'Данные не найдены. Проверьте ORCID.',
        'total_publications': '📚 Публикации',
        'h_index': '📈 h-индекс',
        'citations': '📊 Цитирования',
        'oa_percentage': '🌐 Открытый доступ',
        'tabs': {
            'overview': '📊 Обзор',
            'publications': '📋 Публикации',
            'collaborations': '🤝 Коллаборации',
            'visualizations': '📈 Визуализации',
            'risk_assessment': '⚠️ Оценка рисков',
            'export': '📄 Экспорт'
        },
        'metrics': {
            'total_pubs': 'Всего публикаций',
            'h_index': 'h-индекс',
            'g_index': 'g-индекс',
            'i10_index': 'i10-индекс',
            'total_citations': 'Всего цитирований',
            'avg_citations': 'Среднее цитирований',
            'median_citations': 'Медиана цитирований',
            'oa_percentage': 'Открытый доступ',
            'active_years': 'Активных лет',
            'papers_per_year': 'Статей/год',
            'unique_coauthors': 'Уникальных соавторов',
            'trend': 'Тренд',
            'retractions': 'Ретракций',
            'corrections': 'Коррекций',
            'domestic_collab': 'Внутристрановые коллаборации',
            'international_collab': 'Международные коллаборации',
            'collaboration_index': 'Индекс коллабораций',
            'thematic_diversity': 'Тематическое разнообразие (Shannon)'
        },
        'risk_flags': 'Флаги риска',
        'recommendation': 'Рекомендация редактора',
        'export_html': '📄 Экспорт HTML',
        'export_pdf': '📑 Экспорт PDF',
        'export_csv': '📊 Экспорт CSV',
        'download': 'Скачать',
        'close': 'Закрыть'
    }
}

# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_text(key: str, lang: str = 'en') -> str:
    """Get localized text"""
    try:
        keys = key.split('.')
        text = LANGUAGES[lang]
        for k in keys:
            text = text[k]
        return text
    except:
        return key

def clean_orcid(orcid_input: str) -> str:
    """Clean ORCID from extra characters"""
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
    """Extract country from affiliation string"""
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
    return name

def safe_get(data, *keys, default=None):
    """Safe get from nested dict"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def format_boolean(value: bool) -> str:
    return "✅" if value else "❌"

def chunks(lst, n):
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
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'figure.facecolor': 'white',
        'figure.constrained_layout.use': True,
        'figure.figsize': (8, 6),
        'lines.linewidth': 2,
        'lines.markersize': 7,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })

# ============================================
# API FUNCTIONS
# ============================================

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_with_retry(session, url, params=None, headers=None, method='GET', timeout=30):
    """Fetch with retry mechanism"""
    try:
        async with session.request(method, url, params=params, headers=headers, timeout=timeout) as response:
            if response.status == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                await asyncio.sleep(retry_after)
                raise Exception("Rate limit")
            if response.status == 200:
                return await response.json()
            return None
    except Exception as e:
        raise e

async def get_orcid_dois(orcid: str, session) -> Set[str]:
    """Get DOI list from ORCID profile"""
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
    except Exception as e:
        pass
    
    return dois

async def get_openalex_metadata(dois: List[str], session, batch_size: int = 50) -> List[Dict]:
    """Get metadata from OpenAlex for DOIs"""
    if not dois:
        return []
    
    all_results = []
    for batch in chunks(dois, batch_size):
        doi_query = '|'.join(batch)
        params = {
            'filter': f'doi:{doi_query}',
            'per-page': len(batch)
        }
        url = "https://api.openalex.org/works"
        
        data = await fetch_with_retry(session, url, params=params)
        if data:
            all_results.extend(data.get('results', []))
        await asyncio.sleep(0.5)
    
    return all_results

async def get_openalex_author(orcid: str, session) -> Dict:
    """Get author info from OpenAlex"""
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
    """Get institution homepages from OpenAlex"""
    if not institution_ids:
        return {}
    
    unique_ids = list(set([id for id in institution_ids if id]))
    if not unique_ids:
        return {}
    
    homepages = {}
    for batch in chunks(unique_ids, 50):
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

# ============================================
# DATA PARSING
# ============================================

def parse_openalex_publication(item: Dict) -> Dict:
    """Parse OpenAlex publication with extended info"""
    try:
        pub = {}
        pub['id'] = item.get('id', '')
        pub['doi'] = item.get('doi', '').replace('https://doi.org/', '')
        pub['title'] = item.get('title', 'No title')
        pub['publication_year'] = item.get('publication_year')
        pub['type'] = item.get('type', 'unknown')
        
        # Journal info
        if item.get('primary_location'):
            source = item['primary_location'].get('source', {})
            pub['journal_name'] = source.get('display_name', 'Unknown')
            pub['publisher'] = source.get('host_organization_name') or source.get('publisher', 'Unknown')
            pub['issn'] = source.get('issn', [])
        else:
            pub['journal_name'] = 'Unknown'
            pub['publisher'] = 'Unknown'
            pub['issn'] = []
        
        # Open access
        oa = item.get('open_access', {})
        pub['is_oa'] = oa.get('is_oa', False)
        pub['open_access_status'] = oa.get('oa_status', 'closed')
        pub['oa_url'] = oa.get('oa_url', None)
        
        # Affiliations
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
        
        # Topics
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
        
        # Concepts
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
        
        # Citations
        pub['cited_by_count'] = item.get('cited_by_count', 0)
        pub['cited_by_percentile'] = item.get('cited_by_percentile', {})
        
        # Retractions
        pub['is_retracted'] = item.get('is_retracted', False)
        pub['is_correction'] = item.get('is_correction', False)
        pub['is_paratext'] = item.get('is_paratext', False)
        
        if pub['is_retracted']:
            pub['retraction_info'] = item.get('retraction_info', {})
        
        pub['publication_date'] = item.get('publication_date')
        pub['created_date'] = item.get('created_date')
        pub['updated_date'] = item.get('updated_date')
        
        return pub
    except Exception:
        return None

# ============================================
# ANALYZER CLASS
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
        
        if not self.author_affiliations and self.publications:
            for pub in self.publications:
                if pub.get('affiliations'):
                    for aff in pub['affiliations']:
                        if aff not in self.author_affiliations:
                            self.author_affiliations.append(aff)
                    if pub.get('country') and pub['country'] not in self.author_countries:
                        self.author_countries.append(pub['country'])
    
    def set_institution_homepages(self, homepages: Dict[str, str]):
        self.institution_homepages = homepages
    
    def analyze_publications(self):
        """Analyze all publications and build profile"""
        if not self.publications:
            return
        
        # Basic info
        self.profile['total_publications'] = len(self.publications)
        self.profile['orcid'] = self.orcid
        self.profile['author_name'] = self.author_name or 'Unknown'
        self.profile['author_affiliations'] = self.author_affiliations
        self.profile['author_countries'] = self.author_countries
        
        # Year distribution
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
        
        # Publication types
        pub_types = [p.get('type') for p in self.publications if p.get('type')]
        self.profile['publication_types'] = dict(Counter(pub_types))
        
        # Open access
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
            self.profile['max_authors_per_paper'] = max(author_counts)
            self.profile['min_authors_per_paper'] = min(author_counts)
        
        # Citations
        citations = [p.get('cited_by_count', 0) for p in self.publications]
        self.profile['total_citations'] = sum(citations)
        self.profile['average_citations'] = sum(citations) / len(citations) if citations else 0
        self.profile['median_citations'] = np.median(citations) if citations else 0
        self.profile['max_citations'] = max(citations) if citations else 0
        self.profile['citations_per_year'] = self.profile['total_citations'] / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        
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
        
        # Productivity
        self.profile['papers_per_year'] = len(self.publications) / self.profile['active_years'] if self.profile['active_years'] > 0 else 0
        
        # OA types
        oa_types = {'gold': 0, 'green': 0, 'hybrid': 0, 'bronze': 0, 'closed': 0}
        for p in self.publications:
            status = p.get('open_access_status', 'closed')
            if status in oa_types:
                oa_types[status] += 1
        self.profile['oa_types'] = oa_types
        
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
        """Analyze collaborations with detailed affiliations"""
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
        """Assess risks and return warnings"""
        flags = []
        
        if self.profile.get('papers_per_year', 0) > 30:
            flags.append("⚠️ Abnormally high productivity (>30 papers/year)")
        
        if self.profile.get('retractions', 0) > 1:
            flags.append(f"🔴 {self.profile['retractions']} retractions in profile")
        
        if self.profile.get('top_journals'):
            top_ratio = list(self.profile['top_journals'].values())[0] / self.profile['total_publications']
            if top_ratio > 0.3:
                flags.append("⚠️ >30% publications in one journal")
        
        suspicious_journals = ['Cureus', 'PLoS ONE', 'Scientific Reports']
        suspicious_pubs = [j for j in self.profile.get('journals', {}).keys() if any(s in j for s in suspicious_journals)]
        if suspicious_pubs:
            flags.append(f"⚠️ Publications in journals with low selectivity: {', '.join(suspicious_pubs[:3])}")
        
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
            return "🟢 Early-career researcher. Requires thorough peer review."
        else:
            return "🟢 Junior researcher. Papers require careful review."
    
    def get_profile_data(self) -> Dict:
        return self.profile
    
    def get_publications(self) -> List[Dict]:
        return self.publications

# ============================================
# DATA COLLECTION
# ============================================

async def collect_scholar_data(orcid: str, batch_size: int = DEFAULT_BATCH_SIZE, max_publications: int = DEFAULT_MAX_PUBLICATIONS) -> Tuple[Optional[ScholarProfileAnalyzer], Dict, List[Dict]]:
    """Collect all data for scholar profile"""
    
    orcid_clean = clean_orcid(orcid)
    if not orcid_clean:
        return None, {}, []
    
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
        if len(all_dois) > max_publications:
            all_dois = all_dois[:max_publications]
        
        # Get metadata from OpenAlex
        all_metadata = await get_openalex_metadata(all_dois, session, batch_size)
        
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
        
        return analyzer, analyzer.profile, analyzer.publications

# ============================================
# VISUALIZATION FUNCTIONS
# ============================================

def create_visualizations(profile: Dict) -> Dict[str, str]:
    """Create visualizations in scientific style"""
    images = {}
    apply_scientific_style()
    
    # 1. Publications by year
    if profile.get('years_distribution'):
        fig, ax = plt.subplots(figsize=(10, 6))
        years = sorted(profile['years_distribution'].keys())
        counts = [profile['years_distribution'][y] for y in years]
        
        bars = ax.bar(years, counts, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                   f'{count}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('Publication Year', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Publications', fontsize=12, fontweight='bold')
        ax.set_title('Publication Activity Dynamics', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_xticks(years)
        ax.set_xticklabels([str(int(y)) for y in years], rotation=45)
        
        if len(years) >= 2:
            x = np.arange(len(years))
            z = np.polyfit(x, counts, 1)
            p = np.poly1d(z)
            ax.plot(years, p(x), 'r-', linewidth=2.5, alpha=0.8, label='Trend')
            
            if len(counts) > 3:
                std_err = np.std(counts - p(x)) / np.sqrt(len(counts))
                ax.fill_between(years, p(x) - 1.96*std_err, p(x) + 1.96*std_err,
                               alpha=0.15, color='red', label='Confidence Interval')
            
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
    
    # 2. Top journals
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
        ax.set_xlabel('Number of Publications', fontsize=12, fontweight='bold')
        ax.set_title('Top Journals', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['journals_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 3. Open Access
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
        
        ax.set_xlabel('Open Access Type', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Publications', fontsize=12, fontweight='bold')
        ax.set_title('Open Access Status', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['oa_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 4. Word cloud
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
        ax.set_title('Key Research Concepts', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['wordcloud'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 5. Citation distribution
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
        ax.set_xlabel('Citation Range', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Papers', fontsize=12, fontweight='bold')
        ax.set_title('Citation Distribution', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['citation_distribution'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 6. Top cited papers
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
        ax.set_xlabel('Number of Citations', fontsize=12, fontweight='bold')
        ax.set_title('Most Cited Papers', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['citations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    return images

# ============================================
# HTML REPORT GENERATION
# ============================================

def generate_html_report(profile: Dict, publications: List[Dict], images: Dict[str, str], logo_base64: Optional[str] = None) -> str:
    """Generate HTML report"""
    
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
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Author Profile - ORCID {profile.get('orcid', '')}</title>
        <style>
            body {{
                font-family: 'Times New Roman', 'DejaVu Serif', serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            .header-left {{
                flex: 1;
            }}
            .header-logo {{
                max-height: 80px;
                max-width: 200px;
                margin-left: 20px;
            }}
            .header h1 {{
                color: white;
                border-bottom: none;
                margin: 0;
            }}
            h1 {{
                font-family: 'Times New Roman', serif;
                color: #2C3E50;
                border-bottom: 3px solid #2C3E50;
                padding-bottom: 10px;
            }}
            h2 {{
                font-family: 'Times New Roman', serif;
                color: #34495E;
                margin-top: 30px;
                border-bottom: 2px solid #BDC3C7;
                padding-bottom: 8px;
            }}
            .author-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-left: 4px solid #2C3E50;
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
                border-left: 4px solid #2C3E50;
                text-align: center;
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
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: 'Times New Roman', serif;
            }}
            th {{
                background-color: #2C3E50;
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-left">
                    <h1 style="color: white; border-bottom: none;">📊 Author Profile</h1>
                </div>
                {f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Logo">' if logo_base64 else ''}
            </div>
            
            <div class="author-info">
                <div class="author-name">{author_name}</div>
                <div class="author-affil"><strong>ORCID:</strong> {profile.get('orcid', 'N/A')}</div>
                {f'<div class="author-affil"><strong>Affiliations:</strong> {", ".join(author_affiliations[:5])}</div>' if author_affiliations else ''}
                {f'<div class="author-affil"><strong>Countries:</strong> {", ".join(author_countries)}</div>' if author_countries else ''}
                <div class="author-affil"><strong>Generated:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
                <div class="author-affil"><strong>Total Publications Analyzed:</strong> {total_pubs}</div>
            </div>
            
            <h2>📈 Key Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_pubs}</div>
                    <div class="metric-label">Total Publications</div>
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
                    <div class="metric-label">Total Citations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_citations:.1f}</div>
                    <div class="metric-label">Avg Citations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{median_citations:.0f}</div>
                    <div class="metric-label">Median Citations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{oa_percentage:.1f}%</div>
                    <div class="metric-label">Open Access</div>
                </div>
            </div>
            
            <div class="recommendation-box {
                'rec-green' if '🟢' in recommendation else 
                'rec-yellow' if '🟡' in recommendation else 
                'rec-red'
            }">
                <strong>Editor Recommendation:</strong> {recommendation}
            </div>
            
            {'<h2>⚠️ Risk Flags</h2>' if risk_flags else ''}
            {''.join([f'<div class="flag {"flag-danger" if "🔴" in flag else ""}">{flag}</div>' for flag in risk_flags])}
            
            <h2>📊 Visualizations</h2>
            
            <div class="chart-container">
                <img src="data:image/png;base64,{images.get('years_chart', '')}" alt="Publications by Year">
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="Top Journals">
                </div>
                <div class="chart-container">
                    <img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="Open Access">
                </div>
            </div>
            
            <div class="chart-container">
                <img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="Word Cloud">
            </div>
            
            <div class="chart-container">
                <img src="data:image/png;base64,{images.get('citations_chart', '')}" alt="Most Cited">
            </div>
            
            <div class="chart-container">
                <img src="data:image/png;base64,{images.get('citation_distribution', '')}" alt="Citation Distribution">
            </div>
            
            <h2>🌍 Collaboration Analysis</h2>
            
            <div class="collab-grid">
                <div class="collab-box">
                    <h4>🇺🇳 Domestic Collaborations</h4>
                    <p><strong>Papers:</strong> {domestic_papers}</p>
                    {''.join([
                        f'<div class="collab-country">📍 {country}</div>' +
                        ''.join([
                            f'<div class="collab-affil-item">• <strong>{affil}</strong>: {count} papers</div>'
                            for affil, count in list(affils.items())[:10]
                        ])
                        for country, affils in list(domestic_collab.items())
                    ]) if domestic_collab else '<p>No data</p>'}
                </div>
                <div class="collab-box">
                    <h4>🌐 International Collaborations</h4>
                    <p><strong>Papers:</strong> {international_papers}</p>
                    {''.join([
                        f'<div class="collab-country">📍 {country}</div>' +
                        ''.join([
                            f'<div class="collab-affil-item">• <strong>{affil}</strong>: {count} papers</div>'
                            for affil, count in list(affils.items())[:10]
                        ])
                        for country, affils in list(international_collab.items())
                    ]) if international_collab else '<p>No data</p>'}
                </div>
            </div>
            
            <div class="collab-box" style="margin-top: 10px;">
                <p><strong>Mixed Papers:</strong> {mixed_papers}</p>
                <p><strong>Collaboration Index:</strong> {collab_index:.2f} (avg coauthors per paper - 1)</p>
                <p><strong>Country Diversity:</strong> {country_diversity} countries</p>
                <p><strong>Most Collaborative Country:</strong> {most_collab_country}</p>
            </div>
            
            <h2>🤝 Top Coauthors</h2>
            <ul>
                {''.join([
                    f'<li>'
                    f'<strong>{author}</strong>'
                    f' ({count} joint works)'
                    f'{" — <a href=\"https://orcid.org/' + coauthors_with_orcid.get(author, '') + '\" target=\"_blank\">ORCID</a>" if coauthors_with_orcid.get(author) else ""}'
                    f'</li>'
                    for author, count in list(top_coauthors.items())[:20]
                ])}
            </ul>
            
            <h2>📋 Extended Statistics</h2>
            <div class="stats-grid">
                <div class="stat-item"><strong>Active Period:</strong> {profile.get('first_publication', 'N/A')} - {profile.get('last_publication', 'N/A')}</div>
                <div class="stat-item"><strong>Active Years:</strong> {active_years}</div>
                <div class="stat-item"><strong>Papers per Year:</strong> {papers_per_year:.1f}</div>
                <div class="stat-item"><strong>Trend:</strong> {trend} (R² = {trend_corr**2:.3f})</div>
                <div class="stat-item"><strong>Retractions:</strong> {retractions}</div>
                <div class="stat-item"><strong>Corrections:</strong> {corrections}</div>
                <div class="stat-item"><strong>Unique Coauthors:</strong> {unique_coauthors}</div>
                <div class="stat-item"><strong>Avg Authors per Paper:</strong> {avg_authors:.1f}</div>
                <div class="stat-item"><strong>Max Citations per Paper:</strong> {max_citations}</div>
                <div class="stat-item"><strong>Thematic Diversity (Shannon):</strong> {profile.get('thematic_diversity_shannon', 0):.3f}</div>
                <div class="stat-item"><strong>Domestic Collaboration:</strong> {profile.get('domestic_papers_ratio', 0)*100:.1f}%</div>
                <div class="stat-item"><strong>International Collaboration:</strong> {profile.get('international_papers_ratio', 0)*100:.1f}%</div>
            </div>
            
            <h2>🏷️ Thematic Structure</h2>
            
            <h3>Topics (Top 10)</h3>
            <ul class="thematic-list">
                {''.join([f'<li><strong>{topic}</strong>: {count} papers</li>' for topic, count in list(top_primary_topics.items())[:10]])}
            </ul>
            
            <h3>Key Concepts (Top 20)</h3>
            <ul class="thematic-list">
                {''.join([f'<li>{concept} ({count})</li>' for concept, count in list(top_keywords.items())[:20]])}
            </ul>
            
            <h2>📚 Publication List</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Title</th>
                            <th>Year</th>
                            <th>Journal</th>
                            <th>Citations</th>
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
                <p><em>Total publications: {len(publications)}</em></p>
            </div>
            
            <div class="footer">
                <p>© Author Profile Analysis / Generated by Streamlit App</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# ============================================
# STREAMLIT UI
# ============================================

def init_session_state():
    """Initialize session state"""
    defaults = {
        'orcid': '',
        'profile_data': None,
        'publications': [],
        'analysis_complete': False,
        'logo_base64': None,
        'language': 'en',
        'batch_size': DEFAULT_BATCH_SIZE,
        'max_publications': DEFAULT_MAX_PUBLICATIONS,
        'use_cache': DEFAULT_USE_CACHE
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="Author Profile Analysis",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    # Language selector
    lang = st.sidebar.selectbox(
        "🌐 Language / Язык",
        options=['en', 'ru'],
        format_func=lambda x: 'English' if x == 'en' else 'Русский',
        index=0 if st.session_state.language == 'en' else 1
    )
    st.session_state.language = lang
    
    # Get localized text
    _ = lambda key: get_text(key, lang)
    
    # Sidebar
    with st.sidebar:
        st.title(_('sidebar_title'))
        
        # ORCID input
        orcid = st.text_input(
            _('orcid_label'),
            value=st.session_state.orcid,
            placeholder=_('orcid_placeholder'),
            help=_('orcid_help')
        )
        st.session_state.orcid = orcid
        
        # Logo upload
        logo_file = st.file_uploader(
            _('upload_logo'),
            type=['png', 'jpg', 'jpeg', 'svg'],
            help=_('upload_logo_help')
        )
        
        if logo_file:
            st.session_state.logo_base64 = base64.b64encode(logo_file.read()).decode()
        
        # Advanced settings
        with st.expander(_('advanced_settings')):
            batch_size = st.slider(
                _('batch_size'),
                min_value=10,
                max_value=100,
                value=st.session_state.batch_size,
                step=10
            )
            st.session_state.batch_size = batch_size
            
            max_pubs = st.number_input(
                _('max_publications'),
                min_value=50,
                max_value=2000,
                value=st.session_state.max_publications,
                step=50
            )
            st.session_state.max_publications = max_pubs
            
            use_cache = st.checkbox(
                _('use_cache'),
                value=st.session_state.use_cache
            )
            st.session_state.use_cache = use_cache
        
        # Analyze button
        analyze_btn = st.button(
            _('analyze_button'),
            type="primary",
            use_container_width=True
        )
    
    # Main content
    st.title(_('app_title'))
    st.caption(_('app_subtitle'))
    
    if analyze_btn and orcid:
        with st.spinner(_('analyzing')):
            try:
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔍 Fetching data from ORCID and OpenAlex...")
                progress_bar.progress(20)
                
                # Run analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                analyzer, profile, publications = loop.run_until_complete(
                    collect_scholar_data(
                        orcid,
                        batch_size=batch_size,
                        max_publications=max_pubs
                    )
                )
                
                progress_bar.progress(80)
                status_text.text("📊 Generating visualizations...")
                
                if profile:
                    st.session_state.profile_data = profile
                    st.session_state.publications = publications
                    st.session_state.analysis_complete = True
                    
                    progress_bar.progress(100)
                    status_text.text(_('analysis_complete'))
                    
                    st.success(_('analysis_complete'))
                    st.rerun()
                else:
                    st.error(_('no_data'))
                    
            except Exception as e:
                st.error(f"{_('error')}: {str(e)}")
    
    # Display results if analysis is complete
    if st.session_state.analysis_complete and st.session_state.profile_data:
        profile = st.session_state.profile_data
        publications = st.session_state.publications
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(_('total_publications'), profile.get('total_publications', 0))
        with col2:
            st.metric(_('h_index'), profile.get('h_index', 0))
        with col3:
            st.metric(_('citations'), f"{profile.get('total_citations', 0):,}")
        with col4:
            st.metric(_('oa_percentage'), f"{profile.get('oa_percentage', 0):.1f}%")
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            _('tabs.overview'),
            _('tabs.publications'),
            _('tabs.collaborations'),
            _('tabs.visualizations'),
            _('tabs.risk_assessment'),
            _('tabs.export')
        ])
        
        # Tab 1: Overview
        with tab1:
            # Author info
            st.subheader("👤 Author Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {profile.get('author_name', 'Unknown')}")
                st.write(f"**ORCID:** {profile.get('orcid', 'N/A')}")
                st.write(f"**Affiliations:** {', '.join(profile.get('author_affiliations', [])[:3])}")
            with col2:
                st.write(f"**Countries:** {', '.join(profile.get('author_countries', []))}")
                st.write(f"**Active Period:** {profile.get('first_publication', 'N/A')} - {profile.get('last_publication', 'N/A')}")
                st.write(f"**Active Years:** {profile.get('active_years', 0)}")
            
            # Key metrics in columns
            st.subheader("📊 Key Metrics")
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            with metrics_col1:
                st.metric(_('metrics.total_pubs'), profile.get('total_publications', 0))
                st.metric(_('metrics.h_index'), profile.get('h_index', 0))
                st.metric(_('metrics.g_index'), profile.get('g_index', 0))
                st.metric(_('metrics.i10_index'), profile.get('i10_index', 0))
            with metrics_col2:
                st.metric(_('metrics.total_citations'), f"{profile.get('total_citations', 0):,}")
                st.metric(_('metrics.avg_citations'), f"{profile.get('average_citations', 0):.1f}")
                st.metric(_('metrics.median_citations'), f"{profile.get('median_citations', 0):.0f}")
                st.metric(_('metrics.oa_percentage'), f"{profile.get('oa_percentage', 0):.1f}%")
            with metrics_col3:
                st.metric(_('metrics.papers_per_year'), f"{profile.get('papers_per_year', 0):.1f}")
                st.metric(_('metrics.unique_coauthors'), profile.get('unique_coauthors', 0))
                st.metric(_('metrics.thematic_diversity'), f"{profile.get('thematic_diversity_shannon', 0):.3f}")
                st.metric(_('metrics.trend'), profile.get('trend_direction', 'unknown'))
            
            # Recommendation
            st.subheader(_('recommendation'))
            rec = profile.get('recommendation', 'No recommendation')
            if '🟢' in rec:
                st.success(rec)
            elif '🟡' in rec:
                st.warning(rec)
            elif '🔴' in rec:
                st.error(rec)
            else:
                st.info(rec)
        
        # Tab 2: Publications
        with tab2:
            st.subheader("📋 Publication List")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                year_filter = st.multiselect(
                    "Filter by Year",
                    options=sorted(set([p.get('publication_year', 0) for p in publications]), reverse=True),
                    default=[]
                )
            with col2:
                journal_filter = st.multiselect(
                    "Filter by Journal",
                    options=sorted(set([p.get('journal_name', 'Unknown') for p in publications])),
                    default=[]
                )
            with col3:
                min_citations = st.slider(
                    "Min Citations",
                    min_value=0,
                    max_value=max([p.get('cited_by_count', 0) for p in publications]) if publications else 100,
                    value=0
                )
            
            # Apply filters
            filtered_pubs = publications
            if year_filter:
                filtered_pubs = [p for p in filtered_pubs if p.get('publication_year', 0) in year_filter]
            if journal_filter:
                filtered_pubs = [p for p in filtered_pubs if p.get('journal_name', 'Unknown') in journal_filter]
            if min_citations > 0:
                filtered_pubs = [p for p in filtered_pubs if p.get('cited_by_count', 0) >= min_citations]
            
            # Display as dataframe
            df = pd.DataFrame(filtered_pubs)
            if not df.empty:
                display_cols = ['title', 'publication_year', 'journal_name', 'cited_by_count', 'is_oa', 'doi']
                display_df = df[display_cols].copy()
                display_df.columns = ['Title', 'Year', 'Journal', 'Citations', 'OA', 'DOI']
                display_df['OA'] = display_df['OA'].apply(lambda x: '✅' if x else '❌')
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    column_config={
                        "Title": st.column_config.TextColumn("Title", width="large"),
                        "Year": st.column_config.NumberColumn("Year", width="small"),
                        "Journal": st.column_config.TextColumn("Journal", width="medium"),
                        "Citations": st.column_config.NumberColumn("Citations", width="small"),
                        "OA": st.column_config.TextColumn("OA", width="small"),
                        "DOI": st.column_config.LinkColumn("DOI", width="medium")
                    }
                )
                st.caption(f"Showing {len(filtered_pubs)} of {len(publications)} publications")
            else:
                st.info("No publications match the filters")
        
        # Tab 3: Collaborations
        with tab3:
            st.subheader("🤝 Collaboration Analysis")
            
            collaborations = profile.get('collaborations', {})
            domestic_papers = collaborations.get('domestic_papers', 0)
            international_papers = collaborations.get('international_papers', 0)
            mixed_papers = collaborations.get('mixed_papers', 0)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Domestic Papers", domestic_papers)
            with col2:
                st.metric("International Papers", international_papers)
            with col3:
                st.metric("Mixed Papers", mixed_papers)
            with col4:
                st.metric("Collaboration Index", f"{profile.get('collaboration_index', 0):.2f}")
            
            # Domestic collaborations
            domestic_collab = collaborations.get('domestic', {})
            if domestic_collab:
                st.subheader("🇺🇳 Domestic Collaborations")
                for country, affils in list(domestic_collab.items())[:10]:
                    with st.expander(f"📍 {country}"):
                        for affil, count in list(affils.items())[:10]:
                            st.write(f"• **{affil}**: {count} papers")
            
            # International collaborations
            international_collab = collaborations.get('international', {})
            if international_collab:
                st.subheader("🌐 International Collaborations")
                for country, affils in list(international_collab.items())[:10]:
                    with st.expander(f"📍 {country}"):
                        for affil, count in list(affils.items())[:10]:
                            st.write(f"• **{affil}**: {count} papers")
            
            # Top coauthors
            top_coauthors = profile.get('top_coauthors', {})
            if top_coauthors:
                st.subheader("🤝 Top Coauthors")
                coauthors_df = pd.DataFrame([
                    {'Author': author, 'Papers': count, 'ORCID': profile.get('coauthors_with_orcid', {}).get(author, '')}
                    for author, count in list(top_coauthors.items())[:20]
                ])
                st.dataframe(coauthors_df, use_container_width=True)
        
        # Tab 4: Visualizations
        with tab4:
            st.subheader("📈 Visualizations")
            
            # Generate visualizations
            with st.spinner("Generating visualizations..."):
                images = create_visualizations(profile)
            
            # Display charts
            if images.get('years_chart'):
                st.image(BytesIO(base64.b64decode(images['years_chart'])), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if images.get('journals_chart'):
                    st.image(BytesIO(base64.b64decode(images['journals_chart'])), use_container_width=True)
            with col2:
                if images.get('oa_chart'):
                    st.image(BytesIO(base64.b64decode(images['oa_chart'])), use_container_width=True)
            
            if images.get('wordcloud'):
                st.image(BytesIO(base64.b64decode(images['wordcloud'])), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if images.get('citations_chart'):
                    st.image(BytesIO(base64.b64decode(images['citations_chart'])), use_container_width=True)
            with col2:
                if images.get('citation_distribution'):
                    st.image(BytesIO(base64.b64decode(images['citation_distribution'])), use_container_width=True)
        
        # Tab 5: Risk Assessment
        with tab5:
            st.subheader("⚠️ Risk Assessment")
            
            risk_flags = profile.get('risk_flags', [])
            if risk_flags:
                for flag in risk_flags:
                    if '🔴' in flag:
                        st.error(flag)
                    elif '⚠️' in flag:
                        st.warning(flag)
                    else:
                        st.info(flag)
            else:
                st.success("✅ No risk flags detected")
            
            # Additional risk metrics
            st.subheader("📊 Risk Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Retractions", profile.get('retractions', 0))
                st.metric("Corrections", profile.get('corrections', 0))
            with col2:
                st.metric("Papers per Year", f"{profile.get('papers_per_year', 0):.1f}")
                st.metric("Unique Coauthors", profile.get('unique_coauthors', 0))
            with col3:
                st.metric("Thematic Diversity", f"{profile.get('thematic_diversity_shannon', 0):.3f}")
                st.metric("International Ratio", f"{profile.get('international_papers_ratio', 0)*100:.1f}%")
        
        # Tab 6: Export
        with tab6:
            st.subheader("📄 Export Reports")
            
            # Generate HTML report
            if st.button(_('export_html')):
                with st.spinner("Generating HTML report..."):
                    images = create_visualizations(profile)
                    html = generate_html_report(
                        profile,
                        publications,
                        images,
                        st.session_state.logo_base64
                    )
                    
                    st.download_button(
                        label=f"{_('download')} HTML",
                        data=html,
                        file_name=f"profile_{profile.get('orcid', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
            
            # Export CSV
            if st.button(_('export_csv')):
                df = pd.DataFrame(publications)
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"{_('download')} CSV",
                    data=csv,
                    file_name=f"publications_{profile.get('orcid', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Export PDF
            if PDF_AVAILABLE and st.button(_('export_pdf')):
                st.info("PDF export is available but requires reportlab. Please use HTML or CSV export for now.")
            elif not PDF_AVAILABLE:
                st.warning("PDF export requires reportlab. Install with: pip install reportlab")

if __name__ == "__main__":
    main()
