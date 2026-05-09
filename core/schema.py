from __future__ import annotations

# --- Dimension: algorithm ---
COL_LIBRARY = "library"           
COL_CRYPTO_TYPE = "crypto_type"   
COL_SECURITY_LEVEL = "security_level"

# --- Dimension: operation ---
COL_OPERATION = "operation"      

# --- Dimension: hardware ---
COL_ENVIRONMENT = "environment"   
COL_ENVIRONMENT_TYPE = "environment_type"
COL_PROCESSOR = "processor"       
COL_RAM_GB = "ram_gb"
COL_OPERATING_SYSTEM = "operating_system"  
COL_VCPU = "vcpu"

# --- Fact: benchmark ---
COL_RESPONSE_MS = "response_ms"       
COL_PAYLOAD_KB = "payload_kb"
COL_KEY_SIZE_BYTES = "key_size_bytes"
COL_ITERATIONS = "iterations"
COL_VS_CLASSIC_PCT = "vs_classic_pct"      
COL_HYBRID_OVERHEAD_PCT = "hybrid_overhead_pct"  

REQUIRED_COLUMNS = (COL_LIBRARY, COL_OPERATION)

NUMERIC_COLUMNS = (
    COL_RESPONSE_MS,
    COL_PAYLOAD_KB,
    COL_KEY_SIZE_BYTES,
    COL_RAM_GB,
    COL_VCPU,
    COL_HYBRID_OVERHEAD_PCT,
    COL_VS_CLASSIC_PCT,
    COL_ITERATIONS,
)
