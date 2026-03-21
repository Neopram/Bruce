#!/usr/bin/env python3
"""
Train Bruce AI - Shipping Domain Knowledge
Ingests structured shipping knowledge into the knowledge base.
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_ingestor import KnowledgeIngestor

# ---------------------------------------------------------------------------
#  Shipping Knowledge Topics
# ---------------------------------------------------------------------------

SHIPPING_TOPICS = {
    "incoterms": {
        "title": "Incoterms (International Commercial Terms)",
        "content": """
Incoterms are standardized trade terms published by the International Chamber of Commerce (ICC)
that define the responsibilities of buyers and sellers in international trade.

Key Incoterms 2020:
- EXW (Ex Works): Seller makes goods available at their premises. Buyer bears all costs and risks.
- FCA (Free Carrier): Seller delivers goods to a carrier nominated by the buyer.
- FAS (Free Alongside Ship): Seller delivers goods alongside the vessel at the port of shipment.
- FOB (Free On Board): Seller delivers goods on board the vessel. Risk transfers at ship's rail.
- CFR (Cost and Freight): Seller pays freight to destination port. Risk transfers at origin port.
- CIF (Cost, Insurance and Freight): Like CFR but seller also provides insurance.
- CPT (Carriage Paid To): Seller pays freight to named destination. Risk transfers at first carrier.
- CIP (Carriage and Insurance Paid To): Like CPT but seller also provides insurance.
- DAP (Delivered at Place): Seller delivers goods at named destination, not unloaded.
- DPU (Delivered at Place Unloaded): Seller delivers and unloads at named destination.
- DDP (Delivered Duty Paid): Seller bears all costs including import duties.

Important distinctions:
- FOB, CFR, CIF, FAS are for sea/inland waterway transport only.
- EXW, FCA, CPT, CIP, DAP, DPU, DDP apply to any mode of transport.
- CIF requires minimum insurance coverage (Institute Cargo Clause C).
- CIP requires broader insurance coverage (Institute Cargo Clause A).
"""
    },
    "vessel_types": {
        "title": "Types of Shipping Vessels",
        "content": """
Major categories of commercial shipping vessels:

1. Container Ships:
   - Feeder ships: 300-1000 TEU, serve smaller ports
   - Panamax: 3,000-5,000 TEU, fit original Panama Canal locks
   - Post-Panamax: 5,000-10,000 TEU
   - New Panamax: 10,000-14,500 TEU, fit new Panama Canal locks
   - Ultra Large Container Vessels (ULCV): 14,500-24,000+ TEU
   TEU = Twenty-foot Equivalent Unit (standard 20ft container)

2. Bulk Carriers:
   - Handysize: 15,000-35,000 DWT, versatile with onboard cranes
   - Handymax/Supramax: 35,000-60,000 DWT
   - Panamax: 60,000-80,000 DWT
   - Capesize: 100,000-200,000+ DWT, too large for Panama/Suez
   - Very Large Ore Carriers (VLOC): 200,000-400,000 DWT
   DWT = Deadweight Tonnage (cargo capacity)

3. Tankers:
   - Product Tankers: refined petroleum products
   - Aframax: 80,000-120,000 DWT
   - Suezmax: 120,000-200,000 DWT, max for Suez Canal laden
   - VLCC (Very Large Crude Carrier): 200,000-320,000 DWT
   - ULCC (Ultra Large Crude Carrier): 320,000+ DWT

4. LNG/LPG Carriers: Specialized for liquefied natural gas / petroleum gas
5. Ro-Ro (Roll-on/Roll-off): Vehicles and wheeled cargo
6. Reefer Ships: Refrigerated cargo (perishables)
7. General Cargo Ships: Break-bulk, project cargo
"""
    },
    "shipping_routes": {
        "title": "Major Global Shipping Routes",
        "content": """
Key global trade routes and chokepoints:

1. Trans-Pacific Route:
   - Asia (China, Japan, Korea) to North America West Coast
   - Highest volume container trade lane globally
   - Transit time: 12-18 days Shanghai to Los Angeles

2. Asia-Europe Route:
   - Via Suez Canal: Shanghai to Rotterdam ~30 days
   - Alternative via Cape of Good Hope: ~40 days (used when Suez disrupted)
   - Carries manufactured goods westbound, raw materials eastbound

3. Trans-Atlantic Route:
   - Europe to North America East Coast
   - Rotterdam to New York: ~9-12 days

