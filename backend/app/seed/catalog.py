"""Catalogo da base de DEMONSTRACAO.

ATENCAO: todos os valores, produtos, aplicacoes, equipes e distribuicoes abaixo sao FICTICIOS,
criados apenas para demonstracao do produto. Nao representam dados reais do Grupo Simpar.
"""

CLOUDS = [
    ("aws", "AWS", "#F59E0B", "AWS Cost Explorer (primaria) + CUR"),
    ("azure", "Azure", "#2563EB", "Azure Cost Management API"),
    ("oci", "OCI", "#E11D48", "OCI Usage API / Cost Reports"),
    ("gcp", "Google Cloud", "#0E9F8E", "Cloud Billing export (BigQuery)"),
    ("huawei", "Huawei Cloud", "#7C3AED", "Huawei BSS (Billing) API"),
]

# code, nome, segmento, cor, share do gasto do grupo, crescimento mensal medio, vies de budget, cobertura de tags alvo, mix de cloud
COMPANIES = [
    ("simpar", "Simpar", "Holding", "#4F46E5", 0.11, 0.006, 0.02, 0.58,
     {"oci": 0.50, "aws": 0.16, "azure": 0.20, "gcp": 0.07, "huawei": 0.07}),
    ("movida", "Movida", "Locação de veículos", "#0E9F8E", 0.33, 0.012, -0.02, 0.84,
     {"gcp": 0.60, "aws": 0.32, "azure": 0.08}),
    ("jsl", "JSL", "Logística", "#2563EB", 0.22, 0.008, 0.012, 0.70,
     {"oci": 0.46, "azure": 0.40, "aws": 0.06, "huawei": 0.08}),
    ("vamos", "Vamos", "Locação de caminhões", "#F59E0B", 0.15, 0.008, 0.012, 0.63,
     {"oci": 0.45, "azure": 0.47, "aws": 0.04, "huawei": 0.04}),
    ("automob", "Automob", "Varejo automotivo", "#E11D48", 0.08, 0.010, -0.025, 0.50,
     {"oci": 0.50, "azure": 0.50}),
    ("csinfra", "CSInfra", "Infraestrutura", "#7C3AED", 0.06, 0.004, 0.03, 0.42,
     {"aws": 0.35, "azure": 0.55, "oci": 0.10}),
    ("csbrasil", "CSBrasil", "Mobilidade e concessões", "#64748B", 0.05, 0.007, 0.0, 0.36,
     {"azure": 0.45, "oci": 0.30, "huawei": 0.15, "aws": 0.10}),
]

