"""
Stock Fundamental Analyzer — Flask Web App
Same logic as Tkinter v15, converted to REST API
"""
from flask import Flask, jsonify, request, render_template
import requests, re, json, os
from bs4 import BeautifulSoup

app = Flask(__name__)

# ── COOKIES (update when expired) ─────────────────────────────────────────────
SCREENER_COOKIES = {
    'csrftoken': os.environ.get('SCREENER_CSRF', 'q7LJ51o4dJS1G5jx15mNILCtbjW6GuTk'),
    'sessionid': os.environ.get('SCREENER_SESSION', 'wao3vnsbhmd9jv8rre730xmma6t540a3'),
    'theme': 'dark',
}
CHARTINK_COOKIES = {
    'ci_session': os.environ.get('CHARTINK_SESSION', 'eyJpdiI6InpqVnMvVDM1aGV6em53WGR6eUo4cVE9PSIsInZhbHVlIjoiazY3SWU4bHh0NlAzOUlVNDE1ZU1ob3NhVnU0ZWNta3N0QVA4aFFSbVJEZFRMaWpQN0JrMnlONUpZRXQwMGtmbGxXM0Q3djVLNVZvcFc2K29lR3NUSkRSTlpvSkIwbDZkSk1mRk5HTDBpbWhpN051eFp5QUJiM041aEFidVloU1ciLCJtYWMiOiI1YzkyNzVhOWJjZmM3NzZlNWIyZmYzNjk0ODU5NTQ0ODliN2U4MGM1NDQ1NGRiMmU2NjNlZGU3MDllYTNkMGZlIiwidGFnIjoiIn0%3D'),
    'XSRF-TOKEN': os.environ.get('CHARTINK_XSRF', 'eyJpdiI6IlNGSFprMFdkb2NFTE1KQy9qWHZoOUE9PSIsInZhbHVlIjoiUTN5K25WekZoSEZmenlYVm1adWx0a1NzbkxHMGZjVGhXZktUR01QMWU2WmxXcFdndnNqRDkxdXNibktpK1BKVTRRalNpRmNVRWM5N3ZwaHRtdTR0M2JGU1hIMG42czMySlhScXFZOGxoaUIrQkw0VkFaRTNuNjhiazNncjVmRGQiLCJtYWMiOiJmYjgyMzY3NWNkOTc2N2Y1ZjNlMThjNjQ4ZjYzYTE3ZmExNzhmMWE5MzgyMzVkYzFhZTZkZDQ4YjJkMGVlODM0IiwidGFnIjoiIn0%3D'),
}

# ── SESSIONS ──────────────────────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
    'Referer': 'https://www.screener.in/',
})
SESSION.cookies.update(SCREENER_COOKIES)

NSE_SESSION = requests.Session()
NSE_SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
    'Referer': 'https://www.nseindia.com/',
    'Accept': 'application/json',
})

