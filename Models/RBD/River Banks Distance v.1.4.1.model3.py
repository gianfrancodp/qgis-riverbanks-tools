"""
Model exported as python.
Name : River Banks Distance v.1.4.1
Group : RBTools
GNU GENERAL PUBLIC LICENSE: Gianfranco Di Pietro
PhD Student - gianfranco.dipietro@phd.unict.it
Created and tested With QGIS : 32811 - FIRENZE
this project is part of:
ACCORDO DI COLLABORAZIONE SCIENTIFICA TRA 
L’AUTORITÀ DI BACINO DEL DISTRETTO IDROGRAFICO DELLA SICILIA 
E IL DIPARTIMENTO DI INGEGNERIA CIVILE E ARCHITETTURA (DICAr) 
DELL’UNIVERSITÀ DEGLI STUDI DI CATANIA(UNICT) 
PER STUDI IDROLOGICI E IDRAULICI PER L’INDIVIDUAZIONE DI FASCE FLUVIALI, 
PER L’INDIVIDUAZIONE DI MISURE NWRM (NATURAL WATER RETENTION MEASURES) 
E PER LA DEFINIZIONE DI PIANI DI LAMINAZIONE
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterDefinition
import processing


class RiverBanksDistanceV141(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('left_riverbank__rbl', 'Left Riverbank - RB-L', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        # If set to TRUE, the cardinal order of the sections along the river channel is reversed. This becomes useful in the case of digitized rods in the reverse direction from the desired direction
        param = QgsProcessingParameterBoolean('revertpathdirection', 'Revert-path-direction', defaultValue=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterVectorLayer('right_riverbank__rbr', 'Right Riverbank - RB-R', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('river_centerline', 'River centerline', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        param = QgsProcessingParameterNumber('sezid_field_lenght', 'SEZ-ID field lenght', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=255)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        # Distance along river path from a node to another.
        self.addParameter(QgsProcessingParameterNumber('step', 'Step', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=50))
        self.addParameter(QgsProcessingParameterNumber('transects_width', 'Transects width', type=QgsProcessingParameterNumber.Integer, defaultValue=100))
        self.addParameter(QgsProcessingParameterFeatureSink('LeftNodes', 'Left nodes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('RightNodes', 'Right nodes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('OutputTransects', 'Output transects', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(12, model_feedback)
        results = {}
        outputs = {}

        # Centerline-nodes
        # Create nodes along river centerline path,  using the input "step"
        alg_params = {
            'DISTANCE': parameters['step'],
            'END_OFFSET': 0,
            'INPUT': parameters['river_centerline'],
            'START_OFFSET': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Centerlinenodes'] = processing.run('native:pointsalonglines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Simplified-centerline
        # Create a new simplified river centerline using centerline nodes
        alg_params = {
            'CLOSE_PATH': False,
            'GROUP_EXPRESSION': '',
            'INPUT': outputs['Centerlinenodes']['OUTPUT'],
            'NATURAL_SORT': False,
            'ORDER_EXPRESSION': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Simplifiedcenterline'] = processing.run('native:pointstopath', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Transects
        # Make Transects
        alg_params = {
            'ANGLE': 90,
            'INPUT': outputs['Simplifiedcenterline']['OUTPUT'],
            'LENGTH': parameters['transects_width'],
            'SIDE': 2,  # Entrambi
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Transects'] = processing.run('native:transect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Assign SEZ-ID
        # Assign a key-value for each nodes called "SEZ-ID"
        # If Revert path direction is set to TRUE order is reverted
        alg_params = {
            'FIELD_LENGTH': parameters['sezid_field_lenght'],
            'FIELD_NAME': 'SEZ-ID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Intero (32 bit)
            'FORMULA': "if(@revertpathdirection is FALSE, @id, (count( 'Centerline-nodes')-@id+1))",
            'INPUT': outputs['Centerlinenodes']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssignSezid'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Assign SEZ-ID to Transects
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELDS_TO_COPY': ['SEZ-ID'],
            'INPUT': outputs['Transects']['OUTPUT'],
            'INPUT_2': outputs['AssignSezid']['OUTPUT'],
            'MAX_DISTANCE': None,
            'NEIGHBORS': 1,
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssignSezidToTransects'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Nodes_INT_R
        # Create nodes on intersection between transects and Right riverbanks
        alg_params = {
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['right_riverbank__rbr'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Nodes_int_r'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Nodes_INT_L
        # Create nodes on intersection between transects and Left riverbanks
        alg_params = {
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['left_riverbank__rbl'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Nodes_int_l'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Right nodes attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"feature_x"','length': 255,'name': 'feature_x','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"feature_y"','length': 255,'name': 'feature_y','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$x','length': 255,'name': 'X_INT_R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$y','length': 255,'name': 'Y_INT_R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)','length': 255,'name': 'dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'minimum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'min-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'maximum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'max-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['Nodes_int_r']['OUTPUT'],
            'OUTPUT': parameters['RightNodes']
        }
        outputs['RightNodesAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['RightNodes'] = outputs['RightNodesAttributes']['OUTPUT']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Left Nodes attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"feature_x"','length': 255,'name': 'feature_x','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"feature_y"','length': 255,'name': 'feature_y','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$x','length': 255,'name': 'X_INT_L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$y','length': 255,'name': 'Y_INT_L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)','length': 255,'name': 'dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'minimum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'min-dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'maximum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'max-dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['Nodes_int_l']['OUTPUT'],
            'OUTPUT': parameters['LeftNodes']
        }
        outputs['LeftNodesAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['LeftNodes'] = outputs['LeftNodesAttributes']['OUTPUT']

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # JOIN Transects - Intersection - Right
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_2': outputs['RightNodesAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': 'R-',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinTransectsIntersectionRight'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # JOIN Transects - Intersection - Left
        # Final vector that contain transects feature and field from their intersection with banks.
        # Fields table will be cleaned and will be generated output data.
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['JoinTransectsIntersectionRight']['OUTPUT'],
            'INPUT_2': outputs['LeftNodesAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': 'L-',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinTransectsIntersectionLeft'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Output
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"R-min-dist-R"','length': 255,'name': 'min-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"R-max-dist-R"','length': 255,'name': 'max-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"L-min-dist-L"','length': 255,'name': 'min-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"L-max-dist-L"','length': 255,'name': 'max-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['JoinTransectsIntersectionLeft']['OUTPUT'],
            'OUTPUT': parameters['OutputTransects']
        }
        outputs['Output'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OutputTransects'] = outputs['Output']['OUTPUT']
        return results

    def name(self):
        return 'River Banks Distance v.1.4.1'

    def displayName(self):
        return 'River Banks Distance v.1.4.1'

    def group(self):
        return 'RBTools'

    def groupId(self):
        return 'RBTools'

    def shortHelpString(self):
        return """<html><body><p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'MS Shell Dlg 2'; font-size:16pt; font-weight:600; font-style:italic;">Description</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Distance between banks and axis of a river along its path, useful for morphological analysis.</p>
