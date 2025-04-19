"""
Model exported as python.
Name : RB Safety Bands tool - v.1.0.1
Group : RBTools
With QGIS : 32811
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProperty
import processing


class RbSafetyBandsToolV101(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('left_side_riverbank', 'LEFT side RiverBank', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('left_erosion_rate_field', 'Left Erosion Rate field', type=QgsProcessingParameterField.Numeric, parentLayerParameterName='left_side_riverbank', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('right_side_riverbank', 'RIGHT side riverBank', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('right_erosion_rate_field', 'Right Erosion Rate field', type=QgsProcessingParameterField.Any, parentLayerParameterName='right_side_riverbank', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('m_factor_for_buffers', 'M factor for buffers', type=QgsProcessingParameterNumber.Double, defaultValue=50))
        self.addParameter(QgsProcessingParameterFeatureSink('OffsetLine', 'Offset line', type=QgsProcessing.TypeVectorLine, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Right side Buffer
        alg_params = {
            'DISTANCE': QgsProperty.fromExpression('@m_factor_for_buffers * attribute( @right_erosion_rate_field )'),
            'INPUT': parameters['right_side_riverbank'],
            'JOIN_STYLE': 0,  # Arrotondato
            'MITER_LIMIT': 2,
            'SEGMENTS': 8,
            'SIDE': 1,  # Destra
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RightSideBuffer'] = processing.run('native:singlesidedbuffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Left side buffer
        alg_params = {
            'DISTANCE': QgsProperty.fromExpression('@m_factor_for_buffers * attribute( @left_erosion_rate_field )'),
            'INPUT': parameters['left_side_riverbank'],
            'JOIN_STYLE': 0,  # Arrotondato
            'MITER_LIMIT': 2,
            'SEGMENTS': 8,
            'SIDE': 0,  # Sinistra
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LeftSideBuffer'] = processing.run('native:singlesidedbuffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Union
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['LeftSideBuffer']['OUTPUT'],
            'OVERLAY': outputs['RightSideBuffer']['OUTPUT'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Union'] = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Dissolve
        alg_params = {
            'FIELD': [''],
            'INPUT': outputs['Union']['OUTPUT'],
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Hole fit
        alg_params = {
            'INPUT': outputs['Dissolve']['OUTPUT'],
            'MIN_AREA': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['HoleFit'] = processing.run('native:deleteholes', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # From polygons to line
        alg_params = {
            'INPUT': outputs['HoleFit']['OUTPUT'],
            'OUTPUT': parameters['OffsetLine']
        }
        outputs['FromPolygonsToLine'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OffsetLine'] = outputs['FromPolygonsToLine']['OUTPUT']
        return results

    def name(self):
        return 'RB Safety Bands tool - v.1.0.1'

    def displayName(self):
        return 'RB Safety Bands tool - v.1.0.1'

    def group(self):
        return 'RBTools'

    def groupId(self):
        return 'RBTools'

    def shortHelpString(self):
        return """<html><body><p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:18pt; font-weight:600;">RB Safety Bands tool</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">This algorithm generates safety lines at a distance from the riverbanks, which have been previously divided into reaches. For each segment, a buffer distance is determined using a multiplicative factor of the riverbank erosion rate.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html></p>
<h2>Parametri in ingresso
</h2>
<h3>LEFT side RiverBank</h3>
<p>Vector that contain the LEFT side of Riverbank. 
This vector must contain at least a field with the year erosion rate to be used in calculus</p>
<h3>Left Erosion Rate field</h3>
<p>Name of the field with values of Erosion Rate</p>
<h3>RIGHT side riverBank</h3>
<p>Vector that contain the RIGHT side of Riverbank. 
This vector must contain at least a field with the year erosion rate to be used in calculus</p>
<h3>Right Erosion Rate field</h3>
<p>Name of the field with values of Erosion Rate</p>
<h3>M factor for buffers</h3>
<p>the multiplicative factor of the erosion rate used to determine the buffer distance from riverbanks</p>
<h2>Risultati</h2>
<h3>Offset line</h3>
<p>Multiline vector generated</p>
<h2>Esempi</h2>
<p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html></p><br><p align="right">Autore algoritmo: Author: @gianfrancodp
Phd Student at University of Catania

with contribution of the following at University of Catania:
- Martina Stagnitti
- Valeria Pennisi
- Rosaria Ester Musumeci</p><p align="right">Autore della guida: Author: @gianfrancodp
Phd Student at University of Catania

with contribution of the following at University of Catania:
- Martina Stagnitti
- Valeria Pennisi
- Rosaria Ester Musumeci</p><p align="right">Versione algoritmo: v.1.0.1 - beta</p></body></html>"""

    def helpUrl(self):
        return 'https://github.com/gianfrancodp/qgis-riverbanks-tools'

    def createInstance(self):
        return RbSafetyBandsToolV101()
