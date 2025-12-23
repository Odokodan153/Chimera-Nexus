from enum import Enum
from typing import List, Dict
from pydantic import BaseModel, Field
from chimera_nexus.core.domain import HybridThreatChain, ThreatDomain, ConfidenceLevel

class BiasType(str, Enum):
    MONO_DOMAIN_FIXATION = "mono_domain_fixation"  # Analyzing only Cyber, ignoring Info/Econ
    PREMATURE_CLOSURE = "premature_closure"        # High confidence with too few data points
    ECHO_CHAMBER = "echo_chamber"                  # High confidence derived entirely from low-cost signals
    DISCONNECTED_NARRATIVE = "disconnected_narrative" # Nodes exist but lack causal edges

class AuditFinding(BaseModel):
    """
    Represents a specific cognitive or structural weakness in the assessment.
    """
    bias_type: BiasType
    severity: float = Field(..., ge=0.0, le=1.0, description="1.0 = Critical Analytical Failure")
    description: str
    remediation_hint: str

class CognitiveAuditor:
    """
    The 'Red Team' algorithm. 
    It critiques the analyst's work to prevent bad decisions.
    """
    
    def audit(self, chain: HybridThreatChain) -> List[AuditFinding]:
        findings = []
        
        # 1. Check for Mono-Domain Fixation (Tunnel Vision)
        # If > 75% of nodes are in a single domain, the analyst might be missing the "Hybrid" aspect.
        if chain.nodes:
            domains = [n.domain for n in chain.nodes.values()]
            most_common = max(set(domains), key=domains.count)
            count = domains.count(most_common)
            ratio = count / len(domains)
            
            if ratio > 0.75 and len(chain.nodes) > 3:
                findings.append(AuditFinding(
                    bias_type=BiasType.MONO_DOMAIN_FIXATION,
                    severity=0.8 * ratio,
                    description=f"Analysis is heavily skewed ({ratio:.0%}) towards {most_common.value.upper()}.",
                    remediation_hint="Force-collect signals from at least one adjacent domain (e.g., Economic or Social)."
                ))

        # 2. Check for Premature Closure
        # High confidence claimed with very few nodes implies overconfidence.
        avg_conf = 0.0
        if chain.nodes:
            avg_conf = sum(n.confidence for n in chain.nodes.values()) / len(chain.nodes)
            
        if avg_conf > 0.8 and len(chain.nodes) < 4:
            findings.append(AuditFinding(
                bias_type=BiasType.PREMATURE_CLOSURE,
                severity=0.7,
                description="High aggregate confidence claimed with sparse data points.",
                remediation_hint="Reduce confidence or corroborate with independent sources."
            ))

        # 3. Disconnected Narrative
        # Nodes exist but aren't linked. This is a list, not a chain.
        if len(chain.nodes) > 2:
            # Simple check: do we have enough edges to connect most nodes?
            # A fully connected linear chain of N nodes needs N-1 edges.
            needed_edges = len(chain.nodes) - 1
            if len(chain.edges) < needed_edges * 0.5:
                findings.append(AuditFinding(
                    bias_type=BiasType.DISCONNECTED_NARRATIVE,
                    severity=0.6,
                    description="Signals are isolated. Causal logic is missing.",
                    remediation_hint="Use the 'link' command to define how Signal A causes/relates to Signal B."
                ))

        return findings