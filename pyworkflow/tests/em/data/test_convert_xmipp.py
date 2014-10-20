#!/usr/bin/env python
# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (jmdelarosa@cnb.csic.es)
# *              Roberto Marabini       (roberto@cnb.csic.es)
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
# *  e-mail address 'jmdelarosa@cnb.csic.es'
# *
# **************************************************************************

import os
from pyworkflow.em.data import SetOfVolumes
import unittest

import xmipp
from pyworkflow.em.packages.xmipp3 import *
from pyworkflow.tests import *
from pyworkflow.em.packages.xmipp3.convert import *



class TestBasic(BaseTest):
    """ Test most basic conversions of the form:
    rowToObject(row, ...)
    objectToRow(obj, row, ...)
    """
    
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('xmipp_tutorial')  
        cls.dbGold = cls.dataset.getFile( 'micsGoldSqlite')
        cls.particles = cls.dataset.getFile( 'particles1')
        
    def getCTF(self, u, v, angle):
        ctf = CTFModel(defocusU=u, defocusV=v, defocusAngle=angle)
        ctf.standardize()
        return ctf
    
    def test_rowToCtfModel(self):
        row = XmippMdRow()
        row.setValue(xmipp.MDL_CTF_DEFOCUSU, 2520.)
        row.setValue(xmipp.MDL_CTF_DEFOCUSV, 2510.)
        row.setValue(xmipp.MDL_CTF_DEFOCUS_ANGLE, 45.)
        
        ctf = rowToCtfModel(row)
        ctf.printAll()        
        # Check that the ctf object was properly set
        self.assertTrue(ctf.equalAttributes(self.getCTF(2520., 2510., 45.)))
        # Check when the EMX standarization takes place
        row.setValue(xmipp.MDL_CTF_DEFOCUSV, 2530.)
        ctf = rowToCtfModel(row)
        self.assertTrue(ctf.equalAttributes(self.getCTF(2530., 2520., 135.)))
        
        # When one of CTF labels is missing, None should be returned
        row.removeLabel(xmipp.MDL_CTF_DEFOCUSV)
        ctf = rowToCtfModel(row)       
        self.assertIsNone(ctf)
        
    def test_rowToImage(self):
        row = XmippMdRow()
        index = 1
        filename = 'images.stk'
        row.setValue(xmipp.MDL_ITEM_ID, 1)
        row.setValue(xmipp.MDL_IMAGE, '%d@%s' % (index, filename))
        
        img = rowToImage(row, xmipp.MDL_IMAGE, Particle)
        
        # Check correct index and filename
        self.assertEquals(index, img.getIndex())
        self.assertEquals(filename, img.getFileName())


class AlignmentList(list):
    """ Utility class to store alignments. """
    def append(self, matrixList):
        list.append(self, Alignment(np.array(matrixList)))


