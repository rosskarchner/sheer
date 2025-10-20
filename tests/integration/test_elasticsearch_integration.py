"""
Integration tests for Sheer with Elasticsearch.
"""
import os
import sys
import pytest
from elasticsearch import Elasticsearch
from sheer.indexer import index_location, ContentProcessor, read_json_file
from sheer.query import QueryFinder, Query
from sheer.wsgi import app_with_config


class Args:
    """Mock args object for indexer."""
    def __init__(self, processors=None, reindex=False):
        self.processors = processors or []
        self.reindex = reindex


@pytest.mark.integration
class TestElasticsearchIntegration:
    """Integration tests with real Elasticsearch instance."""

    def test_elasticsearch_connection(self, elasticsearch_container):
        """Test that we can connect to Elasticsearch."""
        es = Elasticsearch([elasticsearch_container["url"]])
        assert es.ping()

    def test_index_creation(self, elasticsearch_container, test_data_dir):
        """Test creating an index in Elasticsearch."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_content"
        }

        args = Args(reindex=True)

        # This should create the index
        index_location(args, config)

        # Verify the index was created
        assert es.indices.exists(index="test_content")

    def test_document_indexing(self, elasticsearch_container, test_data_dir):
        """Test indexing documents from processors."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_posts"
        }

        args = Args(reindex=True)
        index_location(args, config)

        # Refresh index to make documents searchable
        es.indices.refresh(index="test_posts")

        # Search for all documents
        result = es.search(index="test_posts", body={"query": {"match_all": {}}})

        # We should have 3 test posts
        total = result['hits']['total']
        if isinstance(total, dict):
            total = total['value']

        assert total == 3, f"Expected 3 documents, got {total}"

    def test_document_search(self, elasticsearch_container, test_data_dir):
        """Test searching for documents with specific content."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_search"
        }

        args = Args(reindex=True)
        index_location(args, config)

        es.indices.refresh(index="test_search")

        # Search for "docker"
        result = es.search(
            index="test_search",
            body={"query": {"match": {"content": "docker"}}}
        )

        total = result['hits']['total']
        if isinstance(total, dict):
            total = total['value']

        assert total >= 1, "Should find at least one post about docker"

    def test_mapping_creation(self, elasticsearch_container, test_data_dir):
        """Test that mappings are properly created."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_mappings"
        }

        args = Args(reindex=True)
        index_location(args, config)

        # Get mappings
        mappings = es.indices.get_mapping(index="test_mappings")

        assert "test_mappings" in mappings
        assert "mappings" in mappings["test_mappings"]

        # Check that our expected fields are in the mapping
        props = mappings["test_mappings"]["mappings"]["properties"]
        assert "title" in props
        assert "author" in props
        assert "date" in props

    def test_document_retrieval(self, elasticsearch_container, test_data_dir):
        """Test retrieving a specific document by ID."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_retrieval"
        }

        args = Args(reindex=True)
        index_location(args, config)

        es.indices.refresh(index="test_retrieval")

        # Get all documents to find an ID
        result = es.search(index="test_retrieval", body={"query": {"match_all": {}}})

        if result['hits']['hits']:
            doc_id = result['hits']['hits'][0]['_id']

            # Retrieve the document
            doc = es.get(index="test_retrieval", id=doc_id)

            assert doc['_id'] == doc_id
            assert '_source' in doc
            assert 'title' in doc['_source']

    def test_aggregations(self, elasticsearch_container, test_data_dir):
        """Test aggregations on indexed data."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_aggs"
        }

        args = Args(reindex=True)
        index_location(args, config)

        es.indices.refresh(index="test_aggs")

        # Aggregate by category
        result = es.search(
            index="test_aggs",
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

    def test_reindexing(self, elasticsearch_container, test_data_dir):
        """Test reindexing functionality."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_reindex"
        }

        # Index once
        args = Args(reindex=True)
        index_location(args, config)

        es.indices.refresh(index="test_reindex")

        # Get document count
        result1 = es.count(index="test_reindex")
        count1 = result1['count']

        # Reindex
        args = Args(reindex=True)
        index_location(args, config)

        es.indices.refresh(index="test_reindex")

        # Get document count again
        result2 = es.count(index="test_reindex")
        count2 = result2['count']

        # Counts should be the same
        assert count1 == count2

    def test_bool_query(self, elasticsearch_container, test_data_dir):
        """Test that bool queries work correctly."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_bool"
        }

        args = Args(reindex=True)
        index_location(args, config)

        es.indices.refresh(index="test_bool")

        # Use bool query with filter
        result = es.search(
            index="test_bool",
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

    def test_partial_indexing(self, elasticsearch_container, test_data_dir):
        """Test indexing specific processors."""
        es = Elasticsearch([elasticsearch_container["url"]])

        config = {
            "location": test_data_dir,
            "elasticsearch": [elasticsearch_container["url"]],
            "index": "test_partial"
        }

        # Index all first
        args = Args(reindex=True)
        index_location(args, config)

        # Now partial index just posts
        args = Args(processors=["posts"], reindex=False)
        index_location(args, config)

        es.indices.refresh(index="test_partial")

        # Should still have documents
        result = es.count(index="test_partial")
        assert result['count'] > 0
