-- =====================================================================================
-- ========================= IDENTITY SERVICE ==========================================
-- =====================================================================================

CREATE TABLE roles (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    name        VARCHAR(50) NOT NULL UNIQUE,
    status      VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED'))
);

CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    phone           VARCHAR(15) NOT NULL UNIQUE,
    google_subject  VARCHAR(255),
    password_hash   VARCHAR(255) NOT NULL,
    role_id         UUID NOT NULL REFERENCES roles(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'LOCKED', 'DELETED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_accounts_role_id ON accounts(role_id);
-- A verified Google provider subject can link to at most one account; local
-- accounts that have not linked Google keep this field NULL.
CREATE UNIQUE INDEX uk_accounts_google_subject ON accounts(google_subject) WHERE google_subject IS NOT NULL;

CREATE TABLE employees (
    account_id      UUID PRIMARY KEY REFERENCES accounts(id),
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    avatar_file_id  UUID,
    address         VARCHAR(255),
    gender          VARCHAR(10) NOT NULL CHECK (gender IN ('MALE', 'FEMALE')),
    birthday        DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE admins (
    account_id      UUID PRIMARY KEY REFERENCES accounts(id),
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    avatar_file_id  UUID,
    address         VARCHAR(255),
    gender          VARCHAR(10) NOT NULL CHECK (gender IN ('MALE', 'FEMALE')),
    birthday        DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE customers (
    account_id      UUID PRIMARY KEY REFERENCES accounts(id),
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    avatar_file_id  UUID,
    gender          VARCHAR(10) CHECK (gender IN ('MALE', 'FEMALE', 'OTHER')),
    birthday        DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE customer_addresses (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    customer_id     UUID NOT NULL REFERENCES customers(account_id),
    recipient_name  VARCHAR(100) NOT NULL,
    phone           VARCHAR(15) NOT NULL,
    address_line    VARCHAR(500) NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_customer_addresses_customer_id ON customer_addresses(customer_id);
-- Only one default address per customer, not a single default across the whole table.
CREATE UNIQUE INDEX uk_customer_addresses_default ON customer_addresses(customer_id) WHERE is_default = true;

-- Seed data
INSERT INTO roles (name, status) VALUES
    ('ROLE_CUSTOMER', 'ACTIVE'),
    ('ROLE_EMPLOYEE', 'ACTIVE'),
    ('ROLE_ADMIN', 'ACTIVE');


-- =====================================================================================
-- ========================= CATALOG SERVICE ===========================================
-- =====================================================================================

CREATE TABLE brands (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    name            VARCHAR(255) NOT NULL,
    seo_name        VARCHAR(255) NOT NULL,
    description     TEXT,
    image_file_id   UUID, -- ref -> Media Service (files.id), no cross-DB FK
    status          VARCHAR(15) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Unique only among non-deleted rows, so a soft-deleted brand's name can be reused.
CREATE UNIQUE INDEX uk_brands_name ON brands(name) WHERE status <> 'DELETED';
CREATE UNIQUE INDEX uk_brands_seo_name ON brands(seo_name) WHERE status <> 'DELETED';

CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    name        VARCHAR(255) NOT NULL,
    seo_name    VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id   UUID REFERENCES categories(id),
    status      VARCHAR(15) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
-- Unique only among non-deleted rows, so a soft-deleted category's name can be reused.
CREATE UNIQUE INDEX uk_categories_name ON categories(name) WHERE status <> 'DELETED';
CREATE UNIQUE INDEX uk_categories_seo_name ON categories(seo_name) WHERE status <> 'DELETED';

CREATE TABLE attribute_definitions (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    key             VARCHAR(100) NOT NULL UNIQUE,
    display_name    VARCHAR(255) NOT NULL,
    data_type       VARCHAR(20) NOT NULL CHECK (data_type IN ('NUMBER', 'STRING', 'ENUM', 'BOOLEAN')),
    unit            VARCHAR(50),
    allowed_values  JSONB,
    aliases         JSONB,
    filterable      BOOLEAN NOT NULL DEFAULT false,
    comparable      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE category_attribute_groups (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    category_id     UUID NOT NULL REFERENCES categories(id),
    name            VARCHAR(100) NOT NULL,
    display_order   INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_category_attribute_groups_category_id ON category_attribute_groups(category_id);

CREATE TABLE category_attributes (
    id                  UUID PRIMARY KEY DEFAULT uuidv7(),
    category_group_id   UUID NOT NULL REFERENCES category_attribute_groups(id),
    attribute_id        UUID NOT NULL REFERENCES attribute_definitions(id),
    required            BOOLEAN NOT NULL DEFAULT false,
    display_order       INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (category_group_id, attribute_id)
);

CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    name            VARCHAR(255) NOT NULL,
    seo_name        VARCHAR(255) NOT NULL,
    brand_id        UUID REFERENCES brands(id),
    category_id     UUID NOT NULL REFERENCES categories(id),
    specifications  JSONB,
    description     TEXT,
    status          VARCHAR(15) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID NOT NULL, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    updated_at      TIMESTAMPTZ,
    updated_by      UUID  -- ref -> Identity Service (employees.account_id), no cross-DB FK
);
-- Unique only among non-deleted rows, so a soft-deleted product's seo_name can be reused.
CREATE UNIQUE INDEX uk_products_seo_name ON products(seo_name) WHERE status <> 'DELETED';
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_category_id ON products(category_id);

CREATE TABLE product_variants (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    product_id      UUID NOT NULL REFERENCES products(id),
    price           BIGINT NOT NULL CHECK (price >= 0),
    quantity        INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    sku             VARCHAR(100) NOT NULL,
    model           VARCHAR(100),
    image_file_id   UUID, -- ref -> Media Service (files.id), no cross-DB FK - optional variant-specific image
    description     TEXT,
    warranty_months INT NOT NULL CHECK (warranty_months > 0),
    barcode         VARCHAR(100),
    release_at      DATE,
    status          VARCHAR(15) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID NOT NULL, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    updated_at      TIMESTAMPTZ,
    updated_by      UUID -- ref -> Identity Service (employees.account_id), no cross-DB FK
);
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
-- Unique only among non-deleted rows, so a soft-deleted variant's sku/barcode can be reused.
-- barcode is nullable; NULLs never collide.
CREATE UNIQUE INDEX uk_product_variants_sku ON product_variants(sku) WHERE status <> 'DELETED';
CREATE UNIQUE INDEX uk_product_variants_barcode ON product_variants(barcode) WHERE status <> 'DELETED';

CREATE TABLE product_images (
    id                  UUID PRIMARY KEY DEFAULT uuidv7(),
    product_id          UUID NOT NULL REFERENCES products(id),
    image_file_id       UUID NOT NULL, -- ref -> Media Service (files.id), no cross-DB FK
    is_main             BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, image_file_id)
);
-- Only one main image per product.
CREATE UNIQUE INDEX uk_product_images_main ON product_images(product_id)
    WHERE is_main = true;

CREATE TABLE options (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    name        VARCHAR(100) NOT NULL,
    value       VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, value)
);

CREATE TABLE variant_options (
    product_variant_id  UUID NOT NULL REFERENCES product_variants(id),
    option_id           UUID NOT NULL REFERENCES options(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (product_variant_id, option_id)
);
-- The PK only serves lookups by variant; this one serves "variants using this option".
CREATE INDEX idx_variant_options_option_id ON variant_options(option_id);

-- Business rule: a variant can have at most one option of each normalized
-- (trim + uppercase) options.name (e.g. one "Màu sắc", one "Dung lượng").
-- Expressed as a deferred constraint trigger (not a plain UNIQUE) because it
-- depends on joining options.name and must also re-check when an option's own
-- name changes after the fact.
-- Both checks only look at the variants touched by the changed row, never the whole table.
-- Deleting a link can't create a duplicate, so no DELETE trigger is needed.
CREATE OR REPLACE FUNCTION check_variant_option_type_uniqueness()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM variant_options vo
        JOIN options o ON o.id = vo.option_id
        WHERE vo.product_variant_id = NEW.product_variant_id
        GROUP BY upper(trim(o.name))
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'A product variant cannot have multiple options with the same name';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_variant_options_unique_type
    AFTER INSERT OR UPDATE ON variant_options
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_variant_option_type_uniqueness();

-- Renaming an option can make two options of one variant collide; re-check only the
-- variants that use the renamed option.
CREATE OR REPLACE FUNCTION check_option_rename_uniqueness()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM variant_options vo
        JOIN options o ON o.id = vo.option_id
        WHERE vo.product_variant_id IN (
            SELECT product_variant_id FROM variant_options WHERE option_id = NEW.id
        )
        GROUP BY vo.product_variant_id, upper(trim(o.name))
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'A product variant cannot have multiple options with the same name';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_options_type_unique_after_change
    AFTER UPDATE OF name ON options
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_option_rename_uniqueness();

CREATE TABLE product_reviews (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    product_id      UUID NOT NULL REFERENCES products(id),
    order_item_id   UUID NOT NULL UNIQUE, -- ref -> Order Service (order_items.id), no cross-DB FK
    customer_id     UUID NOT NULL,        -- ref -> Identity Service (customers.account_id), no cross-DB FK
    rating          INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    status          VARCHAR(15) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Edit policy (Shopee-style): a review can be edited once, within 30 days of creation.
    -- NULL = never edited; a non-NULL value means the single edit is used up.
    -- "Product must still be on sale" is checked in the service, it spans tables.
    edited_at       TIMESTAMPTZ,
    CHECK (edited_at IS NULL OR (edited_at >= created_at AND edited_at <= created_at + INTERVAL '30 days'))
);
CREATE INDEX idx_product_reviews_product_status_created ON product_reviews (product_id, status, created_at DESC);

-- Outbox: reliable dispatch of replies/events (e.g. stock reserved / out of stock for the order
-- saga) written atomically with the variants.quantity change in the same DB transaction.
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    aggregate_type  VARCHAR(50) NOT NULL,
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    channel         VARCHAR(10) NOT NULL CHECK (channel IN ('KAFKA', 'RABBITMQ')),
    destination     VARCHAR(255) NOT NULL, -- Kafka topic or RabbitMQ routing key
    payload         JSONB NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PUBLISHED', 'FAILED')),
    trace_context   VARCHAR(100), -- W3C traceparent captured at write time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at    TIMESTAMPTZ
);
-- The dispatcher only ever polls PENDING rows oldest-first; published rows stay out of the index.
CREATE INDEX idx_outbox_events_pending ON outbox_events(created_at) WHERE status = 'PENDING';

-- Inbox: dedup for at-least-once RabbitMQ/Kafka delivery. event_id is the producer's
-- message id, so re-delivery of the same command/event is a no-op instead of double-processing.
CREATE TABLE inbox_events (
    event_id        UUID PRIMARY KEY,
    consumer_name   VARCHAR(100) NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =====================================================================================
-- ========================= MEDIA SERVICE =============================================
-- =====================================================================================

CREATE TABLE files (
    id                  UUID PRIMARY KEY DEFAULT uuidv7(),
    storage_provider    VARCHAR(30) NOT NULL,
    storage_key         VARCHAR(500) NOT NULL,
    original_name       VARCHAR(255) NOT NULL,
    mime_type           VARCHAR(100) NOT NULL,
    size_bytes          BIGINT NOT NULL CHECK (size_bytes >= 0),
    public_url          VARCHAR(2048),
    status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DELETED')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (storage_provider, storage_key)
);


-- =====================================================================================
-- ========================= ORDER SERVICE =============================================
-- =====================================================================================

CREATE TABLE carts (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    customer_id     UUID NOT NULL UNIQUE, -- ref -> Identity Service (customers.account_id), no cross-DB FK; one cart per customer, no guest carts
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE cart_items (
    cart_id     UUID NOT NULL REFERENCES carts(id),
    variant_id  UUID NOT NULL, -- ref -> Catalog Service (product_variants.id), no cross-DB FK
    quantity    INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (cart_id, variant_id)
);

CREATE TABLE shipping_methods (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    code        VARCHAR(50) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    fee         BIGINT NOT NULL DEFAULT 0 CHECK (fee >= 0),
    status      VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id                  UUID PRIMARY KEY DEFAULT uuidv7(),
    customer_id         UUID NOT NULL, -- ref -> Identity Service (customers.account_id), no cross-DB FK; guests cannot place orders
    order_discount_id   UUID, -- ref -> Promotion Service (discounts.id), no cross-DB FK
    shipping_method_id  UUID NOT NULL REFERENCES shipping_methods(id),
    payment_method_id   UUID NOT NULL, -- ref -> Payment Service (payment_methods.id), no cross-DB FK
    idempotency_key     VARCHAR(100),
    invoice_number      VARCHAR(50) NOT NULL, -- generated at order creation: 'INV-' + 10 random chars, e.g. INV-7K3M9QX2BD; retry on unique violation
    subtotal_amount     BIGINT NOT NULL CHECK (subtotal_amount >= 0), -- sum of line totals AFTER line discounts
    discount_amount     BIGINT NOT NULL DEFAULT 0 CHECK (discount_amount >= 0), -- order-level voucher only (order_discount_id)
    shipping_fee        BIGINT NOT NULL CHECK (shipping_fee >= 0),
    total_amount        BIGINT NOT NULL CHECK (total_amount >= 0),
    note                TEXT,
    delivery_address    VARCHAR(500) NOT NULL,
    recipient_name      VARCHAR(100) NOT NULL,
    recipient_phone     VARCHAR(15) NOT NULL,
    delivered_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    updated_at          TIMESTAMPTZ,
    updated_by          UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    status              VARCHAR(30) NOT NULL DEFAULT 'PENDING_CONFIRMATION'
                            CHECK (status IN (
                                'PENDING_PAYMENT', 'PENDING_CONFIRMATION', 'CONFIRMED',
                                'SHIPPING', 'COMPLETED', 'CANCELLED'
                            )),
    CHECK (status <> 'COMPLETED' OR delivered_at IS NOT NULL), -- invoice date = delivered_at
    CHECK (discount_amount <= subtotal_amount),
    CHECK (total_amount = subtotal_amount - discount_amount + shipping_fee)
);
-- Customer order history, newest first, keyset (cursor) pagination on (created_at, id).
-- Also serves plain lookups by customer_id, so no separate customer_id index is needed.
CREATE INDEX idx_orders_customer_created ON orders(customer_id, created_at DESC, id DESC);
CREATE INDEX idx_orders_shipping_method_id ON orders(shipping_method_id);
-- Admin order search / dashboard counts by status, newest first.
CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC, id DESC);
-- Revenue / invoice reports: only COMPLETED orders, by delivery (invoice) date.
CREATE INDEX idx_orders_completed_delivered ON orders(delivered_at DESC) WHERE status = 'COMPLETED';
-- One order per idempotency key. NULL-safe: multiple NULLs don't collide.
CREATE UNIQUE INDEX uk_orders_idempotency_key ON orders(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE UNIQUE INDEX ux_orders_invoice_number ON orders(invoice_number);

CREATE TABLE order_items (
    id                  UUID PRIMARY KEY DEFAULT uuidv7(),
    order_id            UUID NOT NULL REFERENCES orders(id),
    product_variant_id  UUID NOT NULL, -- ref -> Catalog Service (product_variants.id), no cross-DB FK
    -- Snapshot at order time so order history stays correct if the variant is edited or deleted.
    product_name        VARCHAR(255) NOT NULL,
    sku                 VARCHAR(100) NOT NULL,
    variant_label       VARCHAR(500), -- pre-joined options, e.g. 'Dung lượng: 256GB, Màu sắc: Xanh'
    quantity            INT NOT NULL CHECK (quantity > 0),
    unit_price          BIGINT NOT NULL CHECK (unit_price >= 0),
    discount_id         UUID, -- ref -> Promotion Service (discounts.id), no cross-DB FK
    discount_amount     BIGINT NOT NULL DEFAULT 0 CHECK (discount_amount >= 0), -- total discount for the whole line, not per unit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (order_id, product_variant_id),
    CHECK (discount_amount <= quantity * unit_price)
);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
-- Top-selling statistics group by variant.
CREATE INDEX idx_order_items_product_variant_id ON order_items(product_variant_id);

-- Every status change of an order, written in the same transaction as the orders.status update.
-- The first row of an order has from_status NULL (initial status). Allowed transitions are
-- enforced by the service, not by the DB.
CREATE TABLE order_status_history (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    order_id        UUID NOT NULL REFERENCES orders(id),
    from_status     VARCHAR(30) CHECK (from_status IN (
                        'PENDING_PAYMENT', 'PENDING_CONFIRMATION', 'CONFIRMED',
                        'SHIPPING', 'COMPLETED', 'CANCELLED'
                    )),
    to_status       VARCHAR(30) NOT NULL CHECK (to_status IN (
                        'PENDING_PAYMENT', 'PENDING_CONFIRMATION', 'CONFIRMED',
                        'SHIPPING', 'COMPLETED', 'CANCELLED'
                    )),
    changed_by      UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK; NULL = customer or system
    reason          TEXT, -- e.g. cancellation reason
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_order_status_history_order_created ON order_status_history(order_id, created_at);

-- Outbox: reliable dispatch of messages (Kafka events or RabbitMQ commands) that must
-- be written atomically with a business change in the same DB transaction.
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    aggregate_type  VARCHAR(50) NOT NULL,
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    channel         VARCHAR(10) NOT NULL CHECK (channel IN ('KAFKA', 'RABBITMQ')),
    destination     VARCHAR(255) NOT NULL, -- Kafka topic or RabbitMQ routing key
    payload         JSONB NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PUBLISHED', 'FAILED')),
    trace_context   VARCHAR(100), -- W3C traceparent captured at write time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at    TIMESTAMPTZ
);
-- The dispatcher only ever polls PENDING rows oldest-first; published rows stay out of the index.
CREATE INDEX idx_outbox_events_pending ON outbox_events(created_at) WHERE status = 'PENDING';

-- Inbox: dedup for at-least-once Kafka/RabbitMQ delivery.
CREATE TABLE inbox_events (
    event_id        UUID PRIMARY KEY,
    consumer_name   VARCHAR(100) NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed data
INSERT INTO shipping_methods (code, name, fee) VALUES
    ('STANDARD', 'Standard Delivery', 30000),
    ('EXPRESS', 'Express Delivery', 60000);


-- =====================================================================================
-- ========================= PAYMENT SERVICE ===========================================
-- =====================================================================================

CREATE TABLE payment_methods (
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    code        VARCHAR(50) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE payments (
    id                          UUID PRIMARY KEY DEFAULT uuidv7(),
    order_id                    UUID NOT NULL, -- ref -> Order Service (orders.id), no cross-DB FK
    customer_id                 UUID NOT NULL, -- ref -> Identity Service (customers.account_id), no cross-DB FK; copied from the order so payments can be searched by customer
    payment_method_id           UUID NOT NULL REFERENCES payment_methods(id),
    idempotency_key             VARCHAR(100),
    amount                      BIGINT NOT NULL CHECK (amount >= 0),
    paid_at                     TIMESTAMPTZ,
    provider_transaction_code   VARCHAR(100) UNIQUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by                  UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    updated_at                  TIMESTAMPTZ,
    updated_by                  UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    -- CANCELLED = pending payment cancelled because its order was cancelled;
    -- REFUNDED  = a PAID payment returned to the customer after its order was cancelled.
    status                      VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PAID', 'FAILED', 'CANCELLED', 'REFUNDED')),
    CHECK (status NOT IN ('PAID', 'REFUNDED') OR paid_at IS NOT NULL)
);
CREATE INDEX idx_payments_payment_method_id ON payments(payment_method_id);
CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_customer_id ON payments(customer_id);
-- Admin transaction search by date range, newest first.
CREATE INDEX idx_payments_created_at ON payments(created_at DESC, id DESC);
-- An order can be paid only once: unique among PAID payments, but retries/failed
-- attempts for the same order are allowed to co-exist as separate rows.
CREATE UNIQUE INDEX uk_payments_order_paid ON payments(order_id) WHERE status = 'PAID';
-- Protects against the saga's create-payment call being retried inserting a second PENDING row.
CREATE UNIQUE INDEX uk_payments_idempotency_key ON payments(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Outbox: reliable dispatch of Kafka events written atomically with a payment status change.
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    aggregate_type  VARCHAR(50) NOT NULL,
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    channel         VARCHAR(10) NOT NULL CHECK (channel IN ('KAFKA', 'RABBITMQ')),
    destination     VARCHAR(255) NOT NULL,
    payload         JSONB NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PUBLISHED', 'FAILED')),
    trace_context   VARCHAR(100), -- W3C traceparent captured at write time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at    TIMESTAMPTZ
);
-- The dispatcher only ever polls PENDING rows oldest-first; published rows stay out of the index.
CREATE INDEX idx_outbox_events_pending ON outbox_events(created_at) WHERE status = 'PENDING';

-- Inbox: dedup for at-least-once Kafka/RabbitMQ delivery.
CREATE TABLE inbox_events (
    event_id        UUID PRIMARY KEY,
    consumer_name   VARCHAR(100) NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed data
INSERT INTO payment_methods (code, name) VALUES
    ('COD', 'Cash on Delivery'),
    ('ONLINE_CARD', 'Online Card Payment');


-- =====================================================================================
-- ========================= PROMOTION SERVICE =========================================
-- =====================================================================================

CREATE TABLE discounts (
    id                  UUID PRIMARY KEY DEFAULT uuidv7(),
    code                VARCHAR(50),
    title               VARCHAR(255) NOT NULL,
    discount_type       VARCHAR(10) NOT NULL CHECK (discount_type IN ('PERCENT', 'FIXED')),
    value               INT NOT NULL,
    application_scope   VARCHAR(20) NOT NULL CHECK (application_scope IN ('ORDER', 'ALL_ITEMS', 'CATEGORY')),
    min_order_amount    BIGINT NOT NULL DEFAULT 0 CHECK (min_order_amount >= 0),
    start_at            TIMESTAMPTZ NOT NULL,
    end_at              TIMESTAMPTZ NOT NULL,
    description         TEXT,
    created_by          UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    updated_by          UUID, -- ref -> Identity Service (employees.account_id), no cross-DB FK
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ,
    -- Expiry is NOT stored: a discount is expired when end_at has passed, checked at query time.
    -- INACTIVE = manually locked/hidden by an employee.
    status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                            CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    CHECK (start_at < end_at),
    CHECK (
        (discount_type = 'PERCENT' AND value BETWEEN 1 AND 100)
        OR (discount_type = 'FIXED' AND value > 0)
    )
);
-- Unique only among non-deleted rows, so a soft-deleted discount's code can be reused.
CREATE UNIQUE INDEX discounts_normalized_code ON discounts (upper(code))
    WHERE code IS NOT NULL AND status <> 'DELETED';

CREATE TABLE discount_categories (
    discount_id UUID NOT NULL REFERENCES discounts(id),
    category_id UUID NOT NULL, -- ref -> Catalog Service (categories.id), no cross-DB FK
    PRIMARY KEY (discount_id, category_id)
);
-- The PK only serves lookups by discount; this one serves "discounts applying to a category".
CREATE INDEX idx_discount_categories_category_id ON discount_categories(category_id);

-- Business rule: ORDER/ALL_ITEMS discounts must have no category targets;
-- CATEGORY discounts must have at least one. Expressed as deferred constraint
-- triggers so the discount row and its targets can be written atomically in
-- one transaction, and re-checked if either side changes.
-- Only the discount touched by the changed row is checked, never the whole table.
CREATE OR REPLACE FUNCTION enforce_discount_scope_targets()
RETURNS TRIGGER AS $$
DECLARE
    target_discount_id  UUID;
    invalid_discount_id UUID;
BEGIN
    IF TG_TABLE_NAME = 'discounts' THEN
        target_discount_id := NEW.id;
    ELSIF TG_OP = 'DELETE' THEN
        target_discount_id := OLD.discount_id;
    ELSE
        target_discount_id := NEW.discount_id;
    END IF;

    SELECT d.id
    INTO invalid_discount_id
    FROM discounts d
    WHERE d.id = target_discount_id
      AND (
            (
                d.application_scope IN ('ORDER', 'ALL_ITEMS')
                AND EXISTS (SELECT 1 FROM discount_categories dc WHERE dc.discount_id = d.id)
            )
            OR (
                d.application_scope = 'CATEGORY'
                AND NOT EXISTS (SELECT 1 FROM discount_categories dc WHERE dc.discount_id = d.id)
            )
      );

    IF invalid_discount_id IS NOT NULL THEN
        RAISE EXCEPTION 'Discount % has targets inconsistent with application_scope', invalid_discount_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_discount_scope_targets
    AFTER INSERT OR UPDATE ON discounts
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION enforce_discount_scope_targets();

CREATE CONSTRAINT TRIGGER trg_discount_category_targets
    AFTER INSERT OR UPDATE OR DELETE ON discount_categories
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION enforce_discount_scope_targets();
