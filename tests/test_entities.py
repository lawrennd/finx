import pytest
import yaml
import os
from pathlib import Path
from finx.entities import EntityManager, Entity, EntityType

class TestEntityManager:
    @pytest.fixture
    def temp_entities_file(self, tmp_path):
        """Create a temporary entities file for testing."""
        entities_file = tmp_path / "test_entities.yml"
        test_data = {
            "entities": [
                {
                    "name": "Test Accountants Ltd",
                    "type": "accountant",
                    "contact": {
                        "primary": "John Smith",
                        "email": "john@testaccountants.com",
                        "phone": "123-456-7890"
                    },
                    "address": {
                        "street": "123 Test Street",
                        "city": "London",
                        "postcode": "EC1A 1AA",
                        "country": "UK"
                    },
                    "url": "https://testaccountants.com",
                    "notes": "Our primary accountant"
                },
                {
                    "name": "Test Bank",
                    "type": "bank",
                    "contact": {
                        "primary": "Jane Doe",
                        "email": "jane@testbank.com",
                        "phone": "098-765-4321"
                    },
                    "address": {},
                    "url": "https://testbank.com"
                }
            ]
        }
        with open(entities_file, 'w') as f:
            yaml.dump(test_data, f)
        return entities_file

    def test_load_entities(self, temp_entities_file):
        """Test loading entities from a YAML file."""
        manager = EntityManager(temp_entities_file)
        entities = manager.load_entities()
        assert len(entities) == 2
        assert entities[0].name == "Test Accountants Ltd"
        assert entities[1].name == "Test Bank"

    def test_load_entities_file_not_found(self):
        """Test handling of missing entities file."""
        manager = EntityManager(Path("nonexistent.yml"))
        entities = manager.load_entities()
        assert entities == []

    def test_load_entities_invalid_yaml(self, temp_entities_file):
        with open(temp_entities_file, 'w') as f:
            f.write("invalid: yaml: structure")
        
        manager = EntityManager(temp_entities_file)
        with pytest.raises(ValueError) as e:
            manager.load_entities()
        assert "Invalid YAML format" in str(e.value)

    def test_load_entities_with_invalid_data(self, tmp_path):
        """Test loading entities with invalid data structure."""
        invalid_file = tmp_path / "invalid_data.yml"
        test_data = {
            "entities": [
                {"invalid": "data"},  # Missing required fields
                {"name": "Test", "type": "invalid_type"},  # Invalid type
                {}  # Empty entity
            ]
        }
        with open(invalid_file, 'w') as f:
            yaml.dump(test_data, f)
        
        manager = EntityManager(invalid_file)
        entities = manager.load_entities()
        # Since we now handle errors and skip invalid entities:
        assert len(entities) == 0

    def test_save_entities(self, temp_entities_file):
        """Test saving entities to a YAML file."""
        manager = EntityManager(temp_entities_file)
        entities = [
            Entity(
                name="New Accountant",
                type=EntityType.ACCOUNTANT,
                contact={
                    "primary": "New Contact",
                    "email": "contact@newaccountant.com",
                    "phone": "555-0123"
                },
                address={
                    "street": "456 New Street",
                    "city": "New City",
                    "postcode": "N3W 1AA"
                },
                url="https://newaccountant.com",
                notes="Test notes"
            )
        ]
        manager.save_entities(entities)
        
        # Reload to verify
        new_manager = EntityManager(temp_entities_file)
        loaded_entities = new_manager.load_entities()
        assert len(loaded_entities) == 1
        assert loaded_entities[0].name == "New Accountant"
        assert loaded_entities[0].type == EntityType.ACCOUNTANT
        assert loaded_entities[0].contact["primary"] == "New Contact"
        assert loaded_entities[0].email == "contact@newaccountant.com"
        assert loaded_entities[0].phone == "555-0123"
        assert loaded_entities[0].address["city"] == "New City"
        assert loaded_entities[0].url == "https://newaccountant.com"
        assert loaded_entities[0].notes == "Test notes"

    def test_save_entities_with_invalid_path(self):
        """Test saving entities to an invalid path."""
        manager = EntityManager("/invalid/path/entities.yml")
        entities = [
            Entity(
                name="Test Entity",
                type=EntityType.ACCOUNTANT
            )
        ]
        # Should handle error gracefully and not raise an exception
        manager.save_entities(entities)

    def test_list_entities(self, temp_entities_file):
        """Test listing entities with filtering."""
        manager = EntityManager(temp_entities_file)
        
        # List all entities
        all_entities = manager.list_entities()
        assert len(all_entities) == 2
        
        # List by type
        accountants = manager.list_entities(entity_type=EntityType.ACCOUNTANT)
        assert len(accountants) == 1
        assert accountants[0].name == "Test Accountants Ltd"

    def test_check_missing_entities(self, temp_entities_file):
        """Test checking for missing entities in configuration."""
        manager = EntityManager(temp_entities_file)
        
        # Test with entities that exist
        existing_entities = ["Test Accountants Ltd", "Test Bank"]
        missing = manager.check_missing_entities(existing_entities)
        assert len(missing) == 0
        
        # Test with missing entities
        some_entities = ["Test Accountants Ltd", "Nonexistent Entity"]
        missing = manager.check_missing_entities(some_entities)
        assert len(missing) == 1
        assert missing[0] == "Nonexistent Entity"

    @pytest.fixture
    def temp_yaml_file(self, tmp_path):
        return tmp_path / "entities.yaml"

    @pytest.fixture
    def sample_entities(self):
        return [
            Entity(name="Test Accountant", 
                  type=EntityType.ACCOUNTANT,
                  email="test@example.com",
                  phone="123-456-7890"),
            Entity(name="Test Bank",
                  type=EntityType.BANK,
                  email="bank@example.com",
                  phone="098-765-4321")
        ]

    def test_entity_manager_init(self, temp_yaml_file):
        manager = EntityManager(temp_yaml_file)
        assert manager.yaml_file == temp_yaml_file

    def test_load_entities_empty_file(self, temp_yaml_file):
        manager = EntityManager(temp_yaml_file)
        assert manager.load_entities() == []

    def test_load_entities_invalid_yaml(self, temp_yaml_file):
        with open(temp_yaml_file, 'w') as f:
            f.write("invalid: yaml: structure")
        
        manager = EntityManager(temp_yaml_file)
        with pytest.raises(ValueError) as e:
            manager.load_entities()
        assert "Invalid YAML format" in str(e.value)

    def test_load_entities_invalid_entities_type(self, temp_yaml_file):
        with open(temp_yaml_file, 'w') as f:
            yaml.safe_dump({'entities': 'not a list'}, f)
        
        manager = EntityManager(temp_yaml_file)
        with pytest.raises(ValueError, match="'entities' must be a list"):
            manager.load_entities()

    def test_save_and_load_entities(self, temp_yaml_file, sample_entities):
        manager = EntityManager(temp_yaml_file)
        
        # Save entities
        manager.save_entities(sample_entities)
        
        # Load entities
        loaded_entities = manager.load_entities()
        
        # Verify loaded entities match original
        assert len(loaded_entities) == len(sample_entities)
        for original, loaded in zip(sample_entities, loaded_entities):
            assert loaded.name == original.name
            assert loaded.type == original.type
            assert loaded.email == original.email
            assert loaded.phone == original.phone

    def test_save_entities_creates_directory(self, tmp_path):
        nested_path = tmp_path / "nested" / "path" / "entities.yaml"
        manager = EntityManager(nested_path)
        
        manager.save_entities([
            Entity(name="Test", type=EntityType.OTHER, email="test@test.com", phone="123")
        ])
        
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_list_entities_by_type(self, temp_yaml_file, sample_entities):
        manager = EntityManager(temp_yaml_file)
        manager.save_entities(sample_entities)
        
        accountants = manager.list_entities(EntityType.ACCOUNTANT)
        assert len(accountants) == 1
        assert accountants[0].name == "Test Accountant"
        
        banks = manager.list_entities(EntityType.BANK)
        assert len(banks) == 1
        assert banks[0].name == "Test Bank"

    def test_format_entity(self, temp_entities_file):
        """Test formatting an entity for display."""
        # Full entity with all fields
        entity = Entity(
            name="Test Entity",
            type=EntityType.ACCOUNTANT,
            contact={
                "primary": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890"
            },
            address={
                "street": "123 Test St",
                "city": "Test City",
                "postcode": "12345",
                "country": "Test Country"
            },
            notes="Test notes",
            url="http://test.com"
        )
        
        manager = EntityManager(temp_entities_file)
        formatted = manager.format_entity(entity)
        
        assert "Name: Test Entity" in formatted
        assert "Type: accountant" in formatted
        assert "Contact: John Doe" in formatted
        assert "Email: john@example.com" in formatted
        assert "Phone: 123-456-7890" in formatted
        assert "Address:" in formatted
        assert "123 Test St" in formatted
        assert "Test City" in formatted
        assert "12345" in formatted
        assert "Test Country" in formatted
        assert "URL: http://test.com" in formatted
        assert "Notes: Test notes" in formatted
        
        # Minimal entity
        minimal_entity = Entity(
            name="Minimal Entity",
            type=EntityType.BANK
        )
        
        minimal_formatted = manager.format_entity(minimal_entity)
        assert "Name: Minimal Entity" in minimal_formatted
        assert "Type: bank" in minimal_formatted
        assert "Contact:" not in minimal_formatted
        assert "Address:" not in minimal_formatted
        assert "URL:" not in minimal_formatted
        assert "Notes:" not in minimal_formatted

