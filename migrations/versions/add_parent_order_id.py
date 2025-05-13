"""Add parent_order_id to orders table

Revision ID: add_parent_order_id
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_parent_order_id'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add parent_order_id column to orders table
    op.add_column('orders', sa.Column('parent_order_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_order_parent',
        'orders', 'orders',
        ['parent_order_id'], ['id']
    )

def downgrade():
    # Remove parent_order_id column from orders table
    op.drop_constraint('fk_order_parent', 'orders', type_='foreignkey')
    op.drop_column('orders', 'parent_order_id') 