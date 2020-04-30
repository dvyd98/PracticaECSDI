# -*- coding: iso-8859-1 -*-
"""
.. module:: RandomInfo

RandomInfo
*************

:Description: RandomInfo

    Genera un grafo RDF con aserciones generando los valores de los atributos aleatoriamente

    Asumimos que tenemos ya definida una ontologia y simplemente escogemos una o varias de las clases
    y generamos aleatoriamente los valores para sus atributos.

    Solo tenemos que a�adir aserciones al grafo RDFlib y despues grabarlo en OWL (o turtle), el resultado
    deberia poder cargarse en Protege, en un grafo RDFlib o en una triplestore (Stardog, Fuseki, ...)

    Se puede a�adir tambien aserciones sobre las clases y los atributos si no estan ya en una ontologia
      que hayamos elaborado con Protege

:Authors: 
    

:Version: 

:Created on: 

"""

from rdflib import Graph, RDF, RDFS, OWL, XSD, Namespace, Literal
import string
import random
import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

limR = [0, 5]

def random_name(prefix, size=6, chars=string.ascii_uppercase + string.digits):
    """
    Genera un nombre aleatorio a partir de un prefijo, una longitud y una lista con los caracteres a usar
    en el nombre
    :param prefix:
    :param size:
    :param chars:
    :return:
    """
    return prefix + '_' + ''.join(random.choice(chars) for _ in range(size))

def random_attribute(type, lim):
    """
    Genera un valor de atributo al azar dentro de un limite de valores para int y floar
    :param type:
    :return:
    """
    if len(lim) == 0 or lim[0] > lim[1]:
        raise Exception('No Limit')
    if type == 'f':
        return random.uniform(lim[0], lim[1])
    elif type == 'i':
        return int(random.uniform(lim[0], lim[1]))

if __name__ == '__main__':
    # Declaramos espacios de nombres de nuestra ontologia, al estilo DBPedia (clases, propiedades, recursos)
    EmOnt = Namespace("http://www.empreses.org/ontology/")
    EmOntPr = Namespace("http://www.empreses.org/ontology/property/")
    EmOntRes = Namespace("http://www.empreses.org/ontology/resource/")

    # lista de tipos XSD datatypes para los rangos de las propiedades
    xsddatatypes = {'s': XSD.string, 'i': XSD.int, 'f': XSD.float}

    # Creamos instancias de la clase PrOnt.ElectronicDevice asumiendo que esta clase ya existe en nuestra ontologia
    # nos hace falta a�adirla al fichero de instancias si queremos usarla para hacer consultas sobre sus subclases
    #
    # Asumimos que tenemos los atributos
    #  * PrOntPr.tieneMarca: de producto a marca
    #  * PrOntPr.precio: real
    #  * PrOnt.peso: real
    #  * PrOntPr.nombre: string

    # Diccionario de atributos f= tipo float, i= tipo int, s= tipo string, otro => clase existente en la ontologia
    product_properties = {'nombre': 's',}

    # Diccionario con clases, cada clase tiene una lista con los atributos y en el caso de necesitarlo, su rango min/max
    product_classes = {'Empresa_transportista1': [['nombre']],
                       'Empresa_transportista2': [['nombre']],
                       'Empresa_transportista3': [['nombre']],
                       'Empresa_transportista4': [['nombre']],
                       'Empresa_transportista5': [['nombre']],
                       }

    products_graph = Graph()

    # A�adimos los espacios de nombres al grafo
    products_graph.bind('cont', EmOnt)
    products_graph.bind('contp', EmOntPr)
    products_graph.bind('contr', EmOntRes)

    # Clase padre de los productos
    products_graph.add((EmOnt.EmpresesTransportistes, RDF.type, OWL.Class))

    # A�adimos los atributos al grafo con sus rangos (los dominios los a�adimos despues con cada clase)
    for prop in product_properties:
        if product_properties[prop] in ['s', 'i', 'f']:
            products_graph.add((EmOntPr[prop], RDF.type, OWL.DatatypeProperty))
            products_graph.add((EmOntPr[prop], RDFS.range, xsddatatypes[product_properties[prop]]))
        else:
            products_graph.add((EmOntPr[prop], RDF.type, OWL.ObjectProperty))
            products_graph.add((EmOntPr[prop], RDFS.range, EmOnt[product_properties[prop]]))

    clase = 0
    for prc in product_classes:
        products_graph.add((EmOnt[prc], RDFS.subClassOf, EmOnt.EmpresesTransportistes))

        # A�adimos las propiedades con sus dominios (si no estan ya en la definicion de la ontologia original)

        for prop in product_classes[prc]:
            products_graph.add((EmOntPr[prop[0]], RDFS.domain, EmOnt[prc]))
        
        #generar instancies productes
        product = 'em' + str(clase+1)
        products_graph.add((EmOntRes[product], RDF.type, EmOnt[prc]))
            
        
        for attr in product_classes[prc]:
            val = Literal('empresa_' + str(clase+1))
            products_graph.add((EmOntRes[product], EmOntPr[attr[0]], val))

        clase = clase + 1
        
    # Resultado en Turtle
    print(products_graph.serialize(format='turtle'))


    # Grabamos el OWL resultante
    # Lo podemos cargar en Protege para verlo y cargarlo con RDFlib o en una triplestore (Stardog/Fuseki)
    ofile  = open('empresesTransp.owl', "w")
    encoding = 'iso-8859-1'
    ofile.write(str(products_graph.serialize(), encoding))
    ofile.close()
    
        