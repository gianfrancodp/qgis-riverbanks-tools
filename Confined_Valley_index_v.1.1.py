"""
Model exported as python.
manually commented after exporting
Name : Confined Valley Index
CC-BY-SA: Gianfranco Di Pietro
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

#Imports from qgis.core

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterDefinition
import processing


class ConfinedValleyIndex(QgsProcessingAlgorithm):

    #Definition of input parameters
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('left_river_bank', 'LEFT River Bank', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('right_river_bank', 'RIGHT River Bank', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('river_line', 'River Line', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        param = QgsProcessingParameterNumber('sezid_number_lenght', 'SEZ-ID number lenght', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=255)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterBoolean('transects_id_assignment_revert', 'Transects ID assignment revert', defaultValue=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterNumber('transects_step', 'Transects STEP', type=QgsProcessingParameterNumber.Integer, defaultValue=50))
        self.addParameter(QgsProcessingParameterNumber('transects_width_m', 'Transects WIDTH [m]', type=QgsProcessingParameterNumber.Integer, defaultValue=2000))
        self.addParameter(QgsProcessingParameterVectorLayer('valley_bottom', 'Valley Bottom', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Out', 'OUT', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(30, model_feedback)
        results = {}
        outputs = {}

        # Center Points
        # Make points along river line, using a constat 'transects step' input parametrer.
        alg_params = {
            'DISTANCE': parameters['transects_step'],
            'END_OFFSET': 0,
            'INPUT': parameters['river_line'],
            'START_OFFSET': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CenterPoints'] = processing.run('native:pointsalonglines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Assign SEZ-ID to centerline points.
        # 'SEZ-ID' is a key value for identification of each transect along river line.
        # Using field calculator processing algorithm, assign a SEZ-ID to each centerline point.
        # There are a conditional assignment, if @transects_id_assignment_revert is TRUE, the SEZ-ID is assigned
        # in a reverse order, useful for revert from downstream to upstream transect id.
        alg_params = {
            'FIELD_LENGTH': parameters['sezid_number_lenght'],
            'FIELD_NAME': 'SEZ-ID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Intero (32 bit)
            'FORMULA': "if(  @transects_id_assignment_revert  is FALSE, @id, (count( 'Center_Points')-@id+1))",
            'INPUT': outputs['CenterPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssignSezidToCenterlinePoints'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Line center Transects
        # This for generate a line feature from centerline points.
        # this line is used for generate transects. 
        alg_params = {
            'CLOSE_PATH': False,
            'GROUP_EXPRESSION': '',
            'INPUT': outputs['CenterPoints']['OUTPUT'],
            'NATURAL_SORT': False,
            'ORDER_EXPRESSION': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LineCenterTransects'] = processing.run('native:pointstopath', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Transects
        # This for generate transects using native qgis processing algorithm.
        alg_params = {
            'ANGLE': 90,
            'INPUT': outputs['LineCenterTransects']['OUTPUT'],
            'LENGTH': parameters['transects_width_m'],
            'SIDE': 2,  # Entrambi
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Transects'] = processing.run('native:transect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Assign_SEZ-ID_Transetti
        # This for assign SEZ-ID to transects, SEZ-ID is a key-value, the ID of each transect
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELDS_TO_COPY': [''],
            'INPUT': outputs['Transects']['OUTPUT'],
            'INPUT_2': outputs['AssignSezidToCenterlinePoints']['OUTPUT'],
            'MAX_DISTANCE': None,
            'NEIGHBORS': 1,
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Assign_sezid_transetti'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # VB Line
        # This algorithm is used to convert a polygon layer to a line layer.
        # The valley bottom polygon is converted to lines feature.
        alg_params = {
            'INPUT': parameters['valley_bottom'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['VbLine'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # SPLIT Transects
        # Transects are splitted with input river_line in two parts.
        alg_params = {
            'INPUT': outputs['Assign_sezid_transetti']['OUTPUT'],
            'LINES': parameters['river_line'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SplitTransects'] = processing.run('native:splitwithlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Transects_L
        # This for assign attributes of left side of riverbank to transects.
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'INPUT': outputs['SplitTransects']['OUTPUT'],
            'JOIN': parameters['left_river_bank'],
            'JOIN_FIELDS': [''],
            'METHOD': 2,  # Prendi solamente gli attributi dell'elemento con maggiore sovrapposizione (uno-a-uno)
            'PREDICATE': [0],  # interseca
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Transects_l'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Left River bank points
        # Intersection between left river bank and transects
        alg_params = {
            'INPUT': outputs['Transects_l']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['left_river_bank'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LeftRiverBankPoints'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Transects_R
        # This for assign attributes of right side of riverbank to transects.
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'INPUT': outputs['SplitTransects']['OUTPUT'],
            'JOIN': parameters['right_river_bank'],
            'JOIN_FIELDS': [''],
            'METHOD': 2,  # Prendi solamente gli attributi dell'elemento con maggiore sovrapposizione (uno-a-uno)
            'PREDICATE': [0],  # interseca
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Transects_r'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Int VB LEFT
        # Intersection between left Valley Bottom and transects
        alg_params = {
            'INPUT': outputs['VbLine']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': outputs['Transects_l']['OUTPUT'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['IntVbLeft'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Field Left River bank points
        # Retain only SEZ-ID, feature_x and feature_y fields
        alg_params = {
            'FIELDS': ['SEZ-ID','feature_x','feature_y'],
            'INPUT': outputs['LeftRiverBankPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldLeftRiverBankPoints'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Int VB RIGHT
        # Intersection between right Valley Bottom and transects
        alg_params = {
            'INPUT': outputs['VbLine']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': outputs['Transects_r']['OUTPUT'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['IntVbRight'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # dist from center River bank point LEFT
        # distance from centerline to left river bank points
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'dist-RB-L',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'sqrt(("feature_x" - $x)^2+("feature_y" - $y)^2)',
            'INPUT': outputs['FieldLeftRiverBankPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DistFromCenterRiverBankPointLeft'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Right river bank points
        # Intersection between right river bank and transects
        alg_params = {
            'INPUT': outputs['Transects_r']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['right_river_bank'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RightRiverBankPoints'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Field VB INT LEFT
        # Retain only SEZ-ID, feature_x and feature_y fields
        alg_params = {
            'FIELDS': ['SEZ-ID','feature_x','feature_y'],
            'INPUT': outputs['IntVbLeft']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldVbIntLeft'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Calculate dist from center line - VB-L
        # Distance from centerline to Left side of ValleyBottom
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'dist-VB-L',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'sqrt(("feature_x" - $x)^2+("feature_y" - $y)^2)',
            'INPUT': outputs['FieldVbIntLeft']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculateDistFromCenterLineVbl'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Field Right River bank points
        # Retain only SEZ-ID, feature_x and feature_y fields
        alg_params = {
            'FIELDS': ['SEZ-ID','feature_x','feature_y'],
            'INPUT': outputs['RightRiverBankPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldRightRiverBankPoints'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Field VB INT Right
        # Retain only SEZ-ID, feature_x and feature_y fields
        alg_params = {
            'FIELDS': ['SEZ-ID','feature_x','feature_y'],
            'INPUT': outputs['IntVbRight']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldVbIntRight'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Min dist-VB-L
        # Aggregate minimum distance from centerline to left side of ValleyBottom
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'min-VB-L',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'minimum( "dist-VB-L","SEZ-ID","SEZ-ID")',
            'INPUT': outputs['CalculateDistFromCenterLineVbl']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MinDistvbl'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # min dist-RB-L
        # Aggregate minimum distance from centerline to left side of RiverBank
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'min-RB-L',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'minimum( "dist-RB-L","SEZ-ID","SEZ-ID")',
            'INPUT': outputs['DistFromCenterRiverBankPointLeft']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MinDistrbl'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Calculate dist from center line - VB_R
        # Distance from centerline to Right side of ValleyBottom
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'dist-VB-R',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'sqrt(("feature_x" - $x)^2+("feature_y" - $y)^2)',
            'INPUT': outputs['FieldVbIntRight']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculateDistFromCenterLineVb_r'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # dist from centerline - Right bank river points
        # Distance from centerline to Right side of RiverBank
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'dist-RB-R',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'sqrt(("feature_x" - $x)^2+("feature_y" - $y)^2)',
            'INPUT': outputs['FieldRightRiverBankPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DistFromCenterlineRightBankRiverPoints'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Min_dist-VB-R
        # Aggregate minimum distance from centerline to right side of ValleyBottom
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'min-VB-R',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'minimum( "dist-VB-R","SEZ-ID","SEZ-ID")',
            'INPUT': outputs['CalculateDistFromCenterLineVb_r']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Min_distvbr'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # assing dist-VB-R to centerline points
        # Assign minimum distance from centerline to right side of ValleyBottom to centerline points
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': ['min-VB-R'],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssignSezidToCenterlinePoints']['OUTPUT'],
            'INPUT_2': outputs['Min_distvbr']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssingDistvbrToCenterlinePoints'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Assign dist-VB-L to centerline points
        # Assign minimum distance from centerline to left side of ValleyBottom to centerline points
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': ['min-VB-L'],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssingDistvbrToCenterlinePoints']['OUTPUT'],
            'INPUT_2': outputs['MinDistvbl']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssignDistvblToCenterlinePoints'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # min dist-RB-R
        # Minimum distance from centerline to right side of RiverBank
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'min-RB-R',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'minimum( "dist-RB-R","SEZ-ID","SEZ-ID")',
            'INPUT': outputs['DistFromCenterlineRightBankRiverPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MinDistrbr'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # assing dist-RB-R to centerline points
        # Assign minimum distance from centerline to right side of RiverBank to centerline points
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssignDistvblToCenterlinePoints']['OUTPUT'],
            'INPUT_2': outputs['MinDistrbr']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssingDistrbrToCenterlinePoints'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # assign dist-RB-L to center points
        # Assign minimum distance from centerline to left side of RiverBank to centerline points
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssingDistrbrToCenterlinePoints']['OUTPUT'],
            'INPUT_2': outputs['MinDistrbl']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssignDirtrblToCenterPoints'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Final attribute Table to centerpoint
        # This for generate a final attribute table to centerline points.
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '("min-VB-R"+"min-VB-L")/("min-RB-R"+"min-RB-L")','length': 255,'name': 'VB_RB-index','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"min-RB-R"+"min-RB-L"','length': 255,'name': 'RB-W','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"min-VB-R"+"min-VB-L"','length': 255,'name': 'VB-W','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"min-RB-R"','length': 255,'name': 'min-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"min-RB-L"','length': 255,'name': 'min-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"min-VB-L"','length': 255,'name': 'min-VB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"min-VB-R"','length': 255,'name': 'min-VB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"distance"','length': 255,'name': 'trasnect_d','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['AssignDirtrblToCenterPoints']['OUTPUT'],
            'OUTPUT': parameters['Out']
        }
        outputs['FinalAttributeTableToCenterpoint'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Out'] = outputs['FinalAttributeTableToCenterpoint']['OUTPUT']
        return results

    def name(self):
        return 'Confined Valley Index'

    def displayName(self):
        return 'Confined Valley Index'

    def group(self):
        return 'FSC'

    def groupId(self):
        return 'FSC'

    def shortHelpString(self):
        return """<html><body><p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'MS Shell Dlg 2'; font-size:18pt; font-weight:600; font-style:italic;">Description</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'MS Shell Dlg 2'; font-size:18pt;">The algorithm is used to calculate the relationship between the width of the ValleyBottom and the banks of a river.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'MS Shell Dlg 2'; font-size:18pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'MS Shell Dlg 2'; font-size:18pt;">Transects are generated,  at constant pitch,  along the river axis; they intersect the right bank, the left bank and the ValleyBottom polygon.</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'MS Shell Dlg 2'; font-size:18pt;">The distances between the river axis and the intersections are calculated,  the minimum value is taken.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'MS Shell Dlg 2'; font-size:18pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'MS Shell Dlg 2'; font-size:18pt;">In Output a layer of points along the river axis containing the calculated data is generated:</span></p>
