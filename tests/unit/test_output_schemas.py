"""
Unit tests for OUTPUT_SCHEMAS and schema helper functions.

Tests for paragraph-based output format (dream) and traditional format (therapy).
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


def test_dream_schema_has_paragraphs():
    """Verify dream schema uses paragraph-based output."""
    schema = OUTPUT_SCHEMAS["dream"]
    assert "paragraphs" in schema["fields"]
    assert schema["fields"]["paragraphs"]["type"] == "array"
    assert schema["fields"]["paragraphs"]["item_type"] == "string"
    assert schema["fields"]["paragraphs"]["required"] is True


def test_therapy_schema_fields():
    """Verify therapy schema has expected fields (traditional format)."""
    schema = OUTPUT_SCHEMAS["therapy"]
    assert "topics" in schema["fields"]
    assert "insights" in schema["fields"]
    assert "action_items" in schema["fields"]


def test_get_output_schema_success():
    """Test successful schema retrieval for dream."""
    schema = get_output_schema("dream")
    assert "fields" in schema
    assert "paragraphs" in schema["fields"]


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


def test_generate_json_schema_instruction_dream_paragraphs():
    """Test JSON schema instruction for dream uses paragraphs array."""
    instruction = generate_json_schema_instruction("dream")

    # Should contain paragraphs-based output
    assert "Respond ONLY with valid JSON" in instruction
    assert "paragraphs" in instruction
    assert "First scene or moment" in instruction

    # Should NOT contain cleaned_text (paragraphs replaces it)
    assert "cleaned_text" not in instruction

    # Should not contain therapy-specific fields
    assert "topics" not in instruction
    assert "insights" not in instruction


def test_generate_json_schema_instruction_therapy():
    """Test schema instruction for therapy entry_type (traditional format)."""
    instruction = generate_json_schema_instruction("therapy")

    # Should contain traditional cleaned_text
    assert "cleaned_text" in instruction

    # Should contain therapy fields
    assert "topics" in instruction
    assert "insights" in instruction
    assert "action_items" in instruction

    # Should NOT contain dream-specific paragraphs
    assert "paragraphs" not in instruction


def test_generate_json_schema_instruction_unknown_type():
    """Test error handling for unknown entry_type in instruction generation."""
    with pytest.raises(ValueError, match="Unknown entry_type"):
        generate_json_schema_instruction("unknown_type")


def test_schema_instruction_format_dream():
    """Test that dream instruction has proper JSON format with paragraphs."""
    instruction = generate_json_schema_instruction("dream")

    # Should have proper JSON formatting
    assert "{" in instruction
    assert "}" in instruction
    assert "paragraphs" in instruction
    assert "[" in instruction  # Array notation


def test_schema_instruction_format_therapy():
    """Test that therapy instruction has proper JSON format with cleaned_text."""
    instruction = generate_json_schema_instruction("therapy")

    # Should have proper JSON formatting
    assert "{" in instruction
    assert "}" in instruction
    assert "cleaned_text" in instruction


def test_therapy_fields_optional():
    """Verify therapy analysis fields are optional (required: False)."""
    schema = OUTPUT_SCHEMAS["therapy"]
    for field_name, field_config in schema["fields"].items():
        assert field_config["required"] is False, (
            f"Field {field_name} in therapy schema should be optional"
        )


def test_dream_paragraphs_required():
    """Verify dream paragraphs field is required (required: True)."""
    schema = OUTPUT_SCHEMAS["dream"]
    assert schema["fields"]["paragraphs"]["required"] is True


def test_schema_fields_are_arrays():
    """Verify all analysis fields are of type array."""
    for entry_type, schema in OUTPUT_SCHEMAS.items():
        for field_name, field_config in schema["fields"].items():
            assert field_config["type"] == "array", (
                f"Field {field_name} in {entry_type} schema should be array type"
            )


# =============================================================================
# MANUAL VERIFICATION TESTS - Print actual prompts to console
# Run with: pytest tests/unit/test_output_schemas.py -v -s
# =============================================================================

def test_print_dream_schema_instruction():
    """
    MANUAL VERIFICATION: Print full dream schema instruction.

    Run with: pytest tests/unit/test_output_schemas.py::test_print_dream_schema_instruction -v -s
    """
    instruction = generate_json_schema_instruction("dream")

    print("\n")
    print("=" * 80)
    print("DREAM SCHEMA INSTRUCTION (paragraph-based output)")
    print("=" * 80)
    print(instruction)
    print("=" * 80)
    print("\n")

    # Basic assertion to ensure test runs
    assert instruction is not None


def test_print_therapy_schema_instruction():
    """
    MANUAL VERIFICATION: Print full therapy schema instruction.

    Run with: pytest tests/unit/test_output_schemas.py::test_print_therapy_schema_instruction -v -s
    """
    instruction = generate_json_schema_instruction("therapy")

    print("\n")
    print("=" * 80)
    print("THERAPY SCHEMA INSTRUCTION (traditional cleaned_text output)")
    print("=" * 80)
    print(instruction)
    print("=" * 80)
    print("\n")

    # Basic assertion to ensure test runs
    assert instruction is not None


def test_print_all_schemas_comparison():
    """
    MANUAL VERIFICATION: Print and compare all schema instructions side by side.

    Run with: pytest tests/unit/test_output_schemas.py::test_print_all_schemas_comparison -v -s
    """
    print("\n")
    print("=" * 80)
    print("ALL SCHEMA INSTRUCTIONS COMPARISON")
    print("=" * 80)

    for entry_type in OUTPUT_SCHEMAS.keys():
        instruction = generate_json_schema_instruction(entry_type)
        print(f"\n--- {entry_type.upper()} ---")
        print(instruction)
        print()

    print("=" * 80)
    print("\n")

    # Basic assertion to ensure test runs
    assert len(OUTPUT_SCHEMAS) >= 2
