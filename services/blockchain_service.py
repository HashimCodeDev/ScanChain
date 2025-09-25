import os
import hashlib
from typing import Optional

class BlockchainService:
    def __init__(self):
        self.contract_address = os.getenv('BSC_CONTRACT_ADDRESS', '0x03D1DC1fC2DB1E831D511B74f5a0Cb34585770d8')
        self.rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/')
        
    def store_product_hash(self, product_id: str, file_hash: str) -> str:
        """Store product hash on BSC blockchain"""
        try:
            # For demo purposes, return a mock transaction hash
            # In production, implement actual blockchain interaction
            mock_tx_hash = f"0x{hashlib.sha256(f'{product_id}{file_hash}'.encode()).hexdigest()}"
            print(f"Mock blockchain storage - Product: {product_id}, Hash: {file_hash}")
            print(f"Mock transaction hash: {mock_tx_hash}")
            return mock_tx_hash
        except Exception as e:
            print(f"Blockchain storage error: {e}")
            raise Exception(f"Failed to store hash on blockchain: {str(e)}")
    
    def get_product_hash(self, product_id: str) -> Optional[str]:
        """Get product hash from BSC blockchain"""
        try:
            # For demo purposes, return a mock hash
            # In production, implement actual blockchain query
            mock_hash = hashlib.sha256(f"mock_file_content_{product_id}".encode()).hexdigest()
            print(f"Mock blockchain query - Product: {product_id}, Hash: {mock_hash}")
            return mock_hash
        except Exception as e:
            print(f"Blockchain query error: {e}")
            return None
    
    def get_product_info(self, product_id: str) -> dict:
        """Get product information from blockchain"""
        try:
            file_hash = self.get_product_hash(product_id)
            if not file_hash:
                return {}
            
            # Mock product info for demo
            return {
                'productId': product_id,
                'fileHash': file_hash,
                'contractAddress': self.contract_address,
                'timestamp': 1721390400,  # Mock timestamp
                'blockNumber': 12345678
            }
        except Exception as e:
            print(f"Blockchain product info error: {e}")
            return {}
