import yaml
import os
from uuid import UUID
from pathlib import Path
from typing import List, Type, TypeVar
from pydantic import BaseModel, ValidationError
from chimera_nexus.core.domain import HybridThreatChain

T = TypeVar("T", bound=BaseModel)

class StorageError(Exception):
    pass

class NexusRepository:
    """
    Manages filesystem persistence for CHIMERA entities.
    Enforces atomic writes to prevent data corruption.
    """
    def __init__(self, data_dir: str = "./nexus_data"):
        self.base_path = Path(data_dir)
        self.chains_path = self.base_path / "chains"
        self._initialize_storage()

    def _initialize_storage(self):
        try:
            self.chains_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Critical: Cannot create storage directory. {e}")

    def _get_file_path(self, obj_id: UUID) -> Path:
        return self.chains_path / f"{obj_id}.yaml"

    def save_chain(self, chain: HybridThreatChain) -> Path:
        """
        Atomically saves a HybridThreatChain to disk.
        """
        target_path = self._get_file_path(chain.id)
        temp_path = target_path.with_suffix('.tmp')

        try:
            # Dump to dictionary using Pydantic JSON logic (handles UUID/Datetime)
            data = chain.model_dump(mode='json')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
            
            # Atomic rename
            temp_path.replace(target_path)
            return target_path
            
        except (IOError, OSError) as e:
            if temp_path.exists():
                os.remove(temp_path)
            raise StorageError(f"Failed to persist chain {chain.id}: {e}")

    def load_chain(self, chain_id: UUID) -> HybridThreatChain:
        target_path = self._get_file_path(chain_id)
        
        if not target_path.exists():
            raise StorageError(f"Chain {chain_id} not found.")

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return HybridThreatChain.model_validate(data)
        except (ValidationError, yaml.YAMLError) as e:
            raise StorageError(f"Corrupt data in {target_path}: {e}")

    def list_chains(self) -> List[HybridThreatChain]:
        chains = []
        for f in self.chains_path.glob("*.yaml"):
            try:
                # Optimized: We load fully here, but in high-scale we would parse header only
                with open(f, 'r', encoding='utf-8') as file_handle:
                    data = yaml.safe_load(file_handle)
                    chains.append(HybridThreatChain.model_validate(data))
            except Exception:
                continue # Skip malformed files in listing
        return chains