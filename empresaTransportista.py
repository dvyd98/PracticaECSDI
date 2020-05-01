# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 02:43:59 2020

@author: pball
"""


from multiprocessing import Process, Queue
import socket
import rdflib
import random

import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, Literal, term
from rdflib.namespace import FOAF, RDF
from flask import Flask, request

from FlaskServer import shutdown_server
from Agent import Agent
from AgentUtil.Logging import config_logger
from ACLMessages import build_message, get_message_properties, send_message
from OntoNamespaces import ACL, DSO, RDF, REQ

limR = [1, 6]  
    
# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = 9000

agn = Namespace("http://www.agentes.org#")
                
logger = config_logger(level=1)

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentCentreLogistic = Agent('AgentCentreLogistic',
                        agn.AgentCentreLogistic,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))


EmpresaTransportista = Agent('EmpresaTransportista', agn.EmpresaTransportista, '', '')

# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)


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
                           sender=EmpresaTransportista.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=EmpresaTransportista.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            
            if action == REQ.PeticioEmpresa:
                logger.info('Es demana preu')
                
                #obté pes, ciutat desti i plaç màxim d'entrega per ara HARDCODED
                pes = 2
                ciutatDesti = 'Barcelona'
                diaMaxim = '15/10/2021'
                
                #calcula preu
                preu = pes * random.uniform(limR[0], limR[1])
                
                gResposta = Graph()
                gResposta.bind('req', REQ)
                resposta_obj = agn['preu']
                
                gResposta.add((resposta_obj, RDF.type, REQ.RespostaEmpresa))
                gResposta.add((resposta_obj, REQ.PreuEnviament, preu))
                
                gr = build_message(gResposta,
                           ACL['inform-done'],
                           sender=EmpresaTransportista.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=EmpresaTransportista.uri,
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
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')

