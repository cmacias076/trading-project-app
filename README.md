# Paper Trading App

## Project Overview
A paper trading application where a user can simulate buying and selling a small set of financial instruments using historical and current prices. The user starts with a fixed virtual cash balance and can track thr portfolios value over time.

## Setup Instructions


### Prerequisites:
- Python 3.x
- Django
- MySQL

### Steps to Run the App:
1. Clone the repository to your local machine:
````bash
    git clone https://github.com/cmacias076/trading-project-app.git

2. Navigate to the project directory:
    cd trading-project-app

3. Set up your virtual environment:
    python -m venv venv

4. Activate the virtual environment:
    * On Windows - 
        .\venv\Scripts\activate

    * On macOS/Linux:
        source venv/bin/activate

5. Install dependencies:
    pip install -r requirements.txt

6. Set up your database (MySQL):
    * Make sure you have your database created and update the settings in 'settings.py' to match your database credentials.

7. Run Migrations:
    python manage.py migrate

8. Create a superuser for admin access
    python manage.py createsuperuser

9. Run the development server:
    python manage.py runserver

10. Visit the app in your browser:
    https://127.0.0.1:8000/


### Features: 
    * View list of instruments with current prices.
    * View detailed charts of instrument prices.
    * Simulate trading by buying and selling instruments.
    * Track portfolio value over time.
    * View transaction history.

### Contributing
Feel free to fork this repository, create issues, and submit pull requests. Make sure to test your changes before submitting.


### Step 2: **Create a `.gitignore`**
This is important to avoid committing sensitive files or unnecessary data (like database files, caches, or Python virtual environments.)

**To Do:**
1. In your project directory, creat a '.gitignore' file. 
2. Add the following content to the '.gitignore':

    # Python
    *.pyc
    __pycache__/
    *.pyo
    *.pyd

    #Django
    db.sqlite3
    *.log
    *.pot
    *.pyv
    __pycache__/

    # Virtual Environment
    venv/
    .env/

    # IDEs and editors
    .vscode/
    .idea
    *.sublime-workspace
    *.sublime -project

    # OS files
    .DS_Store
    Thumbs.db