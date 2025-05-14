from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import hashlib
from db import get_db_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if 'user_id' in session:
        return render_template('home_logged_in.html')
    else:
        return render_template('home_logged_out.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        department_id = request.form.get('department_id')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO users (username, password, role, department_id) VALUES (?, ?, ?, ?)',
                (username, hashed_password, role, department_id or None)
            )
            conn.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('main.login'))
        except:
            flash('Username already exists.')
        finally:
            conn.close()
    return render_template('register.html')

@main_bp.route('/tickets/delete/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    #Checking if user is authorised to delete tickets (user must be admin)
    if 'user_id' not in session or session['role'] != 'admin':
        flash('You are not authorised to delete tickets.')
        return redirect(url_for('main.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()

    flash('Ticket deleted successfully.')
    return redirect(url_for('main.list_tickets'))

@main_bp.route('/tickets/update/<int:ticket_id>', methods=['GET', 'POST'])
def update_ticket(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
    ticket = cursor.fetchone()

    if not ticket:
        flash('Ticket not found.')
        conn.close()
        return redirect(url_for('main.list_tickets'))

    if request.method == 'POST':
        new_title = request.form['title']
        new_description = request.form['description']
        new_status = request.form['status']

        cursor.execute('''
            UPDATE tickets SET title = ?, description = ?, status = ? WHERE id = ?
        ''', (new_title, new_description, new_status, ticket_id))
        conn.commit()
        conn.close()

        flash('Ticket updated successfully.')
        return redirect(url_for('main.list_tickets'))

    conn.close()
    return render_template('update_ticket.html', ticket=ticket)

@main_bp.route('/users')
def manage_users():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access.')
        return redirect(url_for('main.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT users.id, users.username, users.role, departments.name AS department FROM users LEFT JOIN departments ON users.department_id = departments.id')
    users = cursor.fetchall()
    conn.close()

    return render_template('users.html', users=users)



@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hashed_password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash('Login successful!')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_role = session['role']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Admin can view everything
    if user_role == 'admin':
        cursor.execute('SELECT COUNT(*) FROM tickets')
        total_tickets = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
    else:
        # Regular user can only view their tickets
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE user_id = ?', (session['user_id'],))
        total_tickets = cursor.fetchone()[0]
        total_users = None

    conn.close()

    return render_template('dashboard.html', total_tickets=total_tickets, total_users=total_users, role=user_role)


@main_bp.route('/tickets')
def list_tickets():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    if session['role'] == 'admin':
        cursor.execute('SELECT * FROM tickets')
    else:
        cursor.execute('SELECT * FROM tickets WHERE user_id = ?', (session['user_id'],))
    tickets = cursor.fetchall()
    conn.close()
    return render_template('tickets.html', tickets=tickets)


@main_bp.route('/tickets/create', methods=['GET', 'POST'])
def create_ticket():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tickets (title, description, user_id) VALUES (?, ?, ?)',
            (title, description, session['user_id'])
        )
        conn.commit()
        conn.close()
        flash('Ticket created.')
        return redirect(url_for('main.list_tickets'))

    return render_template('create_ticket.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('main.home'))