# ── CRITERIA ──────────────────────────────────────────────────────────────────
CRITERIA = {
    'swing': [
        ('Market Cap',        'market_cap',        '> 1000 Cr',          lambda v: v > 1000),
        ('Net Profit',        'net_profit',         '> 0',                lambda v: v > 0),
        ('Net Profit Qtr',    'net_profit_qtr',     '> 0',                lambda v: v > 0),
        ('Debt to Equity',    'debt_to_equity',     '< 1',                lambda v: v < 1),
        ('Current Ratio',     'current_ratio',      '> 1',                lambda v: v > 1),
        ('Interest Coverage', 'interest_coverage',  '> 3',                lambda v: v > 3),
        ('Promoter Holding',  'promoter_holding',   '> 50%',              lambda v: v > 50),
        ('Pledged %',         'pledged',            '< 10%',              lambda v: v < 10),
        ('ROE',               'roe',                '> 12%',              lambda v: v > 12),
        ('Profit Growth 3Y',  'profit_growth_3y',   '> 10%',              lambda v: v > 10),
        ('Promoter Change?',  'promoter_change',    'No big fall >2%',    lambda v: v > -2.0),
        ('FII/DII Chg',       'fii_change',         '>= 0 (not falling)', lambda v: v >= -1.0),
        ('Sector Outlook',    '_manual',            'Positive?',          None),
    ],
    'positional': [
        ('Market Cap',        'market_cap',        '> 1000 Cr',          lambda v: v > 1000),
        ('Net Profit',        'net_profit',         '> 0',                lambda v: v > 0),
        ('Net Profit Qtr',    'net_profit_qtr',     '> 0',                lambda v: v > 0),
        ('Debt to Equity',    'debt_to_equity',     '< 1',                lambda v: v < 1),
        ('Current Ratio',     'current_ratio',      '> 1.2',              lambda v: v > 1.2),
        ('Interest Coverage', 'interest_coverage',  '> 3',                lambda v: v > 3),
        ('Promoter Holding',  'promoter_holding',   '> 50%',              lambda v: v > 50),
        ('Pledged %',         'pledged',            '< 10%',              lambda v: v < 10),
        ('ROE',               'roe',                '> 15%',              lambda v: v > 15),
        ('ROCE',              'roce',               '> 15%',              lambda v: v > 15),
        ('Operating Margin',  'operating_margin',   '> 15%',              lambda v: v > 15),
        ('Sales Growth 3Y',   'sales_growth_3y',    '> 10%',              lambda v: v > 10),
        ('Profit Growth 3Y',  'profit_growth_3y',   '> 15%',              lambda v: v > 15),
        ('Promoter Change?',  'promoter_change',    'No big fall >2%',    lambda v: v > -2.0),
        ('FII/DII Chg',       'fii_change',         '>= 0 (not falling)', lambda v: v >= -1.0),
        ('Sector Outlook',    '_manual',            'Positive?',          None),
    ],
    'longterm': [
        ('Market Cap',        'market_cap',        '> 2000 Cr',          lambda v: v > 2000),
        ('Net Profit',        'net_profit',         '> 0',                lambda v: v > 0),
        ('Net Profit Qtr',    'net_profit_qtr',     '> 0',                lambda v: v > 0),
        ('Debt to Equity',    'debt_to_equity',     '< 0.5',              lambda v: v < 0.5),
        ('Current Ratio',     'current_ratio',      '> 1.5',              lambda v: v > 1.5),
        ('Interest Coverage', 'interest_coverage',  '> 5',                lambda v: v > 5),
        ('Promoter Holding',  'promoter_holding',   '> 50%',              lambda v: v > 50),
        ('Pledged %',         'pledged',            '< 5%',               lambda v: v < 5),
        ('ROE',               'roe',                '> 20%',              lambda v: v > 20),
        ('ROCE',              'roce',               '> 20%',              lambda v: v > 20),
        ('Operating Margin',  'operating_margin',   '> 15%',              lambda v: v > 15),
        ('Net Profit Margin', 'net_margin',         '> 10%',              lambda v: v > 10),
        ('Sales Growth 3Y',   'sales_growth_3y',    '> 12%',              lambda v: v > 12),
        ('Profit Growth 3Y',  'profit_growth_3y',   '> 12%',              lambda v: v > 12),
        ('Sales Growth 5Y',   'sales_growth_5y',    '> 12%',              lambda v: v > 12),
        ('Profit Growth 5Y',  'profit_growth_5y',   '> 12%',              lambda v: v > 12),
        ('EPS Growth 5Y',     'eps_growth_5y',      '> 10%',              lambda v: v > 10),
        ('PEG Ratio',         'peg',                '< 2',                lambda v: 0 < v < 2),
        ('Price to Book',     'price_to_book',      '< 10',               lambda v: 0 < v < 10),
        ('Dividend Yield',    'dividend_yield',     '> 0%',               lambda v: v >= 0),
        ('Promoter Change?',  'promoter_change',    'No big fall >2%',    lambda v: v > -2.0),
        ('FII/DII Chg',       'fii_change',         '>= 0 (not falling)', lambda v: v >= -1.0),
        ('Sector Outlook',    '_manual',            'Positive?',          None),
    ],
}

CHARTINK_SCREENERS = [
    {"label": "🏔️ 52W High",           "url": "https://chartink.com/screener/fresh-52-week-highs",                    "slug": "fresh-52-week-highs"},
    {"label": "📈 52W High Breakout",   "url": "https://chartink.com/screener/52-week-high-breakout",                  "slug": "52-week-high-breakout"},
    {"label": "📊 Near 52W High",       "url": "https://chartink.com/screener/copy-stock-near-5-of-52-week-high-36691","slug": "copy-stock-near-5-of-52-week-high-36691"},
    {"label": "🔵 Swing Scanner",       "url": "https://chartink.com/screener/claude-swing-trading-screener",          "slug": "claude-swing-trading-screener"},
    {"label": "🟡 Positional Scanner",  "url": "https://chartink.com/screener/claude-positinal-screener",              "slug": "claude-positinal-screener"},
    {"label": "🟢 Long Term Scanner",   "url": "https://chartink.com/screener/claude-long-term",                       "slug": "claude-long-term"},
    {"label": "📐 44 MA Scanner",       "url": "https://chartink.com/screener/44-ma-swing-stocks-3",                   "slug": "44-ma-swing-stocks-3"},
    {"label": "🚀 Rocket Base",         "url": "https://chartink.com/screener/copy-rb-stockexploder-322",              "slug": "copy-rb-stockexploder-322"},
    {"label": "🌀 VCP Scanner",         "url": "https://chartink.com/screener/copy-vcp-stockexploder-223",             "slug": "copy-vcp-stockexploder-223"},
    {"label": "💥 Breakout Short Term", "url": "https://chartink.com/screener/copy-breakouts-in-short-term-5280",      "slug": "copy-breakouts-in-short-term-5280"},
    {"label": "⭐ Badiya Scanner",      "url": "https://chartink.com/screener/badiya-vala-scanner",                    "slug": "badiya-vala-scanner"},
    {"label": "🔍 Swing Scanner 2",     "url": "https://chartink.com/screener/swing-scanner-20102336",                 "slug": "swing-scanner-20102336"},
]

