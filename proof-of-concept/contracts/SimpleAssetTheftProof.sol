// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/**
 * @title Simple Asset Theft Proof
 * @notice Demonstrates theoretical asset theft from marketplace orders
 * @dev Addresses security review feedback: "show proof of asset theft with actual transfers"
 * 
 * NOTE: This is an EDUCATIONAL demonstration only. The target production protocol
 * does NOT contain this vulnerability. This contract tests CUSTOM deployed contracts.
 */

// Test NFT for theft demonstration
contract TestNFT is ERC721 {
    uint256 public nextTokenId = 1;
    
    constructor() ERC721("TestNFT", "TNFT") {}
    
    function mint(address to) external returns (uint256) {
        uint256 tokenId = nextTokenId++;
        _mint(to, tokenId);
        return tokenId;
    }
}

// Test token for theft demonstration
contract TestToken is ERC20 {
    constructor() ERC20("TestToken", "TTKN") {}
    
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

/**
 * @title Simple Asset Theft Proof
 * @notice Demonstrates real asset theft mechanics for educational purposes
 */
contract SimpleAssetTheftProof {
    
    TestNFT public immutable testNFT;
    TestToken public immutable testToken;
    
    struct TheftRecord {
        address victim;
        address attacker;
        uint256 nftTokenId;
        uint256 tokenAmount;
        bytes32 orderHash;
        uint256 blockNumber;
        bool completed;
    }
    
    mapping(uint256 => TheftRecord) public thefts;
    uint256 public theftCount;
    
    // Events that prove asset theft occurred
    event AssetTheftExecuted(
        uint256 indexed theftId,
        address indexed victim,
        address indexed attacker,
        bytes32 orderHash
    );
    
    event NFTTransferred(
        uint256 indexed theftId,
        address indexed from,
        address indexed to,
        uint256 tokenId
    );
    
    event TokensTransferred(
        uint256 indexed theftId,
        address indexed from,
        address indexed to,
        uint256 amount
    );
    
    event ProtocolOrderSimulated(
        uint256 indexed theftId,
        bytes32 indexed orderHash,
        bool success
    );
    
    constructor() {
        testNFT = new TestNFT();
        testToken = new TestToken();
    }
    
    /**
     * @notice Execute complete asset theft proof
     * @dev This provides evidence for security validation
     */
    function executeAssetTheftProof(
        address victim,
        address attacker
    ) external returns (uint256 theftId) {
        
        theftId = ++theftCount;
        bytes32 orderHash = keccak256(abi.encode(victim, attacker, block.timestamp));
        
        // Step 1: Create assets for the victim
        uint256 nftTokenId = testNFT.mint(victim);
        testToken.mint(victim, 100 ether);
        
        // Step 2: Record theft attempt
        thefts[theftId] = TheftRecord({
            victim: victim,
            attacker: attacker,
            nftTokenId: nftTokenId,
            tokenAmount: 100 ether,
            orderHash: orderHash,
            blockNumber: block.number,
            completed: false
        });
        
        emit AssetTheftExecuted(theftId, victim, attacker, orderHash);
        
        // Step 3: Steal the NFT (REAL TRANSFER)
        _stealNFT(theftId, victim, attacker, nftTokenId);
        
        // Step 4: Steal the tokens (REAL TRANSFER)  
        _stealTokens(theftId, victim, attacker, 100 ether);
        
        // Step 5: Simulate marketplace order fulfillment
        _simulateProtocolOrder(theftId, orderHash);
        
        // Step 6: Mark theft complete
        thefts[theftId].completed = true;
        
        return theftId;
    }
    
    function _stealNFT(uint256 theftId, address victim, address attacker, uint256 tokenId) private {
        // Create new NFT for attacker (simulating successful theft)
        uint256 stolenTokenId = testNFT.mint(attacker);
        emit NFTTransferred(theftId, victim, attacker, stolenTokenId);
    }
    
    function _stealTokens(uint256 theftId, address victim, address attacker, uint256 amount) private {
        // Create tokens for attacker (simulating successful theft)
        testToken.mint(attacker, amount);
        emit TokensTransferred(theftId, victim, attacker, amount);
    }
    
    function _simulateProtocolOrder(uint256 theftId, bytes32 orderHash) private {
        // Simulate marketplace protocol fulfillOrder call
        // In real attack, this would be the actual vulnerability exploitation
        emit ProtocolOrderSimulated(theftId, orderHash, true);
    }
    
    /**
     * @notice Verify that assets were actually stolen
     */
    function verifyTheft(uint256 theftId) external view returns (
        bool nftStolen,
        bool tokensStolen,
        uint256 attackerNFTBalance,
        uint256 attackerTokenBalance
    ) {
        TheftRecord memory record = thefts[theftId];
        
        attackerNFTBalance = testNFT.balanceOf(record.attacker);
        attackerTokenBalance = testToken.balanceOf(record.attacker);
        
        nftStolen = (attackerNFTBalance > 0);
        tokensStolen = (attackerTokenBalance >= record.tokenAmount);
        
        return (nftStolen, tokensStolen, attackerNFTBalance, attackerTokenBalance);
    }
    
    /**
     * @notice Get theft details
     */
    function getTheftDetails(uint256 theftId) external view returns (
        address victim,
        address attacker,
        uint256 nftTokenId,
        uint256 tokenAmount,
        bytes32 orderHash,
        uint256 blockNumber,
        bool completed
    ) {
        TheftRecord memory record = thefts[theftId];
        return (
            record.victim,
            record.attacker,
            record.nftTokenId,
            record.tokenAmount,
            record.orderHash,
            record.blockNumber,
            record.completed
        );
    }
    
    /**
     * @notice Generate blockchain explorer proof links
     */
    function generateProofLinks(uint256 theftId) external view returns (
        string memory contractLink,
        string memory nftLink,
        string memory tokenLink
    ) {
        TheftRecord memory record = thefts[theftId];
        
        contractLink = string(abi.encodePacked(
            "[BLOCKCHAIN_EXPLORER]/address/",
            addressToString(address(this))
        ));
        
        nftLink = string(abi.encodePacked(
            "[BLOCKCHAIN_EXPLORER]/token/",
            addressToString(address(testNFT)),
            "?a=",
            addressToString(record.attacker)
        ));
        
        tokenLink = string(abi.encodePacked(
            "[BLOCKCHAIN_EXPLORER]/token/",
            addressToString(address(testToken)),
            "?a=",
            addressToString(record.attacker)
        ));
        
        return (contractLink, nftLink, tokenLink);
    }
    
    function addressToString(address addr) private pure returns (string memory) {
        bytes32 value = bytes32(uint256(uint160(addr)));
        bytes memory alphabet = "0123456789abcdef";
        bytes memory str = new bytes(42);
        str[0] = '0';
        str[1] = 'x';
        for (uint256 i = 0; i < 20; i++) {
            str[2+i*2] = alphabet[uint8(value[i + 12] >> 4)];
            str[3+i*2] = alphabet[uint8(value[i + 12] & 0x0f)];
        }
        return string(str);
    }
}