# produtos: (code, nome, owner, chargeback_enabled, [(app code, app nome, criticidade, peso)])
PRODUCTS = {
    "simpar": [
        ("plataforma-corp", "Plataforma Corporativa", "Squad Plataforma Corporativa", True, [
            ("erp-corp", "ERP Corporativo", "A+", 5), ("portal-colab", "Portal do Colaborador", "B", 1),
            ("tesouraria", "Tesouraria", "A", 2), ("fiscal", "Motor Fiscal", "A", 2)]),
        ("dados-analytics", "Dados & Analytics", "Squad Dados e Analytics", False, [
            ("datalake", "Data Lake Corporativo", "A", 5), ("bi-corp", "BI Corporativo", "B", 2),
            ("mlops", "Plataforma MLOps", "C", 1)]),
        ("seguranca-corp", "Segurança Corporativa", "Squad Segurança", False, [
            ("siem", "SIEM Corporativo", "A+", 2), ("iam", "Gestão de Identidades", "A+", 1)]),
    ],
    "movida": [
        ("locacao-digital", "Locação Digital", "Squad Locação", True, [
            ("app-movida", "App Movida", "A+", 5), ("site-movida", "Site Movida", "A", 3),
            ("motor-precos", "Motor de Preços", "A", 3), ("reservas-api", "API de Reservas", "A+", 4)]),
        ("gestao-frotas", "Gestão de Frotas", "Squad Frotas", True, [
            ("telemetria", "Telemetria de Frota", "A", 6), ("manutencao", "Gestão de Manutenção", "B", 2),
            ("roteirizacao", "Roteirização", "B", 2)]),
        ("seminovos", "Seminovos", "Squad Seminovos", True, [
            ("portal-seminovos", "Portal Seminovos", "A", 3), ("precificacao-sn", "Precificação Seminovos", "B", 2),
            ("crm-sn", "CRM Seminovos", "C", 1)]),
        ("pagamentos", "Pagamentos", "Squad Pagamentos", False, [
            ("gateway", "Gateway de Pagamentos", "A+", 3), ("antifraude", "Antifraude", "A+", 2)]),
    ],
    "jsl": [
        ("logistica-dedicada", "Logística Dedicada", "Squad Logística", True, [
            ("tms-jsl", "TMS JSL", "A+", 6), ("torre-controle", "Torre de Controle", "A", 3),
            ("roteirizacao-jsl", "Roteirização JSL", "B", 2)]),
        ("armazenagem", "Armazenagem", "Squad Armazéns", True, [
            ("wms", "WMS", "A", 4), ("estoque", "Gestão de Estoque", "B", 2)]),
        ("transporte-rodoviario", "Transporte Rodoviário", "Squad Transporte", False, [
            ("gestao-cargas", "Gestão de Cargas", "A", 4), ("rastreamento", "Rastreamento", "A", 3)]),
        ("plataforma-comercial", "Plataforma Comercial", "Squad Comercial", False, [
            ("cotacao", "Cotação Online", "B", 2), ("crm-jsl", "CRM JSL", "C", 1)]),
    ],
    "vamos": [
        ("locacao-caminhoes", "Locação de Caminhões", "Squad Locação Vamos", True, [
            ("portal-vamos", "Portal Vamos", "A", 3), ("contratos", "Contratos de Locação", "A+", 4),
            ("telemetria-vamos", "Telemetria Vamos", "A", 4)]),
        ("seminovos-vamos", "Seminovos Vamos", "Squad Seminovos Vamos", True, [
            ("portal-sn-vamos", "Portal Seminovos Vamos", "B", 2), ("avaliacao", "Avaliação de Ativos", "B", 2)]),
        ("manutencao-pv", "Manutenção e Pós-venda", "Squad Pós-venda", False, [
            ("oficinas", "Gestão de Oficinas", "A", 3), ("pecas", "Gestão de Peças", "B", 2)]),
    ],
    "automob": [
        ("revenda-digital", "Revenda Digital", "Squad Revenda", True, [
            ("marketplace", "Marketplace Automob", "A", 4), ("avaliacao-veic", "Avaliação de Veículos", "B", 2)]),
        ("financiamento", "Financiamento", "Squad Crédito", False, [
            ("motor-credito", "Motor de Crédito", "A+", 4), ("originacao", "Originação", "A", 2)]),
        ("pos-venda-auto", "Pós-venda", "Squad Pós-venda Auto", False, [
            ("agendamento", "Agendamento", "B", 2), ("garantia", "Garantia Estendida", "C", 1)]),
    ],
    "csinfra": [
        ("gestao-obras", "Gestão de Obras", "Squad Obras", True, [
            ("gestao-contratos", "Gestão de Contratos", "A", 3), ("bim-cloud", "BIM Cloud", "B", 3)]),
        ("portos-terminais", "Portos e Terminais", "Squad Terminais", False, [
            ("tos", "TOS", "A+", 4), ("gate-auto", "Gate Automation", "A", 2)]),
        ("operacao-concessoes", "Operação de Concessões", "Squad Concessões", False, [
            ("monitoramento", "Monitoramento Operacional", "A", 3), ("telemetria-viaria", "Telemetria Viária", "B", 2)]),
    ],
    "csbrasil": [
        ("mobilidade-urbana", "Mobilidade Urbana", "Squad Mobilidade", False, [
            ("bilhetagem", "Bilhetagem", "A+", 4), ("operacao-frota", "Operação de Frota", "A", 3)]),
        ("servicos-compartilhados", "Serviços Compartilhados", "Squad Serviços", False, [
            ("erp-cs", "ERP CS", "A", 3), ("fiscal-cs", "Fiscal CS", "B", 1)]),
    ],
}

