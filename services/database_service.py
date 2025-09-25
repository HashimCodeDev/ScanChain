import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class DatabaseService:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.batches_file = os.path.join(self.data_dir, 'batches.json')
        self.scans_file = os.path.join(self.data_dir, 'scans.json')
        self.products_file = os.path.join(self.data_dir, 'products.json')
        self.users_file = os.path.join(self.data_dir, 'users.json')
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with default structure"""
        files = [
            (self.batches_file, {"batches": [], "lastBatchId": 0}),
            (self.scans_file, {"scans": [], "lastScanId": 0}),
            (self.products_file, {"products": [], "metadata": [], "lastProductId": 0})
        ]
        
        for file_path, default_data in files:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2)

    def _load_data(self, file_path: str) -> Dict:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_data(self, file_path: str, data: Dict):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data to {file_path}: {e}")

    def store_batch(self, batch_id: str, data: Dict) -> Dict:
        """Store batch information with enhanced tracking and JSON persistence"""
        batches_data = self._load_data(self.batches_file)
        
        batch = {
            **data,
            'batchId': batch_id,
            'createdAt': datetime.utcnow().isoformat(),
            'scans': [],
            'status': 'active',
            'lastActivity': datetime.utcnow().isoformat(),
            'metadata': {
                'fileName': data.get('fileName', 'unknown'),
                'fileSize': data.get('fileSize', 0),
                'mimeType': data.get('mimeType', 'application/octet-stream'),
                'uploadedBy': data.get('userId', 'unknown'),
                'uploadedAt': datetime.utcnow().isoformat()
            }
        }
        
        # Add to batches array
        batches_data['batches'].append(batch)
        batches_data['lastBatchId'] += 1
        
        # Save to JSON file
        self._save_data(self.batches_file, batches_data)
        
        # Also store in products data for metadata tracking
        products_data = self._load_data(self.products_file)
        
        product_metadata = {
            'productId': batch_id,
            'userId': data.get('userId'),
            'userEmail': data.get('userEmail'),
            'batchName': data.get('batchName'),
            'manufacturerName': data.get('manufacturerName'),
            'productType': data.get('productType'),
            'description': data.get('description'),
            'fileHash': data.get('fileHash'),
            'greenfieldUrl': data.get('greenfieldUrl'),
            'txHash': data.get('txHash'),
            'contractAddress': data.get('contractAddress'),
            'createdAt': datetime.utcnow().isoformat(),
            'metadata': batch['metadata']
        }
        
        products_data['products'].append(product_metadata)
        products_data['lastProductId'] += 1
        self._save_data(self.products_file, products_data)
        
        return batch

    def get_batch(self, batch_id: str) -> Optional[Dict]:
        """Get batch information from JSON data"""
        batches_data = self._load_data(self.batches_file)
        
        for batch in batches_data.get('batches', []):
            if batch['batchId'] == batch_id:
                return batch
        
        return None

    def record_scan(self, batch_id: str, scan_data: Dict) -> Optional[Dict]:
        """Record a scan event with enhanced supplier tracking and JSON persistence"""
        batch = self.get_batch(batch_id)
        if not batch:
            return None
        
        scans_data = self._load_data(self.scans_file)
        
        scan_record = {
            'id': str(scans_data.get('lastScanId', 0) + 1),
            'batchId': batch_id,
            **scan_data,
            'timestamp': datetime.utcnow().isoformat(),
            'location': scan_data.get('location', 'Unknown')
        }
        
        # Add scan to the specific batch
        batch['scans'].append(scan_record)
        batch['lastActivity'] = datetime.utcnow().isoformat()
        
        # Update the batch in the array
        batches_data = self._load_data(self.batches_file)
        for i, b in enumerate(batches_data['batches']):
            if b['batchId'] == batch_id:
                batches_data['batches'][i] = batch
                break
        
        self._save_data(self.batches_file, batches_data)
        
        # Add to scans data
        scans_data['scans'].append(scan_record)
        scans_data['lastScanId'] += 1
        self._save_data(self.scans_file, scans_data)
        
        return scan_record

    def get_user_dashboard(self, user_id: str, user_role: str = None) -> Dict:
        """Get role-based dashboard data for any user"""
        batches_data = self._load_data(self.batches_file)
        scans_data = self._load_data(self.scans_file)
        products_data = self._load_data(self.products_file)
        users_data = self._load_data(self.users_file)
        
        # Find user details
        user_info = None
        for user in users_data.get('users', []):
            if (str(user.get('id')) == str(user_id) or 
                user.get('username') == user_id or
                user.get('fullName').lower().replace(' ', '_') == user_id.lower()):
                user_info = user
                break
        
        if not user_info:
            return {'error': 'User not found', 'success': False}
        
        actual_user_id = user_info.get('id')
        user_role = user_info.get('role', 'user')
        user_name = user_info.get('fullName', user_id)
        
        if user_role == 'manufacturer':
            return self._get_manufacturer_dashboard(actual_user_id, user_name, batches_data, scans_data, products_data)
        elif user_role == 'supplier':
            return self._get_supplier_dashboard(actual_user_id, user_name, batches_data, scans_data, products_data)
        else:
            return self._get_general_user_dashboard(actual_user_id, user_name, batches_data, scans_data, products_data)
    
    def _get_manufacturer_dashboard(self, user_id: int, user_name: str, batches_data: Dict, scans_data: Dict, products_data: Dict) -> Dict:
        """Get manufacturer dashboard showing their batches and who scanned them"""
        manufacturer_batches = []
        recent_scans = []
        total_scans = 0
        unique_suppliers = set()
        manufacturer_batch_ids = set()
        
        # Get manufacturer's batches by user ID
        for batch in batches_data.get('batches', []):
            if str(batch.get('userId')) == str(user_id):
                manufacturer_batches.append(batch)
                manufacturer_batch_ids.add(batch.get('batchId'))
                
                # Collect scans from batches (legacy)
                for scan in batch.get('scans', []):
                    recent_scans.append({
                        **scan,
                        'batchId': batch['batchId'],
                        'productName': batch.get('batchName') or batch.get('productName')
                    })
                    total_scans += 1
                    if scan.get('supplierName'):
                        unique_suppliers.add(scan['supplierName'])
        
        # Get manufacturer's products
        for product in products_data.get('products', []):
            if str(product.get('userId')) == str(user_id):
                manufacturer_batch_ids.add(product.get('productId'))
        
        # Get scans from separate scans.json that belong to this manufacturer
        for scan in scans_data.get('scans', []):
            if scan.get('batchId') in manufacturer_batch_ids:
                # Find the corresponding batch/product info
                batch_info = None
                for batch in manufacturer_batches:
                    if batch.get('batchId') == scan.get('batchId'):
                        batch_info = batch
                        break
                
                if not batch_info:
                    for product in products_data.get('products', []):
                        if product.get('productId') == scan.get('batchId'):
                            batch_info = product
                            break
                
                recent_scans.append({
                    **scan,
                    'productName': batch_info.get('batchName') or batch_info.get('productName', 'Unknown Product') if batch_info else 'Unknown Product',
                    'manufacturerName': batch_info.get('manufacturerName', user_name) if batch_info else user_name
                })
                total_scans += 1
                if scan.get('supplierName'):
                    unique_suppliers.add(scan['supplierName'])
        
        # Sort recent scans by timestamp (newest first)
        recent_scans.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'userId': user_id,
            'userName': user_name,
            'role': 'manufacturer',
            'totalBatches': len(manufacturer_batches),
            'totalScans': total_scans,
            'totalSuppliers': len(unique_suppliers),
            'batches': manufacturer_batches,
            'recentScans': recent_scans[:10],
            'supplierList': list(unique_suppliers),
            'allScans': recent_scans
        }
    
    def _get_supplier_dashboard(self, user_id: int, user_name: str, batches_data: Dict, scans_data: Dict, products_data: Dict) -> Dict:
        """Get supplier dashboard showing batches they have scanned"""
        scanned_batches = []
        my_scans = []
        unique_manufacturers = set()
        total_scans = 0
        
        # Find scans by this supplier
        for scan in scans_data.get('scans', []):
            if (scan.get('supplierName') == user_name or 
                str(scan.get('supplierId', '')) == str(user_id)):
                my_scans.append(scan)
                total_scans += 1
                
                # Find batch/product info for this scan
                batch_info = None
                for batch in batches_data.get('batches', []):
                    if batch.get('batchId') == scan.get('batchId'):
                        batch_info = batch
                        break
                
                if not batch_info:
                    for product in products_data.get('products', []):
                        if product.get('productId') == scan.get('batchId'):
                            batch_info = product
                            break
                
                if batch_info:
                    unique_manufacturers.add(batch_info.get('manufacturerName', 'Unknown'))
                    
                    # Add to scanned batches if not already there
                    batch_id = scan.get('batchId')
                    if not any(b.get('batchId') == batch_id for b in scanned_batches):
                        scanned_batches.append({
                            **batch_info,
                            'lastScanned': scan.get('timestamp'),
                            'scanCount': sum(1 for s in my_scans if s.get('batchId') == batch_id)
                        })
        
        # Also check legacy scans in batches
        for batch in batches_data.get('batches', []):
            for scan in batch.get('scans', []):
                if (scan.get('supplierName') == user_name or 
                    str(scan.get('supplierId', '')) == str(user_id)):
                    my_scans.append({
                        **scan,
                        'batchId': batch.get('batchId'),
                        'productName': batch.get('batchName')
                    })
                    total_scans += 1
                    unique_manufacturers.add(batch.get('manufacturerName', 'Unknown'))
                    
                    # Add batch if not already there
                    batch_id = batch.get('batchId')
                    if not any(b.get('batchId') == batch_id for b in scanned_batches):
                        scanned_batches.append({
                            **batch,
                            'lastScanned': scan.get('timestamp'),
                            'scanCount': sum(1 for s in my_scans if s.get('batchId') == batch_id)
                        })
        
        # Sort scans by timestamp (newest first)
        my_scans.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'userId': user_id,
            'userName': user_name,
            'role': 'supplier',
            'totalScans': total_scans,
            'totalBatches': len(scanned_batches),
            'totalManufacturers': len(unique_manufacturers),
            'scannedBatches': scanned_batches,
            'recentScans': my_scans[:10],
            'manufacturerList': list(unique_manufacturers),
            'allScans': my_scans
        }
    
    def _get_general_user_dashboard(self, user_id: int, user_name: str, batches_data: Dict, scans_data: Dict, products_data: Dict) -> Dict:
        """Get general user dashboard showing batches they have viewed via QR scans"""
        viewed_batches = []
        my_scans = []
        unique_manufacturers = set()
        total_scans = 0
        
        # Find scans by this user (could be stored with username or user ID)
        for scan in scans_data.get('scans', []):
            if (scan.get('supplierName') == user_name or 
                str(scan.get('userId', '')) == str(user_id) or
                scan.get('scannerName') == user_name):
                my_scans.append(scan)
                total_scans += 1
                
                # Find batch/product info for this scan
                batch_info = None
                for batch in batches_data.get('batches', []):
                    if batch.get('batchId') == scan.get('batchId'):
                        batch_info = batch
                        break
                
                if not batch_info:
                    for product in products_data.get('products', []):
                        if product.get('productId') == scan.get('batchId'):
                            batch_info = product
                            break
                
                if batch_info:
                    unique_manufacturers.add(batch_info.get('manufacturerName', 'Unknown'))
                    
                    # Add to viewed batches if not already there
                    batch_id = scan.get('batchId')
                    if not any(b.get('batchId') == batch_id for b in viewed_batches):
                        viewed_batches.append({
                            **batch_info,
                            'lastViewed': scan.get('timestamp'),
                            'viewCount': sum(1 for s in my_scans if s.get('batchId') == batch_id)
                        })
        
        # Sort scans by timestamp (newest first)
        my_scans.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'userId': user_id,
            'userName': user_name,
            'role': 'user',
            'totalScans': total_scans,
            'totalBatches': len(viewed_batches),
            'totalManufacturers': len(unique_manufacturers),
            'viewedBatches': viewed_batches,
            'recentScans': my_scans[:10],
            'manufacturerList': list(unique_manufacturers),
            'allScans': my_scans
        }

    def get_manufacturer_dashboard(self, manufacturer_id: str) -> Dict:
        """Legacy method - redirect to new role-based dashboard"""
        return self.get_user_dashboard(manufacturer_id, 'manufacturer')

    def get_user_products(self, user_id: int) -> List[Dict]:
        """Get all products/batches for a specific user"""
        products_data = self._load_data(self.products_file)
        return [p for p in products_data.get('products', []) if p.get('userId') == user_id]

    def get_user_metadata(self, user_id: int) -> Dict:
        """Get user metadata including their uploads and activity"""
        user_products = self.get_user_products(user_id)
        scans_data = self._load_data(self.scans_file)
        
        user_scans = [
            scan for scan in scans_data.get('scans', [])
            if any(product['productId'] == scan.get('batchId') for product in user_products)
        ]
        
        return {
            'userId': user_id,
            'totalUploads': len(user_products),
            'totalScans': len(user_scans),
            'products': user_products,
            'recentActivity': user_scans[-10:],  # Last 10 scans
            'uploadHistory': [
                {
                    'productId': product['productId'],
                    'batchName': product['batchName'],
                    'uploadedAt': product['createdAt'],
                    'fileHash': product['fileHash'],
                    'txHash': product['txHash']
                }
                for product in user_products
            ]
        }

    def search_products(self, query: str, criteria: str = 'all') -> List[Dict]:
        """Search products by various criteria"""
        products_data = self._load_data(self.products_file)
        search_term = query.lower()
        results = []
        
        for product in products_data.get('products', []):
            match = False
            
            if criteria == 'productId':
                match = search_term in product.get('productId', '').lower()
            elif criteria == 'batchName':
                match = product.get('batchName') and search_term in product['batchName'].lower()
            elif criteria == 'manufacturer':
                match = product.get('manufacturerName') and search_term in product['manufacturerName'].lower()
            elif criteria == 'productType':
                match = product.get('productType') and search_term in product['productType'].lower()
            else:  # 'all'
                match = (
                    search_term in product.get('productId', '').lower() or
                    (product.get('batchName') and search_term in product['batchName'].lower()) or
                    (product.get('manufacturerName') and search_term in product['manufacturerName'].lower()) or
                    (product.get('productType') and search_term in product['productType'].lower())
                )
            
            if match:
                results.append(product)
        
        return results
