# Philippine Fisheries Production & Value Dashboard (2002–2025)

An end-to-end data processing pipeline and interactive Streamlit web application analyzing Philippine fisheries production volume and valuation data across four major subsectors: **Aquaculture**, **Commercial Fisheries**, **Inland Municipal Fisheries**, and **Marine Municipal Fisheries**.

---

## 📌 Project Overview

This repository processes and synthesizes official Philippine Statistics Authority (PSA) fisheries production datasets spanning 2002 through 2025. It addresses key data quality challenges in raw government datasets—including hierarchy header duplications, species alias fragmentation, and provincial data suppression—to deliver a clean, audit-compliant master dataset.

### Core Subsectors Covered
- **Aquaculture** (by Aquafarm Type & Culture System)
- **Commercial Fisheries**
- **Inland Municipal Fisheries**
- **Marine Municipal Fisheries**

---

## 🛠️ Key Pipeline Features & Data Methodology

### 1. Species Standardization & Deduplication
- Standardizes local species aliases and common names (e.g., mapping `Catfish` to `Catfish (Hito)`, `Suahe` to `Endeavor Prawn (Suahe)`, `Lapu-Lapu` to `Grouper (Lapu-Lapu)`).
- Strips culture system prefixes (e.g., `FC -`, `BF -`) from species entries to ensure clean naming conventions.

### 2. Elimination of Header Double-Counting
- Implements strict filtering logic to exclude aggregate sub-total headers (e.g., `..FISH`, `..CRUSTACEANS`, `..MOLLUSCS`, `TOTAL`) and macro environment categories from row-level summation.

### 3. National Benchmark Reconciliation
- **Data Gap Challenge:** Raw PSA datasets contain suppressed or uncollected data points (`..`) at the granular provincial/species level for recent years, causing raw bottom-up provincial sums to fall slightly below published national totals.
- **Reconciliation Strategy:** The pipeline automatically calculates annual variances between published national totals and granular provincial sums for both **Volume (MT)** and **Value ('000 PHP)**. It creates an explicit `Unallocated / National Balancing` record per subsector/year.
- **Benefit:** Guarantees **100% fidelity to published national benchmark figures** for macro reporting while preserving full granularity for provincial and regional analysis.

---

## 📁 Repository Structure

```text
├── app.py                                    # Streamlit interactive web application
├── master_fisheries_fact_annual_2002_2025.csv # Reconciled master dataset (Output)
├── pipeline.py                               # Full Python data processing pipeline
├── audit_raw_vs_clean.py                     # Standalone audit and reconciliation script
├── requirements.txt                          # Streamlit Cloud deployment dependencies
└── README.md                                 # Project documentation


Data Source: Philippine Statistics Authority (PSA) - OpenSTAT Fisheries Statistics (1996–2025).
