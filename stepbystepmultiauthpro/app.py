import uuid
from flask import Flask, request, render_template,jsonify, redirect, url_for, session
import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import json
import oracledb
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
import os
import fitz  
import pytesseract 
import cv2
import numpy as np
import requests
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

linkedin_api_token = "YOUR_LINKEDIN_API_ACCESS_TOKEN"
app = Flask(__name__)
app.secret_key = 'prema2'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'soulmate4yours@gmail.com'
app.config['MAIL_PASSWORD'] = 'nvupxddghoatuldw'


mail = Mail(app)


DB_DSN = 'prema2'
DB_USER = 'prema2'
DB_PASSWORD = 'prema34'

def get_db_connection():
    connection_string = f"DSN={DB_DSN};UID={DB_USER};PWD={DB_PASSWORD}"
    return pyodbc.connect(connection_string)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
from flask import Flask
from datetime import datetime



# Define a datetimeformat filter
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, datetime):
        return value.strftime(format)
    else:
        # If the value is a string or something else, try parsing or return as is
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.strftime(format)
        except Exception:
            return value

# Now your template can use {{ message.sent_at|datetimeformat }}


uploaded_files = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            age = request.form.get('age')
            gender = request.form.get('gender')
            location = request.form.get('location')
            religion = request.form.get('religion', '')  # New religion field
            
            # Validate required fields
            if not all([name, email, password, age, gender, location]):
                return jsonify({"success": False, "error": "All fields are required"}), 400
            
            # Handle profile picture upload
            profile_pic = request.files.get('profile_pic')
            filename = None
            
            if profile_pic and profile_pic.filename != '':
                if not allowed_file(profile_pic.filename):
                    return jsonify({
                        "success": False, 
                        "error": "Invalid file type. Only JPG, PNG, GIF allowed."
                    }), 400
                
                # Generate secure filename
                filename = secure_filename(f"{uuid.uuid4()}_{profile_pic.filename}")
                try:
                    profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    return jsonify({
                        "success": False, 
                        "error": f"Failed to save profile picture: {str(e)}"
                    }), 500
            
            # Hash password
            hashed_password = generate_password_hash(password)
            
            # Connect to database
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # Insert user with profile picture and religion
                cursor.execute(""" 
                    INSERT INTO users1 (
                        name, email, password, age, gender, 
                        location, religion, profile_pic
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (name, email, hashed_password, age, gender, 
                     location, religion, filename))
                
                conn.commit()

                # Get the new user ID
                cursor.execute("SELECT user_seq.CURRVAL FROM dual")
                user_id = cursor.fetchone()[0]

                # Set session variables
                session['user_id'] = user_id
                session['logged_in'] = True
                session['email'] = email
                session['name'] = name

                # Send welcome email
                msg = Message(
                    'Registration Successful',
                    sender='soulmate4yours@gmail.com',
                    recipients=[email]
                )
                msg.body = f"""Hi {name},

Welcome to our matrimony platform! Your registration was successful.

Account Details:
- Name: {name}
- Email: {email}
- Age: {age}
- Gender: {gender}
- Location: {location}
- Religion: {religion if religion else 'Not specified'}

You can now complete your profile and start finding your perfect match.

Thank you,
Matrimony Team
"""
                try:
                    mail.send(msg)
                except Exception as mail_error:
                    print(f"Mail Error: {mail_error}")
                    # Don't fail registration just because email failed

                return jsonify({
                    "success": True, 
                    "message": "Registration successful.",
                    "user_id": user_id
                })

            except pyodbc.IntegrityError as e:
                if "unique constraint" in str(e).lower():
                    return jsonify({
                        "success": False, 
                        "error": "Email already registered"
                    }), 400
                return jsonify({
                    "success": False, 
                    "error": f"Database error: {str(e)}"
                }), 500

            except Exception as e:
                conn.rollback()
                return jsonify({
                    "success": False, 
                    "error": f"An error occurred: {str(e)}"
                }), 500

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print("Error during registration:", str(e))
            return jsonify({
                "success": False, 
                "error": f"An error occurred: {str(e)}"
            }), 500

    else:
        # GET request - show registration form
        return render_template('register.html', 
            religions=['Hindu', 'Muslim', 'Christian', 'Sikh', 'Buddhist', 'Jain', 'Other'])
    


# User Login
from werkzeug.security import check_password_hash


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Extract form data
            email = request.form['email']
            password = request.form['password']

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fetch user by email
            cursor.execute("SELECT user_id, password FROM users1 WHERE email = ?", (email,))
            user = cursor.fetchone()

            if user:
                user_id, hashed_password = user
                # Check the hashed password
                if check_password_hash(hashed_password, password):
                    session['user_id'] = user_id
                    session['logged_in'] = True
                    return jsonify({"success": True})
                else:
                    return jsonify({"success": False, "error": "Invalid password"})
            else:
                return jsonify({"success": False, "error": "User not found"})

        except Exception as e:
            print("Login error:", str(e))
            return jsonify({"success": False, "error": f"An error occurred: {str(e)}"})

        finally:
            cursor.close()
            conn.close()
    
    else:
        return render_template('login.html')


# Browse Profiles (with age filter)
@app.route('/browse')
def browse():
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get filter parameters from request
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Results per page
        religion_filter = request.args.get('religion', '')
        gender_filter = request.args.get('gender', '')
        location_filter = request.args.get('location', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user's own religion for default filtering
        cursor.execute("SELECT religion FROM users1 WHERE user_id = ?", (session['user_id'],))
        user_religion_row = cursor.fetchone()
        user_religion = user_religion_row[0] if user_religion_row else None
        
        # Get user's age preferences
        cursor.execute("""
            SELECT min_age, max_age 
            FROM user_preferences 
            WHERE user_id = ?
        """, (session['user_id'],))
        pref = cursor.fetchone()
        min_age, max_age = pref if pref else (18, 60)  # Default range
        
        # Build base query
        query = """
            SELECT user_id, name, age, gender, location, profile_pic, religion, bio
            FROM users1
            WHERE age BETWEEN ? AND ?
            AND user_id != ?
            AND verified = 1  # Only show verified profiles
        """
        params = [min_age, max_age, session['user_id']]
        
        # Apply religion filter (either from user's preference or explicit filter)
        if religion_filter:
            query += " AND religion = ?"
            params.append(religion_filter)
        elif user_religion:
            query += " AND religion = ?"
            params.append(user_religion)
        
        # Apply gender filter if specified
        if gender_filter:
            query += " AND gender = ?"
            params.append(gender_filter)
        
        # Apply location filter if specified
        if location_filter:
            query += " AND location LIKE ?"
            params.append(f"%{location_filter}%")
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM (" + query + ")"
        cursor.execute(count_query, params)
        total_profiles = cursor.fetchone()[0]
        
        # Add pagination to main query
        query += " ORDER BY name OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        offset = (page - 1) * per_page
        params.extend([offset, per_page])
        
        # Execute main query
        cursor.execute(query, params)
        
        # Build profiles list
        profiles = []
        for row in cursor:
            profile = {
                'id': row[0],
                'name': row[1],
                'age': row[2],
                'gender': row[3],
                'location': row[4],
                'img': row[5] if row[5] else 'default_profile.jpg',
                'religion': row[6],
                'bio': row[7] if row[7] else 'No bio yet'
            }
            profiles.append(profile)
        
        # Get list of all religions for filter dropdown
        cursor.execute("SELECT DISTINCT religion FROM users1 WHERE religion IS NOT NULL ORDER BY religion")
        all_religions = [row[0] for row in cursor.fetchall()]
        
        # Get list of all locations for filter dropdown
        cursor.execute("SELECT DISTINCT location FROM users1 WHERE location IS NOT NULL ORDER BY location")
        all_locations = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Calculate pagination values
        total_pages = (total_profiles + per_page - 1) // per_page
        
        return render_template(
            'browse.html',
            profiles=profiles,
            religions=all_religions,
            locations=all_locations,
            current_page=page,
            total_pages=total_pages,
            religion_filter=religion_filter,
            gender_filter=gender_filter,
            location_filter=location_filter,
            min_age=min_age,
            max_age=max_age
        )
    
    except Exception as e:
        print(f"Error in browse route: {str(e)}")
        if 'conn' in locals():
            conn.close()
        flash("An error occurred while loading profiles. Please try again.", "error")
        return redirect(url_for('dashboard'))
    
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clears the session
    return jsonify({'success': True}), 200  # Returns success when logged out
def get_user_by_id(user_id):
    """Get user details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_id, name, email, age, gender, location, religion, profile_pic
            FROM users1 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'name': row[1],
                'email': row[2],
                'age': row[3],
                'gender': row[4],
                'location': row[5],
                'religion': row[6],
                'profile_pic': row[7]
                
            }
        return None
    finally:
        cursor.close()
        conn.close()

