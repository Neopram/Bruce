#!/usr/bin/env python3
"""
Train Bruce AI - Crypto Domain Knowledge
Ingests structured cryptocurrency and blockchain knowledge into the knowledge base.
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_ingestor import KnowledgeIngestor

# ---------------------------------------------------------------------------
#  Crypto Knowledge Topics
# ---------------------------------------------------------------------------

CRYPTO_TOPICS = {
    "blockchain_basics": {
        "title": "Blockchain Fundamentals",
        "content": """
Blockchain is a distributed, immutable ledger technology that records transactions across a
network of computers without requiring a central authority.

Core Concepts:
- Block: A collection of transactions bundled together with a header containing the previous
  block's hash, a timestamp, a nonce, and a Merkle root of all transactions.
- Chain: Blocks linked by cryptographic hashes forming a tamper-evident sequence.
- Consensus Mechanisms:
  - Proof of Work (PoW): Miners solve computational puzzles. Used by Bitcoin. Energy intensive.
  - Proof of Stake (PoS): Validators stake tokens as collateral. Used by Ethereum post-Merge.
  - Delegated Proof of Stake (DPoS): Token holders vote for delegates. Used by EOS, Tron.
  - Proof of Authority (PoA): Pre-approved validators. Used in private chains.

Key Properties:
- Immutability: Once confirmed, transactions cannot be reversed or altered.
- Transparency: All transactions are publicly visible on public blockchains.
- Decentralization: No single point of failure or control.
- Finality: Transaction confirmation is probabilistic (PoW) or deterministic (PoS BFT).

Major Blockchains:
- Bitcoin (BTC): First blockchain (2009). Digital gold, store of value. ~7 TPS.
- Ethereum (ETH): Smart contract platform (2015). Turing-complete EVM. ~30 TPS (L1).
- Solana (SOL): High-throughput chain. Proof of History + PoS. ~4000 TPS.
- Avalanche (AVAX): Subnet architecture. Avalanche consensus. Sub-second finality.
- Polygon (POL): Ethereum scaling solution. Multiple scaling technologies.
- BNB Chain: Binance ecosystem. EVM compatible. Low fees.

Block Explorers: Etherscan, Solscan, Blockchain.com for viewing on-chain data.
"""
    },
    "defi_protocols": {
        "title": "Decentralized Finance (DeFi) Protocols",
        "content": """
DeFi refers to financial services built on blockchain without traditional intermediaries.

Core DeFi Categories:

1. Lending/Borrowing:
   - Aave: Multi-chain lending. Flash loans. Variable/stable rates. ~$10B+ TVL.
   - Compound: Algorithmic interest rates. cToken model. Governance via COMP.
   - MakerDAO: CDP-based lending. Generates DAI stablecoin. Multi-collateral.
   - Key metric: Utilization Rate = Total Borrows / Total Supply.

2. Decentralized Exchanges (DEXs):
   - Uniswap: AMM pioneer. Concentrated liquidity (V3). Dominant on Ethereum.
   - Curve: Optimized for stablecoin and pegged asset swaps. Low slippage.
   - Jupiter: Solana DEX aggregator. Routes across multiple liquidity sources.

3. Yield Aggregators:
   - Yearn Finance: Auto-compounding vaults. Strategy optimization.
   - Convex Finance: Boost Curve yields. Vote-locked CRV.
   - Beefy Finance: Multi-chain yield optimizer.

4. Derivatives:
   - dYdX: Perpetual futures. Order book model. L2 scaling.
   - GMX: Perpetual DEX. GLP liquidity model. Arbitrum/Avalanche.
   - Synthetix: Synthetic assets tracking real-world prices.

Key DeFi Concepts:
- TVL (Total Value Locked): Measure of assets deposited in protocols.
- APY vs APR: APY includes compounding, APR does not.
- Impermanent Loss: Loss from providing liquidity vs holding.
- Liquidation: Forced position closure when collateral ratio drops.
- Flash Loans: Uncollateralized loans that must be repaid in same transaction.
"""
    },
    "dex_cex": {
        "title": "DEX vs CEX - Exchange Types",
        "content": """
