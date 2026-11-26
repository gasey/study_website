"""Read-only date-focused projection of live questions. Never publishes bank facts.

Dates in choices are ignored unless the selected answer passes existing readiness.
Ambiguous statements and calculations remain questions to check, without a date.
"""
import hashlib
import re
from datetime import date
from ..db import cursor
from .public_catalog_cache import public_catalog

MONTH_NAMES = ('January','February','March','April','May','June','July','August','September','October','November','December')
MONTHS = {name.lower(): i for i, name in enumerate(MONTH_NAMES, 1)}
for name, number in list(MONTHS.items()):
    MONTHS[name[:3]] = number
MONTHS['sept'] = 9
MONTH_PATTERN = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?'
DAY_MONTH = re.compile(rf'(?<!\w)(\d{{1,2}})(?:st|nd|rd|th)?\s*(?:of\s+)?({MONTH_PATTERN})(?:\s*,?\s*(\d{{4}})(?!\d))?', re.I)
MONTH_DAY = re.compile(rf'\b({MONTH_PATTERN})\s+(\d{{1,2}})(?!\d)(?:st|nd|rd|th)?(?:\s*,?\s*(\d{{4}})(?!\d))?', re.I)
MONTH_YEAR = re.compile(rf'\b({MONTH_PATTERN})\s*,?\s*((?:1[0-9]{{3}}|20[0-9]{{2}}))(?!\d)', re.I)
YEAR_ERA = re.compile(r'(?<!\w)([1-9][0-9]{0,3})\s*(BC|BCE|AD|CE)\b', re.I)
YEAR = re.compile(r'(?<![\w.,/])((?:1[0-9]{3}|20[0-9]{2}))(?:\s*(BC|BCE|AD|CE))?(?!\w|[.,/]\d)', re.I)
YEAR_PREFIX_REJECT = re.compile(r'(?:\b(?:per|exceeds?|above|below|under|over|rs\.?|inr|usd|section|sec\.?|article|art\.?|clause|rule|item|page|no\.?|code|model|serial|pin|iso|is)\s*|[₹$€£]\s*)$', re.I)
YEAR_SUFFIX_REJECT = re.compile(r'^\s*(?:live\s+births?|still[- ]?births?|births?|women|men|persons?|people|employees?|workers?|students?|voters?|seats?|km|mm|cm|kg|mg|kw|mw|kwh|hz|rpm|rev|rupees?|crores?|lakhs?|millions?|billions?|tonnes?|tons?|litres?|liters?|meters?|metres?|feet|ft|hours?|hrs?|minutes?|mins?|seconds?|bytes?|kb|mb|gb|bits?|calories?|kcal|volts?|watts?|amps?|ohms?|mpa|kpa|psi|ppm)\b', re.I)
OBSERVANCE = re.compile(r"\b((?:(?:World|International|National|Universal|United Nations|Indian|Global|Earth|Environment|Teachers?|Children|Women|Human Rights|Republic|Independence|Constitution|Labour|Labor|Army|Navy|Air Force|AIDS|Health|Water|Food|Literacy|Population|Press|Science|Youth|Tourism|Forests?|Ozone|Biodiversity|Mizoram|Statehood|Yoga|Mother|Father)[\w’' -]{0,70}?)\s+Day)\b", re.I)
BATTLE = re.compile(r'\b(Battle of [A-Za-z][A-Za-z -]{1,48}?)(?=\s*[,(:?]|\s+(?:was|is|in|marked|considered|for|on|fought|took|after)|$)', re.I)
DATE_FOCUS = re.compile(r'\b(?:when|which (?:year|date|day|month)|what (?:year|date)|in the year|observed on|celebrated on|falls on|held on|established in|founded in|born on|born in|took place in|fought in|attained statehood|became.*state|first observed)\b', re.I)
EVENT = re.compile(r'\b(?:battle|war|movement|treaty|pact|revolution|revolt|rebellion|act|amendment|constitution|independence|founded|established|formed|created|launched|statehood|anniversary|centenary|birth|born|died|death|conference|summit|mission|election|inaugurat|observed|celebrat|commemorat|abolish|partition|discovered|introduced|began|started|ended|invaded|passed|signed|adopted|enacted)\w*\b', re.I)
AMBIGUOUS = re.compile(r'\b(?:not|incorrect|false|except|following statements|statements given|consider the following|match the following|match list|chronological|ascending|descending|assertion\s*\(a\)|reason\s*\(r\))\b', re.I)
NON_EVENT = re.compile(r'\b(?:simple interest|compound interest|per annum|rate of interest|profit|depreciation|speed|distance|age of|how old|calendar year|leap year|day of the week|what day|weekday|train|rupees|\d+\s*%|code language|per\s+1000|live\s+births?|still[- ]?births?|energy\s+meter|trivector|single[- ]phase|3[- ]phase|\d+\s*(?:V|Hz|kW|MW|rpm|kWh|MPa)\b|number\s+of\s+(?:persons|people|employees|workers)|exceeds\s+_+|\bhow\s+(?:many|much)\b|\bcalculate\b|\bfind\s+the\s+value\b)\b', re.I)
# Database prefilter only. Python below decides what belongs in this date projection.
CANDIDATE_PATTERN = r'\m(day|date|year|when|anniversary|centenary|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|aug|sept|oct|nov|dec|battle|war|movement|treaty|pact|revolt|rebellion|born|died|founded|established|statehood)\M|\m(1[0-9]{3}|20[0-9]{2})\M'