CHARTINK_SCAN_CLAUSES = {
    "fresh-52-week-highs": "( {cash} (  daily high >  1 day ago max( 240 ,  daily close ) and  daily close >  20 and  daily volume >  5000 and  daily close >  1 day ago close and  daily sma(  daily volume , 20 ) *  daily sma( close,20 ) >  20000000 ) )",
    "52-week-high-breakout": "( {cash} (  daily close >  1 day ago max( 240 ,  daily high ) ) )",
    "claude-swing-trading-screener": "( {cash} (  daily close >  daily ema(  daily close , 21 ) and  daily ema(  daily close , 21 ) >  daily ema(  daily close , 50 ) and  daily rsi( 14 ) >  50 and  daily rsi( 14 ) <  70 and  daily volume >  daily sma(  daily volume , 20 ) and  daily low <=  daily ema(  daily close , 21 ) *  1.02 and  market cap >  500 ) )",
    "claude-positinal-screener": "( {cash} (  weekly close >  weekly ema(  weekly close , 10 ) and  weekly ema(  weekly close , 10 ) >  weekly ema(  weekly close , 40 ) and  weekly rsi( 14 ) >  55 and  weekly rsi( 14 ) <  75 and  weekly volume >  weekly sma(  weekly volume , 20 ) and  weekly low <=  weekly ema(  weekly close , 10 ) *  1.02 and  market cap >  1000 ) )",
    "claude-long-term": "( {cash} (  monthly close >  monthly ema(  monthly close , 10 ) and  monthly ema(  monthly close , 10 ) >  monthly ema(  monthly close , 40 ) and  monthly rsi( 14 ) >  50 and  monthly close >  monthly open and  monthly volume >  monthly sma(  monthly volume , 12 ) and  monthly low <=  monthly ema(  monthly close , 10 ) *  1.03 and  market cap >  2000 ) )",
    "44-ma-swing-stocks-3": "( {cash} (  daily close >  daily sma(  daily close , 44 ) and  daily sma(  daily close , 44 ) >  1 day ago sma(  daily close , 44 ) and  daily sma(  daily close , 44 ) >  daily ema(  daily close , 200 ) and  daily low <=  daily sma(  daily close , 44 ) *  1.02 and  market cap >  500 ) )",
    "copy-stock-near-5-of-52-week-high-36691": "( {cash} (  daily close >=  daily max( 252 ,  daily high ) *  .95 and  daily close /  65 days ago close >  1 and  daily close >  10 and  daily ema(  daily close , 20 ) >  daily ema(  daily close , 50 ) and  daily close >  daily ema(  daily close , 21 ) and( {cash} (  yearly return on capital employed percentage >  15 and  yearly return on net worth percentage >=  15 ) ) and  market cap >  1000 and  quarterly net sales >=  1 quarter ago net sales ) )",
    "copy-rb-stockexploder-322": "( {cash} (  daily wma( close,1 ) >  monthly wma( close,2 ) +  1 and  monthly wma( close,2 ) >  monthly wma( close,4 ) +  2 and  daily wma( close,1 ) >  weekly wma( close,6 ) +  2 and  weekly wma( close,6 ) >  weekly wma( close,12 ) +  2 and  daily wma( close,1 ) >  4 days ago wma( close,12 ) +  2 and  daily wma( close,1 ) >  2 days ago wma( close,20 ) +  2 and  daily close >  25 and  daily close <=  500 and  weekly volume >  85000 and  quarterly net sales >=  1 quarter ago net sales ) )",
    "copy-vcp-stockexploder-223": "( {cash} (  daily avg true range( 14 ) <  10 days ago avg true range( 14 ) and  daily avg true range( 14 ) /  daily close <  0.08 and  daily close >  (  weekly max( 52 ,  weekly close ) *  0.75 ) and  daily ema(  daily close , 50 ) >  daily ema(  daily close , 150 ) and  daily ema(  daily close , 150 ) >  daily ema(  daily close , 200 ) and  daily close >  daily ema(  daily close , 50 ) and  daily close >  10 and  daily close *  daily volume >  1000000 and  quarterly net sales >=  1 quarter ago net sales ) )",
    "copy-breakouts-in-short-term-5280": "( {cash} (  daily max( 5 ,  daily close ) >  6 days ago max( 120 ,  daily close ) *  1.05 and  daily volume >  daily sma( volume,5 ) and  daily close >  1 day ago close and  quarterly net sales >=  1 quarter ago net sales ) )",
    "badiya-vala-scanner": "( {cash} (  daily volume >  daily sma(  daily volume , 20 ) and  daily close >  daily upper bollinger band( 20 , 2 ) and  weekly close >  weekly upper bollinger band( 20 , 2 ) and  monthly close >  monthly upper bollinger band( 20 , 2 ) and  daily rsi( 14 ) >  60 and  weekly rsi( 14 ) >  60 and  monthly rsi( 14 ) >  60 and  monthly wma(  monthly close , 30 ) >  monthly wma(  monthly close , 50 ) and  1 month ago  wma(  monthly close , 30 )<=  1 month ago  wma(  monthly close , 50 ) and  monthly wma(  monthly close , 30 ) >  60 and  monthly wma(  monthly close , 50 ) >  60 ) )",
    "swing-scanner-20102336": "( {cash} (  daily open >=  1 day ago close and  daily close >=  daily ema(  daily close , 20 ) and  daily ema(  daily close , 10 ) >=  daily ema(  daily close , 20 ) and  daily macd line( 26 , 12 , 9 ) >  daily macd signal( 26 , 12 , 9 ) and  1 day ago  macd line( 26 , 12 , 9 ) <=  1 day ago  macd signal( 26 , 12 , 9 ) and  daily rsi( 14 ) >=  59 and  market cap >=  2000 and  quarterly net sales >=  1 quarter ago net sales ) )",
}

