#!/usr/bin/env python3
"""
EIP-1153 Bytecode Scanner

Automated tool for detecting TSTORE/TLOAD opcode usage in production smart contracts.
Part of the EIP-1153 Transient Storage Security Research project.

Usage:
    python3 eip1153_scanner.py <contract_address>
    python3 eip1153_scanner.py --batch contracts.txt
"""

import sys
import json
from web3 import Web3
from typing import Dict, List, Optional
import os

class EIP1153Scanner:
    """Scanner for detecting EIP-1153 transient storage usage in contract bytecode."""
    
    # EVM Opcodes
    TSTORE_OPCODE = '5d'
    TLOAD_OPCODE = '5c'
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize scanner with Web3 connection.
        
        Args:
            rpc_url: Ethereum RPC endpoint (defaults to environment variable)
        """
        if rpc_url is None:
            rpc_key = os.getenv('RPC_API_KEY') or os.getenv('ALCHEMY_API_KEY')
            if not rpc_key:
                raise ValueError("RPC_API_KEY environment variable not set")
            rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{rpc_key}"
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")
    
    def fetch_bytecode(self, address: str) -> str:
        """
        Fetch contract bytecode from blockchain.
        
        Args:
            address: Contract address (with or without 0x prefix)
            
        Returns:
            Hex-encoded bytecode string
        """
        if not address.startswith('0x'):
            address = '0x' + address
        
        checksum_address = Web3.to_checksum_address(address)
        bytecode = self.w3.eth.get_code(checksum_address)
        
        return bytecode.hex()
    
    def scan_for_opcodes(self, bytecode: str) -> Dict[str, int]:
        """
        Scan bytecode for TSTORE and TLOAD opcodes.
        
        Args:
            bytecode: Hex-encoded bytecode string
            
        Returns:
            Dictionary with opcode counts
        """
        # Remove 0x prefix if present
        if bytecode.startswith('0x'):
            bytecode = bytecode[2:]
        
        # Count opcode occurrences
        tstore_count = bytecode.count(self.TSTORE_OPCODE)
        tload_count = bytecode.count(self.TLOAD_OPCODE)
        
        return {
            'tstore': tstore_count,
            'tload': tload_count,
            'total_eip1153': tstore_count + tload_count
        }
    
    def analyze_contract(self, address: str) -> Dict:
        """
        Complete analysis of contract for EIP-1153 usage.
        
        Args:
            address: Contract address
            
        Returns:
            Analysis results dictionary
        """
        print(f"🔍 Analyzing contract: {address}")
        
        # Fetch bytecode
        try:
            bytecode = self.fetch_bytecode(address)
        except Exception as e:
            return {
                'address': address,
                'error': str(e),
                'success': False
            }
        
        # Scan for opcodes
        opcode_counts = self.scan_for_opcodes(bytecode)
        
        # Build result
        result = {
            'address': address,
            'bytecode_size': len(bytecode) // 2,  # Convert hex chars to bytes
            'tstore_count': opcode_counts['tstore'],
            'tload_count': opcode_counts['tload'],
            'uses_eip1153': opcode_counts['total_eip1153'] > 0,
            'success': True
        }
        
        return result
    
    def print_analysis(self, result: Dict):
        """Print formatted analysis results."""
        if not result['success']:
            print(f"❌ Error analyzing {result['address']}: {result.get('error', 'Unknown error')}")
            return
        
        print("\n" + "="*60)
        print(f"📊 EIP-1153 Bytecode Analysis Results")
        print("="*60)
        print(f"Contract Address:  {result['address']}")
        print(f"Bytecode Size:     {result['bytecode_size']:,} bytes")
        print(f"TSTORE (0x5d):     {result['tstore_count']} occurrences")
        print(f"TLOAD (0x5c):      {result['tload_count']} occurrences")
        print(f"Uses EIP-1153:     {'✅ YES' if result['uses_eip1153'] else '❌ NO'}")
        print("="*60)
        
        if result['uses_eip1153']:
            print("\n⚠️  This contract uses transient storage!")
            print("Potential attack surface identified.")
        else:
            print("\n✅ This contract does NOT use transient storage.")
            print("EIP-1153 attack vectors are NOT applicable.")
        print()
    
    def batch_analyze(self, addresses: List[str]) -> List[Dict]:
        """
        Analyze multiple contracts.
        
        Args:
            addresses: List of contract addresses
            
        Returns:
            List of analysis results
        """
        results = []
        
        print(f"🔍 Batch analyzing {len(addresses)} contracts...\n")
        
        for i, address in enumerate(addresses, 1):
            print(f"[{i}/{len(addresses)}] ", end='')
            result = self.analyze_contract(address)
            results.append(result)
            
            if i < len(addresses):
                print()  # Spacing between analyses
        
        return results
    
    def export_results(self, results: List[Dict], output_file: str):
        """
        Export analysis results to JSON file.
        
        Args:
            results: List of analysis results
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results exported to: {output_file}")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single contract: python3 eip1153_scanner.py <address>")
        print("  Batch mode:      python3 eip1153_scanner.py --batch <file>")
        print("\nExample:")
        print("  python3 eip1153_scanner.py 0x1234567890abcdef1234567890abcdef12345678")
        sys.exit(1)
    
    scanner = EIP1153Scanner()
    
    if sys.argv[1] == '--batch':
        if len(sys.argv) < 3:
            print("Error: Batch mode requires input file")
            sys.exit(1)
        
        # Read addresses from file
        with open(sys.argv[2], 'r') as f:
            addresses = [line.strip() for line in f if line.strip()]
        
        # Batch analyze
        results = scanner.batch_analyze(addresses)
        
        # Print summary
        print("\n" + "="*60)
        print("📈 Batch Analysis Summary")
        print("="*60)
        
        total = len(results)
        with_eip1153 = sum(1 for r in results if r.get('uses_eip1153', False))
        
        print(f"Total Contracts:        {total}")
        print(f"Using EIP-1153:         {with_eip1153}")
        print(f"Not Using EIP-1153:     {total - with_eip1153}")
        print(f"Adoption Rate:          {with_eip1153/total*100:.1f}%")
        print("="*60)
        
        # Export results
        output_file = 'eip1153_scan_results.json'
        scanner.export_results(results, output_file)
    
    else:
        # Single contract mode
        address = sys.argv[1]
        result = scanner.analyze_contract(address)
        scanner.print_analysis(result)


if __name__ == '__main__':
    main()


# Example usage for common scenarios
"""
# Scan a single contract
python3 eip1153_scanner.py 0x1234...

# Batch scan from file
python3 eip1153_scanner.py --batch contracts.txt

# Use in scripts
from eip1153_scanner import EIP1153Scanner

scanner = EIP1153Scanner()
result = scanner.analyze_contract('0x1234...')
if result['uses_eip1153']:
    print("Contract uses transient storage!")
"""