def get_recent_messages(user_id, limit=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM (
                SELECT 
                    m.message_id, 
                    m.sender_id, 
                    u.name AS sender_name,
                    m.message_text, 
                    m.is_read
                FROM messages m
                JOIN users1 u ON m.sender_id = u.user_id
                WHERE m.receiver_id = ?
                ORDER BY m.message_id DESC
            ) WHERE ROWNUM <= ?
        """, (user_id, limit))

        messages = []
        for row in cursor:
            messages.append({
                'message_id': row[0],
                'sender_id': row[1],
                'sender_name': row[2],
                'message_text': row[3],
                'is_read': bool(row[4])
            })
        return messages
    finally:
        cursor.close()
        conn.close()
def get_user_preferences(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT min_age, max_age, religion 
            FROM user_preferences 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {'min_age': row[0], 'max_age': row[1], 'religion': row[2]}
        else:
            return {'min_age': 18, 'max_age': 60, 'religion': ''}
    finally:
        cursor.close()
        conn.close()

def get_recent_contacts(user_id, limit=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM (
                SELECT 
                    u.user_id, u.name, u.age, u.profile_pic, MAX(m.message_id) AS max_msg_id
                FROM users1 u
                JOIN messages m 
                  ON (m.sender_id = u.user_id OR m.receiver_id = u.user_id)
                WHERE 
                    (m.sender_id = ? OR m.receiver_id = ?)
                    AND u.user_id != ?
                GROUP BY u.user_id, u.name, u.age, u.profile_pic
                ORDER BY max_msg_id DESC
            ) WHERE ROWNUM <= ?
        """, (user_id, user_id, user_id, limit))

        contacts = []
        for row in cursor:
            contacts.append({
                'user_id': row[0],
                'name': row[1],
                'age': row[2],
                'profile_pic': row[3]
            })
        return contacts
    finally:
        cursor.close()
        conn.close()



