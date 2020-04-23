# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 13:31:53 2020

@author: Dvyd
"""
import sys
import os

from rdflib import Graph, Literal, RDF, RDFS, OWL, URIRef, Namespace
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
g.parse("./Ontologies/product.owl", format="xml")

# Iterate over triples in store and print them out.
#print("--- printing raw triples ---")
p1= PrOnt.Phone
for p, o in g[p1]:
    print(p,o)
    
#print("--- printing mboxes ---")
#for triple in g:
#    print(triple)
        
if (PrOnt.ElectronicDevice, RDF.type, OWL.Class) in g:
    print("El grafo contiene electronic devices")

#for s, p, o in g[PrOntPr.Phone]:
#    print(s,p,o)
#for obj in g.subject_predicates(PrOnt.Phone):
#    print(obj)
test= Namespace("http://www.products.org/ontology/resource/Marca_Blender_OWM78C")
nombre_filter = '"nombre_Phone"'
query = """SELECT ?nombre ?class ?n
              WHERE {
              ?a rdf:type ?class .
              ?class rdfs:subClassOf ?n .
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:tieneMarca ?b .
              ?b PrOntPr:nombre ?marca .
              
              }
              """
#print(query)
qres = g.query(query, initNs = {'PrOnt': PrOnt, 'PrOntPr': PrOntPr, 'PrOntRes' : PrOntRes})

for row in qres:
   print(row['class'])
name="this"
other="that"
#print("testing %s and %s" % (name,other))

#print(g.serialize(format='turtle').decode("utf-8"))