COST_CENTERS = [("1001", "Tecnologia"), ("1002", "Operações"), ("1003", "Comercial"),
                ("1004", "Financeiro"), ("1005", "Dados e Analytics"), ("1006", "Segurança")]

# servico -> (categoria, custo tipico mensal por recurso, tipo de recurso, sigma lognormal)
CATEGORIES = {
    "compute": ["EC2", "Virtual Machines", "Compute", "Compute Engine", "ECS"],
    "db": ["RDS", "SQL Database", "Exadata Database Service", "Autonomous Database", "Database System",
           "Cloud SQL", "DynamoDB", "Cosmos DB", "ElastiCache", "Azure Cache for Redis"],
    "k8s": ["EKS", "AKS", "OKE", "GKE", "CCE"],
    "block": ["EBS", "Managed Disks", "Block Volume", "Persistent Disk", "EVS"],
    "object": ["S3", "Storage Account", "Object Storage", "Cloud Storage", "OBS"],
    "logs": ["CloudWatch", "Log Analytics", "Logging", "Cloud Logging", "LTS"],
}
SERVICE_CAT = {s: c for c, lst in CATEGORIES.items() for s in lst}

SERVICES = {
    "aws": [("EC2", .30, 1100, "instance"), ("RDS", .15, 3200, "db-instance"), ("S3", .09, 900, "bucket"),
            ("EKS", .08, 7000, "cluster"), ("EBS", .08, 180, "volume"), ("Lambda", .04, 500, "function"),
            ("CloudWatch", .05, 700, "log-group"), ("DynamoDB", .04, 900, "table"),
            ("Data Transfer", .06, 3500, "network"), ("ElastiCache", .03, 1800, "cache-cluster"),
            ("Elastic Load Balancing", .03, 600, "load-balancer"), ("Outros", .05, 800, "misc")],
    "azure": [("Virtual Machines", .30, 1300, "vm"), ("SQL Database", .14, 3500, "sql-db"),
              ("Storage Account", .10, 1000, "storage-account"), ("AKS", .10, 6500, "cluster"),
              ("App Service", .08, 1200, "app-service"), ("Managed Disks", .06, 200, "disk"),
              ("Log Analytics", .06, 900, "workspace"), ("Cosmos DB", .04, 2500, "cosmos-db"),
              ("Bandwidth", .05, 3000, "network"), ("Azure Cache for Redis", .02, 1500, "redis"),
              ("Load Balancer", .02, 500, "load-balancer"), ("Outros", .03, 800, "misc")],
    "oci": [("Compute", .22, 1500, "instance"), ("Exadata Database Service", .30, 65000, "exadata-infra"),
            ("Autonomous Database", .08, 9000, "adb"), ("Database System", .08, 6000, "db-system"),
            ("Object Storage", .06, 900, "bucket"), ("Block Volume", .08, 220, "volume"),
            ("OKE", .04, 6000, "cluster"), ("Logging", .03, 500, "log-group"),
            ("Networking", .06, 3000, "network"), ("Load Balancer", .03, 600, "load-balancer"),
            ("Outros", .02, 800, "misc")],
    "gcp": [("Compute Engine", .26, 1400, "instance"), ("BigQuery", .18, 6000, "dataset"),
            ("Cloud SQL", .12, 3000, "sql-instance"), ("GKE", .12, 7500, "cluster"),
            ("Cloud Storage", .08, 1000, "bucket"), ("Persistent Disk", .06, 190, "disk"),
            ("Dataflow", .05, 3500, "job"), ("Cloud Logging", .04, 800, "log-bucket"),
            ("Networking", .06, 3200, "network"), ("Pub/Sub", .03, 700, "topic")],
    "huawei": [("ECS", .35, 1000, "ecs-instance"), ("RDS", .20, 2500, "rds-instance"), ("OBS", .15, 800, "bucket"),
               ("CCE", .10, 5000, "cluster"), ("EVS", .10, 170, "volume"), ("ELB", .05, 500, "load-balancer"),
               ("LTS", .05, 500, "log-group")],
}