4. Critical Chokepoints:
   - Suez Canal: ~12% of global trade, links Mediterranean to Red Sea
   - Panama Canal: ~5% of global trade, links Atlantic to Pacific
   - Strait of Malacca: ~25% of global trade, links Indian Ocean to Pacific
   - Strait of Hormuz: ~20% of global oil supply
   - Bab el-Mandeb: Links Red Sea to Gulf of Aden

5. Emerging Routes:
   - Northern Sea Route (Arctic): Russia's northern coast, seasonal
   - Polar Silk Road: China's Arctic shipping ambitions
   - New Suez Canal: Expanded capacity since 2015

Route economics depend on: fuel costs, canal tolls, piracy risk, weather, port congestion.
"""
    },
    "port_operations": {
        "title": "Port Operations and Terminal Management",
        "content": """
Port operations encompass vessel berthing, cargo handling, and logistics coordination.

Key concepts:
1. Berth Allocation: Assigning vessels to quay positions based on size, cargo, schedule.
2. Crane Operations: Ship-to-shore (STS) gantry cranes for container loading/unloading.
   - Modern STS cranes handle 30-40 moves per hour.
   - Twin-lift and tandem-lift cranes increase throughput.

3. Yard Operations:
   - Rubber-Tired Gantry (RTG) cranes for container stacking
   - Automated Guided Vehicles (AGV) for horizontal transport
   - Terminal Operating Systems (TOS) for container tracking

4. Performance Metrics:
   - Berth productivity: Moves per hour per vessel
   - Yard utilization: TEU per hectare
   - Truck turnaround time: Average time in terminal
   - Vessel turnaround time: Arrival to departure
   - Dwell time: How long containers stay in terminal

5. Major Global Ports by TEU (approximate annual throughput):
   - Shanghai: ~47 million TEU
   - Singapore: ~37 million TEU
   - Ningbo-Zhoushan: ~33 million TEU
   - Shenzhen: ~30 million TEU
   - Guangzhou: ~24 million TEU
   - Busan: ~22 million TEU
   - Rotterdam: ~15 million TEU

6. Port charges include: pilotage, towage, wharfage, stevedoring, terminal handling.
"""
    },
    "freight_markets": {
        "title": "Freight Markets and Indices",
        "content": """
Freight markets determine the cost of shipping goods globally.

1. Baltic Exchange Indices:
   - Baltic Dry Index (BDI): Composite of Capesize, Panamax, Supramax rates
   - Baltic Capesize Index (BCI): Iron ore and coal routes
   - Baltic Panamax Index (BPI): Grain and coal routes
   - Baltic Clean Tanker Index (BCTI): Clean petroleum products
   - Baltic Dirty Tanker Index (BDTI): Crude oil tanker rates

2. Container Freight Indices:
   - Shanghai Containerized Freight Index (SCFI): Spot rates from Shanghai
   - Drewry World Container Index (WCI): Composite of major routes
   - Freightos Baltic Index (FBX): Global container freight benchmark

3. Freight Market Structure:
   - Spot market: Immediate/near-term fixtures
   - Time charter: Vessel hired for a period (months to years)
   - Contract of Affreightment (COA): Multiple voyages over a period
   - Forward Freight Agreements (FFA): Financial derivatives for hedging

4. Market Drivers:
   - Supply: Fleet size, newbuilding orderbook, scrapping rates
   - Demand: Global trade volumes, commodity flows, seasonal patterns
   - Disruptions: Canal closures, port congestion, geopolitical events
   - Costs: Bunker fuel prices, crew costs, maintenance

5. Freight rate units: USD per TEU (containers), USD per metric ton (dry bulk),
   Worldscale points (tankers), USD per day (time charter).
"""
    },
    "maritime_regulations": {
        "title": "Maritime Regulations and Compliance",
        "content": """
Key maritime regulatory frameworks:

1. IMO (International Maritime Organization) Regulations:
   - SOLAS (Safety of Life at Sea): Safety standards for construction, equipment, operation
   - MARPOL (Marine Pollution): Prevention of pollution from ships
     - Annex I: Oil pollution prevention
     - Annex II: Noxious liquid substances
     - Annex VI: Air pollution and GHG emissions
   - STCW: Standards of Training, Certification and Watchkeeping
   - MLC (Maritime Labour Convention): Seafarer working conditions

2. Environmental Regulations:
   - IMO 2020: Global sulfur cap of 0.5% (from 3.5%)
   - EEXI (Energy Efficiency Existing Ship Index): Efficiency standards
   - CII (Carbon Intensity Indicator): Annual operational carbon rating (A-E)
   - EU ETS: Emissions Trading System including maritime from 2024
   - FuelEU Maritime: Greenhouse gas intensity of energy used onboard

