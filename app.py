

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
from plotly.subplots import make_subplots
from wordcloud import WordCloud
from datetime import datetime
from typing import List, Set, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
import re
import json
import os
import base64
from io import BytesIO
import hashlib
from matplotlib.ticker import MaxNLocator
import nest_asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from bs4 import BeautifulSoup

# ============================================
# STREAMLIT CONFIGURATION
# ============================================

st.set_page_config(
    page_title="🔬 Author Profile Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# LANGUAGE SUPPORT
# ============================================

LANGUAGES = {
    'en': {
        'app_title': '🔬 Author Profile Analysis',
        'app_subtitle': 'Deep analysis of researcher profiles via ORCID',
        'orcid_input': 'ORCID ID',
        'orcid_placeholder': '0000-0002-1234-567X or https://orcid.org/...',
        'analyze_btn': '🔍 Analyze Profile',
        'export_csv': '📊 Export CSV',
        'export_html': '📄 Export HTML Report',
        'export_pdf': '📑 Export PDF Report',
        'publications': 'Publications',
        'citations': 'Citations',
        'h_index': 'h-index',
        'open_access': 'Open Access',
        'visualizations': '📊 Visualizations',
        'publications_tab': '📋 Publications',
        'collaborations_tab': '🤝 Collaborations',
        'risk_tab': '⚠️ Risk Assessment',
        'analysis_complete': '✅ Analysis Complete!',
        'processing': 'Processing...',
        'total_publications': 'Total Publications',
        'total_citations': 'Total Citations',
        'avg_citations': 'Avg Citations',
        'oa_percentage': 'Open Access %',
        'error_invalid_orcid': '❌ Please enter a valid ORCID',
        'error_no_data': '❌ No data found. Please check ORCID.',
        'success': '✅ Analysis completed successfully!',
        'risks_detected': '⚠️ Risk Flags Detected',
        'recommendation': '💡 Recommendation',
        'coauthors': 'Top Co-authors',
        'institutions': 'Top Institutions',
        'journals': 'Top Journals',
        'years_distribution': 'Publications by Year',
        'citation_distribution': 'Citation Distribution',
        'trend_analysis': 'Publication Trend',
        'collaboration_analysis': '🌍 Collaboration Analysis',
        'domestic': 'Domestic Collaborations',
        'international': 'International Collaborations',
        'mixed': 'Mixed Collaborations',
        'collaboration_index': 'Collaboration Index',
        'country_diversity': 'Country Diversity',
        'thematic_structure': '🏷️ Thematic Structure',
        'concepts': 'Key Concepts',
        'fields': 'Fields',
        'domains': 'Domains',
        'topics': 'Topics',
        'subtopics': 'Subtopics',
        'retractions': 'Retractions',
        'corrections': 'Corrections',
        'active_years': 'Active Years',
        'papers_per_year': 'Papers per Year',
        'unique_coauthors': 'Unique Co-authors',
        'most_cited': 'Most Cited Articles',
        'download': 'Download',
        'settings': '⚙️ Settings',
        'cache_settings': 'Cache Settings',
        'use_cache': 'Use Cache',
        'clear_cache': 'Clear Cache',
        'batch_size': 'Batch Size',
        'max_publications': 'Max Publications to Analyze',
        'logo_upload': 'Upload Logo (Optional)',
        'advanced_settings': 'Advanced Settings',
        'report_settings': 'Report Settings',
        'generate_html': 'Generate HTML Report',
        'generate_pdf': 'Generate PDF Report',
        'institution_homepages': 'Institution Homepages',
        'language': 'Language'
    },
    'ru': {
        'app_title': '🔬 Анализ профиля ученого',
        'app_subtitle': 'Глубокий анализ профилей исследователей через ORCID',
        'orcid_input': 'ORCID ID',
        'orcid_placeholder': '0000-0002-1234-567X или https://orcid.org/...',
        'analyze_btn': '🔍 Анализировать профиль',
        'export_csv': '📊 Экспорт CSV',
        'export_html': '📄 Экспорт HTML отчета',
        'export_pdf': '📑 Экспорт PDF отчета',
        'publications': 'Публикации',
        'citations': 'Цитирования',
        'h_index': 'h-индекс',
        'open_access': 'Открытый доступ',
        'visualizations': '📊 Визуализации',
        'publications_tab': '📋 Публикации',
        'collaborations_tab': '🤝 Коллаборации',
        'risk_tab': '⚠️ Оценка рисков',
        'analysis_complete': '✅ Анализ завершен!',
        'processing': 'Обработка...',
        'total_publications': 'Всего публикаций',
        'total_citations': 'Всего цитирований',
        'avg_citations': 'Среднее цитирований',
        'oa_percentage': 'Открытый доступ %',
        'error_invalid_orcid': '❌ Введите корректный ORCID',
        'error_no_data': '❌ Данные не найдены. Проверьте ORCID.',
        'success': '✅ Анализ успешно завершен!',
        'risks_detected': '⚠️ Обнаружены флаги риска',
        'recommendation': '💡 Рекомендация',
        'coauthors': 'Топ соавторы',
        'institutions': 'Топ институты',
        'journals': 'Топ журналы',
        'years_distribution': 'Публикации по годам',
        'citation_distribution': 'Распределение цитирований',
        'trend_analysis': 'Тренд публикаций',
        'collaboration_analysis': '🌍 Анализ коллабораций',
        'domestic': 'Внутристрановые коллаборации',
        'international': 'Международные коллаборации',
        'mixed': 'Смешанные коллаборации',
        'collaboration_index': 'Индекс коллабораций',
        'country_diversity': 'Страновое разнообразие',
        'thematic_structure': '🏷️ Тематическая структура',
        'concepts': 'Ключевые концепты',
        'fields': 'Fields (уровень 2)',
        'domains': 'Domains (уровень 3)',
        'topics': 'Topics (уровень 1)',
        'subtopics': 'Subtopics (уровень 0)',
        'retractions': 'Ретракции',
        'corrections': 'Коррекции',
        'active_years': 'Активных лет',
        'papers_per_year': 'Статей в год',
        'unique_coauthors': 'Уникальных соавторов',
        'most_cited': 'Самые цитируемые статьи',
        'download': 'Скачать',
        'settings': '⚙️ Настройки',
        'cache_settings': 'Настройки кэша',
        'use_cache': 'Использовать кэш',
        'clear_cache': 'Очистить кэш',
        'batch_size': 'Размер батча',
        'max_publications': 'Макс. статей для анализа',
        'logo_upload': 'Загрузить логотип (опционально)',
        'advanced_settings': 'Расширенные настройки',
        'report_settings': 'Настройки отчетов',
        'generate_html': 'Создать HTML отчет',
        'generate_pdf': 'Создать PDF отчет',
        'institution_homepages': 'Сайты институтов',
        'language': 'Язык'
    }
}

def _(key: str) -> str:
    """Get localized string"""
    lang = st.session_state.get('language', 'en')
    return LANGUAGES[lang].get(key, key)

# ============================================
# CACHE MANAGEMENT
# ============================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_from_cache(orcid: str) -> Optional[Dict]:
    """Load data from cache with TTL"""
    orcid_clean = clean_orcid(orcid)
    if not os.path.exists('cache'):
        os.makedirs('cache')
    cache_path = f"cache/{orcid_clean}.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except:
            return None
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def save_to_cache(orcid: str, data: Dict):
    """Save data to cache"""
    orcid_clean = clean_orcid(orcid)
    if not os.path.exists('cache'):
        os.makedirs('cache')
    cache_path = f"cache/{orcid_clean}.json"
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def clear_cache():
    """Clear all cached data"""
    if os.path.exists('cache'):
        import shutil
        shutil.rmtree('cache')
        os.makedirs('cache')
    st.cache_data.clear()

# ============================================
# HELPER FUNCTIONS
# ============================================

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

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_with_retry(session, url, params=None, headers=None, method='GET'):
    """Fetch with retry mechanism"""
    for attempt in range(3):
        try:
            async with session.request(method, url, params=params, headers=headers, timeout=30) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 2 * (attempt + 1)))
                    await asyncio.sleep(retry_after)
                    continue
                if response.status == 200:
                    return await response.json()
                return None
        except:
            await asyncio.sleep(2 ** attempt)
    return None

