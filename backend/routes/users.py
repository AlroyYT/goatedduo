from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash
from models.user import User
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# Admin role check decorator
def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        # Check if user has admin role
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Admin privileges required'
            }), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@users_bp.route('/', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Limit maximum per_page to avoid overload
        per_page = min(per_page, 100)
        
        # Query users with pagination
        users_pagination = User.query.paginate(page=page, per_page=per_page)
        
        # Prepare response data
        users_data = []
        for user in users_pagination.items:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'age': user.age,
                'income': user.income,
                'risk_tolerance': user.risk_tolerance,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            })
        
        # Return paginated results
        return jsonify({
            'status': 'success',
            'users': users_data,
            'pagination': {
                'page': users_pagination.page,
                'per_page': users_pagination.per_page,
                'total_pages': users_pagination.pages,
                'total_items': users_pagination.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching users'
        }), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get specific user details"""
    try:
        # Get current user claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        # Check if admin or same user
        is_admin = claims.get('role') == 'admin'
        is_same_user = int(current_user_id) == user_id
        
        if not (is_admin or is_same_user):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized to access this user profile'
            }), 403
        
        # Find user
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Return user data
        return jsonify({
            'status': 'success',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'age': user.age,
                'income': user.income,
                'risk_tolerance': user.risk_tolerance,
                'investment_horizon': user.investment_horizon,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user (ID: {user_id}): {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching user'
        }), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user details"""
    try:
        # Get current user claims
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        # Check if admin or same user
        is_admin = claims.get('role') == 'admin'
        is_same_user = int(current_user_id) == user_id
        
        if not (is_admin or is_same_user):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized to update this user'
            }), 403
        
        # Find user
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Define updatable fields based on role
        if is_admin:
            # Admin can update all fields including role
            updatable_fields = [
                'email', 'first_name', 'last_name', 'role',
                'age', 'income', 'risk_tolerance', 'investment_horizon'
            ]
        else:
            # Regular users can update their own profile but not role
            updatable_fields = [
                'first_name', 'last_name', 'age', 
                'income', 'risk_tolerance', 'investment_horizon'
            ]
        
        # Update allowed fields
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Handle password update separately (if provided)
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])
        
        # Save changes
        user.save()
        
        logger.info(f"User updated (ID: {user_id})")
        
        # Return updated user
        return jsonify({
            'status': 'success',
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'age': user.age,
                'income': user.income,
                'risk_tolerance': user.risk_tolerance,
                'investment_horizon': user.investment_horizon,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user (ID: {user_id}): {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating user'
        }), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        # Find user
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Store user email for logging
        user_email = user.email
        
        # Delete user
        user.delete()
        
        logger.info(f"User deleted: {user_email} (ID: {user_id})")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': f'User {user_id} deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting user (ID: {user_id}): {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting user'
        }), 500

@users_bp.route('/search', methods=['GET'])
@admin_required
def search_users():
    """Search users by criteria (admin only)"""
    try:
        # Get search parameters
        email = request.args.get('email')
        name = request.args.get('name')
        risk = request.args.get('risk_tolerance')
        
        # Start with base query
        query = User.query
        
        # Apply filters
        if email:
            query = query.filter(User.email.ilike(f'%{email}%'))
        
        if name:
            query = query.filter(
                (User.first_name.ilike(f'%{name}%')) | 
                (User.last_name.ilike(f'%{name}%'))
            )
        
        if risk:
            query = query.filter(User.risk_tolerance == risk)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Limit maximum per_page to avoid overload
        per_page = min(per_page, 100)
        
        # Execute query with pagination
        users_pagination = query.paginate(page=page, per_page=per_page)
        
        # Prepare response data
        users_data = []
        for user in users_pagination.items:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'age': user.age,
                'risk_tolerance': user.risk_tolerance,
                'created_at': user.created_at.isoformat()
            })
        
        # Return search results
        return jsonify({
            'status': 'success',
            'users': users_data,
            'pagination': {
                'page': users_pagination.page,
                'per_page': users_pagination.per_page,
                'total_pages': users_pagination.pages,
                'total_items': users_pagination.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while searching users'
        }), 500

@users_bp.route('/stats', methods=['GET'])
@admin_required
def get_user_stats():
    """Get user statistics (admin only)"""
    try:
        # Get total user count
        total_users = User.query.count()
        
        # Get users by risk tolerance
        risk_stats = {}
        for risk in ['low', 'moderate', 'high']:
            risk_stats[risk] = User.query.filter_by(risk_tolerance=risk).count()
        
        # Get active/inactive stats (users who have logged in recently)
        # This would require an additional 'last_login' field in the User model
        
        # Return stats
        return jsonify({
            'status': 'success',
            'stats': {
                'total_users': total_users,
                'risk_distribution': risk_stats,
                # Add more stats as needed
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching user statistics'
        }), 500