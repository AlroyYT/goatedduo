from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.transaction import Transaction
from datetime import datetime
import json

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get all transactions for the current user with optional filtering"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get filter parameters
        transaction_type = request.args.get('type')  # income, expense, etc.
        category = request.args.get('category')  # groceries, utilities, etc.
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'date')  # date, amount, etc.
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc
        
        # Get paginated results
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get transactions with filters
        transactions, total_count = Transaction.get_transactions_by_user_id(
            current_user_id,
            transaction_type=transaction_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        # Calculate pagination metadata
        total_pages = (total_count + per_page - 1) // per_page
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_items': total_count,
            'total_pages': total_pages
        }
        
        return jsonify({
            "success": True, 
            "transactions": transactions,
            "pagination": pagination
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get a specific transaction by ID"""
    current_user_id = get_jwt_identity()
    
    try:
        transaction = Transaction.get_transaction_by_id(transaction_id)
        
        if not transaction:
            return jsonify({"success": False, "error": "Transaction not found"}), 404
            
        # Check if the transaction belongs to the current user
        if transaction['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
            
        return jsonify({"success": True, "transaction": transaction}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create a new transaction"""
    current_user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'transaction_type', 'category', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Create transaction object with data
        new_transaction = {
            'user_id': current_user_id,
            'amount': float(data['amount']),
            'transaction_type': data['transaction_type'],  # income, expense, transfer
            'category': data['category'],
            'date': data['date'],
            'description': data.get('description', ''),
            'payment_method': data.get('payment_method', ''),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save transaction to database
        transaction_id = Transaction.create_transaction(new_transaction)
        
        if transaction_id:
            new_transaction['id'] = transaction_id
            return jsonify({"success": True, "transaction": new_transaction}), 201
        else:
            return jsonify({"success": False, "error": "Failed to create transaction"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def update_transaction(transaction_id):
    """Update an existing transaction"""
    current_user_id = get_jwt_identity()
    
    try:
        # Check if transaction exists and belongs to user
        existing_transaction = Transaction.get_transaction_by_id(transaction_id)
        
        if not existing_transaction:
            return jsonify({"success": False, "error": "Transaction not found"}), 404
            
        if existing_transaction['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
        
        # Get update data
        data = request.get_json()
        
        # Prepare update data (only allow specific fields to be updated)
        update_data = {}
        allowed_fields = ['amount', 'transaction_type', 'category', 'date', 
                         'description', 'payment_method']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update transaction
        if update_data:
            success = Transaction.update_transaction(transaction_id, update_data)
            
            if success:
                updated_transaction = Transaction.get_transaction_by_id(transaction_id)
                return jsonify({"success": True, "transaction": updated_transaction}), 200
            else:
                return jsonify({"success": False, "error": "Failed to update transaction"}), 500
        else:
            return jsonify({"success": False, "error": "No valid fields to update"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    """Delete a transaction"""
    current_user_id = get_jwt_identity()
    
    try:
        # Check if transaction exists and belongs to user
        existing_transaction = Transaction.get_transaction_by_id(transaction_id)
        
        if not existing_transaction:
            return jsonify({"success": False, "error": "Transaction not found"}), 404
            
        if existing_transaction['user_id'] != current_user_id:
            return jsonify({"success": False, "error": "Unauthorized access"}), 403
        
        # Delete transaction
        success = Transaction.delete_transaction(transaction_id)
        
        if success:
            return jsonify({"success": True, "message": "Transaction deleted successfully"}), 200
        else:
            return jsonify({"success": False, "error": "Failed to delete transaction"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_transaction_summary():
    """Get transaction summary for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get period from query parameters (default to 'month')
        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get transaction summary
        summary = Transaction.get_transaction_summary(
            current_user_id, period, start_date, end_date)
        
        return jsonify({"success": True, "summary": summary}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_transaction_categories():
    """Get transaction categories for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get transaction type from query parameters (default to all)
        transaction_type = request.args.get('transaction_type')
        
        # Get categories
        categories = Transaction.get_transaction_categories(current_user_id, transaction_type)
        
        return jsonify({"success": True, "categories": categories}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_spending_insights():
    """Get spending insights for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get period from query parameters (default to 'month')
        period = request.args.get('period', '3months')  # week, month, 3months, 6months, year
        
        # Get spending insights
        insights = Transaction.get_spending_insights(current_user_id, period)
        
        return jsonify({"success": True, "insights": insights}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_spending_trends():
    """Get spending trends over time for the current user"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get parameters from query
        period = request.args.get('period', 'monthly')  # daily, weekly, monthly
        months = int(request.args.get('months', 6))  # number of months to analyze
        category = request.args.get('category')  # optional category filter
        
        # Get spending trends
        trends = Transaction.get_spending_trends(current_user_id, period, months, category)
        
        return jsonify({"success": True, "trends": trends}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_transaction_recommendations():
    """Get spending recommendations based on transaction history"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get recommendations based on spending patterns
        recommendations = Transaction.generate_spending_recommendations(current_user_id)
        
        return jsonify({"success": True, "recommendations": recommendations}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@transactions_bp.route('/import', methods=['POST'])
@jwt_required()
def import_transactions():
    """Import transactions from CSV or other formats"""
    current_user_id = get_jwt_identity()
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
            
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
            
        # Process the file and import transactions
        import_results = Transaction.import_transactions_from_file(file, current_user_id)
        
        return jsonify({
            "success": True, 
            "message": "Transactions imported successfully",
            "results": import_results
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500