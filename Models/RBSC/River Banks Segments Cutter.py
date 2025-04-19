"""
Model exported as python.
Name : River Banks Segments Cutter v.1.1.1
Group : RBTools
With QGIS : 32811
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class RiverBanksSegmentsCutterV111(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        # Line feature with Left riverbank to be used for buffer generation
        self.addParameter(QgsProcessingParameterVectorLayer('left_river_bank', 'Left River Bank', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        # Line feature with Right riverbank ti be used for the buffers generation
        self.addParameter(QgsProcessingParameterVectorLayer('right_riverbank', 'Right RiverBank', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        # Line features that contain the "cutting" separator from two homogeneous stretch of river.
        # 
        self.addParameter(QgsProcessingParameterVectorLayer('river_reach_transect_limits', 'River reach transect limits', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        # Line features that contain the centerline of river.  The vector must be subdivided in single homogeneous stretch. 
        # Field table contain te erosion rate value of every element
        self.addParameter(QgsProcessingParameterVectorLayer('river_centerline_reaches', 'River centerline reaches', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Lrb', 'LRB', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Rrb', 'RRB', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # RIGHT riverbank cut
        alg_params = {
            'INPUT': parameters['right_riverbank'],
            'LINES': parameters['river_reach_transect_limits'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RightRiverbankCut'] = processing.run('native:splitwithlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # LEFT riverbank cut
        alg_params = {
            'INPUT': parameters['left_river_bank'],
            'LINES': parameters['river_reach_transect_limits'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LeftRiverbankCut'] = processing.run('native:splitwithlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Max lenght of separation lines (field calc)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'len',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': '$length',
            'INPUT': parameters['river_reach_transect_limits'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MaxLenghtOfSeparationLinesFieldCalc'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # divider_line_statistics (field stat)
        alg_params = {
            'FIELD_NAME': 'len',
            'INPUT_LAYER': outputs['MaxLenghtOfSeparationLinesFieldCalc']['OUTPUT']
        }
        outputs['Divider_line_statisticsFieldStat'] = processing.run('qgis:basicstatisticsforfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # LEFT RB with field from C (spatial join)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELDS_TO_COPY': [''],
            'INPUT': outputs['LeftRiverbankCut']['OUTPUT'],
            'INPUT_2': parameters['river_centerline_reaches'],
            'MAX_DISTANCE': outputs['Divider_line_statisticsFieldStat']['MAX'],
            'NEIGHBORS': 1,
            'PREFIX': '',
            'OUTPUT': parameters['Lrb']
        }
        outputs['LeftRbWithFieldFromCSpatialJoin'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Lrb'] = outputs['LeftRbWithFieldFromCSpatialJoin']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # RIGHT RB with field from C (spatial join)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELDS_TO_COPY': [''],
            'INPUT': outputs['RightRiverbankCut']['OUTPUT'],
            'INPUT_2': parameters['river_centerline_reaches'],
            'MAX_DISTANCE': outputs['Divider_line_statisticsFieldStat']['MAX'],
            'NEIGHBORS': 1,
            'PREFIX': '',
            'OUTPUT': parameters['Rrb']
        }
        outputs['RightRbWithFieldFromCSpatialJoin'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Rrb'] = outputs['RightRbWithFieldFromCSpatialJoin']['OUTPUT']
        return results

    def name(self):
        return 'River Banks Segments Cutter v.1.1.1'

    def displayName(self):
        return 'River Banks Segments Cutter v.1.1.1'

    def group(self):
        return 'RBTools'

    def groupId(self):
        return 'RBTools'

    def shortHelpString(self):
        return """<html><body><p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<h1 style=" margin-top:18px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:xx-large; font-weight:600;">RB Segments Cutter</span></h1>
<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">This model algorytm separate RiverBanks (RB) into single segments using the stretches of the River Centerline (RC) vector.<br />New elements will inherit the field table values from RC.</p>
<h2 style=" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:x-large; font-weight:600;">Procedure description</span></h2>
<ul style="margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 0;"><li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Step #1: Cut RB with separation lines vector</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Step #2: Get the max lenght of separation lines feature</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Step #3: Use &quot;proximity&quot; join (with a threshold distance provided from Step #2) to inherit field table values from RC to RB</li></ul></body></html></p>
<h2>Parametri in ingresso
</h2>
<h3>Left River Bank</h3>
<p>LBR: Line or multiline feature with Left riverbank to consider.
This model is tested with a single-feature vector</p>
<h3>Right RiverBank</h3>
<p>RBR: Line or multiline feature with Right riverbank to consider.
This model is tested with a single-feature vector</p>
<h3>River reach transect limits</h3>
<p>Cutter geometry used to segment and cut riverbanks.
The best thing is to use specific transects at the exact point where the river is divided into distinct reaches.
This vector must be complaiant with the River centerline reaches vector. </p>
<h3>River centerline reaches</h3>
<p>Line features that contain the centerline of river.  The vector must be subdivided in single homogeneous stretch. 
Field table contain te erosion rate value of every element</p>
<br><p align="right">Autore algoritmo: Author: @gianfrancodp
Phd Student at University of Catania

with contribution of the following at University of Catania:
- Martina Stagnitti
- Valeria Pennisi
- Rosaria Ester Musumeci</p><p align="right">Autore della guida: Author: @gianfrancodp
Phd Student at University of Catania

with contribution of the following at University of Catania:
- Martina Stagnitti
- Valeria Pennisi
- Rosaria Ester Musumeci</p><p align="right">Versione algoritmo: v.1.1.1</p></body></html>"""

    def helpUrl(self):
        return 'https://github.com/gianfrancodp/qgis-riverbanks-tools'

    def createInstance(self):
        return RiverBanksSegmentsCutterV111()
