from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from models.user import User
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
@auth_bp.route('', methods=['GET'])
def auth_root():
    return jsonify({
        'status': 'success',
        'message': 'Auth service is up'
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        # Get user data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'status': 'error',
                'message': 'User with this email already exists'
            }), 409
        
        # Create new user
        new_user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            # Optional fields
            age=data.get('age'),
            income=data.get('income'),
            risk_tolerance=data.get('risk_tolerance', 'moderate'),
            investment_horizon=data.get('investment_horizon')
        )
        
        # Save to database
        new_user.save()
        
        logger.info(f"New user registered: {data['email']}")
        
        # Return success response (without sending password back)
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'created_at': new_user.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during registration'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and provide access tokens"""
    try:
        # Get login credentials
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
        
        # Create access and refresh tokens
        access_expiry = datetime.timedelta(hours=1)  # Short-lived token
        refresh_expiry = datetime.timedelta(days=30)  # Long-lived token
        
        # Add user claims to token
        additional_claims = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=access_expiry
        )
        
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=refresh_expiry
        )
        
        logger.info(f"User logged in: {data['email']}")
        
        # Return tokens
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during login'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        # Get current user identity from refresh token
        current_user_id = get_jwt_identity()
        
        # Get additional claims from current token
        claims = get_jwt()
        
        # Create new access token
        access_expiry = datetime.timedelta(hours=1)
        
        # Preserve user claims
        additional_claims = {
            'user_id': claims.get('user_id'),
            'email': claims.get('email'),
            'role': claims.get('role')
        }
        
        new_access_token = create_access_token(
            identity=current_user_id,
            additional_claims=additional_claims,
            expires_delta=access_expiry
        )
        
        logger.info(f"Access token refreshed for user ID: {current_user_id}")
        
        # Return new access token
        return jsonify({
            'status': 'success',
            'message': 'Token refreshed',
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while refreshing token'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        # Get current user identity
        current_user_id = get_jwt_identity()
        
        # Find user
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Return user profile data
        return jsonify({
            'status': 'success',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'age': user.age,
                'income': user.income,
                'risk_tolerance': user.risk_tolerance,
                'investment_horizon': user.investment_horizon,
                'role': user.role,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving profile'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        # Get current user identity
        current_user_id = get_jwt_identity()
        
        # Find user
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Get updated data
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = [
            'first_name', 'last_name', 'age', 'income', 
            'risk_tolerance', 'investment_horizon'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Handle password update separately (if provided)
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])
        
        # Update timestamp and save
        user.updated_at = datetime.datetime.utcnow()
        user.save()
        
        logger.info(f"Profile updated for user ID: {current_user_id}")
        
        # Return updated profile
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'age': user.age,
                'income': user.income,
                'risk_tolerance': user.risk_tolerance,
                'investment_horizon': user.investment_horizon,
                'updated_at': user.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating profile'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Log out user by revoking token"""
    try:
        # Get JWT ID
        jti = get_jwt()['jti']
        
        # In a more complete implementation, you would add the token to a blacklist
        # For example, using Redis or another fast database for token revocation
        
        # For now, we'll just return a success message
        logger.info(f"User logged out: {get_jwt_identity()}")
        
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during logout'
        }), 500