def get_all_religions():
    """Get all distinct religions in the system"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT religion 
            FROM users1 
            WHERE religion IS NOT NULL 
            ORDER BY religion
        """)
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()
from flask import session, flash, redirect, url_for, render_template
import traceback
from flask import session, redirect, url_for, flash, render_template
import traceback

def get_user_preferences(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT min_age, max_age, religion 
            FROM user_preferences 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {'min_age': row[0], 'max_age': row[1], 'religion': row[2]}
        else:
            return {'min_age': 18, 'max_age': 60, 'religion': ''}
    finally:
        cursor.close()
        conn.close()

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        print("No user_id in session, redirecting to login")
        return redirect(url_for('login'))

    try:
        user_id = session['user_id']
        print(f"Dashboard loading for user_id: {user_id}")

        # Load current user info
        user_data = get_user_by_id(user_id)
        if not user_data:
            print("User data not found!")
            flash("User not found", "error")
            return redirect(url_for('login'))
        print("User data loaded")

        # Load preferences as a dictionary
        preferences = get_user_preferences(user_id)
        print("User preferences loaded:", preferences)

        messages = get_recent_messages(user_id)
        print("Messages loaded:", len(messages))

        contacts = get_recent_contacts(user_id)
        print("Contacts loaded:", len(contacts))

        religions = get_all_religions()
        print("Religions loaded:", religions)

        # Query matched profiles directly using SQL
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT user_id, name, age, religion, location, profile_pic
FROM users1
WHERE age BETWEEN ? AND ?
  AND (? = '' OR religion = ?)
  AND gender = ?
  AND user_id != ?


        """
                # Determine opposite gender
        user_gender = user_data.get('gender', '').strip().capitalize()

        if user_gender == 'Female':
            opposite_gender = 'Male'
        elif user_gender == 'Male':
            opposite_gender = 'Female'
        else:
            opposite_gender = ''  # No filtering for 'Other'



        params = [
    preferences['min_age'],
    preferences['max_age'],
    preferences['religion'],
    preferences['religion'],
    opposite_gender,
    user_id
]



        def safe_str(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8')
                except UnicodeDecodeError:
                    return "<invalid data>"
            return val

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        matched_profiles = []
        for row in rows:
            matched_profiles.append({
                'user_id': row[0],
                'name': safe_str(row[1]),
                'age': row[2],
                'religion': safe_str(row[3]),
                'location': safe_str(row[4]),
                'profile_pic': safe_str(row[5])  # If this is a string (e.g., image URL/path)
            })

        cursor.close()
        conn.close()

        print("Matched profiles loaded:", len(matched_profiles))

        return render_template('dashboard.html',
                               user_data=user_data,
                               preferences=preferences,
                               messages=messages,
                               recent_contacts=contacts,
                               all_religions=religions,
                               matched_profiles=matched_profiles)

    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()
        flash("An error occurred while loading your dashboard", "error")
        return redirect(url_for('home'))
@app.route('/featured_profiles')
def featured_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, age, gender, location, profile_pic
            FROM users1
        """)
        rows = cursor.fetchall()
        profiles = []

        for row in rows:
            profiles.append({
                'id': row[0],
                'name': row[1],
                'age': row[2],
                'gender': row[3],
                'location': row[4],
                'img': f"/static/uploads/{row[5]}" if row[5] else "/static/images/default.jpg"
            })

        cursor.close()
        conn.close()

        return jsonify(profiles)

    except Exception as e:
        print("Error fetching featured profiles:", e)
        return jsonify([]), 500



