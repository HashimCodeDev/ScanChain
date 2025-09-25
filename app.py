from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
import json
import hashlib
import bcrypt
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import qrcode
import io
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-for-testing')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Initialize extensions
CORS(app)
jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'error': 'Token has expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'success': False,
        'error': 'Invalid token'
    }), 422

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        'success': False,
        'error': 'Authorization header is expected'
    }), 401

# Import services
from services.auth_service import AuthService
from services.database_service import DatabaseService
from services.greenfield_service import GreenfieldService
from services.blockchain_service import BlockchainService
from services.qr_service import QRService

# Import routes
from routes.auth_routes import auth_bp

# Initialize services
auth_service = AuthService()
db_service = DatabaseService()
greenfield_service = GreenfieldService()
blockchain_service = BlockchainService()
qr_service = QRService()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10MB.'
    }), 413

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10MB.'
    }), 413

# Serve static files
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/dcellar-test')
def dcellar_test():
    return send_from_directory('public', 'dcellar-upload.html')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'contract': os.getenv('CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000'),
        'greenfield_rpc': os.getenv('GREENFIELD_RPC', 'Not configured'),
        'bucket_id': os.getenv('BUCKET_ID', 'Not configured')
    })

# DCellar bucket upload endpoint
@app.route('/upload', methods=['POST'])
def upload_to_dcellar():
    """Upload files to BNB Greenfield DCellar bucket"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Read file data
        file_data = file.read()
        filename = secure_filename(file.filename)
        
        # Validate file size
        if len(file_data) == 0:
            return jsonify({
                'success': False,
                'error': 'File is empty'
            }), 400
        
        if len(file_data) > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({
                'success': False,
                'error': 'File too large. Maximum size is 10MB.'
            }), 413
        
        # Upload to Greenfield DCellar bucket
        try:
            greenfield_url = greenfield_service.upload_file(
                file_data,
                filename,
                file.content_type or 'application/octet-stream'
            )
            
            if not greenfield_url:
                raise Exception('Upload failed - no URL returned')
            
        except Exception as upload_error:
            return jsonify({
                'success': False,
                'error': f'Upload failed: {str(upload_error)}'
            }), 500
        
        return jsonify({
            'success': True,
            'filename': filename,
            'greenfieldUrl': greenfield_url,
            'fileSize': len(file_data),
            'contentType': file.content_type or 'application/octet-stream'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Original upload endpoint (for backward compatibility)
@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # Manual JWT token verification (same as verify endpoint)
        auth_header = request.headers.get('Authorization')
        print(f"🔍 Upload - Authorization header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Authorization header required'
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode token to get user
        from flask_jwt_extended import decode_token
        try:
            decoded_token = decode_token(token)
            current_user_id = int(decoded_token['sub'])
            print(f"🔍 Upload - User ID: {current_user_id}")
        except Exception as decode_error:
            print(f"💥 Upload - Token decode error: {decode_error}")
            return jsonify({
                'success': False,
                'error': 'Invalid token'
            }), 422
        
        user = auth_service.get_user_by_id(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Get form data
        product_id = request.form.get('productId')
        manufacturer_name = request.form.get('manufacturerName')
        batch_name = request.form.get('batchName')
        product_type = request.form.get('productType')
        description = request.form.get('description')
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400
        
        print(f"Processing upload for batch: {product_id} by {manufacturer_name}")
        
        # Generate SHA-256 hash of the file
        file_data = file.read()
        file_hash = hashlib.sha256(file_data).hexdigest()
        print(f"Generated file hash: {file_hash}")
        
        # Store file on BNB Greenfield DCellar bucket
        print('Uploading to Greenfield DCellar bucket...')
        greenfield_url = greenfield_service.upload_file(
            file_data,
            f"{product_id}-{int(datetime.utcnow().timestamp())}.{file.filename.split('.')[-1]}",
            file.content_type or 'application/octet-stream'
        )
        print(f"File uploaded to Greenfield DCellar: {greenfield_url}")
        
        # Store hash on BSC
        print('Storing hash on BSC...')
        tx_hash = blockchain_service.store_product_hash(product_id, file_hash)
        print(f"Hash stored on BSC. Transaction: {tx_hash}")
        
        # Store batch information in database with enhanced metadata
        batch_data = {
            'manufacturerId': manufacturer_name.lower().replace(' ', '_') if manufacturer_name else 'unknown',
            'manufacturerName': manufacturer_name or 'Unknown Manufacturer',
            'batchName': batch_name or product_id,
            'productType': product_type or 'Unknown',
            'description': description or '',
            'fileHash': file_hash,
            'greenfieldUrl': greenfield_url,
            'txHash': tx_hash,
            'contractAddress': os.getenv('BSC_CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000'),
            'documentUrl': greenfield_url,
            'userId': user['id'],
            'userEmail': user['email'],
            'fileName': file.filename,
            'fileSize': len(file_data),
            'mimeType': file.content_type,
            'uploadTimestamp': datetime.utcnow().isoformat()
        }
        
        db_service.store_batch(product_id, batch_data)
        
        # Associate blockchain hash with user
        auth_service.associate_blockchain_hash(user['id'], {
            'batchId': product_id,
            'fileHash': file_hash,
            'txHash': tx_hash,
            'contractAddress': os.getenv('BSC_CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000'),
            'blockNumber': None,
            'productName': batch_data['batchName']
        })
        
        # Generate QR code
        qr_result = qr_service.generate_product_qr(
            product_id, 
            os.getenv('BSC_CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000'),
            {
                'batchName': batch_data['batchName'],
                'manufacturer': batch_data['manufacturerName'],
                'productType': batch_data['productType']
            }
        )
        
        return jsonify({
            'success': True,
            'batchId': product_id,
            'manufacturerName': batch_data['manufacturerName'],
            'batchName': batch_data['batchName'],
            'fileHash': file_hash,
            'greenfieldUrl': greenfield_url,
            'txHash': tx_hash,
            'qrCode': qr_result['qrImage'],
            'qrCodeData': qr_result['qrData'],
            'contractAddress': os.getenv('BSC_CONTRACT_ADDRESS', '0x0000000000000000000000000000000000000000'),
            'message': 'Batch created successfully! Share the QR code with your supply chain partners.'
        })
    
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Verify endpoint
@app.route('/api/verify', methods=['POST'])
@jwt_required()
def verify_product():
    try:
        data = request.get_json()
        product_id = data.get('productId')
        greenfield_url = data.get('greenfieldUrl')
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400
        
        print(f"Verifying product: {product_id}")
        
        # Get stored hash from BSC
        print('Fetching hash from BSC...')
        stored_hash = blockchain_service.get_product_hash(product_id)
        
        if not stored_hash:
            return jsonify({
                'success': True,
                'isVerified': False,
                'error': 'Product not found on blockchain',
                'productId': product_id
            })
        
        # Download file from Greenfield and calculate current hash
        if greenfield_url:
            print('Downloading file from Greenfield...')
            file_data = greenfield_service.download_file(greenfield_url)
            current_hash = hashlib.sha256(file_data).hexdigest()
        else:
            # If no Greenfield URL provided, use stored hash for comparison
            current_hash = stored_hash
        
        print(f"Current hash: {current_hash}, Stored hash: {stored_hash}")
        
        # Compare hashes
        is_verified = stored_hash == current_hash
        
        return jsonify({
            'success': True,
            'isVerified': is_verified,
            'productId': product_id,
            'storedHash': stored_hash,
            'currentHash': current_hash,
            'message': 'Product is authentic' if is_verified else 'Product has been tampered with'
        })
    
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Scan endpoint
@app.route('/api/scan', methods=['POST'])
@jwt_required()
def scan_product():
    try:
        data = request.get_json()
        qr_data = data.get('qrData')
        supplier_name = data.get('supplierName')
        supplier_location = data.get('supplierLocation')
        
        if not qr_data or not supplier_name:
            return jsonify({
                'success': False,
                'error': 'QR data and supplier name are required'
            }), 400
        
        # Parse QR data
        try:
            parsed_qr = json.loads(qr_data) if isinstance(qr_data, str) else qr_data
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'error': 'Invalid QR code format'
            }), 400
        
        batch_id = parsed_qr.get('productId')
        batch = db_service.get_batch(batch_id)
        
        if not batch:
            return jsonify({
                'success': False,
                'error': 'Batch not found'
            }), 404
        
        # Record the scan with current user information
        current_user_identity = get_jwt_identity()
        
        scan_record = db_service.record_scan(batch_id, {
            'supplierName': supplier_name,
            'supplierLocation': supplier_location or 'Unknown',
            'scanType': 'QR_SCAN',
            'ipAddress': request.remote_addr,
            'userAgent': request.headers.get('User-Agent'),
            'userId': current_user_identity.get('id') if isinstance(current_user_identity, dict) else None,
            'scannerUsername': current_user_identity.get('username') if isinstance(current_user_identity, dict) else current_user_identity
        })
        
        return jsonify({
            'success': True,
            'batchInfo': {
                'batchId': batch_id,
                'batchName': batch.get('batchName'),
                'manufacturerName': batch.get('manufacturerName'),
                'productType': batch.get('productType'),
                'description': batch.get('description'),
                'documentUrl': batch.get('documentUrl'),
                'createdAt': batch.get('createdAt'),
                'contractAddress': batch.get('contractAddress'),
                'txHash': batch.get('txHash')
            },
            'scanRecord': {
                'scanId': scan_record['id'],
                'timestamp': scan_record['timestamp'],
                'supplierName': scan_record['supplierName']
            },
            'message': f'Welcome {supplier_name}! Scan recorded successfully.'
        })
    
    except Exception as e:
        print(f"Scan error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Dashboard endpoint
@app.route('/api/dashboard/<user_id>', methods=['GET'])
@jwt_required()
def get_dashboard(user_id):
    try:
        # Get current user from JWT token to determine role
        current_user = get_jwt_identity()
        
        # Use the new role-based dashboard method
        dashboard_data = db_service.get_user_dashboard(user_id)
        
        return jsonify({
            'success': True,
            **dashboard_data
        })
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Get all scans for manufacturer
@app.route('/api/scans/<manufacturer_id>', methods=['GET'])
@jwt_required()
def get_manufacturer_scans(manufacturer_id):
    try:
        # Get dashboard data which includes all scans
        dashboard_data = db_service.get_manufacturer_dashboard(manufacturer_id)
        
        return jsonify({
            'success': True,
            'scans': dashboard_data.get('allScans', []),
            'totalScans': dashboard_data.get('totalScans', 0),
            'recentScans': dashboard_data.get('recentScans', [])
        })
    
    except Exception as e:
        print(f"Get scans error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Get scan details by scan ID
@app.route('/api/scan/<scan_id>', methods=['GET'])
@jwt_required()
def get_scan_details(scan_id):
    try:
        scans_data = db_service._load_data(db_service.scans_file)
        
        scan = None
        for s in scans_data.get('scans', []):
            if str(s.get('id')) == str(scan_id):
                scan = s
                break
        
        if not scan:
            return jsonify({
                'success': False,
                'error': 'Scan not found'
            }), 404
        
        # Get batch/product info
        batch_info = db_service.get_batch(scan.get('batchId')) if scan else None
        if not batch_info:
            products_data = db_service._load_data(db_service.products_file)
            for product in products_data.get('products', []):
                if product.get('productId') == scan.get('batchId'):
                    batch_info = product
                    break
        
        return jsonify({
            'success': True,
            'scan': scan,
            'batchInfo': batch_info
        })
    
    except Exception as e:
        print(f"Get scan details error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Test endpoint for dashboard data (remove in production)
@app.route('/api/test/dashboard-data/<manufacturer_id>', methods=['GET'])
def test_dashboard_data(manufacturer_id):
    """Test endpoint to see raw dashboard data"""
    try:
        dashboard_data = db_service.get_manufacturer_dashboard(manufacturer_id)
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'message': f'Dashboard data for manufacturer: {manufacturer_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Product info endpoint
@app.route('/api/product/<product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    try:
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400
        
        product_info = blockchain_service.get_product_info(product_id)
        
        if not product_info.get('fileHash'):
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        return jsonify({
            'success': True,
            'productId': product_id,
            **product_info
        })
    
    except Exception as e:
        print(f"Get product error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# User metadata endpoints
@app.route('/api/user/metadata', methods=['GET'])
@jwt_required()
def get_current_user_metadata():
    try:
        current_user_id = get_jwt_identity()
        user_metadata = db_service.get_user_metadata(current_user_id)
        
        return jsonify({
            'success': True,
            'userMetadata': user_metadata
        })
    
    except Exception as e:
        print(f"Get current user metadata error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<int:user_id>/metadata', methods=['GET'])
@jwt_required()
def get_user_metadata(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = auth_service.get_user_by_id(current_user_id)
        
        # Ensure user can only access their own data (or admin access)
        if current_user_id != user_id and current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'error': 'Access denied. You can only view your own metadata.'
            }), 403
        
        user_metadata = db_service.get_user_metadata(user_id)
        
        return jsonify({
            'success': True,
            'userMetadata': user_metadata
        })
    
    except Exception as e:
        print(f"Get user metadata error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Search products endpoint
@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        query = request.args.get('q')
        criteria = request.args.get('criteria', 'all')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        results = db_service.search_products(query, criteria)
        
        return jsonify({
            'success': True,
            'query': query,
            'criteria': criteria,
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        print(f"Search products error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Frontend routes
@app.route('/')
def serve_login():
    return send_from_directory('public', 'login.html')

@app.route('/home')
def serve_home():
    return send_from_directory('public', 'index.html')

@app.route('/login')
def serve_login_page():
    return send_from_directory('public', 'login.html')

@app.route('/register')
def serve_register():
    return send_from_directory('public', 'register.html')

@app.route('/upload')
def serve_upload():
    return send_from_directory('public', 'upload.html')

@app.route('/scan')
def serve_scan():
    return send_from_directory('public', 'scan.html')

@app.route('/verify')
def serve_verify():
    return send_from_directory('public', 'verify.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory('public', 'dashboard.html')

@app.route('/auth-test')
def serve_auth_test():
    return send_from_directory('public', 'auth-test.html')

@app.route('/simple-auth-test')
def serve_simple_auth_test():
    return send_from_directory('public', 'simple-auth-test.html')

@app.route('/qr-test')
def serve_qr_test():
    return send_from_directory('public', 'qr-test.html')

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

if __name__ == '__main__':
    print("🚀 ScanChain Python server starting...")
    print(f"📊 Health check available at http://localhost:5000/api/health")
    print(f"📋 Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.run(debug=True, host='0.0.0.0', port=5000)