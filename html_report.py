# ============================================
# html_report.py
# Генерация HTML-отчёта (с сортировкой и фильтрами таблицы,
# секцией Retraction, Sources by Type без категории articles)
# ============================================

import html
import html as html_module
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (локальные копии,
# чтобы модуль был автономным и не тянул app.py)
# ============================================

def _get_filtered_publications(publications: List[Dict], start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
    """Фильтрует публикации по диапазону лет"""
    if start_year is None and end_year is None:
        return publications
    filtered = []
    for p in publications:
        pub_year = p.get('publication_year')
        if pub_year is None:
            continue
        if start_year is not None and pub_year < start_year:
            continue
        if end_year is not None and pub_year > end_year:
            continue
        filtered.append(p)
    return filtered


def _safe_translate(key: str, lang: str = 'en', **kwargs) -> str:
    """
    Локальная обёртка перевода: если app.py передал свою функцию translate —
    используем её (передаётся как атрибут модуля _translate_impl),
    иначе возвращаем key (в тестах). Реальная подстановка — через set_translate_impl().
    """
    impl = globals().get('_translate_impl')
    if impl is not None:
        return impl(key, lang, **kwargs)
    return key


def set_translate_impl(fn):
    """Устанавливает функцию перевода из app.py, чтобы не дублировать словарь LANG."""
    global _translate_impl
    _translate_impl = fn


def _format_affiliation_html(affil_name: str, institution_homepages: Optional[Dict[str, str]] = None) -> str:
    """Форматирует название аффилиации: если в institution_homepages есть ссылка — делает кликабельной."""
    escaped_name = html.escape(str(affil_name))
    if institution_homepages and isinstance(institution_homepages, dict):
        url = institution_homepages.get(affil_name)
        if url:
            return f'<a href="{html.escape(str(url))}" target="_blank" class="doi-link" style="font-size: inherit;">{escaped_name}</a>'
    return escaped_name


def _calculate_h_index(publications: List[Dict]) -> int:
    """Вычисляет h-index по списку публикаций."""
    if not publications:
        return 0
    citations = [p.get('cited_by_count', 0) for p in publications]
    citations_sorted = sorted([c for c in citations if c > 0], reverse=True)
    h_idx = 0
    for i, c in enumerate(citations_sorted, 1):
        if c >= i:
            h_idx = i
        else:
            break
    return h_idx


def _extract_sort_surname(author_name: str) -> str:
    """Возвращает ключ для алфавитной сортировки по имени/фамилии из app.py."""
    if not author_name:
        return ""
    clean_name = str(author_name).strip()
    parts = clean_name.split()
    if len(parts) > 1:
        return (parts[-1].lower() + " " + clean_name.lower())
    return clean_name.lower()


# ============================================
# JS ДЛЯ СОРТИРОВКИ И ФИЛЬТРАЦИИ ТАБЛИЦЫ PUBLICATION LIST
# ============================================

_PUBLICATIONS_TABLE_JS = r"""
<script>
(function() {
    function initPublicationsTable(tableId, filterBarId) {
        var table = document.getElementById(tableId);
        if (!table) return;
        var tbody = table.querySelector('tbody');
        if (!tbody) return;
        var filterBar = document.getElementById(filterBarId);

        // ==== ФИЛЬТРЫ ====
        var filters = {};
        if (filterBar) {
            var inputs = filterBar.querySelectorAll('[data-col-filter]');
            inputs.forEach(function(inp) {
                inp.addEventListener('input', function() {
                    filters[inp.getAttribute('data-col-filter')] = inp.value.toLowerCase().trim();
                    applyFilters();
                });
            });
            var yearFrom = filterBar.querySelector('.year-from-input, #year-from');
            var yearTo = filterBar.querySelector('.year-to-input, #year-to');
            if (yearFrom) yearFrom.addEventListener('input', applyFilters);
            if (yearTo) yearTo.addEventListener('input', applyFilters);
        }

        function getCellText(row, colIdx) {
            var cell = row.children[colIdx];
            return cell ? cell.textContent.trim() : '';
        }

        function applyFilters() {
            var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
            var yfEl = filterBar ? filterBar.querySelector('.year-from-input, #year-from') : null;
            var ytEl = filterBar ? filterBar.querySelector('.year-to-input, #year-to') : null;
            var yearFromVal = yfEl ? parseInt(yfEl.value, 10) : NaN;
            var yearToVal = ytEl ? parseInt(ytEl.value, 10) : NaN;
            var yearColIdx = -1;
            // определим индекс колонки Year по data-key на th
            table.querySelectorAll('thead th').forEach(function(th, i) {
                if (th.getAttribute('data-key') === 'year') yearColIdx = i;
            });

            rows.forEach(function(row) {
                var show = true;
                // текстовые фильтры
                Object.keys(filters).forEach(function(key) {
                    if (!filters[key]) return;
                    var colIdx = -1;
                    table.querySelectorAll('thead th').forEach(function(th, i) {
                        if (th.getAttribute('data-key') === key) colIdx = i;
                    });
                    if (colIdx >= 0) {
                        var txt = getCellText(row, colIdx).toLowerCase();
                        if (txt.indexOf(filters[key]) === -1) show = false;
                    }
                });
                // фильтр по годам (диапазон)
                if (show && yearColIdx >= 0 && (!isNaN(yearFromVal) || !isNaN(yearToVal))) {
                    var yv = parseInt(getCellText(row, yearColIdx), 10);
                    if (!isNaN(yv)) {
                        if (!isNaN(yearFromVal) && yv < yearFromVal) show = false;
                        if (!isNaN(yearToVal) && yv > yearToVal) show = false;
                    }
                }
                row.style.display = show ? '' : 'none';
            });
        }

        // ==== СОРТИРОВКА ====
        var sortState = { key: null, dir: 1 }; // 1 = asc, -1 = desc
        table.querySelectorAll('thead th').forEach(function(th, colIdx) {
            th.style.cursor = 'pointer';
            th.style.userSelect = 'none';
            th.addEventListener('click', function() {
                var key = th.getAttribute('data-key');
                if (!key) return;
                var numeric = th.getAttribute('data-numeric') === '1';
                if (sortState.key === key) {
                    sortState.dir = -sortState.dir;
                } else {
                    sortState.key = key;
                    sortState.dir = 1;
                }
                // сброс индикаторов
                table.querySelectorAll('thead th').forEach(function(h) {
                    h.classList.remove('sort-asc', 'sort-desc');
                    var ind = h.querySelector('.sort-indicator');
                    if (ind) ind.textContent = '';
                });
                th.classList.add(sortState.dir === 1 ? 'sort-asc' : 'sort-desc');
                var ind = th.querySelector('.sort-indicator');
                if (ind) ind.textContent = sortState.dir === 1 ? ' ▲' : ' ▼';

                var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
                rows.sort(function(a, b) {
                    var av = getCellText(a, colIdx);
                    var bv = getCellText(b, colIdx);
                    if (numeric) {
                        var an = parseFloat(av.replace(/[^\d.\-]/g, ''));
                        var bn = parseFloat(bv.replace(/[^\d.\-]/g, ''));
                        if (isNaN(an)) an = -Infinity;
                        if (isNaN(bn)) bn = -Infinity;
                        return (an - bn) * sortState.dir;
                    } else {
                        return av.localeCompare(bv) * sortState.dir;
                    }
                });
                rows.forEach(function(r) { tbody.appendChild(r); });
            });
        });
    }
    document.addEventListener('DOMContentLoaded', function() {
        initPublicationsTable('publications-table', 'publications-filter-bar');
        document.querySelectorAll('table.pub-table[id^="publications-table-"]').forEach(function(tbl) {
            var suffix = tbl.id.replace('publications-table-', '');
            initPublicationsTable(tbl.id, 'publications-filter-bar-' + suffix);
        });
    });
})();
</script>
"""


def _build_publications_table_html(
    filtered_publications: List[Dict],
    t,
    lang: str,
    with_filters: bool = True,
    table_suffix: str = "",
) -> str:
    """
    Строит таблицу публикаций с сортировкой и фильтрами (для HTML).
    Колонки: #, Title, Year, Journal, Citations, Citations/year, OA, DOI
    """
    table_id = f"publications-table-{table_suffix}" if table_suffix != "" else "publications-table"
    filter_bar_id = f"publications-filter-bar-{table_suffix}" if table_suffix != "" else "publications-filter-bar"
    year_from_id = f"year-from-{table_suffix}" if table_suffix != "" else "year-from"
    year_to_id = f"year-to-{table_suffix}" if table_suffix != "" else "year-to"

    # Строки таблицы
    rows_html = []
    sorted_pubs = sorted(filtered_publications, key=lambda x: x.get('publication_year', 0) or 0, reverse=True)
    for i, pub in enumerate(sorted_pubs, 1):
        title = html.escape(pub.get('title') or 'No title')
        year = pub.get('publication_year', 'N/A')
        journal = html.escape(pub.get('journal_name') or 'Unknown')
        citations = pub.get('cited_by_count', 0)
        cpy = pub.get('citations_per_year', 0)
        try:
            cpy_str = f"{float(cpy):.1f}"
        except Exception:
            cpy_str = "0.0"
        oa = '✅' if pub.get('is_oa', False) else '❌'
        doi = html.escape(pub.get('doi', '') or '')
        doi_cell = f'<a href="https://doi.org/{doi}" target="_blank" class="doi-link">{doi}</a>' if doi else ''
        rows_html.append(
            f"<tr>"
            f"<td>{i}</td>"
            f"<td>{title[:200]}</td>"
            f"<td>{year}</td>"
            f"<td>{journal}</td>"
            f"<td>{citations}</td>"
            f"<td>{cpy_str}</td>"
            f"<td>{oa}</td>"
            f"<td>{doi_cell}</td>"
            f"</tr>"
        )

    filter_bar = ""
    if with_filters:
        filter_bar = f"""
        <div id="{filter_bar_id}" class="pub-filter-bar">
            <div class="pub-filter-item">
                <label>{t('title')}:</label>
                <input type="text" data-col-filter="title" placeholder="{t('title')}...">
            </div>
            <div class="pub-filter-item">
                <label>{t('journal')}:</label>
                <input type="text" data-col-filter="journal" placeholder="{t('journal')}...">
            </div>
            <div class="pub-filter-item pub-filter-years">
                <label>{t('year')}:</label>
                <input type="number" id="{year_from_id}" class="year-from-input" placeholder="от" min="1900" max="2100">
                <span>—</span>
                <input type="number" id="{year_to_id}" class="year-to-input" placeholder="до" min="1900" max="2100">
            </div>
            <div class="pub-filter-reset">
                <button type="button" onclick="(function(){{
                    var bar = document.getElementById('{filter_bar_id}');
                    if (!bar) return;
                    bar.querySelectorAll('[data-col-filter]').forEach(function(i){{i.value=''; i.dispatchEvent(new Event('input'));}});
                    var yf=document.getElementById('{year_from_id}'); var yt=document.getElementById('{year_to_id}');
                    if(yf){{yf.value=''; yf.dispatchEvent(new Event('input'));}}
                    if(yt){{yt.value=''; yt.dispatchEvent(new Event('input'));}}
                }})()">✕ {t('clear_cache') if False else 'Сброс'}</button>
            </div>
        </div>
        """

    table_html = f"""
    {filter_bar}
    <div class="pub-table-wrapper">
        <table id="{table_id}" class="pub-table">
            <thead>
                <tr>
                    <th data-key="idx" data-numeric="1">#<span class="sort-indicator"></span></th>
                    <th data-key="title" data-numeric="0">{t('title')}<span class="sort-indicator"></span></th>
                    <th data-key="year" data-numeric="1">{t('year')}<span class="sort-indicator"></span></th>
                    <th data-key="journal" data-numeric="0">{t('journal')}<span class="sort-indicator"></span></th>
                    <th data-key="citations" data-numeric="1">{t('citations')}<span class="sort-indicator"></span></th>
                    <th data-key="cpy" data-numeric="1">{t('citations_per_year')}<span class="sort-indicator"></span></th>
                    <th data-key="oa" data-numeric="0">OA<span class="sort-indicator"></span></th>
                    <th data-key="doi" data-numeric="0">{t('doi')}<span class="sort-indicator"></span></th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    <p><em>{t('publications')}: {len(filtered_publications)}</em></p>
    """
    return table_html


# ============================================
# СЕКЦИЯ RETRACTION
# ============================================

def _build_retraction_section_html(retracted_publications: List[Dict], t, lang: str, section_id: str = "retraction") -> str:
    """Строит секцию Retraction со списком всех ретрагированных статей."""
    if not retracted_publications:
        return ""
    rows = []
    for p in retracted_publications:
        title = html.escape(p.get('title') or 'No title')
        year = p.get('publication_year', 'N/A')
        journal = html.escape(p.get('journal_name') or 'Unknown')
        doi = html.escape(p.get('doi', '') or '')
        doi_cell = f'<a href="https://doi.org/{doi}" target="_blank" class="doi-link">{doi}</a>' if doi else '—'
        retr_info = p.get('retraction_info') or {}
        reason = ''
        if isinstance(retr_info, dict):
            reason = retr_info.get('reason') or retr_info.get('note') or ''
        reason = html.escape(str(reason)) if reason else '—'
        rows.append(
            f"<tr>"
            f"<td>{title}</td>"
            f"<td>{year}</td>"
            f"<td>{journal}</td>"
            f"<td>{doi_cell}</td>"
            f"<td>{reason}</td>"
            f"</tr>"
        )
    return f"""
    <div id="{section_id}" class="section">
        <div class="section-title">🚫 Retraction</div>
        <div class="retraction-warning">⚠️ {t('retraction_warning', count=len(retracted_publications))}</div>
        <div class="pub-table-wrapper">
            <table class="pub-table">
                <thead>
                    <tr>
                        <th>{t('title')}</th>
                        <th>{t('year')}</th>
                        <th>{t('journal')}</th>
                        <th>{t('doi')}</th>
                        <th>Причина</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </div>
    """


# ============================================
# СЕКЦИЯ SOURCES BY TYPE (без articles)
# ============================================

def _build_sources_section_html(source_categories: Dict, t, lang: str, section_id: str = "sources") -> str:
    """
    Строит секцию Sources by Type. Категория articles ИСКЛЮЧЕНА
    (самая массовая группа). Включаются repositories, ebooks, proceedings, other.
    """
    if not source_categories:
        return ""

    category_labels = {
        'repositories': 'source_repositories',
        'ebooks': 'source_ebooks',
        'proceedings': 'source_proceedings',
        'other': 'source_other',
    }
    category_order = ['repositories', 'ebooks', 'proceedings', 'other']

    # Проверяем, что есть хотя бы одна непустая не-articles категория
    has_any = any(cat in source_categories and source_categories[cat].get('count', 0) > 0 for cat in category_order)
    if not has_any:
        return ""

    rows_html = []
    for cat in category_order:
        if cat not in source_categories:
            continue
        cat_data = source_categories[cat]
        count = cat_data.get('count', 0)
        if count <= 0:
            continue
        items = cat_data.get('items', [])
        label_key = category_labels.get(cat)
        label = t(label_key) if label_key else cat

        examples_html = ""
        if items:
            for item in items[:3]:
                title = item.get('title', 'No title') or 'No title'
                doi = item.get('doi', '') or ''
                item_id = item.get('id', '') or ''
                title_esc = html.escape(title[:80])
                if doi:
                    examples_html += (
                        f'<div class="source-example-item">• {title_esc} — '
                        f'<a href="https://doi.org/{html.escape(doi)}" target="_blank" class="source-example-link">'
                        f'DOI: {html.escape(doi[:25])}{"..." if len(doi) > 25 else ""}</a> '
                        f'<span class="source-badge source-badge-doi">✅ {t("source_doi_available")}</span></div>'
                    )
                elif item_id:
                    examples_html += (
                        f'<div class="source-example-item">• {title_esc} — '
                        f'<a href="{html.escape(item_id)}" target="_blank" class="source-example-link">'
                        f'{t("source_view_link")}</a> '
                        f'<span class="source-badge source-badge-nodoi">⚠️ {t("source_no_doi")}</span></div>'
                    )
                else:
                    examples_html += (
                        f'<div class="source-example-item">• {title_esc} '
                        f'<span class="source-badge source-badge-nodoi">⚠️ {t("source_no_link")}</span></div>'
                    )
        else:
            examples_html = f'<em>{t("no_publications")}</em>'

        rows_html.append(
            f"<tr>"
            f"<td><strong>{label}</strong><br><span class=\"src-count\">{count}</span></td>"
            f"<td>{examples_html}</td>"
            f"</tr>"
        )

    return f"""
    <div id="{section_id}" class="section">
        <div class="section-title">{t('source_types')}</div>
        <table class="source-table">
            <thead>
                <tr>
                    <th>{t('source_count')}</th>
                    <th>{t('source_examples')}</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    """


# ============================================
# CSS ДЛЯ ТАБЛИЦ (сортировка / фильтры / retraction)
# ============================================

def _build_table_styles(primary: str, secondary: str) -> str:
    return f"""
    <style>
        .pub-filter-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: flex-end;
            background: #f8f9fa;
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 12px;
            border-left: 4px solid {primary};
        }}
        .pub-filter-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            font-size: 12px;
            color: #555;
        }}
        .pub-filter-item label {{
            font-weight: 600;
            font-family: 'Times New Roman', serif;
        }}
        .pub-filter-item input {{
            padding: 6px 10px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 13px;
            min-width: 160px;
            font-family: 'Times New Roman', serif;
        }}
        .pub-filter-years {{
            flex-direction: row;
            align-items: center;
            gap: 6px;
        }}
        .pub-filter-years input {{
            min-width: 80px;
            width: 80px;
        }}
        .pub-filter-years label {{
            margin-right: 4px;
        }}
        .pub-filter-reset button {{
            padding: 7px 14px;
            border: 1px solid {primary};
            background: white;
            color: {primary};
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .pub-filter-reset button:hover {{
            background: {primary};
            color: white;
        }}
        .pub-table-wrapper {{
            overflow-x: auto;
            margin: 15px 0;
        }}
        .pub-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: 'Times New Roman', serif;
        }}
        .pub-table th {{
            background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }}
        .pub-table th:hover {{
            filter: brightness(1.1);
        }}
        .pub-table th.sort-asc .sort-indicator,
        .pub-table th.sort-desc .sort-indicator {{
            font-size: 12px;
            opacity: 1;
        }}
        .pub-table td {{
            padding: 10px;
            border-bottom: 1px solid #BDC3C7;
            vertical-align: top;
        }}
        .pub-table tr:hover {{
            background-color: #f5f5f5;
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
        .src-count {{
            font-size: 12px;
            color: #666;
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
        .source-badge-doi {{ background: #d4edda; color: #155724; }}
        .source-badge-nodoi {{ background: #f8d7da; color: #721c24; }}
        .retraction-warning {{
            background: #FFE5E5;
            border-left: 4px solid #FF0000;
            color: #CC0000;
            font-weight: bold;
            padding: 12px 15px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 16px;
        }}
        .sidebar-author-group {{
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.25);
        }}
        .sidebar-author-group:last-child {{
            border-bottom: none;
        }}
        .sidebar-author-title {{
            font-size: 15px;
            font-weight: 700;
            color: #fff;
            padding: 6px 10px;
            margin-bottom: 4px;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 6px;
            word-break: break-word;
        }}
        .sidebar-sublink {{
            font-size: 13px;
            padding: 6px 12px 6px 20px !important;
            margin: 2px 0 !important;
        }}
    </style>
    """


# ============================================
# ПОЛНЫЙ РЕНДЕРИНГ БЛОКА ОДНОГО АВТОРА (ДЛЯ ОДИНОЧНОГО И МУЛЬТИ-ОТЧЁТА)
# ============================================

def _build_single_author_full_sections(
    profile: Dict,
    publications: List[Dict],
    images: Optional[Dict[str, str]],
    institution_homepages: Optional[Dict[str, str]],
    primary: str,
    secondary: str,
    lang: str,
    coauthor_profiles: Optional[Dict],
    start_year: Optional[int],
    end_year: Optional[int],
    create_visualizations_fn=None,
    id_prefix: str = "",
    table_suffix: str = "",
) -> Tuple[str, str, int]:
    """
    Генерирует полный HTML-блок секций одного автора и HTML-ссылки для бокового меню.
    Возвращает кортеж: (body_html, sidebar_links_html, h_index).
    """
    t = lambda key, **kw: _safe_translate(key, lang, **kw)

    sec_overview = f"{id_prefix}overview"
    sec_metrics = f"{id_prefix}metrics"
    sec_visualizations = f"{id_prefix}visualizations"
    sec_thematic = f"{id_prefix}thematic"
    sec_collaborations = f"{id_prefix}collaborations"
    sec_coauthors = f"{id_prefix}coauthors"
    sec_retraction = f"{id_prefix}retraction"
    sec_sources = f"{id_prefix}sources"
    sec_stats = f"{id_prefix}stats"
    sec_publications = f"{id_prefix}publications"

    # Фильтрация по годам
    filtered_publications = _get_filtered_publications(publications, start_year, end_year)
    filter_info = None
    if start_year is not None or end_year is not None:
        years_f = [p.get('publication_year') for p in filtered_publications if p.get('publication_year')]
        if years_f:
            filter_info = t('temporal_gap_filter_info', start_year=min(years_f), end_year=max(years_f))

    # Пересчёт визуализаций под отфильтрованные данные (если не переданы готовые или активен фильтр)
    if create_visualizations_fn is not None and (
        not images
        or all(v == '' for v in images.values() if v is not None)
        or start_year is not None
        or end_year is not None
    ):
        filtered_profile = dict(profile)
        if start_year is not None or end_year is not None:
            yrs = [p.get('publication_year') for p in filtered_publications if p.get('publication_year')]
            filtered_profile['years_distribution'] = dict(Counter(yrs)) if yrs else {}
            journals_f = [p.get('journal_name') for p in filtered_publications if p.get('journal_name')]
            filtered_profile['top_journals'] = dict(Counter(journals_f).most_common(10)) if journals_f else {}
            oa_f = [p.get('open_access_status') for p in filtered_publications if p.get('open_access_status')]
            filtered_profile['open_access'] = dict(Counter(oa_f)) if oa_f else {}
            publishers_f = [p.get('publisher') for p in filtered_publications if p.get('publisher') and p.get('publisher') != 'Unknown']
            filtered_profile['publishers'] = dict(Counter(publishers_f)) if publishers_f else {}
            affs_f = []
            for p in filtered_publications:
                if p.get('affiliations'):
                    affs_f.extend(p['affiliations'])
            filtered_profile['top_affiliations'] = dict(Counter(affs_f).most_common(5)) if affs_f else {}
            sp = sorted(filtered_publications, key=lambda x: x.get('cited_by_count', 0), reverse=True)
            filtered_profile['most_cited'] = [
                {
                    'title': p.get('title', 'No title'),
                    'citations': p.get('cited_by_count', 0),
                    'year': p.get('publication_year', 'Unknown'),
                    'journal': p.get('journal_name', 'Unknown'),
                    'doi': p.get('doi', ''),
                }
                for p in sp[:10]
            ]
            cf = [p.get('cited_by_count', 0) for p in filtered_publications]
            if cf:
                bins = [0, 1, 5, 10, 20, 50, 100, 500, 1000]
                cdist = {}
                for j in range(len(bins) - 1):
                    cdist[f"{bins[j]}-{bins[j+1]}"] = sum(1 for c in cf if bins[j] <= c < bins[j+1])
                cdist[f">{bins[-1]}"] = sum(1 for c in cf if c >= bins[-1])
                filtered_profile['citation_distribution'] = cdist
            else:
                filtered_profile['citation_distribution'] = {}

            c_cnt = defaultdict(int)
            d_cnt = defaultdict(int)
            f_cnt = defaultdict(int)
            t_cnt = defaultdict(int)
            s_cnt = defaultdict(int)
            for p in filtered_publications:
                for c in set(p.get('concepts', []) or []):
                    c_cnt[c] += 1
                for d in set(p.get('domains', []) or []):
                    d_cnt[d] += 1
                for f in set(p.get('fields', []) or []):
                    f_cnt[f] += 1
                for tp in set(p.get('topics_old', []) or []):
                    t_cnt[tp] += 1
                for s in set(p.get('subtopics', []) or []):
                    s_cnt[s] += 1
            if c_cnt:
                filtered_profile['top_concepts'] = dict(sorted(c_cnt.items(), key=lambda x: x[1], reverse=True)[:15])
                filtered_profile['concepts'] = dict(c_cnt)
            if f_cnt:
                filtered_profile['top_fields'] = dict(sorted(f_cnt.items(), key=lambda x: x[1], reverse=True)[:10])
                filtered_profile['fields'] = dict(f_cnt)
            if d_cnt:
                filtered_profile['top_domains'] = dict(sorted(d_cnt.items(), key=lambda x: x[1], reverse=True)[:5])
                filtered_profile['domains'] = dict(d_cnt)
            if t_cnt:
                filtered_profile['top_topics'] = dict(sorted(t_cnt.items(), key=lambda x: x[1], reverse=True)[:15])
                filtered_profile['topics'] = dict(t_cnt)
            if s_cnt:
                filtered_profile['top_subtopics'] = dict(sorted(s_cnt.items(), key=lambda x: x[1], reverse=True)[:20])
                filtered_profile['subtopics'] = dict(s_cnt)

        images = create_visualizations_fn(filtered_profile, lang)

    if images is None:
        images = {}

    # Пересчёт метрик по отфильтрованным публикациям
    total_pubs = len(filtered_publications)
    h_index = g_index = i10_index = i100_index = 0
    total_citations = 0
    avg_citations = 0.0
    median_citations = 0.0
    max_citations = 0
    oa_percentage = 0.0

    if filtered_publications:
        citations = [p.get('cited_by_count', 0) for p in filtered_publications]
        total_citations = sum(citations)
        avg_citations = sum(citations) / len(citations) if citations else 0
        median_citations = float(np.median(citations)) if citations else 0
        max_citations = max(citations) if citations else 0
        citations_sorted = sorted([c for c in citations if c > 0], reverse=True)
        for i, c in enumerate(citations_sorted, 1):
            if c >= i:
                h_index = i
            else:
                break
        i10_index = sum(1 for c in citations if c >= 10)
        i100_index = sum(1 for c in citations if c >= 100)
        total_citations_sorted = 0
        for i, c in enumerate(citations_sorted, 1):
            total_citations_sorted += c
            if total_citations_sorted >= i * i:
                g_index = i
        total_oa = sum(1 for p in filtered_publications if p.get('is_oa', False))
        oa_percentage = (total_oa / len(filtered_publications) * 100) if filtered_publications else 0

    # Тематические агрегаты по отфильтрованным данным
    concept_counter = defaultdict(int)
    domain_counter = defaultdict(int)
    field_counter = defaultdict(int)
    topic_counter = defaultdict(int)
    subtopic_counter = defaultdict(int)
    primary_counter = defaultdict(int)
    subfield_counter = defaultdict(int)
    keyword_counter = defaultdict(int)

    for p in filtered_publications:
        if p.get('concepts'):
            for c in set(p['concepts']):
                concept_counter[c] += 1
        if p.get('domains'):
            for d in set(p['domains']):
                domain_counter[d] += 1
        if p.get('fields'):
            for f in set(p['fields']):
                field_counter[f] += 1
        if p.get('topics_old'):
            for tp in set(p['topics_old']):
                topic_counter[tp] += 1
        if p.get('subtopics'):
            for s in set(p['subtopics']):
                subtopic_counter[s] += 1
        if p.get('primary_topic') and p['primary_topic'].get('display_name'):
            primary_counter[p['primary_topic']['display_name']] += 1
        if p.get('primary_topic') and p['primary_topic'].get('subfield'):
            subfield_counter[p['primary_topic']['subfield']] += 1
        if p.get('keywords'):
            for k in set(p['keywords']):
                keyword_counter[k] += 1

    # Фоллбэк на данные профиля, если в самих публикациях нет развёрнутых primary_topic/keywords
    top_primary_topics = (
        dict(sorted(primary_counter.items(), key=lambda x: x[1], reverse=True)[:10])
        if primary_counter else dict(list((profile.get('top_topics') or {}).items())[:10])
    )
    top_subfields = (
        dict(sorted(subfield_counter.items(), key=lambda x: x[1], reverse=True)[:10])
        if subfield_counter else dict(list((profile.get('top_subtopics') or {}).items())[:10])
    )
    top_fields = (
        dict(sorted(field_counter.items(), key=lambda x: x[1], reverse=True)[:10])
        if field_counter else dict(list((profile.get('top_fields') or {}).items())[:10])
    )
    top_domains = (
        dict(sorted(domain_counter.items(), key=lambda x: x[1], reverse=True)[:5])
        if domain_counter else dict(list((profile.get('top_domains') or {}).items())[:5])
    )
    top_keywords = (
        dict(sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:20])
        if keyword_counter else (
            dict(sorted(concept_counter.items(), key=lambda x: x[1], reverse=True)[:20])
            if concept_counter else dict(list((profile.get('top_concepts') or {}).items())[:20])
        )
    )

    # Годы
    years = [p.get('publication_year') for p in filtered_publications if p.get('publication_year')]
    active_years = len(set(years)) if years else 0
    papers_per_year = (len(filtered_publications) / active_years) if active_years else 0
    first_pub_year = min(years) if years else profile.get('first_publication', 'N/A')
    last_pub_year = max(years) if years else profile.get('last_publication', 'N/A')

    # Тренд
    trend = 'unknown'
    trend_corr = 0.0
    if len(years) >= 3:
        year_counts = Counter(years)
        sorted_years = sorted(set(years))
        years_range = range(min(sorted_years), max(sorted_years) + 1)
        counts = [year_counts.get(y, 0) for y in years_range]
        if len(counts) >= 3:
            x = np.arange(len(counts))
            z = np.polyfit(x, counts, 1)
            if len(counts) > 1:
                corr_matrix = np.corrcoef(x, counts)
                trend_corr = float(corr_matrix[0, 1]) if len(corr_matrix) > 1 else 0.0
            if z[0] > 1.0:
                trend = 'strong_up'
            elif z[0] > 0.3:
                trend = 'up'
            elif z[0] < -1.0:
                trend = 'strong_down'
            elif z[0] < -0.3:
                trend = 'down'
            else:
                trend = 'stable'

    # Ретрагированные и прочие флаги
    retracted_publications = [p for p in filtered_publications if p.get('is_retracted', False)]
    retractions = len(retracted_publications)
    corrections = sum(1 for p in filtered_publications if p.get('is_correction', False))

    # Соавторы
    unique_coauthors = len(set([a for p in filtered_publications for a in p.get('authors', [])]))
    avg_authors_list = [p.get('author_count', 0) for p in filtered_publications if p.get('author_count', 0) > 0]
    avg_authors = float(np.mean(avg_authors_list)) if avg_authors_list else 0.0

    # Профиль
    author_name = profile.get('author_name', 'Unknown')
    author_affiliations = profile.get('author_affiliations', [])
    author_countries = profile.get('author_countries', [])
    author_orcid = profile.get('orcid', 'N/A')

    # Коллаборации (пересчёт с учётом фильтра по годам, если в публикациях есть данные, иначе из profile)
    collaborations = profile.get('collaborations', {})
    author_affils = set(profile.get('author_affiliations', []))
    author_country_set = set(profile.get('author_countries', []))

    if (start_year is not None or end_year is not None) and any(
        p.get('countries') or p.get('affiliations_by_country') for p in filtered_publications
    ):
        domestic_papers = 0
        international_papers = 0
        dom_map: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        int_map: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        all_collab_countries = Counter()

        for p in filtered_publications:
            p_countries = set(p.get('countries') or [])
            aff_by_country = p.get('affiliations_by_country') or {}
            if not p_countries and isinstance(aff_by_country, dict):
                p_countries = set(aff_by_country.keys())
            other_countries = p_countries - author_country_set
            if other_countries:
                international_papers += 1
                for c_name in other_countries:
                    all_collab_countries[c_name] += 1
            elif p_countries and (p_countries & author_country_set):
                domestic_papers += 1

            if isinstance(aff_by_country, dict):
                for c_name, aff_list in aff_by_country.items():
                    for af in set(aff_list or []):
                        if af in author_affils:
                            continue
                        if c_name in author_country_set:
                            dom_map[c_name][af] += 1
                        else:
                            int_map[c_name][af] += 1

        domestic_collab_filtered = {k: dict(v) for k, v in dom_map.items() if v}
        international_collab_filtered = {k: dict(v) for k, v in int_map.items() if v}
        if not domestic_collab_filtered and not international_collab_filtered:
            for country, affils_dict in collaborations.get('domestic', {}).items():
                filtered_d = {k: v for k, v in affils_dict.items() if k not in author_affils}
                if filtered_d:
                    domestic_collab_filtered[country] = filtered_d
            for country, affils_dict in collaborations.get('international', {}).items():
                filtered_i = {k: v for k, v in affils_dict.items() if k not in author_affils}
                if filtered_i:
                    international_collab_filtered[country] = filtered_i
        most_collab_country = (
            all_collab_countries.most_common(1)[0][0]
            if all_collab_countries else profile.get('most_collaborative_country', 'None')
        )
        country_diversity = len(all_collab_countries) if all_collab_countries else profile.get('country_diversity', 0)
        collab_index = profile.get('collaboration_index', 0)
        domestic_ratio = (domestic_papers / total_pubs * 100) if total_pubs else 0.0
        international_ratio = (international_papers / total_pubs * 100) if total_pubs else 0.0
    else:
        domestic_papers = collaborations.get('domestic_papers', 0)
        international_papers = collaborations.get('international_papers', 0)
        domestic_collab_filtered = {}
        for country, affils_dict in collaborations.get('domestic', {}).items():
            filtered_d = {k: v for k, v in affils_dict.items() if k not in author_affils}
            if filtered_d:
                domestic_collab_filtered[country] = filtered_d
        international_collab_filtered = {}
        for country, affils_dict in collaborations.get('international', {}).items():
            filtered_i = {k: v for k, v in affils_dict.items() if k not in author_affils}
            if filtered_i:
                international_collab_filtered[country] = filtered_i
        most_collab_country = profile.get('most_collaborative_country', 'None')
        collab_index = profile.get('collaboration_index', 0)
        country_diversity = profile.get('country_diversity', 0)
        domestic_ratio = profile.get('domestic_papers_ratio', 0) * 100
        international_ratio = profile.get('international_papers_ratio', 0) * 100

    # Соавторы с ORCID
    top_coauthors_with_orcids = profile.get('top_coauthors_with_orcids', {})
    if not top_coauthors_with_orcids or start_year is not None or end_year is not None:
        coauthors_recalc = {}
        for p in filtered_publications:
            for auth in (p.get('authors_with_orcids') or []):
                nm = auth.get('name', '')
                oc = auth.get('orcid', '')
                if nm and nm != author_name:
                    if nm not in coauthors_recalc:
                        coauthors_recalc[nm] = {'count': 0, 'orcid': oc}
                    coauthors_recalc[nm]['count'] += 1
                    if oc and not coauthors_recalc[nm].get('orcid'):
                        coauthors_recalc[nm]['orcid'] = oc
        if coauthors_recalc:
            # Дополняем ORCID из профиля, если в статье он не был указан
            for nm, d_val in coauthors_recalc.items():
                if not d_val.get('orcid') and nm in (profile.get('top_coauthors_with_orcids') or {}):
                    d_val['orcid'] = profile['top_coauthors_with_orcids'][nm].get('orcid', '')
            top_coauthors_with_orcids = dict(
                sorted(coauthors_recalc.items(), key=lambda x: x[1]['count'], reverse=True)[:15]
            )

    if coauthor_profiles is None:
        coauthor_profiles = profile.get('coauthor_profiles', {})

    # ====== БЛОКИ ======
    # Секция Retraction
    retraction_section_html = _build_retraction_section_html(retracted_publications, t, lang, section_id=sec_retraction)

    # Секция Sources by Type (без articles)
    sources_section_html = _build_sources_section_html(profile.get('source_categories', {}), t, lang, section_id=sec_sources)

    # Таблица публикаций с фильтрами
    publications_table_html = _build_publications_table_html(
        filtered_publications, t, lang, with_filters=True, table_suffix=table_suffix
    )

    # Карточки соавторов
    coauthors_html = ""
    if top_coauthors_with_orcids:
        for name, data in list(top_coauthors_with_orcids.items())[:15]:
            count = data.get('count', 0)
            orcid = data.get('orcid', '')
            clean = orcid.replace('https://orcid.org/', '').strip() if orcid else ''
            person_info = coauthor_profiles.get(clean) or coauthor_profiles.get(orcid) or {}
            links = person_info.get('links', []) if isinstance(person_info, dict) else []
            coauthors_html += f'<div class="coauthor-card"><div class="coauthor-name">{html.escape(name)}</div>'
            coauthors_html += f'<div class="coauthor-joint">{count} {t("joint_works")}</div>'
            if orcid:
                coauthors_html += f'<div style="margin-bottom:8px;"><a href="https://orcid.org/{html.escape(clean)}" target="_blank" class="coauthor-profile-link orcid">🆔 ORCID: {html.escape(clean)}</a></div>'
            if links:
                coauthors_html += generate_coauthor_links_html(links, lang)
            else:
                coauthors_html += '<p class="no-links">No additional links found</p>'
            coauthors_html += '</div>'
    else:
        coauthors_html = f'<p>{t("no_publications")}</p>'

    # Фильтр-инфо
    filter_info_html = ""
    if filter_info:
        filter_info_html = f"""
        <div style="background: #e8f4f8; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid {primary};">
            <strong>{filter_info}</strong>
            <span style="margin-left: 15px; font-size: 13px; color: #555;">
                {t('temporal_gap_original_count', count=len(publications))} |
                {t('temporal_gap_filtered_count', count=len(filtered_publications))}
            </span>
        </div>
        """

    # Ретракционный флаг (короткий, сверху)
    retraction_flag_html = ""
    if retractions > 0:
        retraction_flag_html = f'<div class="flag-retraction">⚠️ {t("retraction_warning", count=retractions)}</div>'

    # Аффилиации автора с поддержкой institution_homepages
    affiliations_formatted = ""
    if author_affiliations:
        affil_links = [_format_affiliation_html(af, institution_homepages) for af in author_affiliations[:5]]
        affiliations_formatted = f'<div class="author-affil"><strong>{t("affiliations")}:</strong> {", ".join(affil_links)}</div>'

    # Коллаборации с поддержкой institution_homepages
    domestic_collab_html = (
        ''.join([
            f'<div class="collab-country">📍 {html.escape(country)}</div>'
            + ''.join([
                f'<div class="collab-affil-item">• <strong>{_format_affiliation_html(affil, institution_homepages)}</strong>: {count} {t("articles")}</div>'
                for affil, count in list(affils.items())[:10]
            ])
            for country, affils in list(domestic_collab_filtered.items())
        ])
        if domestic_collab_filtered else f'<p>{t("no_data_collab")}</p>'
    )

    international_collab_html = (
        ''.join([
            f'<div class="collab-country">📍 {html.escape(country)}</div>'
            + ''.join([
                f'<div class="collab-affil-item">• <strong>{_format_affiliation_html(affil, institution_homepages)}</strong>: {count} {t("articles")}</div>'
                for affil, count in list(affils.items())[:10]
            ])
            for country, affils in list(international_collab_filtered.items())
        ])
        if international_collab_filtered else f'<p>{t("no_data_collab")}</p>'
    )

    # Боковое меню для данного автора
    sub_cls = ' class="sidebar-sublink"' if id_prefix else ''
    sidebar_items = (
        f'<a href="#{sec_overview}"{sub_cls}>📊 {t("profile")}</a>'
        f'<a href="#{sec_metrics}"{sub_cls}>📈 {t("main_metrics")}</a>'
        f'<a href="#{sec_visualizations}"{sub_cls}>📊 {t("citations")}</a>'
        f'<a href="#{sec_thematic}"{sub_cls}>🏷️ {t("topics")}</a>'
        f'<a href="#{sec_collaborations}"{sub_cls}>🌍 {t("collaborations")}</a>'
        f'<a href="#{sec_coauthors}"{sub_cls}>🤝 {t("top_coauthors")}</a>'
        f'{f"""<a href="#{sec_retraction}"{sub_cls}>🚫 Retraction</a>""" if retraction_section_html else ""}'
        f'{f"""<a href="#{sec_sources}"{sub_cls}>📚 {t("source_types")}</a>""" if sources_section_html else ""}'
        f'<a href="#{sec_stats}"{sub_cls}>📊 Statistics</a>'
        f'<a href="#{sec_publications}"{sub_cls}>📚 {t("publications")}</a>'
    )

    body_html = f"""
            <div id="{sec_overview}" class="section">
                <div class="section-title">📋 {t('profile')}</div>
                {filter_info_html}
                <div class="author-info">
                    <div class="author-name">{html.escape(author_name)}</div>
                    <div class="author-affil"><strong>{t('orcid')}:</strong> <a href="https://orcid.org/{html.escape(author_orcid)}" target="_blank">{html.escape(author_orcid)}</a></div>
                    {affiliations_formatted}
                    {f'<div class="author-affil"><strong>{t("countries")}:</strong> {html.escape(", ".join(author_countries))}</div>' if author_countries else ''}
                    <div class="author-affil"><strong>{t('total_analyzed')}:</strong> {total_pubs}</div>
                </div>
                {retraction_flag_html}
            </div>

            <div id="{sec_metrics}" class="section">
                <div class="section-title">📈 {t('main_metrics')}</div>
                <div class="metrics-grid">
                    <div class="metric-card"><div class="metric-value">{total_pubs}</div><div class="metric-label">{t('publications')}</div></div>
                    <div class="metric-card"><div class="metric-value">{h_index}</div><div class="metric-label">{t('h_index')}</div></div>
                    <div class="metric-card"><div class="metric-value">{g_index}</div><div class="metric-label">{t('g_index')}</div></div>
                    <div class="metric-card"><div class="metric-value">{i10_index}</div><div class="metric-label">{t('i10_index')}</div></div>
                    <div class="metric-card"><div class="metric-value">{i100_index}</div><div class="metric-label">{t('i100_index')}</div></div>
                    <div class="metric-card"><div class="metric-value">{total_citations:,}</div><div class="metric-label">{t('total_citations')}</div></div>
                    <div class="metric-card"><div class="metric-value">{avg_citations:.1f}</div><div class="metric-label">{t('avg_citations')}</div></div>
                    <div class="metric-card"><div class="metric-value">{median_citations:.0f}</div><div class="metric-label">{t('median_citations')}</div></div>
                    <div class="metric-card"><div class="metric-value">{oa_percentage:.1f}%</div><div class="metric-label">{t('open_access')}</div></div>
                </div>
            </div>

            <div id="{sec_visualizations}" class="section">
                <div class="section-title">📊 {t('citations')}</div>
                <div class="chart-container"><img src="data:image/png;base64,{images.get('years_chart', '')}" alt="{t('years_chart_title')}"></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="chart-container"><img src="data:image/png;base64,{images.get('journals_chart', '')}" alt="{t('journals_chart_title')}"></div>
                    <div class="chart-container"><img src="data:image/png;base64,{images.get('oa_chart', '')}" alt="{t('oa_chart_title')}"></div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="chart-container"><img src="data:image/png;base64,{images.get('publishers_chart', '')}" alt="{t('publishers_chart_title')}"></div>
                    <div class="chart-container"><img src="data:image/png;base64,{images.get('affiliations_chart', '')}" alt="{t('affiliations_chart_title')}"></div>
                </div>
                <div class="chart-container"><img src="data:image/png;base64,{images.get('wordcloud', '')}" alt="{t('wordcloud_title')}"></div>
                <div class="chart-container"><img src="data:image/png;base64,{images.get('citations_chart', '')}" alt="{t('citations_chart_title')}"></div>
                <div class="chart-container"><img src="data:image/png;base64,{images.get('citation_distribution', '')}" alt="{t('citation_distribution_title')}"></div>
                <div class="chart-container"><img src="data:image/png;base64,{images.get('thematic_structure', '')}" alt="{t('thematic_structure_title')}"></div>
                {f'<div class="chart-container"><img src="data:image/png;base64,{images.get("radar_chart", "")}" alt="{t("radar_title")}"></div>' if images.get('radar_chart') else ''}
            </div>

            <div id="{sec_thematic}" class="section">
                <div class="section-title">🏷️ {t('topics')}</div>
                <h3 style="color: {primary}; margin-top: 20px;">{t('topics')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([f'<div class="thematic-card"><div class="thematic-name">{html.escape(topic)}</div><div class="thematic-count">📄 {count} {t("articles")}</div></div>' for topic, count in list(top_primary_topics.items())[:5]])}
                </div>
                <h3 style="color: {primary}; margin-top: 20px;">{t('subtopics')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([f'<div class="thematic-card"><div class="thematic-name">{html.escape(sub)}</div><div class="thematic-count">📄 {count} {t("articles")}</div></div>' for sub, count in list(top_subfields.items())[:5]])}
                </div>
                <h3 style="color: {primary}; margin-top: 20px;">{t('fields')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([f'<div class="thematic-card"><div class="thematic-name">{html.escape(f)}</div><div class="thematic-count">📄 {count} {t("articles")}</div></div>' for f, count in list(top_fields.items())[:5]])}
                </div>
                <h3 style="color: {primary}; margin-top: 20px;">{t('domains')} (Top 5)</h3>
                <div class="thematic-grid">
                    {''.join([f'<div class="thematic-card"><div class="thematic-name">{html.escape(d)}</div><div class="thematic-count">📄 {count} {t("articles")}</div></div>' for d, count in list(top_domains.items())[:5]])}
                </div>
                <h3 style="color: {primary}; margin-top: 20px;">{t('concepts')} (Top 10)</h3>
                <div class="thematic-grid">
                    {''.join([f'<div class="thematic-card"><div class="thematic-name">{html.escape(k)}</div><div class="thematic-count">📄 {count} {t("articles")}</div></div>' for k, count in list(top_keywords.items())[:10]])}
                </div>
            </div>

            <div id="{sec_collaborations}" class="section">
                <div class="section-title">{t('collaborations')}</div>
                <div class="collab-grid">
                    <div class="collab-box">
                        <h4>{t('domestic')}</h4>
                        <p><strong>{t('papers')}:</strong> {domestic_papers}</p>
                        {domestic_collab_html}
                    </div>
                    <div class="collab-box">
                        <h4>{t('international')}</h4>
                        <p><strong>{t('papers')}:</strong> {international_papers}</p>
                        {international_collab_html}
                    </div>
                </div>
                <div class="collab-box" style="margin-top: 10px;">
                    <p><strong>{t('collab_index', index=collab_index)}</strong></p>
                    <p><strong>{t('country_diversity', count=country_diversity)}</strong></p>
                    <p><strong>{t('most_collaborative', country=most_collab_country)}</strong></p>
                </div>
            </div>

            <div id="{sec_coauthors}" class="section">
                <div class="section-title">{t('top_coauthors')}</div>
                {coauthors_html}
            </div>

            {retraction_section_html}

            {sources_section_html}

            <div id="{sec_stats}" class="section">
                <div class="section-title">📋 {t('h_index')}</div>
                <div class="stats-grid">
                    <div class="stat-item"><strong>{t('first_publication')}:</strong> {first_pub_year} - {last_pub_year}</div>
                    <div class="stat-item"><strong>{t('active_years')}:</strong> {active_years}</div>
                    <div class="stat-item"><strong>{t('papers_per_year')}:</strong> {papers_per_year:.1f}</div>
                    <div class="stat-item"><strong>{t('trend')}:</strong> {trend} (R² = {trend_corr**2:.3f})</div>
                    <div class="stat-item"><strong>{t('retractions')}:</strong> {retractions}</div>
                    <div class="stat-item"><strong>{t('corrections')}:</strong> {corrections}</div>
                    <div class="stat-item"><strong>{t('unique_coauthors')}:</strong> {unique_coauthors}</div>
                    <div class="stat-item"><strong>{t('avg_authors_per_paper')}:</strong> {avg_authors:.1f}</div>
                    <div class="stat-item"><strong>{t('max_citations')}:</strong> {max_citations}</div>
                    <div class="stat-item"><strong>{t('thematic_diversity')}:</strong> {profile.get('thematic_diversity_shannon', 0):.3f}</div>
                    <div class="stat-item"><strong>{t('domestic_ratio')}:</strong> {domestic_ratio:.1f}%</div>
                    <div class="stat-item"><strong>{t('international_ratio')}:</strong> {international_ratio:.1f}%</div>
                </div>
            </div>

            <div id="{sec_publications}" class="section">
                <div class="section-title">{t('publications_list')}</div>
                {publications_table_html}
            </div>
    """
    return body_html, sidebar_items, h_index


# ============================================
# ОСНОВНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ HTML-ОТЧЁТА (один автор)
# ============================================

def generate_html_report(
    profile: Dict,
    publications: List[Dict],
    images: Dict[str, str],
    logo_base64: Optional[str] = None,
    app_logo_base64: Optional[str] = None,
    institution_homepages: Optional[Dict[str, str]] = None,
    theme_colors: Optional[Dict] = None,
    lang: str = 'en',
    coauthor_profiles: Optional[Dict] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    create_visualizations_fn=None,
) -> str:
    """
    Генерирует HTML-отчёт по одному автору.
    create_visualizations_fn — функция из app.py (передаётся, чтобы избежать циклического импорта).
    """
    t = lambda key, **kw: _safe_translate(key, lang, **kw)

    if theme_colors is None:
        theme_colors = {'primary': '#667eea', 'secondary': '#f39c12'}
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')

    author_orcid = profile.get('orcid', 'N/A')

    # Заголовок с логотипами
    header_logos = ""
    if app_logo_base64:
        header_logos += f'<img src="data:image/png;base64,{app_logo_base64}" class="header-logo-app" alt="App Logo">'
    if logo_base64:
        header_logos += f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Journal Logo">'

    body_sections_html, sidebar_links_html, _ = _build_single_author_full_sections(
        profile=profile,
        publications=publications,
        images=images,
        institution_homepages=institution_homepages,
        primary=primary,
        secondary=secondary,
        lang=lang,
        coauthor_profiles=coauthor_profiles,
        start_year=start_year,
        end_year=end_year,
        create_visualizations_fn=create_visualizations_fn,
        id_prefix="",
        table_suffix="",
    )

    table_styles = _build_table_styles(primary, secondary)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{t('app_title')} - ORCID {html.escape(author_orcid)}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Times New Roman', 'DejaVu Serif', serif;
                margin: 0; padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #333;
            }}
            .report-wrapper {{ max-width: 1400px; margin: 0 auto; background: white; box-shadow: 0 10px 40px rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden; }}
            .sidebar {{
                position: fixed; left: 0; top: 0; width: 260px; height: 100vh;
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white; padding: 30px 20px; overflow-y: auto; z-index: 1000;
            }}
            .sidebar h3 {{ margin-bottom: 20px; font-size: 18px; font-weight: 600; color: white; }}
            .sidebar a {{ color: white; text-decoration: none; display: flex; align-items: center; gap: 12px; padding: 10px 15px; margin: 5px 0; border-radius: 8px; transition: all 0.3s; }}
            .sidebar a:hover {{ background: rgba(255,255,255,0.2); transform: translateX(5px); }}
            .main-content {{ margin-left: 260px; padding: 30px 40px; }}
            .header {{ background: linear-gradient(135deg, {primary} 0%, {secondary} 100%); color: white; padding: 40px; border-radius: 15px; margin-bottom: 30px; text-align: center; }}
            .header h1 {{ color: white; border-bottom: none; margin: 0; font-size: 32px; }}
            .header .date {{ opacity: 0.9; margin-top: 10px; }}
            .header-logo {{ max-height: 150px; max-width: 300px; margin-bottom: 15px; }}
            .header-logo-app {{ max-height: 120px; max-width: 360px; margin-bottom: 10px; }}
            .author-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid {primary}; }}
            .author-name {{ font-size: 22px; font-weight: bold; color: #2C3E50; }}
            .author-affil {{ color: #555; font-size: 14px; margin-top: 5px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid {primary}; text-align: center; transition: transform 0.3s; }}
            .metric-card:hover {{ transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #2C3E50; font-family: 'Times New Roman', serif; }}
            .metric-label {{ font-size: 12px; color: #7F8C8D; margin-top: 5px; font-family: 'Times New Roman', serif; }}
            .flag-retraction {{ background-color: #FFE5E5; border-left: 4px solid #FF0000; color: #CC0000; font-weight: bold; padding: 12px 15px; border-radius: 5px; margin: 10px 0; font-size: 16px; }}
            .chart-container {{ margin: 20px 0; text-align: center; }}
            .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .collab-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .collab-box {{ background: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #ddd; }}
            .collab-box h4 {{ margin: 0 0 8px 0; color: #2C3E50; }}
            .collab-box ul {{ margin: 5px 0; padding-left: 20px; }}
            .collab-box li {{ margin-bottom: 3px; }}
            .collab-country {{ font-weight: bold; color: #2C3E50; margin-top: 8px; font-size: 14px; }}
            .collab-affil-item {{ margin-left: 15px; font-size: 13px; }}
            .doi-link {{ color: #2980B9; text-decoration: none; font-size: 12px; word-break: break-all; }}
            .doi-link:hover {{ text-decoration: underline; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #BDC3C7; text-align: center; color: #7F8C8D; font-size: 12px; }}
            .footer a {{ color: #2980B9; text-decoration: none; }}
            .footer a:hover {{ text-decoration: underline; }}
            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .stat-item {{ padding: 8px; background: #f8f9fa; border-radius: 4px; }}
            .section {{ background: white; border-radius: 15px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .section-title {{ font-size: 24px; font-weight: 600; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid {primary}; display: flex; align-items: center; gap: 12px; }}
            .thematic-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin: 15px 0; }}
            .thematic-card {{ background: linear-gradient(135deg, {primary}10 0%, {secondary}10 100%); border-radius: 12px; padding: 16px 20px; border-left: 4px solid {primary}; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .thematic-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }}
            .thematic-name {{ font-weight: 600; color: {primary}; font-size: 14px; font-family: 'Times New Roman', serif; }}
            .thematic-count {{ color: #555; font-size: 13px; margin-top: 4px; font-family: 'Times New Roman', serif; }}
            .coauthor-card {{ background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; border: 1px solid #e0e0e0; border-left: 4px solid {primary}; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .coauthor-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); border-color: {primary}; }}
            .coauthor-name {{ font-size: 16px; font-weight: 600; color: {primary}; margin-bottom: 6px; }}
            .coauthor-joint {{ font-size: 13px; color: #666; margin-bottom: 8px; }}
            .coauthor-profile-link {{ display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 15px; font-size: 11px; font-weight: 500; text-decoration: none; transition: all 0.2s; margin: 2px; }}
            .coauthor-profile-link:hover {{ transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
            .coauthor-profile-link.orcid {{ background: #a6ce39; color: #1a1a1a; }}
            .coauthor-profile-link.orcid:hover {{ background: #8cb82e; }}
            .coauthor-profile-link.website {{ background: #6c757d; color: white; }}
            .coauthor-profile-link.website:hover {{ background: #5a6268; }}
            .coauthor-profile-link.other {{ background: #17a2b8; color: white; }}
            .coauthor-profile-link.other:hover {{ background: #138496; }}
            .no-links {{ color: #999; font-style: italic; margin: 5px 0; font-size: 12px; }}
            @media print {{ .sidebar {{ display: none; }} .main-content {{ margin-left: 0; }} }}
            @media (max-width: 768px) {{ .sidebar {{ display: none; }} .main-content {{ margin-left: 0; padding: 20px; }} .thematic-grid {{ grid-template-columns: 1fr; }} }}
        </style>
        {table_styles}
        {_PUBLICATIONS_TABLE_JS}
    </head>
    <body>
        <div class="sidebar">
            <h3>📑 {t('app_title')}</h3>
            {sidebar_links_html}
        </div>
        <div class="main-content">
            <div class="header">
                {header_logos}
                <h1>🔬 {t('app_title')}</h1>
                <div class="date">{t('report_preview')}: {datetime.now().strftime('%d.%m.%Y')}</div>
            </div>
            {body_sections_html}
            <div class="footer">
                <p>{t('footer')}</p>
                <p><a href="{t('journal_url')}" target="_blank">{t('journal_url')}</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


# ============================================
# ГЕНЕРАЦИЯ HTML ДЛЯ НЕСКОЛЬКИХ АВТОРОВ
# ============================================

def generate_html_report_with_multiple_authors(
    all_authors: List[Dict],
    show_all: bool,
    journal_logo_base64: Optional[str] = None,
    app_logo_base64: Optional[str] = None,
    theme_colors: Optional[Dict] = None,
    lang: str = 'en',
    filter_params: Optional[Dict] = None,
    create_visualizations_fn=None,
) -> str:
    """
    Генерирует HTML-отчёт для всех введённых авторов.
    Авторы сортируются по убыванию h-index, а при равенстве — по алфавиту фамилии/имени.
    Для каждого автора строятся все полные разделы (как в одиночном отчёте) и иерархическое меню.
    """
    t = lambda key, **kw: _safe_translate(key, lang, **kw)
    if filter_params is None:
        filter_params = {}
    start_year = filter_params.get('start_year')
    end_year = filter_params.get('end_year')

    if theme_colors is None:
        theme_colors = {'primary': '#667eea', 'secondary': '#f39c12'}
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')

    if not all_authors:
        return "<html><body><h1>Нет данных для отображения</h1></body></html>"

    # Если передан всего один автор — используем основную функцию
    if len(all_authors) == 1:
        ad = all_authors[0]
        analyzer = ad.get('analyzer')
        coauthor_profiles = {}
        if analyzer and hasattr(analyzer, 'coauthor_profiles'):
            coauthor_profiles = analyzer.coauthor_profiles
        if not coauthor_profiles:
            coauthor_profiles = ad.get('profile', {}).get('coauthor_profiles', {})
        return generate_html_report(
            profile=ad.get('profile', {}),
            publications=ad.get('publications', []),
            images=ad.get('images', {}),
            logo_base64=journal_logo_base64,
            app_logo_base64=app_logo_base64,
            institution_homepages=analyzer.institution_homepages if analyzer and hasattr(analyzer, 'institution_homepages') else {},
            theme_colors=theme_colors,
            lang=lang,
            coauthor_profiles=coauthor_profiles,
            start_year=start_year,
            end_year=end_year,
            create_visualizations_fn=create_visualizations_fn,
        )

    # ====== МНОГО АВТОРОВ (отображаем всех, сортируем по h-index desc, затем по фамилии/имени asc) ======
    authors_with_sort_keys = []
    for idx, ad in enumerate(all_authors):
        profile = ad.get('profile', {})
        publications = ad.get('publications', [])
        filtered_pubs = _get_filtered_publications(publications, start_year, end_year)
        if start_year is not None or end_year is not None or 'h_index' not in ad:
            calc_h = _calculate_h_index(filtered_pubs)
        else:
            calc_h = ad.get('h_index', _calculate_h_index(filtered_pubs))
        author_name = ad.get('author_name') or profile.get('author_name') or f'Автор {idx + 1}'
        surname_key = _extract_sort_surname(author_name)
        authors_with_sort_keys.append((calc_h, surname_key, idx, ad))

    authors_with_sort_keys.sort(key=lambda item: (-item[0], item[1], item[2]))
    authors_to_show = [item[3] for item in authors_with_sort_keys]

    header_logos = ""
    if app_logo_base64:
        header_logos += f'<img src="data:image/png;base64,{app_logo_base64}" class="header-logo-app" alt="App Logo">'
    if journal_logo_base64:
        header_logos += f'<img src="data:image/png;base64,{journal_logo_base64}" class="header-logo" alt="Journal Logo">'

    sidebar_links = ""
    author_sections_html = ""

    for i, ad in enumerate(authors_to_show):
        profile = dict(ad.get('profile', {}) or {})
        author_name = ad.get('author_name') or profile.get('author_name') or f'Автор {i + 1}'
        profile['author_name'] = author_name
        publications = ad.get('publications', [])
        analyzer = ad.get('analyzer')

        coauthor_profiles = {}
        if analyzer and hasattr(analyzer, 'coauthor_profiles'):
            coauthor_profiles = analyzer.coauthor_profiles
        if not coauthor_profiles:
            coauthor_profiles = profile.get('coauthor_profiles', {})

        inst_homepages = {}
        if analyzer and hasattr(analyzer, 'institution_homepages'):
            inst_homepages = analyzer.institution_homepages
        elif profile.get('institution_homepages'):
            inst_homepages = profile.get('institution_homepages', {})

        id_prefix = f"author_{i}_"
        table_suffix = str(i)

        body_html, author_sidebar_items, h_index = _build_single_author_full_sections(
            profile=profile,
            publications=publications,
            images=ad.get('images', {}),
            institution_homepages=inst_homepages,
            primary=primary,
            secondary=secondary,
            lang=lang,
            coauthor_profiles=coauthor_profiles,
            start_year=start_year,
            end_year=end_year,
            create_visualizations_fn=create_visualizations_fn,
            id_prefix=id_prefix,
            table_suffix=table_suffix,
        )

        sidebar_links += f"""
        <div class="sidebar-author-group">
            <div class="sidebar-author-title">👤 {html.escape(author_name)} (h-index: {h_index})</div>
            {author_sidebar_items}
        </div>
        """

        author_sections_html += f"""
        <div id="author_{i}" class="author-section">
            {body_html}
        </div>
        """

    table_styles = _build_table_styles(primary, secondary)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{t('app_title')} - {t('profile_analysis')}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Times New Roman', 'DejaVu Serif', serif;
                margin: 0; padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #333;
            }}
            .report-wrapper {{ max-width: 1400px; margin: 0 auto; background: white; box-shadow: 0 10px 40px rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden; }}
            .sidebar {{
                position: fixed; left: 0; top: 0; width: 260px; height: 100vh;
                background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                color: white; padding: 30px 20px; overflow-y: auto; z-index: 1000;
            }}
            .sidebar h3 {{ margin-bottom: 20px; font-size: 18px; font-weight: 600; color: white; }}
            .sidebar a {{ color: white; text-decoration: none; display: flex; align-items: center; gap: 12px; padding: 10px 15px; margin: 5px 0; border-radius: 8px; transition: all 0.3s; }}
            .sidebar a:hover {{ background: rgba(255,255,255,0.2); transform: translateX(5px); }}
            .main-content {{ margin-left: 260px; padding: 30px 40px; }}
            .header {{ background: linear-gradient(135deg, {primary} 0%, {secondary} 100%); color: white; padding: 40px; border-radius: 15px; margin-bottom: 30px; text-align: center; }}
            .header h1 {{ color: white; border-bottom: none; margin: 0; font-size: 32px; }}
            .header .date {{ opacity: 0.9; margin-top: 10px; }}
            .header-logo {{ max-height: 150px; max-width: 300px; margin-bottom: 15px; }}
            .header-logo-app {{ max-height: 120px; max-width: 360px; margin-bottom: 10px; }}
            .author-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid {primary}; }}
            .author-name {{ font-size: 22px; font-weight: bold; color: #2C3E50; }}
            .author-affil {{ color: #555; font-size: 14px; margin-top: 5px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid {primary}; text-align: center; transition: transform 0.3s; }}
            .metric-card:hover {{ transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #2C3E50; font-family: 'Times New Roman', serif; }}
            .metric-label {{ font-size: 12px; color: #7F8C8D; margin-top: 5px; font-family: 'Times New Roman', serif; }}
            .flag-retraction {{ background-color: #FFE5E5; border-left: 4px solid #FF0000; color: #CC0000; font-weight: bold; padding: 12px 15px; border-radius: 5px; margin: 10px 0; font-size: 16px; }}
            .chart-container {{ margin: 20px 0; text-align: center; }}
            .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .collab-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .collab-box {{ background: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #ddd; }}
            .collab-box h4 {{ margin: 0 0 8px 0; color: #2C3E50; }}
            .collab-box ul {{ margin: 5px 0; padding-left: 20px; }}
            .collab-box li {{ margin-bottom: 3px; }}
            .collab-country {{ font-weight: bold; color: #2C3E50; margin-top: 8px; font-size: 14px; }}
            .collab-affil-item {{ margin-left: 15px; font-size: 13px; }}
            .doi-link {{ color: #2980B9; text-decoration: none; font-size: 12px; word-break: break-all; }}
            .doi-link:hover {{ text-decoration: underline; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #BDC3C7; text-align: center; color: #7F8C8D; font-size: 12px; }}
            .footer a {{ color: #2980B9; text-decoration: none; }}
            .footer a:hover {{ text-decoration: underline; }}
            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .stat-item {{ padding: 8px; background: #f8f9fa; border-radius: 4px; }}
            .section {{ background: white; border-radius: 15px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .section-title {{ font-size: 24px; font-weight: 600; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid {primary}; display: flex; align-items: center; gap: 12px; }}
            .thematic-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin: 15px 0; }}
            .thematic-card {{ background: linear-gradient(135deg, {primary}10 0%, {secondary}10 100%); border-radius: 12px; padding: 16px 20px; border-left: 4px solid {primary}; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .thematic-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }}
            .thematic-name {{ font-weight: 600; color: {primary}; font-size: 14px; font-family: 'Times New Roman', serif; }}
            .thematic-count {{ color: #555; font-size: 13px; margin-top: 4px; font-family: 'Times New Roman', serif; }}
            .author-section {{ margin-bottom: 45px; padding-bottom: 25px; border-bottom: 3px dashed {primary}; }}
            .author-section:last-child {{ border-bottom: none; }}
            .filter-info {{ background: #e8f4f8; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid {primary}; }}
            .coauthor-card {{ background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; border: 1px solid #e0e0e0; border-left: 4px solid {primary}; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .coauthor-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); border-color: {primary}; }}
            .coauthor-name {{ font-size: 16px; font-weight: 600; color: {primary}; margin-bottom: 6px; }}
            .coauthor-joint {{ font-size: 13px; color: #666; margin-bottom: 8px; }}
            .coauthor-profile-link {{ display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 15px; font-size: 11px; font-weight: 500; text-decoration: none; transition: all 0.2s; margin: 2px; }}
            .coauthor-profile-link:hover {{ transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
            .coauthor-profile-link.orcid {{ background: #a6ce39; color: #1a1a1a; }}
            .coauthor-profile-link.orcid:hover {{ background: #8cb82e; }}
            .coauthor-profile-link.website {{ background: #6c757d; color: white; }}
            .coauthor-profile-link.website:hover {{ background: #5a6268; }}
            .coauthor-profile-link.other {{ background: #17a2b8; color: white; }}
            .coauthor-profile-link.other:hover {{ background: #138496; }}
            .no-links {{ color: #999; font-style: italic; margin: 5px 0; font-size: 12px; }}
            @media print {{ .sidebar {{ display: none; }} .main-content {{ margin-left: 0; }} }}
            @media (max-width: 768px) {{ .sidebar {{ display: none; }} .main-content {{ margin-left: 0; padding: 20px; }} .thematic-grid {{ grid-template-columns: 1fr; }} }}
        </style>
        {table_styles}
        {_PUBLICATIONS_TABLE_JS}
    </head>
    <body>
        <div class="sidebar">
            <h3>📑 {t('app_title')}</h3>
            {sidebar_links}
        </div>
        <div class="main-content">
            <div class="header">
                {header_logos}
                <h1>📊 {t('app_title')}</h1>
                <div class="date">{t('report_preview')}: {datetime.now().strftime('%d.%m.%Y')}</div>
            </div>
            {author_sections_html}
            <div class="footer">
                <p>{t('footer')}</p>
                <p><a href="{t('journal_url')}" target="_blank">{t('journal_url')}</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


# ============================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ СОАВТОРОВ
# (перенесена из app.py, чтобы html_report был автономным)
# ============================================

def generate_coauthor_links_html(links: List[Dict], lang: str = 'en') -> str:
    """
    Генерирует HTML для отображения ссылок соавтора (Websites & Social Links / Other IDs).
    """
    t = lambda key, **kw: _safe_translate(key, lang, **kw)
    if not links:
        return '<p class="no-links">No additional links found</p>'

    websites_links = []
    other_links = []
    for link in links:
        if link.get('type') == 'Websites & Social Links':
            websites_links.append(link)
        else:
            other_links.append(link)

    html_out = ""

    if websites_links:
        html_out += '<div style="margin-top: 8px; margin-bottom: 8px;">'
        html_out += '<div style="font-weight: 600; font-size: 12px; color: #555; margin-bottom: 4px;">🌐 Websites & Social Links:</div>'
        html_out += '<div style="display: flex; flex-wrap: wrap; gap: 6px;">'
        for link in websites_links:
            ln = link.get('name', 'Website')
            url = link.get('url')
            icon = "🌐"
            low = ln.lower()
            if "linkedin" in low: icon = "💼"
            elif "twitter" in low or "x.com" in low: icon = "🐦"
            elif "facebook" in low: icon = "📘"
            elif "researchgate" in low: icon = "🔬"
            elif "academia" in low: icon = "📖"
            elif "github" in low: icon = "💻"
            elif "scholar" in low: icon = "🎓"
            if url:
                html_out += (f'<a href="{html.escape(url)}" target="_blank" class="coauthor-profile-link website" '
                             f'style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;'
                             f'font-size:11px;font-weight:500;text-decoration:none;background:#6c757d;color:white;'
                             f'transition:all 0.2s;margin:2px;">{icon} {html.escape(ln[:30])}</a>')
            else:
                html_out += (f'<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;'
                             f'border-radius:15px;font-size:11px;font-weight:500;background:#e9ecef;color:#666;'
                             f'margin:2px;">{html.escape(ln[:30])} (no link)</span>')
        html_out += '</div></div>'

    if other_links:
        html_out += '<div style="margin-top: 8px;">'
        html_out += '<div style="font-weight: 600; font-size: 12px; color: #555; margin-bottom: 4px;">🔗 Other IDs:</div>'
        html_out += '<div style="display: flex; flex-wrap: wrap; gap: 6px;">'
        for link in other_links:
            ln = link.get('name', 'Other ID')
            url = link.get('url')
            bg = "#17a2b8"; icon = "🔗"
            low = ln.lower()
            if "scopus" in low: bg = "#e97132"; icon = "📚"
            elif "researcher" in low: bg = "#005a9c"; icon = "🆔"
            elif "orcid" in low: bg = "#a6ce39"; icon = "🆔"
            elif "linkedin" in low: bg = "#0077b5"; icon = "💼"
            elif "twitter" in low: bg = "#1da1f2"; icon = "🐦"
            elif "facebook" in low: bg = "#1877f2"; icon = "📘"
            elif "researchgate" in low: bg = "#00ccbb"; icon = "🔬"
            elif "academia" in low: bg = "#8a2be2"; icon = "📖"
            elif "mendeley" in low: bg = "#9d1620"; icon = "📑"
            elif "publons" in low: bg = "#2a7de1"; icon = "📝"
            elif "loop" in low: bg = "#ff6b6b"; icon = "🔄"
            elif "github" in low: bg = "#333333"; icon = "💻"
            elif "impactstory" in low: bg = "#993366"; icon = "📊"
            elif "google-scholar" in low: bg = "#4285f4"; icon = "🎓"
            if url:
                html_out += (f'<a href="{html.escape(url)}" target="_blank" class="coauthor-profile-link other" '
                             f'style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:15px;'
                             f'font-size:11px;font-weight:500;text-decoration:none;background:{bg};color:white;'
                             f'transition:all 0.2s;margin:2px;">{icon} {html.escape(ln[:40])}</a>')
            else:
                html_out += (f'<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;'
                             f'border-radius:15px;font-size:11px;font-weight:500;background:#e9ecef;color:#666;'
                             f'margin:2px;">{icon} {html.escape(ln[:40])} (no link)</span>')
        html_out += '</div></div>'

    if not html_out:
        html_out = '<p class="no-links">No additional links found</p>'
    return html_out
    return html_out