Cryptocurrency exchanges come in two main types: centralized (CEX) and decentralized (DEX).

Centralized Exchanges (CEX):
- Operated by a company that maintains order books and custody of funds.
- Top CEXs: Binance, Coinbase, Kraken, OKX, Bybit.
- Advantages: High liquidity, fast execution, fiat on/off ramps, customer support.
- Disadvantages: Custody risk, KYC requirements, potential for censorship.
- Order types: Market, limit, stop-loss, OCO, trailing stop, iceberg.
- Trading pairs: Spot, margin (up to 125x on some platforms), futures, options.

Decentralized Exchanges (DEX):
- Smart contract-based. Users retain custody of funds.
- Types:
  - AMM (Automated Market Maker): Uniswap, PancakeSwap. Liquidity pools.
  - Order Book: dYdX, Serum. Traditional matching engine on-chain or hybrid.
  - Aggregators: 1inch, Jupiter. Route across multiple DEXs for best price.
- Advantages: Non-custodial, permissionless, no KYC, composable.
- Disadvantages: Higher slippage, MEV exposure, gas costs, limited fiat.

Key Trading Metrics:
- Spread: Difference between best bid and ask.
- Slippage: Difference between expected and executed price.
- Depth: Volume available at various price levels.
- Volume: Total traded value in a time period.
- Maker/Taker fees: Fees for adding vs removing liquidity.

CEX vs DEX Volume Split: CEXs handle ~85-90% of crypto trading volume.
DEX volume has grown significantly since 2020 DeFi summer.
"""
    },
    "tokenomics": {
        "title": "Tokenomics - Token Economics",
        "content": """
Tokenomics refers to the economic design and mechanics of a cryptocurrency token.

Supply Mechanics:
- Max Supply: Hard cap on total tokens (Bitcoin: 21M, BNB: 200M).
- Circulating Supply: Tokens currently available in market.
- Fully Diluted Valuation (FDV): Price x Max Supply.
- Market Cap: Price x Circulating Supply.
- Inflation Rate: New token issuance per year.
- Deflation: Token burning reduces supply (ETH post-EIP-1559).

Distribution Models:
- Fair Launch: No pre-mine, no VC allocation (e.g., Bitcoin).
- ICO (Initial Coin Offering): Public token sale.
- IDO (Initial DEX Offering): Launch on decentralized exchange.
- Airdrop: Free distribution to wallet holders or protocol users.
- Vesting: Locked tokens released over time (cliff + linear vesting).
- Team/Investor allocation: Typically 15-30% with vesting schedules.

Token Utility Types:
- Governance: Voting on protocol decisions (UNI, AAVE, COMP).
- Staking: Lock tokens for network security rewards.
- Fee payment: Gas fees, transaction fees, service fees.
- Collateral: Used to back loans or synthetic assets.
- Access: Required to use certain platform features.

Valuation Frameworks:
- P/E Ratio: Market Cap / Annual Protocol Revenue.
- P/S Ratio: Market Cap / Annual Fees Generated.
- Token Velocity: Transaction Volume / Average Token Value.
- NVT Ratio: Network Value / Daily Transaction Volume (crypto P/E).
"""
    },
    "smart_contracts": {
        "title": "Smart Contracts and Development",
        "content": """
Smart contracts are self-executing programs stored on a blockchain that run when
predetermined conditions are met.

Core Concepts:
- Deployed to a blockchain address, immutable once deployed.
- Execute deterministically: same input always produces same output.
- Cost gas to deploy and interact with (Ethereum model).
- Can hold and transfer tokens, interact with other contracts.

Development Languages:
- Solidity: Primary language for EVM chains (Ethereum, BSC, Polygon, Avalanche).
- Rust: Used for Solana (via Anchor framework) and Near Protocol.
- Move: Used by Aptos and Sui blockchains.
- Vyper: Python-like alternative for Ethereum.
- Cairo: StarkNet's language for validity proofs.

Common Smart Contract Patterns:
- ERC-20: Fungible token standard. Functions: transfer, approve, transferFrom.
- ERC-721: Non-fungible token (NFT) standard.
- ERC-1155: Multi-token standard (fungible + non-fungible).
- Proxy Pattern: Upgradeable contracts via delegatecall.
- Factory Pattern: Deploy new contracts from a template.
- Oracle Pattern: Bring off-chain data on-chain (Chainlink).