NSE_BROAD = {'NIFTY 50','NIFTY NEXT 50','NIFTY 100','NIFTY 200','NIFTY 500','NIFTY MIDCAP 50','NIFTY MIDCAP 100','NIFTY MIDCAP 150','NIFTY SMLCAP 50','NIFTY SMLCAP 100','NIFTY SMLCAP 250','NIFTY MIDSML 400','NIFTY LARGEMID250','NIFTY MID SELECT','NIFTY MICROCAP250','NIFTY TOTAL MKT','INDIA VIX','NIFTY500 MULTICAP','NIFTY500 LMS EQL','NIFTY FPI 150'}
NSE_SECTORAL = {'NIFTY AUTO','NIFTY BANK','NIFTY FIN SERVICE','NIFTY FINSRV25 50','NIFTY FMCG','NIFTY IT','NIFTY MEDIA','NIFTY METAL','NIFTY PHARMA','NIFTY PSU BANK','NIFTY REALTY','NIFTY PVT BANK','NIFTY HEALTHCARE','NIFTY CONSR DURBL','NIFTY OIL AND GAS','NIFTY MIDSML HLTH','NIFTY CHEMICALS','NIFTY500 HEALTH','NIFTY FINSEREXBNK','NIFTY MS IT TELCM','NIFTY MS FIN SERV'}
NSE_STRATEGY = {'NIFTY DIV OPPS 50','NIFTY50 VALUE 20','NIFTY100 QUALTY30','NIFTY50 EQL WGT','NIFTY100 EQL WGT','NIFTY100 LOWVOL30','NIFTY ALPHA 50','NIFTY200 QUALTY30','NIFTY ALPHALOWVOL','NIFTY200MOMENTM30','NIFTY M150 QLTY50','NIFTY200 ALPHA 30','NIFTYM150MOMNTM50','NIFTY500MOMENTM50','NIFTYMS400 MQ 100','NIFTYSML250MQ 100','NIFTY TOP 10 EW','NIFTY AQL 30','NIFTY AQLV 30','NIFTY HIGHBETA 50','NIFTY LOW VOL 50','NIFTY QLTY LV 30','NIFTY SML250 Q50','NIFTY TOP 15 EW','NIFTY100 ALPHA 30','NIFTY200 VALUE 30','NIFTY500 EW','NIFTY MULTI MQ 50','NIFTY500 VALUE 50','NIFTY TOP 20 EW','NIFTY500 QLTY50','NIFTY500 LOWVOL50','NIFTY500 MQVLV50','NIFTY500 FLEXICAP','NIFTY TMMQ 50','NIFTY GROWSECT 15','NIFTY50 USD'}
NSE_SKIP = {'NIFTY GS 8 13YR','NIFTY GS 10YR','NIFTY GS 10YR CLN','NIFTY GS 4 8YR','NIFTY GS 11 15YR','NIFTY GS 15YRPLUS','NIFTY GS COMPSITE','BHARATBOND-APR30','BHARATBOND-APR31','BHARATBOND-APR32','BHARATBOND-APR33','NIFTY50 TR 2X LEV','NIFTY50 PR 2X LEV','NIFTY50 TR 1X INV','NIFTY50 PR 1X INV','NIFTY50 DIV POINT'}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def clean_num(text):
    if text is None: return None
    t = str(text).strip()
    if t.startswith('(') and t.endswith(')'): t = '-' + t[1:-1]
    t = re.sub(r'[₹,\s]', '', t)
    t = re.sub(r'(Cr|cr)\.?$', '', t)
    t = t.replace('%', '').strip()
    if t in ['-', '', '--', 'N/A', 'na', 'NA', '—', '–']: return None
    try: return float(t)
    except: return None

