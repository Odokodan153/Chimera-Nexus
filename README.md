# CHIMERA Nexus
**Contextual Hybrid Intelligence for Monitoring, Evaluation & Risk Assessment**

> **Operational Doctrine:** Minimal Viable Collection | Offline-First | Cognitive Bias Suppression

![Chimera Nexus Logo](chimera_nexus/assets/Chimera-Nexus_Logo.png)

## Overview

**CHIMERA Nexus** is a decision-support engine designed for analysts operating in resource-constrained, high-pressure environments. Unlike traditional Threat Intelligence Platforms (TIPs) that focus on *collecting* massive amounts of data, Nexus focuses on **structuring** minimal signals into coherent decision models.

It implements the **Hybrid Threat Chain (HTC)** formalism to track asymmetric threats across Cyber, Information, Economic, and Social domains simultaneously.

## Core Capabilities

1.  **Hybrid Threat Modeling:** Formalizes threats as vectors (`Actor`, `Capability`, `Intent`) rather than isolated incidents.
2.  **IAP Metric (Information Asymmetry Pressure):** Mathematically calculates the risk of delaying a decision based on urgency vs. confidence.
3.  **Cognitive Auditing:** An automated "Red Team" module that scans your analysis for tunnel vision, confirmation bias, and logical gaps.
4.  **Offline Resilience:** Zero external dependencies. All intelligence is stored in atomic, human-readable YAML files.

## Installation

### Prerequisites
* Python 3.10+
* Pip / Poetry

### Setup
```bash
# 1. Clone the protocol repository
git clone [https://github.com/your-org/chimera-nexus.git](https://github.com/your-org/chimera-nexus.git)
cd chimera-nexus

# 2. Install dependencies (Production Mode)
pip install .

# 3. Verify installation
python -m chimera_nexus.cli.main --help