3. Emission Control Areas (ECAs):
   - Baltic Sea, North Sea, North American, US Caribbean
   - Stricter sulfur limit: 0.1%
   - Compliance options: low-sulfur fuel, scrubbers, LNG

4. Port State Control (PSC):
   - Inspections to verify vessel compliance
   - Major PSC regimes: Paris MoU, Tokyo MoU, US Coast Guard
   - Detentions for serious deficiencies

5. Sanctions and Trade Compliance:
   - OFAC (US), EU sanctions lists
   - Ship-to-ship (STS) transfer monitoring
   - AIS (Automatic Identification System) requirements
"""
    },
    "container_logistics": {
        "title": "Container Logistics and Intermodal Transport",
        "content": """
Container logistics covers the movement of standardized containers across the supply chain.

1. Container Types:
   - 20ft (TEU): 5.9m x 2.35m x 2.39m, max payload ~28 tons
   - 40ft (FEU): 12.03m x 2.35m x 2.39m, max payload ~26 tons
   - 40ft High Cube (HC): Extra 30cm height, most common for lighter goods
   - Reefer: Temperature-controlled (-25C to +25C)
   - Open Top: For oversized cargo
   - Flat Rack: For heavy/odd-shaped cargo
   - Tank Container: For liquids and gases

2. Intermodal Chain:
   - Shipper warehouse -> Trucking -> Origin port -> Ocean transit
   - Destination port -> Rail/Truck -> Consignee warehouse
   - Door-to-door transit times range from 20-60+ days

3. Container Tracking:
   - BIC (Bureau International des Containers) codes
   - ISO 6346 container identification system
   - Smart containers with GPS, temperature, humidity sensors
   - EDI (Electronic Data Interchange) for documentation

4. Key Documents:
   - Booking confirmation
   - Shipping instructions
   - Bill of Lading (B/L)
   - Packing list
   - Commercial invoice
   - Certificate of origin

5. Demurrage and Detention:
   - Demurrage: Charges for container at port beyond free time
   - Detention: Charges for container outside port beyond free time
   - Free time: Typically 3-7 days at origin, 5-14 days at destination
"""
    },
    "bunker_fuel": {
        "title": "Bunker Fuel and Marine Energy",
        "content": """
Bunker fuel is the fuel used to power commercial ships.

1. Fuel Types:
   - HFO (Heavy Fuel Oil): Traditional, high sulfur (3.5%), cheapest
   - VLSFO (Very Low Sulfur Fuel Oil): 0.5% sulfur, IMO 2020 compliant
   - LSMGO (Low Sulfur Marine Gas Oil): 0.1% sulfur, for ECAs
   - LNG (Liquefied Natural Gas): Cleaner alternative, growing adoption
   - Methanol: Emerging as green fuel option
   - Ammonia: Future zero-carbon fuel under development
   - Hydrogen: Long-term zero-carbon option

2. Bunkering Operations:
   - Major bunkering hubs: Singapore, Fujairah, Rotterdam, Houston
   - Methods: alongside berth, at anchorage, ship-to-ship
   - Typical consumption: VLCC ~80 tons/day, container ship ~150-250 tons/day

3. Fuel Costs (approximate ranges):
   - HFO: $400-600/ton
   - VLSFO: $500-800/ton
   - LSMGO: $600-1000/ton
   - LNG: Varies widely with natural gas prices

4. Scrubber Systems:
   - Open-loop: Uses seawater to wash exhaust, discharges overboard
   - Closed-loop: Recirculates wash water, stores residue
   - Hybrid: Can switch between open and closed loop
   - Allow continued use of cheaper HFO while meeting emission rules

5. Energy Transition:
   - Wind-assisted propulsion (rotor sails, wing sails)
   - Shore power (cold ironing) at ports
   - Battery-hybrid systems for short-sea shipping
   - Carbon capture onboard ships (experimental)
"""
    },
    "chartering": {
        "title": "Ship Chartering and Fixture Process",
        "content": """
Chartering is the process of hiring a vessel for cargo transport.

1. Charter Types:
   - Voyage Charter: Ship hired for a specific voyage
     - Owner pays operating costs and fuel
     - Charterer pays freight rate per ton or lump sum
   - Time Charter: Ship hired for a period
     - Charterer pays daily hire rate + fuel
     - Owner pays crew, maintenance, insurance
   - Bareboat (Demise) Charter: Charterer takes full control
     - Charterer pays all costs including crew
     - Essentially operating as owner

