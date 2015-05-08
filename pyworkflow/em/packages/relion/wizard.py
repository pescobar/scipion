# **************************************************************************
# *
# * Authors:     Jose Gutierrez (jose.gutierrez@cnb.csic.es)
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
from pyworkflow.em.packages.relion.protocol_autopick import ProtRelionAutopick
"""
This module implement some wizards
"""

from pyworkflow.em.packages.xmipp3.constants import *

from constants import *
from pyworkflow.em import *
from pyworkflow.em.wizard import *
from protocol_classify3d import ProtRelionClassify3D
from protocol_refine3d import ProtRelionRefine3D
from protocol_classify2d import ProtRelionClassify2D
from protocol_preprocess import ProtRelionPreprocessParticles
from protocol_autopick import ProtRelionAutopickFom

#===============================================================================
# MASKS
#===============================================================================

class RelionBackRadiusWizard(ParticleMaskRadiusWizard):
    _targets = [
#                 (ProtRelionClassify2D, ['backRadius']),
#                 (ProtRelionRefine3D, ['backRadius']),
#                 (ProtRelionClassify3D, ['backRadius']),
#                 (ProtRelionClassify2D, ['backRadius']),
                (ProtRelionPreprocessParticles, ['backRadius'])]
    _unit = UNIT_PIXEL
    
    def _getProtocolImages(self, protocol):
        return protocol.inputParticles
    
    def _getParameters(self, protocol):
        
        label, value = self._getInputProtocol(self._targets, protocol)
        
        protParams = {}
        protParams['input']= self._getProtocolImages(protocol)
        protParams['label']= label
        protParams['value']= value
        return protParams  
    
    def _getProvider(self, protocol):
        _objs = self._getParameters(protocol)['input']    
        return ParticleMaskRadiusWizard._getListProvider(self, _objs)
    
    def show(self, form):
        params = self._getParameters(form.protocol)
        _value = params['value']
        _label = params['label']
        ParticleMaskRadiusWizard.show(self, form, _value, _label, units=self._unit)


class RelionPartMaskDiameterWizard(RelionBackRadiusWizard):
    _targets = [(ProtRelionClassify2D, ['maskDiameterA']),
                (ProtRelionRefine3D, ['maskDiameterA']),
                (ProtRelionClassify3D, ['maskDiameterA']),
                (ProtRelionClassify2D, ['maskDiameterA'])]
    _unit = UNIT_ANGSTROM
    
    def _getParameters(self, protocol):
        protParams = RelionBackRadiusWizard._getParameters(self, protocol)
        # adjust to from diameter to radius
        protParams['value'] = protParams['value'] / 2
        
        return protParams 
    
    def setVar(self, form, label, value):
        # adjust again from radius to diameter
        form.setVar(label, value * 2)

        
#===============================================================================
# FILTER
#===============================================================================

class RelionVolFilterWizard(FilterVolumesWizard):
    _targets = [(ProtRelionClassify3D, ['initialLowPassFilterA']),
                (ProtRelionRefine3D, ['initialLowPassFilterA'])]
    
    def _getParameters(self, protocol):
        
        label, value = self._getInputProtocol(self._targets, protocol)
        
        protParams = {}
        protParams['input']= protocol.referenceVolume
        protParams['label']= label
        protParams['value']= value
        protParams['mode'] = FILTER_LOW_PASS_NO_DECAY
        return protParams  
    
    def _getProvider(self, protocol):
        _objs = self._getParameters(protocol)['input']    
        return FilterVolumesWizard._getListProvider(self, _objs)
    
    # def show(self, form):
    #     params = self._getParameters(form.protocol)
    #     # Value should be LowFreq=0, HighFreq and Decay for Low pass filter
    #     _value = params['value']
    #     _label = params['label']
    #     FilterVolumesWizard.show(self, form, _value, _label,
    #                              mode=FILTER_LOW_PASS,
    #                              unit=UNIT_ANGSTROM,
    #                              showDecay=False)

    def show(self, form):
        params = self._getParameters(form.protocol)
        protocol = form.protocol
        provider = self._getProvider(protocol)

        if provider is not None:

            args = {'mode': params['mode'],
                    'highFreq': params['value'],
                    'unit': UNIT_ANGSTROM
                    }

            args['showLowFreq'] = False
            args['showDecay'] = False

            d = BandPassFilterDialog(form.root, provider, **args)

            if d.resultYes():
                form.setVar('initialLowPassFilterA', d.samplingRate/d.getHighFreq())

        else:
            dialog.showWarning("Input volumes", "Select volumes first", form.root)
            

#===============================================================================
# PICKING
#===============================================================================

class RelionPartDiameter(RelionPartMaskDiameterWizard):  
    _targets = [(ProtRelionAutopickFom, ['particleDiameter'])]
    
    def _getProtocolImages(self, protocol):
        return protocol.inputReferences 


class RelionAutopickParams(EmWizard):  
    _targets = [(ProtRelionAutopick, ['pickingThreshold',
                                      'interParticleDistance'])]
    
    def show(self, form):
        autopickProt = form.protocol
        autopickFomProt = autopickProt.getInputAutopick()
        params = autopickFomProt.getAutopickParams()
        # Get current values of the properties
        _, values = self._getInputProtocol(self._targets, autopickProt)
        threshold, distance = values
        autopickFomProt.setStepsExecutor() # allow to use runJob
        autopickFomProt.autopickStep(params, 
                                     threshold, distance, 
                                     '--read_fom_maps')
        print "Writing Xmipp coordinate files."
        micFn, coordDir = autopickFomProt.writeXmippCoords()
        print "Launching picking GUI..."
        CoordinatesObjectView(autopickProt.getProject(), micFn, coordDir).show()
                                     
    
    