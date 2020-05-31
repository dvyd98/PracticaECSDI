# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 13:51:30 2020

@author: pball
"""

#Template
from multiprocessing import Process, Queue, Value, Array, Manager
import socket

import rdflib
import sys
import os

#Per fer timer
import threading

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from ctypes import c_char_p
from rdflib import Namespace, Graph, RDF, RDFS, FOAF, Literal
from flask import Flask, request

from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
from AgentUtil.Logging import config_logger

from ACLMessages import build_message, get_message_properties, send_message
from OntoNamespaces import ACL, EmOnt, EmOntPr, EmOntRes, REQ, OWL, XSD
from Agent import portCentreLogistic, portCentreLogistic2, portCentreLogistic3, portCentreLogistic4, portCentreLogistic5, portAgentEmpresa, portGestorPlataforma

__author__ = 'pball'


# Configuration stuff
hostname = "localhost"
ip = 'localhost'

#logger = config_logger(level=1, file="./logs/AgentCentreLogistic")
logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

#Lot de producte Centre1
L_centre1 = []
NomsLot_centre1 = []
Quantitats_centre1 = []
pesTotalLot_centre1 = Value('d', 0.0)

#Lot de producte Centre2
L_centre2 = []
NomsLot_centre2 = []
Quantitats_centre2 = []
pesTotalLot_centre2 = Value('d', 0.0)

#Lot de producte Centre3
L_centre3 = []
NomsLot_centre3 = []
Quantitats_centre3 = []
pesTotalLot_centre3 = Value('d', 0.0)

#Lot de producte Centre4
L_centre4 = []
NomsLot_centre4 = []
Quantitats_centre4 = []
pesTotalLot_centre4 = Value('d', 0.0)

#Lot de producte Centre5
L_centre5 = []
NomsLot_centre5 = []
Quantitats_centre5 = []
pesTotalLot_centre5 = Value('d', 0.0)


# Datos del Agente

#AgentCentreLogistic = None
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

EmpresaTransportista = Agent('EmpresaTransportista',
                             agn.EmpresaTransportista,
                             'http://%s:%d/comm' % (hostname, portAgentEmpresa),
                             'http://%s:%d/comm' % (hostname, portAgentEmpresa))

PlataformaAgent = Agent('PlataformaAgent',
                        agn.PlataformaAgent,
                        'http://%s:%d/comm' % (hostname, portGestorPlataforma),
                        'http://%s:%d/Stop' % (hostname, portGestorPlataforma))

# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)
app2 = Flask(__name__)
app3 = Flask(__name__)
app4 = Flask(__name__)
app5 = Flask(__name__)

def negociarTransport(pes, ciutatDesti, diaMaxim, LotProductes, NomsLot, Quantitats, centre):
        
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
        print('len conjuntEmpreses:', len(conjuntEmpreses))
        print('\n')  
        
        #construeix el graph per passar a l'empresa
        contentPeticioEmpresa = Graph()
        contentPeticioEmpresa.bind('req', REQ)
        enviament_obj = agn['enviament']
        
        contentPeticioEmpresa.add((enviament_obj, RDF.type, REQ.PeticioEmpresa))
        contentPeticioEmpresa.add((enviament_obj, REQ.QuantProductes, Literal(pes)))
        contentPeticioEmpresa.add((enviament_obj, REQ.CiutatDesti, Literal(ciutatDesti)))
        contentPeticioEmpresa.add((enviament_obj, REQ.DiaMaxim, Literal(diaMaxim)))
        e = str(conjuntEmpreses[0])
        contentPeticioEmpresa.add((enviament_obj, REQ.CJE1, Literal(e)))
        e = str(conjuntEmpreses[1])
        contentPeticioEmpresa.add((enviament_obj, REQ.CJE2, Literal(e)))
        e = str(conjuntEmpreses[2])
        contentPeticioEmpresa.add((enviament_obj, REQ.CJE3, Literal(e)))
        e = str(conjuntEmpreses[3])
        contentPeticioEmpresa.add((enviament_obj, REQ.CJE4, Literal(e)))
        e = str(conjuntEmpreses[4])
        contentPeticioEmpresa.add((enviament_obj, REQ.CJE5, Literal(e)))
        
        
        messageEmpresa = Graph()
        if centre == 1:
            messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=CentroLogistico1.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        elif centre == 2:
            messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=CentroLogistico2.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        elif centre == 3:
            messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=CentroLogistico3.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        elif centre == 4:
            messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=CentroLogistico4.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        else:
            messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=CentroLogistico5.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
            
            
        #envia missatge a l'Agent EmpresaTransportista
        response = send_message(messageEmpresa, EmpresaTransportista.address)
        
        print('REBEM RESPOSTA DE EMPRESA TRANSPORTISTA')
        
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
            print('Nom empresa:', row['nombre'])
            print('Preu empresa:', row['precio'])
            if first:
                nomEmpresaAmbPreuMesBaix = row['nombre']
                preuMesBaix = row['precio']
                first = False
            else:
                if preuMesBaix > row['precio']:
                    nomEmpresaAmbPreuMesBaix = row['nombre']
                    preuMesBaix = row['precio']
            
                    
                    
        print('El preu mes baix:', preuMesBaix)
        print('Nom de la empresa amb preu més baix:', nomEmpresaAmbPreuMesBaix)
        
        #INFORMAR EMPRESA GUANYADORA
        gRespostaEmp = Graph()
        gRespostaEmp.bind('req', REQ)
        empresa_guanyadora = agn['empresa_guany']
        
        gRespostaEmp.add((empresa_guanyadora, RDF.type, REQ.EmpresaGuanyadora))
        gRespostaEmp.add((empresa_guanyadora, REQ.NomEmpresa, Literal(nomEmpresaAmbPreuMesBaix)))
        
        messagePerEmpresa = Graph()
        
        if centre == 1:
            messagePerEmpresa = build_message(gRespostaEmp, perf=ACL.request, sender=CentroLogistico1.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=empresa_guanyadora)
        elif centre == 2:
            messagePerEmpresa = build_message(gRespostaEmp, perf=ACL.request, sender=CentroLogistico2.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=empresa_guanyadora)
        elif centre == 3:
            messagePerEmpresa = build_message(gRespostaEmp, perf=ACL.request, sender=CentroLogistico3.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=empresa_guanyadora)
        elif centre == 4:
            messagePerEmpresa = build_message(gRespostaEmp, perf=ACL.request, sender=CentroLogistico4.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=empresa_guanyadora)
        else:
            messagePerEmpresa = build_message(gRespostaEmp, perf=ACL.request, sender=CentroLogistico5.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=empresa_guanyadora)
        
        send_message(messagePerEmpresa, EmpresaTransportista.address)
        
        #PETICIONS A GESTOR PLATAFORMA
        gResposta = Graph()
        gResposta.bind('req', REQ)
        resposta_enviament = agn['resposta_env']
        
        for i in range(0, len(LotProductes)):
                    print('Estic dins: ', i)
                    preu = float(preuMesBaix.strip('"'))/len(LotProductes)
                    print('Preu CALCULAT')
                    gResposta.add((resposta_enviament, RDF.type, REQ.IniciarEnviament))
                    print('Estic a dins del bucle:', LotProductes[i])
                    gResposta.add((resposta_enviament, REQ.idCompra, Literal(LotProductes[i])))
                    print('Estic a dins del bucle2:', LotProductes[i])
                    gResposta.add((resposta_enviament, REQ.Preu, Literal(preu)))
                    print(preu)       
                    gResposta.add((resposta_enviament, REQ.NomEmpresa, Literal(nomEmpresaAmbPreuMesBaix)))
                    gResposta.add((resposta_enviament, REQ.NomProd, Literal(NomsLot[i])))
                    print(NomsLot[i]) 
                    gResposta.add((resposta_enviament, REQ.quant, Literal(Quantitats[i])))
                    print(Quantitats[i]) 
                    
                    messagePerPlataforma = Graph()
                    
                    if centre == 1:
                        messagePerPlataforma = build_message(gResposta, perf=ACL.request, sender=CentroLogistico1.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta_enviament)
                    elif centre == 2:
                        messagePerPlataforma = build_message(gResposta, perf=ACL.request, sender=CentroLogistico2.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta_enviament)
                    elif centre == 3:
                        messagePerPlataforma = build_message(gResposta, perf=ACL.request, sender=CentroLogistico3.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta_enviament)
                    elif centre == 4:
                        messagePerPlataforma = build_message(gResposta, perf=ACL.request, sender=CentroLogistico4.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta_enviament)
                    else:
                        messagePerPlataforma = build_message(gResposta, perf=ACL.request, sender=CentroLogistico5.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta_enviament)
                        
                    #envia missatge a l'Agent EmpresaTransportista
                    send_message(messagePerPlataforma, PlataformaAgent.address)
        

      
    
def comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats, centre):    
      
  if centre == 1:
      
      global pesTotalLot_centre1
      global L_centre1
      global NomsLot_centre1
      global Quantitats_centre1
      
      pesTotal = pesTotalLot_centre1
      LotProductes = L_centre1
      NomsLot = NomsLot_centre1
      Quantitats = Quantitats_centre1
      
  elif centre == 2:
      
      global pesTotalLot_centre2
      global L_centre2
      global NomsLot_centre2
      global Quantitats_centre2
      
      pesTotal = pesTotalLot_centre2
      LotProductes = L_centre2
      NomsLot = NomsLot_centre2
      Quantitats = Quantitats_centre2
      
  elif centre == 3:
      
      global pesTotalLot_centre3
      global L_centre3
      global NomsLot_centre3
      global Quantitats_centre3
      
      pesTotal = pesTotalLot_centre3
      LotProductes = L_centre3
      NomsLot = NomsLot_centre3
      Quantitats = Quantitats_centre3
      
  elif centre == 4:
      
      global pesTotalLot_centre4
      global L_centre4
      global NomsLot_centre4
      global Quantitats_centre4
      
      pesTotal = pesTotalLot_centre4
      LotProductes = L_centre4
      NomsLot = NomsLot_centre4
      Quantitats = Quantitats_centre4
      
  else:
      
      global pesTotalLot_centre5
      global L_centre5
      global NomsLot_centre5
      global Quantitats_centre5
      
      pesTotal = pesTotalLot_centre5
      LotProductes = L_centre5
      NomsLot = NomsLot_centre5
      Quantitats = Quantitats_centre5
      
  print("El pes del centre",centre, "és: ", pesTotal.value)
  #De moment sempre que hi hagi un producte al lot ja fa la petició
  if pesTotal.value > 700:
      ciutatDesti = 'Barcelona'
      diaMaxim = '15/10/2021'
      
      print('Preparar enviar peticio a empresa transportista')
      negociarTransport(pesTotal.value, ciutatDesti, diaMaxim, LotProductes, NomsLot, Quantitats, centre)         
      print('-----------EMPRESSA NEGOCIADA-------------')
      
      pesTotal.value = 0
      print("El pesTotal ha canviat a",pesTotal.value)
      del LotProductes[:]
      del NomsLot[:]
      del Quantitats[:]

  threading.Timer(20.0, comprovarLotComplet, args=(pesTotal, LotProductes, NomsLot, Quantitats, centre,)).start()
  print("S'està comprovant si tenim un lot complet i podem començar la negociació")
      
      
  

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
    global pesTotalLot_centre1
    
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
                           sender=CentroLogistico1.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico1.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioEmpresa)
            
            if action == REQ.PeticioEnviament:
                logger.info('Es delega enviament')
                print('Rebut peticio de delegar enviament')
                
                content = msgdic['content']
                pes = gm.value(subject=content, predicate=REQ.pes)
                CompraId = gm.value(subject=content, predicate=REQ.idCompra)
                nomProd = gm.value(subject=content, predicate=REQ.prod)
                quant = gm.value(subject=content, predicate=REQ.quant)
                #ciutatDesti = gm.value(subject=content, predicate=REQ.CiutatDesti)
                #diaMaxim = gm.value(subject=content, predicate=REQ.DiaMaxim)
                #Afegir producte al lot
                
                L_centre1.append(CompraId)
                pesTotalLot_centre1.value += float(pes)*float(quant)
                NomsLot_centre1.append(nomProd)
                Quantitats_centre1.append(quant)
                
                #escollir millor empresa
                print('El pes rebut es: ', pes, '\n')
                print('El pes total del lot es: ', pesTotalLot_centre1.value, '\n')
            
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=CentroLogistico1.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico1.uri,
                           msgcnt=mss_cnt)        
        mss_cnt += 1
        return gr.serialize(format='xml')

    pass

@app2.route("/comm")
def comunicacion2():
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
    global pesTotalLot_centre2
    
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
                           sender=CentroLogistico2.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico2.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioEmpresa)
            
            if action == REQ.PeticioEnviament:
                logger.info('Es delega enviament')
                print('Rebut peticio de delegar enviament')
                
                content = msgdic['content']
                pes = gm.value(subject=content, predicate=REQ.pes)
                CompraId = gm.value(subject=content, predicate=REQ.idCompra)
                nomProd = gm.value(subject=content, predicate=REQ.prod)
                quant = gm.value(subject=content, predicate=REQ.quant)
                #ciutatDesti = gm.value(subject=content, predicate=REQ.CiutatDesti)
                #diaMaxim = gm.value(subject=content, predicate=REQ.DiaMaxim)
                #Afegir producte al lot
                
                L_centre2.append(CompraId)
                pesTotalLot_centre2.value += float(pes)*float(quant)
                NomsLot_centre2.append(nomProd)
                Quantitats_centre2.append(quant)
                
                #escollir millor empresa
                print('El pes rebut centre 2 es: ', pes, '\n')
                print('El pes total del lot es: ', pesTotalLot_centre2.value, '\n')
            
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=CentroLogistico2.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico2.uri,
                           msgcnt=mss_cnt)        
        mss_cnt += 1
        return gr.serialize(format='xml')

    pass

@app3.route("/comm")
def comunicacion3():
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
    global pesTotalLot_centre3
    
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
                           sender=CentroLogistico3.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico3.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioEmpresa)
            
            if action == REQ.PeticioEnviament:
                logger.info('Es delega enviament')
                print('Rebut peticio de delegar enviament')
                
                content = msgdic['content']
                pes = gm.value(subject=content, predicate=REQ.pes)
                CompraId = gm.value(subject=content, predicate=REQ.idCompra)
                nomProd = gm.value(subject=content, predicate=REQ.prod)
                quant = gm.value(subject=content, predicate=REQ.quant)
                #ciutatDesti = gm.value(subject=content, predicate=REQ.CiutatDesti)
                #diaMaxim = gm.value(subject=content, predicate=REQ.DiaMaxim)
                #Afegir producte al lot
                
                L_centre3.append(CompraId)
                pesTotalLot_centre3.value += float(pes)*float(quant)
                NomsLot_centre3.append(nomProd)
                Quantitats_centre3.append(quant)
                
                #escollir millor empresa
                print('El pes rebut centre 3 es: ', pes, '\n')
                print('El pes total del lot es: ', pesTotalLot_centre3.value, '\n')
            
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=CentroLogistico3.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico3.uri,
                           msgcnt=mss_cnt)        
        mss_cnt += 1
        return gr.serialize(format='xml')

    pass

@app4.route("/comm")
def comunicacion4():
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
    global pesTotalLot_centre4
    
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
                           sender=CentroLogistico4.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico4.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioEmpresa)
            
            if action == REQ.PeticioEnviament:
                logger.info('Es delega enviament')
                print('Rebut peticio de delegar enviament')
                
                content = msgdic['content']
                pes = gm.value(subject=content, predicate=REQ.pes)
                CompraId = gm.value(subject=content, predicate=REQ.idCompra)
                nomProd = gm.value(subject=content, predicate=REQ.prod)
                quant = gm.value(subject=content, predicate=REQ.quant)
                #ciutatDesti = gm.value(subject=content, predicate=REQ.CiutatDesti)
                #diaMaxim = gm.value(subject=content, predicate=REQ.DiaMaxim)
                #Afegir producte al lot
                
                L_centre4.append(CompraId)
                pesTotalLot_centre4.value += float(pes)*float(quant)
                NomsLot_centre4.append(nomProd)
                Quantitats_centre4.append(quant)
                
                #escollir millor empresa
                print('El pes rebut centre 4 es: ', pes, '\n')
                print('El pes total del lot es: ', pesTotalLot_centre4.value, '\n')
            
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=CentroLogistico4.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico4.uri,
                           msgcnt=mss_cnt)        
        mss_cnt += 1
        return gr.serialize(format='xml')

    pass

@app5.route("/comm")
def comunicacion5():
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
    global pesTotalLot_centre5
    
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
                           sender=CentroLogistico5.uri,
                           msgcnt=mss_cnt)
    else:
        #Si ho es obtenim la performativa
        if msgdic['performative'] != ACL.request:
            #No es un request, not understood
            logger.info('Msg no es una request')
            gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico5.uri,
                           msgcnt=mss_cnt)
        else:
            #Mirem tipus request
            content = msgdic['content']
            action = gm.value(subject=content, predicate=RDF.type)
            print('La action es:', action)
            print('La action hauria de ser:', REQ.PeticioEmpresa)
            
            if action == REQ.PeticioEnviament:
                logger.info('Es delega enviament')
                print('Rebut peticio de delegar enviament')
                
                content = msgdic['content']
                pes = gm.value(subject=content, predicate=REQ.pes)
                CompraId = gm.value(subject=content, predicate=REQ.idCompra)
                nomProd = gm.value(subject=content, predicate=REQ.prod)
                quant = gm.value(subject=content, predicate=REQ.quant)
                #ciutatDesti = gm.value(subject=content, predicate=REQ.CiutatDesti)
                #diaMaxim = gm.value(subject=content, predicate=REQ.DiaMaxim)
                #Afegir producte al lot
                
                L_centre5.append(CompraId)
                pesTotalLot_centre5.value += float(pes)*float(quant)
                NomsLot_centre5.append(nomProd)
                Quantitats_centre5.append(quant)
                
                #escollir millor empresa
                print('El pes rebut centre 5 es: ', pes, '\n')
                print('El pes total del lot es: ', pesTotalLot_centre5.value, '\n')
            
                gr = build_message(Graph(),
                           ACL['inform-done'],
                           sender=CentroLogistico5.uri,
                           msgcnt=mss_cnt)
            else:
                logger.info('Es una request que no entenem')
                gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=CentroLogistico5.uri,
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

@app2.route("/Stop")
def stop2():
    """
    Entrypoint que para el agente
    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"

