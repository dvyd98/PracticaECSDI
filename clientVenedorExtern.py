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
from Agent import portVenedorExtern

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = portVenedorExtern

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentVenedorExtern = Agent('AgentCercador',
                       agn.AgentVenedorExtern,
                       'http://%s:%d/comm' % (hostname, portVenedorExtern),
                       'http://%s:%d/Stop' % (hostname, portVenedorExtern))

Client = Agent('Client', agn.Client, '', '')
'''
content = Graph()
content.bind('req', REQ)
cerca_obj = agn['producte']

product_obj = REQ.Properties + '_properties'

content.add((cerca_obj, RDF.type, REQ.AfegirProducteExtern))
content.add((cerca_obj, REQ.Properties, product_obj))

#passem cerca hardcoded ( de moment xd)
content.add((product_obj, REQ.Nombre, Literal("Test")))
content.add((product_obj, REQ.Precio, Literal(10)))
content.add((product_obj, REQ.Peso, Literal(50.1)))
content.add((product_obj, REQ.Marca, Literal("Marca_Computer_RSBDXK")))
content.add((product_obj, REQ.Categoria, Literal("Blender")))

#content.add((filters_obj, REQ.Nombre, Literal("Blender")))
#content.add((filters_obj, REQ.Precio, Literal(500)))
#content.add((filters_obj, REQ.TieneMarca, Literal("Marca_Blender_1UI0FG")))
ofile  = open('request.owl', "w")
encoding = 'iso-8859-1'
ofile.write(str(content.serialize(), encoding))
ofile.close()


g = Graph()
#construim el missatge com una req al agent cercador
g = build_message(content, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentVenedorExtern.uri, content=cerca_obj)
#enviem el msg
response = send_message(g, AgentVenedorExtern.address)
'''
print("Instruccions disponibles")
print("1 - Afegir un producte extern a la botiga")
var_input = input("Introdueix instruccio: ")
while(var_input != "1" and var_input != "2" and var_input != "3"):
    print ("Instruccio desconeguda")
    var_input = input("Introdueix instruccio: ")

if (var_input == "1"):
    content = Graph()
    content.bind('req', REQ)
    cerca_obj = agn['producte']
    
    product_obj = REQ.Properties + '_properties'
    
    content.add((cerca_obj, RDF.type, REQ.AfegirProducteExtern))
    content.add((cerca_obj, REQ.Properties, product_obj))
    
    print("Introdueix les propietats del producte que vols afegir")
    var_filtre = input("Introdueix nom del producte: ")
    while(var_filtre == ""):
        var_filtre = input("Aquest camp es obligatori: ")
    content.add((product_obj, REQ.Nombre, Literal(var_filtre)))
    var_filtre = input("Introdueix preu del producte: ")
    while(var_filtre == ""):
        var_filtre = input("Aquest camp es obligatori: ")
    content.add((product_obj, REQ.Precio, Literal(int(var_filtre))))
    var_filtre = input("Introdueix pes del producte:")
    while(var_filtre == ""):
        var_filtre = input("Aquest camp es obligatori: ")
    content.add((product_obj, REQ.Peso, Literal(float(var_filtre))))
    var_filtre = input("Introdueix marca del producte: ")
    while(var_filtre == ""):
        var_filtre = input("Aquest camp es obligatori: ")
    content.add((product_obj, REQ.Marca, Literal(var_filtre)))
    var_filtre = input("Introdueix categoria del producte: ")
    while(var_filtre == ""):
        var_filtre = input("Aquest camp es obligatori: ")
    content.add((product_obj, REQ.Categoria, Literal(var_filtre)))
    
    g = Graph()
    #construim el missatge com una req al agent cercador
    g = build_message(content, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentVenedorExtern.uri, content=cerca_obj)
    #enviem el msg
    response = send_message(g, AgentVenedorExtern.address)
    
if (var_input == "2"):
    content = Graph()
    content.bind('req', REQ)
    cerca_obj = agn['producte']
    
    product_obj = REQ.Properties + '_properties'
        
    content.add((cerca_obj, RDF.type, REQ.AfegirMarca))
    content.add((cerca_obj, REQ.Properties, product_obj))
    
    print("Introdueix les propietats de la marca que vols afegir")
    var_filtre = input("Introdueix nom de la marca: ")
    content.add((product_obj, REQ.Nombre, Literal(var_filtre)))
    
    g = Graph()
    #construim el missatge com una req al agent cercador
    g = build_message(content, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentVenedorExtern.uri, content=cerca_obj)
    #enviem el msg
    response = send_message(g, AgentVenedorExtern.address)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        