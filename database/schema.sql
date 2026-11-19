-- Simpar FinOps Control Tower - esquema relacional (PostgreSQL 14+)
-- Todas as tabelas de negocio chegam a "org" via dim_company: base para multi-tenancy (SaaS).

CREATE TABLE org (
    id          serial PRIMARY KEY,
    code        text UNIQUE NOT NULL,
    name        text NOT NULL
);

CREATE TABLE dim_company (
    id          serial PRIMARY KEY,
    org_id      int  NOT NULL REFERENCES org(id),
    code        text NOT NULL,
    name        text NOT NULL,
    segment     text,
    color       text,
    UNIQUE (org_id, code)
);

CREATE TABLE dim_cloud (
    code        text PRIMARY KEY,           -- aws | azure | oci | gcp | huawei
    name        text NOT NULL,
    color       text NOT NULL,
    cost_source text NOT NULL               -- fonte primaria de custo
);

CREATE TABLE cloud_account (
    id          serial PRIMARY KEY,
    company_id  int  NOT NULL REFERENCES dim_company(id),
    cloud_code  text NOT NULL REFERENCES dim_cloud(code),
    external_id text NOT NULL,              -- AWS account / Azure subscription / OCI tenancy+compartment / GCP project / Huawei domain
    name        text NOT NULL,
    env_scope   text,
    status      text NOT NULL DEFAULT 'active'
);

CREATE TABLE dim_product (
    id                  serial PRIMARY KEY,
    company_id          int  NOT NULL REFERENCES dim_company(id),
    code                text NOT NULL,
    name                text NOT NULL,
    owner               text,
    chargeback_enabled  boolean NOT NULL DEFAULT false,
    UNIQUE (company_id, code)
);

CREATE TABLE dim_application (
    id          serial PRIMARY KEY,
    company_id  int  NOT NULL REFERENCES dim_company(id),
    product_id  int  NOT NULL REFERENCES dim_product(id),
    code        text NOT NULL,
    name        text NOT NULL,
    criticality text,
    UNIQUE (company_id, code)
);

CREATE TABLE dim_cost_center (
    id          serial PRIMARY KEY,
    company_id  int  NOT NULL REFERENCES dim_company(id),
    code        text NOT NULL,
    name        text NOT NULL,
    UNIQUE (company_id, code)
);

CREATE TABLE tag_policy (
    id              serial PRIMARY KEY,
    org_id          int  NOT NULL REFERENCES org(id),
    tag_key         text NOT NULL,
    required        boolean NOT NULL DEFAULT true,
    allowed_values  jsonb,
    description     text
);

-- Inventario unificado de recursos (1 linha por recurso)
CREATE TABLE resource (
    id              bigserial PRIMARY KEY,
    account_id      int  NOT NULL REFERENCES cloud_account(id),
    company_id      int  NOT NULL REFERENCES dim_company(id),
    cloud_code      text NOT NULL REFERENCES dim_cloud(code),
    service         text NOT NULL,
    resource_type   text NOT NULL,
    resource_name   text NOT NULL,
    region          text,
    environment     text,                   -- valor da tag de ambiente (pode estar fora do padrao)
    owner           text,                   -- tag owner
    product_id      int  REFERENCES dim_product(id),
    application_id  int  REFERENCES dim_application(id),
    cost_center_id  int  REFERENCES dim_cost_center(id),
    tags            jsonb NOT NULL DEFAULT '{}',
    state           text,
    cpu_avg         numeric(5,2),
    arch            text,
    is_idle         boolean NOT NULL DEFAULT false,
    is_orphan       boolean NOT NULL DEFAULT false,
    is_optimized    boolean NOT NULL DEFAULT false,
    naming_ok       boolean NOT NULL DEFAULT true,
    created_at      date,
    retired_at      date
);
CREATE INDEX ix_resource_company ON resource(company_id);
CREATE INDEX ix_resource_cloud   ON resource(cloud_code);
CREATE INDEX ix_resource_product ON resource(product_id);
CREATE INDEX ix_resource_app     ON resource(application_id);

-- Fato de custo: recurso x mes (BRL)
CREATE TABLE cost_monthly (
    resource_id bigint NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
    month       date   NOT NULL,
    cost_brl    numeric(14,2) NOT NULL,
    usage_qty   numeric(18,4),
    usage_unit  text,
    PRIMARY KEY (resource_id, month)
);
CREATE INDEX ix_cost_month ON cost_monthly(month);

