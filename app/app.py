from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask import Response
from functools import wraps
from models import User, TeamMember, PortfolioCategory, Portfolio, Gallery, ServiceCategory, Service, Testimonial
from database import get_db_connection, DBCursor
import json
from jinja2 import Environment
from werkzeug.utils import secure_filename
import os
import numpy as np
import bcrypt
import mysql.connector
from slugify import slugify
import hashlib
import unicodedata
from datetime import timedelta, datetime
import uuid


app = Flask(__name__)
app.secret_key = 'INIKODERAHASIAANDA'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=6)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db_cursor():
    conn = get_db_connection()
    return conn.cursor(dictionary=True), conn

# Configure upload folders
BASE_UPLOAD_FOLDER = 'static/uploads'
GALLERY_UPLOAD_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, 'gallery')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure Flask app
app.config['UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER  # Untuk upload umum
app.config['GALLERY_UPLOAD_FOLDER'] = GALLERY_UPLOAD_FOLDER  # Khusus gallery

# Pastikan folder gallery dibuat
os.makedirs(GALLERY_UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    cursor, conn = get_db_cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(
                id=user['id'],
                username=user['username'],
                fullname=user['fullname'],
                email=user['email'],
                password=user['password'],
                role=user.get('role', 'user'),
                is_admin=bool(user.get('is_admin', 0)),
                created_at=user.get('created_at'),
                updated_at=user.get('updated_at')
            )
        return None
    finally:
        cursor.close()
        conn.close()

def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@is_admin
def admin_dashboard():
    try:
        with DBCursor() as cursor:
            # Get statistics
            cursor.execute("SELECT COUNT(*) as total FROM portfolio")
            total_portfolio = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM services")
            total_services = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM gallery")
            total_media = cursor.fetchone()['total']
            
            # Get recent portfolio items
            cursor.execute("""
                SELECT p.id, p.title, p.client_name, p.project_date, p.status 
                FROM portfolio p 
                ORDER BY p.project_date DESC 
                LIMIT 5
            """)
            recent_portfolios = cursor.fetchall()
            
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {str(e)}")
        flash('Error fetching dashboard data', 'danger')
        total_portfolio = total_services = total_media = 0
        recent_portfolios = []
    
    return render_template('admin.html',
                         total_portfolio=total_portfolio,
                         total_services=total_services,
                         total_media=total_media,
                         recent_portfolios=recent_portfolios)

@app.route('/team_management', methods=['GET', 'POST'])
@login_required
@is_admin
def team_management():
    if request.method == 'POST':
        try:
            # Handle file upload
            file = request.files.get('file')
            filename = None
            file_path = None
            
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash('Invalid file type', 'danger')
                    return redirect(url_for('team_management'))
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

            # Create new member
            new_member = TeamMember(
                nama=request.form['nama'],
                divisi=request.form['divisi'],
                subdivisi=request.form.get('subdivisi', ''),
                file_name=filename,
                file_path=file_path,
                file_type=file.content_type if file else None,
                level=request.form['level'],
                uploaded_by=current_user.id
            )
            
            new_member.save()
            flash('Member added successfully', 'success')
        except Exception as e:
            flash(f'Error creating member: {str(e)}', 'danger')
        
        return redirect(url_for('team_management'))
    
    # GET request - show all members
    members = TeamMember.get_all()
    return render_template('team_management.html', members=members)

@app.route('/team_member/<int:member_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def team_member_detail(member_id):
    if request.method == 'GET':
        member = TeamMember.get_by_id(member_id)
        if member:
            return jsonify({
                'id': member.id,
                'nama': member.nama,
                'divisi': member.divisi,
                'subdivisi': member.subdivisi,
                'file_name': member.file_name,
                'level': member.level,
                'created_at': member.created_at.strftime('%Y-%m-%d') if member.created_at else None
            })
        return jsonify({'error': 'Member not found'}), 404
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            member = TeamMember.get_by_id(member_id)
            if not member:
                return jsonify({'error': 'Member not found'}), 404
            
            # Update member fields
            member.nama = data.get('nama', member.nama)
            member.divisi = data.get('divisi', member.divisi)
            member.subdivisi = data.get('subdivisi', member.subdivisi)
            member.level = data.get('level', member.level)
            
            member.save()
            return jsonify({
                'message': 'Member updated successfully',
                'member': {
                    'id': member.id,
                    'nama': member.nama,
                    'divisi': member.divisi,
                    'subdivisi': member.subdivisi,
                    'level': member.level
                }
            }), 200
                
        except Exception as e:
            return jsonify({'error': f'Failed to update member: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            member = TeamMember.get_by_id(member_id)
            if not member:
                return jsonify({'error': 'Member not found'}), 404
            
            # Delete associated file
            if member.file_path and os.path.exists(member.file_path):
                os.remove(member.file_path)
            
            member.delete()
            return jsonify({'message': 'Member deleted successfully'}), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/portfolio_categories', methods=['GET', 'POST'])
@login_required
@is_admin
def portfolio_categories():
    if request.method == 'POST':
        try:
            name = request.form['name']
            slug = request.form['slug']
            description = request.form.get('description', '')
            
            new_category = PortfolioCategory(
                name=name,
                slug=slug,
                description=description,
            )
            new_category.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'message': 'Category added successfully',
                    'category': {
                        'id': new_category.id,
                        'name': new_category.name,
                        'slug': new_category.slug
                    }
                })
            else:
                flash('Category added successfully', 'success')
                return redirect(url_for('portfolio_categories'))
                
        except Exception as e:
            error_msg = f'Error creating category: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), 400
            else:
                flash(error_msg, 'danger')
                return redirect(url_for('portfolio_categories'))
    
    # GET request - show all categories
    categories = PortfolioCategory.get_all()
    return render_template('portfolio_categories.html', categories=categories)

@app.route('/portfolio_category/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def portfolio_category_detail(category_id):
    if request.method == 'GET':
        category = PortfolioCategory.get_by_id(category_id)
        if category:
            return jsonify({
                'status': 'success',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'created_at': category.created_at.strftime('%Y-%m-%d') if category.created_at else None
                }
            })
        return jsonify({
            'status': 'error',
            'message': 'Category not found'
        }), 404
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
                
            category = PortfolioCategory.get_by_id(category_id)
            if not category:
                return jsonify({
                    'status': 'error',
                    'message': 'Category not found'
                }), 404
            
            # Update category fields
            category.name = data.get('name', category.name)
            category.slug = data.get('slug', category.slug)
            category.description = data.get('description', category.description)
            
            category.save()
            return jsonify({
                'status': 'success',
                'message': 'Category updated successfully',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug
                }
            })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to update category: {str(e)}'
            }), 500
    
    elif request.method == 'DELETE':
        try:
            category = PortfolioCategory.get_by_id(category_id)
            if not category:
                return jsonify({
                    'status': 'error',
                    'message': 'Category not found'
                }), 404
            
            category.delete()
            return jsonify({
                'status': 'success',
                'message': 'Category deleted successfully'
            })
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@app.route('/portfolio', methods=['GET', 'POST'])
@login_required
@is_admin
def portfolio_management():
    if request.method == 'POST':
        try:
            # Handle new portfolio creation
            title = request.form['title']
            client_name = request.form['client_name']
            project_date = request.form['project_date']
            description = request.form['description']
            project_date_str = request.form['project_date']
            project_date = None
            if project_date_str:
                try:
                    project_date = datetime.strptime(project_date_str, '%Y-%m-%d')
                except ValueError:
                    project_date = None
            
            # Process file upload
            cover_image = request.files.get('cover_image')
            cover_image_name = None
            if cover_image and cover_image.filename != '':
                if not allowed_file(cover_image.filename):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400
                    flash('Invalid file type', 'danger')
                    return redirect(url_for('portfolio_management'))
                
                cover_image_name = secure_filename(cover_image.filename)
                cover_image.save(os.path.join(app.config['UPLOAD_FOLDER'], cover_image_name))
            
            # Create new portfolio
            portfolio = Portfolio(
                title=title,
                slug=slugify(title),
                client_name=client_name,
                project_date=project_date,
                description=description,
                idea=request.form.get('idea', ''),
                cover_image=cover_image_name,
                project_url=request.form.get('project_url', ''),
                project_url_behance=request.form.get('project_url_behance', ''),
                user_id=current_user.id,
                category_id=request.form.get('category_id'),
                is_featured=1 if request.form.get('is_featured') else 0,
                status=1 if request.form.get('status') == '1' else 0
            )
            portfolio.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success', 
                    'message': 'Portfolio created successfully',
                    'portfolio': portfolio.to_dict()
                })
            return redirect(url_for('portfolio_management'))
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': f'Error creating portfolio: {str(e)}'
                }), 500
            flash(f'Error creating portfolio: {str(e)}', 'danger')
            return redirect(url_for('portfolio_management'))
    
    # GET request - show all portfolios
    portfolios = Portfolio.get_all()
    categories = PortfolioCategory.get_all()
    return render_template('portofolio_admin.html', portfolios=portfolios, categories=categories)

