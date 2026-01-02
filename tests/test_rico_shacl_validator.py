"""
Test suite for RICO SHACL validator.

This test suite validates that the SHACL rules in rico-shacl.ttl correctly
validate and invalidate RICO data according to the specified constraints.
"""

from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
VALIDATOR_DIR = Path(__file__).parent.parent / "validator"


def load_shacl_shapes():
    """Load the SHACL shapes from the rico-shacl.ttl file."""
    shacl_graph = Graph()
    shacl_graph.parse(VALIDATOR_DIR / "rico-shacl.ttl", format="turtle")
    return shacl_graph


def validate_data(data_file: Path, expected_conform: bool):
    """Validate RICO data against SHACL shapes."""
    shacl_graph = load_shacl_shapes()

    # Load the data to validate
    data_graph = Graph()
    data_graph.parse(str(data_file), format="turtle")

    # Perform validation
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )

    return conforms, results_text


class TestInstantiationShape:
    """Test cases for Instantiation shape validation."""

    def test_valid_instantiation(self):
        """Test that a valid Instantiation passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_instantiation.ttl", expected_conform=True
        )
        assert conforms, f"Valid instantiation should conform: {results}"

    def test_invalid_instantiation_non_literal_properties(self):
        """Test that Instantiation with non-literal properties fails validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_instantiation_non_literal.ttl",
            expected_conform=False,
        )
        assert not conforms, f"Invalid instantiation should not conform: {results}"
        assert "must be a literal" in results


class TestRecordResourceShape:
    """Test cases for RecordResource shape validation."""

    def test_valid_record_resource(self):
        """Test that a valid RecordResource passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_record_resource.ttl", expected_conform=True
        )
        assert conforms, f"Valid record resource should conform: {results}"

    def test_invalid_record_resource_wrong_type(self):
        """Test that RecordResource with wrong property types fails validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_record_resource_wrong_type.ttl",
            expected_conform=False,
        )
        assert not conforms, f"Invalid record resource should not conform: {results}"
        assert "must be of type" in results


class TestRecordSetShape:
    """Test cases for RecordSet shape validation."""

    def test_valid_record_set(self):
        """Test that a valid RecordSet passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_record_set.ttl", expected_conform=True
        )
        assert conforms, f"Valid record set should conform: {results}"

    def test_invalid_record_set_wrong_content_type(self):
        """Test that RecordSet with wrong content type fails validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_record_set_wrong_content_type.ttl",
            expected_conform=False,
        )
        assert not conforms, f"Invalid record set should not conform: {results}"
        assert "must be of type ContentType" in results


class TestRecordShape:
    """Test cases for Record shape validation."""

    def test_valid_record(self):
        """Test that a valid Record passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_record.ttl", expected_conform=True
        )
        assert conforms, f"Valid record should conform: {results}"

    def test_invalid_record_wrong_subject_type(self):
        """Test that Record with wrong subject type fails validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_record_wrong_subject.ttl", expected_conform=False
        )
        assert not conforms, f"Invalid record should not conform: {results}"
        assert "must be of type Thing" in results


class TestThingShape:
    """Test cases for Thing shape validation."""

    def test_valid_thing(self):
        """Test that a valid Thing passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_thing.ttl", expected_conform=True
        )
        assert conforms, f"Valid thing should conform: {results}"

    def test_invalid_thing_non_literal_title(self):
        """Test that Thing with non-literal title fails validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_thing_non_literal_title.ttl",
            expected_conform=False,
        )
        assert not conforms, f"Invalid thing should not conform: {results}"
        assert "title must be a literal" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