# ============================================
# API FUNCTIONS
# ============================================

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
    except:
        pass
    return dois

async def get_openalex_metadata(dois: List[str], session) -> List[Dict]:
    """Get metadata from OpenAlex for DOIs"""
    if not dois:
        return []
    
    doi_query = '|'.join(dois[:50])
    params = {'filter': f'doi:{doi_query}', 'per-page': len(dois)}
    url = "https://api.openalex.org/works"
    data = await fetch_with_retry(session, url, params=params)
    if not data:
        return []
    return data.get('results', [])

async def get_openalex_author(orcid: str, session) -> Dict:
    """Get author info from OpenAlex"""
    if not orcid:
        return {}
    orcid_clean = clean_orcid(orcid)
    params = {'filter': f'orcid:{orcid_clean}', 'per-page': 1}
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
        params = {'filter': f'openalex:{id_query}', 'per-page': len(batch)}
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
    """Parse publication from OpenAlex with enhanced information"""
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
                concept_levels[concept_name] = {'level': concept_level, 'score': concept_score}
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
    except:
        return None

# ============================================
# DATA COLLECTOR
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
        if not self.publications:
            return
        
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
    
    def _analyze_collaborations(self):
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
            flags.append("⚠️ Low international collaboration")
        return flags
    
    def _generate_recommendation(self) -> str:
        risk_count = len(self.profile.get('risk_flags', []))
        total_pubs = self.profile.get('total_publications', 0)
        h_index = self.profile.get('h_index', 0)
        trend = self.profile.get('trend_direction', 'stable')
        
        if risk_count >= 3:
            return "🔴 Further verification required. Multiple red flags detected."
        elif risk_count >= 1:
            return "🟡 Caution recommended. Some warnings detected."
        elif total_pubs >= 30 and h_index >= 15 and trend in ['up', 'strong_up']:
            return "🟢 Outstanding scholar. High productivity and growing h-index."
        elif total_pubs >= 20 and h_index >= 10:
            return "🟢 Strong candidate. Stable publication activity."
        elif total_pubs >= 10 and h_index >= 5:
            return "🟢 Promising researcher. Recommended for consideration."
        elif total_pubs >= 5:
            return "🟢 Early-career researcher. Requires expert evaluation."
        else:
            return "🟢 Junior researcher. Papers require careful peer review."

