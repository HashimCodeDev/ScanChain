import json
import qrcode
import io
import base64
from typing import Dict

class QRService:
    def __init__(self):
        self.qr_version = 1
        self.error_correction = qrcode.constants.ERROR_CORRECT_L
        self.box_size = 10
        self.border = 4
    
    def generate_qr_data(self, product_id: str, contract_address: str, additional_data: Dict = None) -> str:
        """Generate QR code data with product information"""
        qr_data = {
            'productId': product_id,
            'contractAddress': contract_address,
            'timestamp': '2025-07-19T12:00:00Z',
            'version': '1.0'
        }
        
        if additional_data:
            qr_data.update(additional_data)
        
        return json.dumps(qr_data)
    
    def create_qr_code(self, data: str) -> str:
        """Create QR code image and return as base64 string"""
        try:
            qr = qrcode.QRCode(
                version=self.qr_version,
                error_correction=self.error_correction,
                box_size=self.box_size,
                border=self.border,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        
        except Exception as e:
            print(f"QR code generation error: {e}")
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    def generate_product_qr(self, product_id: str, contract_address: str, 
                          additional_data: Dict = None) -> Dict:
        """Generate complete QR code data and image for a product"""
        try:
            qr_data = self.generate_qr_data(product_id, contract_address, additional_data)
            qr_image = self.create_qr_code(qr_data)
            
            return {
                'qrData': qr_data,
                'qrImage': qr_image,
                'productId': product_id,
                'contractAddress': contract_address
            }
        
        except Exception as e:
            print(f"Product QR generation error: {e}")
            raise Exception(f"Failed to generate product QR: {str(e)}")
