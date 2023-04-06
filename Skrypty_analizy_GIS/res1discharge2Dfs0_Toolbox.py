#!/usr/bin/env python
#-*- coding: utf-8 -*-

import mikeio,arcpy
from mikeio1d.res1d import Res1D, QueryDataReach

def readOutletNodes(res1dFile):
    outletNodes = []
    res1d = Res1D(res1dFile)
    for n in res1d.data.Nodes:
        if 'Res1DOutlet' in str(n):
            outletNodes.append(str(n).split(' ')[1])
    return outletNodes

def getChainage(reachData):
    s1 = str(reachData).split(' ')[-1]
    s2 = s1.replace('(', '')
    s3 = s2.replace(')', '')
    chainages = s3.split('-')
    chainages = [float(chainages[0]), float(chainages[1].replace(',', '.'))]
    return chainages

def readOutletReaches(worspaceGdb, outletNodes):
    arcpy.env.workspace = worspaceGdb
    outletReaches = []
    linkTemp = r'in_memory\Link'
    linkTempOst = r'in_memory\LinkOst'
    nodeTemp = r'in_memory\Node'
    wc = "MUID IN " + str(outletNodes).replace('[', '(').replace(']', ')')
    arcpy.MakeFeatureLayer_management('msm_Node', nodeTemp, wc)
    arcpy.MakeFeatureLayer_management('msm_Link', linkTemp)
    arcpy.SelectLayerByLocation_management(in_layer = linkTemp, overlap_type = 'intersect', select_features = nodeTemp, selection_type = 'NEW_SELECTION')
    arcpy.CopyFeatures_management(linkTemp, linkTempOst)

    with arcpy.da.SearchCursor(linkTempOst, ['MUID']) as cur:
        for row in cur:
            outletReaches.append(row[0])
    del cur

    return outletReaches

def readReachDISCHARGE(res1dFile, outletReaches):
    queries = []
    res1d = Res1D(res1dFile)

    for n in res1d.data.Reaches:
        chanages = getChainage(n)
        reachID = str(n).split(' ')[1].split('-')[0]
        if reachID in outletReaches:
            chainage = chanages[1]
            query = QueryDataReach("Discharge", reachID, chainage)
            queries.append(query)
    df = res1d.read(queries)

    return df

def saveDfs0(dataframe, outputDfs0File):
    mikeio.Dfs0.from_dataframe(dataframe,
                               outputDfs0File,
                               mikeio.EUMType.Discharge,
                               mikeio.EUMUnit.meter_pow_3_per_sec)
    return

if __name__ == '__main__':
    res = arcpy.GetParameterAsText(0)
    resGdb = arcpy.GetParameterAsText(1)
    outputDfs0 = arcpy.GetParameterAsText(2)

    node = readOutletNodes(res)
    reaches = readOutletReaches(resGdb, node)
    dischargeDataFrame = readReachDISCHARGE(res, reaches)
    saveDfs0(dischargeDataFrame, outputDfs0)