def latest_valid(cells, from_end=2):
    nums = [clean_num(c.get_text()) for c in cells[1:]]
    valid = [n for n in nums if n is not None]
    if not valid: return None
    return valid[-from_end] if len(valid) >= from_end else valid[-1]

# ── SCREENER SCRAPER (same as v15) ────────────────────────────────────────────
def scrape_screener(url):
    r = SESSION.get(url, timeout=22)
    soup = BeautifulSoup(r.text, 'html.parser')
    d = {
        'name': '', 'page_url': r.url, 'is_consolidated': 'consolidated' in r.url,
        'nse_symbol': None, 'market_cap': None, 'current_price': None,
        'pe': None, 'roe': None, 'roce': None, 'dividend_yield': None, '_book_value': None,
        'debt_to_equity': None, 'current_ratio': None, 'peg': None,
        'price_to_book': None, 'interest_coverage': None,
        'promoter_holding': None, 'pledged': None,
        'promoter_holding_prev': None, 'promoter_change': None,
        'fii_holding': None, 'dii_holding': None, 'fii_change': None, 'dii_change': None,
        'net_profit': None, 'net_profit_qtr': None,
        'operating_margin': None, 'net_margin': None,
        'operating_profit_annual': None, 'interest_annual': None,
        'sales_growth_3y': None, 'sales_growth_5y': None,
        'profit_growth_3y': None, 'profit_growth_5y': None, 'eps_growth_5y': None,
    }
    for sel in ['h1.margin-0', '.company-name h1', 'h1']:
        el = soup.select_one(sel)
        if el: d['name'] = el.get_text(strip=True); break
    m = re.search(r'/company/([^/]+)/', r.url)
    if m: d['nse_symbol'] = m.group(1).upper()
    for li in soup.select('#top-ratios li'):
        name_el = li.select_one('.name'); num_el = li.select_one('.number')
        if not name_el or not num_el: continue
        name = name_el.get_text(strip=True).lower().strip()
        val = clean_num(num_el.get_text())
        if val is None: continue
        if 'market cap' in name: d['market_cap'] = val
        elif 'current price' in name: d['current_price'] = val
        elif 'stock p/e' in name: d['pe'] = val
        elif name == 'roce': d['roce'] = val
        elif name == 'roe': d['roe'] = val
        elif 'book value' in name: d['_book_value'] = val
        elif 'dividend yield' in name: d['dividend_yield'] = val
    if d['_book_value'] and d['current_price'] and d['_book_value'] > 0:
        d['price_to_book'] = round(d['current_price'] / d['_book_value'], 2)
    # Quick ratios API
    _qd = {}
    try:
        info_el = soup.find(attrs={'data-warehouse-id': True})
        if info_el:
            wid = info_el['data-warehouse-id']
            cid = info_el.get('data-company-id', '')
            for api_url in [f"https://www.screener.in/api/company/{wid}/quick_ratios/", f"https://www.screener.in/api/company/{cid}/quick_ratios/"]:
                try:
                    api_r = SESSION.get(api_url, timeout=8)
                    if api_r.status_code == 200 and api_r.text.strip():
                        ct = api_r.headers.get('content-type', '')
                        if 'json' in ct:
                            jdata = api_r.json()
                            items = jdata if isinstance(jdata, list) else jdata.get('ratios', jdata.get('quick_ratios', []))
                            for item in (items or []):
                                n = (item.get('name') or item.get('title', '')).strip()
                                v = item.get('value') or item.get('number', '')
                                if n: _qd[n] = str(v)
                        if _qd: break
                except: continue
    except: pass
    QMAP = {
        'Debt to equity': 'debt_to_equity', 'Price to book value': 'price_to_book',
        'Current ratio': 'current_ratio', 'PEG Ratio': 'peg',
        'Int Coverage': 'interest_coverage', 'Promoter holding': 'promoter_holding',
        'Pledged percentage': 'pledged', 'Change in Prom Hold': 'promoter_change',
        'Profit Var 5Yrs': 'profit_growth_5y', 'Profit Var 3Yrs': 'profit_growth_3y',
        'Sales growth 5Years': 'sales_growth_5y', 'EPS growth 5Years': 'eps_growth_5y',
        'Net profit': 'net_profit', 'OPM': 'operating_margin',
        'Chg in FII Hold': 'fii_change', 'Chg in DII Hold': 'dii_change',
    }
    for fname, dkey in QMAP.items():
        if fname in _qd:
            try:
                raw = str(_qd[fname]).replace(',', '').replace('%', '').replace('₹', '').rstrip('x').strip()
                raw = raw.split('/')[0].strip()
                if raw.startswith('(') and raw.endswith(')'): raw = '-' + raw[1:-1]
                if raw: d[dkey] = float(raw)
            except: pass
    # Shareholding
    sh = soup.find('section', id='shareholding')
    if sh:
        tables = sh.select('table')
        if tables:
            for row in tables[0].select('tr'):
                cells = row.select('td')
                if not cells: continue
                label = cells[0].get_text(strip=True).lower()
                vals = [clean_num(c.get_text(strip=True).replace('%', '')) for c in cells[1:]]
                vals = [v for v in vals if v is not None]
                if not vals: continue
                if 'promoters' in label:
                    d['promoter_holding'] = vals[-1]
                    if len(vals) >= 2: d['promoter_holding_prev'] = vals[0]
                elif 'fii' in label or 'foreign' in label:
                    d['fii_holding'] = vals[-1]
                    if len(vals) >= 2: d['_fii_prev'] = vals[0]
                elif 'dii' in label or 'domestic' in label:
                    d['dii_holding'] = vals[-1]
                    if len(vals) >= 2: d['_dii_prev'] = vals[0]
                elif 'pledg' in label:
                    d['pledged'] = vals[-1]
    if d['pledged'] is None and d['promoter_holding'] is not None:
        d['pledged'] = 0.0
    # P&L
    pl = soup.find('section', id='profit-loss')
    if pl:
        mode = None; rev_all = []; prf_all = []
        for row in pl.select('table tr'):
            cells = row.select('td, th')
            if not cells: continue
            label = cells[0].get_text(strip=True).lower()
            vals_text = [c.get_text(strip=True) for c in cells[1:]]
            if 'compounded sales growth' in label: mode = 'sales'; continue
            if 'compounded profit growth' in label: mode = 'profit'; continue
            if 'stock price cagr' in label: mode = 'stock'; continue
            if 'return on equity' in label: mode = 'roe_s'; continue
            if mode in ('sales', 'profit') and vals_text:
                val = clean_num(vals_text[0])
                if val is not None:
                    if '5 year' in label:
                        if mode == 'sales' and d['sales_growth_5y'] is None: d['sales_growth_5y'] = val
                        if mode == 'profit' and d['profit_growth_5y'] is None: d['profit_growth_5y'] = val
                    elif '3 year' in label:
                        if mode == 'sales' and d['sales_growth_3y'] is None: d['sales_growth_3y'] = val
                        if mode == 'profit' and d['profit_growth_3y'] is None: d['profit_growth_3y'] = val
                continue
            mode = None
            nums = [clean_num(v) for v in vals_text]
            valid = [n for n in nums if n is not None]
            if not valid: continue
            if label in ('revenue+', 'revenue', 'sales+', 'sales', 'net sales', 'total revenue'):
                rev_all = [n for n in nums if n is not None]
            elif label in ('net profit+', 'net profit', 'profit after tax'):
                if d['net_profit'] is None: d['net_profit'] = valid[-2] if len(valid) >= 2 else valid[-1]
                prf_all = [n for n in nums if n is not None]
            elif label in ('operating profit', 'operating profit+', 'ebit', 'ebitda'):
                d['operating_profit_annual'] = valid[-2] if len(valid) >= 2 else valid[-1]
            elif label == 'opm %':
                if d['operating_margin'] is None: d['operating_margin'] = valid[-2] if len(valid) >= 2 else valid[-1]
            elif label in ('interest', 'finance cost', 'finance costs'):
                if d['interest_annual'] is None: d['interest_annual'] = valid[-2] if len(valid) >= 2 else valid[-1]
            elif 'net profit %' in label or label == 'npm %':
                if d['net_margin'] is None: d['net_margin'] = valid[-2] if len(valid) >= 2 else valid[-1]
        if d['interest_coverage'] is None:
            op = d.get('operating_profit_annual'); intr = d.get('interest_annual'); np_ = d.get('net_profit')
            if intr and intr > 0:
                if op: d['interest_coverage'] = round(op / intr, 2)
                elif np_: d['interest_coverage'] = round((np_ + intr) / intr, 2)
            elif op and not intr: d['interest_coverage'] = 999.0
        if rev_all:
            if len(rev_all) >= 4 and d['sales_growth_3y'] is None:
                try: d['sales_growth_3y'] = round(((rev_all[-1] / rev_all[-4]) ** (1 / 3) - 1) * 100, 1)
                except: pass
            if len(rev_all) >= 5 and d['sales_growth_5y'] is None:
                try: d['sales_growth_5y'] = round(((rev_all[-1] / rev_all[-5]) ** (1 / 4) - 1) * 100, 1)
                except: pass
        if prf_all:
            if len(prf_all) >= 4 and d['profit_growth_3y'] is None:
                try:
                    if prf_all[-4] > 0 and prf_all[-1] > 0: d['profit_growth_3y'] = round(((prf_all[-1] / prf_all[-4]) ** (1 / 3) - 1) * 100, 1)
                except: pass
    # Quarterly
    qr = soup.find('section', id='quarters')
    if qr:
        for row in qr.select('table tr'):
            cells = row.select('td, th')
            if not cells: continue
            if 'net profit' in cells[0].get_text(strip=True).lower():
                nums = [clean_num(c.get_text()) for c in cells[1:]]
                valid = [n for n in nums if n is not None]
                if valid: d['net_profit_qtr'] = valid[-1]; break
    # Balance sheet
    bs = soup.find('section', id='balance-sheet')
    if bs:
        eq_cap = res = borr = deposits = other_liab = other_assets = None
        for row in bs.select('table tr'):
            cells = row.select('td, th')
            if not cells: continue
            label = cells[0].get_text(strip=True).lower()
            nums = [clean_num(c.get_text()) for c in cells[1:]]
            valid = [n for n in nums if n is not None]
            if not valid: continue
            if 'equity capital' in label: eq_cap = valid[-1]
            elif 'reserves' in label: res = valid[-1]
            elif label.startswith('borrowing'): borr = valid[-1]
            elif 'deposits' in label: deposits = valid[-1]
            elif 'other liabilities' in label: other_liab = valid[-1]
            elif 'other assets' in label: other_assets = valid[-1]
        total_eq = (eq_cap or 0) + (res or 0)
        if d['debt_to_equity'] is None and total_eq > 0:
            if deposits is not None: d['debt_to_equity'] = round(((deposits or 0) + (borr or 0)) / total_eq, 2)
            elif borr is not None: d['debt_to_equity'] = round(borr / total_eq, 2) if borr > 0 else 0.0
        if d['current_ratio'] is None and other_assets and other_liab:
            cl = (borr or 0) + other_liab
            if cl > 0: d['current_ratio'] = round(other_assets / cl, 2)
    return d

