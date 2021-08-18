#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Skrypt służy do zapsiu projekcji arkuszy mapowych MZP i MRP
'''

import arcpy
import os
import traceback


def BatchSaveMXD(mxdPath, folderMxd, rodzMapy, scen, wydanie):
    mxd = arcpy.mapping.MapDocument(mxdPath)
    for pageNum in range(1, mxd.dataDrivenPages.pageCount + 1):
         try:
             mxd.dataDrivenPages.currentPageID = pageNum
             pageName = mxd.dataDrivenPages.pageRow.Godlo.replace('-', '')

             if len(pageName) < 8:
                pageName = pageName[:3]+'00'+pageName[3:]

             if len(pageName) < 9:
                pageName = pageName[:3]+'0'+pageName[3:]

             arcpy.AddMessage(u"Arkusz {}".format(pageName))
             outName = os.path.join(folderMxd, pageName + rodzMapy+'_'+scen+'_'+wydanie+'.mxd')
             arcpy.AddMessage(u"--Zapisuje arkusz {}...".format(outName))
             mxd.saveACopy(outName)

         except Exception as e:
             arcpy.AddWarning(u"--Arkusz ID {} spowodowal error:\n{}".format(pageNum, traceback.format_exc()))

    del mxd


if __name__ == '__main__':

    mxdPath = arcpy.GetParameterAsText(0)
    outFolder = arcpy.GetParameterAsText(1)
    rodzMap = arcpy.GetParameterAsText(2)
    scen = arcpy.GetParameterAsText(3)
    wydanie = arcpy.GetParameterAsText(4)
    
    BatchSaveMXD(mxdPath, outFolder, rodzMap, scen, wydanie)
    
    
    

