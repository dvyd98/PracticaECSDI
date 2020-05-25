# -*- coding: utf-8 -*-
"""
Created on Mon May 25 12:23:10 2020

@author: Dvyd
"""


from multiprocessing import Process, Queue
import sys
import os
import random
import string
sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, RDF, RDFS, Literal
from flask import Flask, request

from ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from OntoNamespaces import ACL, DSO, RDF, PrOnt, REQ, PrOntPr, PrOntRes, CenOntRes, CenOntPr, CenOnt
from OntoNamespaces import LocCenOntRes, LocCenOntPr, LocCenOnt
from AgentUtil.Logging import config_logger
from math import sin, cos, sqrt, atan2, radians
from Agent import portGestorPlataforma, portCerca, portClient

def test_search(var_input, content, cerca_obj, filters_obj):

    if var_input == "1":
        print("Aquest joc de prova realitza una busqueda amb un filtre de categoria")
        print("La categoria per la qual filtrem es la de 'Blender'")
        content.add((cerca_obj, RDF.type, REQ.PeticioCerca))
        content.add((cerca_obj, REQ.Filters, filters_obj))
        
        #passem cerca hardcoded ( de moment xd)
        content.add((filters_obj, REQ.Categoria, Literal("Blender")))
        #content.add((filters_obj, REQ.Nombre, Literal("Blender")))
        #content.add((filters_obj, REQ.Precio, Literal(500)))
        #content.add((filters_obj, REQ.TieneMarca, Literal("Marca_Blender_1UI0FG")))
   
    return content