-- Custos compartilhados (rede, suporte, observabilidade...) e regras de rateio
CREATE TABLE shared_pool (
    id          serial PRIMARY KEY,
    company_id  int  NOT NULL REFERENCES dim_company(id),   -- empresa hospedeira
    code        text NOT NULL,
    name        text NOT NULL,
    cloud_code  text REFERENCES dim_cloud(code),
    description text
);
CREATE TABLE shared_cost_monthly (
    pool_id     int  NOT NULL REFERENCES shared_pool(id) ON DELETE CASCADE,
    month       date NOT NULL,
    cost_brl    numeric(14,2) NOT NULL,
    PRIMARY KEY (pool_id, month)
);
CREATE TABLE allocation_rule (
    pool_id     int PRIMARY KEY REFERENCES shared_pool(id) ON DELETE CASCADE,
    method      text NOT NULL CHECK (method IN ('proportional','even','fixed')),
    weights     jsonb NOT NULL DEFAULT '{}',                -- usado em 'fixed': {"movida":0.4,...}
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE budget (
    company_id  int  NOT NULL REFERENCES dim_company(id),
    month       date NOT NULL,
    amount_brl  numeric(14,2) NOT NULL,
    PRIMARY KEY (company_id, month)
);

CREATE TABLE commitment (
    id              serial PRIMARY KEY,
    company_id      int  NOT NULL REFERENCES dim_company(id),
    account_id      int  REFERENCES cloud_account(id),
    cloud_code      text NOT NULL REFERENCES dim_cloud(code),
    kind            text NOT NULL,         -- Savings Plan | Reserved Instance | Azure Reservation | OCI Annual Flex | GCP CUD | Huawei Yearly/Monthly
    term_months     int  NOT NULL,
    monthly_commit_brl numeric(14,2) NOT NULL,
    coverage_pct    numeric(5,2) NOT NULL,
    utilization_pct numeric(5,2) NOT NULL,
    expires_on      date
);

CREATE TABLE opportunity (
    id                  bigserial PRIMARY KEY,
    company_id          int  NOT NULL REFERENCES dim_company(id),
    cloud_code          text NOT NULL REFERENCES dim_cloud(code),
    account_id          int  REFERENCES cloud_account(id),
    resource_id         bigint REFERENCES resource(id) ON DELETE SET NULL,
    opp_type            text NOT NULL,
    title               text NOT NULL,
    description         text,
    current_cost_brl    numeric(14,2) NOT NULL,   -- custo mensal enderecavel
    savings_monthly_brl numeric(14,2) NOT NULL,
    savings_pct         numeric(5,2)  NOT NULL,
    effort              text NOT NULL CHECK (effort IN ('Baixo','Médio','Alto')),
    term_days           int  NOT NULL,
    risk                text NOT NULL CHECK (risk IN ('Baixo','Médio','Alto')),
    priority_score      numeric(6,2) NOT NULL,
    status              text NOT NULL DEFAULT 'Identificada',
    owner               text,
    captured_month      date,
    created_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_opp_company ON opportunity(company_id);
CREATE INDEX ix_opp_type    ON opportunity(opp_type);

CREATE TABLE savings_captured (
    month       date NOT NULL,
    opportunity_id bigint NOT NULL REFERENCES opportunity(id) ON DELETE CASCADE,
    company_id  int  NOT NULL REFERENCES dim_company(id),
    cloud_code  text NOT NULL REFERENCES dim_cloud(code),
    opp_type    text NOT NULL,
    amount_brl  numeric(14,2) NOT NULL,
    PRIMARY KEY (month, opportunity_id)
);

-- Conectores: metadados nao sensiveis em config; segredo criptografado (Fernet) em secret_enc
CREATE TABLE cloud_connection (
    id            serial PRIMARY KEY,
    company_id    int  NOT NULL REFERENCES dim_company(id),
    cloud_code    text NOT NULL REFERENCES dim_cloud(code),
    display_name  text NOT NULL,
    auth_type     text NOT NULL,
    config        jsonb NOT NULL DEFAULT '{}',
    secret_enc    text,
    mode          text NOT NULL DEFAULT 'demo' CHECK (mode IN ('demo','live')),
    status        text NOT NULL DEFAULT 'pending',
    sync_enabled  boolean NOT NULL DEFAULT true,
    last_sync_at  timestamptz,
    last_message  text,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE etl_run (
    id             bigserial PRIMARY KEY,
    connection_id  int REFERENCES cloud_connection(id) ON DELETE CASCADE,
    started_at     timestamptz NOT NULL DEFAULT now(),
    finished_at    timestamptz,
    status         text NOT NULL,
    rows_cost      int DEFAULT 0,
    rows_resources int DEFAULT 0,
    rows_recs      int DEFAULT 0,
    message        text
);
