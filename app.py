from flask import Flask, render_template, jsonify, request
import pymysql
from pymysql.cursors import DictCursor
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'cine-soul-secret-key-2024'

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'pravv',
    'database': 'cinesoul',
    'cursorclass': DictCursor,
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get a database connection"""
    return pymysql.connect(**MYSQL_CONFIG)

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/movie-details')
def movie_details():
    return render_template('movie-details.html')

@app.route('/search-results')
def search_results():
    return render_template('search-results.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q')
    # Make TMDB API call here (server-side)
    # Return JSON data
    return jsonify({"results": []})



# ========== API ENDPOINTS ==========

@app.route('/api/auth/check-username', methods=['GET'])
def check_username():
    username = request.args.get('username', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return jsonify({'exists': exists})
    except Exception as e:
        print(f"Error checking username: {e}")
        return jsonify({'exists': False})

@app.route('/api/auth/check-email', methods=['GET'])
def check_email():
    email = request.args.get('email', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return jsonify({'exists': exists})
    except Exception as e:
        print(f"Error checking email: {e}")
        return jsonify({'exists': False})

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CORRECTED: Your table has 'password' not 'password_hash'
        query = """
            SELECT id, username, email, password, name, created_at
            FROM users 
            WHERE username = %s OR email = %s
            LIMIT 1
        """
        
        cursor.execute(query, (username, username))
        user = cursor.fetchone()
        
        if user:
            print(f"User found: {user['username']}")
            
            # Check password (plain text since you inserted 'password123')
            if user['password'] == password:
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'name': user['name'] if user['name'] else user['username'],
                    'created_at': str(user['created_at']) if user['created_at'] else None
                }
                
                cursor.close()
                conn.close()
                return jsonify({'success': True, 'user': user_data})
            else:
                print(f"Password mismatch. Stored: {user['password']}, Provided: {password}")
        
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid username or password'})
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.json
    
    # Validate required fields
    if not data.get('username'):
        return jsonify({'success': False, 'error': 'Username is required'})
    if not data.get('email'):
        return jsonify({'success': False, 'error': 'Email is required'})
    if not data.get('password'):
        return jsonify({'success': False, 'error': 'Password is required'})
    
    if len(data['password']) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters'})
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (data['username'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Username already taken'})
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Email already registered'})
        
        # Insert new user - CORRECTED: using 'password' column
        insert_data = {
            'username': data['username'],
            'email': data['email'],
            'password': data['password'],  # Plain text for now
            'name': data.get('name', '')
        }
        
        query = """
            INSERT INTO users (username, email, password, name, created_at)
            VALUES (%(username)s, %(email)s, %(password)s, %(name)s, NOW())
        """
        
        cursor.execute(query, insert_data)
        conn.commit()
        user_id = cursor.lastrowid
        
        # Get the created user
        cursor.execute("""
            SELECT id, username, email, name, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Prepare response
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'name': user['name'] if user['name'] else user['username'],
            'created_at': str(user['created_at'])
        }
        
        return jsonify({'success': True, 'user': user_data})
        
    except Exception as e:
        print(f"Signup error: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
            conn.close()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'})

@app.route('/api/auth/verify-email', methods=['GET'])
def verify_email():
    """Verify email exists (for forgot password)"""
    email = request.args.get('email', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return jsonify({'exists': exists})
    except Exception as e:
        print(f"Error verifying email: {e}")
        return jsonify({'exists': False})

@app.route('/api/auth/verify-dob', methods=['POST'])
def verify_dob():
    """Verify date of birth (for forgot password) - SIMPLIFIED since no DOB column"""
    try:
        data = request.json
        email = data.get('email')
        
        # Your current table doesn't have date_of_birth, so just check email
        if not email:
            return jsonify({'verified': False})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Just check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        
        verified = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        return jsonify({'verified': verified})
    except Exception as e:
        print(f"Error verifying: {e}")
        return jsonify({'verified': False})

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password"""
    try:
        data = request.json
        email = data.get('email')
        new_password = data.get('newPassword')
        
        if not email or not new_password:
            return jsonify({'success': False, 'error': 'Email and new password required'})
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update password - CORRECTED: 'password' column
        cursor.execute("""
            UPDATE users 
            SET password = %s 
            WHERE email = %s
        """, (new_password, email))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'User not found'})
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'success': False, 'error': 'Server error'})

@app.route('/api/auth/test', methods=['GET'])
def test_auth():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'success',
        'message': 'CineSoul Authentication API is running!',
        'endpoints': {
            'login': '/api/auth/login (POST)',
            'signup': '/api/auth/signup (POST)',
            'check_username': '/api/auth/check-username (GET)',
            'check_email': '/api/auth/check-email (GET)'
        }
    })

@app.route('/api/auth/test-login', methods=['GET'])
def test_login():
    """Test login with test user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get test user
        cursor.execute("SELECT * FROM users WHERE username = 'testuser'")
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'password': user['password'],
                    'name': user['name']
                },
                'note': 'Password is stored as: ' + user['password']
            })
        else:
            return jsonify({'success': False, 'error': 'Test user not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print(" Starting CineSoul application...")
    print("=" * 50)
    print("Welcome page: http://localhost:5000/")
    print(" Login page: http://localhost:5000/login")
    print("=" * 50)
    print("\r API Endpoints:")
    print("  POST   /api/auth/login")
    print("  POST   /api/auth/signup")
    print("  GET    /api/auth/check-username")
    print("  GET    /api/auth/check-email")
    print("  GET    /api/auth/test")
    print("  GET    /api/auth/test-login")
    print("=" * 50)
    print("\n Test user created in database:")
    print("  Username: testuser")
    print("  Password: password123")
    print("  Email: test@example.com")
    print("=" * 50)
    
    app.run(debug=True, port=5000)
