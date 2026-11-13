import os
import html
import html as html_module
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from weasyprint import HTML as _WeasyHTML
    _WEASY_AVAILABLE = True
except Exception:
    _WEASY_AVAILABLE = False
    _WeasyHTML = None


def _get_filtered_publications(publications: List[Dict], start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
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
    impl = globals().get('_translate_impl')
    if impl is not None:
        return impl(key, lang, **kwargs)
    return key


def set_translate_impl(fn):
    global _translate_impl
    _translate_impl = fn


def _format_affiliation_html(affil_name: str, institution_homepages: Optional[Dict[str, str]] = None) -> str:
    escaped_name = html.escape(str(affil_name))
    if institution_homepages and isinstance(institution_homepages, dict):
        url = institution_homepages.get(affil_name)
        if url:
            return f'<a href="{html.escape(str(url))}" target="_blank">{escaped_name}</a>'
    return escaped_name


def _calculate_h_index(publications: List[Dict]) -> int:
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
    if not author_name:
        return ""
    clean_name = str(author_name).strip()
    parts = clean_name.split()
    if len(parts) > 1:
        return parts[-1].lower() + " " + clean_name.lower()
    return clean_name.lower()


def _get_emoji_font_path() -> Optional[str]:
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "NotoColorEmoji.ttf"),
        os.path.join(os.getcwd(), "fonts", "NotoColorEmoji.ttf"),
        os.path.join(os.getcwd(), "NotoColorEmoji.ttf"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def _build_emoji_font_face_css() -> str:
    path = _get_emoji_font_path()
    if not path:
        return ""
    file_url = "file://" + path.replace("\\", "/")
    return f"""
    @font-face {{
        font-family: 'Noto Color Emoji';
        src: url('{file_url}') format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
    """


def _build_retraction_section_html(retracted_publications: List[Dict], t, lang: str, section_id: str = "retraction") -> str:
    if not retracted_publications:
        return ""
    rows = []
    for p in retracted_publications:
        title = html.escape(p.get('title') or 'No title')
        year = p.get('publication_year', 'N/A')
        journal = html.escape(p.get('journal_name') or 'Unknown')
        doi = html.escape(p.get('doi', '') or '')
        doi_cell = f'<a href="https://doi.org/{doi}" target="_blank">{doi}</a>' if doi else '—'
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
    <div id="{section_id}" class="section pdf-avoid-break">
        <div class="section-title">🚫 Retraction</div>
        <div class="retraction-warning">⚠️ {t('retraction_warning', count=len(retracted_publications))}</div>
        <table class="pdf-table">
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
    """


def _build_sources_section_html(source_categories: Dict, t, lang: str, section_id: str = "sources") -> str:
    if not source_categories:
        return ""
    category_labels = {
        'repositories': 'source_repositories',
        'ebooks': 'source_ebooks',
        'proceedings': 'source_proceedings',
        'other': 'source_other',
    }
    category_order = ['repositories', 'ebooks', 'proceedings', 'other']
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
                        f'<div class="src-ex">• {title_esc} — '
                        f'<a href="https://doi.org/{html.escape(doi)}">{html.escape(doi[:30])}</a> '
                        f'<span class="src-badge src-doi">✅ {t("source_doi_available")}</span></div>'
                    )
                elif item_id:
                    examples_html += (
                        f'<div class="src-ex">• {title_esc} — '
                        f'<a href="{html.escape(item_id)}">{t("source_view_link")}</a> '
                        f'<span class="src-badge src-nodoi">⚠️ {t("source_no_doi")}</span></div>'
                    )
                else:
                    examples_html += (
                        f'<div class="src-ex">• {title_esc} '
                        f'<span class="src-badge src-nodoi">⚠️ {t("source_no_link")}</span></div>'
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
    <div id="{section_id}" class="section pdf-avoid-break">
        <div class="section-title">{t('source_types')}</div>
        <table class="pdf-table">
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


def _build_publications_table_html(filtered_publications: List[Dict], t, lang: str) -> str:
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
        doi_cell = f'<a href="https://doi.org/{doi}">{doi}</a>' if doi else ''
        rows_html.append(
            f"<tr>"
            f"<td class=\"col-idx\">{i}</td>"
            f"<td class=\"col-title\">{title[:200]}</td>"
            f"<td class=\"col-year\">{year}</td>"
            f"<td class=\"col-journal\">{journal}</td>"
            f"<td class=\"col-cit\">{citations}</td>"
            f"<td class=\"col-cpy\">{cpy_str}</td>"
            f"<td class=\"col-oa\">{oa}</td>"
            f"<td class=\"col-doi\">{doi_cell}</td>"
            f"</tr>"
        )
    return f"""
    <table class="pdf-table pub-table-landscape">
        <thead>
            <tr>
                <th class="col-idx">#</th>
                <th class="col-title">{t('title')}</th>
                <th class="col-year">{t('year')}</th>
                <th class="col-journal">{t('journal')}</th>
                <th class="col-cit">{t('citations')}</th>
                <th class="col-cpy">{t('citations_per_year')}</th>
                <th class="col-oa">OA</th>
                <th class="col-doi">{t('doi')}</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
    <p><em>{t('publications')}: {len(filtered_publications)}</em></p>
    """


def _build_pdf_css(primary: str, secondary: str) -> str:
    emoji_face = _build_emoji_font_face_css()
    font_stack = "'Times New Roman', 'DejaVu Serif', 'Noto Color Emoji', 'Noto Emoji', sans-serif"

    return f"""
    {emoji_face}

    @page {{
        size: A4 portrait;
        margin: 18mm 14mm 18mm 14mm;
        @bottom-center {{
            content: counter(page) " / " counter(pages);
            font-family: {font_stack};
            font-size: 9pt;
            color: {secondary};
        }}
        @top-center {{
            content: "Author Profile Analysis";
            font-family: {font_stack};
            font-size: 8pt;
            color: {primary};
        }}
    }}
    @page :first {{
        @top-center {{ content: ""; }}
        @bottom-center {{ content: ""; }}
    }}

    @page landscape-page {{
        size: A4 landscape;
        margin: 14mm 12mm 14mm 12mm;
        @bottom-center {{
            content: counter(page) " / " counter(pages);
            font-family: {font_stack};
            font-size: 9pt;
            color: {secondary};
        }}
        @top-center {{
            content: "Publication list";
            font-family: {font_stack};
            font-size: 8pt;
            color: {primary};
        }}
    }}

    * {{ box-sizing: border-box; }}
    body {{
        font-family: {font_stack};
        font-size: 10pt;
        color: #222;
        line-height: 1.35;
    }}
    h1, h2, h3, h4 {{
        font-family: {font_stack};
        color: {primary};
        page-break-after: avoid;
        break-after: avoid;
    }}
    a {{ color: {primary}; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    .pdf-cover {{
        page-break-after: always;
        break-after: page;
        text-align: center;
        padding-top: 40mm;
    }}
    .pdf-cover .cover-logos img {{
        max-height: 28mm;
        max-width: 70mm;
        margin: 0 4mm 6mm 4mm;
    }}
    .pdf-cover h1 {{
        font-size: 26pt;
        color: {primary};
        margin: 6mm 0 4mm 0;
        border: none;
    }}
    .pdf-cover .cover-author {{
        font-size: 16pt;
        color: {primary};
        margin: 4mm 0;
    }}
    .pdf-cover .cover-orcid {{
        font-size: 11pt;
        color: {secondary};
        margin: 2mm 0;
    }}
    .pdf-cover .cover-date {{
        font-size: 11pt;
        color: {secondary};
        margin-top: 20mm;
    }}
    .pdf-cover .cover-band {{
        height: 6mm;
        background: linear-gradient(90deg, {primary} 0%, {secondary} 100%);
        margin: 8mm auto;
        width: 80%;
        border-radius: 3mm;
    }}

    .pdf-toc {{
        page-break-after: always;
        break-after: page;
    }}
    .pdf-toc .toc-title {{
        font-size: 20pt;
        color: {primary};
        border-bottom: 3px solid {primary};
        padding-bottom: 3mm;
        margin-bottom: 6mm;
        bookmark-level: 1;
    }}
    .pdf-toc ul {{
        list-style: none;
        padding-left: 0;
        margin: 0;
    }}
    .pdf-toc li {{
        margin: 2mm 0;
        font-size: 11pt;
    }}
    .pdf-toc li.toc-level-1 {{
        font-weight: bold;
        margin-top: 3mm;
    }}
    .pdf-toc li.toc-level-2 {{
        padding-left: 8mm;
        font-weight: normal;
        font-size: 10pt;
    }}
    .pdf-toc a {{
        color: {primary};
        text-decoration: none;
    }}
    .pdf-toc a::after {{
        content: leader('.') target-counter(attr(href), page);
        color: {secondary};
        font-weight: normal;
        font-size: 10pt;
    }}
    .pdf-toc .toc-author {{
        color: {primary};
        font-weight: bold;
    }}

    .section {{
        margin-bottom: 8mm;
        padding-bottom: 3mm;
        page-break-inside: auto;
    }}
    .pdf-avoid-break {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .section-title {{
        font-size: 15pt;
        font-weight: bold;
        color: {primary};
        border-bottom: 3px solid {primary};
        padding-bottom: 2mm;
        margin-bottom: 4mm;
        bookmark-level: 1;
        string-set: section content();
    }}
    .author-block .section-title {{
        bookmark-level: 2;
    }}
    .author-block .thematic-h3 {{
        bookmark-level: 3;
    }}

    .author-info {{
        background: {primary}15;
        padding: 4mm;
        border-left: 4px solid {primary};
        border-radius: 2mm;
        margin-bottom: 4mm;
    }}
    .author-name {{
        font-size: 15pt;
        font-weight: bold;
        color: {primary};
    }}
    .author-affil {{
        font-size: 9.5pt;
        color: #555;
        margin-top: 1.5mm;
    }}

    .flag-retraction {{
        background: #ffe5e5;
        border-left: 4px solid #e00000;
        color: #b00000;
        font-weight: bold;
        padding: 3mm 4mm;
        border-radius: 2mm;
        margin: 3mm 0;
        font-size: 10.5pt;
    }}
    .retraction-warning {{
        background: #ffe5e5;
        border-left: 4px solid #e00000;
        color: #b00000;
        font-weight: bold;
        padding: 3mm 4mm;
        border-radius: 2mm;
        margin: 2mm 0 4mm 0;
        font-size: 10.5pt;
    }}

    .metrics-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 2.5mm;
        margin: 3mm 0;
    }}
    .metric-card {{
        flex: 1 1 28mm;
        background: {primary}10;
        padding: 3mm;
        border-radius: 2mm;
        border-left: 3px solid {primary};
        text-align: center;
        min-width: 26mm;
    }}
    .metric-value {{
        font-size: 15pt;
        font-weight: bold;
        color: {primary};
    }}
    .metric-label {{
        font-size: 8pt;
        color: {secondary};
        margin-top: 1mm;
    }}

    .chart-container {{
        text-align: center;
        margin: 3mm 0;
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .chart-container img {{
        max-width: 100%;
        height: auto;
        max-height: 110mm;
    }}
    .two-col-charts {{
        display: flex;
        gap: 4mm;
        margin: 3mm 0;
    }}
    .two-col-charts .chart-container {{
        flex: 1;
    }}
    .two-col-charts .chart-container img {{
        max-height: 70mm;
    }}

    .pdf-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 3mm 0;
        font-size: 8.5pt;
    }}
    .pdf-table th {{
        background: {primary};
        color: #ffffff;
        padding: 2mm;
        text-align: left;
        font-size: 8.5pt;
    }}
    .pdf-table td {{
        padding: 1.8mm;
        border-bottom: 0.3mm solid #ccc;
        vertical-align: top;
    }}
    .pdf-table tr:nth-child(even) td {{
        background: {primary}08;
    }}
    .src-count {{ font-size: 8pt; color: {secondary}; }}
    .src-ex {{ font-size: 8pt; margin: 1mm 0; }}
    .src-badge {{
        display: inline-block;
        padding: 0.3mm 2mm;
        border-radius: 3mm;
        font-size: 7pt;
        font-weight: bold;
        margin-left: 1mm;
    }}
    .src-doi {{ background: #d4edda; color: #155724; }}
    .src-nodoi {{ background: #f8d7da; color: #721c24; }}

    .landscape-section {{
        page: landscape-page;
        page-break-before: always;
        break-before: page;
    }}
    .pub-table-landscape {{
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
        font-size: 7.5pt;
        word-wrap: break-word;
    }}
    .pub-table-landscape thead {{
        display: table-header-group;
    }}
    .pub-table-landscape th {{
        background: {primary};
        color: #ffffff;
        padding: 1.5mm 1mm;
        text-align: left;
        font-size: 7.5pt;
        word-break: break-word;
    }}
    .pub-table-landscape td {{
        padding: 1.2mm 1mm;
        border-bottom: 0.3mm solid #ccc;
        vertical-align: top;
        word-break: break-word;
        overflow-wrap: anywhere;
        font-size: 7.5pt;
    }}
    .pub-table-landscape tr {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .pub-table-landscape tr:nth-child(even) td {{
        background: {primary}08;
    }}
    .pub-table-landscape .col-idx     {{ width: 5%;  text-align: right; }}
    .pub-table-landscape .col-title   {{ width: 38%; }}
    .pub-table-landscape .col-year    {{ width: 6%; }}
    .pub-table-landscape .col-journal {{ width: 18%; }}
    .pub-table-landscape .col-cit     {{ width: 6%;  text-align: right; }}
    .pub-table-landscape .col-cpy     {{ width: 7%;  text-align: right; }}
    .pub-table-landscape .col-oa      {{ width: 4%;  text-align: center; }}
    .pub-table-landscape .col-doi     {{ width: 16%; word-break: break-all; }}

    .thematic-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 2.5mm;
        margin: 2mm 0;
    }}
    .thematic-card {{
        flex: 1 1 45mm;
        background: {secondary}10;
        border-left: 4px solid {secondary};
        border-radius: 2mm;
        padding: 2.5mm 3mm;
        min-width: 40mm;
    }}
    .thematic-name {{
        font-weight: bold;
        color: {primary};
        font-size: 9pt;
    }}
    .thematic-count {{
        font-size: 8pt;
        color: {secondary};
        margin-top: 0.5mm;
    }}
    .thematic-h3 {{
        font-size: 11pt;
        color: {secondary};
        margin-top: 4mm;
        margin-bottom: 1.5mm;
        bookmark-level: 2;
    }}

    .collab-grid {{
        display: flex;
        gap: 4mm;
        margin: 2mm 0;
    }}
    .collab-box {{
        flex: 1;
        background: {primary}10;
        padding: 3mm;
        border-radius: 2mm;
        border: 0.3mm solid #ddd;
    }}
    .collab-box h4 {{
        font-size: 10.5pt;
        color: {primary};
        margin-bottom: 2mm;
    }}
    .collab-country {{
        font-weight: bold;
        color: {primary};
        font-size: 9pt;
        margin-top: 2mm;
    }}
    .collab-affil-item {{
        font-size: 8.5pt;
        color: {secondary};
        margin-left: 3mm;
    }}

    .coauthor-card {{
        background: {secondary}10;
        padding: 2.5mm 3.5mm;
        margin-bottom: 2.5mm;
        border-left: 4px solid {secondary};
        border-radius: 2mm;
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .coauthor-name {{
        font-size: 10pt;
        font-weight: bold;
        color: {primary};
    }}
    .coauthor-joint {{
        font-size: 8.5pt;
        color: {secondary};
        margin: 1mm 0;
    }}
    .coauthor-links-label {{
        font-size: 8.5pt;
        color: {secondary};
        font-weight: bold;
        margin-top: 1.5mm;
    }}
    .coauthor-profile-link {{
        display: inline-block;
        padding: 0.5mm 2mm;
        margin: 0.5mm 1.5mm 0.5mm 0;
        border-radius: 3mm;
        font-size: 7.5pt;
        font-weight: 500;
        text-decoration: none;
        color: #ffffff;
    }}
    .coauthor-profile-link.orcid {{ background: #a6ce39; color: #1a1a1a; }}
    .coauthor-profile-link.scopus {{ background: #e97132; color: #ffffff; }}
    .coauthor-profile-link.researcherid {{ background: #005a9c; color: #ffffff; }}
    .coauthor-profile-link.website {{ background: #6c757d; color: #ffffff; }}
    .coauthor-profile-link.wos {{ background: #5b3a8e; color: #ffffff; }}
    .coauthor-profile-link.other {{ background: #17a2b8; color: #ffffff; }}
    .no-links {{ color: {secondary}; font-style: italic; font-size: 8pt; }}

    .stats-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 2.5mm;
        margin: 2mm 0;
    }}
    .stat-item {{
        flex: 1 1 45%;
        background: {primary}10;
        padding: 2mm 3mm;
        border-radius: 2mm;
        font-size: 9pt;
    }}
    .stat-item strong {{
        color: {secondary};
    }}

    .pdf-footer {{
        margin-top: 8mm;
        padding-top: 3mm;
        border-top: 0.3mm solid #ccc;
        text-align: center;
        color: {secondary};
        font-size: 8pt;
    }}
    .pdf-footer a {{ color: {primary}; }}
    """


def _render_coauthor_links_pdf(links: List[Dict], t, lang: str) -> str:
    if not links:
        return '<p class="no-links">No additional links found</p>'

    def _class_for(name: str) -> str:
        low = name.lower()
        if "orcid" in low:
            return "orcid"
        if "scopus" in low:
            return "scopus"
        if "researcher" in low:
            return "researcherid"
        if "web of science" in low or "wos" in low or "publons" in low:
            return "wos"
        return "other"

    def _icon_for(name: str) -> str:
        low = name.lower()
        if "linkedin" in low:
            return "💼"
        if "twitter" in low or "x.com" in low:
            return "🐦"
        if "facebook" in low:
            return "📘"
        if "researchgate" in low:
            return "🔬"
        if "academia" in low:
            return "📖"
        if "github" in low:
            return "💻"
        if "scholar" in low:
            return "🎓"
        if "scopus" in low:
            return "📚"
        if "researcher" in low or "orcid" in low:
            return "🆔"
        if "mendeley" in low:
            return "📑"
        if "loop" in low:
            return "🔄"
        if "impactstory" in low:
            return "📊"
        return "🔗"

    websites_links = [l for l in links if l.get('type') == 'Websites & Social Links']
    other_links = [l for l in links if l.get('type') != 'Websites & Social Links']

    out = ""

    if websites_links:
        out += '<div class="coauthor-links-label">🌐 Websites &amp; Social Links:</div>'
        out += '<div>'
        for lk in websites_links:
            nm = lk.get('name', 'Website')
            url = lk.get('url') or ''
            cls = _class_for(nm) if _class_for(nm) != "orcid" else "website"
            icon = _icon_for(nm)
            if url:
                out += (
                    f'<a href="{html.escape(url)}" target="_blank" '
                    f'class="coauthor-profile-link {cls}">'
                    f'{icon} {html.escape(nm[:40])}</a>'
                )
            else:
                out += (
                    f'<span class="coauthor-profile-link {cls}">'
                    f'{icon} {html.escape(nm[:40])} (no link)</span>'
                )
        out += '</div>'

    if other_links:
        out += '<div class="coauthor-links-label">🔗 Other IDs:</div>'
        out += '<div>'
        for lk in other_links:
            nm = lk.get('name', 'Other ID')
            url = lk.get('url') or ''
            cls = _class_for(nm)
            icon = _icon_for(nm)
            if url:
                out += (
                    f'<a href="{html.escape(url)}" target="_blank" '
                    f'class="coauthor-profile-link {cls}">'
                    f'{icon} {html.escape(nm[:40])}</a>'
                )
            else:
                out += (
                    f'<span class="coauthor-profile-link {cls}">'
                    f'{icon} {html.escape(nm[:40])} (no link)</span>'
                )
        out += '</div>'

    if not out:
        out = '<p class="no-links">No additional links found</p>'
    return out


def _render_coauthors_html_pdf(top_coauthors_with_orcids: Dict, coauthor_profiles: Dict, t, lang: str) -> str:
    if not top_coauthors_with_orcids:
        return f'<p class="no-links">{t("no_publications")}</p>'

    out = ""
    for name, data in list(top_coauthors_with_orcids.items())[:15]:
        count = data.get('count', 0)
        orcid = data.get('orcid', '')
        clean = orcid.replace('https://orcid.org/', '').strip() if orcid else ''
        person_info = {}
        if clean and clean in coauthor_profiles:
            person_info = coauthor_profiles.get(clean, {})
        elif orcid and orcid in coauthor_profiles:
            person_info = coauthor_profiles.get(orcid, {})
        links = person_info.get('links', []) if isinstance(person_info, dict) else []

        out += f'<div class="coauthor-card">'
        out += f'<div class="coauthor-name">{html.escape(name)}</div>'
        out += f'<div class="coauthor-joint">{count} {t("joint_works")}</div>'
        if orcid:
            out += (
                f'<a href="https://orcid.org/{html.escape(clean)}" target="_blank" '
                f'class="coauthor-profile-link orcid">🆔 ORCID: {html.escape(clean)}</a>'
            )
        if links:
            out += _render_coauthor_links_pdf(links, t, lang)
        else:
            out += '<p class="no-links">No additional links found</p>'
        out += '</div>'
    return out


def _build_toc_html(entries: List[Dict], t, lang: str) -> str:
    items_html = []
    for e in entries:
        cls = "toc-level-1" if e.get('level', 1) == 1 else "toc-level-2"
        if e.get('is_author'):
            cls += " toc-author"
        items_html.append(
            f'<li class="{cls}"><a href="#{html.escape(e["anchor"])}">{html.escape(e["text"])}</a></li>'
        )

    return f"""
    <div class="pdf-toc">
        <div class="toc-title">📖 Contents</div>
        <ul>
            {''.join(items_html)}
        </ul>
    </div>
    """


def _build_single_author_pdf_sections(
    profile: Dict,
    publications: List[Dict],
    images: Optional[Dict[str, str]],
    institution_homepages: Optional[Dict[str, str]],
    lang: str,
    coauthor_profiles: Optional[Dict],
    start_year: Optional[int],
    end_year: Optional[int],
    create_visualizations_fn=None,
    id_prefix: str = "",
    toc_level: int = 1,
) -> Tuple[str, List[Dict], int]:
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

    filtered_publications = _get_filtered_publications(publications, start_year, end_year)
    filter_info = None
    if start_year is not None or end_year is not None:
        yrs = [p.get('publication_year') for p in filtered_publications if p.get('publication_year')]
        if yrs:
            filter_info = t('temporal_gap_filter_info', start_year=min(yrs), end_year=max(yrs))

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
        cs = sorted([c for c in citations if c > 0], reverse=True)
        for i, c in enumerate(cs, 1):
            if c >= i:
                h_index = i
            else:
                break
        i10_index = sum(1 for c in citations if c >= 10)
        i100_index = sum(1 for c in citations if c >= 100)
        tc = 0
        for i, c in enumerate(cs, 1):
            tc += c
            if tc >= i * i:
                g_index = i
        oa = sum(1 for p in filtered_publications if p.get('is_oa', False))
        oa_percentage = (oa / len(filtered_publications) * 100) if filtered_publications else 0

    concept_counter = defaultdict(int)
    domain_counter = defaultdict(int)
    field_counter = defaultdict(int)
    primary_counter = defaultdict(int)
    subfield_counter = defaultdict(int)
    keyword_counter = defaultdict(int)
    for p in filtered_publications:
        for c in set(p.get('concepts', []) or []):
            concept_counter[c] += 1
        for d in set(p.get('domains', []) or []):
            domain_counter[d] += 1
        for f in set(p.get('fields', []) or []):
            field_counter[f] += 1
        if p.get('primary_topic'):
            pt = p['primary_topic']
            if pt.get('display_name'):
                primary_counter[pt['display_name']] += 1
            if pt.get('subfield'):
                subfield_counter[pt['subfield']] += 1
        for k in set(p.get('keywords', []) or []):
            keyword_counter[k] += 1

    top_primary = (
        dict(sorted(primary_counter.items(), key=lambda x: x[1], reverse=True)[:5])
        if primary_counter else dict(list((profile.get('top_topics') or {}).items())[:5])
    )
    top_subfields = (
        dict(sorted(subfield_counter.items(), key=lambda x: x[1], reverse=True)[:5])
        if subfield_counter else dict(list((profile.get('top_subtopics') or {}).items())[:5])
    )
    top_fields = (
        dict(sorted(field_counter.items(), key=lambda x: x[1], reverse=True)[:5])
        if field_counter else dict(list((profile.get('top_fields') or {}).items())[:5])
    )
    top_domains = (
        dict(sorted(domain_counter.items(), key=lambda x: x[1], reverse=True)[:5])
        if domain_counter else dict(list((profile.get('top_domains') or {}).items())[:5])
    )
    top_keywords = (
        dict(sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:10])
        if keyword_counter else (
            dict(sorted(concept_counter.items(), key=lambda x: x[1], reverse=True)[:10])
            if concept_counter else dict(list((profile.get('top_concepts') or {}).items())[:10])
        )
    )

    years = [p.get('publication_year') for p in filtered_publications if p.get('publication_year')]
    active_years = len(set(years)) if years else 0
    papers_per_year = (len(filtered_publications) / active_years) if active_years else 0
    first_pub_year = min(years) if years else profile.get('first_publication', 'N/A')
    last_pub_year = max(years) if years else profile.get('last_publication', 'N/A')

    trend = 'unknown'
    trend_corr = 0.0
    if len(years) >= 3:
        yc = Counter(years)
        sy = sorted(set(years))
        yr_range = range(min(sy), max(sy) + 1)
        counts = [yc.get(y, 0) for y in yr_range]
        if len(counts) >= 3:
            x = np.arange(len(counts))
            z = np.polyfit(x, counts, 1)
            if len(counts) > 1:
                cm = np.corrcoef(x, counts)
                trend_corr = float(cm[0, 1]) if len(cm) > 1 else 0.0
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

    retracted = [p for p in filtered_publications if p.get('is_retracted', False)]
    retractions = len(retracted)
    corrections = sum(1 for p in filtered_publications if p.get('is_correction', False))

    unique_coauthors = len(set([a for p in filtered_publications for a in p.get('authors', [])]))
    avg_authors_list = [p.get('author_count', 0) for p in filtered_publications if p.get('author_count', 0) > 0]
    avg_authors = float(np.mean(avg_authors_list)) if avg_authors_list else 0.0

    author_name = profile.get('author_name', 'Unknown')
    author_affiliations = profile.get('author_affiliations', [])
    author_countries = profile.get('author_countries', [])
    author_orcid = profile.get('orcid', 'N/A')

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

        domestic_collab = {k: dict(v) for k, v in dom_map.items() if v}
        international_collab = {k: dict(v) for k, v in int_map.items() if v}
        if not domestic_collab and not international_collab:
            for country, affs in collaborations.get('domestic', {}).items():
                ff = {k: v for k, v in affs.items() if k not in author_affils}
                if ff:
                    domestic_collab[country] = ff
            for country, affs in collaborations.get('international', {}).items():
                ff = {k: v for k, v in affs.items() if k not in author_affils}
                if ff:
                    international_collab[country] = ff
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
        domestic_collab = {}
        for country, affs in collaborations.get('domestic', {}).items():
            ff = {k: v for k, v in affs.items() if k not in author_affils}
            if ff:
                domestic_collab[country] = ff
        international_collab = {}
        for country, affs in collaborations.get('international', {}).items():
            ff = {k: v for k, v in affs.items() if k not in author_affils}
            if ff:
                international_collab[country] = ff
        most_collab_country = profile.get('most_collaborative_country', 'None')
        collab_index = profile.get('collaboration_index', 0)
        country_diversity = profile.get('country_diversity', 0)
        domestic_ratio = profile.get('domestic_papers_ratio', 0) * 100
        international_ratio = profile.get('international_papers_ratio', 0) * 100

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
            for nm, d_val in coauthors_recalc.items():
                if not d_val.get('orcid') and nm in (profile.get('top_coauthors_with_orcids') or {}):
                    d_val['orcid'] = profile['top_coauthors_with_orcids'][nm].get('orcid', '')
            top_coauthors_with_orcids = dict(
                sorted(coauthors_recalc.items(), key=lambda x: x[1]['count'], reverse=True)[:15]
            )

    if coauthor_profiles is None:
        coauthor_profiles = profile.get('coauthor_profiles', {})

    retraction_html = _build_retraction_section_html(retracted, t, lang, section_id=sec_retraction)
    sources_html = _build_sources_section_html(profile.get('source_categories', {}), t, lang, section_id=sec_sources)
    publications_html = _build_publications_table_html(filtered_publications, t, lang)
    coauthors_html = _render_coauthors_html_pdf(top_coauthors_with_orcids, coauthor_profiles, t, lang)

    filter_info_html = ""
    if filter_info:
        filter_info_html = (
            f'<div class="author-info" style="margin-bottom:4mm;">'
            f'<strong>{filter_info}</strong>'
            f'<span style="margin-left:6mm;font-size:9pt;color:#555;">'
            f'{t("temporal_gap_original_count", count=len(publications))} | '
            f'{t("temporal_gap_filtered_count", count=len(filtered_publications))}'
            f'</span></div>'
        )

    retraction_flag = ""
    if retractions > 0:
        retraction_flag = f'<div class="flag-retraction">⚠️ {t("retraction_warning", count=retractions)}</div>'

    affiliations_formatted = ""
    if author_affiliations:
        affil_links = [_format_affiliation_html(af, institution_homepages) for af in author_affiliations[:5]]
        affiliations_formatted = f'<div class="author-affil"><strong>{t("affiliations")}:</strong> {", ".join(affil_links)}</div>'

    def _img(key: str, alt: str) -> str:
        b = images.get(key, "")
        if not b:
            return ""
        return f'<div class="chart-container"><img src="data:image/png;base64,{b}" alt="{html.escape(alt)}"></div>'

    def _thematic_cards(items: Dict, label_articles: str) -> str:
        return "".join(
            f'<div class="thematic-card"><div class="thematic-name">{html.escape(k)}</div>'
            f'<div class="thematic-count">📄 {v} {label_articles}</div></div>'
            for k, v in items.items()
        )

    dom_html = ""
    if domestic_collab:
        for country, affs in domestic_collab.items():
            dom_html += f'<div class="collab-country">📍 {html.escape(country)}</div>'
            for aff, cnt in list(affs.items())[:10]:
                dom_html += f'<div class="collab-affil-item">• <strong>{_format_affiliation_html(aff, institution_homepages)}</strong>: {cnt} {t("articles")}</div>'
    else:
        dom_html = f'<p>{t("no_data_collab")}</p>'

    int_html = ""
    if international_collab:
        for country, affs in international_collab.items():
            int_html += f'<div class="collab-country">📍 {html.escape(country)}</div>'
            for aff, cnt in list(affs.items())[:10]:
                int_html += f'<div class="collab-affil-item">• <strong>{_format_affiliation_html(aff, institution_homepages)}</strong>: {cnt} {t("articles")}</div>'
    else:
        int_html = f'<p>{t("no_data_collab")}</p>'

    toc_entries = [
        {'level': toc_level, 'text': t('profile'), 'anchor': sec_overview, 'is_author': False},
        {'level': toc_level, 'text': t('main_metrics'), 'anchor': sec_metrics, 'is_author': False},
        {'level': toc_level, 'text': t('citations'), 'anchor': sec_visualizations, 'is_author': False},
        {'level': toc_level, 'text': t('topics'), 'anchor': sec_thematic, 'is_author': False},
        {'level': toc_level, 'text': t('collaborations'), 'anchor': sec_collaborations, 'is_author': False},
        {'level': toc_level, 'text': t('top_coauthors'), 'anchor': sec_coauthors, 'is_author': False},
    ]
    if retraction_html:
        toc_entries.append({'level': toc_level, 'text': '🚫 Retraction', 'anchor': sec_retraction, 'is_author': False})
    if sources_html:
        toc_entries.append({'level': toc_level, 'text': t('source_types'), 'anchor': sec_sources, 'is_author': False})
    toc_entries.append({'level': toc_level, 'text': '📊 Statistics', 'anchor': sec_stats, 'is_author': False})
    toc_entries.append({'level': toc_level, 'text': t('publications_list'), 'anchor': sec_publications, 'is_author': False})

    sections_html = f"""
        <div id="{sec_overview}" class="section pdf-avoid-break">
            <div class="section-title">📋 {t('profile')}</div>
            {filter_info_html}
            <div class="author-info">
                <div class="author-name">{html.escape(author_name)}</div>
                <div class="author-affil"><strong>{t('orcid')}:</strong>
                    <a href="https://orcid.org/{html.escape(author_orcid)}">{html.escape(author_orcid)}</a></div>
                {affiliations_formatted}
                {f'<div class="author-affil"><strong>{t("countries")}:</strong> {html.escape(", ".join(author_countries))}</div>' if author_countries else ''}
                <div class="author-affil"><strong>{t('total_analyzed')}:</strong> {total_pubs}</div>
            </div>
            {retraction_flag}
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
            {_img('years_chart', t('years_chart_title'))}
            <div class="two-col-charts">
                {_img('journals_chart', t('journals_chart_title'))}
                {_img('oa_chart', t('oa_chart_title'))}
            </div>
            <div class="two-col-charts">
                {_img('publishers_chart', t('publishers_chart_title'))}
                {_img('affiliations_chart', t('affiliations_chart_title'))}
            </div>
            {_img('wordcloud', t('wordcloud_title'))}
            {_img('citations_chart', t('citations_chart_title'))}
            {_img('citation_distribution', t('citation_distribution_title'))}
            {_img('thematic_structure', t('thematic_structure_title'))}
            {_img('radar_chart', t('radar_title'))}
        </div>

        <div id="{sec_thematic}" class="section">
            <div class="section-title">🏷️ {t('topics')}</div>
            <h3 class="thematic-h3">{t('topics')} (Top 5)</h3>
            <div class="thematic-grid">{_thematic_cards(top_primary, t('articles'))}</div>
            <h3 class="thematic-h3">{t('subtopics')} (Top 5)</h3>
            <div class="thematic-grid">{_thematic_cards(top_subfields, t('articles'))}</div>
            <h3 class="thematic-h3">{t('fields')} (Top 5)</h3>
            <div class="thematic-grid">{_thematic_cards(top_fields, t('articles'))}</div>
            <h3 class="thematic-h3">{t('domains')} (Top 5)</h3>
            <div class="thematic-grid">{_thematic_cards(top_domains, t('articles'))}</div>
            <h3 class="thematic-h3">{t('concepts')} (Top 10)</h3>
            <div class="thematic-grid">{_thematic_cards(top_keywords, t('articles'))}</div>
        </div>

        <div id="{sec_collaborations}" class="section">
            <div class="section-title">🌍 {t('collaborations')}</div>
            <div class="collab-grid">
                <div class="collab-box">
                    <h4>{t('domestic')}</h4>
                    <p><strong>{t('papers')}:</strong> {domestic_papers}</p>
                    {dom_html}
                </div>
                <div class="collab-box">
                    <h4>{t('international')}</h4>
                    <p><strong>{t('papers')}:</strong> {international_papers}</p>
                    {int_html}
                </div>
            </div>
            <div class="collab-box" style="margin-top:3mm;">
                <p><strong>{t('collab_index', index=collab_index)}</strong></p>
                <p><strong>{t('country_diversity', count=country_diversity)}</strong></p>
                <p><strong>{t('most_collaborative', country=most_collab_country)}</strong></p>
            </div>
        </div>

        <div id="{sec_coauthors}" class="section">
            <div class="section-title">🤝 {t('top_coauthors')}</div>
            {coauthors_html}
        </div>

        {retraction_html}

        {sources_html}

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

        <div id="{sec_publications}" class="section landscape-section">
            <div class="section-title">📚 {t('publications_list')}</div>
            {publications_html}
        </div>
    """
    return sections_html, toc_entries, h_index


def _build_pdf_html_single_author(
    profile: Dict,
    publications: List[Dict],
    images: Dict[str, str],
    logo_base64: Optional[str],
    app_logo_base64: Optional[str],
    theme_colors: Optional[Dict],
    lang: str,
    coauthor_profiles: Optional[Dict],
    start_year: Optional[int],
    end_year: Optional[int],
    create_visualizations_fn=None,
    institution_homepages: Optional[Dict[str, str]] = None,
) -> str:
    t = lambda key, **kw: _safe_translate(key, lang, **kw)

    if theme_colors is None:
        theme_colors = {'primary': '#667eea', 'secondary': '#f39c12'}
    primary = theme_colors.get('primary', '#667eea')
    secondary = theme_colors.get('secondary', '#f39c12')

    author_name = profile.get('author_name', 'Unknown')
    author_affiliations = profile.get('author_affiliations', [])
    author_countries = profile.get('author_countries', [])
    author_orcid = profile.get('orcid', 'N/A')

    css = _build_pdf_css(primary, secondary)

    cover_logos = ""
    if app_logo_base64:
        cover_logos += f'<img src="data:image/png;base64,{app_logo_base64}" alt="App Logo">'
    if logo_base64:
        cover_logos += f'<img src="data:image/png;base64,{logo_base64}" alt="Journal Logo">'

    sections_html, toc_entries, _ = _build_single_author_pdf_sections(
        profile=profile,
        publications=publications,
        images=images,
        institution_homepages=institution_homepages,
        lang=lang,
        coauthor_profiles=coauthor_profiles,
        start_year=start_year,
        end_year=end_year,
        create_visualizations_fn=create_visualizations_fn,
        id_prefix="",
        toc_level=1,
    )

    toc_html = _build_toc_html(toc_entries, t, lang)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{t('app_title')} - ORCID {html.escape(author_orcid)}</title>
        <style>{css}</style>
    </head>
    <body>
        <div class="pdf-cover">
            <div class="cover-logos">{cover_logos}</div>
            <h1>🔬 {t('app_title')}</h1>
            <div class="cover-band"></div>
            <div class="cover-author">{html.escape(author_name)}</div>
            <div class="cover-orcid">
                <a href="https://orcid.org/{html.escape(author_orcid)}">ORCID: {html.escape(author_orcid)}</a>
            </div>
            {f'<div class="cover-orcid">{html.escape(", ".join(author_affiliations[:3]))}</div>' if author_affiliations else ''}
            {f'<div class="cover-orcid">{html.escape(", ".join(author_countries))}</div>' if author_countries else ''}
            <div class="cover-date">{datetime.now().strftime('%d.%m.%Y')}</div>
        </div>

        {toc_html}

        {sections_html}

        <div class="pdf-footer">
            <p>{t('footer')}</p>
            <p><a href="{t('journal_url')}">{t('journal_url')}</a></p>
        </div>
    </body>
    </html>
    """
    return html_content


def _build_pdf_html_multiple_authors(
    all_authors: List[Dict],
    show_all: bool,
    journal_logo_base64: Optional[str],
    app_logo_base64: Optional[str],
    theme_colors: Optional[Dict],
    lang: str,
    filter_params: Optional[Dict],
    create_visualizations_fn=None,
) -> str:
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
        return "<html><body><h1>Нет данных</h1></body></html>"

    if len(all_authors) == 1:
        ad = all_authors[0]
        analyzer = ad.get('analyzer')
        cp = {}
        if analyzer and hasattr(analyzer, 'coauthor_profiles'):
            cp = analyzer.coauthor_profiles
        if not cp:
            cp = ad.get('profile', {}).get('coauthor_profiles', {})
        inst_homepages = (
            analyzer.institution_homepages
            if analyzer and hasattr(analyzer, 'institution_homepages')
            else ad.get('profile', {}).get('institution_homepages', {})
        )
        return _build_pdf_html_single_author(
            profile=ad.get('profile', {}),
            publications=ad.get('publications', []),
            images=ad.get('images', {}),
            logo_base64=journal_logo_base64,
            app_logo_base64=app_logo_base64,
            theme_colors=theme_colors,
            lang=lang,
            coauthor_profiles=cp,
            start_year=start_year,
            end_year=end_year,
            create_visualizations_fn=create_visualizations_fn,
            institution_homepages=inst_homepages,
        )

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

    css = _build_pdf_css(primary, secondary)

    cover_logos = ""
    if app_logo_base64:
        cover_logos += f'<img src="data:image/png;base64,{app_logo_base64}" alt="App Logo">'
    if journal_logo_base64:
        cover_logos += f'<img src="data:image/png;base64,{journal_logo_base64}" alt="Journal Logo">'

    cover_html = f"""
    <div class="pdf-cover">
        <div class="cover-logos">{cover_logos}</div>
        <h1>📊 {t('app_title')}</h1>
        <div class="cover-band"></div>
        <div class="cover-author">{t('report_preview')}</div>
        <div class="cover-date">{datetime.now().strftime('%d.%m.%Y')}</div>
    </div>
    """

    toc_entries = []
    author_sections = ""

    for i, ad in enumerate(authors_to_show):
        profile = dict(ad.get('profile', {}) or {})
        author_name = ad.get('author_name') or profile.get('author_name') or f'Автор {i + 1}'
        profile['author_name'] = author_name
        publications = ad.get('publications', [])
        analyzer = ad.get('analyzer')

        cp = {}
        if analyzer and hasattr(analyzer, 'coauthor_profiles'):
            cp = analyzer.coauthor_profiles
        if not cp:
            cp = profile.get('coauthor_profiles', {})

        inst_homepages = {}
        if analyzer and hasattr(analyzer, 'institution_homepages'):
            inst_homepages = analyzer.institution_homepages
        elif profile.get('institution_homepages'):
            inst_homepages = profile.get('institution_homepages', {})

        id_prefix = f"author_{i}_"

        sections_html, author_toc_items, h_index = _build_single_author_pdf_sections(
            profile=profile,
            publications=publications,
            images=ad.get('images', {}),
            institution_homepages=inst_homepages,
            lang=lang,
            coauthor_profiles=cp,
            start_year=start_year,
            end_year=end_year,
            create_visualizations_fn=create_visualizations_fn,
            id_prefix=id_prefix,
            toc_level=2,
        )

        toc_entries.append({
            'level': 1,
            'text': f'{author_name} (h-index: {h_index})',
            'anchor': f'author_{i}',
            'is_author': True,
        })
        toc_entries.extend(author_toc_items)

        author_sections += f"""
        <div id="author_{i}" class="author-block" style="page-break-before:always;">
            <h2 style="font-size:16pt;color:{primary};border-bottom:2px solid {primary};padding-bottom:2mm;margin-bottom:4mm;bookmark-level:1;">
                👤 {html.escape(author_name)} (h-index: {h_index})
            </h2>
            {sections_html}
        </div>
        """

    toc_html = _build_toc_html(toc_entries, t, lang)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{t('app_title')} - {t('profile_analysis')}</title>
        <style>{css}</style>
    </head>
    <body>
        {cover_html}
        {toc_html}
        {author_sections}
        <div class="pdf-footer">
            <p>{t('footer')}</p>
            <p><a href="{t('journal_url')}">{t('journal_url')}</a></p>
        </div>
    </body>
    </html>
    """
    return html_content


def generate_pdf_report(
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
) -> bytes:
    if not _WEASY_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint не установлен. Установите его и системные библиотеки "
            "(libpango, libcairo, libgdk-pixbuf) или используйте другой движок."
        )

    html_content = _build_pdf_html_single_author(
        profile=profile,
        publications=publications,
        images=images,
        logo_base64=logo_base64,
        app_logo_base64=app_logo_base64,
        theme_colors=theme_colors,
        lang=lang,
        coauthor_profiles=coauthor_profiles,
        start_year=start_year,
        end_year=end_year,
        create_visualizations_fn=create_visualizations_fn,
        institution_homepages=institution_homepages,
    )

    pdf_bytes = _WeasyHTML(string=html_content).write_pdf()
    return pdf_bytes


def generate_pdf_report_with_multiple_authors(
    all_authors: List[Dict],
    show_all: bool,
    journal_logo_base64: Optional[str] = None,
    app_logo_base64: Optional[str] = None,
    theme_colors: Optional[Dict] = None,
    lang: str = 'en',
    filter_params: Optional[Dict] = None,
    create_visualizations_fn=None,
) -> bytes:
    if not _WEASY_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint не установлен. Установите его и системные библиотеки "
            "(libpango, libcairo, libgdk-pixbuf) или используйте другой движок."
        )

    html_content = _build_pdf_html_multiple_authors(
        all_authors=all_authors,
        show_all=show_all,
        journal_logo_base64=journal_logo_base64,
        app_logo_base64=app_logo_base64,
        theme_colors=theme_colors,
        lang=lang,
        filter_params=filter_params,
        create_visualizations_fn=create_visualizations_fn,
    )

    pdf_bytes = _WeasyHTML(string=html_content).write_pdf()
    return pdf_bytes
