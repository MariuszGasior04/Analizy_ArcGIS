#!/usr/bin/env python
# -*- coding: utf-8 -*-

# skrypt do obracania kierunku rysowania linii sieci uzbrojenia terenu w kierunku wylotu

import arcpy

arcpy.env.overwriteOutput = True


def createFlippedLineGeom(line, line_flip):
    """
    Funkcja tworząca kolekcje id linii o obróconej geometrii gdzie wspołrzędne są kluczem, a identyfikator wartością
    """
    arcpy.Copy_management(line, line_flip)
    arcpy.FlipLine_edit(line_flip)
    line_geom = {}
    with arcpy.da.SearchCursor(line_flip, ['SHAPE@', 'OID@']) as cur:
        for row in cur:
            line_geom[row[1]] = row[0]
    arcpy.Delete_management(line_flip)
    return line_geom


def readEndpoint(point):
    """
    Funkcja tworząca kolekcje id punktów wylotowych gdzie wspołrzędne są kluczem, a identyfikator wartością
    """
    dictPointID = {}

    with arcpy.da.SearchCursor(point, ['SHAPE@X', 'SHAPE@Y', 'OID@']) as cur:
        for row in cur:
            dictPointID[(round(row[0], 3), round(row[1], 3))] = row[2]
    del cur
    return dictPointID


def flipNetwork(outflow_node, network):
    """
    Funkcja mająca na celu
    1) obrócenie ostatniego, wylotowego kolektora w kierunkuw ujscia z sieci
    2) budowanie kolekcji kolektorów o poprawnym kierunku
    3) obracanie kolektorów w sieci w kierunku ostatniego wylotu z sieci
    Informacja o uzgodnieniu obrotu jest zalisywana w atrybucie 'kierunek'.
    Analizowane są tylko te kolektory które nie posiadają wartosci 'UZGODNIONY' w atrybucie 'kierunek'
    """

    siec_flip = network + '_flip'

    arcpy.AddField_management(network, field_name="kierunek", field_type="TEXT", field_length=20)

    arcpy.AddMessage('Tworzenie roboczej geometrii sieci odwrotnej do analizowanej...')
    flipped_line_geom = createFlippedLineGeom(network, siec_flip)

    arcpy.AddMessage('Przygotowywanie warstwy wylotow...')
    wyloty = readEndpoint(outflow_node)

    arcpy.AddMessage("Obracanie kolektorow bezposrednio dotykajacych wyloty w kierunku wylotu...")
    with arcpy.da.UpdateCursor(network, ['SHAPE@', 'OID@', 'kierunek']) as cur:
        for row in cur:
            (xs, ys) = (round(row[0].firstPoint.X, 3), round(row[0].firstPoint.Y, 3))
            if (xs, ys) in wyloty:
                row[0] = flipped_line_geom[row[1]]
                row[2] = 'UZGODNIONY'
                cur.updateRow(row)
    del cur

    siec_count = 0
    kolektory_poprawne = {}

    arcpy.AddMessage('Budowanie kolekcji kolektorow o uzgodnionym kierunku na podstawie kolektorow wylotowych...')
    with arcpy.da.UpdateCursor(network, ['SHAPE@', 'OID@', 'kierunek']) as cur:
        for row in cur:
            siec_count += 1
            (xs, ys) = (round(row[0].firstPoint.X, 3), round(row[0].firstPoint.Y, 3))
            (xe, ye) = (round(row[0].lastPoint.X, 3), round(row[0].lastPoint.Y, 3))
            if (xe, ye) in wyloty:
                kolektory_poprawne[row[1]] = (row[0], (xs, ys), (xe, ye))
                row[2] = 'UZGODNIONY'
                cur.updateRow(row)
            if row[2] == 'UZGODNIONY' and row[1] not in kolektory_poprawne:
                kolektory_poprawne[row[1]] = (row[0], (xs, ys), (xe, ye))

    del cur

    arcpy.AddMessage('Uzgadnianie kierunkow na calej sieci (ilosc obiektow sieci - {0})...'.format(siec_count))
    przyrost_kontrolny = 1
    while przyrost_kontrolny > 0:
        kol_temp = kolektory_poprawne.copy()
        stan_p = len(kolektory_poprawne)
        with arcpy.da.UpdateCursor(network, ['SHAPE@', 'OID@', 'kierunek']) as cur:
            for row in cur:
                if row[1] not in kolektory_poprawne:
                    (xe, ye) = (round(row[0].lastPoint.X, 3), round(row[0].lastPoint.Y, 3))
                    (xs, ys) = (round(row[0].firstPoint.X, 3), round(row[0].firstPoint.Y, 3))
                    for item in kol_temp.iteritems():
                        if (xe, ye) == item[1][1]:
                            kolektory_poprawne[row[1]] = (row[0], (xs, ys), (xe, ye))
                            row[2] = 'UZGODNIONY'
                            cur.updateRow(row)
                        elif (xs, ys) == item[1][1]:
                            row[0] = flipped_line_geom[row[1]]
                            kolektory_poprawne[row[1]] = (row[0], (xe, ye), (xs, ys))
                            row[2] = 'UZGODNIONY'
                            cur.updateRow(row)
        del cur
        przyrost_kontrolny = len(kolektory_poprawne) - stan_p

        arcpy.AddMessage('Poprawnie zorientowanych odcinkow sieci - {0} - {1}%'.format(len(kolektory_poprawne), round(
            float(len(kolektory_poprawne)) * 100 / siec_count, 2)))
    return


if __name__ == '__main__':
    """parametry programu"""
    wyloty = arcpy.GetParameterAsText(0)
    network = arcpy.GetParameterAsText(1)

    flipNetwork(wyloty, network)