@app3.route("/Stop")
def stop3():
    """
    Entrypoint que para el agente
    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"

@app4.route("/Stop")
def stop4():
    """
    Entrypoint que para el agente
    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"

@app5.route("/Stop")
def stop5():
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


def agentbehavior1(cola1, pesTotal, LotProductes, NomsLot, Quantitats):
    
    comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats, 1)
    app.run(host=hostname, port=portCentreLogistic)
    pass

def agentbehavior2(cola1, pesTotal, LotProductes, NomsLot, Quantitats):
    
    comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats, 2)
    app2.run(host=hostname, port=portCentreLogistic2)
    pass

def agentbehavior3(cola1, pesTotal, LotProductes, NomsLot, Quantitats):
    
    comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats, 3)
    app3.run(host=hostname, port=portCentreLogistic3)
    pass

def agentbehavior4(cola1, pesTotal, LotProductes, NomsLot, Quantitats):
    
    comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats, 4)
    app4.run(host=hostname, port=portCentreLogistic4)
    pass

def agentbehavior5(cola1, pesTotal, LotProductes, NomsLot, Quantitats):
    
    comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats, 5)
    app5.run(host=hostname, port=portCentreLogistic5)
    pass

if __name__ == '__main__':
    with Manager() as manager:
        L_centre1 = manager.list()
        NomsLot_centre1 = manager.list()
        Quantitats_centre1 = manager.list()
        
        L_centre2 = manager.list()
        NomsLot_centre2 = manager.list()
        Quantitats_centre2 = manager.list()
        
        L_centre3 = manager.list()
        NomsLot_centre3 = manager.list()
        Quantitats_centre3 = manager.list()
        
        L_centre4 = manager.list()
        NomsLot_centre4 = manager.list()
        Quantitats_centre4 = manager.list()
        
        L_centre5 = manager.list()
        NomsLot_centre5 = manager.list()
        Quantitats_centre5 = manager.list()
        
        
        # Ponemos en marcha los behaviors
        ab1 = Process(target=agentbehavior1, args=(cola1, pesTotalLot_centre1, L_centre1, NomsLot_centre1, Quantitats_centre1,))
        ab2 = Process(target=agentbehavior2, args=(cola1, pesTotalLot_centre2, L_centre2, NomsLot_centre2, Quantitats_centre2,))
        ab3 = Process(target=agentbehavior3, args=(cola1, pesTotalLot_centre3, L_centre3, NomsLot_centre3, Quantitats_centre3,))
        ab4 = Process(target=agentbehavior4, args=(cola1, pesTotalLot_centre4, L_centre4, NomsLot_centre4, Quantitats_centre4,))
        ab5 = Process(target=agentbehavior5, args=(cola1, pesTotalLot_centre5, L_centre5, NomsLot_centre5, Quantitats_centre5,))
        
        ab1.start()
        ab2.start()
        ab3.start()
        ab4.start()
        ab5.start()

        # Ponemos en marcha el servidor
       
        # Esperamos a que acaben los behaviors
        ab1.join()
        ab2.join()
        ab3.join()
        ab4.join()
        ab5.join()
        print('The End')