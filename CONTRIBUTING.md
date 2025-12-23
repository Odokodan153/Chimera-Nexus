# Contributing to CHIMERA Nexus

Thank you for your interest in contributing to **CHIMERA Nexus**. 

This project operates under a strict **"Production-Only" Doctrine**. We build decision-support tools for high-pressure environments. As such, we have zero tolerance for unstable code, mock data, or ambiguity.

Please read these guidelines carefully before submitting a Pull Request (PR).

## 1. Core Engineering Principles

If your PR violates these principles, it will be rejected:

1.  **No Mock / No Placeholders:** * Never commit code containing `TODO`, `pass`, `mock_data`, or hardcoded "dummy" returns.
    * Every function must be fully implemented and functional.
2.  **Offline-First & Local-First:**
    * The tool must function 100% without an internet connection.
    * Do not add dependencies on external cloud APIs (AWS, Azure, OpenAI) unless they are strictly optional plugins.
    * All persistence must use the `NexusRepository` (atomic filesystem storage).
3.  **Strict Typing:**
    * Python 3.10+ type hints are mandatory.
    * We use `mypy` strict mode. No `Any` allowed in core logic.
4.  **Explainable Intelligence:**
    * Every analytical output (scores, alerts) must be traceable. "Black box" algorithms are not permitted.

## 2. Development Environment

We use standard Python tooling.

```bash
# 1. Clone the repository
git clone [https://github.com/your-org/chimera-nexus.git](https://github.com/your-org/chimera-nexus.git)
cd chimera-nexus

# 2. Install dependencies (we recommend Poetry or Pipenv)
pip install -e .[dev]
pip install black mypy ruff pytest

# 3. Verify the environment
nexus --help