def dates_in(text, years=True):
    """Unambiguous English month-name dates; no locale-dependent 3/4/19 guesses."""
    result = []
    spans = []
    for pattern, reverse in ((DAY_MONTH, False), (MONTH_DAY, True)):
        for match in pattern.finditer(text or ''):
            day, month = (match[2], match[1]) if reverse else (match[1], match[2])
            number = MONTHS[month.lower().rstrip('.')]
            year = int(match[3]) if match[3] else None
            try:
                date(year or 2000, number, int(day))
            except ValueError:
                spans.append(match.span())
                continue
            value = {'year': year, 'month': number, 'day': int(day), 'precision': 'date'}
            if value not in result:
                result.append(value)
            spans.append(match.span())
    for match in MONTH_YEAR.finditer(text or ''):
        if any(a <= match.start() < b for a, b in spans):
            continue
        result.append({'year': int(match[2]), 'month': MONTHS[match[1].lower().rstrip('.')], 'day': None, 'precision': 'month'})
        spans.append(match.span())
    for match in YEAR_ERA.finditer(text or ''):
        if any(a <= match.start() < b for a, b in spans):
            continue
        value = {'year': int(match[1]), 'month': None, 'day': None, 'precision': 'year'}
        if match[2].upper() in ('BC', 'BCE'):
            value['era'] = 'BCE'
        if value not in result:
            result.append(value)
        spans.append(match.span())
    if years:
        src = text or ''
        for match in YEAR.finditer(src):
            if any(a <= match.start() < b for a, b in spans):
                continue
            yr = int(match[1])
            if not match[2] and yr > 2050:
                continue
            before = src[max(0, match.start() - 24):match.start()]
            after = src[match.end():match.end() + 24]
            if not match[2] and (YEAR_PREFIX_REJECT.search(before) or YEAR_SUFFIX_REJECT.search(after)):
                continue
            value = {'year': yr, 'month': None, 'day': None, 'precision': 'year'}
            if match[2] and match[2].upper() in ('BC', 'BCE'):
                value['era'] = 'BCE'
            if value not in result:
                result.append(value)
    return result


def clean(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text or '')).strip()


