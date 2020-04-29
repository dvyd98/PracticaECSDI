# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 13:51:30 2020

@author: pball
"""

#Template
from multiprocessing import Process, Queue
import socket

import sys
import os
sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, RDF, REQ
from flask import Flask, request

from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from AgentUtil.Logging import config_logger

from ACLMessages import build_message, get_message_properties, send_message
from OntoNamespaces import ACL

__author__ = 'pball'


# Configuration stuff
hostname = socket.gethostname()
port = 9010

#logger = config_logger(level=1, file="./logs/AgentCentreLogistic")
logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

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
    
    def negociarTransport(pes, ciutatDesti, diaMaxim):
        result = Graph()
        
        #construeix el graph per passar a l'empresa
        contentPeticioEmpresa = Graph()
        contentPeticioEmpresa.bind('req', REQ)
        enviament_obj = agn['enviament']
        
        contentPeticioEmpresa.add((enviament_obj, RDF.type, REQ.PeticioEmpresa))
        contentPeticioEmpresa.add((enviament_obj, REQ.PesProductes, pes))
        contentPeticioEmpresa.add((enviament_obj, REQ.CiutatDesti, ciutatDesti))
        contentPeticioEmpresa.add((enviament_obj, REQ.DiaMaxim, diaMaxim))
        
        messageEmpresa = Graph()
        messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=AgentCentreLogistic.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        
        #envia missatge a EmpresaTransportista
        response = send_message(messageEmpresa, EmpresaTransportista.address)
        
        return result
    
    global dsgraph
    global mss_cnt
    
    logger.info('Peticion de informacion recibida')
    
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
                           sender=AgentCentreLogistic.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentCentreLogistic.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            
            if action == REQ.PeticioEnviament:
                logger.info('Es delega enviament')
                
                #obtenir info per passar empresa HARDCODED DE MOMENT
                pes = 2
                ciutatDesti = 'Barcelona'
                diaMaxim = '15/10/2021'
                
                #Encara no es pot fer
#               content = msgdic['content']
#               pes = gm.value(subject=content, predicate=REQ.PesProducte)
#               ciutatDesti = gm.value(subject=content, predicate=REQ.CiutatDesti)
#               diaMaxim = gm.value(subject=content, predicate=REQ.DiaMaxim)
            
                #escollir millor empresa
                gResposta = negociarTransport(pes, ciutatDesti, diaMaxim)
                
                gr = build_message(gResposta,
                           ACL['inform-done'],
                           sender=AgentCentreLogistic.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentCentreLogistic.uri,
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