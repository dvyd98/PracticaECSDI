# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 13:31:53 2020

@author: Dvyd
"""


from rdflib import Graph, Literal, RDF, OWL, URIRef, Namespace
from rdflib.namespace import FOAF , XSD

import rdflib
PrOnt = Namespace("http://www.products.org/ontology/")
PrOntPr = Namespace("http://www.products.org/ontology/property/")
PrOntRes = Namespace("http://www.products.org/ontology/resource/")
    
g=rdflib.Graph()
g.parse("product.owl", format="xml")

# Iterate over triples in store and print them out.
#print("--- printing raw triples ---")
#for s, p, o in g:
#    print((s, p, o))
    
print("--- printing mboxes ---")
for obj in g.subjects(RDF.type, OWL.Class):
    for mbox in g.objects(obj, PrOnt.ElectronicDevice):
        print(mbox)


print(g.serialize(format='turtle').decode("utf-8"))