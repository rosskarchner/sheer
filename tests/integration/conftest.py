"""
Pytest configuration and fixtures for integration tests.
"""
import os
import time
import pytest
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.core.generic import DockerContainer
from elasticsearch import Elasticsearch
from opensearchpy import OpenSearch


@pytest.fixture(scope="session")
def elasticsearch_container():
    """
    Spin up an Elasticsearch container for testing.
    """
    container = ElasticSearchContainer("docker.elastic.co/elasticsearch/elasticsearch:8.11.0")
    container.with_env("xpack.security.enabled", "false")
    container.with_env("discovery.type", "single-node")
    container.start()

    # Wait for Elasticsearch to be ready
    es_url = container.get_connection_url()
    es = Elasticsearch([es_url])

    max_attempts = 30
    for _ in range(max_attempts):
        try:
            if es.ping():
                break
        except:
            time.sleep(1)

    yield {
        "url": es_url,
        "host": container.get_container_host_ip(),
        "port": container.get_exposed_port(9200),
        "container": container
    }

    container.stop()


@pytest.fixture(scope="session")
def opensearch_container():
    """
    Spin up an OpenSearch container for testing.
    """
    container = DockerContainer("opensearchproject/opensearch:2.11.0")
    container.with_env("discovery.type", "single-node")
    container.with_env("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "Admin123!")
    container.with_env("plugins.security.disabled", "true")
    container.with_exposed_ports(9200)
    container.start()

    host = container.get_container_host_ip()
    port = container.get_exposed_port(9200)

    # Wait for OpenSearch to be ready
    os_client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=None,
        use_ssl=False,
        verify_certs=False
    )

    max_attempts = 30
    for _ in range(max_attempts):
        try:
            if os_client.ping():
                break
        except:
            time.sleep(1)

    yield {
        "host": host,
        "port": port,
        "container": container
    }

    container.stop()


@pytest.fixture
def test_data_dir():
    """
    Return the path to the test data directory.
    """
    return os.path.join(os.path.dirname(__file__), "test_data")