# ============================================
# DATA COLLECTION PIPELINE
# ============================================

async def collect_scholar_data(orcid: str, max_publications: int = 1000) -> Tuple[ScholarProfileAnalyzer, Dict, List[Dict]]:
    """Main data collection pipeline"""
    orcid_clean = clean_orcid(orcid)
    if not orcid_clean:
        return None, {}, []
    
    # Check cache first
    cached_data = load_from_cache(orcid_clean)
    if cached_data and st.session_state.get('use_cache', True):
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
        
        # Get DOIs
        orcid_dois = await get_orcid_dois(orcid_clean, session)
        if not orcid_dois:
            return analyzer, {}, []
        
        all_dois = list(orcid_dois)
        if len(all_dois) > max_publications:
            all_dois = all_dois[:max_publications]
        
        # Get metadata
        all_metadata = []
        doi_batches = list(chunks(all_dois, 50))
        
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
        
        # Analyze
        analyzer.analyze_publications()
        
        # Cache
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
# VISUALIZATION FUNCTIONS
# ============================================

def apply_scientific_style():
    """Apply scientific style to matplotlib plots"""
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
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.edgecolor': '#000000',
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'figure.facecolor': 'white',
        'figure.constrained_layout.use': True,
        'lines.linewidth': 2,
        'lines.markersize': 7,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })

