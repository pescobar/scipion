# **************************************************************************
# *
# * Authors:     Antonio Poza Ballesteros (apoza@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'apoza@cnb.csic.es'
# *
# **************************************************************************
"""
This modules contains basic hierarchy
for specific EMAN2 EM data objects
"""

from pyworkflow.em import *
from pyworkflow.utils.path import replaceBaseExt, exists
from glob import glob
import os
import json
            
class EmanCoordinate(Coordinate):
    """This class holds the (x,y) position and other information
    associated with a EMAN coordinate (Eman coordinates are POS_TOPLEFT mode)"""    
    
    def getPosition(self, mode=Coordinate.POS_TOPLEFT):
        """Return the position of the coordinate.
        mode: select if the position is the center of the box
          or in the top left corner."""
        if mode == Coordinate.POS_TOPLEFT:
            return self.x, self.y
        elif mode == Coordinate.POS_CENTER: 
            return (int(self.x) + self._boxSize/2, int(self.y) + self._boxSize/2)
        else:
            raise Exception("No coordinate mode registered for : " + str(mode)) 
    
    def setPosition(self, x, y):
        self.x = x
        self.y = y
    
    def getMicrograph(self):
        """Return the micrograph object to which
        this coordinate is associated"""
        return self._micrograph
    
    def setMicrograph(self, micrograph):
        """Set the micrograph to which this coordinate belongs"""
        self._micrograph = micrograph
    
    def getPair(self):
        """It should return the paired coordinate associate to self.
        If self is an untilted coordinate, getPaired will return the 
        tilted one and viceversa"""
        pass 
    
    
class EmanSetOfCoordinates(SetOfCoordinates):
    """Encapsulate the logic of a set of particles coordinates for EMAN.
    Each coordinate has a (x,y) position and is related to a Micrograph
    The SetOfCoordinates can also have information about TiltPairs.
    EMAN coordinates are taken from top left"""
    def __init__(self, filename=None, **args):
        # Use object value to store filename
        # Here filename is the path to a json file where coordinates (on json format) are linked to micrographs ids
        SetOfCoordinates.__init__(self, value=filename, **args)
        #emanJson = EmanJson(self.getFileName())
        self.jsonDict = loadJson(self.getFileName())
        
    def getFileName(self):
        return self.get()
    
    def getList(self, param):
        """ Return the list asociated to a param """
        list =  self.jsonDict[param]
        return list
        jsonDict
    def getSize(self):
        """ Return the number of coordinates on the set """
        size = len(self.jsonDict["boxes"])
        return size      
        
    def iterMicrographCoordinates(self, micrograph):
        """ Iterates over the set of coordinates belonging to that micrograph. """
        pathJsonPos = self.getMicrographPosFile(micrograph.getId())
        if exists(pathJsonPos):
            coordJson = loadJson(pathJsonPos)
            coordList = coordJson["boxes"]
            for pos in coordList:
                x = pos[0]
                y = pos[1]
                #coorId = mdPos.getValue(xmipp.MDL_ITEM_ID, objId)
                coordinate = EmanCoordinate()
                coordinate.setPosition(x, y)
                coordinate.setMicrograph(micrograph)
                coordinate.setBoxSize(self.boxSize.get())
                coordinate.setId(coorId)        
                yield coordinate
        
