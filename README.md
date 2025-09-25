# ScanChain - Product Authenticity Verification

ScanChain is a blockchain-based product authenticity verification system built on BNB Greenfield for decentralized storage and BNB Smart Chain for immutable hash storage. The system allows manufacturers to upload product documents and generate QR codes for consumer verification.

## 🌟 Features

- **File Storage**: Secure file storage on BNB Greenfield Testnet
- **Blockchain Verification**: Immutable hash storage on BSC Testnet
- **QR Code Generation**: Dynamic QR codes for easy product verification
- **REST API**: Clean API endpoints for upload and verification
- **Hash Verification**: SHA-256 hash comparison for tamper detection
- **Multi-format Support**: PDF and JSON file support

## 🎥 Demo Video

[**Watch ScanChain Demo**](https://drive.google.com/file/d/1ZsiyckN-RSQg4RmrPDLJEAWvYBmvjAen/view?usp=sharing)

See ScanChain in action - from product upload to QR code verification!

## 🛠️ Tech Stack

- **Backend**: Python with Flask
- **Blockchain**: BNB Smart Chain (BSC) Testnet
- **Storage**: BNB Greenfield Testnet
- **Hashing**: SHA-256 via hashlib
- **QR Codes**: qrcode library
- **Smart Contract**: Solidity

## 📋 Prerequisites

Before running this project, ensure you have:

- Python (v3.8 or later)
- pip
- BSC Testnet account with test BNB
- BNB Greenfield Testnet account
- Git

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/HashimCodeDev/ScanChain.git
cd ScanChain
uv sync
```

### 2. Environment Setup

Copy the environment file and configure:

```bash
cp .env.example .env
```

Update `.env` with your credentials:

```env
# BNB Greenfield Configuration
GREENFIELD_ADDRESS=your_testnet_address
GREENFIELD_PRIVATE_KEY=your_testnet_private_key

# BNB Smart Chain Configuration  
CONTRACT_ADDRESS=0x...
BSC_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
BSC_PRIVATE_KEY=your_bsc_private_key

# Server Configuration
PORT=3000
NODE_ENV=development

# Greenfield Testnet Configuration
GREENFIELD_RPC_URL=https://gnfd-testnet-fullnode-tendermint-us.bnbchain.org:443
GREENFIELD_CHAIN_ID=5600
```

### 3. Deploy Smart Contract

Deploy the contract using Remix IDE:
- Contract code: `contracts/ProductAuthenticity.sol`
- Network: BSC Testnet (Chain ID: 97)
- Update `CONTRACT_ADDRESS` in `.env` after deployment

### 4. Run Tests

```bash
uv run python test_app.py
```

### 5. Start Server

```bash
uv run python app.py
# or
uv run python run.py
```

The server will start on `http://localhost:5000`

## 📡 API Endpoints

### Health Check
```http
GET /api/health
```

### Upload Product File
```http
POST /api/upload
Content-Type: multipart/form-data

Body:
- productId: string (required)
- file: file (PDF or JSON, max 10MB)
```

**Response:**
```json
{
  "success": true,
  "productId": "ABC123456789",
  "fileHash": "sha256_hash_here",
  "greenfieldUrl": "https://gnfd-testnet-sp1.bnbchain.org/bucket/file",
  "txHash": "0x...",
  "qrCode": "data:image/png;base64,..."
}
```

### Verify Product
```http
POST /api/verify
Content-Type: application/json

{
  "productId": "ABC123456789",
  "greenfieldUrl": "https://gnfd-testnet-sp1.bnbchain.org/bucket/file"
}
```

**Response:**
```json
{
  "success": true,
  "isVerified": true,
  "productId": "ABC123456789",
  "storedHash": "original_hash",
  "currentHash": "current_hash",
  "message": "Product is authentic"
}
```

### Get Product Info
```http
GET /api/product/:productId
```

### QR Code Operations

#### Generate QR Code
```http
POST /api/qr/generate
{
  "productId": "ABC123456789",
  "contractAddress": "0x...",
  "metadata": {
    "manufacturer": "Company Name",
    "productName": "Product Name"
  }
}
```

#### Parse QR Code
```http
POST /api/qr/parse
{
  "qrData": "qr_code_json_string"
}
```

#### Scan QR Code
```http
POST /api/qr/scan
{
  "qrData": "qr_code_json_string"
}
```

## 🏗️ Project Structure

```
ScanChain/
├── contracts/
│   └── ProductAuthenticity.sol      # Smart contract
├── services/
│   ├── greenfield_service.py        # BNB Greenfield integration
│   ├── blockchain_service.py        # BSC integration
│   ├── qr_service.py                # QR code utilities
│   ├── auth_service.py              # Authentication service
│   └── database_service.py          # Database operations
├── routes/
│   └── auth_routes.py               # Authentication routes
├── public/
│   ├── *.html                       # Frontend files
├── data/
│   └── *.json                       # Data storage files
├── app.py                           # Main Flask application
├── run.py                           # Server runner
├── test_app.py                      # Test suite
├── pyproject.toml                   # Python dependencies (uv)
├── .env
└── README.md
```

## 🔧 Smart Contract Functions

The `ProductAuthenticity.sol` contract provides:

- `storeProductHash(string productId, string fileHash)` - Store product hash
- `getProductHash(string productId)` - Retrieve product hash
- `getProductInfo(string productId)` - Get full product information
- `productExists(string productId)` - Check if product exists

## 🌐 Network Configuration

### BSC Testnet
- **RPC URL**: https://data-seed-prebsc-1-s1.binance.org:8545
- **Chain ID**: 97
- **Symbol**: tBNB
- **Explorer**: https://testnet.bscscan.com/
- **Faucet**: https://testnet.binance.org/faucet-smart

### BNB Greenfield Testnet
- **RPC URL**: https://gnfd-testnet-fullnode-tendermint-us.bnbchain.org:443
- **Chain ID**: 5600
- **Explorer**: https://testnet.greenfieldscan.com/

## 🧪 Testing

Run the test suite to verify functionality:

```bash
uv run python test_app.py
```

This will test:
- Environment variables
- Python dependencies
- Hash generation
- JSON processing
- Service availability

## 🔒 Security Features

- **Input Validation**: All inputs are validated and sanitized
- **File Type Restrictions**: Only PDF and JSON files allowed
- **Size Limits**: 10MB maximum file size
- **Error Handling**: Comprehensive error handling and logging
- **Environment Variables**: Sensitive data stored in environment variables

## 🚨 Error Handling

The API returns consistent error responses:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common error codes:
- `400`: Bad Request (validation errors)
- `404`: Not Found (product not found)
- `500`: Internal Server Error
- `503`: Service Unavailable (blockchain/storage issues)

## 📈 Development

### Adding New Features

1. Create new service files in `services/`
2. Add routes in `routes/`
3. Update validation in Flask app
4. Add tests in `test_app.py`

### Environment Variables

Required variables:
- `GREENFIELD_ADDRESS` - Your Greenfield address
- `GREENFIELD_PRIVATE_KEY` - Greenfield private key
- `CONTRACT_ADDRESS` - Deployed contract address
- `BSC_PRIVATE_KEY` - BSC account private key

Optional variables:
- `PORT` - Server port (default: 3000)
- `NODE_ENV` - Environment mode

## 🐛 Troubleshooting

### Common Issues

1. **Contract not deployed**: Deploy using Remix IDE with the provided Solidity contract
2. **Network issues**: Check RPC URLs and internet connection
3. **Private key errors**: Ensure keys are valid and have test funds
4. **File upload fails**: Check file size and type restrictions

### Development Mode

The application includes fallbacks for development:
- Mock Greenfield URLs when service unavailable
- Mock blockchain transactions when contract not deployed
- Detailed error messages in development mode

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Run `uv run python test_app.py` to verify setup
- Review server logs for error details

## 🎯 Roadmap

Future enhancements:
- [ ] Frontend web application
- [ ] Mobile app for QR scanning
- [ ] Batch upload functionality
- [ ] Advanced analytics dashboard
- [ ] Multi-chain support
- [ ] IPFS integration as backup storage

---

Built with ❤️ for the BNB Chain ecosystem
