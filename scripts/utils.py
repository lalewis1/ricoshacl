"""Functions for scraping details out of an ontology"""

import datetime
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, SDO, SH, XSD


def git_short_hash() -> str:
    output = subprocess.check_output("git rev-parse --short HEAD".split())
    short_hash = output.decode().strip()
    return short_hash


@dataclass(frozen=True)
class Restriction:
    on_klass: tuple[URIRef]
    on_property: [URIRef]
    min_cardinality: Literal | None = None
    max_cardinality: Literal | None = None


class Ontology:
    def __init__(self, src: Path, uri: URIRef):
        self.graph = Graph().parse(src)
        self.graph.bind(":", str(uri))
        self.identifier = uri

    def classes(
        self, in_domain_of: URIRef | None = None, in_range_of: URIRef | None = None
    ) -> set[URIRef]:
        """Get all owl:Class's defined in the ontology

        optionally restricted to those that are in the range or domain of
        a given owl:ObjectProperty .
        """
        assert not all(
            [in_domain_of, in_range_of]
        ), "domain and range cannot be given at the same time"

        all_klasses = {
            klass
            for klass in self.graph.subjects(RDF.type, OWL.Class)
            if not isinstance(klass, BNode)
            and str(klass).startswith(str(self.identifier))
        }
        if in_domain_of:
            return {
                klass
                for klass in self.graph.objects(in_domain_of, RDFS.range)
                if klass in all_klasses
            }
        if in_range_of:
            return {
                klass
                for klass in self.graph.objects(in_range_of, RDFS.range)
                if klass in all_klasses
            }
        return all_klasses

    def properties(
        self, with_domain: URIRef | None = None, with_range: URIRef | None = None
    ) -> list[URIRef]:
        """Get all owl:ObjectProperty's defined in the ontology
        optionally restricted to those with the given rdfs:domain or rdfs:range
        """

        assert not all(
            [with_domain, with_range]
        ), "domain and range cannot be given at the same time"

        assert any([with_domain, with_range]), "One of domain or range must be given"

        pred, obj = (
            (RDFS.domain, with_domain) if with_domain else (RDFS.range, with_range)
        )
        assert (
            obj in self.classes()
        ), f"{object} is not an owl:Class defined in this ontology"

        return {
            prop
            for prop in self.graph.subjects(pred, obj)
            if not isinstance(prop, BNode)
            and str(prop).startswith(str(self.identifier))
        }

    def restrictions(self, for_klass: URIRef) -> set[Restriction]:
        """Get all owl:Restrictions as Restriction objects

        Optionally limited to restrictions on a given owl:Class
        """

        restrictions = []
        restriction_uris = {
            uri for uri in self.graph.subjects(RDF.type, OWL.Restriction)
        }
        if for_klass:
            subklass_uris = {
                uri for uri in self.graph.objects(for_klass, RDFS.subClassOf)
            }
            restriction_uris = restriction_uris.intersection(subklass_uris)
        for restriction_uri in restriction_uris:
            on_klass = self.graph.value(restriction_uri, OWL.onClass, None)
            if isinstance(on_klass, BNode):
                union_bnode = self.graph.value(on_klass, OWL.unionOf, None)
                on_klass = tuple(Collection(self.graph, union_bnode))
            else:
                on_klass = (on_klass,)
            on_property = self.graph.value(restriction_uri, OWL.onProperty, None)
            min_cardinality = self.graph.value(
                restriction_uri, OWL.minQualifiedCardinality, None, default=None
            )
            # TODO: handle unqualified min_cardinality
            max_cardinality = self.graph.value(
                restriction_uri, OWL.maxQualifiedCardinality, None, default=None
            )
            # TODO: handle unqualified max_cardinality
            restriction = Restriction(
                on_klass=on_klass,
                on_property=on_property,
                min_cardinality=min_cardinality,
                max_cardinality=max_cardinality,
            )
            restrictions.append(restriction)
        return restrictions


