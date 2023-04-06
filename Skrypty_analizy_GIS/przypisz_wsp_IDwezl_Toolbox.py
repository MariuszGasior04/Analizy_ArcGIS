#!/usr/bin/env python
#-*- coding: utf-8 -*-
#skrypt do przypisania współczynnika splywu z opracowane bazy danych do modelu w URBANIE

import arcpy

def wsp_splyw(msm_HMod, zlewnie, pola):
    """
        Funkcja przypisująca współczynniki splywu do tabeli msm_HMod
    """
    zlew_dict = {}
    arcpy.AddMessage("1-Tworzenie kolekcji ID zlewni, ID Wezlow i wspolczynnikow splywu...")

    with arcpy.da.SearchCursor(zlewnie, pola) as search:
        for row in search:
            zlew_dict[row[0]] = [row[1], row[2]]
    del search

    arcpy.AddMessage("2-Uzupelnianie wspolczynnikow splywu w tabeli msm_HMod...")
    with arcpy.da.UpdateCursor(msm_HMod, ['CatchID', 'ImpArea'])as cur:
        for row in cur:
            if row[0] in zlew_dict:
                row[1] = round(float(zlew_dict[row[0]][0])*100, 2)
            cur.updateRow(row)
    del cur

    return zlew_dict

def powiazanie_zlewnia_wezel(msm_CtachCon, zlew_dict):
    """
        Funkcja do  uzupełniania tabeli łacznikowej ID Wezlów i ID zlewni
    """
    arcpy.AddMessage("3-Czyszczenie, przygotowanie do zaladaowania tabeli msm_CtachCon...")
    arcpy.DeleteRows_management(msm_CtachCon)

    values = []
    i = 0
    for key in zlew_dict.keys():
        i+=1
        values.append((i, key, 1, zlew_dict[key][1], 1))

    arcpy.AddMessage("4-Uzupelnianie tabeli msm_CtachCon...")
    with arcpy.da.InsertCursor(msm_CtachCon, ['MUID', 'CatchID', 'TypeNo', 'NodeID', 'Fraction']) as insert:
        for row in values:
            insert.insertRow(row)
    del insert

if __name__ == '__main__':
    zlew = arcpy.GetParameterAsText(0)
    field_ID = arcpy.GetParameterAsText(1)
    field_ID_NOD = arcpy.GetParameterAsText(2)
    field_WSP = arcpy.GetParameterAsText(3)
    msm_Hmod = arcpy.GetParameterAsText(4)
    msm_CatchCon = arcpy.GetParameterAsText(5)
    fields = [field_ID, field_WSP, field_ID_NOD]

    powiazanie_zlewnia_wezel(msm_CatchCon, wsp_splyw(msm_Hmod, zlew, fields))
