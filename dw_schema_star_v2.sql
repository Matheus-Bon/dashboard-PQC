-- ================================================================
-- Star Schema — PQC Benchmark DW (v2)
-- 3 Dimensões + 1 Fato | 4 Tabelas | 2.277 Registros
-- ================================================================

CREATE DATABASE IF NOT EXISTS pqc_benchmark_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE pqc_benchmark_dw;

-- ================================================================
-- DIM_ALGORITHM
-- 23 registros (classic / pqc / hybrid)
-- ================================================================
CREATE TABLE IF NOT EXISTS dim_algorithm (
  sk_algorithm     INT          NOT NULL AUTO_INCREMENT,
  algorithm_name   VARCHAR(255) NOT NULL,
  algorithm_family VARCHAR(255),
  security_level   VARCHAR(50),
  PRIMARY KEY (sk_algorithm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 23 registros reais: classic (2) + pqc (12) + hybrid (9)
INSERT INTO dim_algorithm (sk_algorithm, algorithm_name, algorithm_family, security_level) VALUES
--  Clássicos
( 1, 'ECDSA-P256',            'ECC',            'Classico'),
( 2, 'RSA-2048',              'RSA',            'Classico'),
--  PQC — ML-DSA
( 3, 'ML-DSA-44',             'ML-DSA',         'L3'),
( 4, 'ML-DSA-65',             'ML-DSA',         'L3'),
( 5, 'ML-DSA-87',             'ML-DSA',         'L5'),
--  PQC — ML-KEM
( 6, 'ML-KEM-1024',           'ML-KEM',         'L5'),
( 7, 'ML-KEM-512',            'ML-KEM',         'L1'),
( 8, 'ML-KEM-768',            'ML-KEM',         'L3'),
--  PQC — SLH-DSA SHA2
( 9, 'SLH-DSA-SHA2-128s',     'SLH-DSA',        'L1'),
(10, 'SLH-DSA-SHA2-192s',     'SLH-DSA',        'L3'),
(11, 'SLH-DSA-SHA2-256s',     'SLH-DSA',        'L5'),
--  PQC — SLH-DSA SHAKE
(12, 'SLH-DSA-SHAKE-128s',    'SLH-DSA',        'L1'),
(13, 'SLH-DSA-SHAKE-192s',    'SLH-DSA',        'L3'),
(14, 'SLH-DSA-SHAKE-256s',    'SLH-DSA',        'L5'),
--  Híbridos P256 + ML-DSA
(15, 'P256+ML-DSA-44',        'P256+ML-DSA',    'Classico'),
(16, 'P256+ML-DSA-65',        'P256+ML-DSA',    'Classico'),
(17, 'P256+ML-DSA-87',        'P256+ML-DSA',    'Classico'),
--  Híbridos P256 + ML-KEM
(18, 'P256+ML-KEM-1024',      'P256+ML-KEM',    'Classico'),
(19, 'P256+ML-KEM-512',       'P256+ML-KEM',    'Classico'),
(20, 'P256+ML-KEM-768',       'P256+ML-KEM',    'Classico'),
--  Híbridos RSA2048 + ML-DSA
(21, 'RSA2048+ML-DSA-44',     'RSA2048+ML-DSA', 'L2'),
(22, 'RSA2048+ML-DSA-65',     'RSA2048+ML-DSA', 'L3'),
(23, 'RSA2048+ML-DSA-87',     'RSA2048+ML-DSA', 'L5');


-- ================================================================
-- DIM_OPERATION
-- 7 registros (keygen, sign, verify, ...)
-- ================================================================
CREATE TABLE IF NOT EXISTS dim_operation (
  sk_operation   INT          NOT NULL AUTO_INCREMENT,
  operation_name VARCHAR(255) NOT NULL,
  PRIMARY KEY (sk_operation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7 operações reais do dataset
INSERT INTO dim_operation (sk_operation, operation_name) VALUES
(1, 'keygen'),
(2, 'sign'),
(3, 'verify'),
(4, 'decrypt'),
(5, 'encrypt'),
(6, 'decap'),
(7, 'encap');


-- ================================================================
-- DIM_HARDWARE
-- 11 registros (7 local + 4 cloud)
-- ================================================================
CREATE TABLE IF NOT EXISTS dim_hardware (
  sk_hardware      INT          NOT NULL AUTO_INCREMENT,
  provider         VARCHAR(100),
  cpu_model        VARCHAR(255),
  vcpu             INT,                     -- nullable
  ram_gb           DECIMAL(5,2),
  os               VARCHAR(100),
  environment_type VARCHAR(50),
  PRIMARY KEY (sk_hardware)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dim_hardware (sk_hardware, provider, cpu_model, vcpu, ram_gb, os, environment_type) VALUES
--  7 locais (vcpu NULL — bare-metal / notebook)
( 1, 'Local',                   'Apple M2',                      NULL, 16.00, 'MacOS',               'local'),
( 2, 'Local',                   'Ryzen7 5825U',                  NULL, 32.00, 'Ubuntu',              'local'),
( 3, 'Local',                   'Ryzen5 5600X',                  NULL, 32.00, 'Windows11',           'local'),
( 4, 'Local',                   'Ryzen9 7900',                   NULL, 32.00, 'Windows11',           'local'),
( 5, 'Local',                   'i5 11300H',                     NULL, 12.00, 'Windows11',           'local'),
( 6, 'Local',                   'i5 1235U',                      NULL, 32.00, 'Windows11',           'local'),
( 7, 'Local',                   'i7 13700F',                     NULL, 32.00, 'Windows11',           'local'),
--  4 cloud (vcpu 2)
( 8, 'AWS EC2',                 'Intel Xeon Platinum 8259CL',       2,  1.00, 'Amazon Linux 2023',  'cloud'),
( 9, 'Azure',                   'Intel Xeon Platinum 8370C',        2,  7.80, 'Linux Ubuntu/Debian', 'cloud'),
(10, 'Hostinger VPS',           'AMD EPYC 9354P',                   2,  8.00, 'Ubuntu 24.04',        'cloud'),
(11, 'Google Cloud Platform',   'Intel Xeon 2.20GHz',               2,  0.97, 'Debian 12',           'cloud');


-- ================================================================
-- FACT_BENCHMARK
-- ~2.277 registros: 11 hw × 23 alg × 9 ops (parcial por tipo)
-- ================================================================
CREATE TABLE IF NOT EXISTS fact_benchmark (
  sk_benchmark         BIGINT      NOT NULL AUTO_INCREMENT,

  -- Chaves estrangeiras
  sk_algorithm         INT         NOT NULL,   -- FK → dim_algorithm
  sk_operation         INT         NOT NULL,   -- FK → dim_operation
  sk_hardware          INT         NOT NULL,   -- FK → dim_hardware

  -- Métricas de medição
  payload_kb           DECIMAL(6,2),
  key_size_bytes       INT,
  latencia_ms          DOUBLE      NOT NULL,
  iterations           INT,

  -- Campos novos v2
  vt_classico_pct      FLOAT       DEFAULT NULL  COMMENT 'campo v — variação vs clássico (%)',
  overhead_hibrido_pct FLOAT       DEFAULT NULL  COMMENT 'campo h — overhead modo híbrido (%)',

  PRIMARY KEY (sk_benchmark),

  CONSTRAINT fk_fb_algorithm FOREIGN KEY (sk_algorithm) REFERENCES dim_algorithm (sk_algorithm),
  CONSTRAINT fk_fb_operation FOREIGN KEY (sk_operation) REFERENCES dim_operation (sk_operation),
  CONSTRAINT fk_fb_hardware  FOREIGN KEY (sk_hardware)  REFERENCES dim_hardware  (sk_hardware),

  KEY idx_fb_algorithm (sk_algorithm),
  KEY idx_fb_operation (sk_operation),
  KEY idx_fb_hardware  (sk_hardware),
  KEY idx_fb_latencia  (latencia_ms),
  KEY idx_fb_alg_hw_op (sk_algorithm, sk_hardware, sk_operation)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- FIM DO SCRIPT
-- ================================================================
