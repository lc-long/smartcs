"""add new tables and columns for advanced features

Revision ID: f8831f0f426b
Revises: 001
Create Date: 2026-05-02 00:18:24.328768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f8831f0f426b'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('products',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('sku', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('category', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('price', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('stock', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('warranty_months', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('image_url', sa.VARCHAR(length=500), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('products_pkey'))
    )
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_table('loyalty_points',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('points', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('balance', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('type', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('reference_id', sa.VARCHAR(length=50), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('loyalty_points_pkey'))
    )
    op.create_index(op.f('ix_loyalty_points_customer_id'), 'loyalty_points', ['customer_id'], unique=False)
    op.create_table('knowledge_articles',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('tags', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('view_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('is_published', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('knowledge_articles_pkey'))
    )
    op.create_index(op.f('ix_knowledge_articles_category'), 'knowledge_articles', ['category'], unique=False)
    op.create_table('customers',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('phone', sa.VARCHAR(length=20), autoincrement=True, nullable=True),
    sa.Column('address', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('vip_level', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('customers_pkey'))
    )
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=True)
    op.create_table('orders',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_no', sa.VARCHAR(length=30), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('total_amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('shipping_address', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('notes', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('orders_pkey'))
    )
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_order_no'), 'orders', ['order_no'], unique=True)
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_table('order_items',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('product_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('product_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('unit_price', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('subtotal', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('order_items_pkey'))
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_table('invoices',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('invoice_no', sa.VARCHAR(length=30), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('tax_amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('total_amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('due_date', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('paid_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('invoices_pkey'))
    )
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_no'), 'invoices', ['invoice_no'], unique=True)
    op.create_index(op.f('ix_invoices_customer_id'), 'invoices', ['customer_id'], unique=False)
    op.create_table('payments',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('payment_no', sa.VARCHAR(length=30), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('method', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('transaction_id', sa.VARCHAR(length=100), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('payments_pkey'))
    )
    op.create_index(op.f('ix_payments_payment_no'), 'payments', ['payment_no'], unique=True)
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_table('refunds',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('refund_no', sa.VARCHAR(length=30), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('reason', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('approved_by', sa.VARCHAR(length=100), autoincrement=True, nullable=True),
    sa.Column('approved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('refunds_pkey'))
    )
    op.create_index(op.f('ix_refunds_status'), 'refunds', ['status'], unique=False)
    op.create_index(op.f('ix_refunds_refund_no'), 'refunds', ['refund_no'], unique=True)
    op.create_index(op.f('ix_refunds_order_id'), 'refunds', ['order_id'], unique=False)
    op.create_table('support_tickets',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('ticket_no', sa.VARCHAR(length=30), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('category', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('priority', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('assigned_to', sa.VARCHAR(length=100), autoincrement=True, nullable=True),
    sa.Column('resolved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('support_tickets_pkey'))
    )
    op.create_index(op.f('ix_support_tickets_ticket_no'), 'support_tickets', ['ticket_no'], unique=True)
    op.create_index(op.f('ix_support_tickets_status'), 'support_tickets', ['status'], unique=False)
    op.create_index(op.f('ix_support_tickets_customer_id'), 'support_tickets', ['customer_id'], unique=False)
    op.create_table('order_status_history',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('old_status', sa.VARCHAR(length=20), autoincrement=True, nullable=True),
    sa.Column('new_status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('changed_by', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('notes', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('order_status_history_pkey'))
    )
    op.create_index(op.f('ix_order_status_history_order_id'), 'order_status_history', ['order_id'], unique=False)
    op.create_table('shipments',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('shipment_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('carrier', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('tracking_no', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('shipped_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('delivered_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('estimated_delivery', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('current_location', sa.VARCHAR(length=200), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('shipments_pkey'))
    )
    op.create_index(op.f('ix_shipments_tracking_no'), 'shipments', ['tracking_no'], unique=False)
    op.create_index(op.f('ix_shipments_shipment_no'), 'shipments', ['shipment_no'], unique=True)
    op.create_index(op.f('ix_shipments_order_id'), 'shipments', ['order_id'], unique=False)
    op.create_table('coupons',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('discount_type', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('discount_value', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('min_order_amount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('max_discount', sa.NUMERIC(precision=10, scale=2), autoincrement=True, nullable=True),
    sa.Column('usage_limit', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('used_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('valid_from', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('valid_until', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('coupons_pkey'))
    )
    op.create_index(op.f('ix_coupons_code'), 'coupons', ['code'], unique=True)
    op.create_table('customer_coupons',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('coupon_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('is_used', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('used_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('customer_coupons_pkey'))
    )
    op.create_index(op.f('ix_customer_coupons_customer_id'), 'customer_coupons', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_coupons_coupon_id'), 'customer_coupons', ['coupon_id'], unique=False)
    op.create_table('product_reviews',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('product_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('rating', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), autoincrement=True, nullable=True),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('is_anonymous', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('helpful_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('product_reviews_pkey'))
    )
    op.create_index(op.f('ix_product_reviews_product_id'), 'product_reviews', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_reviews_customer_id'), 'product_reviews', ['customer_id'], unique=False)
    op.create_table('customer_feedback',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('order_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('ticket_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('type', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('subject', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('rating', sa.INTEGER(), autoincrement=True, nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('response', sa.TEXT(), autoincrement=True, nullable=True),
    sa.Column('responded_by', sa.VARCHAR(length=100), autoincrement=True, nullable=True),
    sa.Column('responded_at', postgresql.TIMESTAMP(timezone=True), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('customer_feedback_pkey'))
    )
    op.create_index(op.f('ix_customer_feedback_customer_id'), 'customer_feedback', ['customer_id'], unique=False)
    op.create_table('shipment_tracking',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('shipment_id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('event_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('location', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('event_time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('shipment_tracking_pkey'))
    )
    op.create_index(op.f('ix_shipment_tracking_shipment_id'), 'shipment_tracking', ['shipment_id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('username', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('hashed_password', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('full_name', sa.VARCHAR(length=100), autoincrement=True, nullable=True),
    sa.Column('role', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('customer_id', sa.VARCHAR(length=36), autoincrement=True, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('users_pkey'))
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_table('shipment_tracking')
    op.drop_table('shipments')
    op.drop_table('customer_coupons')
    op.drop_table('coupons')
    op.drop_table('product_reviews')
    op.drop_table('customer_feedback')
    op.drop_table('support_tickets')
    op.drop_table('refunds')
    op.drop_table('payments')
    op.drop_table('invoices')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('customers')
    op.drop_table('knowledge_articles')
    op.drop_table('loyalty_points')
    op.drop_table('products')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
