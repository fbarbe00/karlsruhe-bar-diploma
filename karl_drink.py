from flask import Flask, render_template, session, request, redirect, url_for
import json
import os
import datetime
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'static')

# yay, security
USER_PASSWORD = "CHANGEME"
ADMIN_PASSWORD = "REALLYCHANGEME"

USERS_PATH = os.path.join(APP_STATIC, 'users.json')
DRINKS_PATH = os.path.join(APP_STATIC, 'drinks.json')

TYPES = {'Bachelor': 5, 'Master': 8}

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_kartoffelsalat5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def userchoice():
    if not check_login():
        return redirect(url_for('login'))
    error_msg = request.args['error_msg'] if 'error_msg' in request.args else None
    users = get_users('non_archived') if 'admin' in session else get_users()
    return render_template('users.html', users=users, error_msg=error_msg, is_admin=('admin' in session))

def check_login():
    if 'username' not in session:
        return False
    return True

@app.route('/user/<smurf>')
def user(smurf):
    if not check_login():
        return redirect(url_for('login'))
    users = get_users(type='all')
    user = [u for u in users if u['name'] == smurf]
    if not user:
        return redirect(url_for('userchoice', error_msg='Benutzer nicht gefunden'))
    user = user[0]
    drinks = get_drinks()
    for i in user['ordered_drinks']:
        drinks[i]['ordered'] = True
    error_msg = request.args['error_msg'] if 'error_msg' in request.args else None
    progress = {'current': len(user['ordered_drinks']), 'total': TYPES[user['type']], "type": user['type']}
    if user['completed']:
        error_msg = "Herzlichen Glückwunsch! Sie haben jetzt einen {} Abschluss in Alkoholismus!".format(user['type'])
    return render_template('user_drinks.html', drinks=drinks, user=user, error_msg=error_msg, progress=progress)

def get_users(type='active'):
    users = json.load(open(USERS_PATH))
    if type == 'non_archived':
        return [u for u in users if 'archived' not in u.keys()]
    elif type != 'all':
        users = [u for u in users if u['completed'] == (type != 'active') and 'archived' not in u.keys()]

    return users

def get_drinks():
    drinks = json.load(open(DRINKS_PATH))
    return drinks

@app.route('/add_user', methods=['POST'])
def add_user():
    if not check_login():
        return redirect(url_for('login'))
    users = json.load(open(USERS_PATH))
    name = request.form['name']
    if name in [u['name'] for u in users]:
        return redirect(url_for('userchoice', error_msg=name +' existiert bereits'))
    users.append({
        'name': request.form['name'],
        'completed': False,
        'ordered_drinks': [],
        'type': request.form['type'],
        'last_edit': session['username'],
        'last_edit_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    json.dump(users, open(USERS_PATH, 'w'))
    return redirect(url_for('user', smurf=name))

@app.route('/add_drink/<smurf>/<drink>')
def add_drink(smurf, drink):
    if not check_login():
        return redirect(url_for('login'))
    users = json.load(open(USERS_PATH))
    user = [u for u in users if u['name'] == smurf]
    if not user:
        return redirect(url_for('userchoice', error_msg='Benutzer nicht gefunden'))
    user = user[0]
    drink = int(drink) - 1
    if drink in user['ordered_drinks']:
        return redirect(url_for('user', smurf=smurf, error_msg='Benutzer hat dieses Getränk bereits bestellt!'))
    user['ordered_drinks'].append(drink)
    if len(user['ordered_drinks']) == TYPES[user['type']]:
        # user['completed'] = True
        user['name'] = user['name'] + ' (abgeschlossen)'
    user['last_edit'] = session['username']
    user['last_edit_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    json.dump(users, open(USERS_PATH, 'w'))
    return redirect(url_for('user', smurf=user['name']))

@app.route('/finished/<smurf>')
def finished(smurf):
    if not check_login():
        return redirect(url_for('login'))
    users = json.load(open(USERS_PATH))
    user = [u for u in users if u['name'] == smurf]
    if not user:
        return redirect(url_for('userchoice', error_msg='Benutzer nicht gefunden'))
    user = user[0]
    user['completed'] = True
    user['last_edit'] = session['username']
    user['last_edit_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    json.dump(users, open(USERS_PATH, 'w'))
    return redirect(url_for('user', smurf=user['name']))

@app.route('/remove_drink/<smurf>/<drink>')
def remove_drink(smurf, drink):
    if not check_login():
        return redirect(url_for('login'))
    users = json.load(open(USERS_PATH))
    user = [u for u in users if u['name'] == smurf]
    if not user:
        return redirect(url_for('userchoice', error_msg='Benutzer nicht gefunden'))
    user = user[0]
    drink = int(drink) - 1
    if drink not in user['ordered_drinks']:
        return redirect(url_for('user', smurf=smurf, error_msg='Der Benutzer hat dieses Getränk nicht bestellt!'))
    user['ordered_drinks'].remove(drink)
    user['last_edit'] = session['username']
    user['last_edit_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    json.dump(users, open(USERS_PATH, 'w'))
    return redirect(url_for('user', smurf=smurf))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == USER_PASSWORD:
            session['username'] = request.form['username']
            return redirect(url_for('userchoice'))
        if request.form['password'] == ADMIN_PASSWORD:
            session['username'] = request.form['username']
            session['admin'] = True
            return redirect(url_for('userchoice'))
        error = 'Du Spasst! Das Passwort ist nicht korrekt.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/popular_drinks')
def popular_drinks():
    drinks = get_drinks()
    users = get_users('all')
    total = 0
    for d in drinks:
        d['count'] = 0
    for u in users:
        for i in u['ordered_drinks']:
            drinks[i]['count'] += 1
            total += 1
    max_count = max(drinks, key=lambda x: x['count'])['count']
    # sort in descending order
    drinks = sorted(drinks, key=lambda k: k['count'], reverse=True)
    return render_template('popular_drinks.html', drinks=drinks, total=max_count+1)

@app.route('/table_view')
def table_view():
    if not check_login():
        return redirect(url_for('login'))
    users = get_users('non_archived') if 'admin' in session else get_users()
    drinks = get_drinks()

    for d in drinks:
        d['count'] = 0
    for u in users:
        u['count'] = len(u['ordered_drinks'])
        for i in u['ordered_drinks']:
            drinks[i]['count'] += 1
    return render_template('table_view.html', users=users, drinks=drinks)

@app.route('/archive_losers')
def delete_losers():
    if 'admin' not in session:
        return redirect(url_for('userchoice', error_msg='Nur Admin kann diese Funktion nutzen!'))
    users = get_users('all')
    for u in users:
        if not u['completed'] and not 'archived' in u.keys():
            u['archived'] = True
            u['name'] = u['name'] + ' (archiviert)'
    json.dump(users, open(USERS_PATH, 'w'))
    return redirect(url_for('userchoice'))

@app.route('/archive_winners')
def archive_winners():
    if 'admin' not in session:
        return redirect(url_for('userchoice', error_msg='Nur Admin kann diese Funktion nutzen!'))
    users = get_users('all')
    for u in users:
        if u['completed'] and not 'archived' in u.keys():
            u['archived'] = True
            u['name'] = u['name'] + ' (archiviert)'
    json.dump(users, open(USERS_PATH, 'w'))
    return redirect(url_for('userchoice'))