def fetch_nse_live(sym):
    try:
        NSE_SESSION.get("https://www.nseindia.com", timeout=6)
        r = NSE_SESSION.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}", timeout=8)
        if r.status_code != 200: return {}
        j = r.json()
        pd_ = j.get('priceInfo', {}); meta = j.get('metadata', {})
        ltp = pd_.get('lastPrice'); chg = pd_.get('change'); chg_pct = pd_.get('pChange')
        high = pd_.get('intraDayHighLow', {}).get('max'); low = pd_.get('intraDayHighLow', {}).get('min')
        wk52 = pd_.get('weekHighLow', {}); w52h = wk52.get('max'); w52l = wk52.get('min')
        uc = pd_.get('upperCP'); lc = pd_.get('lowerCP')
        return {'ltp': ltp, 'change': chg, 'change_pct': chg_pct, 'high': high, 'low': low, 'week52_high': w52h, 'week52_low': w52l, 'upper_circuit': uc, 'lower_circuit': lc}
    except: return {}

def search_screener(q):
    try:
        r = SESSION.get(f"https://www.screener.in/api/company/search/?q={requests.utils.quote(q)}&v=3&fts=1", timeout=8)
        if r.status_code == 200: return r.json()
        return []
    except: return []

def fetch_chartink(slug):
    try:
        url = f"https://chartink.com/screener/{slug}"
        cs = requests.Session()
        cs.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120 Safari/537.36", "Accept": "text/html,application/xhtml+xml"})
        for k, v in CHARTINK_COOKIES.items():
            cs.cookies.set(k, v, domain="chartink.com")
        r = cs.get(url, timeout=18)
        if "login" in r.url.lower(): return {"error": "Chartink cookies expired"}
        soup = BeautifulSoup(r.text, "html.parser")
        csrf = ""
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta: csrf = meta.get("content", "")
        scan_clause = CHARTINK_SCAN_CLAUSES.get(slug, "")
        if not scan_clause:
            m = re.search(r'"scan_clause"\s*:\s*"((?:[^"\\]|\\.)+)"', r.text)
            if m: scan_clause = m.group(1).replace('\\"', '"')
        if not scan_clause: return {"error": f"No scan_clause for {slug}"}
        cs.headers.update({"X-CSRF-TOKEN": csrf, "X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json", "Accept": "application/json", "Origin": "https://chartink.com", "Referer": url})
        post_r = cs.post("https://chartink.com/screener/process", data=json.dumps({"scan_clause": scan_clause}), timeout=25)
        if post_r.status_code != 200: return {"error": f"POST failed {post_r.status_code}"}
        items = post_r.json().get("data", [])
        rows = []
        for item in items:
            sym = (item.get("nsecode") or item.get("symbol") or "").strip()
            name = (item.get("name") or item.get("company") or sym).strip()
            try: ltp = float(str(item.get("close", 0)).replace(",", ""))
            except: ltp = 0
            try: chg = float(str(item.get("per_chg", 0)).replace(",", "").replace("%", ""))
            except: chg = 0
            try: vol = float(str(item.get("volume", 0)).replace(",", ""))
            except: vol = 0
            if sym: rows.append({"symbol": sym, "company": name, "ltp": ltp, "change_pct": chg, "volume": vol})
        return {"rows": rows}
    except Exception as e:
        return {"error": str(e)}

