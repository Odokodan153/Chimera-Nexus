import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

# --- Enumerations (Strict Vocabulary) ---

class ThreatDomain(str, Enum):
    CYBER = "cyber"
    INFORMATION = "information"
    ECONOMIC = "economic"
    POLITICAL = "political"
    SOCIAL = "social"
    PHYSICAL = "physical"
    PSYCHOLOGICAL = "psychological"

class RelationType(str, Enum):
    AMPLIFICATION = "amplification"
    ENABLEMENT = "enablement"
    MASKING = "masking"
    TRIGGERING = "triggering"
    CORRELATION = "correlation"

# --- Domain Entities ---

class HybridNode(BaseModel):
    """
    Represents a discrete signal or event within a hybrid environment.
    Immutable by design to preserve audit trails.
    """
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    domain: ThreatDomain
    signal_type: str = Field(..., min_length=3, description="Classification of the event")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analyst confidence (0.0-1.0)")
    cost_estimate: float = Field(0.0, ge=0.0, description="Normalized resource cost for the actor")
    description: str = Field(..., description="Short analytical summary")

    @field_validator('confidence')
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(v, 2)

class HybridEdge(BaseModel):
    """
    Defines the causal or correlative link between two nodes.
    """
    source_id: uuid.UUID
    target_id: uuid.UUID
    relation_type: RelationType
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Strength of the connection")
    justification: str = Field(..., description="Why does this link exist?")

class HybridThreatChain(BaseModel):
    """
    The primary operational unit of CHIMERA Nexus.
    Aggregates nodes and edges to model a specific threat vector over time.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(..., min_length=3)
    nodes: Dict[uuid.UUID, HybridNode] = Field(default_factory=dict)
    edges: List[HybridEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_node(self, node: HybridNode) -> None:
        self.nodes[node.id] = node
        self.updated_at = datetime.utcnow()

    def add_edge(self, edge: HybridEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Edge references non-existent nodes in this chain.")
        self.edges.append(edge)
        self.updated_at = datetime.utcnow()

    @property
    def domain_mix(self) -> List[ThreatDomain]:
        return list({n.domain for n in self.nodes.values()})

    @property
    def coherence_score(self) -> float:
        """
        Calculates Chain Coherence Score (CCS).
        Higher score = Logic is sound and data is interconnected.
        """
        if not self.edges:
            return 0.0
        
        avg_weight = sum(e.weight for e in self.edges) / len(self.edges)
        # Density calculation: Edges / Possible Edges (Nodes - 1 for a simple line)
        node_count = len(self.nodes)
        if node_count < 2:
            return 0.0
            
        density = len(self.edges) / (node_count - 1)
        return round(avg_weight * min(1.0, density), 2)

    def calculate_iap(self, urgency: float) -> float:
        """
        Calculates Information Asymmetry Pressure (IAP).
        IAP = Urgency / Average_Confidence
        """
        if not self.nodes:
            return 0.0
        
        avg_conf = sum(n.confidence for n in self.nodes.values()) / len(self.nodes)
        # Avoid division by zero and extreme outliers
        safe_conf = max(0.1, avg_conf)
        
        return round(urgency / safe_conf, 2)