@app.route('/portfolio/<int:portfolio_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def portfolio_detail(portfolio_id):
    if request.method == 'GET':
        portfolio = Portfolio.get_by_id(portfolio_id)
        if portfolio:
            return jsonify(portfolio.to_dict())
        return jsonify({'error': 'Portfolio not found'}), 404
    
    elif request.method == 'PUT' and portfolio_id:
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
                
            portfolio = Portfolio.get_by_id(portfolio_id)
            if not portfolio:
                return jsonify({
                    'status': 'error',
                    'message': 'Portfolio not found'
                }), 404
            
            # Convert project_date string to date object if it exists
            project_date_str = data.get('project_date')
            project_date = None
            if project_date_str:
                try:
                    project_date = datetime.strptime(project_date_str, '%Y-%m-%d').date()
                except ValueError:
                    project_date = None
            
            # Update portfolio fields
            portfolio.title = data.get('title', portfolio.title)
            portfolio.slug = slugify(data.get('title', portfolio.title))
            portfolio.client_name = data.get('client_name', portfolio.client_name)
            portfolio.project_date = project_date if project_date_str else portfolio.project_date
            portfolio.description = data.get('description', portfolio.description)
            portfolio.idea = data.get('idea', portfolio.idea)
            portfolio.project_url = data.get('project_url', portfolio.project_url)
            portfolio.is_featured = bool(data.get('is_featured', portfolio.is_featured))
            portfolio.status = bool(data.get('status', portfolio.status))
            portfolio.category_id = data.get('category_id', portfolio.category_id)
            
            portfolio.save()
            return jsonify({
                'status': 'success',
                'message': 'Portfolio updated successfully',
                'portfolio': portfolio.to_dict()
            })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error updating portfolio: {str(e)}'
            }), 500
    elif request.method == 'DELETE':
        try:
            portfolio = Portfolio.get_by_id(portfolio_id)
            if not portfolio:
                return jsonify({'error': 'Portfolio not found'}), 404
            
            # Delete cover image if exists
            if portfolio.cover_image:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], portfolio.cover_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            portfolio.delete()
            return jsonify({'message': 'Portfolio deleted successfully'}), 200
        
        except Exception as e:
                return jsonify({'error': str(e)}), 500
            
