#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Skrypt służy do zapsiu projekcji arkuszy mapowych MZP i MRP
'''

import arcpy, os

def checkOutputFolder(folder_map):
    wydrukowane= []
    for mapa in os.listdir(folder_map):
        wydrukowane.append(os.path.splitext(mapa)[0])
    wydruki = set(wydrukowane)
    return wydruki

def zrobGeoTIFF(mxd,df,plik_wynik, rozdz):
    ar = df.extent.height / df.extent.width
    arcpy.AddMessage("---Aspect ratio: {}".format(ar))
    ext = df.extent.width
    arcpy.AddMessage("---Extent width: {}".format(ext))
    m_in = 39.37007874
    rozm_ark = ext / df.scale
    arcpy.AddMessage("---Rozm. ark.: {}".format(rozm_ark))
    szer_pix = int(rozdz * m_in * rozm_ark)
    arcpy.AddMessage("---Pixel width: {}".format(szer_pix))
    wys_pix = int(szer_pix*ar)
    arcpy.AddMessage("---Pixel ht: {}".format(wys_pix))
    arcpy.mapping.ExportToTIFF(mxd,plik_wynik,df,szer_pix,szer_pix*ar,rozdz,False,"24-BIT_TRUE_COLOR","LZW",True)


def ProcessMxdView(mapPath,options):
    ext = {'TIFF':'.tif','JPEG':'.jpg','PDF':'.pdf','PNG':'.png','GEOTIFF':'.tif'}
    mapPath = unicode(mapPath)
    outFile = unicode(os.path.join(options['outFolder'],os.path.basename(mapPath).replace('.mxd',ext[options['type']])))
    
    
    arcpy.AddMessage("{} -> {}".format(mapPath,outFile))
    arcpy.AddMessage("Opening mxd...")
    mxd = arcpy.mapping.MapDocument(mapPath)
    if mxd.isDDPEnabled:
        mxd.dataDrivenPages.refresh()
    if options['type'] == 'PDF':
        arcpy.mapping.ExportToPDF(mxd, outFile, 
                                  resolution = options['resolution'], 
                                  image_quality = options['pdfImageQuality'], 
                                  jpeg_compression_quality=options['jpegQuality'], 
                                  layers_attributes = "NONE", 
                                  colorspace='RGB',
                                  compress_vectors=True, 
                                  image_compression='JPEG',
                                  picture_symbol="RASTERIZE_PICTURE",
                                  convert_markers=False,
                                  embed_fonts=True)
        arcpy.AddMessage("Exported PDF")
    elif options['type'] == 'JPEG':
        arcpy.mapping.ExportToJPEG(mxd, outFile, resolution = options['resolution'], world_file = True, jpeg_quality = options['jpegQuality'])
        arcpy.AddMessage("Exported JPEG")
    elif options['type']== "TIFF":
        arcpy.mapping.ExportToTIFF(mxd,outFile, resolution = options['resolution'], world_file = False, geoTIFF_tags=False)
        arcpy.AddMessage("Exported TIFF")
    elif options['type'] == "GEOTIFF":
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        zrobGeoTIFF(mxd,df, outFile, float(options['resolution']))
        arcpy.AddMessage("Exported GEOTIFF...")
    else:
        arcpy.mapping.ExportToPNG(mxd, outFile,resolution = options['resolution'], world_file = True)
        arcpy.AddMessage("Exported PNG")

    del mxd

    if os.stat(outFile).st_size == 0:
        os.remove(outFile)
        raise Exception('Zero file size generated')

if __name__ == '__main__':

    folder = arcpy.GetParameterAsText(0)


    options = {}
    options['outFolder'] = arcpy.GetParameterAsText(1)
    options['type'] = arcpy.GetParameterAsText(2)
    options['resolution'] = arcpy.GetParameterAsText(3)
    options['pdfImageQuality'] = arcpy.GetParameterAsText(4)
    options['jpegQuality'] = arcpy.GetParameterAsText(5)
    subfolders = arcpy.GetParameterAsText(6).lower()=="false"

    wydruki = checkOutputFolder(options['outFolder'])

    if subfolders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".mxd"):
                    mapPath = os.path.join(root, file)
                    if os.path.splitext(file)[0] not in wydruki:
                        ProcessMxdView(mapPath, options)


    else:
        for file in os.listdir(folder):
            if file.endswith(".mxd"):
                mapPath = os.path.join(folder, file)
                if os.path.splitext(file)[0] not in wydruki:
                    ProcessMxdView(mapPath, options)


