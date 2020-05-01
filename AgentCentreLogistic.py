# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 13:51:30 2020

@author: pball
"""

#Template
from multiprocessing import Process, Queue
import socket

import rdflib
import sys
import os
sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, RDF
from flask import Flask, request

from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from AgentUtil.Logging import config_logger

from ACLMessages import build_message, get_message_properties, send_message
from OntoNamespaces import ACL, EmOnt, EmOntPr, EmOntRes, REQ

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

#AgentCentreLogistic = None
AgentCentreLogistic = Agent('CentreLogistic1',
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
        
        conjuntEmpreses = []
        
        gProd=rdflib.Graph()
        gProd.parse("./Ontologies/empresesTransp.owl", format="xml")
        
        query = """SELECT?nombre
                    WHERE {
                            ?a EmOntPr:nombre ?nombre .
                    }
                """
                  
        qres = gProd.query(query, initNs = {'EmOnt': EmOnt, 'EmOntPr': EmOntPr, 'EmOntRes' : EmOntRes})
        for row in qres:
            conjuntEmpreses.append(row['nombre'])
            
        print('\n')       
        print('conjuntEmpreses:', conjuntEmpreses)
        print('\n')  
        
        #construeix el graph per passar a l'empresa
        contentPeticioEmpresa = Graph()
        contentPeticioEmpresa.bind('req', REQ)
        enviament_obj = agn['enviament']
        
        contentPeticioEmpresa.add((enviament_obj, RDF.type, REQ.PeticioEmpresa))
        contentPeticioEmpresa.add((enviament_obj, REQ.PesProductes, pes))
        contentPeticioEmpresa.add((enviament_obj, REQ.CiutatDesti, ciutatDesti))
        contentPeticioEmpresa.add((enviament_obj, REQ.DiaMaxim, diaMaxim))
        contentPeticioEmpresa.add((enviament_obj, REQ.ConjuntEmpreses, conjuntEmpreses))
        
        messageEmpresa = Graph()
        messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=AgentCentreLogistic.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        
        #envia missatge a l'Agent EmpresaTransportista
        response = send_message(messageEmpresa, EmpresaTransportista.address)
        
        #obtenir la resposta de l'Agent EmpresaTransportista
        query = """
              SELECT ?nombre ?precio 
              WHERE {
              ?a REQ:Nombre ?nombre .
              ?a REQ:Precio ?precio .
              }
              """
        qres = response.query(query, initNs = {'REQ': REQ})  
        
        #busca el preu de la empresa més baix
        first = True
        preuMesBaix = None
        nomEmpresaAmbPreuMesBaix = None
        
        for row in qres:
            if first:
                nomEmpresaAmbPreuMesBaix = row['nombre']
                preuMesBaix = row['precio']
                first = False
            else:
                if preuMesBaix > row['precio']:
                    nomEmpresaAmbPreuMesBaix = row['nombre']
                    preuMesBaix = row['precio']
            
                    
        result = Graph()
        result.bind('req', REQ)
        result_obj = agn['result']
        
        result.add((result_obj, RDF.type, REQ.ResultEnviament))
        result.add((result_obj, REQ.NomEmpresa, nomEmpresaAmbPreuMesBaix))
        result.add((result_obj, REQ.Preu, preuMesBaix))
        
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
    
#    AgentCentreLogistic = Agent('CentreLogistic1',
#                       agn.AgentCentreLogistic,
#                       'http://%s:%d/comm' % (hostname, port),
#                       'http://%s:%d/Stop' % (hostname, port))
#    return
    pass

#def agentbehavior2(cola):
#    
#    AgentCentreLogistic = Agent('CentreLogistic2',
#                       agn.AgentCentreLogistic,
#                       'http://%s:%d/comm' % (hostname, port+1),
#                       'http://%s:%d/Stop' % (hostname, port+1))
#    return

if __name__ == '__main__':
    
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    #ab2 = Process(target=agentbehavior2, args=(cola1,))
    ab1.start()
    #ab2.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    #ab2.join()
    print('The End')