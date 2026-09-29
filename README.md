# eSports Manager — Flask CRUD App

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your SQL Server connection
Open `app.py` and edit the `DB_CONFIG` block at the top:

```python
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'localhost',        # or your server name e.g. 'DESKTOP-XYZ\\SQLEXPRESS'
    'database': 'eSports',
    'trusted_connection': 'yes',  # Windows Authentication

    # For SQL Server Auth instead, comment out trusted_connection and use:
    # 'uid': 'sa',
    # 'pwd': 'your_password',
}
```

### 3. Make sure ODBC Driver 17 is installed
Download from Microsoft if needed:
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### 4. Run the app
```bash
python app.py
```

Then open: http://127.0.0.1:5000

---

## SQL Injection Prevention — What's implemented

| Layer | Method |
|-------|--------|
| **Primary** | All DB queries use **parameterized statements** with `?` placeholders (pyodbc) — user input is NEVER concatenated into SQL strings |
| **Type casting** | `safe_int()` rejects anything non-numeric for ID/rank fields |
| **Length limiting** | `safe_str(value, max_length)` truncates to column max length |
| **Date validation** | `validate_date()` only accepts `YYYY-MM-DD` format via regex |
| **Status whitelisting** | `validate_status(value, allowed_list)` — only predefined values accepted |
| **Confirm on delete** | JavaScript confirmation before any DELETE |
| **FK error handling** | Catches `IntegrityError` and shows user-friendly message |

---

## Project Structure

```
esports_app/
├── app.py                  # Flask routes + SQL injection prevention helpers
├── requirements.txt
├── README.md
└── templates/
    ├── base.html           # Shared layout + nav
    ├── index.html          # Home dashboard
    ├── teams.html          # Teams list
    ├── team_form.html      # Add/Edit team
    ├── players.html        # Players list
    ├── player_form.html    # Add/Edit player
    ├── tournaments.html    # Tournaments list
    ├── tournament_form.html
    ├── matches.html        # Matches list
    └── match_form.html     # Add/Edit match
```
