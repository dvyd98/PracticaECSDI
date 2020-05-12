# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 02:43:59 2020

@author: Dvyd
"""


from multiprocessing import Process, Queue
import sys
import os
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
from Agent import portGestorPlataforma, portCerca, portClient

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = portClient

logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

Client = Agent('Client', 
               agn.Client,
               'http://%s:%d/comm' % (hostname, portClient), 
               'http://%s:%d/Stop' % (hostname, portClient))

PlataformaAgent = Agent('PlataformaAgent',
                        agn.PlataformaAgent,
                        'http://%s:%d/comm' % (hostname, portGestorPlataforma),
                        'http://%s:%d/Stop' % (hostname, portGestorPlataforma))
AgentCercador = Agent('AgentCercador',
                       agn.AgentCercador,
                       'http://%s:%d/comm' % (hostname, portCerca),
                       'http://%s:%d/Stop' % (hostname, portCerca))

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
            if action == REQ.ConfirmacioAmbFactura:
                a = 0
            
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


def agentbehavior1(q, fileno):
    """
    Un comportamiento del agente

    :return:
    """
    sys.stdin = os.fdopen(fileno)
    print("Instruccions disponibles")
    print("1 - Buscar un producte")
    print("2 - Comprar un producte")
    print("3 - Modificar localitzacio client (Predefinida: 42.2, 2.19)")
    latClient = 42.2
    longClient = 2.19
    var_input = input("Introdueix instruccio:")
    while(var_input != "1" and var_input != "2" and var_input != "3"):
        print ("Instruccio desconeguda")
        var_input = input("Introdueix instruccio:")
        
    if (var_input == "1"):
        content = Graph()
        content.bind('req', REQ)
        cerca_obj = agn['cerca']
        
        filters_obj = REQ.Filters + '_filters'
        
        content.add((cerca_obj, RDF.type, REQ.PeticioCerca))
        content.add((cerca_obj, REQ.Filters, filters_obj))
        
        print("Introdueix els filtres desitjats, apreta enter sense escriure res per no filtrar")
        var_filtre = input("Introdueix categoria del producte:")
        if (var_filtre != ""):   
            content.add((filters_obj, REQ.Categoria, Literal(var_filtre)))
        var_filtre = input("Introdueix nom del producte:")
        if (var_filtre != ""): 
            content.add((filters_obj, REQ.Nombre, Literal(var_filtre)))
        var_filtre = input("Introdueix preu maxim del producte:")
        if (var_filtre != ""): 
            content.add((filters_obj, REQ.Precio, Literal(int(var_filtre))))
        var_filtre = input("Introdueix marca del producte:")
        if (var_filtre != ""): 
            content.add((filters_obj, REQ.TieneMarca, Literal(var_filtre)))
        ofile  = open('request.owl', "w")
        encoding = 'iso-8859-1'
        ofile.write(str(content.serialize(), encoding))
        ofile.close()
        
        g = Graph()
        #construim el missatge com una req al agent cercador
        g = build_message(content, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentCercador.uri, content=cerca_obj)
        #enviem el msg
        response = send_message(g, AgentCercador.address)
        #mirem que hem rebut 
        query = """
        SELECT ?nombre ?precio ?marca ?categoria
        WHERE {
                ?a REQ:Nombre ?nombre .
                ?a REQ:Precio ?precio .
                ?a REQ:Marca ?marca .
                ?a REQ:Categoria ?categoria .
                }
        """
        qres = response.query(query, initNs = {'REQ': REQ})  
        for row in qres:
            print("-------------------------------------------")
            print("Nom: " + row['nombre'])
            print("Preu:" + row['precio'])
            print("Marca: " + row['marca'])
            print("Categoria: " + row['categoria'])
        #ho guardem
        ofile  = open('output.owl', "w")
        encoding = 'iso-8859-1'
        ofile.write(str(response.serialize(), encoding))
        ofile.close()
        
    if (var_input == "2"):
        print("Introdueix el nom del producte i la quantitat que vols comprar")
        #enviar peticio compra
    
        contentPeticioCompra = Graph()
        contentPeticioCompra.bind('req', REQ)
        compra_obj = agn['compra']
        contentPeticioCompra.add((compra_obj, RDF.type, REQ.PeticioCompra))
        var_nomP = input("Introdueix el nom del producte:")
        if (var_nomP != ""):
            contentPeticioCompra.add((compra_obj, REQ.NombreProducte, Literal(str(var_nomP))))
        var_Q = input("Introdueix quantitat del producte (0-5):")
        if (var_Q != ""):
            contentPeticioCompra.add((compra_obj, REQ.QuantitatProducte, Literal(int(var_Q))))
        contentPeticioCompra.add((compra_obj, REQ.LatitudClient, Literal(float(latClient))))
        contentPeticioCompra.add((compra_obj, REQ.LongitudClient, Literal(float(longClient))))
        messageCompra = Graph()
        messageCompra = build_message(contentPeticioCompra, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=compra_obj)
        print('EnviemPeticioCompra')
        response = send_message(messageCompra, PlataformaAgent.address)
        #(aixo haura d'anar en el commm del client)
        print('Resposta: ', response)
        query = """
        SELECT ?nomP ?preuEnviament ?preuProd ?preuTotal ?nomEmpresa
        WHERE {
                ?a REQ:nomP ?nomP .
                ?a REQ:preuEnviament ?preuEnviament .
                ?a REQ:preuProd ?preuProd .
                ?a REQ:preuTotal ?preuTotal .
                ?a REQ:nomEmpresa ?nomEmpresa .
                }
        """
        qres = response.query(query, initNs = {'REQ': REQ})
        print('-------------------FACTURA--------------------')
        for row in qres:
            print('NomProducte:',row['nomP'])
            print('PreuEnviament:',row['preuEnviament'])
            print('PreuProducte:',row['preuProd'])
            print('PreuTotal:',row['preuTotal'])
            print('NomEmpresa:',row['nomEmpresa'])
            print('FinalitzemPeticioCompra')
    if var_input == "3":
        print("Introdueix la latitud i longitud usant punts i no comes (ex: 40.4555).")
        var_lat = input("Introdueix la latitud:")
        if var_lat != "":
            latClient = float(var_lat)
        var_long = input("Introdueix la longitud:")
        if var_long != "":
            longClient = float(var_long)
             
    pass

if __name__ == '__main__':
      
    #print('BUSCAR PREU PRODUCTE:')
    #print(buscarPreuProducte(Literal('nombre_Blender_4ARQ13')))
    #buscarCentreLogistic(Literal("nombre_Blender_4ARQ13"), Literal(1), Literal(42.2), Literal(2.19))
    q = Queue()
    fn = sys.stdin.fileno()
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(q,fn))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=portClient)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')