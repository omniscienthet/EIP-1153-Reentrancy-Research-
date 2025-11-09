# Research Methodology: Phase 1 - Hypothesis Formation

**Phase:** Initial Research & Hypothesis Development  
**Duration:** September 2025  
**Objective:** Identify potential EIP-1153 attack vectors in NFT marketplace protocols

---

## Research Question

**Primary Question:**
> Can EIP-1153 transient storage enable novel reentrancy attacks in NFT Marketplace Protocol v1.6's hook system?

**Sub-Questions:**
1. Does NFT Marketplace Protocol v1.6 implement EIP-1153 in production?
2. Can TSTORE/TLOAD bypass traditional reentrancy guards?
3. What is the attack surface of the hook callback system?
4. How can transient storage be exploited during order fulfillment?

---

## Background Research

### EIP-1153 Overview

**Specification:** [EIP-1153: Transient Storage Opcodes](https://eips.ethereum.org/EIPS/eip-1153)

**Key Properties:**
- Transaction-scoped persistence
- Clears after transaction completion
- ~100 gas per operation vs 20,000+ for SSTORE
- Introduced in Cancun upgrade (March 2024)
- Available in Solidity 0.8.24+

**Security Implications:**
```
Traditional Storage:
- SSTORE/SLOAD persist across transactions
- Reentrancy guards: set flag → execute → clear flag
- Flag persists even if external call reenters

Transient Storage:
- TSTORE/TLOAD cleared after transaction
- Reentrancy guards: cheaper but same pattern?
- State persists during nested calls
- NEW: Could enable cross-contract state sharing?
```

### NFT Marketplace Protocol v1.6 Architecture

**Deployment Details:**
```
Contract:    NFT Marketplace Protocol v1.6
Address:     0x0000000000000068F116a894984e2DB1123eB395
Deployed:    April 26, 2024
Network:     Ethereum Mainnet (all EVM chains)
Compiler:    Solidity 0.8.24+ (requires Cancun)
```

**New Features:**
- Hook system (pre/post transfer callbacks)
- Zone-based order validation
- Consideration extensions
- Aggregate fulfillment optimizations

**Hook Callback Points:**
```solidity
interface IMarketplaceProtocolHook {
    function beforeOrderValidation(...) external returns (bytes4);
    function afterOrderValidation(...) external returns (bytes4);
    function beforeOrderFulfillment(...) external returns (bytes4);
    function afterOrderFulfillment(...) external returns (bytes4);
}
```

---

## Initial Hypothesis

### Hypothesis 1: TSTORE Reentrancy in Hooks

**Theory:**
A malicious hook contract could use TSTORE to maintain attack state across reentrant calls, bypassing traditional reentrancy guards that only check persistent storage.

**Attack Flow:**
```
1. User creates order with malicious zone
2. Target Protocol calls beforeOrderValidation()
3. Malicious hook:
   - Stores attack state in TSTORE
   - Performs reentrant call to Target Protocol
4. Reentrant call reads corrupted TSTORE state
5. Validation bypassed
6. Order fulfilled incorrectly
```

**Expected Impact:**
- Order validation bypass
- Asset theft from users
- Protocol-wide exploitation

### Hypothesis 2: Hook State Manipulation

**Theory:**
Hooks executing during order fulfillment could manipulate transient storage to affect validation logic, even without reentrancy.

**Attack Flow:**
```
1. beforeOrderValidation() sets malicious TSTORE state
2. Target Protocol reads TSTORE for validation decision
3. Order incorrectly passes validation
4. afterOrderFulfillment() cleans up evidence
```

### Hypothesis 3: Cross-Hook TSTORE Pollution

**Theory:**
Multiple hooks in a single transaction could share transient storage slots, allowing one malicious hook to poison state for other hooks.

**Attack Flow:**
```
1. Transaction includes multiple orders
2. First order uses malicious hook A
3. Hook A: tstore(0x1, MALICIOUS_VALUE)
4. Second order uses legitimate hook B
5. Hook B reads from tstore(0x1)
6. Hook B corrupted by Hook A's state
```

---

## Research Assumptions

### Assumption 1: Production Uses EIP-1153
**Status:**  **INVALID** (later disproven)

**Initial Reasoning:**
- NFT Marketplace Protocol v1.6 released April 2024 (after Cancun)
- Requires Solidity 0.8.24+ (has TSTORE support)
- Gas optimization would benefit from cheap transient storage
- Hook system seems designed for TSTORE

**Reality:**
Production bytecode contains ZERO TSTORE/TLOAD opcodes.

### Assumption 2: Hooks Can Reenter Target Protocol
**Status:**  **PARTIALLY VALID**

**Reasoning:**
- Hooks are external calls to untrusted contracts
- No explicit documentation preventing reentrancy
- CallbackValidation may not cover all cases

**Reality:**
Reentrancy possible but protected by existing guards.

### Assumption 3: TSTORE Bypasses Guards
**Status:**  **INVALID**

**Reasoning:**
- Traditional guards use SSTORE
- TSTORE might not trigger same protections

**Reality:**
Production doesn't use TSTORE, making this irrelevant.

### Assumption 4: Victim Uses Malicious Zone
**Status:**  **CRITICAL FLAW**

**Reasoning:**
- Initial assumption: victims would accept any zone

**Reality:**
- Users choose their own zones
- Won't select attacker's malicious contract
- Invalid threat model

---

## Hypothesis Testing Plan

### Phase 1: Source Code Review

**Objectives:**
- Locate TSTORE/TLOAD usage in Target Protocol
- Identify hook implementation details
- Map attack surface

**Methods:**
```bash
# Fetch verified source
cast etherscan-source 0x0000000000000068F116a894984e2DB1123eB395

# Search for transient storage
grep -r "tstore\|tload\|transient" src/

# Analyze hook functions
grep -r "beforeOrder\|afterOrder" src/
```

### Phase 2: Bytecode Analysis

**Objectives:**
- Verify EIP-1153 usage in production
- Confirm or refute Assumption 1

**Methods:**
```python
# Automated opcode scanning
def verify_eip1153(address):
    bytecode = fetch_bytecode(address)
    has_tstore = '5d' in bytecode
    has_tload = '5c' in bytecode
    return has_tstore or has_tload
```

### Phase 3: Proof of Concept Development

**Objectives:**
- Demonstrate TSTORE reentrancy
- Validate attack feasibility
- Measure gas costs

**Approach:**
```solidity
contract MaliciousHook {
    function beforeOrderValidation(...) external {
        // Store attack state
        assembly { tstore(0x0, 1) }
        
        // Attempt reentrancy
        IMarketplaceProtocol(SEAPORT).fulfillOrder(...);
        
        // Verify state persistence
        uint256 state;
        assembly { state := tload(0x0) }
        require(state == 1);  // Did it persist?
    }
}
```

### Phase 4: Testnet Validation

**Objectives:**
- Deploy PoC to Sepolia
- Execute attack
- Gather on-chain evidence

**Deployment Plan:**
```javascript
// Deploy malicious hook
const hook = await MaliciousHook.deploy();

// Create order with malicious zone
const order = {
    zone: hook.address,
    // ... other params
};

// Execute attack
await marketplace protocol.fulfillOrder(order);
```

---

## Expected Outcomes

### Scenario A: Hypothesis Confirmed
**If production uses TSTORE:**
- Develop working exploit
- Demonstrate asset theft
- Submit coordinated disclosure
- Expected severity: Critical (P1)

### Scenario B: Hypothesis Refuted
**If production doesn't use TSTORE:**
- Pivot to alternative attack vectors
- Analyze hook system without TSTORE
- Focus on traditional vulnerabilities
- Document lessons learned

### Scenario C: Partial Confirmation
**If some components use TSTORE:**
- Identify specific vulnerable components
- Assess real-world exploitability
- Consider impact limitations
- Expected severity: High (P2) or Medium (P3)

---

## Success Criteria

### Research Success

**Criteria:**
1.  Determine if Target Protocol uses EIP-1153
2.  Identify actual attack surface
3.  Develop working PoC (if applicable)
4.  Document findings comprehensively

### Vulnerability Disclosure Success

**Criteria:**
1. Demonstrate real production vulnerability
2. Prove financial impact
3. Provide clear reproduction steps
4. No custom contract deployment
5. Mainnet fork validation

---

## Risk Assessment

### Research Risks

**Risk 1: False Positive**
- Likelihood: High
- Impact: Wasted time
- Mitigation: Bytecode verification first

**Risk 2: Invalid Threat Model**
- Likelihood: Medium
- Impact: Rejection
- Mitigation: Understand victim interaction model

**Risk 3: Out of Scope**
- Likelihood: Low
- Impact: Wasted effort
- Mitigation: Verify scope before deep research

---

## Timeline

```
Week 1: Hypothesis formation and background research
Week 2: Source code and bytecode analysis
Week 3: PoC development
Week 4: Testnet deployment and validation
Week 5: Documentation and potential disclosure
```

**Actual Timeline:**
- Week 1-3: Research and PoC development
- Week 4: Submission and feedback
- Week 5: Bytecode discovery (hypothesis refuted)
- Week 6: Pivot to valid attack vectors

---

## Initial Assumptions Summary

| Assumption | Initial Belief | Validation Method | Actual Result |
|------------|---------------|-------------------|---------------|
| Production uses TSTORE | Yes | Bytecode analysis |  NO |
| Hooks enable reentrancy | Yes | Code review |  Protected |
| TSTORE bypasses guards | Yes | Testing |  Irrelevant |
| Users accept any zone | Yes | Threat modeling |  User choice |

---

## Lessons for Future Research

### Start with Verification

**Wrong approach:**
```
1. Form hypothesis
2. Build PoC
3. Deploy to testnet
4. Discover production doesn't match
```

**Correct approach:**
```
1. Form hypothesis
2. VERIFY production bytecode
3. If confirmed → build PoC
4. If refuted → pivot immediately
```

### Question All Assumptions

Every assumption should be verified:
- Does it exist in production?
- Can victims be forced into vulnerable state?
- Is custom deployment required?
- What's the real threat model?

---

**Phase Status:**  Complete  
**Hypothesis Result:**  Refuted (production doesn't use TSTORE)  
**Research Value:**  High (methodology established)  
**Next Phase:** [02-bytecode-analysis.md](./02-bytecode-analysis.md)