def create_visualizations(profile: Dict) -> Dict[str, str]:
    """Create visualizations in scientific style"""
    apply_scientific_style()
    images = {}
    
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
        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
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
        oa_labels = {'gold': 'Gold OA', 'green': 'Green OA', 'hybrid': 'Hybrid OA',
                    'bronze': 'Bronze OA', 'closed': 'Closed Access'}
        oa_colors = {'gold': '#2ECC71', 'green': '#3498DB', 'hybrid': '#F1C40F',
                    'bronze': '#E67E22', 'closed': '#95A5A6'}
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
    
    # 4. Word Cloud
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
    
    # 5. Most cited
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
        ax.set_xlabel('Citations', fontsize=12, fontweight='bold')
        ax.set_title('Most Cited Articles', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['citations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 6. Top affiliations
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
        ax.set_xlabel('Number of Publications', fontsize=12, fontweight='bold')
        ax.set_title('Top Affiliations', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        ax.set_axisbelow(True)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        images['affiliations_chart'] = base64.b64encode(buf.getvalue()).decode()
        plt.close()
    
    # 7. Citation distribution
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
        ax.set_ylabel('Number of Articles', fontsize=12, fontweight='bold')
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
    
    return images

def create_plotly_charts(profile: Dict) -> Dict[str, go.Figure]:
    """Create interactive Plotly charts"""
    figures = {}
    
    # Interactive year trend
    if profile.get('years_distribution'):
        years = sorted(profile['years_distribution'].keys())
        counts = [profile['years_distribution'][y] for y in years]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=years,
            y=counts,
            name='Publications',
            marker_color='#2E86AB',
            text=counts,
            textposition='outside'
        ))
        
        if len(years) >= 2:
            x = np.arange(len(years))
            z = np.polyfit(x, counts, 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=years,
                y=p(x),
                mode='lines',
                name='Trend',
                line=dict(color='red', width=3, dash='dash')
            ))
        
        fig.update_layout(
            title='Publication Activity Dynamics',
            xaxis_title='Year',
            yaxis_title='Number of Publications',
            template='plotly_white',
            hovermode='x unified',
            showlegend=True
        )
        figures['years'] = fig
    
    # Top journals
    if profile.get('top_journals'):
        journals = list(profile['top_journals'].keys())[:10]
        counts = list(profile['top_journals'].values())[:10]
        sorted_pairs = sorted(zip(counts, journals), reverse=True)
        counts, journals = zip(*sorted_pairs)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=counts,
            y=journals,
            orientation='h',
            marker_color='#A23B72',
            text=counts,
            textposition='outside'
        ))
        fig.update_layout(
            title='Top Journals',
            xaxis_title='Number of Publications',
            yaxis_title='Journal',
            template='plotly_white',
            height=500
        )
        figures['journals'] = fig
    
    return figures

# ============================================
# REPORT GENERATION
# ============================================

