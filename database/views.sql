-- Camada semantica: todas as consultas analiticas da API passam por estas views.
-- "fully_tagged": possui owner, produto, aplicacao, centro de custo e ambiente.
-- "std_ok": nomenclatura valida e ambiente dentro dos valores permitidos (prod|hml|dev).

CREATE OR REPLACE VIEW v_resource AS
SELECT r.id AS resource_id, co.org_id, r.company_id, co.code AS company_code, co.name AS company_name,
       r.cloud_code, a.id AS account_id, a.name AS account_name, a.external_id AS account_external_id,
       r.service, r.resource_type, r.resource_name, r.region, r.environment, r.owner,
       r.product_id, p.name AS product_name, COALESCE(p.chargeback_enabled, false) AS chargeback_enabled,
       r.application_id, ap.name AS application_name,
       r.cost_center_id, cc.code AS cost_center_code, cc.name AS cost_center_name,
       CASE WHEN r.environment IS NULL THEN NULL
            WHEN lower(r.environment) IN ('prod','production','producao','prd') THEN 'prod'
            WHEN lower(r.environment) IN ('hml','homolog','staging') THEN 'hml'
            WHEN lower(r.environment) IN ('dev','development','desenvolvimento') THEN 'dev'
            ELSE 'outro' END AS env_norm,
       r.tags, r.state, r.cpu_avg, r.arch, r.is_idle, r.is_orphan, r.is_optimized,
       (r.owner IS NOT NULL AND r.product_id IS NOT NULL AND r.application_id IS NOT NULL
        AND r.cost_center_id IS NOT NULL AND r.environment IS NOT NULL) AS fully_tagged,
       (r.naming_ok AND r.environment IN ('prod','hml','dev')) AS std_ok,
       r.created_at, r.retired_at
FROM resource r
JOIN dim_company co ON co.id = r.company_id
JOIN cloud_account a ON a.id = r.account_id
LEFT JOIN dim_product p ON p.id = r.product_id
LEFT JOIN dim_application ap ON ap.id = r.application_id
LEFT JOIN dim_cost_center cc ON cc.id = r.cost_center_id;

CREATE OR REPLACE VIEW v_cost AS
SELECT cm.month, cm.cost_brl, cm.usage_qty, cm.usage_unit, v.*
FROM cost_monthly cm
JOIN v_resource v ON v.resource_id = cm.resource_id;

CREATE OR REPLACE VIEW v_shared_cost AS
SELECT sc.month, sc.cost_brl, sp.id AS pool_id, sp.code AS pool_code, sp.name AS pool_name,
       sp.cloud_code, sp.company_id, co.code AS company_code, co.org_id,
       COALESCE(ar.method, 'proportional') AS method, COALESCE(ar.weights, '{}'::jsonb) AS weights
FROM shared_cost_monthly sc
JOIN shared_pool sp ON sp.id = sc.pool_id
JOIN dim_company co ON co.id = sp.company_id
LEFT JOIN allocation_rule ar ON ar.pool_id = sp.id;

CREATE OR REPLACE VIEW v_opportunity AS
SELECT o.*, co.code AS company_code, co.name AS company_name, co.org_id,
       cl.name AS cloud_name, r.resource_name, r.service
FROM opportunity o
JOIN dim_company co ON co.id = o.company_id
JOIN dim_cloud cl ON cl.code = o.cloud_code
LEFT JOIN resource r ON r.id = o.resource_id;
