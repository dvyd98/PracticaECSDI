"""
.. module:: Agent

Agent
******

:Description: Agent
  Clase para guardar los atributos de un agente

"""

__author__ = 'bejar'

portClient = 9000
portGestorPlataforma = 9001
portCentreLogistic = 9002
portAgentEmpresa = 9003
portCerca = 9050
portVenedorExtern = 9060

class Agent():
    def __init__(self, name, uri, address, stop):
        self.name = name
        self.uri = uri
        self.address = address
        self.stop = stop