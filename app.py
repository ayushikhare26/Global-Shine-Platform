import os
import sqlite3
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, jsonify, flash, send_from_directory, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'global_shine_secret_key_2026_super_secure'

DB_FILE = os.path.join(os.path.dirname(__file__), 'database.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE SETUP ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table (Super Admin, Admin, Team Member, Partner, Client User)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        role TEXT NOT NULL, -- admin, team, partner, client
        designation TEXT,
        employee_id TEXT UNIQUE,
        photo_url TEXT DEFAULT '/static/images/default_user.png',
        joining_date TEXT,
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Clients Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        mobile TEXT,
        whatsapp TEXT,
        email TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        gst_number TEXT,
        website TEXT,
        assigned_team_id INTEGER,
        assigned_partner_id INTEGER,
        project_cost REAL DEFAULT 0.0,
        amount_received REAL DEFAULT 0.0,
        balance_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Leads CRM Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_name TEXT NOT NULL,
        company TEXT,
        contact_person TEXT,
        mobile TEXT,
        whatsapp TEXT,
        email TEXT,
        address TEXT,
        requirement TEXT,
        service_required TEXT,
        lead_source TEXT,
        assigned_team_id INTEGER,
        assigned_partner_id INTEGER,
        status TEXT DEFAULT 'New', -- New, Discussion, Requirement, Quotation, Won, Lost
        follow_up_date TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Lead Followups History
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lead_followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        follow_up_date TEXT,
        notes TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Projects Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        project_name TEXT NOT NULL,
        service_category TEXT,
        project_value REAL DEFAULT 0.0,
        advance_received REAL DEFAULT 0.0,
        total_received REAL DEFAULT 0.0,
        balance_due REAL DEFAULT 0.0,
        stage TEXT DEFAULT 'Requirement', -- Lead, Discussion, Requirement, Quotation, Advance, Design, Development, Testing, Client Review, Modification, Final Approval, Deployment, Completed
        status TEXT DEFAULT 'In Progress',
        assigned_partner_id INTEGER,
        assigned_team_id INTEGER,
        deadline TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Project Tasks Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        title TEXT NOT NULL,
        assigned_to_id INTEGER,
        start_date TEXT,
        deadline TEXT,
        priority TEXT DEFAULT 'Medium', -- Low, Medium, High, Urgent
        status TEXT DEFAULT 'Pending', -- Pending, In Progress, Submitted, Approved, Completed
        remarks TEXT,
        proof_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Financial & Incentive Tracking Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incentives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        user_id INTEGER NOT NULL,
        user_role TEXT NOT NULL, -- team, partner
        amount_earned REAL DEFAULT 0.0,
        amount_paid REAL DEFAULT 0.0,
        amount_pending REAL DEFAULT 0.0,
        remarks TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Document Vault Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT, -- Proposal, Quotation, Client Document, ID Proof, Code Asset, Image
        file_path TEXT NOT NULL,
        uploaded_by TEXT,
        visible_role TEXT DEFAULT 'All', -- All, Admin, Team, Partner, Client
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 10 Indian Clients Testimonials Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS testimonials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        designation TEXT NOT NULL,
        organization TEXT NOT NULL,
        location TEXT,
        headline TEXT NOT NULL,
        review_text TEXT NOT NULL,
        rating INTEGER DEFAULT 5,
        photo_url TEXT,
        service_provided TEXT
    )
    ''')

    # Contact Enquiries
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT NOT NULL,
        service TEXT,
        message TEXT,
        status TEXT DEFAULT 'New',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Seed Default Admin Account if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash('admin123')
        cursor.execute('''
        INSERT INTO users (username, password_hash, name, email, phone, role, designation, employee_id, joining_date)
        VALUES ('admin', ?, 'Nishant Chaturvedi', 'globalshinedigitals@gmail.com', '+919005874417', 'admin', 'Director', 'GS-DIR-001', '2020-01-01')
        ''', (admin_pass,))

    # Seed Default Team Member Account if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'team1'")
    if not cursor.fetchone():
        team_pass = generate_password_hash('team123')
        cursor.execute('''
        INSERT INTO users (username, password_hash, name, email, phone, role, designation, employee_id, joining_date)
        VALUES ('team1', ?, 'Amit Verma', 'amit.team@globalshine.in', '+919876543210', 'team', 'Senior Lead Engineer', 'GS-ENG-101', '2022-03-15')
        ''', (team_pass,))

    # Seed Default Partner Account if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'partner1'")
    if not cursor.fetchone():
        partner_pass = generate_password_hash('partner123')
        cursor.execute('''
        INSERT INTO users (username, password_hash, name, email, phone, role, designation, employee_id, joining_date)
        VALUES ('partner1', ?, 'Abhishek Chaturvedi', 'abhishek@globalshine.in', '+919104313824', 'partner', 'Digital Business Strategist', 'GS-PTR-201', '2021-06-10')
        ''', (partner_pass,))

    # Seed the 10 Indian Clients Testimonials if empty
    cursor.execute("SELECT COUNT(*) as count FROM testimonials")
    if cursor.fetchone()['count'] == 0:
        seed_testimonials = [
            (
                "Dr. Abhay Mishra",
                "Dermatologist",
                "Vimla Skin Clinic",
                "Jalaun, Uttar Pradesh",
                "A Complete Digital Transformation for a Modern Healthcare Brand.",
                "Global Shine Digital Solutions completely transformed the digital presence of Vimla Skin Clinic. Their team engineered a seamless patient engagement website, online branding, and custom appointment management setup. Highly professional IT partners!",
                5,
                "/static/images/clients/dr_abhay_mishra.jpg",
                "Healthcare Web Portal & Patient Engagement System"
            ),
            (
                "Dr. Ajay Shrivastava",
                "MD Chest Physician & DM Cardiologist",
                "Aadityam Chest & Dietary Centre Hospital",
                "Gorakhpur, Uttar Pradesh",
                "Exceptional Hospital Management Software & Digital Engineering.",
                "Global Shine built our enterprise hospital management portal with outstanding speed and security. Their technical depth in custom healthcare software is truly top-tier.",
                5,
                "/static/images/clients/dr_ajay_shrivastava.jpg",
                "Hospital Management System & Enterprise Web"
            ),
            (
                "Dr. Sarvendra Vikram Singh",
                "MD Chest Physician",
                "Medical Clinic",
                "Kushinagar, Uttar Pradesh",
                "Reliable IT Solutions & Custom Software Architecture.",
                "The team at Global Shine delivered a robust, secure, and fast patient portal tailored precisely to our requirements. Excellent support and flawless execution.",
                5,
                "/static/images/clients/dr_sarvendra_singh.jpg",
                "Custom Medical Software & SEO Setup"
            ),
            (
                "Mr. Kunal Shrivastava",
                "Founder & Managing Director",
                "Chai Chaska (Chai & Samosa Co.)",
                "Paalm Paradise, Gorakhpur",
                "Streamlined POS & Billing Automation for Multi-Outlet Retail.",
                "Global Shine's billing & POS automation system transformed our daily sales tracking across outlets. Their IT solutions are fast, modern, and user-friendly.",
                5,
                "/static/images/clients/mr_kunal_shrivastava.jpg",
                "Custom POS, Billing Software & Brand Web App"
            ),
            (
                "Khushi Verma",
                "Entrepreneur & Founder",
                "Food Paradise",
                "Paalm Paradise, Gorakhpur",
                "Modern E-Commerce & Interactive Digital Experience.",
                "Global Shine created an extraordinary online food ordering web app for Food Paradise. The user experience is lightning fast and our order volume increased significantly!",
                5,
                "/static/images/clients/khushi_verma.jpg",
                "Web Application & E-Commerce Platform"
            ),
            (
                "Mr. Manish Pathak",
                "Entrepreneur & Business Owner",
                "Pathak Enterprises",
                "Gorakhpur, Uttar Pradesh",
                "Top-Grade Enterprise ERP & Business Automation.",
                "Working with Global Shine was a game changer for our operations. They digitized our inventory, invoicing, and reporting into a unified cloud portal.",
                5,
                "/static/images/clients/mr_manish_pathak.jpg",
                "Business Management & ERP Software"
            ),
            (
                "Mr. Durgesh Dubey",
                "Entrepreneur & Tech Partner",
                "Dubey Commercial Services",
                "Gorakhpur, Uttar Pradesh",
                "High Performance Cloud Infrastructure & Custom Apps.",
                "Global Shine brings international-level engineering standards. Their custom web solutions and API integrations are reliable, secure, and scalable.",
                5,
                "/static/images/clients/mr_durgesh_dubey.jpg",
                "Cloud API Development & Corporate Web App"
            ),
            (
                "Sharda Devi Memorial College",
                "Management Board",
                "Sharda Devi Memorial College",
                "Uttar Pradesh",
                "Comprehensive College ERP & Student Management Portal.",
                "Global Shine developed a complete campus ERP system covering admissions, fee management, student records, and exam portals. Outstanding technical capability!",
                5,
                "/static/images/clients/sharda_devi_college.jpg",
                "College ERP & Campus Portal Development"
            ),
            (
                "Mr. Sanjeev Singh",
                "Advocate & Legal Managing Director",
                "VRSS Management Services",
                "Uttar Pradesh",
                "Secure Legal Management & Client Communication Platform.",
                "Global Shine developed our corporate web ecosystem with strict data privacy and seamless document handling. Their team is dedicated, punctual, and highly skilled.",
                5,
                "/static/images/clients/mr_sanjeev_singh.jpg",
                "Corporate Portal & Document Management System"
            ),
            (
                "Shri Siddhi Vinayak Enterprises",
                "Corporate Management",
                "Shri Siddhi Vinayak Enterprises",
                "New Delhi",
                "Scalable Enterprise Software & National Web Presence.",
                "Global Shine engineered our multi-branch inventory and client portal seamlessly. Their technical support and post-deployment service are unmatched.",
                5,
                "/static/images/clients/siddhi_vinayak_enterprises.jpg",
                "Custom Enterprise Software & Billing Solutions"
            )
        ]
        cursor.executemany('''
        INSERT INTO testimonials (client_name, designation, organization, location, headline, review_text, rating, photo_url, service_provided)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', seed_testimonials)

    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