@app.route('/api/user')
def get_user_data():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, location FROM users1 WHERE user_id = ?", (session['user_id'],))
        row = cursor.fetchone()
        if row:
            name, age, location = row
            return jsonify({"name": name, "age": age, "location": location})
        else:
            return jsonify({"error": "User not found"}), 404
    finally:
        cursor.close()
        conn.close()

@app.route('/get_profile_details')
def get_profile_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({"error": "User ID missing"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT name, email, age, gender, location, religion
            FROM users1
            WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "User not found"}), 404

        profile_details = {
            "name": row[0],
            "email": row[1],
            "age": row[2],
            "gender": row[3],
            "location": row[4],
            "religion": row[5] or 'Not specified',
        }
        return jsonify(profile_details)

    except Exception as e:
        # Print full error to console for debugging
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, age, gender, location, religion, profile_pic 
            FROM users1 
            WHERE id = :id
        """, id=user_id)

        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "User not found"}), 404

        profile = {
            "name": row[0],
            "age": row[1],
            "gender": row[2],
            "location": row[3],
            "religion": row[4],
            "img": url_for('static', filename='uploads/' + row[5]) if row[5] else url_for('static', filename='images/default_profile.jpg')
        }

        return jsonify({"success": True, "profile": profile})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "document" not in request.files:
            return jsonify({"error": "No file uploaded!"}), 400

        file = request.files["document"]
        
        if file.filename == "":
            return jsonify({"error": "No selected file!"}), 400

        allowed_extensions = {"pdf", "jpg", "png"}
        file_ext = file.filename.split(".")[-1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({"error": "Invalid file type!"}), 400

        # Ensure upload folder exists
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        # Generate a unique filename
        filename = str(uuid.uuid4()) + "_" + file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        uploaded_files["latest_file"] = filename

        try:
            # Save to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert file details into the database
            # Detect if file came from reupload form (optional based on referrer or other hint)
            referrer = request.referrer or ""
            is_reupload_flag = 'true' if 'reupload' in referrer.lower() else 'false'

            cursor.execute(
                "INSERT INTO document_uploads (file_name, file_path, is_reupload) VALUES (?, ?, ?)", 
                (filename, file_path, is_reupload_flag)
)



            conn.commit()

            # Fetch the user's email from the users1 table using session's user_id
            user_id = session.get('user_id')  # Retrieve user_id from session
            if user_id:
                cursor.execute("SELECT email FROM users1 WHERE user_id = ?", (user_id,))
                user_email = cursor.fetchone()
                if user_email:
                    user_email = user_email[0]  # Extract the email from the result tuple
                else:
                    return jsonify({"error": "User not found!"}), 404
            else:
                return jsonify({"error": "User is not logged in!"}), 400

            # Send email notification
            msg = Message('Document Uploaded Successfully',
                          sender='soulmate4yours@gmail.com',
                          recipients=[user_email])
            msg.body = f"Hi,\n\nYour document '{filename}' has been successfully uploaded and is being processed."

            try:
                mail.send(msg)
            except Exception as mail_error:
                print(f"Mail Error: {mail_error}")

        except Exception as e:
            print("DB error:", str(e))
            return jsonify({"error": "Database error!"}), 500
        finally:
            conn.close()

        return jsonify({"message": "File uploaded successfully!", "file_name": filename})

    else:   
        return render_template("upload.html")




def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text


def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text


def validate_document_format(text):
    required_keywords = ["Aadhaar", "Passport", "Driving License", "Govt", "ID", "Date of Birth"]
    return any(keyword in text for keyword in required_keywords)

@app.route("/validate", methods=["POST"])
def validate_file():
    if "document" not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400

    file = request.files["document"]
    file_ext = file.filename.split(".")[-1].lower()
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    extracted_text = ""

    if file_ext == "pdf":
        extracted_text = extract_text_from_pdf(file_path)
    elif file_ext in ["jpg", "png"]:
        extracted_text = extract_text_from_image(file_path)
    else:
        return jsonify({"error": "Unsupported file format!"}), 400

    is_valid = validate_document_format(extracted_text)

  
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO document_verification (file_name, text_content, is_valid) VALUES (?, ?, ?)",
                   (file.filename, extracted_text, is_valid))
    conn.commit()
    conn.close()

    if is_valid:
        return jsonify({"message": "Document format is valid!", "text": extracted_text})
    else:
        return jsonify({"error": "Invalid document format!", "text": extracted_text})
@app.route('/details')
def details():
    connection_string = f"DSN={DB_DSN};UID={DB_USER};PWD={DB_PASSWORD}"
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

 
    cursor.execute("SELECT text_content FROM (SELECT text_content FROM document_verification ORDER BY id DESC) WHERE ROWNUM = 1")
    extracted_text = cursor.fetchone()

  
    return render_template('details.html')
@app.route("/compare", methods=["POST"])
def compare_details():
    data = request.json
    name = data.get("name")
    dob = data.get("dob")
    id_number = data.get("idNumber")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT text_content FROM (SELECT text_content FROM document_verification ORDER BY id DESC) WHERE ROWNUM = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        extracted_text = row[0]
        if name in extracted_text and dob in extracted_text and id_number in extracted_text:
            return jsonify({"success": True, "message": "Details verified successfully!"})
        else:
            return jsonify({"success": False, "error": "Mismatch found! Please check your details."})
    else:
        return jsonify({"success": False, "error": "No extracted data found!"})
@app.route("/selfie")
def selfie_page():
    return render_template("selfie.html")
@app.route('/facial_recognition', methods=['GET', 'POST'])
def facial_recognition():
    if request.method == 'POST':
        selfie = request.files['selfie']
        id_photo = request.files['id_photo']
        if selfie and id_photo:
            selfie_path = os.path.join(app.config['UPLOAD_FOLDER'], 'selfie.jpg')
            id_path = os.path.join(app.config['UPLOAD_FOLDER'], 'id.jpg')
            selfie.save(selfie_path)
            id_photo.save(id_path)

            # Load images as grayscale
            selfie_img = cv2.imread(selfie_path, cv2.IMREAD_GRAYSCALE)
            id_img = cv2.imread(id_path, cv2.IMREAD_GRAYSCALE)

            # Resize both to same size
            selfie_img = cv2.resize(selfie_img, (200, 200))
            id_img = cv2.resize(id_img, (200, 200))

            # Calculate similarity using SSIM
            score, _ = ssim(selfie_img, id_img, full=True)

            # Simulate liveness check (basic placeholder)
            is_live = True  # always True for now

            match_result = 'Match' if score > 0.6 else 'Mismatch'
            flash(f'Match Confidence Score: {round(score*100, 2)}% — Result: {match_result}', 'info')

            return redirect(url_for('facial_recognition'))

    return render_template('facial_recognition.html')


@app.route("/verify_selfie")
def verify_selfie():
    return render_template("link_linkedin.html")
@app.route("/link_linkedin", methods=["POST"])
def link_linkedin():
    linkedin_url = request.form.get('linkedin_url')
    if not linkedin_url:
        return jsonify({"error": "LinkedIn URL is required!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update LinkedIn URL in the DB
        cursor.execute("UPDATE users1 SET linkedin_url = ? WHERE user_id = ?", 
                       (linkedin_url, session['user_id']))
        conn.commit()

        # Fetch user email and name
        cursor.execute("SELECT name, email FROM users1 WHERE user_id = ?", (session['user_id'],))
        user = cursor.fetchone()
        user_name, user_email = user[0], user[1]

        # Send email notification
        msg = Message('LinkedIn Profile Linked',
                      sender='soulmatenevermate@gmail.com',
                      recipients=[user_email])
        msg.body = f"Hi {user_name},\n\nYour LinkedIn profile has been successfully linked to your account."

        try:
            mail.send(msg)
        except Exception as mail_error:
            print(f"Mail Error: {mail_error}")

        return jsonify({"message": "LinkedIn URL linked successfully!"}), 200

    except Exception as e:
        print("Error linking LinkedIn:", str(e))
        return jsonify({"error": "An error occurred while linking LinkedIn"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/upload_selfie", methods=["POST"])
def upload_selfie():
    if "selfie" not in request.files:
        return jsonify({"error": "No selfie uploaded!"}), 400

    file = request.files["selfie"]
    filename = file.filename
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO selfie_uploads (file_name, file_path) VALUES (?, ?)", (filename, file_path))
        conn.commit()
        conn.close()
        
    except pyodbc.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Selfie uploaded successfully!", "success": True})
    

@app.route("/fetch_linkedin_data", methods=["GET"])
def fetch_linkedin_data():
    linkedin_profile_url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {linkedin_api_token}"}
    

    response = requests.get(linkedin_profile_url, headers=headers)
    
    if response.status_code == 200:
        profile_data = response.json()
        employment_details = profile_data.get("positions", None)
        
        if employment_details:
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET employment_details = ? WHERE user_id = ?", (str(employment_details), session['user_id']))
            conn.commit()
            conn.close()
            
            return jsonify({"message": "LinkedIn data fetched successfully!", "employment_details": employment_details}), 200
        else:
            return jsonify({"error": "No employment details found!"}), 400
    else:
        return jsonify({"error": "Failed to fetch LinkedIn data!"}), 500
@app.route("/verify_employment_details", methods=["GET"])
def verify_employment_details():
    # Fetch the LinkedIn employment details from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT employment_details FROM users WHERE user_id = ?", (session['user_id'],))
    employment_details = cursor.fetchone()
    conn.close()
    
    if employment_details:
        # Check for the presence of a job title or company
        if "developer" in employment_details[0].lower():
            return jsonify({"message": "Employment verified as developer!"}), 200
        else:
            return jsonify({"message": "Employment details do not match!"}), 400
    else:
        return jsonify({"error": "No employment details found!"}), 404
@app.route("/submit_linkedin", methods=["POST"])
def submit_linkedin():
    linkedin_url = request.form.get("linkedin_url")
    if linkedin_url:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insert LinkedIn URL into linkedin_profiles table
            cursor.execute("INSERT INTO linkedin_profiles (linkedin_url) VALUES (?)", (linkedin_url,))
            conn.commit()

            # Get the latest inserted ID from the sequence
            cursor.execute("SELECT LINKED_ID_SEQ.CURRVAL FROM dual")
            user_id = cursor.fetchone()[0]

            # Store the user_id in session
            # session["user_id"] = user_id

            # # Fetch the user's email from the users1 table using the session's user_id
            # user_id_from_session = session.get('user_id')  # Retrieve user_id from session

            # if user_id_from_session:
            #     cursor.execute("SELECT email FROM users1 WHERE user_id = ?", (user_id_from_session,))
            #     user_email_row = cursor.fetchone()

            #     if user_email_row:
            #         user_email = user_email_row[0]  # Extract the email from the result tuple
            #     else:
            #         return "User email not found in users1!", 404
            # else:
            #     return "User not logged in!", 400

            # Send email notification
            # msg = Message('LinkedIn URL Submitted Successfully',
            #               sender='soulmatenevermate@gmail.com',
            #               recipients=[user_email])
            # msg.body = f"Hi,\n\nYour LinkedIn URL '{linkedin_url}' has been successfully submitted and stored."

            # try:
            #     mail.send(msg)
            # except Exception as mail_error:
            #     print(f"Mail Error: {mail_error}")

        except Exception as e:
            conn.rollback()
            return f"Database error: {e}", 500
        finally:
            conn.close()

        return render_template("linkedin_success.html")
    else:
        return "No LinkedIn URL provided", 400


    


@app.route("/set_age_preference", methods=["GET", "POST"])
def set_age_preference():
    if request.method == "POST":
        min_age = request.form.get("min_age")
        max_age = request.form.get("max_age")
        user_id = session.get("user_id")  # Assumes this is set earlier

        if not (min_age and max_age and user_id):
            return "Please fill all the fields.", 400

        try:
            # Cast values to int
            min_age = int(min_age)
            max_age = int(max_age)
            user_id = int(user_id)

            conn = get_db_connection()
            cursor = conn.cursor()

            # INSERT only the three fields
            cursor.execute(
                "INSERT INTO AgePreference (USER_ID, MIN_AGE, MAX_AGE) VALUES (?, ?, ?)",
                (user_id, min_age, max_age)
            )

            conn.commit()
            conn.close()

            
            return render_template("age_success.html")
  # ✅ Correct

        except Exception as e:
            return f"Database Error: {e}", 500

    return render_template("set_age_preference.html")

@app.route("/check_age_compatibility", methods=["POST"])
def check_age_compatibility():
    user_id = session.get("user_id")
    chat_partner_id = request.form.get("chat_partner_id")

    if not user_id or not chat_partner_id:
        return "Invalid request", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the user's age preference from the database
    cursor.execute("SELECT MIN_AGE, MAX_AGE FROM AgePreference WHERE USER_ID = :1", (user_id,))
    user_preference = cursor.fetchone()

    if not user_preference:
        return "User preferences not found", 404

    min_age, max_age = user_preference

    # Fetch the chat partner's age from the database
    cursor.execute("SELECT AGE FROM Users WHERE USER_ID = :1", (chat_partner_id,))
    partner_age = cursor.fetchone()

    if not partner_age:
        return "Chat partner not found", 404

    partner_age = partner_age[0]

    # Check if the partner's age is within the user's preferred age range
    if partner_age < min_age or partner_age > max_age:
        return redirect(url_for('chat_request_error'))  # Redirect to error page

    # Proceed with initiating the chat if ages match
    return redirect(url_for('chat_session'))  # Proceed to chat session

@app.route('/chat_request', methods=['GET', 'POST'])
def chat_request():
    return render_template('chat_request.html')
from flask import flash, redirect, url_for
# @app.route('/send_message', methods=['POST'])
# def send_message():
#     if 'user_id' not in session:
#         return jsonify({'success': False, 'error': 'User not logged in'}), 401

#     sender_id = session['user_id']
#     receiver_id = request.form.get('receiver_id')
#     message_text = request.form.get('message_text')

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             INSERT INTO messages (sender_id, receiver_id, message_text, is_read)
#             VALUES (?, ?, ?, 0)
#         """, (sender_id, receiver_id, message_text))

