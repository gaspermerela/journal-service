"""add_prompt_templates_table

Revision ID: 240e345c9e39
Revises: 7124b003165b
Create Date: 2025-11-11 17:23:30.419175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '240e345c9e39'
down_revision: Union[str, None] = '7124b003165b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create prompt_templates table
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('entry_type', sa.String(length=50), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'entry_type', name='uq_prompt_name_entry_type'),
        schema='journal'
    )

    # Create indexes
    op.create_index(
        'ix_prompt_templates_active',
        'prompt_templates',
        ['entry_type', 'is_active'],
        unique=False,
        schema='journal',
        postgresql_where=sa.text('is_active = true')
    )
    op.create_index(
        'ix_prompt_templates_entry_type',
        'prompt_templates',
        ['entry_type'],
        unique=False,
        schema='journal'
    )

    # Add prompt_template_id to cleaned_entries
    op.add_column(
        'cleaned_entries',
        sa.Column('prompt_template_id', sa.Integer(), nullable=True),
        schema='journal'
    )
    op.create_foreign_key(
        'fk_cleaned_entries_prompt_template',
        'cleaned_entries',
        'prompt_templates',
        ['prompt_template_id'],
        ['id'],
        source_schema='journal',
        referent_schema='journal',
        ondelete='SET NULL'
    )
    op.create_index(
        'ix_cleaned_entries_prompt_template_id',
        'cleaned_entries',
        ['prompt_template_id'],
        unique=False,
        schema='journal'
    )

    # Drop old prompt_used column
    op.drop_column('cleaned_entries', 'prompt_used', schema='journal')

    # Seed initial prompts (migrated from hardcoded constants)
    op.execute("""
        INSERT INTO journal.prompt_templates (name, entry_type, prompt_text, description, is_active, version)
        VALUES
        (
            'dream_v1',
            'dream',
            'You are a dream journal assistant. Clean up this voice transcription of a dream:

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Organize into coherent paragraphs
4. Keep the original meaning and emotional tone intact
5. Extract key themes (max 5)
6. Identify emotions present
7. Note any people/entities mentioned
8. Note any locations mentioned

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here",
  "themes": ["theme1", "theme2"],
  "emotions": ["emotion1", "emotion2"],
  "characters": ["person or entity"],
  "locations": ["place mentioned"]
}}',
            'Original dream cleanup prompt',
            true,
            1
        ),
        (
            'generic_v1',
            'journal',
            'You are a transcription cleanup assistant. Clean up this voice transcription:

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Organize into coherent paragraphs
4. Keep the original meaning and tone intact
5. Extract key topics or themes (max 5)
6. Identify the overall sentiment or emotions
7. Note any people/entities mentioned
8. Note any locations mentioned

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here",
  "themes": ["topic1", "topic2"],
  "emotions": ["emotion1", "emotion2"],
  "characters": ["person or entity"],
  "locations": ["place mentioned"]
}}',
            'Generic cleanup prompt for journal entries',
            true,
            1
        ),
        (
            'generic_v1',
            'meeting',
            'You are a transcription cleanup assistant. Clean up this voice transcription:

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Organize into coherent paragraphs
4. Keep the original meaning and tone intact
5. Extract key topics or themes (max 5)
6. Identify the overall sentiment or emotions
7. Note any people/entities mentioned
8. Note any locations mentioned

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here",
  "themes": ["topic1", "topic2"],
  "emotions": ["emotion1", "emotion2"],
  "characters": ["person or entity"],
  "locations": ["place mentioned"]
}}',
            'Generic cleanup prompt for meeting notes',
            true,
            1
        ),
        (
            'generic_v1',
            'note',
            'You are a transcription cleanup assistant. Clean up this voice transcription:

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Organize into coherent paragraphs
4. Keep the original meaning and tone intact
5. Extract key topics or themes (max 5)
6. Identify the overall sentiment or emotions
7. Note any people/entities mentioned
8. Note any locations mentioned

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here",
  "themes": ["topic1", "topic2"],
  "emotions": ["emotion1", "emotion2"],
  "characters": ["person or entity"],
  "locations": ["place mentioned"]
}}',
            'Generic cleanup prompt for notes',
            true,
            1
        );
    """)


def downgrade() -> None:
    # Re-add prompt_used column
    op.add_column(
        'cleaned_entries',
        sa.Column('prompt_used', sa.Text(), nullable=True),
        schema='journal'
    )

    # Drop foreign key and column
    op.drop_constraint(
        'fk_cleaned_entries_prompt_template',
        'cleaned_entries',
        schema='journal',
        type_='foreignkey'
    )
    op.drop_index(
        'ix_cleaned_entries_prompt_template_id',
        'cleaned_entries',
        schema='journal'
    )
    op.drop_column('cleaned_entries', 'prompt_template_id', schema='journal')

    # Drop indexes
    op.drop_index('ix_prompt_templates_entry_type', 'prompt_templates', schema='journal')
    op.drop_index('ix_prompt_templates_active', 'prompt_templates', schema='journal')

    # Drop table
    op.drop_table('prompt_templates', schema='journal')
