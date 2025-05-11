from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.budget import Budget
from models.user import User
from datetime import datetime
import json

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/', methods=['GET'])
@jwt_required()
def get_budgets():
    """Get all budgets for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        user_budgets = Budget.get_budgets_by_user_id(current_user_id)
        return jsonify({"success": True, "budgets": user_budgets}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['GET'])
@jwt_required()
def get_budget(budget_id):
    """Get a specific budget by ID"""
    current_user_id = get_jwt_identity()
    
    try:
        budget = Budget.get_budget_by_id(budget_id)
        
        if not budget:
            return jsonify({"success": False, "error": "Budget not found"}), 404
            
        # Check if the budget belongs to the current user
        if budget['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
            
        return jsonify({"success": True, "budget": budget}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@budgets_bp.route('/', methods=['POST'])
@jwt_required()
def create_budget():
    """Create a new budget"""
    current_user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'amount', 'category', 'period']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Create budget object with data
        new_budget = {
            'user_id': current_user_id,
            'name': data['name'],
            'amount': float(data['amount']),
            'category': data['category'],
            'period': data['period'],  # 'monthly', 'weekly', etc.
            'start_date': data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
            'end_date': data.get('end_date'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save budget to database
        budget_id = Budget.create_budget(new_budget)
        
        if budget_id:
            new_budget['id'] = budget_id
            return jsonify({"success": True, "budget": new_budget}), 201
        else:
            return jsonify({"success": False, "error": "Failed to create budget"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    """Update an existing budget"""
    current_user_id = get_jwt_identity()
    
    try:
        # Check if budget exists and belongs to user
        existing_budget = Budget.get_budget_by_id(budget_id)
        
        if not existing_budget:
            return jsonify({"success": False, "error": "Budget not found"}), 404
            
        if existing_budget['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
        
        # Get update data
        data = request.get_json()
        
        # Prepare update data (only allow specific fields to be updated)
        update_data = {}
        allowed_fields = ['name', 'amount', 'category', 'period', 'start_date', 'end_date']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update budget
        if update_data:
            success = Budget.update_budget(budget_id, update_data)
            
            if success:
                updated_budget = Budget.get_budget_by_id(budget_id)
                return jsonify({"success": True, "budget": updated_budget}), 200
            else:
                return jsonify({"success": False, "error": "Failed to update budget"}), 500
        else:
            return jsonify({"success": False, "error": "No valid fields to update"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    """Delete a budget"""
    current_user_id = get_jwt_identity()
    
    try:
        # Check if budget exists and belongs to user
        existing_budget = Budget.get_budget_by_id(budget_id)
        
        if not existing_budget:
            return jsonify({"success": False, "error": "Budget not found"}), 404
            
        if existing_budget['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
        
        # Delete budget
        success = Budget.delete_budget(budget_id)
        
        if success:
            return jsonify({"success": True, "message": "Budget deleted successfully"}), 200
        else:
            return jsonify({"success": False, "error": "Failed to delete budget"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@budgets_bp.route('/analysis', methods=['GET'])
@jwt_required()
def budget_analysis():
    """Get budget analysis for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get time period from query parameters (default to 'month')
        period = request.args.get('period', 'month')
        
        # Get budget analysis data
        analysis = Budget.get_budget_analysis(current_user_id, period)
        
        return jsonify({"success": True, "analysis": analysis}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@budgets_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def budget_recommendations():
    """Get budget recommendations for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get user's financial profile for generating recommendations
        user_profile = User.get_user_financial_profile(current_user_id)
        
        # Get spending patterns for recommendations
        spending_patterns = Budget.get_spending_patterns(current_user_id)
        
        # Generate budget recommendations based on user profile and spending patterns
        recommendations = Budget.generate_budget_recommendations(user_profile, spending_patterns)
        
        return jsonify({"success": True, "recommendations": recommendations}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500