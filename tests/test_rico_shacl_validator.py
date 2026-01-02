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


class TestActivityShape:
    """Test cases for Activity shape validation."""

    def test_valid_activity(self):
        """Test that a valid Activity passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_activity.ttl", expected_conform=True
        )
        assert conforms, f"Valid activity should conform: {results}"

    def test_invalid_activity_wrong_type(self):
        """Test that Activity with wrong property type fails validation."""
        # Create test data with wrong type for activity property
        test_data = """@prefix : <https://www.ica.org/standards/RiC/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

# Invalid Activity with wrong type for activity property
:activity1 a :Activity ;
    :title "Test Activity" ;
    :activity "invalid_string" .  # Should be a Thing
"""
        with open(TEST_DATA_DIR / "invalid_activity_wrong_type.ttl", "w") as f:
            f.write(test_data)
        
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_activity_wrong_type.ttl",
            expected_conform=False,
        )
        assert not conforms, f"Invalid activity should not conform: {results}"
        assert "must be of type Thing" in results


class TestPersonShape:
    """Test cases for Person shape validation."""

    def test_valid_person(self):
        """Test that a valid Person passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_person.ttl", expected_conform=True
        )
        assert conforms, f"Valid person should conform: {results}"

    def test_invalid_person_wrong_type(self):
        """Test that Person with wrong property type fails validation."""
        # Create test data with wrong type for person property
        test_data = """@prefix : <https://www.ica.org/standards/RiC/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

# Invalid Person with wrong type for person property
:person1 a :Person ;
    :title "John Doe" ;
    :person "invalid_string" .  # Should be an Agent
"""
        with open(TEST_DATA_DIR / "invalid_person_wrong_type.ttl", "w") as f:
            f.write(test_data)
        
        conforms, results = validate_data(
            TEST_DATA_DIR / "invalid_person_wrong_type.ttl",
            expected_conform=False,
        )
        assert not conforms, f"Invalid person should not conform: {results}"
        assert "must be of type Agent" in results


class TestCorporateBodyShape:
    """Test cases for CorporateBody shape validation."""

    def test_valid_corporate_body(self):
        """Test that a valid CorporateBody passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_corporate_body.ttl", expected_conform=True
        )
        assert conforms, f"Valid corporate body should conform: {results}"


class TestEventShape:
    """Test cases for Event shape validation."""

    def test_valid_event(self):
        """Test that a valid Event passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_event.ttl", expected_conform=True
        )
        assert conforms, f"Valid event should conform: {results}"


class TestPlaceShape:
    """Test cases for Place shape validation."""

    def test_valid_place(self):
        """Test that a valid Place passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_place.ttl", expected_conform=True
        )
        assert conforms, f"Valid place should conform: {results}"


class TestRelationShape:
    """Test cases for Relation shape validation."""

    def test_valid_relation(self):
        """Test that a valid Relation passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_relation.ttl", expected_conform=True
        )
        assert conforms, f"Valid relation should conform: {results}"


class TestIdentifierShape:
    """Test cases for Identifier shape validation."""

    def test_valid_identifier(self):
        """Test that a valid Identifier passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_identifier.ttl", expected_conform=True
        )
        assert conforms, f"Valid identifier should conform: {results}"


class TestFamilyShape:
    """Test cases for Family shape validation."""

    def test_valid_family(self):
        """Test that a valid Family passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_family.ttl", expected_conform=True
        )
        assert conforms, f"Valid family should conform: {results}"


class TestMechanismShape:
    """Test cases for Mechanism shape validation."""

    def test_valid_mechanism(self):
        """Test that a valid Mechanism passes validation."""
        conforms, results = validate_data(
            TEST_DATA_DIR / "valid_mechanism.ttl", expected_conform=True
        )
        assert conforms, f"Valid mechanism should conform: {results}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