class Shacl:
    def __init__(
        self,
        base_ontology: Ontology,
        namespace: Namespace,
        versionIRI: URIRef,
        creator: URIRef,
        dateCreated: Literal | None = None,
        name: Literal | None = None,
        description: Literal | None = None,
        publisher: URIRef | None = None,
        base_ontology_prefix: str | None = None,
    ):
        self.identifier = URIRef(namespace)
        self.shape = namespace
        self.ont = base_ontology
        self.graph = Graph()
        self.graph.bind("", self.identifier)
        if base_ontology_prefix:
            self.graph.bind(base_ontology_prefix, self.ont.identifier)

        # Validator Ontology metadata
        # --------------------------------------------------------------------------------
        self.graph.add((self.identifier, RDF.type, OWL.Ontology))
        self.graph.add((self.identifier, OWL.versionIRI, versionIRI))
        self.graph.add(
            (
                self.identifier,
                OWL.versionInfo,
                Literal(
                    f"{versionIRI.n3(namespace_manager=self.graph.namespace_manager)}: Generated by OntoShacl on commit: {git_short_hash()}"
                ),
            )
        )
        self.graph.add((self.identifier, SDO.creator, creator))
        dateModified = datetime.date.today().isoformat()
        dateCreated = dateCreated or dateModified
        self.graph.add(
            (self.identifier, SDO.dateCreated, Literal(dateCreated, datatype=XSD.date))
        )
        self.graph.add(
            (
                self.identifier,
                SDO.dateModified,
                Literal(dateModified, datatype=XSD.date),
            )
        )
        description = (
            description or f"OntoShacl generated validator for {self.ont.identifier}"
        )
        self.graph.add((self.identifier, SDO.description, Literal(description)))
        name = name or f"{self.ont.identifier} Validator"
        self.graph.add((self.identifier, SDO.name, Literal(name)))
        if publisher:
            self.graph.add((self.identifier, SDO.publisher, publisher))
        # --------------------------------------------------------------------------------

        for klass in self.ont.classes():
            self.add_nodeshape(klass)

    def add_nodeshape(self, klass: URIRef):
        shape_uri = self.compute_shape_uri(klass)
        self.graph.add((shape_uri, RDF.type, SH.NodeShape))
        self.graph.add((shape_uri, RDFS.isDefinedBy, self.ont.identifier))
        self.graph.add((shape_uri, SH.targetClass, klass))

        # TODO: better combining of sh:properties
        # should only really be one loop here instead of one for properties
        # and one for restrictions.
        prop_path_map = dict()
        for prop in self.ont.properties(with_domain=klass):
            prop_klasses = self.ont.classes(in_range_of=prop)
            if len(prop_klasses) < 1:
                continue
            prop_bnode = BNode()
            prop_path_map[prop] = prop_bnode
            self.graph.add((shape_uri, SH.property, prop_bnode))
            self.graph.add((prop_bnode, SH.path, prop))
            if len(prop_klasses) > 1:
                collection = Collection(self.graph, BNode())
                for prop_klass in prop_klasses:
                    k = BNode()
                    self.graph.add((k, SH["class"], prop_klass))
                    collection.append(k)
                self.graph.add((prop_bnode, SH["or"], collection.uri))
            elif len(prop_klasses) == 1:
                self.graph.add((prop_bnode, SH["class"], list(prop_klasses)[0]))

        for restriction in self.ont.restrictions(for_klass=klass):
            prop_bnode = prop_path_map.get(restriction.on_property, None)
            if prop_bnode is None:
                prop_bnode = BNode()
                self.graph.add((shape_uri, SH.property, prop_bnode))
                self.graph.add((prop_bnode, SH.path, restriction.on_property))
            if len(restriction.on_klass) > 1:
                collection = Collection(self.graph, BNode())
                for restriction_klass in restriction.on_klass:
                    k = BNode()
                    self.graph.add((k, SH["class"], restriction_klass))
                    collection.append(k)
                self.graph.add((prop_bnode, SH["or"], collection.uri))
            elif len(restriction.on_klass) == 1:
                self.graph.add((prop_bnode, SH["class"], restriction.on_klass[0]))
            if restriction.min_cardinality:
                self.graph.add((prop_bnode, SH.minCount, restriction.min_cardinality))
            if restriction.max_cardinality:
                self.graph.add((prop_bnode, SH.maxCount, restriction.max_cardinality))

        # TODO: add sh:message for each sh:property [ sh:path <...> ; sh:message "some message" ]

    def compute_shape_uri(self, klass: URIRef) -> URIRef:
        parse_result = urlparse(str(klass))
        fragment = parse_result.fragment
        path_part = parse_result.path.split("/")[-1]
        shape_name = f"{fragment}Shape" if fragment else f"{path_part}Shape"
        shape_uri = self.shape[shape_name]
        return shape_uri

    def __repr__(self):
        return self.graph.serialize(format="longturtle")


if __name__ == "__main__":
    src = Path(__file__).parent.parent / "ontology/rico.ttl"
    uri = URIRef("https://www.ica.org/standards/RiC/ontology#")
    rico = Ontology(src=src, uri=uri)

    namespace = Namespace("https://kurrawong.ai/validator/rico#")
    shacl = Shacl(
        base_ontology=rico,
        base_ontology_prefix="rico",
        namespace=namespace,
        versionIRI=namespace["0.0.1"],
        creator=URIRef("https://kurrawong.ai/people#lawson-lewis"),
        name=Literal("RiC-O Validator"),
        description=Literal(
            "Unofficial SHACL Shapes Validator for the Records in Contect Ontology [RiC-O]"
        ),
        publisher=URIRef("https://kurrawong.ai"),
    )

    print(shacl)
