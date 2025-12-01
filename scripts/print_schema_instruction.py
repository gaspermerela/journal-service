#!/usr/bin/env python3
"""
Standalone script to print the JSON schema instructions for manual verification.

This script does NOT import app.config (which requires env vars), instead it
duplicates the schema logic for testing purposes.

Run with: python scripts/print_schema_instruction.py
"""

# Duplicate schema definitions from app/config.py for standalone testing
OUTPUT_SCHEMAS = {
    "dream": {
        "description": "Schema for dream journal entries with paragraph-based output",
        "fields": {
            "paragraphs": {
                "type": "array",
                "item_type": "string",
                "description": "List of paragraphs, each representing one scene or moment in the dream",
                "required": True
            }
        }
    },
    "therapy": {
        "description": "Analysis schema for therapy session transcriptions",
        "fields": {
            "topics": {
                "type": "array",
                "item_type": "string",
                "description": "Main topics discussed in session",
                "required": False
            },
            "insights": {
                "type": "array",
                "item_type": "string",
                "description": "Key insights or realizations",
                "required": False
            },
            "action_items": {
                "type": "array",
                "item_type": "string",
                "description": "Action items or next steps identified",
                "required": False
            }
        }
    },
}


def get_output_schema(entry_type: str) -> dict:
    """Get output schema for a given entry type."""
    if entry_type not in OUTPUT_SCHEMAS:
        raise ValueError(f"Unknown entry_type '{entry_type}'")
    return OUTPUT_SCHEMAS[entry_type]


def generate_json_schema_instruction(entry_type: str) -> str:
    """
    Generate JSON schema instruction to append to prompts.

    This is the EXACT same logic as app/config.py - duplicated here for standalone testing.
    """
    schema = get_output_schema(entry_type)

    # Build example JSON structure based on schema fields
    example_fields = []

    # Check if schema has 'paragraphs' field (new paragraph-based output)
    if "paragraphs" in schema["fields"]:
        # Paragraph-based output: paragraphs array replaces cleaned_text
        example_fields.append('  "paragraphs": ["First scene or moment...", "Second scene...", "..."]')
    else:
        # Traditional output: cleaned_text as primary field
        example_fields.append('  "cleaned_text": "The cleaned and formatted text here"')

    # Add remaining fields from schema (excluding paragraphs if already added)
    for field_name, field_config in schema["fields"].items():
        if field_name == "paragraphs":
            continue  # Already handled above
        if field_config["type"] == "array":
            example_fields.append(f'  "{field_name}": ["{field_config["description"]}"]')
        else:
            example_fields.append(f'  "{field_name}": "{field_config["description"]}"')

    example_json = "{{\n" + ",\n".join(example_fields) + "\n}}"

    instruction = f"""
Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{example_json}
"""

    return instruction.strip()


def main():
    print()
    print("=" * 80)
    print("DREAM SCHEMA INSTRUCTION (paragraph-based output)")
    print("=" * 80)
    print(generate_json_schema_instruction("dream"))
    print("=" * 80)
    print()
    print("=" * 80)
    print("THERAPY SCHEMA INSTRUCTION (traditional cleaned_text output)")
    print("=" * 80)
    print(generate_json_schema_instruction("therapy"))
    print("=" * 80)
    print()

    # Show what a complete dream prompt would look like
    print("=" * 80)
    print("EXAMPLE: Complete dream cleanup prompt with schema instruction")
    print("=" * 80)

    # This is similar to what's in the database (dream_v8 style)
    example_prompt_template = """Clean this Slovenian dream transcription for a personal journal.

RULES:
1. Fix grammar, spelling, punctuation. Use "knjižna slovenščina".
2. Write in present tense, first person ("jaz").
3. Break into short paragraphs (one scene/moment each).
4. Remove only STT artifacts: filler words ("v bistvu", "torej"), false starts, repeated words, audio junk ("Hvala").
5. KEEP EVERY specific detail - actions, objects, descriptions, sensory details, feelings. Unusual or strange details are ESPECIALLY important to preserve exactly as stated.
6. Do NOT summarize. Do NOT shorten. Do NOT invent or explain anything not in the original.
7. Fix obvious mishearings

OUTPUT FORMAT:
{output_format}

TRANSCRIPTION:
"{transcription_text}"
"""

    schema_instruction = generate_json_schema_instruction("dream")
    complete_prompt = example_prompt_template.replace("{output_format}", schema_instruction)
    complete_prompt = complete_prompt.replace("{transcription_text}", "[YOUR TRANSCRIPTION HERE]")

    print(complete_prompt)
    print("=" * 80)


if __name__ == "__main__":
    main()
