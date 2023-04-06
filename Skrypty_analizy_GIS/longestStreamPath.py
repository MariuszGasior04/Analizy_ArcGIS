#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import arcpy
import networkx

arcpy.env.overwriteOutput = True

def shp2longestPathNetwork(shpFile):
    '''Funkcja zamieniająca warstwe liniową shp na DAG network. Zwraca network'''

    network = networkx.read_shp(shpFile, simplify=False, geom_attrs=True, strict=True)
    longestPathNetwork = networkx.DiGraph(networkx.dag_longest_path(network))

    return longestPathNetwork


def addLongestPaths2Shp(shpFile, catchmentField):
    '''Funkcja dodająca do warstwy liniowej z atrybutem ID zlewni najdłuższe sciezki splywu z danej zlewni'''

    catchList = []
    with arcpy.da.SearchCursor(shpFile, [catchmentField]) as cur:
        for row in cur:
            catchList.append(row[0])
    catchList = set(catchList)

    print("Przetwarzanie sciezek splywu dla {} zlewni...".format(len(catchList)))
    i = 1
    for catchmentID in catchList:
        print("Przetwarzanie zlewni nr {} o ID {}...".format(i, catchmentID))

        out_shp = os.path.join(os.path.dirname(shpFile), 'temp.shp')
        where_clause = '"'+catchmentField+'"'+'=' + str(catchmentID)

        # print(where_clause)
        arcpy.Select_analysis(shpFile, out_shp, where_clause)

        network = shp2longestPathNetwork(out_shp)

        wsp = []
        for node in network.edges:
            wsp.append(arcpy.Point(node[0], node[1]))
        array = arcpy.Array(wsp)
        polyline = arcpy.Polyline(array)

        # dodawanie geometrii najdłuzszej sciezki splywu do shp
        cursor = arcpy.da.InsertCursor(shpFile, ['SHAPE@'])
        cursor.insertRow([polyline])
        i += 1

        del cursor
        arcpy.Delete_management(out_shp)

if __name__ == '__main__':

    # r"C:\robo\_warstwy_tymczasowe\rzeszow\zlewnie\sciezki_splywu_zlewnie.shp"
    shp = input("Enter line shapeFile path:")


    addLongestPaths2Shp(shp, 'Label')