class TestAlignmentConvert(BaseTest):
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('emx')
    
    def test_isInverse(self):
        def _testInv(matrixList):
            a = Alignment(matrixList)
            
            row = XmippMdRow()
            alignmentToRow(a, row, is2D=True, inverseTransform=False)
            print "isInv=False, row", row      
            
            row2 = XmippMdRow()
            alignmentToRow(a, row2, is2D=True, inverseTransform=True)
            print "isInv=True, row2", row2
          
        _testInv([[1.0, 0.0, 0.0, 20.0],
                  [0.0, 1.0, 0.0, 0.0],
                  [0.0, 0.0, 1.0, 0.0],
                  [0.0, 0.0, 0.0, 1.0]])
          
        _testInv([[0.93969, 0.34202, 0.0, -6.8404],
                  [-0.34202, 0.93969, 0.0, 18.7939],
                  [0.0, 0.0, 1.0, 0.0],
                  [0.0, 0.0, 0.0, 1.0]])    


    def launchAlignmentTest(self, fileKey, mList,
                            is2D=True, inverseTransform=False,
                            **kwargs):
        """ Helper function to launch similar alignment tests
        give the EMX transformation matrix.
        Params:
            fileKey: the file where to grab the input stack images.
            mList: the matrix list of transformations 
                (should be the same length of the stack of images)
        """
        print "\n"
        print "*" * 80
        print "* Launching test: ", fileKey
        print "*" * 80
        
        stackFn = self.dataset.getFile(fileKey)
        partFn1 = self.getOutputPath(fileKey + "_particles1.sqlite")
        mdFn = self.getOutputPath(fileKey + "_particles.xmd")
        partFn2 = self.getOutputPath(fileKey + "_particles2.sqlite")
        print "BINARY DATA: ", stackFn
        print "SET1: ", partFn1
        print "  MD: ", mdFn
        print "SET2: ", partFn2  
        
        if is2D:
            partSet = SetOfParticles(filename=partFn1)
        else:
            partSet = SetOfVolumes(filename=partFn1)
        partSet.setAcquisition(Acquisition(voltage=300,
                                  sphericalAberration=2,
                                  amplitudeContrast=0.1,
                                  magnification=60000))
        # Populate the SetOfParticles with  images
        # taken from images.mrc file
        # and setting the previous alignment parameters
        aList = [np.array(m) for m in mList]
        for i, a in enumerate(aList):
            p = Particle()
            p.setLocation(i+1, stackFn)
            p.setAlignment(Alignment(a))
            partSet.append(p)
        # Write out the .sqlite file and check that are correctly aligned
        partSet.write()

        # Convert to a Xmipp metadata and also check that the images are
        # aligned correctly
        if is2D:
            writeSetOfParticles(partSet, mdFn, is2D=is2D, inverseTransform=inverseTransform)
        else:
            writeSetOfVolumes(partSet, mdFn, is2D=is2D, inverseTransform=inverseTransform)
        # Let's create now another SetOfImages reading back the written
        # Xmipp metadata and check one more time.
        partSet2 = SetOfParticles(filename=partFn2)
        partSet2.copyInfo(partSet)
        if is2D:
            readSetOfParticles(mdFn, partSet2, is2D=is2D,
                               inverseTransform=(not inverseTransform))
        else:
            readSetOfParticles(mdFn, partSet2, is2D=is2D,
                               inverseTransform=not inverseTransform)
            
        partSet2.write()         
        #TODO_rob: I do not know how to make an assert here
        #lo que habria que comprobar es que las imagenes de salida son identicas a la imagen 3
        #inverse has no effect

        if kwargs.get('printMatrix', False):
            for i, img in enumerate(partSet2):
                m1 = aList[i]
                m2 = img.getAlignment().getMatrix()
                print "-"*5
                print img.getFileName(), img.getIndex()
                print 'm1:\n', m1
                print 'm2:\n', m2
                #self.assertTrue(np.array_equiv(m1, m2))
        
    def test_alignment(self):
        mList = [[[ 1.0, 0.0, 0.0, 20.0],                  
                  [ 0.0, 1.0, 0.0,  0.0],
                  [ 0.0, 0.0, 1.0,  0.0],
                  [ 0.0, 0.0, 0.0,  1.0]],
                 [[0.86602539, 0.5, 0.0, 20.0],
                  [ -0.5,0.86602539, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[0.86602539, 0.5, 0.0, 27.706396],
                  [ -0.5,0.86602539, 0.0,0.331312],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[0.5, 0.86602539, 0.0, 3.239186],
                  [ -0.86602539, 0.5, 0.0,20.310715],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 0.0, 1.0, 0.0, 10.010269],
                  [ -1.0, 0.0, 0.0, 3.6349521],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]
        
        self.launchAlignmentTest('alignment', mList, 
                         is2D=True, inverseTransform=True,
                         printMatrix=True) 
        
    def test_alignment3D(self):
        """
        0.71461016 0.63371837 -0.29619813         15 
        -0.61309201 0.77128059 0.17101008         25 
        0.33682409 0.059391174 0.93969262         35 
                 0          0          0          1
        """
        mList = [[[ 0.71461016, 0.63371837, -0.29619813, 15], 
                  [ -0.61309201, 0.77128059, 0.17101008, 25], 
                  [ 0.33682409, 0.059391174, 0.93969262, 35], 
                  [ 0,          0,           0,           1]],
                 
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]
        
        self.launchAlignmentTest('alignment3D', mList, 
                         is2D=False, inverseTransform=True,
                         printMatrix=True)   
              
    def test_rotOnly(self):
        """ Check that a given alignment object,
        the Xmipp metadata row is generated properly.
        mList[0] * (0,32,0,1)' -> (32,0,0,1)'  T -> ref
        mList[1] * (-32,0,0,1)' -> (32,0,0,1)'
        """
        mList = [[[ 0.0, 1.0, 0.0, 0.0],
                  [-1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[-1.0, 0.0, 0.0, 0.0],
                  [ 0.0,-1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]
        
        self.launchAlignmentTest('alignRotOnly', mList,
                                 is2D=True, inverseTransform=True,
                                 printMatrix=True)

    def test_rotOnly3D(self):
        """ Check that a given alignment object,
        the Xmipp metadata row is generated properly.
           mList[0] * (22.8586, -19.6208, 10.7673)' -> (32,0,0,1); T -> ref
           mList[1] * (22.8800, 20.2880, -9.4720) ->(32,0,0,1)'; T -> ref
        """
        #TODO NOTE: inverseTRansform is true for 3D
        #but false for 2D in aligment!!!! This should be corrected
        #angles checked with transform geometry What else can
        #  I do for checking!!!!!
        
        mList = [[[ 0.715,-0.613, 0.337, 0.],
                  [ 0.634, 0.771, 0.059, 0.],
                  [-0.296, 0.171, 0.94,  0.],
                  [ 0.   , 0.   , 0.,    1.]],
                 [[ 0.71433,   0.63356,  -0.29586,   -0.00000],
                  [ -0.61315,   0.77151,   0.17140,  -0.00000],
                  [  0.33648,   0.05916,   0.93949,  -0.00000],
                  [  0.00000,   0.00000,   0.00000,   1.00000]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]

        self.launchAlignmentTest('alignRotOnly3D', mList,
                                 is2D=False, inverseTransform=True,
                                 printMatrix=True)
        #TODO:now read result, apply xmipp_transform geometry....<<<<<<<<<<
    def test_shiftOnly(self):
        """ Check that a given alignment object,
        the Xmipp metadata row is generated properly.
         mList[0] * ( 32,0,0,1)-> (0,0,0,1); T -> ref
         mList[1] * (  0,32,0,1)-> (0,0,0,1); T -> ref

        """
        mList = [[[ 1.0, 0.0, 0.0, -32.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, -32.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]
        
        self.launchAlignmentTest('alignShiftOnly', mList, 
                                 is2D=True, inverseTransform=True,
                                 printMatrix=True)

    def test_shiftOnly3D(self):
        """ Check that a given alignment object,
        the Xmipp metadata row is generated properly.
        """
        mList = [[[ 1.0, 0.0, 0.0, 32.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 16.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 8.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]
        
        self.launchAlignmentTest('alignShiftOnly3D', mList, 
                                 is2D=False, inverseTransform=True,
                                 printMatrix=True)
        
    def test_shiftRot(self):
        """ Check that a given alignment object,
        the Xmipp metadata row is generated properly.
        note that when rot and shift are involved
        the correct transformation matrix is
        rot matrix + rot*shift
        mList[0] * (16,32,0) -> (32,0,0)
        mList[1] * (-32,16,0) -> (32,0,0)
        """
        mList = [[[ 0.0, 1.0, 0.0, 0.0],                  
                  [-1.0, 0.0, 0.0,16.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[-1.0, 0.0, 0.0, 0.0],
                  [ 0.0,-1.0, 0.0,16.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]],
                 [[ 1.0, 0.0, 0.0, 0.0],
                  [ 0.0, 1.0, 0.0, 0.0],
                  [ 0.0, 0.0, 1.0, 0.0],
                  [ 0.0, 0.0, 0.0, 1.0]]]
        
        self.launchAlignmentTest('alignShiftRot', mList, 
                         is2D=True, inverseTransform=True,
                         printMatrix=True)


    def test_rowToAlignment2D(self):
        """ Check that given a row with the alignment
        parameters (shiftx, shifty, rot and flip)
        the proper alignment matrix is built.
        """
        row = XmippMdRow()
        row.setValue(xmipp.MDL_SHIFT_X, 10.)
        row.setValue(xmipp.MDL_SHIFT_Y, 10.)
        row.setValue(xmipp.MDL_ANGLE_ROT, 0.)
        row.setValue(xmipp.MDL_FLIP, False)
        
        alignment = rowToAlignment(row)
        alignment.printAll()      
        
    def aaatest_readWriteParticles(self):
        mdFn = self.dataset.getFile('particles/xmipp_particles.xmd') 
        print "INPUT MD: ", mdFn
        md = xmipp.MetaData(mdFn)
        imgFn = self.getOutputPath('particles.sqlite')
        imgSet = SetOfParticles(filename=imgFn)
        readSetOfParticles(mdFn, imgSet)
        
        outputFn = self.getOutputPath('particles.xmd')
        print "OUTPUT MD: ", outputFn
        writeSetOfParticles(imgSet, outputFn)
        mdOut = xmipp.MetaData(outputFn)
        
        
        
    
class TestSetConvert(BaseTest):
    
    @classmethod
    def setUpClass(cls):
        setupTestOutput(cls)
        cls.dataset = DataSet.getDataSet('xmipp_tutorial')  
        cls.dbGold = cls.dataset.getFile( 'micsGoldSqlite')
        cls.particles = cls.dataset.getFile( 'particles1')        
    
    def test_metadataToParticles(self):
        """ This test will read a set of particles from a given metadata.
        The resulting set should contains the x and y coordinates from
        the particle picking. 
        """
        fn = self.dataset.getFile('images10')
        partSet = SetOfParticles(filename=self.getOutputPath('particles_coord.sqlite'))
        readSetOfParticles(fn, partSet)
        
        self.assertEquals(partSet.getSize(), 10)
        self.assertTrue(partSet.hasCTF())
        
        for img in partSet:
            self.assertTrue(img.getCoordinate() is not None)    
            self.assertTrue(img.hasCTF())
            
        mdIn = xmipp.MetaData(fn)
        #print mdIn
        
        mdOut = xmipp.MetaData()
        setOfParticlesToMd(partSet, mdOut)
        #print mdOut
        
        # Labels order is not the same
        # TODO: Implement a better way to compare two metadatas
        #self.assertEqual(mdIn, mdOut)
        
    def test_metadataToParticleAndBack(self):
        imgsFn="/home/coss/ScipionUserData/projects/CL2D/input.xmd"
        outputFn="/home/coss/ScipionUserData/projects/CL2D/output.xmd"
        alignedSet = SetOfParticles(filename='/home/coss/ScipionUserData/projects/CL2D/metadataWithAlignment.sqlite')
        readSetOfParticles(imgsFn, alignedSet, is2D=True, inverseTransform=False)
        alignedSet.write()
        writeSetOfParticles(alignedSet, outputFn, is2D=True, inverseTransform=False)
        
    def test_micrographsToMd(self):
        """ Test the convertion of a SetOfMicrographs to Xmipp metadata. """
        micSet = SetOfMicrographs(filename=self.getOutputPath("micrographs.sqlite"))
        n = 3
        ctfs = [CTFModel(defocusU=10000, defocusV=15000, defocusAngle=15),
                CTFModel(defocusU=20000, defocusV=25000, defocusAngle=25)
               ]
        acquisition = Acquisition(magnification=60000, 
                                  voltage=300,
                                  sphericalAberration=2., 
                                  amplitudeContrast=0.07)
        micSet.setAcquisition(acquisition)
        micSet.setSamplingRate(1.)
        mdXmipp = xmipp.MetaData()
        

        for i in range(n):
            p = Micrograph()
            file = self.dataset.getFile("mic%s"%(i + 1))
            p.setLocation(file)
            ctf = ctfs[i%2]
            p.setCTF(ctf)
            micSet.append(p)
            id = mdXmipp.addObject()
            mdXmipp.setValue(xmipp.MDL_ITEM_ID, long(i+1), id)
            mdXmipp.setValue(xmipp.MDL_MICROGRAPH, file, id)
            # set CTFModel params
            mdXmipp.setValue(xmipp.MDL_CTF_DEFOCUSU, ctf.getDefocusU(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_DEFOCUSV, ctf.getDefocusV(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_DEFOCUS_ANGLE, ctf.getDefocusAngle(), id)
            # set Acquisition params
            mdXmipp.setValue(xmipp.MDL_CTF_Q0, acquisition.getAmplitudeContrast(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_CS, acquisition.getSphericalAberration(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_VOLTAGE, acquisition.getVoltage(), id)
            
        mdScipion = xmipp.MetaData()
        setOfMicrographsToMd(micSet, mdScipion)
        writeSetOfMicrographs(micSet, self.getOutputPath("micrographs.xmd"))
        self.assertEqual(mdScipion, mdXmipp, "metadata are not the same")
        
    def test_alignedParticlesToMd(self):
        """ Test the convertion of a SetOfParticles to Xmipp metadata. """
        fn = self.dataset.getFile('aligned_particles')
        print "Converting sqlite: %s" % fn
        imgSet = SetOfParticles(filename=fn) 
        imgSet.setAcquisition(Acquisition(magnification=60000,
                                          voltage=300,
                                          sphericalAberration=0.1,
                                          amplitudeContrast=0.1))
        
        md = xmipp.MetaData()
        setOfParticlesToMd(imgSet, md)
        
        # test that the metadata contains some geometry labels
        self.assertTrue(md.containsLabel(xmipp.MDL_SHIFT_X))
        fn = self.getOutputPath("aligned_particles.xmd")
        #print "Aligned particles written to: ", fn
        #md.write(fn)
        
        #self.assertEqual(mdScipion, mdXmipp, "metadata are not the same")

        
    def test_particlesToMd(self):
        """ Test the convertion of a SetOfParticles to Xmipp metadata. """
        imgSet = SetOfParticles(filename=self.getOutputPath("particles.sqlite"))
        n = 10
        fn = self.particles
        ctfs = [CTFModel(defocusU=10000, defocusV=15000, defocusAngle=15),
                CTFModel(defocusU=20000, defocusV=25000, defocusAngle=25)
               ]
        acquisition = Acquisition(magnification=60000, voltage=300,
                                  sphericalAberration=2., amplitudeContrast=0.07)
        mdXmipp = xmipp.MetaData()
        imgSet.setAcquisition(acquisition)

        for i in range(n):
            p = Particle()
            p.setLocation(i+1, fn)
            ctf = ctfs[i%2]
            p.setCTF(ctf)
            p.setAcquisition(acquisition)
            imgSet.append(p)
            id = mdXmipp.addObject()
            mdXmipp.setValue(xmipp.MDL_ITEM_ID, long(i+1), id)
            mdXmipp.setValue(xmipp.MDL_IMAGE, locationToXmipp(i+1, fn), id)
            # set CTFModel params
            mdXmipp.setValue(xmipp.MDL_CTF_DEFOCUSU, ctf.getDefocusU(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_DEFOCUSV, ctf.getDefocusV(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_DEFOCUS_ANGLE, ctf.getDefocusAngle(), id)
            # set Acquisition params
            mdXmipp.setValue(xmipp.MDL_CTF_Q0, acquisition.getAmplitudeContrast(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_CS, acquisition.getSphericalAberration(), id)
            mdXmipp.setValue(xmipp.MDL_CTF_VOLTAGE, acquisition.getVoltage(), id)
            
        mdScipion = xmipp.MetaData()
        setOfParticlesToMd(imgSet, mdScipion)
        self.assertEqual(mdScipion, mdXmipp, "metadata are not the same")
        
                
    def test_CTF(self):
        """ Test the convertion of a SetOfParticles to Xmipp metadata. """
        mdCtf = xmipp.MetaData(self.dataset.getFile('ctfGold'))
        objId = mdCtf.firstObject()
        rowCtf = rowFromMd(mdCtf, objId)
        ctf = rowToCtfModel(rowCtf)        
        
        ALL_CTF_LABELS = [   
            xmipp.MDL_CTF_CA,
            xmipp.MDL_CTF_ENERGY_LOSS,
            xmipp.MDL_CTF_LENS_STABILITY,
            xmipp.MDL_CTF_CONVERGENCE_CONE,
            xmipp.MDL_CTF_LONGITUDINAL_DISPLACEMENT,
            xmipp.MDL_CTF_TRANSVERSAL_DISPLACEMENT,
            xmipp.MDL_CTF_K,
            xmipp.MDL_CTF_BG_GAUSSIAN_K,
            xmipp.MDL_CTF_BG_GAUSSIAN_SIGMAU,
            xmipp.MDL_CTF_BG_GAUSSIAN_SIGMAV,
            xmipp.MDL_CTF_BG_GAUSSIAN_CU,
            xmipp.MDL_CTF_BG_GAUSSIAN_CV,
            xmipp.MDL_CTF_BG_SQRT_K,
            xmipp.MDL_CTF_BG_SQRT_U,
            xmipp.MDL_CTF_BG_SQRT_V,
            xmipp.MDL_CTF_BG_SQRT_ANGLE,
            xmipp.MDL_CTF_BG_BASELINE,
            xmipp.MDL_CTF_BG_GAUSSIAN2_K,
            xmipp.MDL_CTF_BG_GAUSSIAN2_SIGMAU,
            xmipp.MDL_CTF_BG_GAUSSIAN2_SIGMAV,
            xmipp.MDL_CTF_BG_GAUSSIAN2_CU,
            xmipp.MDL_CTF_BG_GAUSSIAN2_CV,
            xmipp.MDL_CTF_BG_GAUSSIAN2_ANGLE,
            xmipp.MDL_CTF_CRIT_FITTINGSCORE,
            xmipp.MDL_CTF_CRIT_FITTINGCORR13,
            xmipp.MDL_CTF_DOWNSAMPLE_PERFORMED,
            xmipp.MDL_CTF_CRIT_PSDVARIANCE,
            xmipp.MDL_CTF_CRIT_PSDPCA1VARIANCE,
            xmipp.MDL_CTF_CRIT_PSDPCARUNSTEST,
            xmipp.MDL_CTF_CRIT_FIRSTZEROAVG,
            xmipp.MDL_CTF_CRIT_DAMPING,
            xmipp.MDL_CTF_CRIT_FIRSTZERORATIO,
            xmipp.MDL_CTF_CRIT_PSDCORRELATION90,
            xmipp.MDL_CTF_CRIT_PSDRADIALINTEGRAL,
            xmipp.MDL_CTF_CRIT_NORMALITY,  
        ]      

        for label in ALL_CTF_LABELS:
            attrName = '_xmipp_%s' % xmipp.label2Str(label)
            self.assertAlmostEquals(mdCtf.getValue(label, objId), ctf.getAttributeValue(attrName))
        
    def test_writeSetOfDefocusGroups(self):
        #reference metadata
        md = xmipp.MetaData()
        objId = md.addObject()
        defocusGroupRow = XmippMdRow()

        defocusGroupRow.setValue(xmipp.MDL_CTF_GROUP, 1)
        defocusGroupRow.setValue(xmipp.MDL_MIN, 2000.)
        defocusGroupRow.setValue(xmipp.MDL_MAX, 2500.)
        defocusGroupRow.setValue(xmipp.MDL_AVG, 2100.)
        defocusGroupRow.writeToMd(md, objId)

        objId = md.addObject()
        defocusGroupRow.setValue(xmipp.MDL_CTF_GROUP, 2)
        defocusGroupRow.setValue(xmipp.MDL_MIN, 3000.)
        defocusGroupRow.setValue(xmipp.MDL_MAX, 5500.)
        defocusGroupRow.setValue(xmipp.MDL_AVG, 5000.)
        defocusGroupRow.writeToMd(md, objId)
        #
        fnScipion=self.getOutputPath("writeSetOfDefocusGroups.sqlite")
        setOfDefocus = SetOfDefocusGroup(filename=fnScipion)

        df = DefocusGroup()
        df.setDefocusMin(2000.)
        df.setDefocusMax(2500.)
        df.setDefocusAvg(2100.)
        setOfDefocus.append(df)
        
        df.cleanObjId()
        df.setDefocusMin(3000)
        df.setDefocusMax(5500)
        df.setDefocusAvg(5000)
        setOfDefocus.append(df)
        
        fnXmipp=self.getOutputPath("writeSetOfDefocusGroups.xmd")
        writeSetOfDefocusGroups(setOfDefocus, fnXmipp)
        mdAux = xmipp.MetaData(fnXmipp)
        self.assertEqual(md,mdAux, "test writeSetOfDefocusGroups fails")
       
