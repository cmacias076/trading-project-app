# 📊 Paper Trading App

A Django-base paper trading simulation that lets users buy and sell instruments

---

## 🚀 Features

- 💰 $10,000 starting virtual cash
- 📈 Real-time & historical price data (via `yfinance`)
- 🛒 Simulated buying and selling
- 📊 Portfolio tracking with gain/loss %
- 📉 Interactive charts using Chart.js
- ♻️ Reset portfolio anytime

---

## 🛠 Tech Stack

- **Backend:** Python 3, Django
- **Database:** MySQL
- **Data API:** yfinance
- **Frontend:** Django Templates, HTML/CSS, Chart.js
- **Others:** `requests`, `curl_cffi`

---

## 📦 Setup Instructions

### Prerequisites

- Python 3.x  
- MySQL  
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/cmacias076/trading-project-app.git
cd trading-project-app

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 🔧 Configure Database

Update `settings.py` with your MySQL credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_db_name',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

### ✅ Final Steps

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver

Visit the app: http://127.0.0.1:8000
```
---

### 📁 **`.gitignore` (Recommended)**

```gitignore
# Python
*.pyc
__pycache__/

# Django
*.log
db.sqlite3

# Virtual Environment
venv/
.env

# IDEs and Editors
.vscode/
.idea/

# OS Files
.DS_Store
Thumbs.db
```
---

### 🚀 **Future Improvements**

- [ ] Add user login/authentication   
- [ ] Deploy app to production (e.g., Railway, Heroku)  
- [ ] Add search and filter functionality for instruments  