def fetch_nse_all_indices():
    try:
        NSE_SESSION.get("https://www.nseindia.com", timeout=8)
        r = NSE_SESSION.get("https://www.nseindia.com/api/allIndices", timeout=12)
        if r.status_code != 200: return []
        rows = []
        for item in r.json().get('data', []):
            sym = (item.get('indexSymbol') or item.get('index', '')).strip()
            if not sym or sym in NSE_SKIP: continue
            try: chg = float(item.get('percentChange', 0))
            except: chg = 0.0
            try: last = float(item.get('last', 0))
            except: last = 0.0
            if sym in NSE_BROAD: cat = 'broad'
            elif sym in NSE_SECTORAL: cat = 'sectoral'
            elif sym in NSE_STRATEGY: cat = 'strategy'
            else: cat = 'thematic'
            rows.append({'name': sym, 'last': last, 'chg': chg, 'cat': cat})
        return rows
    except: return []

def fetch_nse_index_stocks(index_name):
    try:
        NSE_SESSION.get("https://www.nseindia.com", timeout=8)
        enc = requests.utils.quote(index_name)
        r = NSE_SESSION.get(f"https://www.nseindia.com/api/equity-stockIndices?index={enc}", timeout=15)
        if r.status_code != 200: return []
        rows = []
        for item in r.json().get('data', []):
            sym = (item.get('symbol') or '').strip()
            if not sym or sym == index_name: continue
            try: chg = float(item.get('pChange', 0))
            except: chg = 0.0
            try: ltp = float(str(item.get('lastPrice', 0)).replace(',', ''))
            except: ltp = 0.0
            rows.append({'symbol': sym, 'ltp': ltp, 'chg': chg})
        return rows
    except: return []