@app.route('/user', methods=['GET', 'POST'])
@login_required
@is_admin
def user_management():
    if request.method == 'POST':
        # Handle JSON requests (from fetch)
        if request.is_json:
            data = request.get_json()
            if 'add_user' in data:
                # Add user logic here similar to PUT but with creation
                username = data['username']
                fullname = data['fullname']
                email = data['email']
                password = data['password']
                role = data['role']
                
                if User.get_by_email_or_username(username) or User.get_by_email_or_username(email):
                    return jsonify({'error': 'Username or email already exists'}), 400
                
                try:
                    new_user = User(
                        username=username,
                        fullname=fullname,
                        email=email,
                        role=role,
                        is_admin=(role == 'admin')
                    )
                    new_user.set_password(password)
                    new_user.save()
                    return jsonify({
                        'message': 'User added successfully',
                        'user': {
                            'id': new_user.id,
                            'username': new_user.username,
                            'email': new_user.email
                        }
                    }), 201
                except Exception as e:
                    return jsonify({'error': f'Error adding user: {str(e)}'}), 500
        
        # Handle traditional form submission
        else:
            if 'add_user' in request.form:
                username = request.form['username']
                fullname = request.form['fullname']
                email = request.form['email']
                password = request.form['password']
                role = request.form['role']
                
                if User.get_by_email_or_username(username) or User.get_by_email_or_username(email):
                    flash('Username or email already exists', 'danger')
                    return redirect(url_for('user_management'))
                
                try:
                    new_user = User(
                        username=username,
                        fullname=fullname,
                        email=email,
                        role=role,
                        is_admin=(role == 'admin')
                    )
                    new_user.set_password(password)
                    new_user.save()
                    flash('User added successfully', 'success')
                except Exception as e:
                    flash(f'Error adding user: {str(e)}', 'danger')
                
                return redirect(url_for('user_management'))
    
    users = User.get_all()
    return render_template('user_admin.html', users=users)

