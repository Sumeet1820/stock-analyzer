# Stock Fundamental Analyzer — Web App

## Deploy on Railway (Free)

### Step 1: GitHub pe upload karo
1. GitHub pe naya repo banao: `stock-analyzer`
2. Yeh saari files upload karo (app.py, templates/, requirements.txt, Procfile, railway.json)

### Step 2: Railway pe deploy karo
1. https://railway.app pe jao
2. "New Project" → "Deploy from GitHub repo"
3. Apna repo select karo
4. Railway automatically detect karega aur deploy karega
5. "Settings" → "Generate Domain" pe click karo → free URL milegi

### Step 3: Cookies update karo (Environment Variables)
Railway dashboard mein "Variables" tab mein yeh set karo:
```
SCREENER_CSRF    = <apni Screener CSRF cookie>
SCREENER_SESSION = <apna Screener session cookie>
CHARTINK_SESSION = <apni Chartink ci_session cookie>
CHARTINK_XSRF   = <apna Chartink XSRF-TOKEN>
```

### Cookies kaise nikale?
1. Browser mein Screener.in/Chartink pe login karo
2. F12 → Application → Cookies → copy karo

### Local Test
```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000 pe khulega
```

## Features
- 🏠 Home screen with quick stock buttons
- 📊 NSE Index Heatmaps (Broad/Sectoral/Thematic/Strategy)
- 🔍 Stock search with auto-suggest
- ✅ Swing / Positional / Long Term checklist
- 📡 Chartink scanners (12 screeners)
- 📰 NSE Announcements in right panel
