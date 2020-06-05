# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 18:32:44 2020

@author: gpoltra98

"""
from multiprocessing import Process, Queue, Value
from time import sleep
import rdflib
import socket
import sys
import os
import datetime
import random
import string
import json
import threading

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from rdflib import Namespace, Graph, RDF, RDFS, Literal
from flask import Flask, request

from ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from OntoNamespaces import ACL, DSO, RDF, PrOnt, REQ, PrOntPr, PrOntRes, CenOntRes, CenOntPr, CenOnt
from OntoNamespaces import LocCenOntRes, LocCenOntPr, LocCenOnt
from AgentUtil.Logging import config_logger
from math import sin, cos, sqrt, atan2, radians
from Agent import portGestorPlataforma, portCentreLogistic,  portCentreLogistic2,  portCentreLogistic3,  portCentreLogistic4,  portCentreLogistic5, portClient, portAgentTesorer

# Configuration stuff
hostname = "localhost"
ip = 'localhost'
port = 9070

#logger = config_logger(level=1, file="./logs/AgentCercador")
logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
PlataformaAgent = Agent('PlataformaAgent',
                        agn.PlataformaAgent,
                        'http://%s:%d/comm' % (hostname, portGestorPlataforma),
                        'http://%s:%d/Stop' % (hostname, portGestorPlataforma))

Client = Agent('Client', 
               agn.Client,
               'http://%s:%d/comm' % (hostname, portClient), 
               'http://%s:%d/Stop' % (hostname, portClient))

#Cargar los centros logisticos
CentroLogistico1 = Agent('CentroLogistico1',
                        agn.cl1,
                        'http://%s:%d/comm' % (hostname, portCentreLogistic),
                        'http://%s:%d/Stop' % (hostname, portCentreLogistic))
CentroLogistico2 = Agent('CentroLogistico2',
                        agn.cl2,
                        'http://%s:%d/comm' % (hostname, portCentreLogistic2),
                        'http://%s:%d/Stop' % (hostname, portCentreLogistic2))
CentroLogistico3 = Agent('CentroLogistico3',
                        agn.cl3,
                        'http://%s:%d/comm' % (hostname, portCentreLogistic3),
                        'http://%s:%d/Stop' % (hostname, portCentreLogistic3))
CentroLogistico4 = Agent('CentroLogistico4',
                        agn.cl4,
                        'http://%s:%d/comm' % (hostname, portCentreLogistic4),
                        'http://%s:%d/Stop' % (hostname, portCentreLogistic4))

CentroLogistico5 = Agent('CentroLogistico5',
                        agn.cl5,
                        'http://%s:%d/comm' % (hostname, portCentreLogistic5),
                        'http://%s:%d/Stop' % (hostname, portCentreLogistic5))

AgentTesorer = Agent('AgentTesorer',
                             agn.AgentTesorer,
                             'http://%s:%d/comm' % (hostname, portAgentTesorer),
                             'http://%s:%d/comm' % (hostname, portAgentTesorer))


# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

idCompra = Literal("0")

def obtenirFeedback():
    print("Esperant temps per enviar feedback")
    sleep(20)
    
    print("Ha passat el temps, preparant peticio feedback...")
    feedGraph = Graph()
    feedGraph.bind('req', REQ)
    feed_obj = agn['feedback']
    feedGraph.add((feed_obj, RDF.type, REQ.PeticioFeedback)) 
    feedGraph.add((feed_obj, REQ.obtenirFeedcack, Literal(True)))
        
    missatgeFeedback = build_message(feedGraph,perf=ACL.request, sender=PlataformaAgent.uri, msgcnt=0, receiver=Client.uri, content=feed_obj)
    response = send_message(missatgeFeedback, Client.address) 
    
    print("Rebem resposta feedback del client")
    query = """
                      SELECT ?marca ?puntuacio 
                      WHERE {
                      ?a REQ:marca ?marca .
                      ?a REQ:puntuacio ?puntuacio .
                      }
                      """
    qres = response.query(query, initNs = {'REQ': REQ})
    
    marca = ''
    puntuacio = 1
    
    print("Guardant el feedback per millorar recomanacions...")
    for row in qres:
        marca = marca + str(row['marca'])
        puntuacio = int(row['puntuacio'])

    print("Marca:", marca)
    print("Puntuacio: ", puntuacio)
    
    feedback = {}
    with open('registreFeedback.txt') as json_file:
        feedback = json.load(json_file)
    
    print('El feedback guardat es:', feedback)
    feedback[marca] = int(feedback[marca]) + puntuacio
    
    with open('registreFeedback.txt', 'w') as outfile:
        json.dump(feedback, outfile)
    

def obtenirProducteRandom(marca):
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
    
    productes = []
    for row in qres:
        if str(row['nombreMarca']).find(str(marca)) >= 0:
            productes.append(str(row['nombre']))
        
    return random.choice(productes)
    

def obtenirRecomenacio():
    registreCompres = {}
    registreCerca = {}
    marques = {}
    
    with open('registreFeedback.txt') as json_file:
        marques = json.load(json_file)
    
    with open('registreCompres.txt') as json_file:
        registreCompres = json.load(json_file)
    
    for idC in registreCompres:
        for infoC in registreCompres[idC]:
            nomP = str(infoC['nomP'])
            if nomP.find("Blender") >= 0:
                marques["Blender"] = marques["Blender"] + 1
            elif nomP.find("Computer") >= 0:
                marques["Computer"] = marques["Computer"] + 1
            elif nomP.find("Phone") >= 0:
                marques["Phone"] = marques["Phone"] + 1
    
    with open('registreCerca.txt') as json_file:
        registreCerca = json.load(json_file)
    
    print("CATEGORIES:", marques)
    for np in registreCerca:
        for infoC in registreCerca[np]:
            marca = str(infoC['marca'])
            if marca.find("Blender") >= 0:
                marques["Blender"] = marques["Blender"] + 1
            elif marca.find("Computer") >= 0:
                marques["Computer"] = marques["Computer"] + 1
            elif marca.find("Phone") >= 0:
                marques["Phone"] = marques["Phone"] + 1
            
    print("CATEGORIES:", marques)
    if len(marques) > 0:
        sorted_mc = sorted(marques.items(), key=lambda kv: kv[1])
        return sorted_mc[len(marques)-1][0]
    else:
        return "Blender"

def enviarRecomenacio(connexioClientIniciada):
    print('Intent de connexio: ', connexioClientIniciada.value)
    if connexioClientIniciada.value > 0:
        marca = obtenirRecomenacio()
        
        producteRec = obtenirProducteRandom(marca)
        
        recGraph = Graph()
        recGraph.bind('req', REQ)
        rec_obj = agn['recomanacio']
        recGraph.add((rec_obj, RDF.type, REQ.PeticioRecomanacio)) 
        recGraph.add((rec_obj, REQ.prod, Literal(producteRec)))
        
        missatgeEnviament = build_message(recGraph,perf=ACL.request, sender=PlataformaAgent.uri, msgcnt=0, receiver=Client.uri, content=rec_obj)
        response = send_message(missatgeEnviament, Client.address)  
    threading.Timer(80.0, enviarRecomenacio, args=(connexioClientIniciada,)).start()
            

def eliminarRegistreCerca(idCompra):
    registreCompres = {}
    idCompra = str(idCompra)
    with open('registreCompres.txt') as json_file:
        registreCompres = json.load(json_file)
        
    dic = dict(registreCompres)
    del dic[idCompra]
    
    with open('registreCompres.txt', 'w') as outfile:
        json.dump(dic, outfile)
        
    
def cercarCompra(idCompra):
    registreCompres = {}
    idCompra = str(idCompra)
    preu = -1.0
    
    with open('registreCompres.txt') as json_file:
        registreCompres = json.load(json_file)
    
    for idC in registreCompres:
        if idC == idCompra:
            for infoC in registreCompres[idC]:
                preu = float(infoC['preuT'])
    
    return preu

def registrarCompra(idCompra, nombreProd, preuTot):
    registreCompres = {}
    idCompra = str(idCompra)
    
    print('Preparat per el registre')
    
    with open('registreCompres.txt') as json_file:
        registreCompres = json.load(json_file)
        
    print('Registre obert')
    
    registreCompres[idCompra] = []
    registreCompres[idCompra].append({
            'nomP': str(nombreProd),
            'preuT': str(preuTot)
            })

    with open('registreCompres.txt', 'w') as outfile:
        json.dump(registreCompres, outfile)
    
    print('Registre reescrit')

def buscarPesProducte(nombreProd):
    pes = Literal(float(0))
    g=rdflib.Graph()
    g.parse("./Ontologies/product.owl", format="xml")
    
    query = """SELECT ?nombre ?peso
              WHERE {
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:peso ?peso .
              
              }
              """
    
    qres = g.query(query, initNs = {'PrOnt': PrOnt, 'PrOntPr': PrOntPr, 'PrOntRes' : PrOntRes})
    for row in qres:
        if row['nombre'] == nombreProd:
            pes = row['peso']
            break
    
    return pes

def buscarPreuProducte(nombreProd):
    preu = Literal(0)
    g=rdflib.Graph()
    g.parse("./Ontologies/product.owl", format="xml")
    
    query = """SELECT ?nombre ?precio
              WHERE {
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:precio ?precio .
              
              }
              """
    
    qres = g.query(query, initNs = {'PrOnt': PrOnt, 'PrOntPr': PrOntPr, 'PrOntRes' : PrOntRes})
    for row in qres:
        if row['nombre'] == nombreProd:
            preu = row['precio']
            break
    
    return preu

def crearRespostaPeticioCompra(cl):
    res = ""
    if cl is None:
        res = "Aquest producte amb aquesta quantitat no es troben disponibles en ningun centre logístic"
    else:
        res = "S'ha enviat el producte al centre logistic: " + str(cl)
    return res

def getStock(nombreProd):
    stock = Literal(1)
    g=rdflib.Graph()
    g.parse("./Ontologies/centresProd.owl", format="xml")
    
    query = """SELECT ?nombre ?stock
              WHERE {
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:stock ?stock .
              
              }
              """
    
    qres = g.query(query, initNs = {'PrOnt': CenOnt, 'PrOntPr': CenOntPr, 'PrOntRes' : CenOntRes})
    for row in qres:
        if row['nombre'] == nombreProd:
            preu = row['precio']
            break
    
    return preu

def actualitzarStock(cl, nombreProd):
    cl = str(cl)
    nombreProd = str(nombreProd)
    instancia = nombreProd + '_' + cl[-1:]
    
    g=Graph()
    g.parse("./Ontologies/centresProd.owl", format="xml")
    gStock = g.triples((CenOntRes[instancia], CenOntPr['stock'], None))
    stock = Literal(1)
    for _, _, o in gStock:
        stock = o
    g.set((CenOntRes[instancia], CenOntPr['stock'], Literal(int(stock)-1)))
    
    ofile  = open('./Ontologies/centresProd.owl', "w")
    encoding = 'iso-8859-1'
    ofile.write(str(g.serialize(), encoding))
    ofile.close()

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
        elif str(row['nombre']) == nombreProd and int(row['stock']) >= quant:
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
    print("El definitiu:", cl)
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
                quant = gm.value(subject=content, predicate=REQ.QuantitatProducte)
                latClient = gm.value(subject=content, predicate=REQ.LatitudClient)
                longClient = gm.value(subject=content, predicate=REQ.LongitudClient)
                idCompra = gm.value(subject=content, predicate=REQ.idCompra)
                
                #cercar el millor centre logistic que tingui aquest producte
                cl = buscarCentreLogistic(nombreProd, quant, latClient, longClient)
                resCL = crearRespostaPeticioCompra(cl)
                if cl is None:
                    logger.info('No hi ha aquest producte en ningun centre')
                    print('No hi ha aquest producte en ningun centre')
                    resGraph = Graph()
                    resGraph.bind('req', REQ)
                    res_obj = agn['factura']
                    resGraph.add((res_obj, RDF.type, REQ.ConfirmacioAmbResposta))
                    resGraph.add((res_obj, REQ.resposta, Literal(resCL)))
                    gr = build_message(resGraph,
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
                    return gr.serialize(format='xml')
                else:
                    print('El millor centre logistic es:', cl)
                    
                #cl sera el reciever del message
                #fer peticio enviament a centre logistic
                actualitzarStock(cl, nombreProd)
                
                envGraph = Graph()
                envGraph.bind('req', REQ)
                env_obj = agn['delegarEnviament']
                pes = buscarPesProducte(nombreProd)
                envGraph.add((env_obj, RDF.type, REQ.PeticioEnviament)) 
                envGraph.add((env_obj, REQ.prod, nombreProd))
                envGraph.add((env_obj, REQ.pes, pes))
                envGraph.add((env_obj, REQ.idCompra, idCompra))
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
                    
                #per ara enviarem sempre al mateix centre (segona entrega)
                #centreReciever = CentroLogistico3
                    
                print('\n')
                print('PREPAREM PER DELEGAR ENVIAMENT')
                print('\n')
                missatgeEnviament = build_message(envGraph,perf=ACL.request, sender=PlataformaAgent.uri, msgcnt=0, receiver=centreReciever.uri, content=env_obj)
                response = send_message(missatgeEnviament, centreReciever.address)
                
                resGraph = Graph()
                resGraph.bind('req', REQ)
                res_obj = agn['factura']
                resGraph.add((res_obj, RDF.type, REQ.ConfirmacioAmbResposta))
                resGraph.add((res_obj, REQ.resposta, Literal(resCL)))
                gr = build_message(resGraph,
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
                return gr.serialize(format='xml')
        
            elif action == REQ.IniciarEnviament:
                content = msgdic['content']
                
                #response = gm.value(subject=content, predicate=REQ.PreuEnviament)
                
                print('\n')
                print('REBEM PREU ENVIAMENT')
                print('\n')
                
                nomE = gm.value(subject=content, predicate=REQ.NomEmpresa)
                preuEnv = gm.value(subject=content, predicate=REQ.Preu)
                idCompra = gm.value(subject=content, predicate=REQ.idCompra)
                nombreProd = gm.value(subject=content, predicate=REQ.NomProd)
                quant = gm.value(subject=content, predicate=REQ.quant)
                
                print('El preu enviament es:', preuEnv)
                print('El nom empresa es:', nomE)
                print('El idCompra es:', idCompra)
                print('El nom prod es:', nombreProd)
                print('La quant del producte es:', quant)
                
                preuProducte = buscarPreuProducte(nombreProd)
                
                print('El preu producte es:', preuProducte)
                
                preuProducte = Literal(int(preuProducte)*int(quant))
                preuTot = Literal(float(preuEnv)+int(preuProducte*int(quant)))
                
                print('Registrant compra...')
                registrarCompra(idCompra, nombreProd, preuTot)
                
                print('Preparant factura...')
                
                contentFactura = Graph()
                contentFactura.bind('req', REQ)
                factura_obj = agn['factura']
                contentFactura.add((factura_obj, RDF.type, REQ.ConfirmacioAmbFactura))
                contentFactura.add((factura_obj, REQ.nomP, nombreProd))
                contentFactura.add((factura_obj, REQ.preuEnviament, Literal(preuEnv)))
                contentFactura.add((factura_obj, REQ.preuProd, preuProducte))
                contentFactura.add((factura_obj, REQ.preuTotal, preuTot))
                contentFactura.add((factura_obj, REQ.nomEmpresa, nomE))
                #El centre logistic hauria de passar el idCompra!!!!!!!!!!!!!!
                contentFactura.add((factura_obj, REQ.idCompra, Literal(idCompra)))
                
                print('Factura creada')
                
                missatgeFactura = build_message(contentFactura,perf=ACL.request, sender=PlataformaAgent.uri, msgcnt=0, receiver=Client.uri, content=factura_obj)
                response = send_message(missatgeFactura, Client.address)
                
                print("Cridar obtenir feedback...")
                obtenirFeedback()
                
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
            
            elif action == REQ.PeticioDevolucio:
                content = msgdic['content']
                idCompra = gm.value(subject=content, predicate=REQ.idCompra)
                dies = gm.value(subject=content, predicate=REQ.dies)
                print("SENSE TRANSFORMACIO: ", dies)
                print("AMB TRANSFORMACIO: ", int(dies))
                resposta = ""
                
                print("Preparat per gestionar peticio devolucio")
                
                if int(dies) >= 0 and int(dies) <= 15:
                    preu = cercarCompra(idCompra)
                    print("Compra cercada")
                    if preu < 0.0:
                        resposta = "NO es possible procedir amb la devolució ja que no existeix un registre d'aquesta compra"
                    else:
                        eliminarRegistreCerca(idCompra)
                        preu = str(preu)
                        resposta = "Peticio ACCEPTADA. L'empresa transportista recollirà el producte en el mateix lloc que l'entrega en un plaç màxim de 3 dies. Es procedirà a fer un reembolsament de "+preu
                        
                        recGraph = Graph()
                        recGraph.bind('req', REQ)
                        rec_obj = agn['recomanacio']
                        recGraph.add((rec_obj, RDF.type, REQ.PeticioTransferenciaAClient)) 
                        recGraph.add((rec_obj, REQ.diners, Literal(preu)))
                        
                        print("Preparant comunicacio amb Tresorer...")
                        
                        missatgeEnviament = build_message(recGraph,perf=ACL.request, sender=PlataformaAgent.uri, msgcnt=0, receiver=AgentTesorer.uri, content=rec_obj)
                        response = send_message(missatgeEnviament, AgentTesorer.address)
                else:
                    resposta = "NO es possible procedir amb la devolució, el període màxim per a la devolució és de 15 dies."
                    
                contentDev = Graph()
                contentDev.bind('req', REQ)
                devo_obj = agn['dev']
                contentDev.add((devo_obj, RDF.type, REQ.RespostaDevolucio))
                contentDev.add((devo_obj, REQ.respostaDev, Literal(resposta)))
                
                print('Resposta devolucio preparada per enviar')
                
                gr = build_message(contentDev,
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
            elif action == REQ.PeticioIniciarConnexio:
                iniC = gm.value(subject=content, predicate=REQ.iniciar)
                
#                global connexiolientIniciada
                if iniC:
                    connexioClientIniciada.value = 1
                print('ESTAT DE CONNEXIO: ', connexioClientIniciada.value)
                
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
            
            elif action == REQ.rebreDiners:
                content = msgdic['content']
                diners = gm.value(subject=content, predicate=REQ.diners)
                
                print("Hem rebut diners: ", diners)

                gr = build_message(Graph(),
                           ACL['inform-done'],
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


def agentbehavior1(cola, connexioClientIniciada):
    """
    Un comportamiento del agente

    :return:
    """
    
    enviarRecomenacio(connexioClientIniciada)
    pass

if __name__ == '__main__':
#    actualitzarStock("cl1", "Nombre_Blender_06KF10")
      
    #print('BUSCAR PREU PRODUCTE:')
    #print(buscarPreuProducte(Literal('nombre_Blender_4ARQ13')))
    #buscarCentreLogistic(Literal("nombre_Blender_4ARQ13"), Literal(1), Literal(42.2), Literal(2.19))
    connexioClientIniciada = Value('i', 0)
    
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,connexioClientIniciada))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=portGestorPlataforma)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
    
    