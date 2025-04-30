import yaml
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum, auto
import os

class EntityType(Enum):
    ACCOUNTANT = "accountant"
    BANK = "bank"
    INVESTMENT = "investment"
    INSURANCE = "insurance"
    LEGAL = "legal"
    GOVERNMENT = "government"
    EMPLOYER = "employer"
    UTILITY = "utility"
    OTHER = "other"

    @classmethod
    def from_str(cls, value: str) -> 'EntityType':
        """Convert string to EntityType, case-insensitive."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid entity type: {value}")

@dataclass
class Entity:
    name: str
    type: Union[EntityType, str]
    contact: Dict[str, str] = None
    address: Dict[str, str] = None
    notes: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        """Initialize default values and validate required fields."""
        if not self.name:
            raise ValueError("Entity name is required")
        
        if isinstance(self.type, str):
            self.type = EntityType.from_str(self.type)
        elif not isinstance(self.type, EntityType):
            raise ValueError("Type must be a string or EntityType")

        # Initialize dictionaries if None
        self.contact = self.contact or {}
        self.address = self.address or {}

        # Move email/phone to contact if provided directly
        if self.email and 'email' not in self.contact:
            self.contact['email'] = self.email
        if self.phone and 'phone' not in self.contact:
            self.contact['phone'] = self.phone

        # Sync back to direct attributes
        self.email = self.contact.get('email', self.email)
        self.phone = self.contact.get('phone', self.phone)

    def validate(self) -> bool:
        """Validate the entity has required fields."""
        return bool(self.name and isinstance(self.type, EntityType))

    def to_dict(self) -> Dict:
        """Convert entity to dictionary for YAML storage."""
        result = {
            "name": self.name,
            "type": self.type.value,
            "contact": self.contact,
            "address": self.address,
        }
        
        if self.notes:
            result["notes"] = self.notes
        if self.url:
            result["url"] = self.url
            
        return result

class EntityManager:
    def __init__(self, yaml_file: Union[str, Path]):
        """Initialize EntityManager with path to entities file."""
        self.yaml_file = Path(yaml_file)

    def load_entities(self) -> List[Entity]:
        """Load entities from YAML file."""
        if not os.path.exists(self.yaml_file):
            return []
        
        try:
            with open(self.yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return []
            
            if not isinstance(data, dict) or 'entities' not in data:
                raise ValueError("Invalid YAML structure. Expected a dictionary with 'entities' key.")
            
            entities_data = data['entities']
            if not isinstance(entities_data, list):
                raise ValueError("Invalid YAML structure. 'entities' must be a list.")
            
            entities = []
            for entity_data in entities_data:
                try:
                    entities.append(Entity(**entity_data))
                except (ValueError, TypeError) as e:
                    # Skip invalid entities but continue processing
                    print(f"Skipping invalid entity: {str(e)}")
            
            return entities
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")

    def save_entities(self, entities: List[Entity]) -> None:
        """Save entities to YAML file."""
        # Convert entities to serializable dicts
        entity_dicts = [entity.to_dict() for entity in entities]
        data = {
            'entities': entity_dicts
        }
        
        try:
            os.makedirs(os.path.dirname(self.yaml_file), exist_ok=True)
            with open(self.yaml_file, 'w') as f:
                yaml.safe_dump(data, f, default_flow_style=False)
        except (OSError, IOError) as e:
            print(f"Warning: Could not save entities to {self.yaml_file}: {str(e)}")

    def list_entities(self, entity_type: Optional[EntityType] = None) -> List[Entity]:
        """List all entities, optionally filtered by type."""
        entities = self.load_entities()
        if entity_type:
            return [entity for entity in entities if entity.type == entity_type]
        return entities

    def check_missing_entities(self, entity_names: List[str]) -> List[str]:
        """Check for entities in the provided list that don't exist in the database."""
        entities = self.load_entities()
        known_entities = {entity.name for entity in entities}
        return [name for name in entity_names if name not in known_entities]

    def format_entity(self, entity: Entity) -> str:
        """Format an entity for display."""
        lines = [
            f"Name: {entity.name}",
            f"Type: {entity.type.value}",
        ]
        
        if entity.contact:
            if 'primary' in entity.contact:
                lines.append(f"Contact: {entity.contact['primary']}")
            if 'email' in entity.contact:
                lines.append(f"Email: {entity.contact['email']}")
            if 'phone' in entity.contact:
                lines.append(f"Phone: {entity.contact['phone']}")
        
        if entity.address:
            address_parts = []
            for key in ['street', 'city', 'postcode', 'country']:
                if key in entity.address:
                    address_parts.append(entity.address[key])
            if address_parts:
                lines.append("Address:")
                for part in address_parts:
                    lines.append(f"         {part}")
        
        if entity.url:
            lines.append(f"URL: {entity.url}")
        if entity.notes:
            lines.append(f"Notes: {entity.notes}")
        
        return "\n".join(lines) 