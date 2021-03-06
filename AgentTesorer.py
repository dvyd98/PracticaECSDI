# -*- coding: utf-8 -*-
"""
Created on Fri May 29 16:04:20 2020

@author: gpoltra98
"""

from multiprocessing import Process, Queue
import socket
import rdflib
import random

import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, Literal, term, RDFS
from rdflib.namespace import FOAF, RDF
from flask import Flask, request

from FlaskServer import shutdown_server
from Agent import Agent
from AgentUtil.Logging import config_logger
from ACLMessages import build_message, get_message_properties, send_message
from OntoNamespaces import ACL, DSO, RDF, REQ, XSD, OWL, PrOnt, PrOntRes, PrOntPr
from Agent import portAgentTesorer, portGestorPlataforma, portClient, portVenedorExtern

limR = [1, 6]  
    
# Configuration stuff
hostname = "localhost"
ip = 'localhost'

agn = Namespace("http://www.agentes.org#")
                
logger = config_logger(level=1)

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentTesorer = Agent('AgentTesorer',
                             agn.AgentTesorer,
                             'http://%s:%d/comm' % (hostname, portAgentTesorer),
                             'http://%s:%d/comm' % (hostname, portAgentTesorer))

PlataformaAgent = Agent('PlataformaAgent',
                        agn.PlataformaAgent,
                        'http://%s:%d/comm' % (hostname, portGestorPlataforma),
                        'http://%s:%d/Stop' % (hostname, portGestorPlataforma))

AgentVenedorExtern = Agent('AgentCercador',
                       agn.AgentVenedorExtern,
                       'http://%s:%d/comm' % (hostname, portVenedorExtern),
                       'http://%s:%d/Stop' % (hostname, portVenedorExtern))

Client = Agent('Client', 
               agn.Client,
               'http://%s:%d/comm' % (hostname, portClient), 
               'http://%s:%d/Stop' % (hostname, portClient))

# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)

def esProducteExtern(nombreProd):
    g=Graph()
    g.parse("./Ontologies/product.owl", format="xml")
    query = """
              SELECT ?nombre ?esExterno
              WHERE {
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:esExterno ?esExterno .
              }
              """
    qres = g.query(query, initNs = {'PrOnt': PrOnt, 'PrOntPr': PrOntPr, 'PrOntRes' : PrOntRes})
    
    extern = False
    for row in qres:
        if str(row['nombre']) == str(nombreProd):
            if int(row['esExterno']) == 1:
                extern = True
    
    return extern

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """    
    global dsgraph
    global mss_cnt
    
    
    # Extraemos el mensaje y creamos un grafo con el
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    #Mirem si es un msg FIPA ACL
    if not msgdic:
        #Si no ho es, responem not understood
        logger.info('Msg no es FIPA ACL')
        gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentTesorer.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentTesorer.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            
            if action == REQ.PeticioTransferenciaAPlataforma:
                content = msgdic['content']
                diners = gm.value(subject=content, predicate=REQ.diners)
                compte = gm.value(subject=content, predicate=REQ.compte)
                nombreProd = gm.value(subject=content, predicate=REQ.np)
                
                esExtern = esProducteExtern(nombreProd)
                
                if esExtern == False:
                
                    print("El client paga a la plataforma ", diners, " usant el compte ", compte)
                    
                    conGraph = Graph()
                    conGraph.bind('req', REQ)
                    con_obj = agn['transferencia']
                    conGraph.add((con_obj, RDF.type, REQ.rebreDiners)) 
                    conGraph.add((con_obj, REQ.diners, Literal(diners)))
                    conGraph.add((con_obj, REQ.compte, Literal(compte)))
            
                    missatgeEnviament = build_message(conGraph,perf=ACL.request, sender=AgentTesorer.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=con_obj)
                    response = send_message(missatgeEnviament, PlataformaAgent.address)
                else:
                    
                    print("El client paga al agent extern")
                    
                    tGraph = Graph()
                    tGraph.bind('req', REQ)
                    t_obj = agn['transferencia']
                    tGraph.add((t_obj, RDF.type, REQ.rebreDiners)) 
                    tGraph.add((t_obj, REQ.diners, Literal(diners)))
                    tGraph.add((t_obj, REQ.compte, Literal(compte)))
            
                    missatgeEnviament2 = build_message(tGraph,perf=ACL.request, sender=AgentTesorer.uri, msgcnt=0, receiver=AgentVenedorExtern.uri, content=t_obj)
                    response = send_message(missatgeEnviament2, AgentVenedorExtern.address)
                
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=AgentTesorer.uri,
                           msgcnt=mss_cnt)
            elif action == REQ.PeticioTransferenciaAClient:
                content = msgdic['content']
                diners = gm.value(subject=content, predicate=REQ.diners)
                print("La plataforma retorna al client els diners:", diners)
                
                transGraph = Graph()
                transGraph.bind('req', REQ)
                trans_obj = agn['transferencia2']
                transGraph.add((trans_obj, RDF.type, REQ.rebreDiners)) 
                transGraph.add((trans_obj, REQ.diners, Literal(diners)))
        
                print("Preparat per enviar a client")
                
                missatgeEnviament2 = build_message(transGraph,perf=ACL.request, sender=AgentTesorer.uri, msgcnt=0, receiver=Client.uri, content=trans_obj)
                response = send_message(missatgeEnviament2, Client.address)
                
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=AgentTesorer.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentTesorer.uri,
                           msgcnt=mss_cnt)
                
        mss_cnt += 1
        return gr.serialize(format='xml')

    pass


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente
    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente
    """
    pass


def agentbehavior1(cola):
    """
    Un comportamiento del agente
    :return:
    """
    pass


if __name__ == '__main__':
    
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=portAgentTesorer)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')