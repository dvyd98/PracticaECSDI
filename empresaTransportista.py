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

from rdflib import Namespace, Graph, Literal, term, RDFS
from rdflib.namespace import FOAF, RDF
from flask import Flask, request

from FlaskServer import shutdown_server
from Agent import Agent
from AgentUtil.Logging import config_logger
from ACLMessages import build_message, get_message_properties, send_message
from OntoNamespaces import ACL, DSO, RDF, REQ, XSD, OWL
from Agent import portAgentEmpresa

limR = [1, 6]  
    
# Configuration stuff
hostname = "localhost"
ip = 'localhost'

agn = Namespace("http://www.agentes.org#")
                
logger = config_logger(level=1)

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

EmpresaTransportista = Agent('EmpresaTransportista',
                             agn.EmpresaTransportista,
                             'http://%s:%d/comm' % (hostname, portAgentEmpresa),
                             'http://%s:%d/comm' % (hostname, portAgentEmpresa))

print(portAgentEmpresa)


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
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioEmpresa)
            
            if action == REQ.PeticioEmpresa:
                logger.info('Es demana preu')
                print('------------------------Rebem peticio------------------------')
                
                #obté pes, ciutat desti i plaç màxim d'entrega per ara HARDCODED
                
                content = msgdic['content']
                pes = gm.value(subject=content, predicate=REQ.QuantProductes)
                #pes = 2
                ciutatDesti = 'Barcelona'
                diaMaxim = '15/10/2021'
                #conjuntEmpreses = ['empresa_1', 'empresa_2', 'empresa_3', 'empresa_4', 'empresa_5']
                conjuntEmpreses = []
                conjuntEmpreses.append(str(gm.value(subject=content, predicate=REQ.CJE1)))
                conjuntEmpreses.append(str(gm.value(subject=content, predicate=REQ.CJE2)))
                conjuntEmpreses.append(str(gm.value(subject=content, predicate=REQ.CJE3)))
                conjuntEmpreses.append(str(gm.value(subject=content, predicate=REQ.CJE4)))
                conjuntEmpreses.append(str(gm.value(subject=content, predicate=REQ.CJE5)))
                
                gResposta = Graph()
                gResposta.bind('req', REQ)
                resposta_empresa = agn['resposta']
        
                xsddatatypes = {'s': XSD.string, 'i': XSD.int, 'f': XSD.float}
                result_properties = {'Nombre': 's',
                          'Precio': 'f'}
                
                print('HOLA1')
                
                for prop in result_properties:
                    if result_properties[prop] in ['s', 'i', 'f']:
                        gResposta.add((REQ[prop], RDF.type, OWL.DatatypeProperty))
                        gResposta.add((REQ[prop], RDFS.range, xsddatatypes[result_properties[prop]]))
                    else:
                        gResposta.add((REQ[prop], RDF.type, OWL.ObjectProperty))
                        gResposta.add((REQ[prop], RDFS.range, REQ[result_properties[prop]]))
    
                gResposta.add((REQ.RespostaEmpresa, RDF.type, OWL.Class))
                
                print('HOLA2')
                print('Conjunt empreses:', conjuntEmpreses)
                print('Tamany empreses:', len(conjuntEmpreses))
                
                for i in range(0, len(conjuntEmpreses)):
                    print('Estic dins: ', i)
                    preu = float(pes) * random.uniform(limR[0], limR[1])
                    print('PES CALCULAT')
                    gResposta.add((resposta_empresa, RDF.type, REQ.RespostaEmpresa))
                    print('Estic a dins del bucle:', conjuntEmpreses[i])
                    gResposta.add((resposta_empresa, REQ['Nombre'], Literal(conjuntEmpreses[i])))
                    print('Estic a dins del bucle2:', conjuntEmpreses[i])
                    gResposta.add((resposta_empresa, REQ['Precio'], Literal(preu)))
                    print(preu)
                    
#                for row in conjuntEmpreses:
#                    print('Estic dins bucle:', row)
#                    preu = pes * random.uniform(limR[0], limR[1])
#                    gResposta.add((resposta_empresa, RDF.type, REQ.RespostaEmpresa))
#                    gResposta.add((resposta_empresa, REQ['Nombre'], row))
#                    gResposta.add((resposta_empresa, REQ['Precio'], preu))
                
                print('------------------------Preparat per retornar resposta------------------------')
                
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
    app.run(host=hostname, port=portAgentEmpresa)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')

