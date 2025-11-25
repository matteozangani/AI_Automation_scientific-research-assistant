"""
Shared pytest fixtures for all tests
"""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def api_key():
    """Get API key from environment"""
    return os.getenv("ANTHROPIC_API_KEY")


@pytest.fixture(scope="session")
def has_api_key():
    """Check if API key is available"""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


@pytest.fixture
def sample_query():
    """Sample research query"""
    return "What are the latest advances in transformer attention mechanisms?"


@pytest.fixture
def medical_query():
    """Sample medical research query"""
    return "What are the mechanisms of CRISPR off-target effects?"


@pytest.fixture
def sample_papers():
    """Sample papers for testing"""
    return [
        {
            'title': 'Attention Is All You Need',
            'summary': 'We propose a new simple network architecture, the Transformer.',
            'authors': ['Vaswani', 'Shazeer', 'Parmar'],
            'year': '2017',
            'citation_count': 50000,
            'arxiv_id': '1706.03762',
            'pdf_url': 'https://arxiv.org/pdf/1706.03762.pdf'
        },
        {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
            'summary': 'We introduce BERT.',
            'authors': ['Devlin', 'Chang'],
            'year': '2018',
            'citation_count': 40000,
            'arxiv_id': '1810.04805',
            'pdf_url': 'https://arxiv.org/pdf/1810.04805.pdf'
        }
    ]


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test"""
    yield
    
    # Cleanup
    test_cache = Path("./test_cache")
    test_db = Path("./test_chroma_db")
    
    if test_cache.exists():
        import shutil
        shutil.rmtree(test_cache, ignore_errors=True)
    
    if test_db.exists():
        import shutil
        shutil.rmtree(test_db, ignore_errors=True)
