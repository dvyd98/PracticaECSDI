# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 02:43:59 2020

@author: pball
"""


from multiprocessing import Process, Queue
import socket

import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, Literal, term
from rdflib.namespace import FOAF, RDF
from flask import Flask

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message
from OntoNamespaces import ACL, DSO, RDF, PrOnt, PrOntPr, PrOntRes, REQ

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = 9000

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentCentreLogistic = Agent('AgentCentreLogistic',
                        agn.AgentCentreLogistic,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))


EmpresaTransportista = Agent('EmpresaTransportista', agn.EmpresaTransportista, '', '')

