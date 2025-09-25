from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'fullName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Register user
        result = auth_service.register_user(
            email=data['email'],
            password=data['password'],
            full_name=data['fullName'],
            role=data.get('role', 'user'),
            company_name=data.get('companyName', '')
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        # Create access token
        access_token = create_access_token(identity=str(result['user']['id']))
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': access_token,
            'user': result['user']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Authenticate user
        result = auth_service.login_user(email, password)
        
        if not result['success']:
            print(f"❌ Login failed for {email}: {result['error']}")
            return jsonify(result), 401
        
        # Create access token
        access_token = create_access_token(identity=str(result['user']['id']))
        print(f"✅ Login successful for {email}, user ID: {result['user']['id']}")
        print(f"🎫 Generated token: {access_token[:50]}...")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'user': result['user']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify JWT token and return user info"""
    try:
        # Manual JWT token extraction and verification
        auth_header = request.headers.get('Authorization')
        print(f"🔍 Authorization header: {auth_header}")
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'No Authorization header'
            }), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Invalid Authorization header format'
            }), 401
        
        token = auth_header.split(' ')[1]
        print(f"🎫 Extracted token: {token[:50]}...")
        
        # Try to decode the token
        from flask_jwt_extended import decode_token
        
        try:
            decoded_token = decode_token(token)
            current_user_id = int(decoded_token['sub'])  # Convert string back to int
            print(f"🔍 Decoded user ID: {current_user_id}")
        except Exception as decode_error:
            print(f"💥 Token decode error: {decode_error}")
            return jsonify({
                'success': False,
                'error': f'Invalid token: {str(decode_error)}'
            }), 422
        
        if not current_user_id:
            return jsonify({
                'success': False,
                'error': 'Invalid token - no user identity'
            }), 422
        
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user:
            print(f"❌ User not found for ID: {current_user_id}")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        print(f"✅ Token verified for user: {user['fullName']}")
        return jsonify({
            'success': True,
            'user': user
        })
    
    except Exception as e:
        print(f"💥 Token verification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Token verification failed: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        # In a stateless JWT system, logout is handled client-side
        # by removing the token. Here we can log the logout event.
        current_user_id = get_jwt_identity()
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Logout failed: {str(e)}'
        }), 500

@auth_bp.route('/demo-login', methods=['POST'])
def demo_login():
    """Generic demo login endpoint"""
    try:
        data = request.get_json()
        user_type = data.get('userType', 'manufacturer')
        
        if user_type == 'manufacturer':
            result = auth_service.login_user('manufacturer@techcorp.com', 'demo123')
        elif user_type == 'supplier':
            result = auth_service.login_user('supplier@logistics.com', 'demo123')
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid user type'
            }), 400
        
        if not result['success']:
            return jsonify(result), 401
        
        access_token = create_access_token(identity=str(result['user']['id']))
        print(f"✅ Demo login successful for {user_type}, user ID: {result['user']['id']}")
        
        return jsonify({
            'success': True,
            'message': f'Demo {user_type} login successful',
            'token': access_token,
            'user': result['user']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Demo login failed: {str(e)}'
        }), 500

# Demo login endpoints for testing
@auth_bp.route('/demo/manufacturer', methods=['POST'])
def demo_manufacturer_login():
    """Demo manufacturer login"""
    try:
        result = auth_service.login_user('manufacturer@techcorp.com', 'demo123')
        
        if not result['success']:
            return jsonify(result), 401
        
        access_token = create_access_token(identity=str(result['user']['id']))
        
        return jsonify({
            'success': True,
            'message': 'Demo manufacturer login successful',
            'token': access_token,
            'user': result['user']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Demo login failed: {str(e)}'
        }), 500

@auth_bp.route('/demo/supplier', methods=['POST'])
def demo_supplier_login():
    """Demo supplier login"""
    try:
        result = auth_service.login_user('supplier@logistics.com', 'demo123')
        
        if not result['success']:
            return jsonify(result), 401
        
        access_token = create_access_token(identity=str(result['user']['id']))
        
        return jsonify({
            'success': True,
            'message': 'Demo supplier login successful',
            'token': access_token,
            'user': result['user']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Demo login failed: {str(e)}'
        }), 500