#        pathBox = join(path, replaceBaseExt(micrograph.getFileName(), 'box'))
#        if exists(pathBox):
#            boxFile =  open (pathBox,"r")
#            for line in boxFile:
#                if len(line.strip()) > 0:
#                    parts = line.strip().split()
#                    x = parts[0]
#                    y = parts[1]
#                    coordinate = EmanCoordinate()
#                    coordinate.setMicrograph(micrograph)
#                    coordinate.setPosition(x, y)
#                    coordinate.setBoxSize(self.boxSize.get())
#                    yield coordinate
#                else:
#                    pass
#            boxFile.close()
        
    def iterCoordinates(self):
        """ Iterates over the whole set of coordinates.
        If the SetOfMicrographs has tilted pairs, the coordinates
        should have the information related to its paired coordinate.
        """
        for mic in self.getMicrographs():
            for coord in self.iterMicrographCoordinates(mic):
                yield coord

    def getFiles(self):
        return self.jsonDict.values() 
    
    def hasTiltPairs(self):
        """Returns True if the SetOfMicrographs has tilted pairs"""
        return self.getMicrographs().hasTiltPairs()
    
    def getMicrographPosFile(self, micId):
        """ This function will return the pos file corresponding to a micrograph item id"""
        micPosJson = self.jsonDict[micId]
        return micPosJson


class EmanImage(Image):
    """Eman implementation for Image"""
    
    def __init__(self, filename=None, **args):
        Image.__init__(self, filename, **args)

    
class EmanSetOfImages(SetOfImages):
    """Represents a set of Images for Eman"""
               
    def __init__(self, filename=None, **args):
        SetOfImages.__init__(self, filename, **args)
  
    def __iter__(self):
        """ Iterate over the set of images. """
        pass


class EmanSetOfMicrographs(EmanSetOfImages, SetOfMicrographs):
    """Represents a set of particles for eman2"""
    def __init__(self, filename=None, **args):
        EmanSetOfImages.__init__(self, filename, **args)
        SetOfMicrographs.__init__(self, filename, **args)

                
class EmanSetOfParticles(EmanSetOfImages, SetOfParticles):
    """Represents a set of particles for eman2"""
    def __init__(self, filename=None, **args):
        EmanSetOfImages.__init__(self, filename, **args)
        SetOfParticles.__init__(self, filename, **args)


# class EmanJson():
#     """ Utility class to access the Eman Json files """
#     def __init__(self, filename=None, **args):
#         if filename is not None:
#             self.jsonFn = filename
#         else:
#             raise Exception("Json file name is empty")
#     
#     @static
def loadJson(jsonFn):
    """ This function loads the Json dictionary into memory """
    jsonFile = open(jsonFn)
    jsonDict = json.load(jsonFile)
    jsonFile.close()
    return jsonDict

def writeJson(jsonDict, jsonFn):
    """ This function write a Json dictionary """
    with open(jsonFn, 'w') as outfile:
        json.dump(jsonDict, outfile)
    

class EmanVolume(Image):
    """Eman implementation for Volume"""
    def __init__(self, filename=None, **args):
        Image.__init__(self, filename, **args)
#        Volume.__init__(self, filename, **args)    


class EmanSetOfVolumes(EmanSetOfImages, SetOfVolumes):
    """Represents a set of Volumes for Xmipp"""
    def __init__(self, filename=None, **args):
        SetOfVolumes.__init__(self, filename, **args)
        EmanSetOfImages.__init__(self, filename, **args)

    
# def getBoxSize(self):
#     """Method to read boxsize from base.json"""
#     return self.jsonDict["box_size"]

#     from EMAN2db import db_open_dict,db_check_dict,db_close_dict
# 
#     EMBOXERBASE_DB = "bdb:emboxerbase"
#     db = db_open_dict(EMBOXERBASE_DB)
#     boxsize = db.get("box_size",dfl=128)
#     return boxsize


#class EmanDbd():
#    """ Utility class to access the Eman dbd database """
#
#    @staticmethod    
#    def getEmanParamValue(paramName):
#        """ Recover a parameter value from EMAN Berkeley data base. """        
#        command = "e2bdb.py -D bdb:emboxerbase"
#        pipe = os.popen(command)
#        stOutput = pipe.readlines()
#        pipe.close()
#        auxValue = None
#        for line in stOutput:
#            if (paramName in line):
#                auxValue = line.split(" : ")[1]
#        if auxValue is None:
#            raise Exception("Error getting the stored paramter with command: " + command) 
#        return auxValue
#    