def generate_html_report(profile: Dict, publications: List[Dict], images: Dict[str, str], logo_base64: Optional[str] = None) -> str:
    """Generate HTML report"""
    total_pubs = profile.get('total_publications', 0)
    h_index = profile.get('h_index', 0)
    g_index = profile.get('g_index', 0)
    total_citations = profile.get('total_citations', 0)
    oa_percentage = profile.get('oa_percentage', 0)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Author Profile - {profile.get('author_name', 'Unknown')}</title>
        <style>
            body {{ font-family: 'Times New Roman', serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
            .header {{ background: #2C3E50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }}
            .header h1 {{ color: white; margin: 0; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2C3E50; }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #2C3E50; }}
            .metric-label {{ font-size: 12px; color: #7F8C8D; }}
            .chart {{ margin: 20px 0; text-align: center; }}
            .chart img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background: #2C3E50; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #BDC3C7; }}
            .recommendation {{ padding: 15px; border-radius: 8px; margin: 20px 0; background: #D5F5E3; border-left: 4px solid #2ECC71; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #BDC3C7; text-align: center; color: #7F8C8D; }}
            .logo {{ max-height: 80px; max-width: 200px; }}
            .collab-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .collab-box {{ background: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>📊 Author Profile</h1>
                    <div style="font-size: 14px; opacity: 0.8;">ORCID: {profile.get('orcid', 'N/A')}</div>
                </div>
                {f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Logo">' if logo_base64 else ''}
            </div>
            
            <h2>{profile.get('author_name', 'Unknown')}</h2>
            <p><strong>Affiliations:</strong> {', '.join(profile.get('author_affiliations', [])[:3])}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            
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
                    <div class="metric-label">Citations</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{oa_percentage:.1f}%</div>
                    <div class="metric-label">Open Access</div>
                </div>
            </div>
            
            <div class="recommendation">
                <strong>Recommendation:</strong> {profile.get('recommendation', 'No recommendation')}
            </div>
            
            <div class="chart"><img src="data:image/png;base64,{images.get('years_chart', '')}" alt="Years"></div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="chart"><img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="Journals"></div>
                <div class="chart"><img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="OA"></div>
            </div>
            <div class="chart"><img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="WordCloud"></div>
            
            <h2>🌍 Collaboration Analysis</h2>
            <div class="collab-grid">
                <div class="collab-box">
                    <h4>Domestic</h4>
                    <p>Papers: {profile.get('collaborations', {}).get('domestic_papers', 0)}</p>
                </div>
                <div class="collab-box">
                    <h4>International</h4>
                    <p>Papers: {profile.get('collaborations', {}).get('international_papers', 0)}</p>
                </div>
            </div>
            
            <h2>📚 Publications</h2>
            <table>
                <thead><tr><th>#</th><th>Title</th><th>Year</th><th>Journal</th><th>Citations</th></tr></thead>
                <tbody>
                    {''.join([
                        f'<tr><td>{i+1}</td><td>{pub.get("title", "")[:60]}</td>'
                        f'<td>{pub.get("publication_year", "N/A")}</td>'
                        f'<td>{pub.get("journal_name", "Unknown")}</td>'
                        f'<td>{pub.get("cited_by_count", 0)}</td></tr>'
                        for i, pub in enumerate(sorted(publications, key=lambda x: x.get('publication_year', 0), reverse=True)[:30])
                    ])}
                </tbody>
            </table>
            <p><em>Showing 30 of {len(publications)} publications</em></p>
            
            <div class="footer">
                <p>© Author Profile Analysis / Chimica Techno Acta</p>
                <p>https://chimicatechnoacta.ru</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def generate_pdf_report(profile: Dict, publications: List[Dict], images: Dict[str, str], filename: str = "profile_report.pdf"):
    """Generate PDF report"""
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=30)
        story.append(Paragraph("Author Profile Analysis", title_style))
        
        # Author info
        story.append(Paragraph(f"<b>{profile.get('author_name', 'Unknown')}</b>", styles['Heading2']))
        story.append(Paragraph(f"ORCID: {profile.get('orcid', 'N/A')}", styles['Normal']))
        if profile.get('author_affiliations'):
            story.append(Paragraph(f"Affiliations: {', '.join(profile['author_affiliations'][:3])}", styles['Normal']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Metrics table
        metrics_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Publications', str(profile.get('total_publications', 0)), 'h-index', str(profile.get('h_index', 0))],
            ['g-index', str(profile.get('g_index', 0)), 'i10-index', str(profile.get('i10_index', 0))],
            ['Citations', f"{profile.get('total_citations', 0):,}", 'OA %', f"{profile.get('oa_percentage', 0):.1f}%"],
            ['Retractions', str(profile.get('retractions', 0)), 'Active years', str(profile.get('active_years', 0))]
        ]
        table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Recommendation
        rec_style = ParagraphStyle('Rec', parent=styles['Normal'], backColor=colors.HexColor('#D5F5E3'), borderPadding=10)
        story.append(Paragraph(f"<b>Recommendation:</b> {profile.get('recommendation', 'No recommendation')}", rec_style))
        story.append(Spacer(1, 20))
        
        # Images
        for img_key in ['years_chart', 'journals_chart', 'oa_chart', 'wordcloud', 'citations_chart']:
            if img_key in images and images[img_key]:
                try:
                    img_data = base64.b64decode(images[img_key])
                    img = Image(BytesIO(img_data), width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 20))
                except:
                    pass
        
        doc.build(story)
        return True
    except:
        return False

# ============================================
# STREAMLIT UI
# ============================================

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'language': 'en',
        'profile_data': None,
        'publications': [],
        'analysis_complete': False,
        'use_cache': True,
        'batch_size': 50,
        'max_publications': 1000,
        'logo_base64': None,
        'images': {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_publications_table(publications: List[Dict]):
    """Display publications in interactive table"""
    if not publications:
        st.info("No publications found")
        return
    
    df = pd.DataFrame(publications)
    cols_to_show = ['title', 'publication_year', 'journal_name', 'cited_by_count', 'is_oa', 'doi']
    available_cols = [c for c in cols_to_show if c in df.columns]
    
    if available_cols:
        display_df = df[available_cols].copy()
        display_df.columns = ['Title', 'Year', 'Journal', 'Citations', 'OA', 'DOI']
        
        # Search filter
        search = st.text_input("🔍 Search publications", placeholder="Search by title, journal, or DOI...")
        if search:
            mask = display_df['Title'].str.contains(search, case=False, na=False) | \
                   display_df['Journal'].str.contains(search, case=False, na=False) | \
                   display_df['DOI'].str.contains(search, case=False, na=False)
            display_df = display_df[mask]
        
        # Sort options
        sort_col = st.selectbox("Sort by", ['Year', 'Citations', 'Title'], index=0)
        ascending = st.checkbox("Ascending", False)
        display_df = display_df.sort_values(sort_col, ascending=ascending)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Year": st.column_config.NumberColumn("Year", format="%d"),
                "Journal": st.column_config.TextColumn("Journal", width="medium"),
                "Citations": st.column_config.NumberColumn("Citations", format="%d"),
                "OA": st.column_config.CheckboxColumn("OA"),
                "DOI": st.column_config.LinkColumn("DOI", display_text="Open")
            }
        )
        
        st.caption(f"Showing {len(display_df)} of {len(publications)} publications")

def show_collaborations(profile: Dict):
    """Display collaboration analysis"""
    collaborations = profile.get('collaborations', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "🏠 Domestic",
            collaborations.get('domestic_papers', 0),
            help="Papers with only author's country institutions"
        )
    with col2:
        st.metric(
            "🌐 International",
            collaborations.get('international_papers', 0),
            help="Papers with non-author country institutions"
        )
    with col3:
        st.metric(
            "🔄 Mixed",
            collaborations.get('mixed_papers', 0),
            help="Papers with both author and non-author country institutions"
        )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇷🇺 Domestic Collaborations")
        domestic = collaborations.get('domestic', {})
        if domestic:
            for country, affils in list(domestic.items())[:5]:
                with st.expander(f"📍 {country}"):
                    for affil, count in list(affils.items())[:10]:
                        st.write(f"• **{affil}**: {count} papers")
        else:
            st.info("No domestic collaborations found")
    
    with col2:
        st.subheader("🌍 International Collaborations")
        international = collaborations.get('international', {})
        if international:
            for country, affils in list(international.items())[:5]:
                with st.expander(f"📍 {country}"):
                    for affil, count in list(affils.items())[:10]:
                        st.write(f"• **{affil}**: {count} papers")
        else:
            st.info("No international collaborations found")

def show_risk_assessment(profile: Dict):
    """Display risk assessment and recommendations"""
    risk_flags = profile.get('risk_flags', [])
    
    st.subheader("⚠️ Risk Assessment")
    
    if risk_flags:
        for flag in risk_flags:
            if '🔴' in flag:
                st.error(flag)
            else:
                st.warning(flag)
    else:
        st.success("✅ No risk flags detected")
    
    st.divider()
    
    st.subheader("💡 Recommendation")
    recommendation = profile.get('recommendation', 'No recommendation available')
    if '🟢' in recommendation:
        st.success(recommendation)
    elif '🟡' in recommendation:
        st.warning(recommendation)
    else:
        st.error(recommendation)

def show_visualizations_tab(images: Dict[str, str], plotly_figs: Dict[str, go.Figure]):
    """Display visualizations tab"""
    
    # Matplotlib charts
    if images.get('years_chart'):
        st.image(f"data:image/png;base64,{images['years_chart']}", use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if images.get('journals_chart'):
            st.image(f"data:image/png;base64,{images['journals_chart']}", use_container_width=True)
    with col2:
        if images.get('oa_chart'):
            st.image(f"data:image/png;base64,{images['oa_chart']}", use_container_width=True)
    
    if images.get('wordcloud'):
        st.image(f"data:image/png;base64,{images['wordcloud']}", use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if images.get('citations_chart'):
            st.image(f"data:image/png;base64,{images['citations_chart']}", use_container_width=True)
    with col2:
        if images.get('affiliations_chart'):
            st.image(f"data:image/png;base64,{images['affiliations_chart']}", use_container_width=True)
    
    if images.get('citation_distribution'):
        st.image(f"data:image/png;base64,{images['citation_distribution']}", use_container_width=True)

def show_author_info(profile: Dict):
    """Display author information"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("👤 Author Information")
        st.write(f"**Name:** {profile.get('author_name', 'Unknown')}")
        st.write(f"**ORCID:** {profile.get('orcid', 'N/A')}")
        
        if profile.get('author_affiliations'):
            st.write("**Affiliations:**")
            for aff in profile['author_affiliations'][:5]:
                st.write(f"  • {aff}")
        
        if profile.get('author_countries'):
            st.write(f"**Countries:** {', '.join(profile['author_countries'])}")
        
        st.write(f"**Active Years:** {profile.get('first_publication', 'N/A')} - {profile.get('last_publication', 'N/A')}")
        st.write(f"**Papers per Year:** {profile.get('papers_per_year', 0):.1f}")
        st.write(f"**Unique Co-authors:** {profile.get('unique_coauthors', 0)}")
    
    with col2:
        st.subheader("📊 Quick Stats")
        st.metric("Publications", profile.get('total_publications', 0))
        st.metric("h-index", profile.get('h_index', 0))
        st.metric("g-index", profile.get('g_index', 0))
        st.metric("i10-index", profile.get('i10_index', 0))
        st.metric("Total Citations", f"{profile.get('total_citations', 0):,}")
        st.metric("Retractions", profile.get('retractions', 0))

def show_thematic_structure(profile: Dict):
    """Display thematic structure"""
    st.subheader("🏷️ Thematic Structure")
    
    tabs = st.tabs(["Concepts", "Fields", "Domains", "Topics", "Keywords"])
    
    with tabs[0]:
        concepts = profile.get('top_concepts', {})
        if concepts:
            st.dataframe(
                pd.DataFrame(list(concepts.items()), columns=['Concept', 'Count']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No concepts found")
    
    with tabs[1]:
        fields = profile.get('top_fields', {})
        if fields:
            st.dataframe(
                pd.DataFrame(list(fields.items()), columns=['Field', 'Count']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No fields found")
    
    with tabs[2]:
        domains = profile.get('top_domains', {})
        if domains:
            st.dataframe(
                pd.DataFrame(list(domains.items()), columns=['Domain', 'Count']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No domains found")
    
    with tabs[3]:
        topics = profile.get('top_primary_topics', {})
        if topics:
            st.dataframe(
                pd.DataFrame(list(topics.items()), columns=['Topic', 'Count']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No topics found")
    
    with tabs[4]:
        keywords = profile.get('top_keywords', {})
        if keywords:
            st.dataframe(
                pd.DataFrame(list(keywords.items()), columns=['Keyword', 'Count']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No keywords found")

# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Main Streamlit application"""
    
    # Initialize
    init_session_state()
    nest_asyncio.apply()
    
    # Language selector in sidebar
    with st.sidebar:
        st.title("🔬 " + _('app_title'))
        st.caption(_('app_subtitle'))
        
        # Language selection
        lang = st.selectbox(
            _('language'),
            options=['en', 'ru'],
            format_func=lambda x: 'English' if x == 'en' else 'Русский',
            index=0 if st.session_state.get('language') == 'en' else 1
        )
        st.session_state.language = lang
        
        st.divider()
        
        # ORCID input
        orcid = st.text_input(
            _('orcid_input'),
            placeholder=_('orcid_placeholder'),
            key='orcid_input'
        )
        
        # Logo upload
        logo_file = st.file_uploader(
            _('logo_upload'),
            type=['png', 'jpg', 'jpeg', 'svg'],
            key='logo_upload'
        )
        
        if logo_file:
            st.session_state.logo_base64 = base64.b64encode(logo_file.getvalue()).decode()
        
        st.divider()
        
        # Settings
        with st.expander(_('settings')):
            st.session_state.use_cache = st.checkbox(
                _('use_cache'),
                value=st.session_state.use_cache
            )
            
            if st.button(_('clear_cache')):
                clear_cache()
                st.success("Cache cleared!")
            
            st.session_state.batch_size = st.slider(
                _('batch_size'),
                10, 100, st.session_state.batch_size, 10
            )
            
            st.session_state.max_publications = st.number_input(
                _('max_publications'),
                min_value=50,
                max_value=5000,
                value=st.session_state.max_publications,
                step=50
            )
        
        # Analyze button
        analyze_btn = st.button(
            _('analyze_btn'),
            type='primary',
            use_container_width=True
        )
    
    # Main content
    st.title(_('app_title'))
    
    # Information box
    with st.expander("ℹ️ About this tool", expanded=False):
        st.markdown("""
        **Author Profile Analysis** provides comprehensive analysis of researcher profiles using ORCID and OpenAlex data.
        
        **Features:**
        - 📊 20+ research metrics (h-index, g-index, i10-index)
        - 📈 Scientific visualizations in publication style
        - 🏷️ Detailed thematic structure (Concepts → Fields → Domains → Topics)
        - 🌍 Collaboration analysis with country-level breakdown
        - ⚠️ Risk assessment and editor recommendations
        - 📄 HTML and PDF reports in scientific format
        """)
    
    # Process analysis
    if analyze_btn and orcid:
        orcid_clean = clean_orcid(orcid)
        if not orcid_clean:
            st.error(_('error_invalid_orcid'))
            return
        
        with st.spinner(_('processing')):
            progress_bar = st.progress(0, text=_('processing'))
            status_text = st.empty()
            
            try:
                # Run async collection
                status_text.text("🔍 Fetching data from ORCID and OpenAlex...")
                progress_bar.progress(20)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                analyzer, profile, publications = loop.run_until_complete(
                    collect_scholar_data(orcid_clean, st.session_state.max_publications)
                )
                
                if not profile:
                    st.error(_('error_no_data'))
                    return
                
                progress_bar.progress(60)
                status_text.text("🎨 Creating visualizations...")
                
                # Create visualizations
                images = create_visualizations(profile)
                plotly_figs = create_plotly_charts(profile)
                
                progress_bar.progress(80)
                status_text.text("📄 Generating reports...")
                
                # Store in session
                st.session_state.profile_data = profile
                st.session_state.publications = publications
                st.session_state.analysis_complete = True
                st.session_state.images = images
                st.session_state.plotly_figs = plotly_figs
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                
                st.success(_('success'))
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display results if available
    if st.session_state.analysis_complete and st.session_state.profile_data:
        profile = st.session_state.profile_data
        publications = st.session_state.publications
        images = st.session_state.images
        plotly_figs = st.session_state.get('plotly_figs', {})
        
        # Author info
        show_author_info(profile)
        
        st.divider()
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            _('visualizations'),
            _('publications_tab'),
            _('collaborations_tab'),
            _('risk_tab'),
            _('thematic_structure')
        ])
        
        with tab1:
            show_visualizations_tab(images, plotly_figs)
        
        with tab2:
            show_publications_table(publications)
        
        with tab3:
            show_collaborations(profile)
        
        with tab4:
            show_risk_assessment(profile)
        
        with tab5:
            show_thematic_structure(profile)
        
        # Export section
        st.divider()
        st.subheader("📥 " + _('download'))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            if publications:
                df = pd.DataFrame(publications)
                csv = df.to_csv(index=False)
                st.download_button(
                    label=_('export_csv'),
                    data=csv,
                    file_name=f"profile_{profile.get('orcid', 'unknown')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            # HTML Export
            if images:
                html_content = generate_html_report(
                    profile,
                    publications,
                    images,
                    st.session_state.logo_base64
                )
                st.download_button(
                    label=_('export_html'),
                    data=html_content,
                    file_name=f"profile_{profile.get('orcid', 'unknown')}.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        with col3:
            # PDF Export
            if images:
                pdf_filename = f"profile_{profile.get('orcid', 'unknown')}.pdf"
                with st.spinner("Generating PDF..."):
                    if generate_pdf_report(profile, publications, images, pdf_filename):
                        with open(pdf_filename, 'rb') as f:
                            st.download_button(
                                label=_('export_pdf'),
                                data=f,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                        os.remove(pdf_filename)
                    else:
                        st.warning("PDF generation failed")
    
    # Footer
    st.divider()
    st.caption("© Author Profile Analysis / Chimica Techno Acta | Created by daM")

if __name__ == "__main__":
    main()