def build_checklist(data):
    result = {}
    for tab_key, criteria in CRITERIA.items():
        rows = []
        pass_count = 0; fail_count = 0; na_count = 0
        for label, key, condition, check_fn in criteria:
            val = data.get(key)
            if key == '_manual' or check_fn is None:
                status = 'manual'; na_count += 1
                display = '❓ Manual check'
            elif val is None:
                status = 'na'; na_count += 1
                display = 'N/A'
            else:
                try:
                    passed = check_fn(float(val))
                    status = 'pass' if passed else 'fail'
                    if passed: pass_count += 1
                    else: fail_count += 1
                    if key in ('market_cap',):
                        display = f"₹{val:.0f} Cr"
                    elif key in ('current_price',):
                        display = f"₹{val:.2f}"
                    elif key in ('interest_coverage',) and val >= 999:
                        display = "Debt-free"
                    else:
                        display = f"{val:.2f}"
                except:
                    status = 'na'; na_count += 1; display = str(val)
            rows.append({'label': label, 'key': key, 'condition': condition, 'status': status, 'value': display})
        result[tab_key] = {'rows': rows, 'pass': pass_count, 'fail': fail_count, 'na': na_count}
    return result

# ── FLASK ROUTES ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', screeners=CHARTINK_SCREENERS)

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    return jsonify(search_screener(q))

@app.route('/api/stock')
def api_stock():
    url = request.args.get('url', '').strip()
    sym = request.args.get('sym', '').strip()
    if not url: return jsonify({'error': 'No URL'})
    try:
        data = scrape_screener(url)
        if sym:
            data['nse'] = fetch_nse_live(sym)
        data['checklist'] = build_checklist(data)
        # Make serializable
        clean = {k: v for k, v in data.items() if not k.startswith('_') or k in ('_fii_prev', '_dii_prev')}
        return jsonify(clean)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chartink/<slug>')
def api_chartink(slug):
    return jsonify(fetch_chartink(slug))

@app.route('/api/nse/indices')
def api_nse_indices():
    return jsonify(fetch_nse_all_indices())

@app.route('/api/nse/index-stocks')
def api_nse_index_stocks():
    name = request.args.get('name', '').strip()
    if not name: return jsonify([])
    return jsonify(fetch_nse_index_stocks(name))

@app.route('/api/nse/announcements')
def api_nse_announcements():
    sym = request.args.get('sym', '').strip()
    if not sym: return jsonify([])
    try:
        NSE_SESSION.get("https://www.nseindia.com", timeout=6)
        NSE_SESSION.get(f"https://www.nseindia.com/get-quote/equity/{sym}", timeout=6)
        r = NSE_SESSION.get(f"https://www.nseindia.com/api/corp-info?symbol={sym}&market=equities&corpType=announcements", timeout=10)
        if r.status_code == 200:
            items = r.json().get('corpInfo', r.json().get('data', []))
            news = []
            for item in (items or [])[:8]:
                desc = item.get('subject') or item.get('headline') or item.get('desc') or ''
                date_ = item.get('exchdisstime') or item.get('bm_timestamp') or item.get('date') or ''
                att = item.get('attchmntFile') or ''
                if desc: news.append({'title': desc[:120], 'date': str(date_)[:16], 'url': f"https://nsearchives.nseindia.com/corporate/{att}" if att else ''})
            return jsonify(news)
    except: pass
    return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