2. Fixture Process:
   - Cargo inquiry -> Ship nomination -> Negotiation -> Recap (main terms agreed)
   - Charter party (C/P) drafted -> Reviewed -> Signed
   - Key terms: laycan (loading date range), freight rate, demurrage rate

3. Common Charter Parties:
   - GENCON: General voyage charter party
   - NYPE (New York Produce Exchange): Time charter
   - Baltime: Time charter
   - SHELLVOY: Shell tanker voyage charter
   - BPVOY: BP tanker voyage charter

4. Key Charter Terms:
   - Laydays/Cancelling (Laycan): Window for vessel arrival
   - NOR (Notice of Readiness): Vessel ready to load/discharge
   - Laytime: Allowed time for loading/discharging
   - Demurrage: Penalty for exceeding laytime
   - Despatch: Reward for completing faster than laytime
   - Off-hire: Periods when time charter hire is not paid

5. Chartering Participants:
   - Shipowners, charterers, ship brokers
   - Major brokerages: Clarksons, SSY, Braemar, BRS
"""
    },
    "bill_of_lading": {
        "title": "Bill of Lading and Shipping Documentation",
        "content": """
The Bill of Lading (B/L) is the most important document in international shipping.

1. Functions of the Bill of Lading:
   - Receipt for goods shipped
   - Evidence of the contract of carriage
   - Document of title (transferable to third parties)

2. Types of Bills of Lading:
   - Clean B/L: No clauses noting damage or defects
   - Claused (Dirty) B/L: Notes damage or discrepancies
   - On Board B/L: Confirms goods loaded on vessel
   - Received for Shipment B/L: Goods received but not yet loaded
   - Through B/L: Covers entire multimodal journey
   - Combined Transport B/L: For door-to-door movements
   - Sea Waybill: Non-negotiable, faster processing
   - Switch B/L: Replaced at intermediate port

3. Key B/L Information:
   - Shipper, consignee, notify party
   - Vessel name, voyage number
   - Port of loading, port of discharge
   - Description of goods, weight, measurements
   - Number of containers/packages
   - Freight terms (prepaid or collect)
   - Date of shipment

4. Other Important Documents:
   - Letter of Credit (L/C): Bank guarantee of payment
   - Certificate of Origin: Country where goods manufactured
   - Phytosanitary Certificate: For agricultural products
   - Dangerous Goods Declaration: For hazardous cargo
   - Insurance Certificate: Proof of cargo insurance

5. Digital Transformation:
   - Electronic Bills of Lading (eB/L) gaining adoption
   - Platforms: WAVE, Bolero, essDOCS, CargoX
   - Blockchain-based documentation for security and speed
   - DCSA standards for digital shipping documents
"""
    },
}

# ---------------------------------------------------------------------------
#  Training Logic
# ---------------------------------------------------------------------------

def train_shipping(topics: list[str], ingestor: KnowledgeIngestor) -> dict:
    """Ingest shipping knowledge topics into the knowledge base."""
    results = []
    total_chunks = 0
    total_chars = 0

    print(f"\n{'='*60}")
    print(f"  Bruce AI - Shipping Knowledge Training")
    print(f"  Topics to process: {len(topics)}")
    print(f"{'='*60}\n")

    for i, topic_key in enumerate(topics, 1):
        if topic_key not in SHIPPING_TOPICS:
            print(f"  [{i}/{len(topics)}] WARNING: Unknown topic '{topic_key}', skipping.")
            continue

        topic = SHIPPING_TOPICS[topic_key]
        print(f"  [{i}/{len(topics)}] Ingesting: {topic['title']}...", end=" ")
        start = time.time()

        result = ingestor.ingest_text(
            text=topic["content"],
            source=f"shipping_training/{topic_key}",
            metadata={
                "domain": "shipping",
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
    parser = argparse.ArgumentParser(description="Train Bruce AI on shipping domain knowledge")
    parser.add_argument(
        "--topics",
        type=str,
        default="all",
        help="Comma-separated topic list or 'all'. Available: " + ", ".join(SHIPPING_TOPICS.keys()),
    )
    args = parser.parse_args()

    if args.topics.lower() == "all":
        topics = list(SHIPPING_TOPICS.keys())
    else:
        topics = [t.strip() for t in args.topics.split(",")]

    ingestor = KnowledgeIngestor()
    train_shipping(topics, ingestor)


if __name__ == "__main__":
    main()