def title_for(stem, observance=None, battle=None):
    first = bool(re.search(r'\bfirst\b', stem, re.I))
    if observance and not re.search(r'\btheme\b', stem, re.I):
        title = observance[1].strip(' \'’')
        suffix = stem[observance.end():]
        continuation = re.match(r'\s+((?:for|of)\s+.+?)(?=\s+(?:is|was|will|falls|observed|celebrated)|[?:]|$)', suffix, re.I)
        if continuation:
            title += ' ' + continuation[1].strip()
        return title + (' · first observance' if first else '')
    if battle and not re.search(r'\b(?:after|before)\b', stem, re.I):
        return battle[1].strip()
    text = re.sub(r'^\s*(?:\([ivx]+\)|\d+[.)])\s*', '', stem, flags=re.I)
    text = re.sub(r'^(?:In which (?:year|date|month)\s+(?:was|did|is|were)?|On which date\s+(?:was|is)?|When\s+(?:was|did|is|were|do we|do|does)?)\s*', '', text, flags=re.I)
    text = re.sub(r'\s+(?:was|is)?\s*(?:observed|celebrated|held|founded|established|fought)?\s*(?:on|in)(?:\s+(?:which|what|the|every)\s*(?:year|date|day|month))?\s*[?:.\-]*$', '', text, flags=re.I)
    text = re.sub(r'\s+(?:occur|take place|happen)\s*[?:.\-]*$', '', text, flags=re.I)
    text = re.sub(r'\b(the|a|an)\s+\1\b', r'\1', text, flags=re.I)
    text = text.strip(' ?:.,;–—-')
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text or stem


def project(row):
    stem = clean(row.get('question'))
    if not stem or len(stem) > 1400 or NON_EVENT.search(stem):
        return None
    observance, battle = OBSERVANCE.search(stem), BATTLE.search(stem)
    focused = bool(DATE_FOCUS.search(stem))
    # Incidental years in language, calculation or specialist questions are not events.
    subject = row.get('subject_id') or ''
    if subject in ('english', 'mizo', 'reasoning', 'reasoning-aptitude', 'mathematics', 'arithmetic') and not observance:
        return None
    stem_dates = dates_in(stem)
    event = bool(observance or battle or EVENT.search(stem))
    answer = clean(row.get('answer_text'))
    answer_dates = dates_in(answer)
    choice_dates = sum(bool(dates_in(clean(option))) for option in row.get('options') or [] if option)
    if not (observance or battle or event and (focused or stem_dates) or focused and choice_dates >= 2):
        return None
    date_gap = bool(re.search(r'\b(?:on|in|since|before|after|by)\s*(?:(?:the|which)\s+)?(?:year|date|month)?\s*[.:?_–—-]*$', stem, re.I))
    ambiguous = bool(AMBIGUOUS.search(stem) or re.search(r'\b\d{1,2}\s*[-–]\s*\d{1,2}\s*' + MONTH_PATTERN, stem, re.I))
    evidence = 'unresolved'
    found = []
    # Only a date-only selected answer is eligible; never parse an explanation or distractor.
    residue = answer
    for pattern in (DAY_MONTH, MONTH_DAY, MONTH_YEAR, YEAR_ERA, YEAR):
        residue = pattern.sub('', residue)
    date_only = not re.sub(r'[\s,.;:\-–—()]+', '', residue)
    if focused and row.get('answer_usable') and len(answer_dates) == 1 and date_only and not ambiguous:
        found, evidence = answer_dates, 'answer'
    elif len(stem_dates) == 1 and not ambiguous and not date_gap and (event or focused) and not re.search(r'\b(?:when|which year|what year|which date|what date)\b', stem, re.I):
        found, evidence = stem_dates, 'question'
    # A theme question's year is its reference period, not the observance's recurring date.
    context = bool(re.search(r'\btheme\b', stem, re.I))
    if context:
        evidence = 'question' if stem_dates and not ambiguous else 'unresolved'
        found = stem_dates[:1] if len(stem_dates) == 1 and not ambiguous else []
    title = title_for(stem, observance, battle)
    if evidence == 'question' and row.get('answer_usable') and len(answer) < 140 and OBSERVANCE.fullmatch(answer):
        title = answer
    kind = 'observance' if observance and not context else 'history' if battle or re.search(r'\b(?:battle|war|revolt|rebellion|movement|treaty|pact|revolution|partition)\b', stem, re.I) else 'event'
    # Do not invent month/day for year-only facts or annual recurrence for event dates.
    return {'title': title, 'category': kind, 'dates': found, 'evidence': evidence,
            'id': row['id'], 'question': stem, 'answer_source': row.get('answer_source') if evidence == 'answer' else None,
            'subject_id': subject or None, 'subject': row.get('subject_label') or None,
            'origin': row.get('origin') or 'paper'}