Security Considerations:
- Reentrancy attacks: Recursive calls before state updates.
- Integer overflow/underflow: Mitigated with SafeMath or Solidity 0.8+.
- Front-running: MEV bots exploit pending transactions.
- Flash loan attacks: Manipulate prices within single transaction.
- Access control: Only authorized addresses can call admin functions.
- Audit firms: OpenZeppelin, Trail of Bits, Certora, Halborn.
"""
    },
    "nfts": {
        "title": "Non-Fungible Tokens (NFTs)",
        "content": """
NFTs are unique digital assets with provable ownership on a blockchain.

Technical Standards:
- ERC-721: Each token has unique ID. One token per contract call.
- ERC-1155: Semi-fungible. Batch transfers. Efficient for gaming.
- Metaplex (Solana): Solana NFT standard with on-chain metadata.
- Metadata: Usually stored off-chain (IPFS, Arweave) with on-chain pointer.

NFT Categories:
- Art: Generative art, 1/1 pieces, photography.
- PFPs (Profile Pictures): Collections like CryptoPunks, Bored Apes.
- Gaming: In-game items, characters, land.
- Music: Royalty-sharing, exclusive access.
- Domain Names: ENS (.eth), Unstoppable Domains.
- Real World Assets (RWA): Tokenized real estate, collectibles.

Marketplace Ecosystem:
- OpenSea: Largest NFT marketplace. Multi-chain.
- Blur: Ethereum NFT marketplace with pro trading features.
- Magic Eden: Multi-chain, originally Solana-focused.
- Tensor: Solana NFT trading platform.
- Creator royalties: Historically 2.5-10%, now often optional.

Key Metrics:
- Floor Price: Lowest listed price in a collection.
- Volume: Total trading volume over time.
- Unique Holders: Number of distinct wallet addresses.
- Rarity: Trait-based rarity scoring (rarity.tools, howrare.is).
- Wash Trading: Artificial volume through self-trades.

NFT Finance:
- NFT lending: Use NFTs as collateral (BendDAO, NFTfi).
- Fractionalization: Split expensive NFTs into tradeable tokens.
- NFT AMMs: Sudoswap model for instant NFT liquidity.
"""
    },
    "layer2": {
        "title": "Layer 2 Scaling Solutions",
        "content": """
Layer 2 (L2) solutions process transactions off the main chain (L1) while inheriting
its security guarantees, dramatically increasing throughput and reducing costs.

Types of Layer 2s:

1. Optimistic Rollups:
   - Assume transactions are valid by default.
   - Fraud proofs: 7-day challenge period for disputes.
   - Examples: Arbitrum One (~$3B TVL), Optimism (~$2B TVL), Base (Coinbase).
   - EVM compatible: Easy to port existing Solidity contracts.
   - Cost reduction: ~10-50x cheaper than L1.

2. ZK (Zero-Knowledge) Rollups:
   - Generate cryptographic validity proofs for each batch.
   - No challenge period: Instant finality once proof verified on L1.
   - Examples: zkSync Era, StarkNet, Polygon zkEVM, Scroll, Linea.
   - Types: zk-SNARKs (smaller proofs) vs zk-STARKs (no trusted setup).
   - Higher computational cost for proof generation.

3. Sidechains:
   - Separate blockchains with own consensus.
   - Bridge to L1 but less security inheritance.
   - Example: Polygon PoS (technically a commit chain).

4. State Channels:
   - Off-chain transactions between parties.
   - Only open/close settled on-chain.
   - Example: Bitcoin Lightning Network.

Key L2 Concepts:
- Sequencer: Entity that orders and batches transactions.
- Data Availability: Where transaction data is stored (on-chain vs off-chain).
- Bridging: Moving assets between L1 and L2 (lock-and-mint or burn-and-mint).
- Escape Hatch: Ability to withdraw funds even if L2 operators are malicious.
- L3 / App-chains: Application-specific chains built on top of L2s.
"""
    },
    "mev": {
        "title": "MEV - Maximal Extractable Value",
        "content": """