@app.route('/user/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def user_detail(user_id):
    if request.method == 'GET':
        user = User.get_by_id(user_id)
        if user:
            return jsonify({
                'id': user.id,
                'username': user.username,
                'fullname': user.fullname,
                'email': user.email,
                'role': user.role,
                'is_admin': user.is_admin,
                'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None
            })
        return jsonify({'error': 'User not found'}), 404
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            user = User.get_by_id(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Check if username/email already exists (excluding current user)
            existing_user = User.get_by_email_or_username(data.get('username'))
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Username already exists'}), 400
                
            existing_email = User.get_by_email_or_username(data.get('email'))
            if existing_email and existing_email.id != user_id:
                return jsonify({'error': 'Email already exists'}), 400
            
            # Update user fields
            user.username = data.get('username', user.username)
            user.fullname = data.get('fullname', user.fullname)
            user.email = data.get('email', user.email)
            user.role = data.get('role', user.role)
            user.is_admin = (data.get('role', user.role) == 'admin')
            
            if data.get('password'):
                user.set_password(data.get('password'))
            
            user.save()
            return jsonify({
                'message': 'User updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
                
        except Exception as e:
            return jsonify({'error': f'Failed to update user: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            user = User.get_by_id(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.id == current_user.id:
                return jsonify({'error': 'Cannot delete your own account'}), 400
            
            user.delete()
            return jsonify({'message': 'User deleted successfully'}), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/service_categories', methods=['GET', 'POST'])
@login_required
@is_admin
def service_categories():
    if request.method == 'POST':
        try:
            name = request.form['name']
            slug = request.form['slug']
            description = request.form.get('description', '')
            
            if not name or not slug:
                return jsonify({'error': 'Name and slug are required'}), 400
            
            new_category = ServiceCategory(
                name=name,
                slug=slug,
                description=description
            )
            if new_category.save():
                return jsonify({
                    'message': 'Category added successfully',
                    'category': {
                        'id': new_category.id,
                        'name': new_category.name,
                        'slug': new_category.slug
                    }
                })
            else:
                return jsonify({'error': 'Failed to save category'}), 500
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    categories = ServiceCategory.get_all()
    return render_template('service_categories.html', categories=categories)

@app.route('/service_category/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def service_category_detail(category_id):
    if request.method == 'GET':
        # Handle GET request
        category = ServiceCategory.get_by_id(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        return jsonify({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description
        })
    
    elif request.method == 'PUT':
        try:
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
                
            data = request.get_json()
            category = ServiceCategory.get_by_id(category_id)
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            
            if 'name' in data:
                category.name = data['name']
            if 'slug' in data:
                category.slug = data['slug']
            if 'description' in data:
                category.description = data.get('description', '')
            
            if category.save():
                return jsonify({
                    'message': 'Category updated successfully',
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'slug': category.slug,
                        'description': category.description
                    }
                })
            return jsonify({'error': 'Failed to update category'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            category = ServiceCategory.get_by_id(category_id)
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            
            if category.delete():
                return jsonify({'message': 'Category deleted successfully'})
            return jsonify({'error': 'Failed to delete category'}), 500
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Return a default response if none of the above methods match
    return jsonify({'error': 'Method not allowed'}), 405

@app.route('/service', methods=['GET', 'POST'])
@login_required
@is_admin
def service_management():
    if request.method == 'POST':
        try:
            title = request.form['title']
            slug = request.form['slug']
            short_description = request.form['short_description']
            full_description = request.form['full_description']
            icon_feature1 = request.form.get('icon_feature1', 'fas fa-cog')
            text_feature1 = request.form.get('text_feature1', '')
            nama_feature1 = request.form.get('nama_feature1', '')
            icon2 = request.form.get('icon2', 'fas fa-cog')
            nama_feature2 = request.form.get('nama_feature2', '')
            text_feature2 = request.form.get('text_feature2', '')
            display_order = int(request.form.get('display_order', 0))
            is_active = 1 if request.form.get('is_active') else 0
            category_id = request.form.get('category_id')
            meta_title = request.form.get('meta_title', '')
            meta_description = request.form.get('meta_description', '')
            
            featured_image = request.files.get('featured_image')
            featured_image_name = None
            if featured_image and featured_image.filename != '':
                if not allowed_file(featured_image.filename):
                    flash('Invalid featured image file type', 'danger')
                    return redirect(url_for('service_management'))
                
                featured_image_name = secure_filename(featured_image.filename)
                featured_image.save(os.path.join(app.config['UPLOAD_FOLDER'], featured_image_name))
            
            detail_image = request.files.get('detail_service_image')
            detail_image_name = None
            if detail_image and detail_image.filename != '':
                if not allowed_file(detail_image.filename):
                    flash('Invalid detail service image file type', 'danger')
                    return redirect(url_for('service_management'))
                
                detail_image_name = secure_filename(detail_image.filename)
                detail_image.save(os.path.join(app.config['UPLOAD_FOLDER'], detail_image_name))
            
            new_service = Service(
                title=title,
                slug=slug,
                short_description=short_description,
                full_description=full_description,
                icon_feature1=icon_feature1,
                text_feature1=text_feature1,
                nama_feature1=nama_feature1,
                icon2=icon2,
                nama_feature2=nama_feature2,
                text_feature2=text_feature2,
                featured_image=featured_image_name,
                detail_service_image=detail_image_name,
                is_active=is_active,
                display_order=display_order,
                meta_title=meta_title,
                meta_description=meta_description,
                category_id=category_id,
                user_id=current_user.id
            )
            new_service.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'message': 'Service added successfully'
                })
            else:
                flash('Service added successfully', 'success')
                return redirect(url_for('service_management'))
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': f'Error creating service: {str(e)}'
                }), 500
            else:
                flash(f'Error creating service: {str(e)}', 'danger')
                return redirect(url_for('service_management'))
    
    services = Service.get_all_with_category()
    categories = ServiceCategory.get_all()
    return render_template('service_management.html', services=services, categories=categories)

@app.route('/service/<int:service_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def service_detail(service_id):
    if request.method == 'GET':
        service = Service.get_by_id(service_id)
        if service:
            return jsonify(service.to_dict())
        return jsonify({'error': 'Service not found'}), 404
    
    elif request.method == 'PUT':
        try:
            service = Service.get_by_id(service_id)
            if not service:
                return jsonify({'error': 'Service not found'}), 404
            
            # Handle form data (including files)
            title = request.form.get('title', service.title)
            slug = request.form.get('slug', service.slug)
            short_description = request.form.get('short_description', service.short_description)
            full_description = request.form.get('full_description', service.full_description)
            icon_feature1 = request.form.get('icon_feature1', service.icon_feature1)
            text_feature1 = request.form.get('text_feature1', service.text_feature1)
            nama_feature1 = request.form.get('nama_feature1', service.nama_feature1)
            icon2 = request.form.get('icon2', service.icon2)
            nama_feature2 = request.form.get('nama_feature2', service.nama_feature2)
            text_feature2 = request.form.get('text_feature2', service.text_feature2)
            display_order = int(request.form.get('display_order', service.display_order))
            is_active = 1 if request.form.get('is_active') else 0
            category_id = request.form.get('category_id', service.category_id)
            meta_title = request.form.get('meta_title', service.meta_title)
            meta_description = request.form.get('meta_description', service.meta_description)
            
            # Handle featured image update
            featured_image = request.files.get('featured_image')
            featured_image_name = service.featured_image
            if featured_image and featured_image.filename != '':
                if not allowed_file(featured_image.filename):
                    return jsonify({'error': 'Invalid featured image file type'}), 400
                
                # Delete old image if exists
                if service.featured_image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], service.featured_image)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service.featured_image))
                
                featured_image_name = secure_filename(featured_image.filename)
                featured_image.save(os.path.join(app.config['UPLOAD_FOLDER'], featured_image_name))
            
            # Handle detail service image update
            detail_image = request.files.get('detail_service_image')
            detail_image_name = service.detail_service_image
            if detail_image and detail_image.filename != '':
                if not allowed_file(detail_image.filename):
                    return jsonify({'error': 'Invalid detail service image file type'}), 400
                
                # Delete old image if exists
                if service.detail_service_image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], service.detail_service_image)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service.detail_service_image))
                
                detail_image_name = secure_filename(detail_image.filename)
                detail_image.save(os.path.join(app.config['UPLOAD_FOLDER'], detail_image_name))
            
            # Update service
            service.update(
                title=title,
                slug=slug,
                short_description=short_description,
                full_description=full_description,
                icon_feature1=icon_feature1,
                text_feature1=text_feature1,
                nama_feature1=nama_feature1,
                icon2=icon2,
                nama_feature2=nama_feature2,
                text_feature2=text_feature2,
                featured_image=featured_image_name,
                detail_service_image=detail_image_name,
                is_active=is_active,
                display_order=display_order,
                meta_title=meta_title,
                meta_description=meta_description,
                category_id=category_id
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Service updated successfully',
                'service': service.to_dict()
            }), 200
                
        except Exception as e:
            print("Server error:", str(e))
            return jsonify({'error': f'Server error: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            service = Service.get_by_id(service_id)
            if not service:
                return jsonify({'error': 'Service not found'}), 404
            
            # Delete images if they exist
            if service.featured_image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], service.featured_image)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service.featured_image))
            if service.detail_service_image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], service.detail_service_image)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service.detail_service_image))
            
            service.delete()
            return jsonify({'message': 'Service deleted successfully'}), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Method not allowed'}), 405

