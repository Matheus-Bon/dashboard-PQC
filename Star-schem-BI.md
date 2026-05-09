┌─────────────────────────┐     ┌─────────────────────────┐
│     dim_algorithm        │     │      dim_operation       │
├─────────────────────────┤     ├─────────────────────────┤
│ sk_algorithm    PK  INT │     │ sk_operation   PK  INT  │
│ algorithm_name  VARCHAR │     │ operation_name VARCHAR   │
│ algorithm_family VARCHAR│     └────────────┬────────────┘
│ security_level  VARCHAR │                  │
└────────────┬────────────┘                  │
             │                               │
             │    ┌──────────────────────────────────────────┐
             │    │          fact_benchmark                   │
             │    ├──────────────────────────────────────────┤
             ├───►│ sk_benchmark       PK  BIGINT AUTO_INCR  │
             │    │ sk_algorithm       FK  INT               │
             │    │ sk_hardware        FK  INT               │◄───┐
             │    │ sk_operation       FK  INT               │    │
             │    │ payload_kb         DECIMAL(6,2)          │    │
             │    │ key_size_bytes     INT                   │    │
             │    │ execution_time_ms  DOUBLE                │    │
             │    │ memory_usage_mb    FLOAT                 │    │
             │    │ cpu_usage_percent  FLOAT                 │    │
             │    │ variation_pct      FLOAT  (nullable)     │    │
             │    │ overhead_pct       FLOAT  (nullable)     │    │
             │    └──────────────────────────────────────────┘    │
             │                                                    │
             │    ┌──────────────────────────┐                    │
             │    │      dim_hardware        │                    │
             │    ├──────────────────────────┤                    │
             │    │ sk_hardware    PK  INT   │────────────────────┘
             │    │ provider       VARCHAR   │
             │    │ cpu_model      VARCHAR   │
             │    │ vcpu           INT (null)│
             │    │ ram_gb      DECIMAL(5,2) │
             │    │ os             VARCHAR   │
             │    │ environment_type VARCHAR │
             │    └──────────────────────────┘