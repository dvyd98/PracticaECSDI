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
from Agent import portCentreLogistic, portAgentEmpresa, portGestorPlataforma

__author__ = 'pball'


# Configuration stuff
hostname = "localhost"
ip = 'localhost'

#logger = config_logger(level=1, file="./logs/AgentCentreLogistic")
logger = config_logger(level=1)

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

#Lot de producte Centre
L = None
NomsLot = None
Quantitats = None
pesTotalLot = Value('d', 0.0)


# Datos del Agente

#AgentCentreLogistic = None
CentroLogistico1 = Agent('CentroLogistico1',
                        agn.cl1,
                        'http://%s:%d/comm' % (hostname, portCentreLogistic),
                        'http://%s:%d/Stop' % (hostname, portCentreLogistic))

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

def negociarTransport(pes, ciutatDesti, diaMaxim, LotProductes, NomsLot, Quantitats):
        
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
        messageEmpresa = build_message(contentPeticioEmpresa, perf=ACL.request, sender=CentroLogistico1.uri, msgcnt=0, receiver=EmpresaTransportista.uri, content=enviament_obj)
        
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
            if first:
                nomEmpresaAmbPreuMesBaix = row['nombre']
                preuMesBaix = row['precio']
                first = False
            else:
                if preuMesBaix > row['precio']:
                    nomEmpresaAmbPreuMesBaix = row['nombre']
                    preuMesBaix = row['precio']
            
                    
                    
        print('El preu mes baix:', preuMesBaix)
        print('Nom de la empresa:', nomEmpresaAmbPreuMesBaix)
        
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
                    messagePerPlataforma = build_message(gResposta, perf=ACL.request, sender=CentroLogistico1.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta_enviament)
                    #envia missatge a l'Agent EmpresaTransportista
                    send_message(messagePerPlataforma, PlataformaAgent.address)
        
        
#        result = Graph()
#        result.bind('req', REQ)
#        result_obj = agn['result']
#        
#        result.add((result_obj, RDF.type, REQ.IniciarEnviament))
#        result.add((result_obj, REQ.NomEmpresa, nomEmpresaAmbPreuMesBaix))
#        result.add((result_obj, REQ.Preu, preuMesBaix))
        
#        gProva = Graph()
#        gProva.bind('req', REQ)
#        resposta1 = agn['resposta1']
#        gProva.add((resposta1, RDF.type, REQ.IniciarEnviament))
#        messagePerPlataforma = Graph()
#        messagePerPlataforma = build_message(gProva, perf=ACL.request, sender=CentroLogistico1.uri, msgcnt=0, receiver=PlataformaAgent.uri, content=resposta1)
#        #envia missatge a l'Agent EmpresaTransportista
#        send_message(messagePerPlataforma, PlataformaAgent.address)
      
    
def comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats):    
  print("El pes del Lot és: ", pesTotal.value)
  #De moment sempre que hi hagi un producte al lot ja fa la petició
  if pesTotal.value > 800:
      ciutatDesti = 'Barcelona'
      diaMaxim = '15/10/2021'
      
      print('Preparar enviar peticio a empresa transportista')
      negociarTransport(pesTotal.value, ciutatDesti, diaMaxim, LotProductes, NomsLot, Quantitats)         
      print('-----------EMPRESSA NEGOCIADA-------------')
      
      pesTotal.value = 0
      print("El pesTotal ha canviat a",pesTotal.value)
      LotProductes = []
      NomsLot = []
      Quantitats = []

  threading.Timer(15.0, comprovarLotComplet, args=(pesTotal, LotProductes, NomsLot, Quantitats,)).start()
  print("S'està comprovant si tenim un lot complet i podem començar la negociació")
      
      
  

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    
    global dsgraph
    global mss_cnt
    global pesTotalLot
    
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
                
                L.append(CompraId)
                pesTotalLot.value += float(pes)
                NomsLot.append(nomProd)
                Quantitats.append(quant)
                
                #escollir millor empresa
                print('El pes rebut es: ', pes, '\n')
                print('El pes total del lot es: ', pesTotalLot.value, '\n')
            
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


def agentbehavior1(cola1, pesTotal, LotProductes, NomsLot, Quantitats):
    
    comprovarLotComplet(pesTotal, LotProductes, NomsLot, Quantitats)
    
    pass

#def agentbehavior2(cola):
#    
#    AgentCentreLogistic = Agent('CentreLogistic2',
#                       agn.AgentCentreLogistic,
#                       'http://%s:%d/comm' % (hostname, port+1),
#                       'http://%s:%d/Stop' % (hostname, port+1))
#    return

if __name__ == '__main__':
    with Manager() as manager:
        L = manager.list()
        NomsLot = manager.list()
        Quantitats = manager.list()
        # Ponemos en marcha los behaviors
        ab1 = Process(target=agentbehavior1, args=(cola1, pesTotalLot, L, NomsLot, Quantitats,))
        #ab2 = Process(target=agentbehavior2, args=(cola1,))
        ab1.start()
        #ab2.start()

        # Ponemos en marcha el servidor
        app.run(host=hostname, port=portCentreLogistic)

        # Esperamos a que acaben los behaviors
        ab1.join()
        #ab2.join()
        print('The End')