<ul style="margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;"><li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">SEZ-ID: transect identifier (key field).</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">VB_RB-index: Ratio of ValleyBottom Width to Riverbank Width.</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">RB-W: River bank width</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">VB-W: Width of the Valley Bottom</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">min-RB-R: Minimum distance to the Right Bank of the river</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">min-RB-L: minimum distance with the Left Bank of the river</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">min-VB-L: minimum distance with the Left ValleyBottom</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">min-VB-R: minimum distance with the ValleyBottom Right</li>
<li style=" font-family:'MS Shell Dlg 2'; font-size:18pt;" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">transect_d: distance along the river path</li></ul></body></html></p>
<h2>Parametri in ingresso
</h2>
<h3>LEFT River Bank</h3>
<p>Linear Layer with LEFT Riverbank </p>
<h3>RIGHT River Bank</h3>
<p>Linear Layer with RIGHT Riverbank </p>
<h3>River Line</h3>
<p>River axis</p>
<h3>Transects ID assignment revert</h3>
<p>If True ID assignment of transect will be inverted.
For example to maintain a conventional assignment (from downstream to upstream, or vice-versa)</p>
<h3>Transects STEP</h3>
<p>Distance along river path from a transect to another</p>
<h3>Transects WIDTH [m]</h3>
<p>Width of transects. This width is a unic value for all transects.
This parameter is important to investigate and calculate Confined index.
It must not be too large to avoid too many intersections, nor too small not to intersect the valleybottom.</p>
<h3>Valley Bottom</h3>
<p>Valley Bottom polygon</p>
<h2>Risultati</h2>
<h3>OUT</h3>
<p>In Output a layer of points along the river axis containing the calculated data is generated:
SEZ-ID = transect identifier (key field);  VB_RB-index = ratio of ValleyBottom Width to Riverbank Width; RB-W = Riverbank width; VB-W = Width of the Valley Bottom; min-RB-R =  Minimum distance to the Right Bank of the river; min-RB-L = minimum distance with the Left Bank of the river; min-VB-L = minimum distance with the Left ValleyBottom; min-VB-R = minimum distance with the ValleyBottom Right; transect_d: distance along the river path</p>
<h2>Esempi</h2>
<p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'MS Shell Dlg 2'; font-size:8.25pt;"><br /></p></body></html></p><br><p align="right">Autore algoritmo: Ing. Gianfranco Di Pietro - Phd Student @ Università di Catania</p><p align="right">Autore della guida: Ing. Gianfranco Di Pietro - Phd Student @ Università di Catania</p><p align="right">Versione algoritmo: v.1.1  -  Gen/02/2024</p></body></html>"""

    def createInstance(self):
        return ConfinedValleyIndex()
