"""Phase 2 ledger engine schema updates

Revision ID: 3c3db0ba7db1
Revises: 2c1138bdc9d7
Create Date: 2026-11-13 12:03:48.551325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c3db0ba7db1'
down_revision: Union[str, None] = '2c1138bdc9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Batch alter customers table
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('phone',
                   existing_type=sa.VARCHAR(length=20),
                   nullable=True)

    # Batch alter transactions table
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('COMPLETED', 'REVERSED', name='transaction_status_enum'), nullable=False, server_default='COMPLETED'))
        batch_op.add_column(sa.Column('idempotency_key', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('reversal_reason', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_transactions_idempotency_key'), ['idempotency_key'], unique=True)
        batch_op.create_index(batch_op.f('ix_transactions_status'), ['status'], unique=False)
        batch_op.drop_constraint('fk_transactions_customer_id_customers', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_transactions_customer_id_customers',
            'customers',
            ['customer_id'],
            ['id'],
            ondelete='RESTRICT',
        )


def downgrade() -> None:
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transactions_customer_id_customers', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_transactions_customer_id_customers',
            'customers',
            ['customer_id'],
            ['id'],
            ondelete='CASCADE',
        )
        batch_op.drop_index(batch_op.f('ix_transactions_status'))
        batch_op.drop_index(batch_op.f('ix_transactions_idempotency_key'))
        batch_op.drop_column('reversal_reason')
        batch_op.drop_column('idempotency_key')
        batch_op.drop_column('status')

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('phone',
                   existing_type=sa.VARCHAR(length=20),
                   nullable=False)
