#!/usr/bin/env python
#-*- #################
#mgasior
#mgsior04@gmail.com

#skrypt do przypisania ID studzienki modelowanej sieci kanalizacji do węzłów ujściowych zlewni (kratek lub dachów)

import arcpy

def idStud(manholes):
    """
    Funkcja tworząca kolekcje id studzienek gdzie wspołrzędne są kluczem, a identyfikator wartością
    """
    dictStudID = {}

    with arcpy.da.SearchCursor(manholes, ['SHAPE@X', 'SHAPE@Y', 'OID@']) as cur:
        for row in cur:
            dictStudID[(round(row[0], 3), round(row[1], 3))] = row[2]
    del cur
    return dictStudID

def idKolektor(network):
    """
    Funkcja tworząca dwie kolekcje
    1) id kolektorów gdzie wspołrzędne początku i konca odcinka sieci są kluczem, a lista identyfikatorów wartością
    2) id kolektorów gdzie id odcinków sieci są kluczem a tupla wspołrzędnych początku i konca odcinka sieci jest wartością
    """
    dictSiecID = {}
    dictSiecWsp = {}
    with arcpy.da.SearchCursor(network, ['SHAPE@', 'OID@']) as cur:
        for row in cur:
            (xs, ys) = (round(row[0].firstPoint.X, 3), round(row[0].firstPoint.Y, 3))
            (xe, ye) = (round(row[0].lastPoint.X, 3), round(row[0].lastPoint.Y, 3))

            if (xs, ys) not in dictSiecID:
                dictSiecID[(xs, ys)] = [row[1]]
            else:
                dictSiecID[(xs, ys)].append(row[1])

            if (xe, ye) not in dictSiecID:
                dictSiecID[(xe, ye)] = [row[1]]
            else:
                dictSiecID[(xe, ye)].append(row[1])

            dictSiecWsp[row[1]] = ((xs, ys), (xe, ye))
    del cur
    return dictSiecID, dictSiecWsp

def updateStudID(manholes, network, nods):
    """
    Funkcja mająca za zadanie przypisać identyfikatory studzienek na sieci modelowanej obiektom na warstwie kratek
    warstwa kratek musi posiadać atrybut ID_STUDZIENKI. Identyfiakotory sa przypisywane obiektom które w atrybucie ID_STUDZIENEK posiadają wartość NULL
    """
    arcpy.AddMessage("Budowanie zbioru ID studzienek modelowanych...")
    dStudnie = idStud(manholes)
    arcpy.AddMessage("Budowanie zbioru ID kolektorow analizowanej sieci...")
    dKolektorID, dKolektorWsp = idKolektor(network)

    arcpy.AddMessage("Dodanie atrybutu ID STUDZIENKI do warstwy wezlow wylotowych zlewni...")
    arcpy.AddField_management(nods, field_name ="ID_STUDZIENKI", field_type ="LONG")

    arcpy.AddMessage("Przypisywania identyfikatorow studzienek do wezlow wylotowych zlewni...")

    with arcpy.da.UpdateCursor(nods, ['SHAPE@X', 'SHAPE@Y', 'OID@', 'ID_STUDZIENKI']) as cur:
        for row in cur:
            if row[3] is None:
                wspKratki = (round(row[0], 3), round(row[1], 3))
                if wspKratki in dStudnie:
                    row[3] = dStudnie[wspKratki]
                    arcpy.AddMessage("Przypisano ID studzienki modelowanej do obiektu o ID {0}".format(row[2]))
                elif wspKratki in dKolektorID:
                    id = dKolektorID[wspKratki][0]
                    # ommitIdList = [id]
                    if dKolektorWsp[id][0] in dStudnie or dKolektorWsp[id][1] in dStudnie:
                        try:
                            row[3] = dStudnie[dKolektorWsp[id][0]]
                            arcpy.AddMessage("Przypisano ID studzienki modelowanej do obiektu o ID {0}".format(row[2]))
                        except KeyError:
                            row[3] = dStudnie[dKolektorWsp[id][1]]
                            arcpy.AddMessage("Przypisano ID studzienki modelowanej do obiektu o ID {0}".format(row[2]))
                    else:
                        IDlist = list(set(dKolektorID[dKolektorWsp[id][0]] + dKolektorID[dKolektorWsp[id][1]]))
                        try:
                            IDlist.remove(id)
                        except ValueError:
                            pass
                        i = 0
                        while row[3] is None and i < 500:
                            i+=1
                            for id in IDlist:
                                # ommitIdList.append(id)
                                # ommitIdList = list(set(ommitIdList))
                                if dKolektorWsp[id][0] in dStudnie or dKolektorWsp[id][1] in dStudnie:
                                    try:
                                        row[3] = dStudnie[dKolektorWsp[id][0]]
                                        arcpy.AddMessage("Przypisano ID studzienki modelowanej do obiektu o ID {0}".format(row[2]))
                                        IDlist.remove(id)
                                        break
                                    except KeyError:
                                        row[3] = dStudnie[dKolektorWsp[id][1]]
                                        arcpy.AddMessage("Przypisano ID studzienki modelowanej do obiektu o ID {0}".format(row[2]))
                                        IDlist.remove(id)
                                        break
                                else:
                                    IDlist = list(set(IDlist + dKolektorID[dKolektorWsp[id][0]] + dKolektorID[
                                        dKolektorWsp[id][1]]))

            cur.updateRow(row)
    del cur
    return

if __name__ == '__main__':
    """parametry"""
    studnie = arcpy.GetParameterAsText(0)
    siec = arcpy.GetParameterAsText(1)
    wezel = arcpy.GetParameterAsText(2)

    updateStudID(studnie, siec, wezel)