@app.route('/settings', methods=['GET'])
@login_required
@is_admin
def settings():
    return render_template('settings_admin.html')

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
@login_required
@is_admin
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        user = User.get_by_email_or_username(email)
        if user:
            flash('Email already registered!', 'danger')
        else:
            try:
                new_user = User(
                    username=username,
                    fullname=fullname,
                    email=email,
                    role=role,
                    is_admin=(role == 'admin')
                )
                new_user.set_password(password)
                new_user.save()
                flash('Account created successfully!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'Error creating account: {str(e)}', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        if not identifier or not password:
            flash('Please fill in all fields', 'danger')
            return redirect(url_for('login'))
        
        user = User.get_by_email_or_username(identifier)
        
        if not user:
            flash('Invalid email/username or password', 'danger')
            return redirect(url_for('login'))
            
        if not user.check_password(password):
            flash('Invalid email/username or password', 'danger')
            return redirect(url_for('login'))
            
        login_user(user)
        flash('Login successful!', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Public routes
@app.route('/')
def index():
    try:
        # Get featured services
        cursor, conn = get_db_cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.short_description, s.featured_image,
                   sc.name as category_name
            FROM services s
            LEFT JOIN service_categories sc ON s.category_id = sc.id
            WHERE s.is_active = 1
            ORDER BY s.display_order ASC
            LIMIT 3
        """)
        services_data = [dict(row) for row in cursor.fetchall()]

        # Get featured portfolios
        cursor.execute("""
            SELECT p.*, pc.name as category_name, pc.slug as category_slug
            FROM portfolio p
            LEFT JOIN portfolio_categories pc ON p.category_id = pc.id
            WHERE p.is_featured = 1 AND p.status = 1
            ORDER BY p.project_date DESC
            LIMIT 3
        """)
        featured_portfolios = [dict(row) for row in cursor.fetchall()]

        # Get active testimonials
        cursor.execute("""
            SELECT name, company, message as testimonial_text, photo as image
            FROM testimonials
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
        """)
        testimonials = [dict(row) for row in cursor.fetchall()]

        # Get stats data
        cursor.execute("SELECT COUNT(*) as total FROM testimonials WHERE is_active = '1'")
        clients = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM portfolio WHERE status = '1'")
        projects = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM services WHERE is_active = '1'")
        services = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM media")
        team = cursor.fetchone()['total']

        stats = {
            'clients': clients,
            'projects': projects,
            'services': services,
            'team': team
        }

    except Exception as e:
        print(f"Error fetching data for home page: {e}")
        services_data = []
        featured_portfolios = []
        testimonials = []
        stats = {}
    finally:
        cursor.close()
        conn.close()

    return render_template('home.html',
                         services=services_data,
                         featured_portfolios=featured_portfolios,
                         testimonials=testimonials, stats=stats)

@app.route('/about-us')
def about_us():
    formatted_members = []
    try:
        cursor, conn = get_db_cursor()
        cursor.execute("""
            SELECT 
                id,
                nama,
                divisi,
                COALESCE(subdivisi, '') as subdivisi,
                file_name,
                created_at,
                level
            FROM media
            WHERE file_name IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN level = 1 THEN 1
                    WHEN divisi = 'Social Media' THEN 2
                    WHEN divisi = 'Creatives' THEN 3
                    WHEN divisi = 'Visual Designers' THEN 4
                    WHEN divisi = 'Media Production' THEN 5
                    ELSE 6
                END,
                level ASC,
                nama ASC
        """)
        
        formatted_members = [
            {
                'id': member['id'],
                'nama': member['nama'],
                'divisi': member['divisi'],
                'subdivisi': member['subdivisi'],
                'file_name': member['file_name'],
                'level': member['level']
            }
            for member in cursor.fetchall()
        ]

    except Exception as e:
        app.logger.error(f"Error fetching team members: {str(e)}")
        flash('Gagal memuat data tim', 'error')
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return render_template('aboutus.html', team_members=formatted_members)


@app.route('/services')
def service():
    try:
        categories = ServiceCategory.get_all()
        services = Service.get_all_with_category()
    except Exception as e:
        print(f"Error fetching service data: {e}")
        categories = []
        services = []

    return render_template('services1.html', 
                           categories=categories,
                           services=services)

@app.route('/portofolio')
def portfolio():
    try:
        # Get all categories
        categories = PortfolioCategory.get_all()
        
        # Get all portfolios with their category information
        portfolios = []
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT p.*, pc.name as category_name, pc.slug as category_slug
            FROM portfolio p
            LEFT JOIN portfolio_categories pc ON p.category_id = pc.id
            ORDER BY p.project_date DESC
        """
        cursor.execute(query)
        
        for row in cursor.fetchall():
            # Create a Portfolio object
            portfolio = Portfolio(
                id=row['id'],
                title=row['title'],
                slug=row['slug'],
                client_name=row['client_name'],
                project_date=row['project_date'],
                description=row['description'],
                idea=row.get('idea', ''),
                cover_image=row.get('cover_image'),
                project_url=row.get('project_url'),
                project_url_behance=row.get('project_url_behance'),
                user_id=row.get('user_id'),
                category_id=row.get('category_id'),
                is_featured=row.get('is_featured', 0),
                status=row.get('status', 'draft'),
                created_at=row.get('created_at')
            )
            
            # Add category information
            portfolio.category = {
                'name': row['category_name'],
                'slug': row['category_slug']
            }
            
            portfolios.append(portfolio)
            
    except Exception as e:
        print(f"Error fetching portfolio data: {e}")
        categories = []
        portfolios = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('portofolio.html', categories=categories, portfolios=portfolios)


@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/portfolio_details/<int:id>')
def portfolio_details(id):
    cursor, conn = get_db_cursor()
    try:
        query = """
            SELECT p.*, pc.name AS category_name, pc.slug AS category_slug 
            FROM portfolio p
            JOIN portfolio_categories pc ON p.category_id = pc.id
            WHERE p.id = %s
        """
        cursor.execute(query, (id,))
        portfolio_data = cursor.fetchone()
        
        if not portfolio_data:
            return render_template('errors/404.html'), 404
        
        portfolio = {
            'id': portfolio_data['id'],
            'title': portfolio_data.get('title', 'Untitled Portfolio'),
            'description': portfolio_data.get('description', ''),
            'idea': portfolio_data.get('idea', ''),
            'cover_image': portfolio_data.get('cover_image'),
            'project_url': portfolio_data.get('project_url'),
            'project_url_behance': portfolio_data.get('project_url_behance'),
            'category': {
                'name': portfolio_data.get('category_name', 'Uncategorized'),
                'slug': portfolio_data.get('category_slug', 'uncategorized')
            }
        }
        
        cursor.execute("SELECT * FROM gallery WHERE portfolio_id = %s ORDER BY id ASC", (id,))
        gallery_items = cursor.fetchall()
        
        return render_template('portofolio1.html', 
                            portfolio=portfolio,
                            gallery_items=gallery_items,
                            referrer=request.referrer or 'direct')
        
    except Exception as e:
        print(f"Error fetching portfolio details: {e}")
        return render_template('errors/500.html'), 500
    finally:
        cursor.close()
        conn.close()

def calculate_file_hash(file):
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    file.seek(0)  # Ensure we're at the start of the file
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)  # Reset file pointer
    return sha256_hash.hexdigest()

@app.route('/gallery', methods=['GET', 'POST'])
@login_required
@is_admin
def gallery_management():
    if request.method == 'POST':
        if 'add_gallery_item' in request.form:
            portfolio_id = request.form.get('portfolio_id')
            if not portfolio_id:
                flash('Portfolio ID is required', 'danger')
                return redirect(request.url)
            
            files = request.files.getlist('files')
            if not files or files[0].filename == '':
                flash('No files selected', 'danger')
                return redirect(request.url)
            
            uploaded_files = []
            for file in files:
                if file and allowed_file(file.filename):
                    try:
                        # Hitung hash file
                        file_hash = calculate_file_hash(file)
                        
                        # Cek apakah file sudah ada
                        existing = Gallery.get_by_hash(file_hash)
                        if existing:
                            flash(f'File {file.filename} already exists in gallery', 'warning')
                            continue
                        
                        # Buat nama file yang aman
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['GALLERY_UPLOAD_FOLDER'], filename)
                        
                        # Simpan file ke folder gallery khusus
                        file.save(filepath)
                        # Set permission file
                        os.chmod(filepath, 0o644)
                        
                        # Buat item gallery
                        new_item = Gallery(
                            portfolio_id=portfolio_id,
                            file_name=filename,
                            file_path=filepath,
                            file_hash=file_hash,
                            file_type=file.content_type,
                            uploaded_by=current_user.id
                        )
                        new_item.save()
                        uploaded_files.append(filename)
                        
                    except PermissionError as e:
                        flash(f'Permission denied saving {file.filename}: {str(e)}', 'danger')
                        continue
                    except Exception as e:
                        flash(f'Error processing {file.filename}: {str(e)}', 'danger')
                        continue
            
            if uploaded_files:
                flash(f'Successfully uploaded {len(uploaded_files)} files', 'success')
            return redirect(url_for('gallery_management'))
        
        elif 'delete_gallery_item' in request.form:
            # Handle gallery item deletion
            item_id = request.form.get('item_id')
            item = Gallery.get_by_id_with_portfolio(item_id)  # Use existing method
            
            if item:
                # Delete file from filesystem
                if os.path.exists(item.file_path):
                    os.remove(item.file_path)
                
                item.delete()
                flash('Gallery item deleted successfully', 'success')
            
            return redirect(url_for('gallery_management'))
    
    # Get all gallery items with portfolio info
    gallery_items = Gallery.get_all_with_portfolio()
    portfolios = Portfolio.get_all()  # For dropdown in upload form
    
    return render_template('gallery_management.html', 
                         gallery_items=gallery_items,
                         portfolios=portfolios)

