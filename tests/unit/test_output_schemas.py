"""
Unit tests for OUTPUT_SCHEMAS and schema helper functions.
"""
import pytest
from app.config import (
    OUTPUT_SCHEMAS,
    get_output_schema,
    generate_json_schema_instruction
)


def test_output_schemas_structure():
    """Verify OUTPUT_SCHEMAS has correct structure."""
    assert "dream" in OUTPUT_SCHEMAS
    assert "therapy" in OUTPUT_SCHEMAS

    for entry_type, schema in OUTPUT_SCHEMAS.items():
        assert "description" in schema
        assert "fields" in schema
        assert isinstance(schema["fields"], dict)

        for field_name, field_config in schema["fields"].items():
            assert "type" in field_config
            assert "item_type" in field_config
            assert "description" in field_config
            assert "required" in field_config


def test_dream_schema_fields():
    """Verify dream schema has expected fields."""
    schema = OUTPUT_SCHEMAS["dream"]
    assert "themes" in schema["fields"]
    assert "emotions" in schema["fields"]
    assert "characters" in schema["fields"]
    assert "locations" in schema["fields"]


def test_therapy_schema_fields():
    """Verify therapy schema has expected fields."""
    schema = OUTPUT_SCHEMAS["therapy"]
    assert "topics" in schema["fields"]
    assert "insights" in schema["fields"]
    assert "action_items" in schema["fields"]


def test_get_output_schema_success():
    """Test successful schema retrieval."""
    schema = get_output_schema("dream")
    assert "fields" in schema
    assert "themes" in schema["fields"]
    assert "emotions" in schema["fields"]


def test_get_output_schema_therapy():
    """Test successful schema retrieval for therapy type."""
    schema = get_output_schema("therapy")
    assert "fields" in schema
    assert "topics" in schema["fields"]
    assert "insights" in schema["fields"]
    assert "action_items" in schema["fields"]


def test_get_output_schema_unknown_type():
    """Test error handling for unknown entry_type."""
    with pytest.raises(ValueError, match="Unknown entry_type"):
        get_output_schema("unknown_type")


def test_generate_json_schema_instruction_dream():
    """Test JSON schema instruction generation for dream."""
    instruction = generate_json_schema_instruction("dream")

    # Should contain all expected elements
    assert "Respond ONLY with valid JSON" in instruction
    assert "cleaned_text" in instruction
    assert "themes" in instruction
    assert "emotions" in instruction
    assert "characters" in instruction
    assert "locations" in instruction

    # Should not contain therapy-specific fields
    assert "topics" not in instruction
    assert "insights" not in instruction
    assert "action_items" not in instruction


def test_generate_json_schema_instruction_therapy():
    """Test schema instruction for therapy entry_type."""
    instruction = generate_json_schema_instruction("therapy")

    # Should contain therapy fields
    assert "topics" in instruction
    assert "insights" in instruction
    assert "action_items" in instruction

    # Should NOT contain dream-specific fields
    assert "themes" not in instruction
    assert "characters" not in instruction
    assert "locations" not in instruction


def test_generate_json_schema_instruction_unknown_type():
    """Test error handling for unknown entry_type in instruction generation."""
    with pytest.raises(ValueError, match="Unknown entry_type"):
        generate_json_schema_instruction("unknown_type")


def test_schema_instruction_format():
    """Test that generated instruction has proper JSON format example."""
    instruction = generate_json_schema_instruction("dream")
    print("test_schema_instruction_format instruction: " + instruction)

    # Should have proper JSON formatting
    assert "{" in instruction
    assert "}" in instruction
    assert "cleaned_text" in instruction


def test_all_fields_optional():
    """Verify all analysis fields are optional (required: False)."""
    for entry_type, schema in OUTPUT_SCHEMAS.items():
        for field_name, field_config in schema["fields"].items():
            assert field_config["required"] is False, (
                f"Field {field_name} in {entry_type} schema should be optional"
            )


def test_schema_fields_are_arrays():
    """Verify all analysis fields are of type array."""
    for entry_type, schema in OUTPUT_SCHEMAS.items():
        for field_name, field_config in schema["fields"].items():
            assert field_config["type"] == "array", (
                f"Field {field_name} in {entry_type} schema should be array type"
            )
