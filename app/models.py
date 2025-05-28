import bcrypt
from datetime import datetime
import mysql.connector
from flask_login import UserMixin
from werkzeug.utils import secure_filename
from flask import current_app
from time import time
from flask import url_for
from database import get_db_connection
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(UserMixin):
    def __init__(self, id=None, username='', fullname='', email='', password='', role='user', is_admin=False, created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.fullname = fullname
        self.email = email
        self.password = password
        self.role = role
        self.is_admin = is_admin
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users")
            users = []
            for row in cursor.fetchall():
                user = User(
                    id=row['id'],
                    username=row['username'],
                    fullname=row['fullname'],
                    email=row['email'],
                    password=row['password'],
                    role=row.get('role', 'user'),
                    is_admin=bool(row.get('is_admin', 0)),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
                users.append(user)
            return users
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id):
        conn = User.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    fullname=row['fullname'],
                    email=row['email'],
                    password=row['password'],
                    role=row.get('role', 'user'),
                    is_admin=bool(row.get('is_admin', 0)),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
            return None
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def get_by_email_or_username(identifier):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (identifier, identifier))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    username=row['username'],
                    fullname=row['fullname'],
                    email=row['email'],
                    password=row['password'],
                    role=row.get('role', 'user'),
                    is_admin=bool(row.get('is_admin', 0)),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
            return None
        finally:
            cursor.close()
            conn.close()

    def check_password(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        except Exception as e:
            print(f"Error verifying password: {e}")
            return False

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.password = hashed_password.decode('utf-8')

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id is None:  # New user
                now = datetime.now()
                cursor.execute(
                    "INSERT INTO users (username, fullname, email, password, role, is_admin, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (self.username, self.fullname, self.email, self.password, 
                     self.role, int(self.is_admin), now, now))
                self.id = cursor.lastrowid
            else:  # Update existing user
                now = datetime.now()
                cursor.execute(
                    "UPDATE users SET username = %s, fullname = %s, email = %s, "
                    "password = %s, role = %s, is_admin = %s, updated_at = %s WHERE id = %s",
                    (self.username, self.fullname, self.email, self.password, 
                     self.role, int(self.is_admin), now, self.id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def delete(self):
        if self.id is None:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (self.id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def __repr__(self):
        return f'<User {self.username}>'
    
class TeamMember:
    def __init__(self, id=None, nama=None, divisi=None, subdivisi=None, level=None, file_name=None, file_path=None, file_type=None, uploaded_by=None, created_at=None):
        self.id = id
        self.nama = nama
        self.divisi = divisi
        self.subdivisi = subdivisi
        self.file_name = file_name
        self.file_path = file_path
        self.file_type = file_type
        self.level = level
        self.uploaded_by = uploaded_by
        self.created_at = created_at

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM media ORDER BY created_at DESC")
            members = []
            for row in cursor.fetchall():
                member = TeamMember(
                    id=row['id'],
                    nama=row['nama'],
                    divisi=row['divisi'],
                    subdivisi=row.get('subdivisi', ''),
                    file_name=row['file_name'],
                    file_path=row['file_path'],
                    file_type=row.get('file_type'),
                    level=row['level'], 
                    uploaded_by=row.get('uploaded_by'),
                    created_at=row.get('created_at')
                )
                members.append(member)
            return members
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(member_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM media WHERE id = %s", (member_id,))
            row = cursor.fetchone()
            if row:
                return TeamMember(
                    id=row['id'],
                    nama=row['nama'],
                    divisi=row['divisi'],
                    subdivisi=row.get('subdivisi', ''),
                    file_name=row['file_name'],
                    file_path=row['file_path'],
                    file_type=row.get('file_type'),
                    level=row['level'],  
                    uploaded_by=row.get('uploaded_by'),
                    created_at=row.get('created_at')
                )
            return None
        finally:
            cursor.close()
            conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id is None:  # Insert new
                cursor.execute(
                    "INSERT INTO media (nama, divisi, subdivisi, level, file_name, file_path, file_type, uploaded_by, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                    (self.nama, self.divisi, self.subdivisi, self.level, self.file_name, 
                     self.file_path, self.file_type, self.uploaded_by)
                )
                self.id = cursor.lastrowid
            else:  # Update existing
                cursor.execute(
                    "UPDATE media SET nama = %s, divisi = %s, subdivisi = %s, level=%s, file_name = %s, "
                    "file_path = %s, file_type = %s, uploaded_by = %s WHERE id = %s",
                    (self.nama, self.divisi, self.subdivisi, self.level, self.file_name, 
                     self.file_path, self.file_type, self.uploaded_by, self.id)
                )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def delete(self):
        if self.id is None:
            return False
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM media WHERE id = %s", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
            
class PortfolioCategory:
    def __init__(self, id=None, name=None, slug=None, description=None, created_at=None):
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.created_at = created_at

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM portfolio_categories ORDER BY created_at DESC")
            categories = []
            for row in cursor.fetchall():
                category = PortfolioCategory(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    description=row.get('description', ''),
                    created_at=row.get('created_at')
                )
                categories.append(category)
            return categories
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(category_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM portfolio_categories WHERE id = %s", (category_id,))
            row = cursor.fetchone()
            if row:
                return PortfolioCategory(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    description=row.get('description', ''),
                    created_at=row.get('created_at')
                )
            return None
        finally:
            cursor.close()
            conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id is None:  # New category
                cursor.execute(
                    "INSERT INTO portfolio_categories (name, slug, description, created_at) "
                    "VALUES (%s, %s, %s, NOW())",
                    (self.name, self.slug, self.description)
                )
                self.id = cursor.lastrowid
            else:  # Update existing category
                cursor.execute(
                    "UPDATE portfolio_categories SET name = %s, slug = %s, description = %s WHERE id = %s",
                    (self.name, self.slug, self.description, self.id)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def delete(self):
        if self.id is None:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM portfolio_categories WHERE id = %s", (self.id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
               
class Portfolio:
    def __init__(self, id=None, title=None, slug=None, client_name=None, project_date=None, 
                 description=None, idea=None, cover_image=None, project_url=None, project_url_behance=None,
                 user_id=None, category_id=None, is_featured=None, status=None, created_at=None, category_name=None, meta_tittle=None, meta_desc=None):
        self.id = id
        self.title = title
        self.slug = slug
        self.client_name = client_name
        self.project_date = project_date
        self.description = description
        self.idea = idea
        self.cover_image = cover_image
        self.project_url = project_url
        self.project_url_behance = project_url_behance
        self.user_id = user_id
        self.category_id = category_id
        self.is_featured = is_featured
        self.status = status
        self.created_at = created_at
        self.meta_tittle = meta_tittle
        self.meta_desc = meta_desc

    def to_dict(self):
        """Convert Portfolio object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'client_name': self.client_name,
            'project_date': self.project_date.strftime('%Y-%m-%d') if self.project_date else None,
            'description': self.description,
            'idea': self.idea,
            'cover_image': self.cover_image,
            'project_url': self.project_url,
            'project_url_behance': self.project_url_behance,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'is_featured': self.is_featured,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'meta_tittle': self.meta_tittle,
            'meta_desc': self.meta_desc
        }

    @staticmethod
    def get_all():
        """Get all portfolios ordered by creation date (newest first)"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT p.*, c.name as category_name 
                FROM portfolio p
                LEFT JOIN portfolio_categories c ON p.category_id = c.id
                ORDER BY p.created_at DESC
            """)
            return [Portfolio(**row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching all portfolios: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(portfolio_id):
        """Get a single portfolio by ID"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT p.*, c.name as category_name 
                FROM portfolio p
                LEFT JOIN portfolio_categories c ON p.category_id = c.id
                WHERE p.id = %s
            """, (portfolio_id,))
            row = cursor.fetchone()
            return Portfolio(**row) if row else None
        except Exception as e:
            print(f"Error fetching portfolio {portfolio_id}: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def save(self):
        """Save the portfolio (insert new or update existing)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id is None:  # New portfolio
                cursor.execute("""
                    INSERT INTO portfolio 
                    (title, slug, client_name, project_date, description, idea, 
                     cover_image, project_url, project_url_behance, user_id, category_id, is_featured, status, meta_tittle, meta_desc, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.title, 
                    self.slug or slugify(self.title),
                    self.client_name, 
                    self.project_date, 
                    self.description,
                    self.idea, 
                    self.cover_image, 
                    self.project_url,
                    self.project_url_behance, 
                    self.user_id, 
                    self.category_id,
                    self.is_featured, 
                    self.status,
                    self.meta_tittle,
                    self.meta_desc,
                    self.created_at or datetime.now()
                ))
                self.id = cursor.lastrowid
            else:  # Update existing portfolio
                cursor.execute("""
                    UPDATE portfolio SET 
                    title = %s, slug = %s, client_name = %s, project_date = %s, 
                    description = %s, idea = %s, cover_image = %s, project_url = %s, project_url_behance = %s,
                    user_id = %s, category_id = %s, is_featured = %s, status = %s, meta_tittle = %s, meta_desc = %s
                    WHERE id = %s
                """, (
                    self.title,
                    self.slug or slugify(self.title),
                    self.client_name,
                    self.project_date,
                    self.description,
                    self.idea,
                    self.cover_image,
                    self.project_url,
                    self.project_url_behance,
                    self.user_id,
                    self.category_id,
                    self.is_featured,
                    self.status,
                    self.meta_tittle,
                    self.meta_desc,
                    self.id
                ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error saving portfolio: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def delete(self):
        """Delete the portfolio from database"""
        if self.id is None:
            return False
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM portfolio WHERE id = %s", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting portfolio {self.id}: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def slugify(text):
    """Helper function to create slugs from text"""
    if not text:
        return ""
    return text.lower().strip().replace(" ", "-")
            
class Gallery:
    def __init__(self, id=None, portfolio_id=None, file_name=None, file_path=None, 
                 file_hash=None, file_type=None, uploaded_by=None, created_at=None,
                 portfolio_title=None, uploaded_by_name=None):
        self.id = id
        self.portfolio_id = portfolio_id
        self.file_name = file_name
        self.file_path = file_path
        self.file_hash = file_hash
        self.file_type = file_type
        self.uploaded_by = uploaded_by
        self.created_at = created_at
        self.portfolio_title = portfolio_title
        self.uploaded_by_name = uploaded_by_name

    @staticmethod
    def get_all_with_portfolio():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT g.*, p.title as portfolio_title, u.username as uploaded_by_name
                FROM gallery g
                LEFT JOIN portfolio p ON g.portfolio_id = p.id
                LEFT JOIN users u ON g.uploaded_by = u.id
                ORDER BY g.created_at DESC
            """
            cursor.execute(query)
            items = []
            for row in cursor.fetchall():
                item = Gallery(
                    id=row['id'],
                    portfolio_id=row['portfolio_id'],
                    file_name=row['file_name'],
                    file_path=row['file_path'],
                    file_hash=row['file_hash'],
                    file_type=row['file_type'],
                    uploaded_by=row['uploaded_by'],
                    created_at=row['created_at'],
                    portfolio_title=row['portfolio_title'],
                    uploaded_by_name=row['uploaded_by_name']
                )
                items.append(item)
            return items
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id_with_portfolio(item_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT g.*, p.title as portfolio_title, u.username as uploaded_by_name
                FROM gallery g
                LEFT JOIN portfolio p ON g.portfolio_id = p.id
                LEFT JOIN users u ON g.uploaded_by = u.id
                WHERE g.id = %s
            """
            cursor.execute(query, (item_id,))
            row = cursor.fetchone()
            if row:
                return Gallery(
                    id=row['id'],
                    portfolio_id=row['portfolio_id'],
                    file_name=row['file_name'],
                    file_path=row['file_path'],
                    file_hash=row['file_hash'],
                    file_type=row['file_type'],
                    uploaded_by=row['uploaded_by'],
                    created_at=row['created_at'],
                    portfolio_title=row['portfolio_title'],
                    uploaded_by_name=row['uploaded_by_name']
                )
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_hash(file_hash):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM gallery WHERE file_hash = %s", (file_hash,))
            row = cursor.fetchone()
            if row:
                return Gallery(
                    id=row['id'],
                    portfolio_id=row['portfolio_id'],
                    file_name=row['file_name'],
                    file_path=row['file_path'],
                    file_hash=row['file_hash'],
                    file_type=row['file_type'],
                    uploaded_by=row['uploaded_by'],
                    created_at=row['created_at']
                )
            return None
        finally:
            cursor.close()
            conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO gallery (portfolio_id, file_name, file_path, file_hash, file_type, uploaded_by) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (self.portfolio_id, self.file_name, self.file_path, 
                 self.file_hash, self.file_type, self.uploaded_by)
            )
            self.id = cursor.lastrowid
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def delete(self):
        if self.id is None:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM gallery WHERE id = %s", (self.id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
            
class ServiceCategory:
    def __init__(self, id=None, name=None, slug=None, description=None, created_at=None):
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.created_at = created_at

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM service_categories ORDER BY created_at DESC")
            categories = []
            for row in cursor.fetchall():
                category = ServiceCategory(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    description=row['description'],
                    created_at=row['created_at']
                )
                categories.append(category)
            return categories
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(category_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM service_categories WHERE id = %s", (category_id,))
            row = cursor.fetchone()
            if row:
                return ServiceCategory(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug'],
                    description=row['description'],
                    created_at=row['created_at']
                )
            return None
        finally:
            cursor.close()
            conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id is None:  # Insert new
                cursor.execute(
                    "INSERT INTO service_categories (name, slug, description, created_at) "
                    "VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
                    (self.name, self.slug, self.description)
                )
                self.id = cursor.lastrowid
            else:  # Update existing
                cursor.execute(
                    "UPDATE service_categories SET name = %s, slug = %s, description = %s "
                    "WHERE id = %s",
                    (self.name, self.slug, self.description, self.id)
                )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error saving category: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def delete(self):
        if self.id is None:
            return False
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM service_categories WHERE id = %s", (self.id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Error deleting category {self.id}: {e}")
            return False
        finally:
            cursor.close()
            conn.close()


class Service:
    def __init__(self, id=None, title=None, slug=None, short_description=None,
                 full_description=None, icon_feature1=None, text_feature1=None, nama_feature1=None,
                 icon2=None, nama_feature2=None, text_feature2=None, featured_image=None, 
                 detail_service_image=None, is_active=None, display_order=None, created_at=None, 
                 meta_title=None, meta_description=None, category_id=None, user_id=None, 
                 category_name=None, username=None):
        self.id = id
        self.title = title
        self.slug = slug
        self.short_description = short_description
        self.full_description = full_description
        self.icon_feature1 = icon_feature1
        self.text_feature1 = text_feature1
        self.nama_feature1 = nama_feature1
        self.icon2 = icon2
        self.nama_feature2 = nama_feature2
        self.text_feature2 = text_feature2
        self.featured_image = featured_image
        self.detail_service_image = detail_service_image
        self.is_active = is_active
        self.display_order = display_order
        self.created_at = created_at
        self.meta_title = meta_title
        self.meta_description = meta_description
        self.category_name = category_name
        self.username = username
        self.category_id = category_id if category_id is not None else None
        self.user_id = user_id if user_id is not None else None

    @staticmethod
    def get_all_with_category():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT s.*, sc.name as category_name, u.username
                FROM services s
                LEFT JOIN service_categories sc ON s.category_id = sc.id
                LEFT JOIN users u ON s.user_id = u.id
                ORDER BY s.display_order, s.title
            """
            cursor.execute(query)
            services = []
            for row in cursor.fetchall():
                service = Service(
                    id=row['id'],
                    title=row['title'],
                    slug=row['slug'],
                    short_description=row['short_description'],
                    full_description=row['full_description'],
                    icon_feature1=row['icon_feature1'],
                    text_feature1=row['text_feature1'],
                    nama_feature1=row['nama_feature1'],
                    icon2=row['icon2'],
                    nama_feature2=row['nama_feature2'],
                    text_feature2=row['text_feature2'],
                    featured_image=row['featured_image'],
                    detail_service_image=row['detail_service_image'],
                    is_active=row['is_active'],
                    display_order=row['display_order'],
                    created_at=row['created_at'],
                    meta_title=row['meta_title'],
                    meta_description=row['meta_description'],
                    category_id=row['category_id'],
                    user_id=row['user_id'],
                    category_name=row.get('category_name'),
                    username=row.get('username')
                )
                services.append(service)
            return services
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(service_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT s.*, sc.name as category_name, u.username 
                FROM services s
                LEFT JOIN service_categories sc ON s.category_id = sc.id
                LEFT JOIN users u ON s.user_id = u.id
                WHERE s.id = %s
            """, (service_id,))
            row = cursor.fetchone()
            if row:
                return Service(
                    id=row['id'],
                    title=row['title'],
                    slug=row['slug'],
                    short_description=row['short_description'],
                    full_description=row['full_description'],
                    icon_feature1=row['icon_feature1'],
                    text_feature1=row['text_feature1'],
                    nama_feature1=row['nama_feature1'],
                    icon2=row['icon2'],
                    nama_feature2=row['nama_feature2'],
                    text_feature2=row['text_feature2'],
                    featured_image=row['featured_image'],
                    detail_service_image=row['detail_service_image'],
                    is_active=row['is_active'],
                    display_order=row['display_order'],
                    created_at=row['created_at'],
                    meta_title=row['meta_title'],
                    meta_description=row['meta_description'],
                    category_id=row['category_id'],
                    user_id=row['user_id'],
                    category_name=row.get('category_name'),
                    username=row.get('username')
                )
            return None
        finally:
            cursor.close()
            conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id is None:  # Insert new
                cursor.execute(
                    "INSERT INTO services (title, slug, short_description, full_description, "
                    "icon_feature1, text_feature1, nama_feature1, icon2, nama_feature2, text_feature2, "
                    "featured_image, detail_service_image, is_active, display_order, meta_title, "
                    "meta_description, category_id, user_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (self.title, self.slug, self.short_description, self.full_description,
                     self.icon_feature1, self.text_feature1, self.nama_feature1, self.icon2,
                     self.nama_feature2, self.text_feature2, self.featured_image, 
                     self.detail_service_image, self.is_active, self.display_order,
                     self.meta_title, self.meta_description, self.category_id, self.user_id)
                )
                self.id = cursor.lastrowid
            else:  # Update existing
                cursor.execute(
                    "UPDATE services SET title = %s, slug = %s, short_description = %s, "
                    "full_description = %s, icon_feature1 = %s, text_feature1 = %s, nama_feature1 = %s, "
                    "icon2 = %s, nama_feature2 = %s, text_feature2 = %s, featured_image = %s, "
                    "detail_service_image = %s, is_active = %s, display_order = %s, meta_title = %s, "
                    "meta_description = %s, category_id = %s, user_id = %s WHERE id = %s",
                    (self.title, self.slug, self.short_description, self.full_description,
                     self.icon_feature1, self.text_feature1, self.nama_feature1, self.icon2,
                     self.nama_feature2, self.text_feature2, self.featured_image,
                     self.detail_service_image, self.is_active, self.display_order,
                     self.meta_title, self.meta_description, self.category_id, self.user_id, self.id)
                )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error saving service: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def update(self, title=None, slug=None, short_description=None, full_description=None,
               icon_feature1=None, text_feature1=None, nama_feature1=None, icon2=None,
               nama_feature2=None, text_feature2=None, featured_image=None, 
               detail_service_image=None, is_active=None, display_order=None,
               meta_title=None, meta_description=None, category_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE services SET title = %s, slug = %s, short_description = %s, "
                "full_description = %s, icon_feature1 = %s, text_feature1 = %s, nama_feature1 = %s, "
                "icon2 = %s, nama_feature2 = %s, text_feature2 = %s, featured_image = %s, "
                "detail_service_image = %s, is_active = %s, display_order = %s, meta_title = %s, "
                "meta_description = %s, category_id = %s WHERE id = %s",
                (title, slug, short_description, full_description, icon_feature1, text_feature1,
                 nama_feature1, icon2, nama_feature2, text_feature2, featured_image,
                 detail_service_image, is_active, display_order, meta_title, meta_description,
                 category_id, self.id)
            )
            conn.commit()
            # Update object properties
            self.title = title if title is not None else self.title
            self.slug = slug if slug is not None else self.slug
            self.short_description = short_description if short_description is not None else self.short_description
            self.full_description = full_description if full_description is not None else self.full_description
            self.icon_feature1 = icon_feature1 if icon_feature1 is not None else self.icon_feature1
            self.text_feature1 = text_feature1 if text_feature1 is not None else self.text_feature1
            self.nama_feature1 = nama_feature1 if nama_feature1 is not None else self.nama_feature1
            self.icon2 = icon2 if icon2 is not None else self.icon2
            self.nama_feature2 = nama_feature2 if nama_feature2 is not None else self.nama_feature2
            self.text_feature2 = text_feature2 if text_feature2 is not None else self.text_feature2
            self.featured_image = featured_image if featured_image is not None else self.featured_image
            self.detail_service_image = detail_service_image if detail_service_image is not None else self.detail_service_image
            self.is_active = is_active if is_active is not None else self.is_active
            self.display_order = display_order if display_order is not None else self.display_order
            self.meta_title = meta_title if meta_title is not None else self.meta_title
            self.meta_description = meta_description if meta_description is not None else self.meta_description
            self.category_id = category_id if category_id is not None else self.category_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'short_description': self.short_description,
            'full_description': self.full_description,
            'icon_feature1': self.icon_feature1,
            'text_feature1': self.text_feature1,
            'nama_feature1': self.nama_feature1,
            'icon2': self.icon2,
            'nama_feature2': self.nama_feature2,
            'text_feature2': self.text_feature2,
            'featured_image': self.featured_image,
            'detail_service_image': self.detail_service_image,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'category_name': self.category_name,
            'username': self.username
        }
        
class Testimonial:
    def __init__(self, id=None, name='', company='', message='', photo='', is_active=False, created_at=None):
        self.id = id
        self.name = name
        self.company = company
        self.message = message
        self.photo = photo
        self.is_active = is_active
        self.created_at = created_at

    @staticmethod
    def get_by_id(testimonial_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM testimonials WHERE id = %s", (testimonial_id,))
            row = cursor.fetchone()
            if row:
                return Testimonial(
                    id=row['id'],
                    name=row['name'],
                    company=row['company'],
                    message=row['message'],
                    photo=row['photo'] if row['photo'] else None,  # Handle NULL
                    is_active=bool(row.get('is_active', 0)),
                    created_at=row.get('created_at')
                )
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM testimonials ORDER BY created_at DESC")
            testimonials = []
            for row in cursor.fetchall():
                testimonial = Testimonial(
                    id=row['id'],
                    name=row['name'],
                    company=row['company'],
                    message=row['message'],
                    photo=row['photo'] if row['photo'] else None,  # Handle NULL
                    is_active=bool(row.get('is_active', 0)),
                    created_at=row.get('created_at')
                )
                testimonials.append(testimonial)
            return testimonials
        finally:
            cursor.close()
            conn.close()

    def save_photo(self, photo_file):
        if photo_file and allowed_file(photo_file.filename):
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'testimonials')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(photo_file.filename)
            unique_filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(upload_dir, unique_filename)
            
            # Save new file
            photo_file.save(filepath)
            
            # Delete old photo if exists
            if self.photo:
                old_filepath = os.path.join(upload_dir, self.photo)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            self.photo = unique_filename
            return True
        return False

    def get_photo_url(self):
        if not self.photo:
            return url_for('static', filename='images/default-avatar.jpg')
        return url_for('static', filename=f'uploads/testimonials/{self.photo}')

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            if self.id is None:  # New testimonial
                cursor.execute(
                    "INSERT INTO testimonials (name, company, message, photo, is_active, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (self.name, self.company, self.message, self.photo if self.photo else None, int(self.is_active), now)
                )
                self.id = cursor.lastrowid
            else:  # Update existing testimonial
                cursor.execute(
                    "UPDATE testimonials SET name = %s, company = %s, message = %s, "
                    "photo = %s, is_active = %s WHERE id = %s",
                    (self.name, self.company, self.message, self.photo if self.photo else None, int(self.is_active), self.id)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()


    def delete(self):
        if self.id is None:
            return False
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Delete photo file if exists
            if self.photo:
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'testimonials')
                filepath = os.path.join(upload_dir, self.photo)
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            # Delete from database
            cursor.execute("DELETE FROM testimonials WHERE id = %s", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        
    def get_photo_url(self):
        if not self.photo:
            return None  # Kembalikan None jika tidak ada foto
        return url_for('static', filename=f'uploads/testimonials/{self.photo}')
    
    def delete_photo(self):
        if self.photo:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'testimonials')
            filepath = os.path.join(upload_dir, self.photo)
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'company': self.company,
            'message': self.message,
            'photo': self.photo,
            'photo_url': self.get_photo_url(),  # Hapus parameter self.photo
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }