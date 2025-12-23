import pytest
import uuid
from pathlib import Path
from chimera_nexus.core.domain import HybridThreatChain, HybridNode, ThreatDomain, RelationType
from chimera_nexus.storage.repository import NexusRepository

# --- Fixtures (Setup) ---

@pytest.fixture
def temp_repo(tmp_path):
    """Creates a temporary repository for testing to avoid messing up real data."""
    return NexusRepository(data_dir=str(tmp_path))

@pytest.fixture
def sample_chain():
    chain = HybridThreatChain(name="Test Operation")
    node = HybridNode(
        domain=ThreatDomain.CYBER,
        signal_type="server_breach",
        confidence=0.9,
        description="Logs show unauthorized access"
    )
    chain.add_node(node)
    return chain

# --- Core Logic Tests ---

def test_iap_calculation_high_pressure():
    """Verify the Math: High urgency + Low confidence = High Pressure."""
    chain = HybridThreatChain(name="Pressure Test")
    
    # Low confidence node (0.2)
    node = HybridNode(
        domain=ThreatDomain.INFORMATION,
        signal_type="rumor",
        confidence=0.2,
        description="Unverified tweet"
    )
    chain.add_node(node)
    
    # Formula: Urgency (8.0) / Confidence (0.2) = 40.0
    iap = chain.calculate_iap(urgency=8.0)
    assert iap == 40.0

def test_chain_immutability_logic(sample_chain):
    """Ensure nodes are correctly keyed by UUID."""
    assert len(sample_chain.nodes) == 1
    node_id = list(sample_chain.nodes.keys())[0]
    assert isinstance(node_id, uuid.UUID)

# --- Storage Tests ---

def test_atomic_persistence(temp_repo, sample_chain):
    """Verify that we can save and load without data loss."""
    # Save
    saved_path = temp_repo.save_chain(sample_chain)
    assert saved_path.exists()
    
    # Load
    loaded_chain = temp_repo.load_chain(sample_chain.id)
    assert loaded_chain.name == "Test Operation"
    assert len(loaded_chain.nodes) == 1
    
    # Verify strict typing survived serialization
    loaded_node = list(loaded_chain.nodes.values())[0]
    assert isinstance(loaded_node.domain, ThreatDomain)
    assert loaded_node.domain == ThreatDomain.CYBER

def test_list_functionality(temp_repo, sample_chain):
    """Verify we can list operations."""
    temp_repo.save_chain(sample_chain)
    chains = temp_repo.list_chains()
    assert len(chains) == 1
    assert chains[0].id == sample_chain.id