def build_index(rows):
    grouped = {}
    for row in rows:
        item = project(row)
        if not item:
            continue
        # First observance/theme/reference qualifiers stay in the title. Do not merge distinct facts.
        base = re.sub(r'[^a-z0-9]+', ' ', item['title'].casefold()).strip()
        signature = (base, tuple((d.get('year'), d.get('month'), d.get('day'), d.get('era')) for d in item['dates']))
        if signature not in grouped:
            digest = hashlib.sha256(repr(signature).encode()).hexdigest()[:20]
            grouped[signature] = {'id': 'date_' + digest, 'title': item['title'], 'category': item['category'], 'dates': item['dates'], 'questions': []}
        grouped[signature]['questions'].append({k: v for k, v in item.items() if k not in ('title', 'category', 'dates')})
    return list(grouped.values())


async def load_index():
    async with cursor() as cur:
        await cur.execute('SET LOCAL statement_timeout=12000')
        await cur.execute('''SELECT v.id,v.question,v.options,v.answer_text,v.answer_source,
          v.status,v.source_defect,v.key_disputed, qc.subject_id,qc.subject_label,
          EXISTS(SELECT 1 FROM v_mock_practice ready WHERE ready.id=v.id) AS answer_usable,
          CASE WHEN EXISTS(SELECT 1 FROM appearances a JOIN papers p ON p.id=a.paper_id
              WHERE a.canonical_id=v.id AND a.is_primary AND p.exam_type='Community')
            THEN 'community' ELSE 'paper' END AS origin
          FROM v_all_questions v
          LEFT JOIN question_classifications qc ON qc.question_id=v.id AND qc.review_status='approved'
          WHERE v.question ~* %s ORDER BY v.id''', (CANDIDATE_PATTERN,))
        rows = await cur.fetchall()
    return build_index(rows)


async def index():
    # Same short-lived, invalidated public-data cache used by other bank catalogs.
    return await public_catalog(('bank-date-index', 2), load_index)


def era_for(entry):
    if entry.get('category') == 'observance':
        return 'observances'
    first = next((d for d in entry.get('dates') or [] if d.get('year') is not None), None)
    if not first:
        return 'other'
    year = first['year']
    if first.get('era') == 'BCE' or year <= 1756:
        return 'ancient'
    if year <= 1856:
        return 'company'
    if year <= 1947:
        return 'crown'
    return 'republic'


def filtered(entries, *, month=None, category=None, origin='all', subject_id=None, q='', evidence='all', era='all'):
    words = q.casefold().split()
    result = []
    for entry in entries:
        questions = [row for row in entry['questions'] if (origin == 'all' or row['origin'] == origin) and (not subject_id or row['subject_id'] == subject_id)]
        if not questions:
            continue
        if category and entry['category'] != category:
            continue
        if era and era != 'all' and era_for(entry) != era:
            continue
        if month and not any(d['month'] == month for d in entry['dates']):
            continue
        if evidence == 'dated' and not entry['dates'] or evidence == 'unresolved' and entry['dates']:
            continue
        date_words = ' '.join(' '.join(str(value) for value in (d.get('day'), MONTH_NAMES[d['month']-1] if d.get('month') else None, d.get('year'), d.get('era')) if value) for d in entry['dates'])
        text = ' '.join([entry['title'], date_words, *(row['question'] for row in questions)]).casefold()
        if not all(word in text for word in words):
            continue
        result.append({**entry, 'questions': questions})
    return result


def summary(entry):
    questions = entry['questions']
    return {k: v for k, v in entry.items() if k != 'questions'} | {
        'era': era_for(entry),
        'question_count': len(questions), 'evidence': sorted({q['evidence'] for q in questions}),
        'subjects': sorted({q['subject'] for q in questions if q['subject']}),
        'preview': questions[0]['question'], 'first_question_id': questions[0]['id'],
    }