@app.route('/gallery/<int:item_id>')
@login_required
@is_admin
def get_gallery_item(item_id):
    item = Gallery.get_by_id_with_portfolio(item_id)
    if item:
        return jsonify({
            'id': item.id,
            'portfolio_id': item.portfolio_id,
            'portfolio_title': item.portfolio_title,
            'file_name': item.file_name,
            'file_path': item.file_path,
            'file_type': item.file_type,
            'uploaded_by': item.uploaded_by_name,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'error': 'Gallery item not found'}), 404

@app.route('/gallery/preview/<path:filename>')
@login_required
def gallery_preview(filename):
    return send_from_directory(app.config['GALLERY_UPLOAD_FOLDER'], filename)


@app.route('/testimonials', methods=['GET', 'POST'])
@login_required
@is_admin
def testimonials_management():
    if request.method == 'POST':
        try:
            # Handle file upload - hanya jika file diunggah
            photo = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'testimonials')
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    photo = filename

            # Create testimonial
            testimonial = Testimonial(
                name=request.form.get('name'),
                company=request.form.get('company'),
                message=request.form.get('message'),
                photo=photo,  # Bisa None jika tidak ada foto
                is_active=request.form.get('is_active') == '1'
            )
            
            testimonial.save()
            flash('Testimonial added successfully', 'success')
        except Exception as e:
            flash(f'Error creating testimonial: {str(e)}', 'danger')
        
        return redirect(url_for('testimonials_management'))
    
    testimonials = Testimonial.get_all()
    return render_template('testimonials_management.html', testimonials=testimonials)

