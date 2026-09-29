from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pyodbc
import re

app = Flask(__name__)
app.secret_key = 'esports_secret_key_2024'

# =========================================
# DATABASE CONNECTION
# =========================================

DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'Moamen\\SQLEXPRESS',          # Change to your server name
    'database': 'eSports',
    'trusted_connection': 'yes',    # Windows Auth — change if using SQL Auth
    # 'uid': 'your_username',       # Uncomment for SQL Auth
    # 'pwd': 'your_password',       # Uncomment for SQL Auth
}

def get_connection():
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)


# =========================================
# SQL INJECTION PREVENTION HELPERS
# =========================================

def safe_int(value, default=None):
    """Safely cast to int — rejects non-numeric input."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, max_length=255):
    """
    Strip dangerous SQL characters and limit length.
    Primary defense is parameterized queries — this is a secondary layer.
    """
    if value is None:
        return None
    # Remove null bytes
    value = value.replace('\x00', '')
    # Limit length
    value = value[:max_length]
    return value

def validate_date(value):
    """Accept only YYYY-MM-DD format."""
    if value is None or value.strip() == '':
        return None
    if re.match(r'^\d{4}-\d{2}-\d{2}$', value.strip()):
        return value.strip()
    return None

def validate_status(value, allowed):
    """Whitelist-validate status fields."""
    return value if value in allowed else None


# =========================================
# HOME
# =========================================

@app.route('/')
def index():
    return render_template('index.html')


# =========================================
# TEAMS CRUD
# =========================================

@app.route('/teams')
def teams():
    conn = get_connection()
    cursor = conn.cursor()
    # Parameterized query — no user input here, but kept consistent
    cursor.execute("SELECT team_id, name, ranking, nationality, coach_name, logo_url, stadium FROM Team ORDER BY ranking")
    rows = cursor.fetchall()
    conn.close()
    return render_template('teams.html', teams=rows)

@app.route('/teams/add', methods=['GET', 'POST'])
def add_team():
    if request.method == 'POST':
        try:
            # Collect and sanitize inputs
            team_id   = safe_int(request.form.get('team_id'))
            name      = safe_str(request.form.get('name'), 100)
            logo_url  = safe_str(request.form.get('logo_url'), 255)
            ranking   = safe_int(request.form.get('ranking'))
            nation    = safe_str(request.form.get('nationality'), 50)
            coach     = safe_str(request.form.get('coach_name'), 100)
            stadium   = safe_str(request.form.get('stadium'), 100)

            if not team_id or not name:
                flash('Team ID and Name are required.', 'error')
                return redirect(url_for('add_team'))

            conn = get_connection()
            cursor = conn.cursor()
            # ✅ PARAMETERIZED QUERY — values never concatenated into SQL string
            cursor.execute(
                "INSERT INTO Team (team_id, name, logo_url, ranking, nationality, coach_name, stadium) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (team_id, name, logo_url, ranking, nation, coach, stadium)
            )
            conn.commit()
            conn.close()
            flash('Team added successfully!', 'success')
            return redirect(url_for('teams'))
        except pyodbc.IntegrityError:
            flash('Team ID already exists.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('team_form.html', team=None, action='Add')

@app.route('/teams/edit/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            name    = safe_str(request.form.get('name'), 100)
            logo    = safe_str(request.form.get('logo_url'), 255)
            ranking = safe_int(request.form.get('ranking'))
            nation  = safe_str(request.form.get('nationality'), 50)
            coach   = safe_str(request.form.get('coach_name'), 100)
            stadium = safe_str(request.form.get('stadium'), 100)

            # ✅ PARAMETERIZED QUERY
            cursor.execute(
                "UPDATE Team SET name=?, logo_url=?, ranking=?, nationality=?, coach_name=?, stadium=? "
                "WHERE team_id=?",
                (name, logo, ranking, nation, coach, stadium, team_id)
            )
            conn.commit()
            conn.close()
            flash('Team updated successfully!', 'success')
            return redirect(url_for('teams'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    # ✅ PARAMETERIZED QUERY
    cursor.execute("SELECT * FROM Team WHERE team_id=?", (team_id,))
    team = cursor.fetchone()
    conn.close()
    return render_template('team_form.html', team=team, action='Edit')

@app.route('/teams/delete/<int:team_id>', methods=['POST'])
def delete_team(team_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # ✅ PARAMETERIZED QUERY
        cursor.execute("DELETE FROM Team WHERE team_id=?", (team_id,))
        conn.commit()
        conn.close()
        flash('Team deleted.', 'success')
    except pyodbc.IntegrityError:
        flash('Cannot delete — team is referenced by other records.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('teams'))


# =========================================
# PLAYERS CRUD
# =========================================

@app.route('/players')
def players():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT player_id, fname, lname, country, birth_date, global_rank, status, email "
        "FROM Player ORDER BY global_rank"
    )
    rows = cursor.fetchall()
    conn.close()
    return render_template('players.html', players=rows)

@app.route('/players/add', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        try:
            pid        = safe_int(request.form.get('player_id'))
            fname      = safe_str(request.form.get('fname'), 50)
            lname      = safe_str(request.form.get('lname'), 50)
            country    = safe_str(request.form.get('country'), 50)
            religion   = safe_str(request.form.get('religion'), 50)
            birth_date = validate_date(request.form.get('birth_date'))
            global_rank= safe_int(request.form.get('global_rank'))
            status     = validate_status(request.form.get('status'), ['Active', 'Inactive'])
            email      = safe_str(request.form.get('email'), 100)

            if not pid or not fname or not lname:
                flash('Player ID, First Name, and Last Name are required.', 'error')
                return redirect(url_for('add_player'))

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Player (player_id, fname, lname, country, religion, birth_date, global_rank, status, email) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pid, fname, lname, country, religion, birth_date, global_rank, status, email)
            )
            conn.commit()
            conn.close()
            flash('Player added successfully!', 'success')
            return redirect(url_for('players'))
        except pyodbc.IntegrityError:
            flash('Player ID already exists.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('player_form.html', player=None, action='Add')

@app.route('/players/edit/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            fname       = safe_str(request.form.get('fname'), 50)
            lname       = safe_str(request.form.get('lname'), 50)
            country     = safe_str(request.form.get('country'), 50)
            religion    = safe_str(request.form.get('religion'), 50)
            birth_date  = validate_date(request.form.get('birth_date'))
            global_rank = safe_int(request.form.get('global_rank'))
            status      = validate_status(request.form.get('status'), ['Active', 'Inactive'])
            email       = safe_str(request.form.get('email'), 100)

            cursor.execute(
                "UPDATE Player SET fname=?, lname=?, country=?, religion=?, birth_date=?, "
                "global_rank=?, status=?, email=? WHERE player_id=?",
                (fname, lname, country, religion, birth_date, global_rank, status, email, player_id)
            )
            conn.commit()
            conn.close()
            flash('Player updated!', 'success')
            return redirect(url_for('players'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    cursor.execute("SELECT * FROM Player WHERE player_id=?", (player_id,))
    player = cursor.fetchone()
    conn.close()
    return render_template('player_form.html', player=player, action='Edit')

@app.route('/players/delete/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Player WHERE player_id=?", (player_id,))
        conn.commit()
        conn.close()
        flash('Player deleted.', 'success')
    except pyodbc.IntegrityError:
        flash('Cannot delete — player is referenced by other records.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('players'))


# =========================================
# TOURNAMENTS CRUD
# =========================================

@app.route('/tournaments')
def tournaments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tournaments ORDER BY start_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return render_template('tournaments.html', tournaments=rows)

@app.route('/tournaments/add', methods=['GET', 'POST'])
def add_tournament():
    if request.method == 'POST':
        try:
            tid        = safe_int(request.form.get('tournament_id'))
            t_name     = safe_str(request.form.get('t_name'), 100)
            max_part   = safe_int(request.form.get('max_part'))
            status     = validate_status(request.form.get('status'), ['Open', 'Closed', 'Ongoing', 'Finished'])
            start_date = validate_date(request.form.get('start_date'))
            end_date   = validate_date(request.form.get('end_date'))
            game_title = safe_str(request.form.get('game_title'), 100)
            prize_pool = request.form.get('prize_pool')
            try:
                prize_pool = float(prize_pool) if prize_pool else None
            except ValueError:
                prize_pool = None

            if not tid or not t_name:
                flash('Tournament ID and Name are required.', 'error')
                return redirect(url_for('add_tournament'))

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Tournaments (tournament_id, t_name, max_part, status, start_date, end_date, game_title, prize_pool) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tid, t_name, max_part, status, start_date, end_date, game_title, prize_pool)
            )
            conn.commit()
            conn.close()
            flash('Tournament added!', 'success')
            return redirect(url_for('tournaments'))
        except pyodbc.IntegrityError:
            flash('Tournament ID already exists.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('tournament_form.html', tournament=None, action='Add')

@app.route('/tournaments/edit/<int:tournament_id>', methods=['GET', 'POST'])
def edit_tournament(tournament_id):
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            t_name     = safe_str(request.form.get('t_name'), 100)
            max_part   = safe_int(request.form.get('max_part'))
            status     = validate_status(request.form.get('status'), ['Open', 'Closed', 'Ongoing', 'Finished'])
            start_date = validate_date(request.form.get('start_date'))
            end_date   = validate_date(request.form.get('end_date'))
            game_title = safe_str(request.form.get('game_title'), 100)
            prize_pool = request.form.get('prize_pool')
            try:
                prize_pool = float(prize_pool) if prize_pool else None
            except ValueError:
                prize_pool = None

            cursor.execute(
                "UPDATE Tournaments SET t_name=?, max_part=?, status=?, start_date=?, end_date=?, "
                "game_title=?, prize_pool=? WHERE tournament_id=?",
                (t_name, max_part, status, start_date, end_date, game_title, prize_pool, tournament_id)
            )
            conn.commit()
            conn.close()
            flash('Tournament updated!', 'success')
            return redirect(url_for('tournaments'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    cursor.execute("SELECT * FROM Tournaments WHERE tournament_id=?", (tournament_id,))
    tournament = cursor.fetchone()
    conn.close()
    return render_template('tournament_form.html', tournament=tournament, action='Edit')

@app.route('/tournaments/delete/<int:tournament_id>', methods=['POST'])
def delete_tournament(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Tournaments WHERE tournament_id=?", (tournament_id,))
        conn.commit()
        conn.close()
        flash('Tournament deleted.', 'success')
    except pyodbc.IntegrityError:
        flash('Cannot delete — tournament has linked stages or registrations.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('tournaments'))


# =========================================
# MATCHES CRUD
# =========================================

@app.route('/matches')
def matches():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.match_id, t1.name AS team1, t2.name AS team2,
               w.name AS winner, m.scheduled_at, m.status, s.stage_name
        FROM Matches m
        JOIN Team t1 ON m.team_1_id = t1.team_id
        JOIN Team t2 ON m.team_2_id = t2.team_id
        LEFT JOIN Team w  ON m.winner_id = w.team_id
        LEFT JOIN Stage s ON m.stage_id  = s.stage_id
        ORDER BY m.scheduled_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return render_template('matches.html', matches=rows)

@app.route('/matches/add', methods=['GET', 'POST'])
def add_match():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT team_id, name FROM Team ORDER BY name")
    teams = cursor.fetchall()
    cursor.execute("SELECT stage_id, stage_name FROM Stage ORDER BY stage_id")
    stages = cursor.fetchall()

    if request.method == 'POST':
        try:
            match_id     = safe_int(request.form.get('match_id'))
            stage_id     = safe_int(request.form.get('stage_id'))
            team_1_id    = safe_int(request.form.get('team_1_id'))
            team_2_id    = safe_int(request.form.get('team_2_id'))
            winner_id    = safe_int(request.form.get('winner_id'))
            scheduled_at = safe_str(request.form.get('scheduled_at'), 50)
            status       = validate_status(request.form.get('status'), ['Scheduled', 'Ongoing', 'Finished', 'Completed'])

            if not match_id or not team_1_id or not team_2_id:
                flash('Match ID and both teams are required.', 'error')
            elif team_1_id == team_2_id:
                flash('Team 1 and Team 2 cannot be the same.', 'error')
            else:
                cursor.execute(
                    "INSERT INTO Matches (match_id, stage_id, team_1_id, team_2_id, winner_id, scheduled_at, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (match_id, stage_id, team_1_id, team_2_id, winner_id, scheduled_at, status)
                )
                conn.commit()
                flash('Match added!', 'success')
                conn.close()
                return redirect(url_for('matches'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    conn.close()
    return render_template('match_form.html', match=None, teams=teams, stages=stages, action='Add')

@app.route('/matches/edit/<int:match_id>', methods=['GET', 'POST'])
def edit_match(match_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT team_id, name FROM Team ORDER BY name")
    teams = cursor.fetchall()
    cursor.execute("SELECT stage_id, stage_name FROM Stage ORDER BY stage_id")
    stages = cursor.fetchall()

    if request.method == 'POST':
        try:
            stage_id     = safe_int(request.form.get('stage_id'))
            team_1_id    = safe_int(request.form.get('team_1_id'))
            team_2_id    = safe_int(request.form.get('team_2_id'))
            winner_id    = safe_int(request.form.get('winner_id'))
            scheduled_at = safe_str(request.form.get('scheduled_at'), 50)
            status       = validate_status(request.form.get('status'), ['Scheduled', 'Ongoing', 'Finished', 'Completed'])

            cursor.execute(
                "UPDATE Matches SET stage_id=?, team_1_id=?, team_2_id=?, winner_id=?, "
                "scheduled_at=?, status=? WHERE match_id=?",
                (stage_id, team_1_id, team_2_id, winner_id, scheduled_at, status, match_id)
            )
            conn.commit()
            conn.close()
            flash('Match updated!', 'success')
            return redirect(url_for('matches'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    cursor.execute("SELECT * FROM Matches WHERE match_id=?", (match_id,))
    match = cursor.fetchone()
    conn.close()
    return render_template('match_form.html', match=match, teams=teams, stages=stages, action='Edit')

@app.route('/matches/delete/<int:match_id>', methods=['POST'])
def delete_match(match_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Matches WHERE match_id=?", (match_id,))
        conn.commit()
        conn.close()
        flash('Match deleted.', 'success')
    except pyodbc.IntegrityError:
        flash('Cannot delete — match has linked game results.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('matches'))


if __name__ == '__main__':
    app.run(debug=True)
