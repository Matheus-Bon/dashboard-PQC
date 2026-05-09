"""Pytest configuration and fixtures"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment to testing before importing app modules
os.environ['ENVIRONMENT'] = 'test'
os.environ['LOG_LEVEL'] = 'DEBUG'


@pytest.fixture
def project_root_path():
    """Get project root path"""
    return project_root


@pytest.fixture
def sample_benchmark_data():
    """Sample benchmark data for testing"""
    return [
        {
            'execution_time_ms': 100.5,
            'memory_usage_mb': 512,
            'cpu_usage_percent': 45.0,
            'throughput_ops_per_second': 1000,
            'latency_us': 100,
            'error_rate_percent': 0.0,
            'cost_usd': 0.5
        },
        {
            'execution_time_ms': 110.2,
            'memory_usage_mb': 520,
            'cpu_usage_percent': 48.0,
            'throughput_ops_per_second': 990,
            'latency_us': 110,
            'error_rate_percent': 0.1,
            'cost_usd': 0.55
        },
        {
            'execution_time_ms': 105.8,
            'memory_usage_mb': 515,
            'cpu_usage_percent': 46.5,
            'throughput_ops_per_second': 995,
            'latency_us': 105,
            'error_rate_percent': 0.05,
            'cost_usd': 0.52
        }
    ]


@pytest.fixture
def sample_algorithm_data():
    """Sample algorithm dimension data"""
    return [
        {
            'nk_id_algorithm': 1,
            'algorithm_name': 'ML-KEM-512',
            'algorithm_family': 'Lattice-based',
            'crypto_type': 'PQC',
            'security_level': '128-bit'
        },
        {
            'nk_id_algorithm': 2,
            'algorithm_name': 'ML-DSA-44',
            'algorithm_family': 'Lattice-based',
            'crypto_type': 'PQC',
            'security_level': '128-bit'
        },
        {
            'nk_id_algorithm': 3,
            'algorithm_name': 'RSA-2048',
            'algorithm_family': 'RSA',
            'crypto_type': 'Classic',
            'security_level': '112-bit'
        }
    ]


@pytest.fixture
def sample_hardware_data():
    """Sample hardware dimension data"""
    return [
        {
            'nk_id_hardware': 1,
            'provider': 'AWS',
            'instance_type': 't3.xlarge',
            'vcpu': 4,
            'ram_gb': 16,
            'environment_type': 'Prod',
            'cost_per_hour_usd': 0.1664
        },
        {
            'nk_id_hardware': 2,
            'provider': 'GCP',
            'instance_type': 'n2-standard-4',
            'vcpu': 4,
            'ram_gb': 16,
            'environment_type': 'Prod',
            'cost_per_hour_usd': 0.1504
        },
        {
            'nk_id_hardware': 3,
            'provider': 'AWS',
            'instance_type': 't3.medium',
            'vcpu': 2,
            'ram_gb': 4,
            'environment_type': 'Dev',
            'cost_per_hour_usd': 0.0416
        }
    ]


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: unit test"
    )
    config.addinivalue_line(
        "markers", "integration: integration test"
    )
    config.addinivalue_line(
        "markers", "slow: slow running test"
    )


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests"""
    return "asyncio"
