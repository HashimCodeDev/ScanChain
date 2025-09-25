// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ProductAuthenticity {
    mapping(string => string) private productHashes;
    mapping(string => address) private productOwners;
    mapping(string => uint256) private productTimestamps;
    
    event ProductStored(string indexed productId, string fileHash, address indexed owner);
    event ProductUpdated(string indexed productId, string newFileHash, address indexed owner);
    
    modifier onlyProductOwner(string memory productId) {
        require(productOwners[productId] == msg.sender || productOwners[productId] == address(0), "Not authorized");
        _;
    }
    
    /**
     * @dev Store a product hash on the blockchain
     * @param productId Unique identifier for the product
     * @param fileHash SHA-256 hash of the product file
     */
    function storeProductHash(string memory productId, string memory fileHash) public {
        require(bytes(productId).length > 0, "Product ID cannot be empty");
        require(bytes(fileHash).length > 0, "File hash cannot be empty");
        
        bool isUpdate = bytes(productHashes[productId]).length > 0;
        
        productHashes[productId] = fileHash;
        productOwners[productId] = msg.sender;
        productTimestamps[productId] = block.timestamp;
        
        if (isUpdate) {
            emit ProductUpdated(productId, fileHash, msg.sender);
        } else {
            emit ProductStored(productId, fileHash, msg.sender);
        }
    }
    
    /**
     * @dev Retrieve a product hash from the blockchain
     * @param productId Unique identifier for the product
     * @return The SHA-256 hash of the product file
     */
    function getProductHash(string memory productId) public view returns (string memory) {
        return productHashes[productId];
    }
    
    /**
     * @dev Get product information including owner and timestamp
     * @param productId Unique identifier for the product
     * @return fileHash The SHA-256 hash
     * @return owner The address that stored the hash
     * @return timestamp When the hash was stored
     */
    function getProductInfo(string memory productId) public view returns (
        string memory fileHash,
        address owner,
        uint256 timestamp
    ) {
        return (
            productHashes[productId],
            productOwners[productId],
            productTimestamps[productId]
        );
    }
    
    /**
     * @dev Check if a product exists
     * @param productId Unique identifier for the product
     * @return True if product exists, false otherwise
     */
    function productExists(string memory productId) public view returns (bool) {
        return bytes(productHashes[productId]).length > 0;
    }
}
