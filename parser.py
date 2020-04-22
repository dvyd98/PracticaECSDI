# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 13:31:53 2020

@author: Dvyd
"""


from rdflib import Graph, Literal, RDF, OWL, URIRef, Namespace
from rdflib.namespace import FOAF , XSD
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import urlparse
from pathlib import PurePosixPath

sys.path.append(os.path.relpath("./AgentUtil"))

import rdflib

PrOnt = Namespace("http://www.products.org/ontology/")
PrOntPr = Namespace("http://www.products.org/ontology/property/")
PrOntRes = Namespace("http://www.products.org/ontology/resource/")
    
g=rdflib.Graph()
g.parse("product.owl", format="xml")

# Iterate over triples in store and print them out.
#print("--- printing raw triples ---")
for s, p, o in g:
    print((p))
    
#print("--- printing mboxes ---")
#for triple in g:
#    print(triple)
        
if (PrOnt.ElectronicDevice , RDF.type, OWL.Class) in g:
    print("El grafo contiene electronic devices")

#for obj in g.subject_predicates(PrOnt.Phone):
#    print(obj)
    
qres = g.query("""
              SELECT ?nombre ?precio ?tieneMarca
              WHERE {
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:precio ?precio .
              ?a PrOntPr:tieneMarca ?tieneMarca .
              ?a PrOntPr:peso ?peso .
                  FILTER (?peso > 10.0)
              }
              """, initNs = {'PrOntPr': PrOntPr})
for row in qres:
    path = urlparse(row['tieneMarca']).path
    print(PurePosixPath(path).parts[3])

#print(g.serialize(format='turtle').decode("utf-8"))