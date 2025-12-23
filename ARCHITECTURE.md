# Architecture: CHIMERA Nexus

> **System Pattern:** Modular Monolith | Layered Architecture
> **Data Strategy:** Local-First | Atomic Persistence

This document outlines the internal engineering of the CHIMERA Nexus protocol. It is intended for core maintainers and contributors.

---

## 1. High-Level Design

CHIMERA Nexus follows a strict **Layered Architecture**. Dependencies flow **inwards**: The CLI depends on the Core, but the Core depends on nothing (Zero-Dependency Domain).

```mermaid
graph TD
    User((Analyst)) --> CLI[Layer 5: CLI Controller]
    
    subgraph Application Logic
        CLI --> Repo[Layer 2: Storage Repository]
        CLI --> Auditor[Layer 3: Cognitive Auditor]
        CLI --> Report[Layer 4: Report Engine]
    end
    
    subgraph Core Domain
        Repo --> Domain[Layer 1: Domain Models]
        Auditor --> Domain
        Report --> Domain
    end
    
    Repo --> FileSystem[(Local YAML Storage)]