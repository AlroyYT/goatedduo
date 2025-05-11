from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.transaction import Transaction
from models.user import User
from datetime import datetime
import json

investments_bp = Blueprint('investments', __name__)

@investments_bp.route('/', methods=['GET'])
@jwt_required()
def get_investments():
    """Get all investments for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        from models.transaction import Transaction
        user_investments = Transaction.get_investments_by_user_id(current_user_id)
        return jsonify({"success": True, "investments": user_investments}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/<int:investment_id>', methods=['GET'])
@jwt_required()
def get_investment(investment_id):
    """Get a specific investment by ID"""
    current_user_id = get_jwt_identity()
    
    try:
        from models.transaction import Transaction
        investment = Transaction.get_investment_by_id(investment_id)
        
        if not investment:
            return jsonify({"success": False, "error": "Investment not found"}), 404
            
        # Check if the investment belongs to the current user
        if investment['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
            
        return jsonify({"success": True, "investment": investment}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/', methods=['POST'])
@jwt_required()
def create_investment():
    """Create a new investment record"""
    current_user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'amount', 'investment_type', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Create investment object with data
        new_investment = {
            'user_id': current_user_id,
            'name': data['name'],
            'amount': float(data['amount']),
            'investment_type': data['investment_type'],  # stocks, bonds, real_estate, etc.
            'date': data['date'],
            'description': data.get('description', ''),
            'expected_return': data.get('expected_return'),
            'risk_level': data.get('risk_level'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save investment to database
        from models.transaction import Transaction
        investment_id = Transaction.create_investment(new_investment)
        
        if investment_id:
            new_investment['id'] = investment_id
            return jsonify({"success": True, "investment": new_investment}), 201
        else:
            return jsonify({"success": False, "error": "Failed to create investment record"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/<int:investment_id>', methods=['PUT'])
@jwt_required()
def update_investment(investment_id):
    """Update an existing investment record"""
    current_user_id = get_jwt_identity()
    
    try:
        from models.transaction import Transaction
        # Check if investment exists and belongs to user
        existing_investment = Transaction.get_investment_by_id(investment_id)
        
        if not existing_investment:
            return jsonify({"success": False, "error": "Investment not found"}), 404
            
        if existing_investment['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
        
        # Get update data
        data = request.get_json()
        
        # Prepare update data (only allow specific fields to be updated)
        update_data = {}
        allowed_fields = ['name', 'amount', 'investment_type', 'date', 'description', 
                          'expected_return', 'risk_level']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update investment
        if update_data:
            success = Transaction.update_investment(investment_id, update_data)
            
            if success:
                updated_investment = Transaction.get_investment_by_id(investment_id)
                return jsonify({"success": True, "investment": updated_investment}), 200
            else:
                return jsonify({"success": False, "error": "Failed to update investment"}), 500
        else:
            return jsonify({"success": False, "error": "No valid fields to update"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/<int:investment_id>', methods=['DELETE'])
@jwt_required()
def delete_investment(investment_id):
    """Delete an investment record"""
    current_user_id = get_jwt_identity()
    
    try:
        from models.transaction import Transaction
        # Check if investment exists and belongs to user
        existing_investment = Transaction.get_investment_by_id(investment_id)
        
        if not existing_investment:
            return jsonify({"success": False, "error": "Investment not found"}), 404
            
        if existing_investment['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
        
        # Delete investment
        success = Transaction.delete_investment(investment_id)
        
        if success:
            return jsonify({"success": True, "message": "Investment deleted successfully"}), 200
        else:
            return jsonify({"success": False, "error": "Failed to delete investment"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/analysis', methods=['GET'])
@jwt_required()
def investment_analysis():
    """Get investment analysis for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Calculate investment portfolio metrics
        from models.transaction import Transaction
        
        # Get investment data
        investments = Transaction.get_investments_by_user_id(current_user_id)
        
        # Calculate metrics
        total_invested = sum(inv['amount'] for inv in investments)
        investment_by_type = {}
        
        for inv in investments:
            inv_type = inv['investment_type']
            if inv_type in investment_by_type:
                investment_by_type[inv_type] += inv['amount']
            else:
                investment_by_type[inv_type] = inv['amount']
        
        # Calculate percentage allocation
        allocation = {k: (v / total_invested * 100) if total_invested > 0 else 0 
                     for k, v in investment_by_type.items()}
        
        # Get historical performance if available
        historical_performance = Transaction.get_investment_performance(current_user_id)
        
        analysis = {
            'total_invested': total_invested,
            'investment_by_type': investment_by_type,
            'allocation': allocation,
            'historical_performance': historical_performance
        }
        
        return jsonify({"success": True, "analysis": analysis}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def investment_recommendations():
    """Get investment recommendations for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get user's risk profile and financial goals
        user_profile = User.get_user_financial_profile(current_user_id)
        
        # Get current investment allocation
        from models.transaction import Transaction
        current_investments = Transaction.get_investments_by_user_id(current_user_id)
        
        # Generate investment recommendations based on profile and current investments
        risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
        investment_horizon = user_profile.get('investment_horizon', 'medium')
        financial_goals = user_profile.get('financial_goals', [])
        
        # Calculate recommended asset allocation based on risk profile
        recommended_allocation = Transaction.get_recommended_allocation(
            risk_tolerance, investment_horizon, financial_goals)
        
        # Generate specific investment recommendations
        investment_recommendations = Transaction.generate_investment_recommendations(
            user_profile, current_investments, recommended_allocation)
        
        recommendations = {
            'recommended_allocation': recommended_allocation,
            'specific_recommendations': investment_recommendations,
            'risk_profile': risk_tolerance
        }
        
        return jsonify({"success": True, "recommendations": recommendations}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@investments_bp.route('/forecast', methods=['GET'])
@jwt_required()
def investment_forecast():
    """Get investment forecast for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get forecast parameters from query
        years = int(request.args.get('years', 10))
        additional_contribution = float(request.args.get('monthly_contribution', 0))
        
        # Get user's current investments
        from models.transaction import Transaction
        current_investments = Transaction.get_investments_by_user_id(current_user_id)
        
        # Generate forecast based on current investments and parameters
        forecast_data = Transaction.generate_investment_forecast(
            current_investments, years, additional_contribution)
        
        return jsonify({"success": True, "forecast": forecast_data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500