class TestEntity:
    def test_entity_creation(self):
        """Test creating an entity with all fields."""
        entity = Entity(
            name="Test Entity",
            type=EntityType.ACCOUNTANT,
            contact={
                "primary": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890"
            },
            address={
                "street": "123 Test St",
                "city": "Test City",
                "postcode": "12345",
                "country": "Test Country"
            },
            notes="Test notes",
            url="http://test.com"
        )
        
        assert entity.name == "Test Entity"
        assert entity.type == EntityType.ACCOUNTANT
        assert entity.contact["primary"] == "John Doe"
        assert entity.contact["email"] == "john@example.com"
        assert entity.contact["phone"] == "123-456-7890"
        assert entity.email == "john@example.com"  # Check sync
        assert entity.phone == "123-456-7890"  # Check sync
        assert entity.address["street"] == "123 Test St"
        assert entity.notes == "Test notes"
        assert entity.url == "http://test.com"

    def test_entity_creation_minimal(self):
        """Test creating an entity with minimal required fields."""
        entity = Entity(
            name="Test Entity",
            type="accountant"  # Test string conversion
        )
        
        assert entity.name == "Test Entity"
        assert entity.type == EntityType.ACCOUNTANT
        assert entity.contact == {}
        assert entity.address == {}
        assert entity.notes is None
        assert entity.url is None
        assert entity.email is None
        assert entity.phone is None

    def test_entity_validation(self):
        """Test entity validation."""
        # Valid entity
        entity = Entity(name="Test", type=EntityType.ACCOUNTANT)
        assert entity.validate()
        
        # Invalid - missing name
        with pytest.raises(ValueError):
            Entity(name="", type=EntityType.ACCOUNTANT)
        
        # Invalid - invalid type
        with pytest.raises(ValueError):
            Entity(name="Test", type="invalid_type")

    def test_entity_type_conversion(self):
        """Test entity type conversion from string."""
        # Test valid conversions
        entity1 = Entity(name="Test", type="accountant")
        assert entity1.type == EntityType.ACCOUNTANT
        
        entity2 = Entity(name="Test", type="bank")
        assert entity2.type == EntityType.BANK
        
        # Test invalid conversion
        with pytest.raises(ValueError):
            Entity(name="Test", type="invalid")

    def test_entity_to_dict(self):
        """Test converting entity to dictionary."""
        entity = Entity(
            name="Test Entity",
            type=EntityType.ACCOUNTANT,
            contact={
                "primary": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890"
            },
            address={
                "street": "123 Test St",
                "city": "Test City"
            },
            notes="Test notes",
            url="http://test.com"
        )
        
        data = entity.to_dict()
        assert data["name"] == "Test Entity"
        assert data["type"] == "accountant"
        assert data["contact"]["primary"] == "John Doe"
        assert data["contact"]["email"] == "john@example.com"
        assert data["contact"]["phone"] == "123-456-7890"
        assert data["address"]["street"] == "123 Test St"
        assert data["address"]["city"] == "Test City"
        assert data["notes"] == "Test notes"
        assert data["url"] == "http://test.com"

    def test_entity_to_dict_minimal(self):
        """Test converting minimal entity to dictionary."""
        entity = Entity(name="Test", type=EntityType.ACCOUNTANT)
        data = entity.to_dict()
        
        assert data["name"] == "Test"
        assert data["type"] == "accountant"
        assert data["contact"] == {}
        assert data["address"] == {} 