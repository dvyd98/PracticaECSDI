# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 18:32:44 2020

@author: gpoltra98
"""

from multiprocessing import Process, Queue
import rdflib
import socket
import sys
import os
import datetime
sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, RDF, RDFS, FOAF, Literal
from flask import Flask, request

from ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from OntoNamespaces import ACL, DSO, RDF, PrOnt, REQ, PrOntPr, PrOntRes, CenOntRes, CenOntPr, CenOnt
from OntoNamespaces import LocCenOntRes, LocCenOntPr, LocCenOnt
from AgentUtil.Logging import config_logger
from math import sin, cos, sqrt, atan2, radians

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = 9000

#logger = config_logger(level=1, file="./logs/AgentCercador")
logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
PlataformaAgent = Agent('PlataformaAgent',
                        agn.PlataformaAgent,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))

#Cargar los centros logisticos
CentroLogistico1 = Agent('CentroLogistico1',
                        agn.cl1,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))
CentroLogistico2 = Agent('CentroLogistico2',
                        agn.cl2,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))
CentroLogistico3 = Agent('CentroLogistico3',
                        agn.cl3,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))
CentroLogistico4 = Agent('CentroLogistico4',
                        agn.cl4,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))

CentroLogistico5 = Agent('CentroLogistico5',
                        agn.cl5,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))


# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

def buscarCentreLogistic(nombreProd, quant, latClient, longClient):
    centresDisponibles = []
    #buscar els centres logistics que tinguin el producte disponible
    #query que retorni nombreProducte, nombreCentreLogistico, stock
    gProd=rdflib.Graph()
    gProd.parse("./Ontologies/centresProd.owl", format="xml")
        
    query = """SELECT ?nombre ?nombreCentreLogistic ?stock
                  WHERE {
                  ?a CenOntPr:nombre ?nombre .
                  ?a CenOntPr:nombreCentreLogistic ?nombreCentreLogistic .
                  ?a CenOntPr:stock ?stock .
                  }
                  """
    qres = gProd.query(query, initNs = {'CenOnt': CenOnt, 'CenOntPr': CenOntPr, 'CenOntRes' : CenOntRes})
    for row in qres:
        if row['nombre'] == nombreProd and row['stock'] >= quant:
            centresDisponibles.append(row['nombreCentreLogistic'])
    print('\n')       
    print('CentresDisponibles:', centresDisponibles)
    print('\n') 
    
    #dels disponibles, retornar el que estigui mes aprop del client
    gCent = rdflib.Graph()
    gCent.parse("./Ontologies/locCentres.owl", format="xml")
    
    query2 = """SELECT ?nombreCentreLogistic ?latitud ?longitud
                  WHERE {
                  ?a LocCenOntPr:latitud ?latitud .
                  ?a LocCenOntPr:nombreCentreLogistic ?nombreCentreLogistic .
                  ?a LocCenOntPr:longitud ?longitud .
                  }
                  """
    qres2 = gCent.query(query2, initNs = {'LocCenOnt': LocCenOnt, 'LocCenOntPr': LocCenOntPr, 'LocCenOntRes' : LocCenOntRes})
    d = 9999999.0
    R = 6373.0 #radi terra
    cl = None
    first = True
    #inicialitzar cl amb el primer element
    for row in qres2:
        if first:
            candidat = row['nombreCentreLogistic']
            if candidat in centresDisponibles:
                cl = row['nombreCentreLogistic']
                first = False
                break
    
    for row in qres2:
        latAux = row['latitud']
        longAux = row['longitud']
        lat1 = radians(float(latAux))
        lon1 = radians(float(longAux))
        lat2 = radians(float(latClient))
        lon2 = radians(float(longClient))
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        if distance < d:
            d = distance
            candidat = row['nombreCentreLogistic']
            if candidat in centresDisponibles:
                cl = candidat
    return cl

# Flask stuff
app = Flask(__name__)

@app.route("/")
def testing():
    return "testing connection"

@app.route("/comm")
def comunicacion():
    
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
        
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
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioCompra)
            
            #placeholder
            if action == REQ.PeticioCompra:
                logger.info('Processem la compra')
                #agafar el nom del producte i la quantitat, i la localitzacio del client
                content = msgdic['content']
                nombreProd = gm.value(subject=content, predicate=REQ.NombreProducte)
                print('HE agafat el nomProducte:', nombreProd)
                quant = gm.value(subject=content, predicate=REQ.QuantitatProducte)
                latClient = gm.value(subject=content, predicate=REQ.LatitudClient)
                longClient = gm.value(subject=content, predicate=REQ.LongitudClient)
                
                #cercar el millor centre logistic que tingui aquest producte
                cl = buscarCentreLogistic(nombreProd, quant, latClient, longClient)
                if cl is None:
                    logger.info('No hi ha aquest producte en ningun centre')
                    print('No hi ha aquest producte en ningun centre')
                    gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
                else:
                    print('El millor centre logistic es:', cl)
                    
                #cl sera el reciever del message
                
                #fer peticio enviament a centre logistic
                
                envGraph = Graph()
                envGraph.bind('req', REQ)
                env_obj = agn['delegarEnviament']
                envGraph.add((env_obj, RDF.type, REQ.PeticioEnviament)) 
                envGraph.add((env_obj, REQ.prod, nombreProd))
                envGraph.add((env_obj, REQ.quant, quant))
                
                missatgeEnviament = Graph()
                centreReciever = None
                if str(cl) == 'cl1':
                    centreReciever = CentroLogistico1
                elif str(cl) == 'cl2':
                    centreReciever = CentroLogistico2
                elif str(cl) == 'cl3':
                    centreReciever = CentroLogistico3
                elif str(cl) == 'cl4':
                    centreReciever = CentroLogistico4
                elif str(cl) == 'cl5':
                    centreReciever = CentroLogistico5
                    
                missatgeEnviament = build_message(envGraph,perf=ACL.request, sender=PlataformaAgent.uri, msgcnt=0, receiver=centreReciever.uri, content=env_obj)
                response = send_message(missatgeEnviament, centreReciever.address)
                
                #mirar el preu que envia centre logistic a la response i enviarlo al client
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
                                       sender=PlataformaAgent.uri,
                                       msgcnt=mss_cnt)
                else:
                    #Si ho es obtenim la performativa
                    if msgdic['performative'] != ACL.request:
                        #No es un request, not understood
                        logger.info('Msg no es una request')
                        gr = build_message(Graph(),
                                       ACL['not-understood'],
                                       sender=PlataformaAgent.uri,
                                       msgcnt=mss_cnt)
                    else:
                        #Mirem tipus request
                        content = msgdic['content']
                        action = gm.value(subject=content, predicate=RDF.type)
                        print('La action es:', action)
                        print('La action hauria de ser:', REQ.PeticioCompra)
                        
                        #placeholder
                        if action == REQ.confirmarEnviament:
                            content = msgdic['content']
                            preuEnvio = gm.value(subject=content, predicate=REQ.preuEnvioProd)
                            #enviar factura a client
                        else:
                            logger.info('Es una request que no entenem')
                            gr = build_message(Graph(),
                                       ACL['not-understood'],
                                       sender=PlataformaAgent.uri,
                                       msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=PlataformaAgent.uri,
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
    print('Hola')
    pass

if __name__ == '__main__':
      
    #print('BuscarCentreLogistic:')
    #print(buscarCentreLogistic('nombre_Blender_0FUO3Q', 1, 42.20064, 2.19033))
    
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
    
    