MEV (Maximal Extractable Value) refers to the profit that can be extracted by reordering,
inserting, or censoring transactions within a block.

Types of MEV:

1. Arbitrage:
   - Price discrepancies between DEXs.
   - Searchers monitor mempool for profitable routes.
   - Atomic arbitrage: Execute in single transaction.
   - Statistical arbitrage: Cross-exchange or cross-chain.

2. Liquidations:
   - Monitor DeFi lending protocols for undercollateralized positions.
   - First to liquidate earns a bonus (liquidation incentive).
   - Competition can lead to priority gas auctions.

3. Sandwich Attacks:
   - Front-run a large trade, then back-run it.
   - Attacker profits from the price movement caused by victim's trade.
   - Victim gets worse execution price (more slippage).

4. Just-In-Time (JIT) Liquidity:
   - Provide concentrated liquidity right before a large swap.
   - Remove liquidity right after, capturing fees with minimal risk.

MEV Infrastructure:
- Flashbots: MEV marketplace. Private transaction pool (Protect).
- MEV-Boost: Proposer-Builder Separation for Ethereum validators.
- Block Builders: Specialized entities that construct optimal blocks.
- Searchers: Bots that find and execute MEV opportunities.
- Relays: Connect builders to proposers (validators).

MEV Mitigation:
- Private mempools: Flashbots Protect, MEV Blocker.
- Batch auctions: CoW Protocol processes trades in batches.
- Encrypted mempools: Hide transaction details until ordering.
- Fair ordering: Time-based ordering protocols (Chainlink FSS).

MEV on different chains: Ethereum ~$600M+ extracted annually.
Solana MEV via Jito validators. L2s have centralized sequencers (less MEV for now).
"""
    },
    "stablecoins": {
        "title": "Stablecoins - Price-Stable Cryptocurrencies",
        "content": """
Stablecoins are cryptocurrencies designed to maintain a stable value, typically pegged
to a fiat currency like the US Dollar.

Types of Stablecoins:

1. Fiat-Collateralized (Centralized):
   - USDT (Tether): Largest stablecoin (~$90B+). Multi-chain. Tether Ltd.
   - USDC (Circle): Regulated, transparent reserves. Circle/Coinbase.
   - BUSD: Binance-branded, Paxos-issued (winding down).
   - Reserves: Cash, T-bills, commercial paper, money market funds.
   - Risk: Centralized issuer can freeze/blacklist addresses.

2. Crypto-Collateralized (Decentralized):
   - DAI (MakerDAO): Over-collateralized by ETH, stETH, USDC, etc.
   - LUSD (Liquity): Only ETH collateral. Immutable contracts. 110% min ratio.
   - sUSD (Synthetix): Backed by SNX staking.
   - Risk: Liquidation cascades, collateral volatility.

3. Algorithmic:
   - Use algorithms to expand/contract supply to maintain peg.
   - Historical failures: UST/LUNA collapse (May 2022, $40B+ lost).
   - Partially algorithmic: FRAX (fractional-algorithmic model).
   - Risk: Death spiral if confidence is lost.

4. Real-World Asset (RWA) Backed:
   - Backed by treasuries, bonds, or other traditional assets.
   - Examples: USDM (Mountain Protocol), various tokenized T-bill products.

Stablecoin Metrics:
- Peg stability: How closely price tracks $1.00.
- Market cap: Total stablecoins in circulation.
- Redemption: Ability to exchange for underlying fiat.
- Transparency: Frequency and quality of reserve attestations.

Use Cases: Trading pairs, DeFi collateral, payments, remittances, savings.
Regulatory landscape: MiCA (EU), potential US stablecoin legislation.
"""
    },
    "yield_farming": {
        "title": "Yield Farming and Liquidity Mining",
        "content": """
Yield farming is the practice of deploying crypto assets across DeFi protocols to
maximize returns through interest, fees, and token rewards.

Core Strategies:

1. Liquidity Providing (LP):
   - Deposit token pairs into AMM pools (e.g., ETH/USDC on Uniswap).
   - Earn trading fees proportional to share of pool.
   - Risk: Impermanent loss when token prices diverge.
   - Concentrated liquidity (Uniswap V3): Higher capital efficiency, higher risk.

