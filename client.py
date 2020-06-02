# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 02:43:59 2020

@author: Dvyd
"""


from multiprocessing import Process, Queue, Value
import sys
import os
import random
import string
import json
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
from Agent import portGestorPlataforma, portCerca, portClient, portAgentTesorer

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

AgentTesorer = Agent('AgentTesorer',
                             agn.AgentTesorer,
                             'http://%s:%d/comm' % (hostname, portAgentTesorer),
                             'http://%s:%d/comm' % (hostname, portAgentTesorer))

dsgraph = Graph()

cola1 = Queue()
consolaEnUs = Value('i', 0)

# Flask stuff
app = Flask(__name__)

def eliminarRegistres():
    registreCompres = {}
    with open('registreCompres.txt', 'w') as outfile:
        json.dump(registreCompres, outfile)
    print("registres de compres eliminats...")
    
    registreCerca = {}
    with open('registreCerca.txt', 'w') as outfile:
        json.dump(registreCerca, outfile)
    print("registres de cerques eliminats...")
    
    registreFeedback = {}
    registreFeedback['Blender'] = 0
    registreFeedback['Computer'] = 0
    registreFeedback['Phone'] = 0
    with open('registreFeedback.txt', 'w') as outfile:
        json.dump(registreFeedback, outfile)
    print("registres de feedback eliminats...")

def iniciarConnexioAmbPlataforma():
    conGraph = Graph()
    conGraph.bind('req', REQ)
    con_obj = agn['recomanacio']
    conGraph.add((con_obj, RDF.type, REQ.PeticioIniciarConnexio)) 
    conGraph.add((con_obj, REQ.iniciar, Literal(True)))
        
    missatgeEnviament = build_message(conGraph,perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=con_obj)
    response = send_message(missatgeEnviament, PlataformaAgent.address)

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
                           sender=Client.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=Client.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('-------------------La action es:', action)
#            print('La action hauria de ser:', REQ.PeticioCompra)
            
            #placeholder
            if action == REQ.ConfirmacioAmbFactura:
                content = msgdic['content']
                print('-------------------FACTURA--------------------')
                nombreProd = gm.value(subject=content, predicate=REQ.nomP)
                preuProd = gm.value(subject=content, predicate=REQ.preuProd)
                preuEnv = gm.value(subject=content, predicate=REQ.preuEnviament)
                preuTotal = gm.value(subject=content, predicate=REQ.preuTotal)
                nomEmpresa = gm.value(subject=content, predicate=REQ.nomEmpresa)
                idCompra = gm.value(subject=content, predicate=REQ.idCompra)
                print('NomProducte:',nombreProd)
                print('PreuEnviament:',preuEnv)
                print('PreuProducte:',preuProd)
                print('PreuTotal:',preuTotal)
                print('NomEmpresa:',nomEmpresa)
                print('idCompra:', idCompra)
                print('FinalitzemPeticioCompra')
                
                print("Proces pagament")
                consolaEnUs.value = 1
                compte = ""
                compte = input("Introdueix el teu compte")
                while compte == "":
                    compte = input("Introdueix un compte vàlid")
                
                consolaEnUs.value = 0
                
                conGraph = Graph()
                conGraph.bind('req', REQ)
                con_obj = agn['transferencia']
                conGraph.add((con_obj, RDF.type, REQ.PeticioTransferenciaAPlataforma)) 
                conGraph.add((con_obj, REQ.diners, Literal(preuTotal)))
                conGraph.add((con_obj, REQ.compte, Literal(compte)))
                conGraph.add((con_obj, REQ.np, Literal(nombreProd)))
        
                missatgeEnviament = build_message(conGraph,perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentTesorer.uri, content=con_obj)
                response = send_message(missatgeEnviament, AgentTesorer.address)
                
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
                
            elif action == REQ.PeticioRecomanacio:
                content = msgdic['content']
                consolaEnUs.value = 1
                print('-------------------RECOMANACIO--------------------')
                nombreProd = gm.value(subject=content, predicate=REQ.prod)
                print("Potser t'interessa el producte " + str(nombreProd))
                consolaEnUs.value = 0
                
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=Client.uri,
                           msgcnt=mss_cnt)
            
            elif action == REQ.PeticioFeedback:
                content = msgdic['content']
                pucObtenirFeedback = gm.value(subject=content, predicate=REQ.obtenirFeedcack)
                pucObtenirFeedback = bool(pucObtenirFeedback)
                
                if pucObtenirFeedback == True:
                    print('-------------------FEEDBACK D\'USUARI--------------------')
                    print("p - Phone")
                    print("v - Blender")
                    print("c - Computer")
                    
                    consolaEnUs.value = 1
                    
                    var_marca = input("Introdueix la categoria que has comprat recentment")
                    while var_marca != "p" and var_marca != "v" and var_marca != "c":
                        var_marca = input("No es una marca. Introdueix una marca:")
                    
                    var_puntuacio = input("Introdueix una valoracio s, a, b")
                    while var_puntuacio != "s" and var_puntuacio != "a" and var_puntuacio != "b":
                        var_puntuacio = input("Valor invalid: Introdueix la puntuacio una altre vegada:")
                    
                    consolaEnUs.value = 0
                    
                    if var_marca == "p":
                        var_marca = "Phone"
                    elif var_marca == "v":
                        var_marca = "Blender"
                    else:
                        var_marca = "Computer"
                        
                    punts = 0
                        
                    if var_puntuacio == "s":
                        punts = 10
                    elif var_puntuacio == "a":
                        punts = 5
                    else:
                        punts = 0
                        
                    contentFeed = Graph()
                    contentFeed.bind('req', REQ)
                    feed_obj = agn['feed']
                    contentFeed.add((feed_obj, RDF.type, REQ.RespostaFeedback))
                    contentFeed.add((feed_obj, REQ.marca, Literal(var_marca)))
                    contentFeed.add((feed_obj, REQ.puntuacio, Literal(punts)))
                    
                    gr = build_message(contentFeed,
                           ACL['inform-done'],
                           sender=PlataformaAgent.uri,
                           msgcnt=mss_cnt)
                    
            elif action == REQ.rebreDiners:
                content = msgdic['content']
                diners = gm.value(subject=content, predicate=REQ.diners)
                        
                print("Hem rebut diners: ", diners)
    
                gr = build_message(Graph(),
                       ACL['inform-done'],
                       sender=Client.uri,
                       msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=Client.uri,
                           msgcnt=mss_cnt)
#                return gr.serialize(format='xml')
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


def agentbehavior1(q, fileno, consolaEnUs):
    """
    Un comportamiento del agente

    :return:
    """
    sys.stdin = os.fdopen(fileno)
    iniciarConnexioAmbPlataforma()
    print("Instruccions disponibles")
    print("1 - Buscar un producte")
    print("2 - Comprar un producte")
    print("3 - Modificar localitzacio client (Predefinida: 42.2, 2.19)")
    print("4 - Devolucio de un producte")
    print("5 - Eliminar registres de compra, cerca i feedback")

    letters = string.ascii_lowercase
    
    latClient = 42.2
    longClient = 2.19

    while True:
        while consolaEnUs.value > 0:
            asd = 0
        
        var_input = input("Introdueix instruccio: ")
        while(var_input != "1" and var_input != "2" and var_input != "3" and var_input != "4" and var_input != "5"):
            print ("Instruccio desconeguda")
            var_input = input("Introdueix instruccio: ")
        
        if (var_input == "1"):
            content = Graph()
            content.bind('req', REQ)
            cerca_obj = agn['cerca']
            
            filters_obj = REQ.Filters + '_filters'
            
            content.add((cerca_obj, RDF.type, REQ.PeticioCerca))
            content.add((cerca_obj, REQ.Filters, filters_obj))
            
            print("Introdueix els filtres desitjats, apreta enter sense escriure res per no filtrar (Tambe pots escrire un '-' per no filtrar)")
            var_filtre = input("Introdueix categoria del producte: ")
            if (var_filtre != "" and var_filtre != "-"):   
                content.add((filters_obj, REQ.Categoria, Literal(var_filtre)))
            var_filtre = input("Introdueix nom del producte: ")
            if (var_filtre != "" and var_filtre != "-"): 
                content.add((filters_obj, REQ.Nombre, Literal(var_filtre)))
            var_filtre = input("Introdueix preu maxim del producte: ")
            if (var_filtre != "" and var_filtre != "-"): 
                content.add((filters_obj, REQ.Precio, Literal(int(var_filtre))))
            var_filtre = input("Introdueix marca del producte: ")
            if (var_filtre != "" and var_filtre != "-"): 
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
            idCompra = ''.join(random.choice(letters) for i in range(32))
            print("Introdueix el nom del producte i la quantitat que vols comprar")
            #enviar peticio compra
        
            contentPeticioCompra = Graph()
            contentPeticioCompra.bind('req', REQ)
            compra_obj = agn['compra']
            contentPeticioCompra.add((compra_obj, RDF.type, REQ.PeticioCompra))
            var_nomP = input("Introdueix el nom del producte: ")
            if (var_nomP != ""):
                contentPeticioCompra.add((compra_obj, REQ.NombreProducte, Literal(str(var_nomP))))
            var_Q = input("Introdueix quantitat del producte (0-5): ")
            if (var_Q != ""):
                contentPeticioCompra.add((compra_obj, REQ.QuantitatProducte, Literal(int(var_Q))))
            contentPeticioCompra.add((compra_obj, REQ.LatitudClient, Literal(float(latClient))))
            contentPeticioCompra.add((compra_obj, REQ.LongitudClient, Literal(float(longClient))))
            contentPeticioCompra.add((compra_obj, REQ.idCompra, Literal(str(idCompra))))
            messageCompra = Graph()
            messageCompra = build_message(contentPeticioCompra, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=compra_obj)
            print('EnviemPeticioCompra')
            response = send_message(messageCompra, PlataformaAgent.address)
            
            query = """
                SELECT ?resposta
                WHERE {
                    ?a REQ:resposta ?resposta
                }
                    """
            qres = response.query(query, initNs = {'REQ': REQ})
            respostaCL = ""
            for row in qres:
                respostaCL = str(row['resposta'])
            print(respostaCL)
        if var_input == "3":
            print("Introdueix la latitud i longitud usant punts i no comes (ex: 40.4555).")
            var_lat = input("Introdueix la latitud: ")
            if var_lat != "":
                latClient = float(var_lat)
            var_long = input("Introdueix la longitud: ")
            if var_long != "":
                longClient = float(var_long)
        if var_input == "4":
            idC = ""
            dies = 0
            print("Introdueix el id de compra, rao de devolucio i quants dies fa que et va arribar el producte")
            var_id = input("Introduir el id de compra:")
            if var_id != "":
                idC = var_id
            var_dies = input("Si la rao de devolucio es un producte defectuos o equivocat, introdueix un 0. Si la rao es que el producte no satisà les vostres espectatives, introdueix el numero de dies que fa des de que us va arribar el producte.")
            if var_dies != "":
                dies = var_dies
            
            contentDevolucio = Graph()
            contentDevolucio.bind('req', REQ)
            dev_obj = agn['devolucio']
            contentDevolucio.add((dev_obj, RDF.type, REQ.PeticioDevolucio))
            contentDevolucio.add((dev_obj, REQ.idCompra, Literal(str(idC))))
            contentDevolucio.add((dev_obj, REQ.dies, Literal(dies)))
            
            messagePeticio = Graph()
            messagePeticio = build_message(contentDevolucio, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=dev_obj)
            print('EnviemPeticioDevolucio')
            response = send_message(messagePeticio, PlataformaAgent.address)
            
            query = """
                          SELECT ?respostaDev
                          WHERE {
                          ?a REQ:respostaDev ?respostaDev .
                          }
                          """
            qres = response.query(query, initNs = {'REQ': REQ})
            
            for row in qres:
                print(row['respostaDev'])
        if var_input == "5":
            eliminarRegistres()
             
    pass

if __name__ == '__main__':
      
    #print('BUSCAR PREU PRODUCTE:')
    #print(buscarPreuProducte(Literal('nombre_Blender_0XF8I9')))
    #buscarCentreLogistic(Literal("nombre_Blender_0XF8I9"), Literal(1), Literal(42.2), Literal(2.19))
    #Nombre_Blender_06KF10
    q = Queue()
    fn = sys.stdin.fileno()
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(q,fn,consolaEnUs))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=portClient)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')