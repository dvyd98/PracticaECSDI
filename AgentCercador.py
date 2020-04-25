# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

@author: javier
"""

from multiprocessing import Process, Queue
import socket
import sys
import os
import datetime
sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, RDF, RDFS, Literal, term
from flask import Flask, request

from ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from OntoNamespaces import ACL, DSO, RDF, XSD, OWL, PrOnt, PrOntPr, PrOntRes, REQ
from AgentUtil.Logging import config_logger
from urllib.parse import urlparse
from pathlib import PurePosixPath

__author__ = 'javier'


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

AgentCercador = Agent('AgentCercador',
                       agn.AgentCercador,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

# placeholder, to be completed
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)


# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

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
    def getProductes():
        global mss_cnt
        #Obtenir parametres de cerca (filtre + keyword)
        content = msgdic['content']
        print(content)
        filters_obj = gm.value(subject=content, predicate=REQ.Filters)
        print(filters_obj)
        categoria_filter = gm.value(subject=filters_obj, predicate=REQ.Categoria)
        nombre_filter = gm.value(subject=filters_obj, predicate=REQ.Nombre)
        precio_filter = gm.value(subject=filters_obj, predicate=REQ.Precio)
        marca_filter = gm.value(subject=filters_obj, predicate=REQ.TieneMarca)
        
        g=Graph()
        g.parse("./Ontologies/product.owl", format="xml")
        query = """
              SELECT ?nombre ?precio ?nombreMarca ?categoria
              WHERE {
              ?a rdf:type ?categoria .
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:precio ?precio .
              ?a PrOntPr:tieneMarca ?b .
              ?b PrOntPr:nombre ?nombreMarca .
              }
              """
        qres = g.query(query, initNs = {'PrOnt': PrOnt, 'PrOntPr': PrOntPr, 'PrOntRes' : PrOntRes})  
            
        
        gresult = Graph()
        gresult.bind('req', REQ)
        cerca_obj = agn['cerca']
        xsddatatypes = {'s': XSD.string, 'i': XSD.int, 'f': XSD.float}
        result_properties = {'Marca': 's',
                          'Precio': 'i',
                          'Peso': 'f',
                          'Categoria': 's',
                          'Nombre': 's'}
        for prop in result_properties:
            if result_properties[prop] in ['s', 'i', 'f']:
                gresult.add((REQ[prop], RDF.type, OWL.DatatypeProperty))
                gresult.add((REQ[prop], RDFS.range, xsddatatypes[result_properties[prop]]))
            else:
                gresult.add((REQ[prop], RDF.type, OWL.ObjectProperty))
                gresult.add((REQ[prop], RDFS.range, REQ[result_properties[prop]]))
        
        gresult.add((REQ.Result, RDF.type, OWL.Class))
        for row in qres:
            result_obj = REQ[row['nombre']]
            count = 0
            i = 0
            while(i < 4):
                product_pr = row[i]
                if (i == 0):
                    if (nombre_filter != None):
                        if (nombre_filter in product_pr):
                            count += 1
                    else:
                        count += 1
                if (i == 1):
                    if (precio_filter != None):
                        if (product_pr <= precio_filter):
                            count += 1
                    else:
                        count += 1
                if (i == 2):
                    if (marca_filter != None):
                        if (marca_filter in product_pr):
                            count += 1
                    else:
                        count += 1
                if (i == 3):
                    if (categoria_filter != None):
                        categoriaURI = urlparse(row['categoria']).path
                        categoria = PurePosixPath(categoriaURI).parts[2]
                        if (categoria_filter in categoria):
                            count += 1
                    else:
                        count += 1
                        
                i += 1
            
            if (count == 4):
                #print(row[0], row[1], row[2], row[3])
                #t = term.URIRef(PrOntPr.nombre + "_" + row[0])
                #gresult.add((cerca_obj, REQ.Results, result_obj))
                gresult.add((result_obj, RDF.type, REQ.Result))
                gresult.add((result_obj, REQ['Nombre'], row[0]))
                gresult.add((result_obj, REQ['Precio'], row[1]))
                gresult.add((result_obj, REQ['Marca'], row[2]))
                gresult.add((result_obj, REQ['Categoria'], Literal(PurePosixPath(urlparse(row[3]).path).parts[2])))
            
            
        
        return gresult
    
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
                           sender=AgentCercador.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentCercador.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            
            #placeholder
            if action == REQ.PeticioCerca:
                logger.info('Processem la cerca')
                getProductes()
                gr = getProductes()
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentCercador.uri,
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

