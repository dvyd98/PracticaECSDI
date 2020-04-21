# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 18:32:44 2020

@author: gpoltra98
"""

from multiprocessing import Process, Queue
import socket
import argparse

from flask import Flask, request
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import FOAF, RDF

from AgentUtil.OntoNamespaces import ACL, DSO
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.Agent import Agent
from AgentUtil.Logging import config_logger

# Flask stuff
app = Flask(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--comprar', type=int , default='None', help="Accio de comprar producte")
    
    logger = config_logger(level=1)
    
    args = parser.parse_args()
    
    comprar_aux = 0
    if args.comprar is None:
        comprar_aux = 0
    else:
        comprar_aux = 1
        
    agn = Namespace("http://www.agentes.org#")
    
    mss_cnt = 0
    
    PlataformaAgent = Agent('PlataformaAgent',
                            agn.Plataforma,
                            "adreça per iniciar",
                            "adreça per acabar")
    
    