<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">The river centerline is simplified into fixed-length segments. </p>
<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">For each step along the path, this model calculates the distance between the centerline and the left/right banks.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Here how it works:</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">1.Create nodes along the river centerline path using the input parameter <span style=" font-style:italic;">step</span>.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">2.Assign a key-value attribute called <span style=" font-style:italic;">SEZ-ID</span> to each node.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">3.Create a new simplified river centerline based on these nodes.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">4.Generate transects perpendicular to the simplified river centerline.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">5.Perform a spatial join between transects and nodes to assign the <span style=" font-style:italic;">SEZ-ID</span> key-value to transects.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">6.Identify intersection nodes between transects and riverbanks (left/right).</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">7.Add intersection coordinates (X/Y) to the attribute table.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">8.Calculate the maximum and minimum distances from the centerline (in cases with two or more intersections).</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">9.Perform a spatial join between intersection nodes and transects.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">10.Clean field data and generate the final output. </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:1; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html></p>
<h2>Parametri in ingresso
</h2>
<h3>Left Riverbank - RB-L</h3>
<p>This LineString type vector must contain ONLY 1-line feature
This is the feature of Left Riverbank</p>
<h3>Revert-path-direction</h3>
<p>If true, key value order along path for transects is reverted </p>
<h3>Right Riverbank - RB-R</h3>
<p>This LineString type vector must contain ONLY 1-line feature
This is the feature of Right riverbank</p>
<h3>River centerline</h3>
<p>This LineString type vector must contain ONLY 1-line feature
This is the feature of river path.</p>
<h3>SEZ-ID field lenght</h3>
<p>This parameter indicates the length of the SEZ-ID number field in which the number identifying the section for which the distance between banks is calculated is saved.</p>
<h3>Step</h3>
<p>Distance along river path from a node to another.
this parameter is used for generating transects and calculation of distances.

A too short step increase computational resource needs and accuracy of data.
A too long step decrease accuracy of the output parameters that describe morphology of the river.</p>
<h3>Transects width</h3>
<p>This value must be large enough, equal to at least twice the maximum distance at which the bank could be to intersect riverbanks.
It is used to generate transects orthogonal to the river simplified centerline </p>
<h2>Risultati</h2>
<h3>Left nodes</h3>
<p>Nodes features. Intersection between Transects and Left riverbanks</p>
<h3>Right nodes</h3>
<p>Nodes features. Intersection between Transects and Right riverbanks</p>
<h3>Output transects</h3>
<p>Main output data.
Line features as transects along path of centerline.
Fields contains these data:
{SEZ-ID: Transect id (key field)}, 
{min-RB-R: miminum distance from centerline to RIGHT riverbank},  
{max-RB-R: maximum distance from centerline to RIGHT riverbank},
{min-RB-L: miminum distance from centerline to LEFT riverbank}, 
{max-RB-L: maximum distance from centerline to LEFT riverbank}</p>
<h2>Esempi</h2>
<p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html></p><br><p align="right">Autore algoritmo: Gianfranco Di Pietro - Phd Student @ Università di Catania</p><p align="right">Autore della guida: Gianfranco Di Pietro - Phd Student @ Università di Catania</p><p align="right">Versione algoritmo: v.1.4  -  Feb/15/2024</p></body></html>"""

    def helpUrl(self):
        return 'https://github.com/gianfrancodp/qgis-riverbanks-tools'

    def createInstance(self):
        return RiverBanksDistanceV141()
