# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 02:43:59 2020

@author: Dvyd
"""


from multiprocessing import Process, Queue
import socket

import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, Literal
from rdflib.namespace import FOAF, RDF
from flask import Flask

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message
from OntoNamespaces import ACL, DSO, RDF, PrOnt, REQ

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = 9000

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentCercador = Agent('AgentCercador',
                       agn.AgentCercador,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

Client = Agent('Client', agn.Client, '', '')

content = Graph()
content.bind('req', REQ)
cerca_obj = agn['cerca']

filters_obj = REQ.Filters + '_filters'
keyword_obj = REQ.KeyWord + '_keyword'

content.add((cerca_obj, RDF.type, REQ.PeticioCerca))
content.add((cerca_obj, REQ.Filters, filters_obj))
content.add((cerca_obj, REQ.KeyWord, keyword_obj))

#passem cerca hardcoded ( de moment xd)
content.add((filters_obj, REQ.Nombre, Literal("Blender")))
content.add((filters_obj, REQ.Precio, Literal(500)))

g = Graph()
#construim el missatge com una req al agent cercador
g = build_message(content, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentCercador.uri, content=cerca_obj)
#enviem el msg
response = send_message(g, AgentCercador.address)
print(response)