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

:Authors: bejar
    

:Version: 

:Created on: 22/04/2016 12:30 

"""
import rdflib
from rdflib import Graph, RDF, RDFS, OWL, XSD, Namespace, Literal
import string
import random
import sys
import os

sys.path.append(os.path.relpath("./AgentUtil"))
sys.path.append(os.path.relpath("./Utils"))

from OntoNamespaces import ACL, DSO, RDF, PrOnt, REQ, PrOntPr, PrOntRes

limR = [0, 5]
#Cargar todos los productos en allProducts
allProducts = []

g=rdflib.Graph()
g.parse("./Ontologies/product.owl", format="xml")

query = """SELECT ?nombre ?class ?n
              WHERE {
              ?a rdf:type ?class .
              ?class rdfs:subClassOf ?n .
              ?a PrOntPr:nombre ?nombre .
              ?a PrOntPr:tieneMarca ?b .
              ?b PrOntPr:nombre ?marca .
              
              }
              """
qres = g.query(query, initNs = {'PrOnt': PrOnt, 'PrOntPr': PrOntPr, 'PrOntRes' : PrOntRes})

for row in qres:
   allProducts.append(row['nombre'])
   
allProductsTest = [allProducts[0], allProducts[1], allProducts[2]]
   
#-------------------

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
    CenOnt = Namespace("http://www.centresProd.org/ontology/")
    CenOntPr = Namespace("http://www.centresProd.org/ontology/property/")
    OntResources = []
    Cen1OntRes = Namespace("http://www.centresProd.org/ontology/resource/cl1")
    Cen2OntRes = Namespace("http://www.centresProd.org/ontology/resource/cl2")
    Cen3OntRes = Namespace("http://www.centresProd.org/ontology/resource/cl3")
    Cen4OntRes = Namespace("http://www.centresProd.org/ontology/resource/cl4")
    Cen5OntRes = Namespace("http://www.centresProd.org/ontology/resource/cl5")
    OntResources.append(Cen1OntRes)
    OntResources.append(Cen2OntRes)
    OntResources.append(Cen3OntRes)
    OntResources.append(Cen4OntRes)
    OntResources.append(Cen5OntRes)

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
    product_properties = {'stock': 'i',
                          'nombre': 's'}

    # Diccionario con clases, cada clase tiene una lista con los atributos y en el caso de necesitarlo, su rango min/max
    product_classes = {'Producte_CentreLogistic1': [['stock', 0, 5],
                                 ['nombre']],
                       'Producte_CentreLogistic2': [['stock', 0, 5],
                                 ['nombre']],
                       'Producte_CentreLogistic3': [['stock', 0, 5],
                                 ['nombre']],
                       'Producte_CentreLogistic4': [['stock', 0, 5],
                                 ['nombre']],
                       'Producte_CentreLogistic5': [['stock', 0, 5],
                                 ['nombre']],
                       }

    products_graph = Graph()

    # A�adimos los espacios de nombres al grafo
    products_graph.bind('cont', CenOnt)
    products_graph.bind('contp', CenOntPr)
    products_graph.bind('contr1', Cen1OntRes)
    products_graph.bind('contr2', Cen2OntRes)
    products_graph.bind('contr3', Cen3OntRes)
    products_graph.bind('contr4', Cen4OntRes)
    products_graph.bind('contr5', Cen5OntRes)

    # Clase padre de los productos
    products_graph.add((CenOnt.CentresLogistics, RDF.type, OWL.Class))

    # A�adimos los atributos al grafo con sus rangos (los dominios los a�adimos despues con cada clase)
    for prop in product_properties:
        if product_properties[prop] in ['s', 'i', 'f']:
            products_graph.add((CenOntPr[prop], RDF.type, OWL.DatatypeProperty))
            products_graph.add((CenOntPr[prop], RDFS.range, xsddatatypes[product_properties[prop]]))
        else:
            products_graph.add((CenOntPr[prop], RDF.type, OWL.ObjectProperty))
            products_graph.add((CenOntPr[prop], RDFS.range, CenOnt[product_properties[prop]]))

    clase = 0
    for prc in product_classes:
        products_graph.add((CenOnt[prc], RDFS.subClassOf, CenOnt.CentresLogistics))

        # A�adimos las propiedades con sus dominios (si no estan ya en la definicion de la ontologia original)

        for prop in product_classes[prc]:
            products_graph.add((CenOntPr[prop[0]], RDFS.domain, CenOnt[prc]))

        CenOntRes = OntResources[clase]
        #generar instancies productes
        for x in allProducts:
            product = x
            products_graph.add((CenOntRes[product], RDF.type, CenOnt[prc]))
            
            for attr in product_classes[prc]:
                prop = product_properties[attr[0]]
                # el atributo es real o entero
                if prop == 'i':
                    val = Literal(random_attribute(prop, attr[1:]))
                # el atributo es string
                elif prop == 's':
                    val = product
                else:
                    break
                products_graph.add((CenOntRes[product], CenOntPr[attr[0]], val))
        clase = clase + 1

    # Resultado en Turtle
    print(products_graph.serialize(format='turtle'))


    # Grabamos el OWL resultante
    # Lo podemos cargar en Protege para verlo y cargarlo con RDFlib o en una triplestore (Stardog/Fuseki)
    ofile  = open('centresProd.owl', "w")
    encoding = 'iso-8859-1'
    ofile.write(str(products_graph.serialize(), encoding))
    ofile.close()
    
    #----------------Localitzacio dels centres--------------------
    
    Locations = [[41.390205, 2.154007], [41.11667, 1.25], [41.979401, 2.821426], [41.617592, 0.620015], [42.3167, 2.3667]]
    
    LocCenOnt = Namespace("http://www.centresLoc.org/ontology/")
    LocCenOntPr = Namespace("http://www.centresLoc.org/ontology/property/")
    LocCenOntRes = Namespace("http://www.centresLoc.org/ontology/resource/")
    
    center_properties = {'latitud': 'f',
                          'longitud': 'f'}
    
    loc_cent_classes = {'Loc_CentreLogistic1': [['latitud'],
                                 ['longitud']],
                       'Loc_CentreLogistic2': [['latitud'],
                                 ['longitud']],
                       'Loc_CentreLogistic3': [['latitud'],
                                 ['longitud']],
                       'Loc_CentreLogistic4': [['latitud'],
                                 ['longitud']],
                       'Loc_CentreLogistic5': [['latitud'],
                                 ['longitud']],
                       }
    
    loc_graph = Graph()
    
    loc_graph.bind('loccont', LocCenOnt)
    loc_graph.bind('loccontp', LocCenOntPr)
    loc_graph.bind('loccontr', LocCenOntRes)
    
    loc_graph.add((LocCenOnt.CentresLogistics, RDF.type, OWL.Class))
    
    for prop in center_properties:
        if center_properties[prop] in ['s', 'i', 'f']:
            loc_graph.add((LocCenOntPr[prop], RDF.type, OWL.DatatypeProperty))
            loc_graph.add((LocCenOntPr[prop], RDFS.range, xsddatatypes[center_properties[prop]]))
        else:
            loc_graph.add((LocCenOntPr[prop], RDF.type, OWL.ObjectProperty))
            loc_graph.add((LocCenOntPr[prop], RDFS.range, LocCenOnt[center_properties[prop]]))
    
    clase = 0
    for prc in loc_cent_classes:
        loc_graph.add((LocCenOnt[prc], RDFS.subClassOf, LocCenOnt.CentresLogistics))
    
        for prop in loc_cent_classes[prc]:
            loc_graph.add((LocCenOntPr[prop[0]], RDFS.domain, LocCenOnt[prc]))
        
        lc = 'LocCentreLog' + str(clase+1)
        loc_graph.add((LocCenOntRes[lc], RDF.type, LocCenOnt[prc]))
        
        first = True
        for attr in loc_cent_classes[prc]:
                prop = center_properties[attr[0]]
                # el atributo es real o entero
                if prop == 'f' and first:
                    val = Literal(Locations[clase][0])
                # el atributo es string
                elif prop == 'f' and not first:
                    val = Literal(Locations[clase][1])
                else:
                    val = 0
                loc_graph.add((LocCenOntRes[lc], LocCenOntPr[attr[0]], val))
        clase = clase +1
    
    ofile  = open('locCentres.owl', "w")
    encoding = 'iso-8859-1'
    ofile.write(str(loc_graph.serialize(), encoding))
    ofile.close()
        