#         conn.commit()
#         return jsonify({'success': True, 'message': 'Message sent'})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)})
#     finally:
#         cursor.close()
#         conn.close()


@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        min_age = data.get('min_age', 18)
        max_age = data.get('max_age', 60)
        religion = data.get('religion', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            MERGE INTO user_preferences target
            USING (SELECT ? AS user_id, ? AS min_age, ? AS max_age, ? AS religion FROM dual) source
            ON (target.user_id = source.user_id)
            WHEN MATCHED THEN
                UPDATE SET
                    target.min_age = source.min_age,
                    target.max_age = source.max_age,
                    target.religion = source.religion
            WHEN NOT MATCHED THEN
                INSERT (user_id, min_age, max_age, religion)
                VALUES (source.user_id, source.min_age, source.max_age, source.religion)
        """, (session['user_id'], min_age, max_age, religion))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Preferences updated'})
    
    except Exception as e:
        print(f"Error updating preferences: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        message_text = data.get('message_text')
        
        if not receiver_id or not message_text:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get sender and receiver details
        cursor.execute("SELECT name, email FROM users1 WHERE user_id = ?", (session['user_id'],))
        sender = cursor.fetchone()
        
        cursor.execute("SELECT name, email FROM users1 WHERE user_id = ?", (receiver_id,))
        receiver = cursor.fetchone()
        
        if not sender or not receiver:
            return jsonify({'success': False, 'error': 'Invalid user'}), 400
        
        # Insert the message
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, message_text)
            VALUES (?, ?, ?)
        """, (session['user_id'], receiver_id, message_text))
        
        conn.commit()
        
        # Send email notification to receiver
        try:
            msg = Message(
                'New Message Received',
                sender='soulmate4yours@gmail.com',
                recipients=[receiver[1]]  # receiver's email
            )
            msg.body = f"""Hi {receiver[0]},

You have received a new message from {sender[0]}:

"{message_text}"

You can reply directly by logging into your account.

Thank you,
Matrimony Team
"""
            mail.send(msg)
        except Exception as mail_error:
            print(f"Failed to send email notification: {mail_error}")
            # Continue even if email fails
        
        return jsonify({
            'success': True, 
            'message': 'Message sent',
            'sender_name': sender[0]
        })
    
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/messages')
def view_messages():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT m.message_id, u.user_id AS sender_id, u.name AS sender_name, 
                   u.email AS sender_email, m.message_text, m.is_read
            FROM messages m
            JOIN users1 u ON m.sender_id = u.user_id
            WHERE m.receiver_id = ?
            ORDER BY m.message_id DESC
        """, (user_id,))

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        messages = [dict(zip(columns, row)) for row in rows]

        return jsonify({'success': True, 'messages': messages})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()
@app.route('/mark_read/<int:message_id>', methods=['POST'])
def mark_message_read(message_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE messages 
            SET is_read = 1 
            WHERE message_id = ? AND receiver_id = ?
        """, (message_id, session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()
        

@app.route('/reply_message', methods=['POST'])
def reply_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        original_sender_id = data.get('original_sender_id')
        reply_text = data.get('reply_text')
        
        if not original_sender_id or not reply_text:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user details for email
        cursor.execute("SELECT name, email FROM users1 WHERE user_id = ?", (session['user_id'],))
        sender = cursor.fetchone()
        
        cursor.execute("SELECT name, email FROM users1 WHERE user_id = ?", (original_sender_id,))
        receiver = cursor.fetchone()
        
        if not sender or not receiver:
            return jsonify({'success': False, 'error': 'Invalid user'}), 400
        
        # Insert the reply (just as a regular message)
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, message_text)
            VALUES (?, ?, ?)
        """, (session['user_id'], original_sender_id, reply_text))
        
        conn.commit()
        
        # Send email notification for the reply
        try:
            msg = Message(
                'You Have a Reply to Your Message',
                sender='soulmate4yours@gmail.com',
                recipients=[receiver[1]]  # original sender's email
            )
            msg.body = f"""Hi {receiver[0]},

You have received a reply from {sender[0]}:

"{reply_text}"

You can continue the conversation by logging into your account.

Thank you,
Matrimony Team
"""
            mail.send(msg)
        except Exception as mail_error:
            print(f"Failed to send email notification: {mail_error}")
        
        return jsonify({
            'success': True, 
            'message': 'Reply sent',
            'sender_name': sender[0]
        })
    
    except Exception as e:
        print(f"Error sending reply: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/message_sent')
def message_sent():
    return render_template('message_sent.html')
@app.route('/message_form')
def message_form():
    return render_template('message_form.html')

@app.route("/compatible_users")
def compatible_users():
    return render_template("compatible_users.html")




    


if __name__ == "__main__":
    app.run(debug=True) 