# --- AUTH DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access the portal.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') not in roles and 'admin' not in roles:
                flash('Unauthorized access to this portal.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- PUBLIC ROUTES ---
@app.route('/')
def home():
    conn = get_db()
    testimonials = conn.execute("SELECT * FROM testimonials").fetchall()
    conn.close()
    return render_template('index.html', testimonials=testimonials)

@app.route('/enquire', methods=['POST'])
def enquire():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    service = request.form.get('service')
    message = request.form.get('message')

    if name and phone:
        conn = get_db()
        conn.execute('''
        INSERT INTO enquiries (name, email, phone, service, message)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, email, phone, service, message))
        
        # Also auto-create a lead in CRM!
        conn.execute('''
        INSERT INTO leads (lead_name, company, contact_person, mobile, email, requirement, service_required, lead_source, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Website Form', 'New')
        ''', (name, name + " (Enquiry)", name, phone, email, message, service))
        
        conn.commit()
        conn.close()
        flash('Thank you! Your enquiry has been received. Our senior engineer will contact you shortly.', 'success')
    else:
        flash('Please fill in your name and phone number.', 'danger')
    return redirect(url_for('home') + '#contact')

# --- SEO ROUTES ---
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': url_for('home', _external=True), 'changefreq': 'weekly', 'priority': '1.0'},
        {'loc': url_for('login', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
    ]
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        xml_content += f"  <url>\n    <loc>{page['loc']}</loc>\n    <changefreq>{page['changefreq']}</changefreq>\n    <priority>{page['priority']}</priority>\n  </url>\n"
    xml_content += '</urlset>'
    return Response(xml_content, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    content = "User-agent: *\nDisallow: /admin/\nDisallow: /team/\nDisallow: /partner/\nDisallow: /client/\nSitemap: " + url_for('sitemap', _external=True)
    return Response(content, mimetype='text/plain')

# --- LOGIN & AUTHENTICATION ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']

            flash(f"Welcome back, {user['name']}!", "success")
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'team':
                return redirect(url_for('team_dashboard'))
            elif user['role'] == 'partner':
                return redirect(url_for('partner_dashboard'))
            else:
                return redirect(url_for('client_dashboard'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for('login'))

# --- ADMIN DASHBOARD ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    clients = conn.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
    leads = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    projects = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    incentives = conn.execute("SELECT i.*, u.name as user_name FROM incentives i JOIN users u ON i.user_id = u.id ORDER BY i.id DESC").fetchall()
    documents = conn.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    enquiries = conn.execute("SELECT * FROM enquiries ORDER BY id DESC").fetchall()
    
    # Financial Summaries
    total_project_val = conn.execute("SELECT SUM(project_value) FROM projects").fetchone()[0] or 0.0
    total_received = conn.execute("SELECT SUM(total_received) FROM projects").fetchone()[0] or 0.0
    total_balance = conn.execute("SELECT SUM(balance_due) FROM projects").fetchone()[0] or 0.0

    conn.close()
    return render_template(
        'admin_dashboard.html',
        users=users, clients=clients, leads=leads, 
        projects=projects, tasks=tasks, incentives=incentives,
        documents=documents, enquiries=enquiries,
        total_project_val=total_project_val, total_received=total_received, total_balance=total_balance
    )

# --- ADMIN ACTIONS (ADD USER, CLIENT, LEAD, PROJECT, TASK, INCENTIVE) ---
@app.route('/admin/add-user', methods=['POST'])
@login_required
def add_user():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    role = request.form.get('role')
    designation = request.form.get('designation')
    employee_id = request.form.get('employee_id')
    joining_date = request.form.get('joining_date')

    pwd_hash = generate_password_hash(password)

    conn = get_db()
    try:
        conn.execute('''
        INSERT INTO users (username, password_hash, name, email, phone, role, designation, employee_id, joining_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, pwd_hash, name, email, phone, role, designation, employee_id, joining_date))
        conn.commit()
        flash(f"User {name} created successfully!", "success")
    except sqlite3.IntegrityError:
        flash("Username or Employee ID already exists.", "danger")
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-client', methods=['POST'])
@login_required
def add_client():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    company_name = request.form.get('company_name')
    contact_person = request.form.get('contact_person')
    mobile = request.form.get('mobile')
    whatsapp = request.form.get('whatsapp')
    email = request.form.get('email')
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state')
    gst_number = request.form.get('gst_number')
    project_cost = float(request.form.get('project_cost') or 0.0)
    amount_received = float(request.form.get('amount_received') or 0.0)
    balance_amount = project_cost - amount_received

    conn = get_db()
    conn.execute('''
    INSERT INTO clients (company_name, contact_person, mobile, whatsapp, email, address, city, state, gst_number, project_cost, amount_received, balance_amount)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (company_name, contact_person, mobile, whatsapp, email, address, city, state, gst_number, project_cost, amount_received, balance_amount))
    conn.commit()
    conn.close()

    flash(f"Client {company_name} added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-lead', methods=['POST'])
@login_required
def add_lead():
    lead_name = request.form.get('lead_name')
    company = request.form.get('company')
    contact_person = request.form.get('contact_person')
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    service_required = request.form.get('service_required')
    assigned_team_id = request.form.get('assigned_team_id') or None
    assigned_partner_id = request.form.get('assigned_partner_id') or None
    follow_up_date = request.form.get('follow_up_date')
    notes = request.form.get('notes')

    conn = get_db()
    conn.execute('''
    INSERT INTO leads (lead_name, company, contact_person, mobile, email, service_required, assigned_team_id, assigned_partner_id, follow_up_date, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (lead_name, company, contact_person, mobile, email, service_required, assigned_team_id, assigned_partner_id, follow_up_date, notes))
    conn.commit()
    conn.close()

    flash("Lead created successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-lead', methods=['POST'])
@login_required
def update_lead():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    lead_id = request.form.get('lead_id')
    status = request.form.get('status')
    assigned_team_id = request.form.get('assigned_team_id') or None
    assigned_partner_id = request.form.get('assigned_partner_id') or None
    
    conn = get_db()
    conn.execute('''
    UPDATE leads SET status = ?, assigned_team_id = ?, assigned_partner_id = ? WHERE id = ?
    ''', (status, assigned_team_id, assigned_partner_id, lead_id))
    conn.commit()
    conn.close()
    flash("Lead updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-lead/<int:lead_id>')
@login_required
def delete_lead(lead_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    flash("Lead removed.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-project', methods=['POST'])
@login_required
def add_project():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    project_name = request.form.get('project_name')
    client_id = request.form.get('client_id') or None
    service_category = request.form.get('service_category')
    project_value = float(request.form.get('project_value') or 0.0)
    advance_received = float(request.form.get('advance_received') or 0.0)
    balance_due = project_value - advance_received
    stage = request.form.get('stage') or 'Requirement'
    deadline = request.form.get('deadline')

    conn = get_db()
    conn.execute('''
    INSERT INTO projects (project_name, client_id, service_category, project_value, advance_received, total_received, balance_due, stage, deadline)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (project_name, client_id, service_category, project_value, advance_received, advance_received, balance_due, stage, deadline))
    conn.commit()
    conn.close()

    flash(f"Project '{project_name}' created successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-task', methods=['POST'])
@login_required
def add_task():
    project_id = request.form.get('project_id')
    title = request.form.get('title')
    assigned_to_id = request.form.get('assigned_to_id')
    deadline = request.form.get('deadline')
    priority = request.form.get('priority') or 'Medium'

    conn = get_db()
    conn.execute('''
    INSERT INTO tasks (project_id, title, assigned_to_id, deadline, priority)
    VALUES (?, ?, ?, ?, ?)
    ''', (project_id, title, assigned_to_id, deadline, priority))
    conn.commit()
    conn.close()

    flash("Task assigned successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-incentive', methods=['POST'])
@login_required
def add_incentive():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    project_id = request.form.get('project_id')
    user_id = request.form.get('user_id')
    user_role = request.form.get('user_role')
    amount_earned = float(request.form.get('amount_earned') or 0.0)
    amount_paid = float(request.form.get('amount_paid') or 0.0)
    amount_pending = amount_earned - amount_paid
    remarks = request.form.get('remarks')

    conn = get_db()
    conn.execute('''
    INSERT INTO incentives (project_id, user_id, user_role, amount_earned, amount_paid, amount_pending, remarks)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (project_id, user_id, user_role, amount_earned, amount_paid, amount_pending, remarks))
    conn.commit()
    conn.close()

    flash("Incentive record logged successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# --- DIGITAL ID CARD VIEW ROUTE ---
@app.route('/id-card/<int:user_id>')
@login_required
def view_id_card(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    return render_template('id_card.html', user=user)

# --- TEAM DASHBOARD ---
@app.route('/team/dashboard')
@login_required
def team_dashboard():
    if session.get('role') not in ['team', 'admin']:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    my_tasks = conn.execute("SELECT t.*, p.project_name FROM tasks t LEFT JOIN projects p ON t.project_id = p.id WHERE t.assigned_to_id = ? ORDER BY t.id DESC", (user_id,)).fetchall()
    my_leads = conn.execute("SELECT * FROM leads WHERE assigned_team_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    my_incentives = conn.execute("SELECT * FROM incentives WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    documents = conn.execute("SELECT * FROM documents WHERE visible_role IN ('All', 'Team') ORDER BY id DESC").fetchall()

    conn.close()
    return render_template('team_dashboard.html', user=user, my_tasks=my_tasks, my_leads=my_leads, my_incentives=my_incentives, documents=documents)

# --- PARTNER DASHBOARD ---
@app.route('/partner/dashboard')
@login_required
def partner_dashboard():
    if session.get('role') not in ['partner', 'admin']:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    my_leads = conn.execute("SELECT * FROM leads WHERE assigned_partner_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    my_clients = conn.execute("SELECT * FROM clients WHERE assigned_partner_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    my_incentives = conn.execute("SELECT * FROM incentives WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    documents = conn.execute("SELECT * FROM documents WHERE visible_role IN ('All', 'Partner') ORDER BY id DESC").fetchall()

    conn.close()
    return render_template('partner_dashboard.html', user=user, my_leads=my_leads, my_clients=my_clients, my_incentives=my_incentives, documents=documents)

# --- CLIENT DASHBOARD ---
@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if session.get('role') not in ['client', 'admin']:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    # Match client by email or phone
    client_info = conn.execute("SELECT * FROM clients WHERE email = ? OR mobile = ?", (user['email'], user['phone'])).fetchone()
    projects = []
    if client_info:
        projects = conn.execute("SELECT * FROM projects WHERE client_id = ?", (client_info['id'],)).fetchall()

    conn.close()
    return render_template('client_dashboard.html', user=user, client_info=client_info, projects=projects)

# --- DOCUMENT UPLOAD ROUTE ---
@app.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    title = request.form.get('title')
    category = request.form.get('category')
    visible_role = request.form.get('visible_role') or 'All'
    file = request.files.get('file')

    if file and title:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        saved_filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)

        web_path = f"/static/uploads/{saved_filename}"

        conn = get_db()
        conn.execute('''
        INSERT INTO documents (title, category, file_path, uploaded_by, visible_role)
        VALUES (?, ?, ?, ?, ?)
        ''', (title, category, web_path, session.get('name'), visible_role))
        conn.commit()
        conn.close()

        flash("Document uploaded successfully!", "success")
    else:
        flash("Please specify a title and select a file.", "danger")

    return redirect(request.referrer or url_for('admin_dashboard'))

# --- TASK UPDATE ROUTE ---
@app.route('/update-task-status', methods=['POST'])
@login_required
def update_task_status():
    task_id = request.form.get('task_id')
    status = request.form.get('status')
    remarks = request.form.get('remarks')

    conn = get_db()
    conn.execute('''
    UPDATE tasks SET status = ?, remarks = ? WHERE id = ?
    ''', (status, remarks, task_id))
    conn.commit()
    conn.close()

    flash("Task updated!", "success")
    return redirect(request.referrer or url_for('team_dashboard'))

if __name__ == '__main__':
    print("Starting Global Shine Digital Platform on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
