"""add_speaker_diarization

Revision ID: f8a9b0c1d2e3
Revises: 27014772c518
Create Date: 2025-12-17 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from schema_config import get_schema


# revision identifiers, used by Alembic.
revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, None] = '27014772c518'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add speaker diarization columns to transcriptions table."""
    schema = get_schema()

    # Add enable_diarization column (boolean, NOT NULL, default False)
    op.add_column(
        'transcriptions',
        sa.Column(
            'enable_diarization',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='Whether speaker diarization was requested'
        ),
        schema=schema
    )

    # Add speaker_count column (integer, NOT NULL, default 1)
    op.add_column(
        'transcriptions',
        sa.Column(
            'speaker_count',
            sa.Integer(),
            nullable=False,
            server_default='1',
            comment='Expected number of speakers (1-10)'
        ),
        schema=schema
    )

    # Add segments column (encrypted JSON, nullable for backward compatibility)
    op.add_column(
        'transcriptions',
        sa.Column(
            'segments',
            sa.LargeBinary(),
            nullable=True,
            comment='Encrypted JSON array of segments with speaker labels'
        ),
        schema=schema
    )

    # Remove server defaults after column creation (keep NOT NULL constraint)
    op.alter_column(
        'transcriptions',
        'enable_diarization',
        server_default=None,
        schema=schema
    )
    op.alter_column(
        'transcriptions',
        'speaker_count',
        server_default=None,
        schema=schema
    )


def downgrade() -> None:
    """Remove speaker diarization columns from transcriptions table."""
    schema = get_schema()

    op.drop_column('transcriptions', 'segments', schema=schema)
    op.drop_column('transcriptions', 'speaker_count', schema=schema)
    op.drop_column('transcriptions', 'enable_diarization', schema=schema)
