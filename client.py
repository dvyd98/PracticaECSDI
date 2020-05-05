# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 02:43:59 2020

@author: Dvyd
"""


from multiprocessing import Process, Queue
import socket

import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, Literal, term
from rdflib.namespace import FOAF, RDF
from flask import Flask

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message
from OntoNamespaces import ACL, DSO, RDF, PrOnt, PrOntPr, PrOntRes, REQ
from Agent import portGestorPlataforma, portCerca

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = 9000

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

PlataformaAgent = Agent('PlataformaAgent',
                        agn.PlataformaAgent,
                        'http://%s:%d/comm' % (hostname, portGestorPlataforma),
                        'http://%s:%d/Stop' % (hostname, portGestorPlataforma))

AgentCercador = Agent('AgentCercador',
                       agn.AgentCercador,
                       'http://%s:%d/comm' % (hostname, portCerca),
                       'http://%s:%d/Stop' % (hostname, portCerca))

Client = Agent('Client', agn.Client, '', '')

latClient = 42.20064
longClient = 2.19033
print("Instruccions disponibles")
print("1 - Buscar un producte")
print("2 - Comprar un producte")
print("3 - Modificar localitzacio client (Predefinida: 42.2, 2.19)")
var_input = input("Introdueix instruccio:")
while(var_input != "1" and var_input != "2"):
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
            contentPeticioCompra.add((compra_obj, REQ.NombreProducte, Literal(var_nomP)))
        var_Q = input("Introdueix quantitat del producte (0-5):")
        if (var_Q != ""):
            contentPeticioCompra.add((compra_obj, REQ.QuantitatProducte, Literal(var_Q)))
        contentPeticioCompra.add((compra_obj, REQ.LatitudClient, Literal(latClient)))
        contentPeticioCompra.add((compra_obj, REQ.LongitudClient, Literal(longClient)))
        messageCompra = Graph()
        messageCompra = build_message(contentPeticioCompra, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=compra_obj)
        print('EnviemPeticioCompra')
        response = send_message(messageCompra, PlataformaAgent.address)
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
    if (var_input == "3"):
         print("Introdueix la latitud i longitud usant punts i no comes (ex: 40.4555).")
         var_lat = input("Introdueix la latitud:")
         if var_lat != "":
             latClient = float(var_lat)
         var_long = input("Introdueix la longitud:")
         if var_long != "":
             longClient = float(var_long)
         