"""
Integration tests for Sheer with OpenSearch.
"""
import os
import sys
import pytest
from opensearchpy import OpenSearch
from sheer.indexer import index_location, ContentProcessor, read_json_file


class Args:
    """Mock args object for indexer."""
    def __init__(self, processors=None, reindex=False):
        self.processors = processors or []
        self.reindex = reindex


@pytest.mark.integration
class TestOpenSearchIntegration:
    """Integration tests with real OpenSearch instance."""

    def test_opensearch_connection(self, opensearch_container):
        """Test that we can connect to OpenSearch."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )
        assert os_client.ping()

    def test_index_creation(self, opensearch_container, test_data_dir):
        """Test creating an index in OpenSearch."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_content"
        }

        args = Args(reindex=True)

        # This should create the index
        index_location(args, config)

        # Verify the index was created
        assert os_client.indices.exists(index="test_os_content")

    def test_document_indexing(self, opensearch_container, test_data_dir):
        """Test indexing documents from processors."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_posts"
        }

        args = Args(reindex=True)
        index_location(args, config)

        # Refresh index to make documents searchable
        os_client.indices.refresh(index="test_os_posts")

        # Search for all documents
        result = os_client.search(index="test_os_posts", body={"query": {"match_all": {}}})

        # We should have 3 test posts
        total = result['hits']['total']
        if isinstance(total, dict):
            total = total['value']

        assert total == 3, f"Expected 3 documents, got {total}"

    def test_document_search(self, opensearch_container, test_data_dir):
        """Test searching for documents with specific content."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_search"
        }

        args = Args(reindex=True)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_search")

        # Search for "elasticsearch"
        result = os_client.search(
            index="test_os_search",
            body={"query": {"match": {"content": "elasticsearch"}}}
        )

        total = result['hits']['total']
        if isinstance(total, dict):
            total = total['value']

        assert total >= 1, "Should find at least one post about elasticsearch"

    def test_mapping_creation(self, opensearch_container, test_data_dir):
        """Test that mappings are properly created."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_mappings"
        }

        args = Args(reindex=True)
        index_location(args, config)

        # Get mappings
        mappings = os_client.indices.get_mapping(index="test_os_mappings")

        assert "test_os_mappings" in mappings
        assert "mappings" in mappings["test_os_mappings"]

        # Check that our expected fields are in the mapping
        props = mappings["test_os_mappings"]["mappings"]["properties"]
        assert "title" in props
        assert "author" in props
        assert "date" in props

    def test_document_retrieval(self, opensearch_container, test_data_dir):
        """Test retrieving a specific document by ID."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_retrieval"
        }

        args = Args(reindex=True)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_retrieval")

        # Get all documents to find an ID
        result = os_client.search(index="test_os_retrieval", body={"query": {"match_all": {}}})

        if result['hits']['hits']:
            doc_id = result['hits']['hits'][0]['_id']

            # Retrieve the document
            doc = os_client.get(index="test_os_retrieval", id=doc_id)

            assert doc['_id'] == doc_id
            assert '_source' in doc
            assert 'title' in doc['_source']

    def test_aggregations(self, opensearch_container, test_data_dir):
        """Test aggregations on indexed data."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_aggs"
        }

        args = Args(reindex=True)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_aggs")

        # Aggregate by category
        result = os_client.search(
            index="test_os_aggs",
            body={
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {"field": "category"}
                    }
                }
            }
        )

        assert "aggregations" in result
        assert "categories" in result["aggregations"]
        assert len(result["aggregations"]["categories"]["buckets"]) > 0

    def test_reindexing(self, opensearch_container, test_data_dir):
        """Test reindexing functionality."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_reindex"
        }

        # Index once
        args = Args(reindex=True)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_reindex")

        # Get document count
        result1 = os_client.count(index="test_os_reindex")
        count1 = result1['count']

        # Reindex
        args = Args(reindex=True)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_reindex")

        # Get document count again
        result2 = os_client.count(index="test_os_reindex")
        count2 = result2['count']

        # Counts should be the same
        assert count1 == count2

    def test_bool_query(self, opensearch_container, test_data_dir):
        """Test that bool queries work correctly."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_bool"
        }

        args = Args(reindex=True)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_bool")

        # Use bool query with filter
        result = os_client.search(
            index="test_os_bool",
            body={
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"category": "Technology"}}
                        ]
                    }
                }
            }
        )

        total = result['hits']['total']
        if isinstance(total, dict):
            total = total['value']

        assert total >= 1, "Should find at least one Technology post"

    def test_partial_indexing(self, opensearch_container, test_data_dir):
        """Test indexing specific processors."""
        os_client = OpenSearch(
            hosts=[{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            http_auth=None,
            use_ssl=False,
            verify_certs=False
        )

        config = {
            "location": test_data_dir,
            "elasticsearch": [{
                "host": opensearch_container["host"],
                "port": opensearch_container["port"]
            }],
            "index": "test_os_partial"
        }

        # Index all first
        args = Args(reindex=True)
        index_location(args, config)

        # Now partial index just posts
        args = Args(processors=["posts"], reindex=False)
        index_location(args, config)

        os_client.indices.refresh(index="test_os_partial")

        # Should still have documents
        result = os_client.count(index="test_os_partial")
        assert result['count'] > 0
