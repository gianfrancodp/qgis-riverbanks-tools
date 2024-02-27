"""
Model exported as python.
Name : River Banks Distance Comparison v.1.4
Group : RBTools
With QGIS : 32811
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterDefinition
import processing


class RiverBanksDistanceComparisonV14(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        # If set to TRUE, the cardinal order of the sections along the river channel is reversed. This becomes useful in the case of digitized rods in the reverse direction from the desired direction
        param = QgsProcessingParameterBoolean('revertpathdirection', 'Revert-path-direction', defaultValue=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterVectorLayer('river_centerline', 'River centerline', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        # Distance along river path from a node to another.
        self.addParameter(QgsProcessingParameterNumber('step', 'Step', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=50))
        self.addParameter(QgsProcessingParameterVectorLayer('time_1__left_riverbank__t1rbl', 'Time 1 - Left Riverbank - T1-RB-L', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('time_1__right_riverbank__t1rbr', 'Time 1 - Right Riverbank - T1-RB-R', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('time_2__left_riverbank__t2rbl', 'Time 2 - Left Riverbank - T2-RB-L', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('time_2__right_riverbank__t2rbr', 'Time 2 - Right Riverbank - T2-RB-R', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('transects_width', 'Transects width', type=QgsProcessingParameterNumber.Integer, defaultValue=100))
        self.addParameter(QgsProcessingParameterFeatureSink('T1t2TransectsRbDistanceComparison', 'T1-T2 Transects RB distance comparison', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('IntersectionNodes', 'Intersection nodes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(23, model_feedback)
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

        # Assign SEZ-ID
        # Assign a key-value for each nodes called "SEZ-ID"
        # If Revert path direction is set to TRUE order is reverted
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'SEZ-ID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Intero (32 bit)
            'FORMULA': "if(@revertpathdirection is FALSE, @id, (count( 'Centerline-nodes')-@id+1))",
            'INPUT': outputs['Centerlinenodes']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AssignSezid'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
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

        feedback.setCurrentStep(3)
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

        # T2-Nodes_INT_R
        alg_params = {
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['time_2__right_riverbank__t2rbr'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2nodes_int_r'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # T1-Nodes_INT_L
        # Create nodes on intersection between transects and Left riverbanks
        alg_params = {
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['time_1__left_riverbank__t1rbl'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1nodes_int_l'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # T2-Right Nodes attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"feature_x"','length': 255,'name': 'feature_x','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"feature_y"','length': 255,'name': 'feature_y','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$x','length': 255,'name': 'T2-X-INT_R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$y','length': 255,'name': 'T2-Y-INT_R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)','length': 255,'name': 'T2-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'minimum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T2-min-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'maximum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T2-max-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['T2nodes_int_r']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2rightNodesAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # T1-Nodes_INT_R
        # Create nodes on intersection between transects and Right riverbanks
        alg_params = {
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['time_1__right_riverbank__t1rbr'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1nodes_int_r'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # T1-Left Nodes attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"feature_x"','length': 255,'name': 'feature_x','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"feature_y"','length': 255,'name': 'feature_y','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$x','length': 255,'name': 'X_INT_L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$y','length': 255,'name': 'Y_INT_L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)','length': 255,'name': 'dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'minimum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T1-min-dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'maximum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T1-max-dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['T1nodes_int_l']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1leftNodesAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # T2-Nodes_INT_L
        alg_params = {
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': parameters['time_2__left_riverbank__t2rbl'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2nodes_int_l'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Intersection Nodes
        alg_params = {
            'INPUT': outputs['T1nodes_int_r']['OUTPUT'],
            'OVERLAYS': [outputs['T1nodes_int_l']['OUTPUT'],outputs['T2nodes_int_l']['OUTPUT'],outputs['T2nodes_int_r']['OUTPUT']],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['IntersectionNodes'] = processing.run('native:multiunion', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Intersection nodes attribute cleaning
        alg_params = {
            'FIELDS_MAPPING': [],
            'INPUT': outputs['IntersectionNodes']['OUTPUT'],
            'OUTPUT': parameters['IntersectionNodes']
        }
        outputs['IntersectionNodesAttributeCleaning'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['IntersectionNodes'] = outputs['IntersectionNodesAttributeCleaning']['OUTPUT']

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # T1-Right nodes attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"feature_x"','length': 255,'name': 'feature_x','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"feature_y"','length': 255,'name': 'feature_y','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$x','length': 255,'name': 'X_INT_R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$y','length': 255,'name': 'Y_INT_R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)','length': 255,'name': 'dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'minimum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T1-min-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'maximum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T1-max-dist-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['T1nodes_int_r']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1rightNodesAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # T2-Left Nodes attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"feature_x"','length': 255,'name': 'feature_x','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"feature_y"','length': 255,'name': 'feature_y','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$x','length': 255,'name': 'T2-X-INT_L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '$y','length': 255,'name': 'T2-Y-INT_L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)','length': 255,'name': 'T2-dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'minimum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T2-min-dist-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'maximum( (sqrt(( $x - "feature_x")^2 + ( $y - "feature_y")^2)),"SEZ-ID","SEZ-ID")','length': 255,'name': 'T2-max-dist-L','precision': 3,'sub_type': 0,'type': 0,'type_name': ''}],
            'INPUT': outputs['T2nodes_int_l']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2leftNodesAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # T2-JOIN Transects - Intersection - Right
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_2': outputs['T2rightNodesAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': 'R-',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2joinTransectsIntersectionRight'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # T2-JOIN Transects - Intersection - Left
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['T2joinTransectsIntersectionRight']['OUTPUT'],
            'INPUT_2': outputs['T2leftNodesAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': 'L-',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2joinTransectsIntersectionLeft'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # T1-JOIN Transects - Intersection - Right
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['AssignSezidToTransects']['OUTPUT'],
            'INPUT_2': outputs['T1rightNodesAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': 'R-',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1joinTransectsIntersectionRight'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # T2-RB Distance attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"R-T2-min-dist-R"','length': 255,'name': 'T2-min-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"R-T2-max-dist-R"','length': 255,'name': 'T2-max-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"L-T2-min-dist-L"','length': 255,'name': 'T2-min-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"L-T2-max-dist-L"','length': 255,'name': 'T2-max-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['T2joinTransectsIntersectionLeft']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T2rbDistanceAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # T1-JOIN Transects - Intersection - Left
        # Final vector that contain transects feature and field from their intersection with banks.
        # Fields table will be cleaned and will be generated output data.
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['T1joinTransectsIntersectionRight']['OUTPUT'],
            'INPUT_2': outputs['T1leftNodesAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': 'L-',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1joinTransectsIntersectionLeft'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # T1-RB Distance attributes
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"R-T1-min-dist-R"','length': 255,'name': 'T1-min-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"R-T1-max-dist-R"','length': 255,'name': 'T1-max-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"L-T1-min-dist-L"','length': 255,'name': 'T1-min-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"L-T1-max-dist-L"','length': 255,'name': 'T1-max-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['T1joinTransectsIntersectionLeft']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1rbDistanceAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # T1-T2 RB Distance Join 
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'SEZ-ID',
            'FIELDS_TO_COPY': [''],
            'FIELD_2': 'SEZ-ID',
            'INPUT': outputs['T1rbDistanceAttributes']['OUTPUT'],
            'INPUT_2': outputs['T2rbDistanceAttributes']['OUTPUT'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['T1t2RbDistanceJoin'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Output Comparison attributes
        # Assign atttributes to difference between RB distance across T1 and T2 (delta T2-T1)
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"SEZ-ID"','length': 255,'name': 'SEZ-ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"T1-min-RB-R"','length': 255,'name': 'T1-min-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T1-max-RB-R"','length': 255,'name': 'T1-max-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T1-min-RB-L"','length': 255,'name': 'T1-min-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T1-max-RB-L"','length': 255,'name': 'T1-max-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T2-min-RB-R"','length': 255,'name': 'T2-min-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T2-max-RB-R"','length': 255,'name': 'T2-max-RB-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T2-min-RB-L"','length': 255,'name': 'T2-min-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T2-max-RB-L"','length': 255,'name': 'T2-max-RB-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T2-min-RB-L"-"T1-min-RB-L"','length': 255,'name': 'T2-T1-min-delta-L','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"T2-min-RB-R"-"T1-min-RB-R"','length': 255,'name': 'T2-T1-min-delta-R','precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['T1t2RbDistanceJoin']['OUTPUT'],
            'OUTPUT': parameters['T1t2TransectsRbDistanceComparison']
        }
        outputs['OutputComparisonAttributes'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['T1t2TransectsRbDistanceComparison'] = outputs['OutputComparisonAttributes']['OUTPUT']
        return results

    def name(self):
        return 'River Banks Distance Comparison v.1.4'

    def displayName(self):
        return 'River Banks Distance Comparison v.1.4'

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
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">2-epoch comparison of distance between riverbanks and axis of a river along path, useful for morphological analysis</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Centerline of the river is simplyfied into fixed-lenght segments,  for each step along the path this model get the distance between centerline and left/right banks.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Here how it works:</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<ol style="margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;"><li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Create nodes along river centerline path,  using the input &quot;step&quot;</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Assign a key-value for each nodes called &quot;SEZ-ID&quot;</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Create a new simplified river centerline using nodes</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Create transect across simplified river centerline</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Make a spatial-join with transects and nodes and assign the key-value &quot;SEZ-ID&quot; to transects</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Create nodes of intersection between Transects and Riverbanks (Left/Right)</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Add coordinates X/Y of intersection into fields table</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Calculate max and min distance from centerline (in case of 2 or more intersections)</li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Spatial join of intersection nodes and Transects, </li>
<li style="" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Fields data cleaning and output.</li></ol>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:1; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html></p>
<h2>Parametri in ingresso
</h2>
<h3>Revert-path-direction</h3>
<p>If true, key value order along path for transects is reverted </p>
<h3>River centerline</h3>
<p>This LineString type vector must contain ONLY 1-line feature
This is the feature of river path.</p>
<h3>Step</h3>
<p>Distance along river path from a node to another.
this parameter is used for generating transects and calculation of distances.

A too short step increase computational resource needs and accuracy of data.
A too long step decrease accuracy of the output parameters that describe morphology of the river.</p>
<h3>Time 1 - Left Riverbank - T1-RB-L</h3>
<p>Linestring (only 1 line element) of Left Riverbank in "time 1"</p>
<h3>Time 1 - Right Riverbank - T1-RB-R</h3>
<p>Linestring (only 1 line element) of Right Riverbank in "time 1"</p>
<h3>Time 2 - Left Riverbank - T2-RB-L</h3>
<p>Linestring (only 1 line element) of Left Riverbank in "time 2"</p>
<h3>Time 2 - Right Riverbank - T2-RB-R</h3>
<p>Linestring (only 1 line element) of Right Riverbank in "time 2"</p>
<h3>Transects width</h3>
<p>This value must be large enough, equal to at least twice the maximum distance at which the bank could be to intersect riverbanks.
It is used to generate transects orthogonal to the river simplified centerline </p>
<h2>Risultati</h2>
<h3>T1-T2 Transects RB distance comparison</h3>
<p>Transect feature with attributes of distance from centerline to riverbanks.
</p>
<h2>Esempi</h2>
<p><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html></p><br><p align="right">Autore algoritmo: Gianfranco Di Pietro - Phd Student @ Università di Catania</p><p align="right">Autore della guida: Gianfranco Di Pietro - Phd Student @ Università di Catania</p><p align="right">Versione algoritmo: v.1.4  -  Feb/15/2024</p></body></html>"""

    def helpUrl(self):
        return 'https://github.com/gianfrancodp/qgis-riverbanks-tools'

    def createInstance(self):
        return RiverBanksDistanceComparisonV14()