REGIONS = {
    "aws": ["sa-east-1", "us-east-1", "us-east-2"],
    "azure": ["brazilsouth", "eastus2", "brazilsoutheast"],
    "oci": ["sa-saopaulo-1", "sa-vinhedo-1", "us-ashburn-1"],
    "gcp": ["southamerica-east1", "us-central1", "us-east1"],
    "huawei": ["sa-brazil-1", "la-south-2"],
}
REGION_W = [0.82, 0.12, 0.06]

# tipos de oportunidade: (codigo, nome, esforco, prazo dias, risco, descricao curta)
OPP_TYPES = [
    ("rightsizing", "Rightsizing", "Médio", 30, "Médio", "Ajustar tamanho de instâncias/bancos subutilizados"),
    ("savings_plans", "Savings Plans / Compromissos de Compute", "Baixo", 15, "Médio", "Elevar cobertura de compute com compromissos"),
    ("reserved_instances", "Reserved Instances / Reservas", "Baixo", 15, "Médio", "Reservas para bancos e serviços de uso estável"),
    ("graviton", "Graviton / ARM", "Alto", 90, "Médio", "Migrar para arquitetura ARM de melhor custo-benefício"),
    ("storage_tiering", "Storage Tiering", "Baixo", 20, "Baixo", "Mover dados frios para classes de armazenamento mais baratas"),
    ("orphan_resources", "Recursos órfãos", "Baixo", 7, "Baixo", "Volumes, IPs, snapshots e balanceadores sem vínculo"),
    ("idle_resources", "Recursos sem uso", "Baixo", 10, "Médio", "Recursos ligados sem utilização relevante"),
    ("off_hours", "Desligamento fora do expediente", "Baixo", 15, "Baixo", "Agendar desligamento de ambientes não produtivos"),
    ("log_retention", "Retenção de logs", "Baixo", 10, "Médio", "Reduzir retenção e volume de logs de baixo valor"),
    ("modernization", "Modernização", "Alto", 180, "Alto", "Refatorar para serviços gerenciados, containers ou serverless"),
]
OPP_TYPE_NAME = {t[0]: t[1] for t in OPP_TYPES}

COMMITMENT_KINDS = {
    "aws": [("Savings Plan (Compute)", 36), ("Reserved Instance (RDS)", 12)],
    "azure": [("Azure Reservation (VM)", 36), ("Azure Savings Plan", 12)],
    "oci": [("OCI Annual Flex / Universal Credits", 12), ("OCI Annual Commit", 36)],
    "gcp": [("GCP Committed Use Discount", 36), ("GCP Flex CUD", 12)],
    "huawei": [("Huawei Pacote Anual", 12), ("Huawei Assinatura Mensal", 1)],
}

SHARED_POOLS = [
    ("rede", "Rede Corporativa e Conectividade", "Interconexões dedicadas, VPN e transit entre clouds", 0.30),
    ("suporte", "Suporte Enterprise dos Provedores", "Planos de suporte AWS, Azure, OCI, GCP e Huawei", 0.26),
    ("observabilidade", "Observabilidade e Logs Corporativos", "Plataforma central de logs, métricas e traces", 0.18),
    ("seguranca", "Segurança e Identidade", "SIEM, IAM e proteção de workloads", 0.14),
    ("plataforma", "Plataforma Compartilhada (CI/CD e Kubernetes)", "Clusters e pipelines compartilhados", 0.12),
]
SHARED_SHARE_OF_TOTAL = 0.055
TOTAL_REF_MONTH = 3_300_000.0   # gasto total mensal (BRL) do grupo no mes de referencia - FICTICIO
