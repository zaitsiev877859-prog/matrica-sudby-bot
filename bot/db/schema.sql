-- Схема БД каркаса бота «Матрица судьбы».
-- Прямое отображение сущностей ДН-01..ДН-13 из 04c-bot-structure-fixed.md.
-- Идемпотентно (CREATE ... IF NOT EXISTS), выполняется при старте бота.

CREATE TABLE IF NOT EXISTS specialists ( -- ДН-01
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    display_name TEXT,
    alias TEXT,
    contact_type TEXT,
    contact_value TEXT,
    language TEXT NOT NULL DEFAULT 'ru',
    status TEXT NOT NULL DEFAULT 'profile_incomplete', -- СТ-01
    first_paid_at TIMESTAMPTZ,
    profile_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS client_operations ( -- ДН-02
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialist_id UUID NOT NULL REFERENCES specialists(id),
    comment TEXT,
    status TEXT NOT NULL DEFAULT 'draft', -- СТ-05
    retain_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS input_datasets ( -- ДН-09
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID NOT NULL REFERENCES client_operations(id),
    specialist_id UUID NOT NULL REFERENCES specialists(id),
    core_type TEXT NOT NULL, -- core_personal / core_compatibility / core_forecast (ЯД-01..03)
    version INT NOT NULL DEFAULT 1,
    previous_version_id UUID REFERENCES input_datasets(id),
    birth_date_1 DATE,
    birth_date_2 DATE,
    label_1 TEXT,
    label_2 TEXT,
    is_child BOOLEAN NOT NULL DEFAULT false,
    forecast_year INT,
    status TEXT NOT NULL DEFAULT 'draft', -- СТ-12: draft / confirmed / superseded
    fingerprint TEXT,
    confirmed_at TIMESTAMPTZ,
    confirmed_by TEXT,
    retain_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS calculations ( -- ДН-03
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID NOT NULL REFERENCES client_operations(id),
    input_dataset_id UUID NOT NULL REFERENCES input_datasets(id),
    core_type TEXT NOT NULL,
    method_version TEXT,
    fingerprint TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    result_ref TEXT,
    error_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS reports ( -- ДН-04
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID NOT NULL REFERENCES client_operations(id),
    calculation_id UUID REFERENCES calculations(id),
    report_type TEXT NOT NULL, -- ОТ-01..ОТ-13
    position INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft', -- СТ-06
    library_version TEXT,
    input_version_id UUID REFERENCES input_datasets(id),
    comment_version INT,
    reservation_id UUID,
    redemption_id UUID,
    error_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (operation_id, position)
);

CREATE TABLE IF NOT EXISTS files ( -- ДН-05
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id),
    status TEXT NOT NULL DEFAULT 'building', -- СТ-07
    storage_ref TEXT,
    checksum TEXT,
    size_bytes BIGINT,
    pages INT,
    template_version TEXT,
    build_version TEXT,
    publish_kind TEXT, -- primary / restore (СОБ-52 / СОБ-52b)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    available_until TIMESTAMPTZ,
    last_downloaded_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS payments ( -- ДН-06
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialist_id UUID NOT NULL REFERENCES specialists(id),
    tariff TEXT NOT NULL, -- single / pack10 / unlimited30
    amount_kzt INT NOT NULL,
    provider_payment_id TEXT,
    idempotency_key TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'created', -- СТ-02
    receipt_file_ref TEXT,
    receipt_parsed_amount INT,
    receipt_parsed_status TEXT,
    needs_admin_review BOOLEAN NOT NULL DEFAULT false,
    start_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    refunded_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS rights_balances ( -- ДН-07
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialist_id UUID NOT NULL REFERENCES specialists(id),
    right_type TEXT NOT NULL, -- demo / single / pack10 / unlimited30
    payment_id UUID REFERENCES payments(id),
    granted_units INT,
    reserved_units INT NOT NULL DEFAULT 0,
    redeemed_units INT NOT NULL DEFAULT 0,
    expired_units INT NOT NULL DEFAULT 0,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active', -- СТ-03 (без 'Зарезервировано' на партии, см. 04c п.2)
    source TEXT NOT NULL,
    origin_right_id UUID REFERENCES rights_balances(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rights_ledger ( -- ДН-08
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    right_id UUID NOT NULL REFERENCES rights_balances(id),
    report_id UUID REFERENCES reports(id),
    entry_type TEXT NOT NULL, -- grant / reserve / release / redeem / expire / restore / adjust
    units INT NOT NULL DEFAULT 1,
    idempotency_key TEXT UNIQUE,
    reservation_state TEXT, -- СТ-11: active / redeemed / released / expired
    reservation_source_right_id UUID REFERENCES rights_balances(id),
    ttl_expires_at TIMESTAMPTZ,
    attempt_id TEXT,
    ttl_extended_at TIMESTAMPTZ,
    reason TEXT,
    initiator_type TEXT,
    initiator_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS errors ( -- ДН-10
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID,
    report_id UUID,
    file_id UUID,
    payment_id UUID,
    error_type TEXT,
    error_code TEXT,
    status TEXT NOT NULL DEFAULT 'new', -- СТ-08
    retryable BOOLEAN NOT NULL DEFAULT true,
    attempts INT NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    user_message TEXT,
    technical_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS support_tickets ( -- ДН-11
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialist_id UUID NOT NULL REFERENCES specialists(id),
    category TEXT,
    message TEXT,
    status TEXT NOT NULL DEFAULT 'new', -- СТ-09
    operation_id UUID,
    payment_id UUID,
    error_id UUID,
    channel TEXT NOT NULL DEFAULT 'telegram',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS admin_log ( -- ДН-12
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id BIGINT NOT NULL,
    action_type TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    reason TEXT,
    before_state JSONB,
    after_state JSONB,
    ticket_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admin_permissions ( -- ДН-13
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES support_tickets(id),
    admin_id BIGINT NOT NULL,
    purpose TEXT NOT NULL,
    scope_type TEXT,
    scope_id UUID,
    allowed_fields TEXT[],
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'created', -- СТ-10
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revoke_reason TEXT,
    idempotency_key TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_client_operations_specialist ON client_operations(specialist_id);
CREATE INDEX IF NOT EXISTS idx_input_datasets_operation ON input_datasets(operation_id);
CREATE INDEX IF NOT EXISTS idx_reports_operation ON reports(operation_id);
CREATE INDEX IF NOT EXISTS idx_rights_balances_specialist ON rights_balances(specialist_id);
CREATE INDEX IF NOT EXISTS idx_rights_ledger_right ON rights_ledger(right_id);
CREATE INDEX IF NOT EXISTS idx_payments_specialist ON payments(specialist_id);
