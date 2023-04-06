from mikeio1d.res1d import Res1D
from mikeio1d.dotnet import to_numpy

import arcpy, os

def readNodeWL(res1dFile):
    nodeWL = {}
    res1d = Res1D(res1dFile)
    for n in res1d.data.Nodes:
        # print(str(n))
        try:
            rv = round(float(res1d.get_node_values(str(n).split(' ')[1], 'WaterLevel').max()), 2)
            nodeWL[str(n).split(' ')[1]] = rv
        except:
            print("Nie dodano wezla - "+str(n))
    return nodeWL

def getChainage(reachData):
    s1 = str(reachData).split(' ')[-1]
    s2 = s1.replace('(', '')
    s3 = s2.replace(')', '')
    chainages = s3.split('-')
    chainages = [float(chainages[0]), float(chainages[1].replace(',', '.'))]
    return chainages

def readReachDEPTH(res1dFile):
    reachDEPTH = {}
    res1d = Res1D(res1dFile)
    # print(res1d.quantities)
    for n in res1d.data.Reaches:
        chanages = getChainage(n)
        # może byc problem z dopasowaniem kiedy w MUID kolektora zostanie wstawiona '-'
        reachID = str(n).split(' ')[1].split('-')[0]
        # print(n, reachID, chanages)
        for chainage in chanages:
            rv_max = to_numpy(res1d.query.GetReachValues(reachID, chainage, 'WaterLevel')).max()
            rv_min = to_numpy(res1d.query.GetReachValues(reachID, chainage, 'WaterLevel')).min()
            rv = rv_max - rv_min
            if reachID not in reachDEPTH:
                reachDEPTH[reachID] = rv
            elif reachDEPTH[reachID] < rv:
                reachDEPTH[reachID] = rv

    return reachDEPTH

def writeNodeDEPTH(outputGdb, nodeWL):
    out_data = os.path.join(outputGdb, 'msm_Node')
    field_names = [f.name for f in arcpy.ListFields(out_data)]
    if 'Result' not in field_names:
        arcpy.AddField_management(out_data, 'Result', "DOUBLE")
    with arcpy.da.UpdateCursor(out_data, ['MUID', 'GroundLevel', 'Result'])as cur:
        for row in cur:
            try:
                row[2] = nodeWL[row[0]] - row[1]
                cur.updateRow(row)
            except KeyError:
                print("Nie dodano wezla o ID {0}".format(row[0]))
                row[2] = -99.0
                cur.updateRow(row)
    del cur
    return

def writeReachPF(outputGdb, reachDEPTH):
    out_data = os.path.join(outputGdb, 'msm_Link')
    field_names = [f.name for f in arcpy.ListFields(out_data)]
    if 'Result' not in field_names:
        arcpy.AddField_management(out_data, 'Result', "DOUBLE")
    with arcpy.da.UpdateCursor(out_data, ['MUID', 'Diameter', 'Result']) as cur:
        for row in cur:
            try:
                row[2] = round(float(reachDEPTH[row[0]])/row[1], 3)
                cur.updateRow(row)
            except KeyError:
                print("Nie dodano kolektora o ID {0}".format(row[0]))
                row[2] = 0.0
                cur.updateRow(row)
            except TypeError:
                print("Nie dodano kolektora o ID {0}".format(row[0]))
                row[2] = 0.0
                cur.updateRow(row)

    del cur
    return

if __name__ == '__main__':
    res = arcpy.GetParameterAsText(0)
    resGdb = arcpy.GetParameterAsText(1)

    arcpy.AddMessage("1-Pobieranie wynikow wezlow...")
    nodeWL = readNodeWL(res)

    arcpy.AddMessage("2-Pobieranie wynikow kolektorow...")
    reachWL = readReachDEPTH(res)

    arcpy.AddMessage("3-Zapisywanie wartosci 'Wypelnienia studzienek' do kolumny 'Result' wezlow...")
    writeNodeDEPTH(resGdb, nodeWL)

    arcpy.AddMessage("4-Zapisywanie wartosci 'Pipe filling' do kolumny 'Result' kolektorow...")
    writeReachPF(resGdb, reachWL)