2. Lending/Borrowing:
   - Supply assets to lending protocols (Aave, Compound).
   - Earn interest from borrowers.
   - Recursive borrowing: Supply, borrow, re-supply to amplify yield.
   - Risk: Smart contract risk, utilization spikes preventing withdrawal.

3. Staking:
   - Validator staking: Stake ETH for ~3-5% APR.
   - Liquid staking: stETH (Lido), rETH (Rocket Pool). Stake and retain liquidity.
   - Restaking: EigenLayer allows staked ETH to secure additional services.
   - Protocol staking: Lock governance tokens for rewards.

4. Vault Strategies:
   - Auto-compounding: Harvest and reinvest rewards automatically.
   - Delta-neutral: Hedge directional exposure while farming yields.
   - Leveraged farming: Borrow to increase farming position.

Yield Sources:
- Trading fees from AMM pools.
- Interest from lending.
- Token emissions (inflationary rewards).
- Protocol revenue sharing.
- Points/Airdrops: Speculative yield from future token distributions.

Risk Management:
- Smart contract risk: Protocol exploits, bugs.
- IL (Impermanent Loss): Divergence loss in AMM pools.
- Rug pulls: Malicious projects draining funds.
- Regulatory risk: Possible classification as securities.
- APY sustainability: High APY often temporary (emission-driven).

Tools: DefiLlama (TVL tracking), Zapper/Zerion (portfolio), APY.vision (IL tracking).
"""
    },
}

# ---------------------------------------------------------------------------
#  Training Logic
# ---------------------------------------------------------------------------

def train_crypto(topics: list[str], ingestor: KnowledgeIngestor) -> dict:
    """Ingest crypto knowledge topics into the knowledge base."""
    results = []
    total_chunks = 0
    total_chars = 0

    print(f"\n{'='*60}")
    print(f"  Bruce AI - Crypto Knowledge Training")
    print(f"  Topics to process: {len(topics)}")
    print(f"{'='*60}\n")

    for i, topic_key in enumerate(topics, 1):
        if topic_key not in CRYPTO_TOPICS:
            print(f"  [{i}/{len(topics)}] WARNING: Unknown topic '{topic_key}', skipping.")
            continue

        topic = CRYPTO_TOPICS[topic_key]
        print(f"  [{i}/{len(topics)}] Ingesting: {topic['title']}...", end=" ")
        start = time.time()

        result = ingestor.ingest_text(
            text=topic["content"],
            source=f"crypto_training/{topic_key}",
            metadata={
                "domain": "crypto",
                "topic": topic_key,
                "title": topic["title"],
                "training_type": "knowledge_base",
            },
        )

        elapsed = time.time() - start
        chunks = result.get("chunks_added", 0)
        chars = result.get("total_chars", 0)
        total_chunks += chunks
        total_chars += chars
        results.append(result)

        print(f"OK ({chunks} chunks, {chars} chars, {elapsed:.2f}s)")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Topics processed: {len(results)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Total characters: {total_chars}")
    print(f"{'='*60}")

    stats = ingestor.get_knowledge_stats()
    print(f"\n  Knowledge Base Stats:")
    print(f"  - Total chunks in KB: {stats['total_chunks']}")
    print(f"  - Total sources: {stats['total_sources']}")
    print(f"  - Disk size: {stats['disk_size_bytes'] / 1024:.1f} KB")
    print()

    return {
        "topics_processed": len(results),
        "total_chunks": total_chunks,
        "total_characters": total_chars,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Train Bruce AI on crypto domain knowledge")
    parser.add_argument(
        "--topics",
        type=str,
        default="all",
        help="Comma-separated topic list or 'all'. Available: " + ", ".join(CRYPTO_TOPICS.keys()),
    )
    args = parser.parse_args()

    if args.topics.lower() == "all":
        topics = list(CRYPTO_TOPICS.keys())
    else:
        topics = [t.strip() for t in args.topics.split(",")]

    ingestor = KnowledgeIngestor()
    train_crypto(topics, ingestor)


if __name__ == "__main__":
    main()
