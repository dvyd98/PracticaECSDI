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
from OntoNamespaces import ACL, DSO, RDF, XSD, OWL, PrOnt, PrOntPr, PrOntRes, REQ, CenOnt, CenOntPr, CenOntRes
from AgentUtil.Logging import config_logger
from urllib.parse import urlparse
from pathlib import PurePosixPath
from Agent import portVenedorExtern

__author__ = 'javier'


# Configuration stuff
hostname = "localhost"
ip = 'localhost'

#logger = config_logger(level=1, file="./logs/AgentCercador")
logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentVenedorExtern = Agent('AgentCercador',
                       agn.AgentVenedorExtern,
                       'http://%s:%d/comm' % (hostname, portVenedorExtern),
                       'http://%s:%d/Stop' % (hostname, portVenedorExtern))

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
    def addMarca():
        content = msgdic['content']
        
        properties_obj = gm.value(subject=content, predicate=REQ.Properties)
        
        nombre = gm.value(subject=properties_obj, predicate=REQ.Nombre)
        
        g=Graph()
        g.parse("./Ontologies/product.owl", format="xml")
        g.add((PrOntRes[nombre], RDF.type, PrOnt.Marca))
        
        g.add((PrOntRes[nombre], PrOntPr.nombre, nombre))
        
        ofile  = open('./Ontologies/product.owl', "w")
        encoding = 'iso-8859-1'
        ofile.write(str(g.serialize(), encoding))
        ofile.close()
        
        return g
    
    def addProducte():
        global mss_cnt
        
        content = msgdic['content']
        
        properties_obj = gm.value(subject=content, predicate=REQ.Properties)
        
        nombre = gm.value(subject=properties_obj, predicate=REQ.Nombre)
        precio = gm.value(subject=properties_obj, predicate=REQ.Precio)
        peso = gm.value(subject=properties_obj, predicate=REQ.Peso)
        marca = gm.value(subject=properties_obj, predicate=REQ.Marca)
        categoria = gm.value(subject=properties_obj, predicate=REQ.Categoria)
        
        g=Graph()
        g.parse("./Ontologies/product.owl", format="xml")
        g.add((PrOntRes[nombre], RDF.type, PrOnt[categoria]))
        
        g.add((PrOntRes[nombre], PrOntPr['nombre'], nombre))
        g.add((PrOntRes[nombre], PrOntPr['precio'], precio))
        g.add((PrOntRes[nombre], PrOntPr['peso'], peso))
        g.add((PrOntRes[nombre], PrOntPr['esExterno'], Literal(1)))
        g.add((PrOntRes[nombre], PrOntPr['tieneMarca'], PrOntRes[marca]))
        
        g.add((PrOntRes[marca], RDF.type, PrOnt.Marca))
        
        g.add((PrOntRes[marca], PrOntPr.nombre, marca))
        
        ofile  = open('./Ontologies/product.owl', "w")
        encoding = 'iso-8859-1'
        ofile.write(str(g.serialize(), encoding))
        ofile.close()
        
        g=Graph()
        g.parse("./Ontologies/centresProd.owl", format="xml")
        g.add((CenOntRes[nombre], RDF.type, CenOnt['Producte_CentreLogistic1']))
        
        g.add((CenOntRes[nombre], CenOntPr['nombre'], nombre))
        g.add((CenOntRes[nombre], CenOntPr['nombreCentreLogistic'], Literal('cl1')))
        g.add((CenOntRes[nombre], CenOntPr['stock'], Literal(5)))
        
        ofile  = open('./Ontologies/centresProd.owl', "w")
        encoding = 'iso-8859-1'
        ofile.write(str(g.serialize(), encoding))
        ofile.close()
        
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
        
        result_obj = REQ[nombre]
        gresult.add((result_obj, RDF.type, REQ.Result))
        gresult.add((result_obj, REQ['Nombre'], nombre))
        gresult.add((result_obj, REQ['Precio'], precio))
        gresult.add((result_obj, REQ['Peso'], peso))
        gresult.add((result_obj, REQ['esExterno'], Literal(1)))
        gresult.add((result_obj, REQ['Marca'], marca))
        
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
                           sender=AgentVenedorExtern.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentVenedorExtern.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            
            #placeholder
            if action == REQ.AfegirProducteExtern:
                logger.info('Processem la peticio')
                gr = addProducte()
                
            elif action == REQ.AfegirMarca:
                gr = addMarca()
            elif action == REQ.rebreDiners:
                content = msgdic['content']
                diners = gm.value(subject=content, predicate=REQ.diners)
                
                print("Hem rebut diners: ", diners)

                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=AgentVenedorExtern.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgentVenedorExtern.uri,
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
    app.run(host=hostname, port=portVenedorExtern)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')