@app.route('/testimonials/<int:testimonial_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@is_admin
def testimonial_detail(testimonial_id):
    try:
        if request.method == 'GET':
            testimonial = Testimonial.get_by_id(testimonial_id)
            if testimonial:
                return jsonify(testimonial.to_dict())
            return jsonify({'error': 'Testimonial not found'}), 404
        
        elif request.method == 'PUT':
            testimonial = Testimonial.get_by_id(testimonial_id)
            if not testimonial:
                return jsonify({'error': 'Testimonial not found'}), 404

            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
                if 'is_active' in data:
                    data['is_active'] = data['is_active'] == '1'

            # Update fields
            testimonial.name = data.get('name', testimonial.name)
            testimonial.company = data.get('company', testimonial.company)
            testimonial.message = data.get('message', testimonial.message)
            testimonial.is_active = data.get('is_active', testimonial.is_active)

            # Handle file upload if exists
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Delete old photo if exists
                    testimonial.delete_photo()
                    
                    # Save new photo
                    filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
                    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'testimonials')
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    testimonial.photo = filename
                elif file.filename == '':
                    # Jika file diupload tapi kosong (tidak memilih file), pertahankan foto lama
                    pass
                else:
                    # Jika file tidak valid
                    return jsonify({'status': 'error', 'error': 'Invalid file type'}), 400

            testimonial.save()
            return jsonify({'status': 'success', 'message': 'Testimonial updated successfully'}), 200
        
        elif request.method == 'DELETE':
            testimonial = Testimonial.get_by_id(testimonial_id)
            if not testimonial:
                return jsonify({'error': 'Testimonial not found'}), 404
            
            # Hapus foto terkait sebelum menghapus testimonial
            testimonial.delete_photo()
            testimonial.delete()
            return jsonify({'status': 'success', 'message': 'Testimonial deleted successfully'}), 200

    except Exception as e:
        app.logger.error(f"Error in testimonial_detail: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
    
@app.route('/seo_analysis')
@login_required
@is_admin
def seo_analysis():
    # Gunakan method yang sudah ada
    services = Service.get_all_with_category()
    
    # Hitung statistik SEO secara manual
    seo_stats = {
        'total_services': len(services),
        'services_with_meta_title': sum(1 for s in services if s.meta_title),
        'services_with_meta_description': sum(1 for s in services if s.meta_description),
        'services_with_images': sum(1 for s in services if s.featured_image),
        'avg_title_length': sum(len(s.title) for s in services)/len(services) if services else 0,
        'avg_meta_desc_length': sum(len(s.meta_description) for s in services if s.meta_description)/len([s for s in services if s.meta_description]) if [s for s in services if s.meta_description] else 0,
        'avg_seo_score': 0  # Akan dihitung
    }
    
    # Hitung SEO score untuk setiap service
    for service in services:
        service.seo_score = calculate_seo_score(service)
    
    # Hitung rata-rata SEO score
    if services:
        seo_stats['avg_seo_score'] = sum(s.seo_score for s in services)/len(services)
    
    return render_template('seo_analysis.html', services=services, seo_stats=seo_stats)

def calculate_seo_score(service):
    score = 0
    
    # Title exists and has proper length
    if service.title and len(service.title) >= 30 and len(service.title) <= 60:
        score += 20
    
    # Meta description exists and has proper length
    if service.meta_description and len(service.meta_description) >= 50 and len(service.meta_description) <= 160:
        score += 20
    
    # Has featured image
    if service.featured_image:
        score += 15
    
    # Has detail image
    if service.detail_service_image:
        score += 10
    
    # Has category
    if service.category_id:
        score += 10
    
    # Content length
    if service.full_description:
        word_count = len(service.full_description.split())
        if word_count >= 300:
            score += 15
        elif word_count >= 150:
            score += 10
        else:
            score += 5
    
    # Is active
    if service.is_active:
        score += 10
    
    return score

@app.template_filter('escapejs')
# Tambahkan custom filter
def escapejs(value):
    """Escape string for JavaScript usage."""
    if value is None:
        return ''
    return (str(value)
            .replace('\\', '\\\\')
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
            .replace('\t', '\\t'))

app.jinja_env.filters['escapejs'] = escapejs

if __name__ == '__main__':
    app.run(debug=True)