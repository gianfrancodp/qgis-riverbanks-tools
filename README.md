# Qgis riverbanks tools

![header](readme_assets/QRBT_main_splash_v2.png)

A simple tools for analysis of banks of a river in Qgis; algorytms and scripts are written with Qgis 3 graphical modeler and Python.

## Table of content

0. [News](#news)
1. [How to use on qgis](#1-how-to-use-on-qgis)
2. [Confined Valley Index](#2-confined-valley-index)
3. [RiverBanks Segments Cutter](#3-riverbanks-segment-cutter-rbsc)
4. [Riverbanks Distance](#4-riverbanks-distance-rbd)
5. [Riverbanks Distance Comparison](#5-riverbanks-distance-comparison-rbdc)
6. [RiverBanks Safety Bands tool](#6-riverbanks-safety-bands-tool-rbsb)
7. [Disclaimers and credits](#7-disclaimer-and-credits)

## NEWS

(Apr - 2025): Minor update of documentation and release 1.4.1

(Nov, 25 - 2024)

1. Renamed RBS model in *River Banks Segments Cutter*. [DOWNLOAD & test in your QGIS!](Models/RBSC/River%20Banks%20Segments%20Cutter.model3): This model separate RiverBanks (RB) into single segments using the stretches of the River Centerline (RC) vector. New elements will inherit the field table values from RC. <- Please refer to **built-in user guide**!

2. A *new* model3 called: *River Banks Safety Bands Tool*. This algorithm generates safety lines at a distance from the riverbanks, which have been previously divided into hydrologically homogeneous segments. For each segment, a buffer distance is determined using a multiplicative factor of the riverbank erosion rate. [DOWNLOAD & test in your QGIS!](Models/RBSB/RB%20Safety%20Bands%20tool.model3) <- Please refer to **built-in user guide**!

(Nov, 7 - 2024)

1. A *new beta-version* of River Banks Distance Comparison is released, try it: [DOWNLOAD & test in your QGIS!](Models/RBDC/River%20Banks%20Distance%20Comparison%20v.1.4.1.model3) model3 file. In this beta will be added new features:

    - Time value inputs of the two riverbanks to compare
    - Year erosion rate computing for each transect

    Please refer to **built-in user guide**!

2. (hidden due last update)

Please send us your feedbak! open a issue [here on Github](https://github.com/gianfrancodp/qgis-riverbanks-tools/issues) or send an email to autors [see below](#71-how-to-cite).

---

## 1. How to use on Qgis

[return to TOC](#table-of-content)

A fast-track is to downaload the [zip folder with all models](QgisRiverbanksTool_models_v1.0.zip), extract and add to your QGIS desktop.

To download a specific model3 files in this repository:
all model3 files are running on Qgis 3.28.11 or higher

1. [Confined Valley Index](Models/CVI/Confined_Valley_Index_v.1.1.model3)
2. [RiverBanks Segments Cutter](Models/RBSC/River%20Banks%20Segments%20Cutter.model3)
3. [Riverbanks Distance](Models/RBD/River%20Banks%20Distance%20v.1.4.model3)
4. [River Banks Distance Comparison](Models/RBDC/River%20Banks%20Distance%20Comparison%20v.1.4.model3)
5. [RiverBanks Safety Bands tool](Models/RBSB/RB%20Safety%20Bands%20tool.model3)

NOTE: If you download file directly from GitHub webpage may assure that the extension of file must be .model3 for properly use in Qgis

1. Open Qgis (developed and testet with Qgis 3.28.11)
2. Go to Processing sidebar and go to Model icon menu
3. Click on "Open existing model" and select the file in your filesystem

## 2. Confined Valley Index

![CVI_icon](Models/CVI/icon/CVI_128px.png)

[return to TOC](#table-of-content)

[DOWNLOAD PDF schema](Models/CVI/simplified-diagram/Confined_Valley_index_v.1.1.drawio.pdf)

### 2.1 CVI Description

The algorithm calculates the relationship $C_{VI}$ between the "width" of the ValleyBottom $VB_W$ and the "banks of a river" $RB_W$. and the *banks of a river* $RB_W$.

$$ C_{Vi} = {{VB_W} \over {RB_W}} $$

![CVIdiagram](Models/CVI/simplified-diagram/Confined_Valley_index_v.1.1-A.jpg)

### 2.2 CVI Input data

| Parameter name    | Data Type     | Description                                                   |
|-------------------|---------------|---------------------------------------------------------------|
| LEFT River Bank   | *Vector Line* | Line of the Left bank                                         |
| RIGHT River Bank  | *Vector Line* | Line of the Right bank                                        |
| River Line        | *Vector Line* | Path of the river                                             |
| Transects STEP    | Integer       | distance in meters along the path used for creating transects |
| Transects WIDTH   | Integer       | Lenght in meters of transects across river path               |
| Valley Bottom     | Polygon       | Polygon features that define the Valley Bottom of the river   |

![CVI-index-B](Models/CVI/simplified-diagram/Confined_Valley_index_v.1.1.-B.jpg)

Transects are generated, at constant distance from each other along the path, along the river axis; they intersect the right bank, the left bank and the ValleyBottom polygon. The distances between the river axis and the intersections are calculated, the minimum value is taken.

### 2.3 CVI Output

In Output a ***Vector Points*** along the river axis containing the calculated data is generated with this attribute table:

| Filed name    | Type  |    Desription                             |
|---------------|-------|-------------------------------------------|
| SEZ-ID        | Int   | Transect identifier (key field)           |
|**VB_RB-index**| Float | $C_{Vi} = {{VB_W} \over {RB_W}}$          |
| RB-W          | Float | Bank width                                |
| VB-W          | Float | ValleyBottom Width                        |
| min-RB-R      | Float | Minimum distance to the Right bank        |
| min-RB-L      | Float | Minimum distance to the Left bank         |
| min-VB-L      | Float | Minimum distance to the Left ValleyBottom |
| min-VB-R      | Float | Mimimum distance to the Right ValleyBottom|
| transect_d    | Float | Progressive distance along river path     |

An example of the results is shown in this map. A scaled-type symbology was used using the **VB_RB-index** field that represent the CVI. Higher values indicate that the valley bottom is further from the river banks. Therefore, in these portions the river is not confined by resistant elements.

![CVI-example](Models/CVI/CVI%20-%20output%20example.png)

## 3. RiverBanks Segment Cutter (RBSC)

![RBSC_icon](Models/RBSC/icon/RBSC_128px.png)

[return to TOC](#table-of-content)

This model algorithm segments the RiverBanks (RB) layer into individual units by leveraging the corresponding stretches of the River Centerline (RC) vector. Each resulting unit inherits attribute values from the RC layer, ensuring consistency across datasets. The output delineates distinct reaches of the water body, facilitating detailed hydromorphological analyses and management planning.​

--> [Download model file](Models/RBSC/River%20Banks%20Segments%20Cutter.model3)
--> [Download python script](Models/RBSC/River%20Banks%20Segments%20Cutter.py)

![diagram](Models/RBSC/RBSC_diagram.png)

### 3.1 RBSC Input data

NOTE: this model is tested with a single-feature vector for inputs

- LBR: Line or multiline feature with Left riverbank to consider.
- RBR: Line or multiline feature with Right riverbank to consider.
- RC stretch: Line or multiline feature with River Centerline to consider.
- River stretch separation lines: This vector contain only geometries used to cut RB. NONE of the field values of this vector will be inherited in the outputs.

### 3.2 RBSC Procedure description

1. Cut RB with separation lines vector
2. Get the max lenght of separation lines feature
3. Use *"proximity"* join (with a threshold distance provided from step #2) to inherit field table values from RC to RB

![model](Models/RBSC/RBSC_model.png)

### 3.3 RBSC Output data

- LRB: Left RiverBank reaches
- RRB: Right RiverBank reaches

## 4. RiverBanks Distance RBD

![RBD_icon](Models/RBD/icon/RBD_128px.png)

[return to TOC](#table-of-content)

![RDB-example-C](Models/RBD/images/RBD-example-C.png)

--> [Download](Models/RBD/River%20Banks%20Distance%20v.1.4.1.model3) Qgis graphical *model3* file
--> [Download](Models/RBD/River%20Banks%20Distance%20v.1.4.1.model3.py) Qgis python script file

### 4.1 RBD Description

Distance between banks and axis of a river along each path; useful for morphological analysis.ks and axis of a river along path; useful for morphological analysis.

Centerline of the river is simplyfied into fixed-lenght segments, for each step along the path this model get the distance between centerline and left/right banks.

Here how it works:

1. Create nodes along river centerline path, using the input "step"
2. Assign a key-value for each nodes called "SEZ-ID"
3. Create a new simplified river centerline using nodes
4. Create transect across simplified river centerline
5. Make a spatial-join with transects and nodes and assign the key-value "SEZ-ID" to transects
6. Create nodes of intersection between Transects and banks (Left/Right)
7. Add coordinates X/Y of intersection into attribute table
8. Spatial join of intersection nodes and Transects, and then assign attribute
9. Calculation of distances (Left and Right) using attribute data
10. Field cleaning and output.

### 4.2 RBD Input data

| Parameter name        | Type          | Description                                                   |
|-----------------------|---------------|---------------------------------------------------------------|
| Left Riverbank - RB-L | Linestring    | Left bank vector, must contain 1-line feature                 |
| Right Riverbank - RB-R| Linestring    | Right bank vector, must contain 1-line feature                |
| River centerline      | Linestring    | Path of river                                                 |
| Step                  | Integer       | Distance in meters along river path from a node to another (*)|
| Transects width       | Integer       | Width in meters used to generate transects (**)               |

(*) A too short step increase computational resource needs and accuracy of data.
A too long step decrease accuracy of the output parameters that describe morphology of the river

(**) This value must be large enough, equal to at least twice the maximum distance at which the bank could be to intersect banks. It is used to generate transects orthogonal to the river simplified centerline

### 4.3 RBD Output

This model generate the ***Transects vector features*** along path of the river, and intersection nodes.
For each transect in attribute table there are Right and Left distance from centerline, useful to calculate banks width.

| Filed name    | Type  |    Description                            |
|---------------|-------|-------------------------------------------|
| SEZ-ID        | Int   | Transect identifier (key field)           |
| min-RB-R      | Float | Minimum distance to the Right Bank        |
| max-RB-R      | Float | Maximum distance to the Right Bank        |
| min-RB-L      | Float | Minimum distance to the Left Bank         |
| max-RB-L      | Float | Maxinum distance to the Left Bank         |

`null` value distance is for no intersection between transects and RB

![RBD Example B](Models/RBD/images/RBD-example-B-800px.png)

This image is an example of map output.
linestring in red are the RB in input, the blue line is the river Centerline

![RBD Example A](Models/RBD/images/RBD-example-A-800px.png)

---

## 5. Riverbanks Distance Comparison RBDC

![RBDC_icon](Models/RBDC/icon/RBDC_128px.png)

[return to TOC](#table-of-content)

![RBDC-schema.svg](Models/RBDC/images/RBDC-schema.svg)

This model generates a two-epoch comparison of the distance between riverbanks and the river's axis along its path.

![Riverbanks Distance Comparison](Models/RBDC/images/RBDC-A-800px.png)

--> [Download](Models/RBDC/River%20Banks%20Distance%20Comparison%20v.1.4.model3) v.1.4 model3 file

*Try a new beta-version*: [Download beta v.1.4.1](Models/RBDC/River%20Banks%20Distance%20Comparison%20v.1.4.1.model3) model3 file

The bank distance comparison model (RBDC) is an implementation of RBD with two banks, which is useful in historical comparison analysis or quantitative analysis of the width of river banks in two epochs.

### 5.1 RBDC Input data

| Parameter name                    | Type          | Description                                                   |
|-----------------------------------|---------------|---------------------------------------------------------------|
| River centerline                  | Linestring    | Path of river                                                 |
| Step                              | Integer       | Distance in meters along river path from a node to another (*)|
| Time 1 Left Riverbank - T1-RB-L   | Linestring    | Time 1 Left bank vector, must contain 1-line feature          |
| Time 1 Right Riverbank - T1-RB-R  | Linestring    | Time 1 Right bank vector, must contain 1-line feature         |
| Time 2 Left Riverbank - T2-RB-L   | Linestring    | Time 2 Left bank vector, must contain 1-line feature          |
| Time 2 Right Riverbank - T2-RB-R  | Linestring    | Time 2 Right bank vector, must contain 1-line feature         |
| Transects width                   | Integer       | Width in meters used to generate transects (**)               |
| Revert-path-direction             | Boolean       | if checked assignment order of "SEZ-ID" is reverted along path|

(*) A too short step increase computational resource needs and accuracy of data.
A too long step decrease accuracy of the output parameters that describe morphology of the river

(**) This value must be large enough, equal to at least twice the maximum distance at which the bank could be to intersect banks. It is used to generate transects orthogonal to the river simplified centerline

### 5.2 RBDC Output

This model generate 2 layers:

1) a **line** layer called: "*T1-T2 Transects RB distance comparison*"
2) a **point** layer called: "*Interseciton nodes*"

Transects layer contain data about bank distance and their comparison, point layer contain only point of intersection between banks and transects.

The attribute table of Transects layer contain this data:

| Filed name        | Type  |    Description                                        |
|-------------------|-------|-------------------------------------------------------|
| SEZ-ID            | Int   | Transect identifier (key field)                       |
| T1-min-RB-R       | Float | Time 1 Minimum distance to the Right Bank: ${r}_{T1}$ |
| T1-max-RB-R       | Float | Time 1 Maximum distance to the Right Bank: ${R}_{T1}$ |
| T1-min-RB-L       | Float | Time 1 Minimum distance to the Left Bank: ${l}_{T1}$  |
| T1-max-RB-L       | Float | Time 1 Maxinum distance to the Left Bank: ${L}_{T1}$  |
| T2-min-RB-R       | Float | Time 2 Minimum distance to the Right Bank: ${r}_{T2}$ |
| T2-max-RB-R       | Float | Time 2 Maximum distance to the Right Bank: ${R}_{T2}$ |
| T2-min-RB-L       | Float | Time 2 Minimum distance to the Left Bank: ${l}_{T2}$  |
| T2-max-RB-L       | Float | Time 2 Maximum distance to the Left Bank: ${L}_{T1}$  |
| T2-T1-min-delta-L | Float | $\Delta_l$ = ${l_{T2}}$ - ${l_{T1}}$                  |
| T2-T1-min-delta-R | Float | $\Delta_r$ = ${r_{T2}}$ - ${r_{T1}}$                  |

`null` value distance is for no intersection between transects and RB

This is an example of results in attribute table

![RBDC Example B](Models/RBDC/images/RBDC-B-800px.png)

This is an example of results in maps

![RBDC Example C](Models/RBDC/images/RBDC-C.png)

***

## 6. RiverBanks Safety Bands Tool (RBSB)

![RBSB_icon](Models/RBSB/icon/RBSB_128px.png)

[return to TOC](#table-of-content)

This algorithm generates safety lines at a distance from the riverbanks, which have been previously divided into reaches. For each reach, a buffer distance is determined using a multiplicative factor of the riverbank erosion rate.

![Models/RBSB/RBSB_example.png](Models/RBSB/RBSB_example.png)

### 6.1 RBSB Input data

- *LEFT side RiverBank*: Vector that contain the LEFT side of Riverbank segments. This vector must contain at least a field with the year erosion rate to be used in calculus
- *Left Erosion Rate field*: Name of the field with values of Erosion Rate
- *RIGHT side riverBank*: Vector that contain the RIGHT side of Riverbank segments. This vector must contain at least a field with the year erosion rate to be used in calculus
- *Right Erosion Rate field*:  Name of the field with values of Erosion Rate
- *M factor for buffers*: the multiplicative factor of the erosion rate used to determine the buffer distance from riverbanks

### 6.2 RBSB Procedure description

![diagram](Models/RBSB/RBSB_diagram.png)

1. Create single-side buffer for each of RB usin the formula: $$ D = {{E_r} \cdot {M}} $$
2. Union geoprocess to merge the two buffer into one feature
3. Dissolve all feature and hole fitting for purify geometric data
4. Convert polygon to lines to get output

![model](Models/RBSB/RBSB_model.svg.png)

### 6.3 RBSB Output data

- *Offset line*: a MultiLine vector with Bands limit.

## 7. Disclaimer and credits

[return to TOC](#table-of-content)

This repository contains algorithms that for calculating and analyzing some hydrographic features that are useful for analyses on historical course trends and river geometry.

Feel free to contribute, see [Contributing guideline](CONTRIBUTING.md), please respect the [code of conduct](CODE_OF_CONDUCT.md).

The work was developed within my research at the University of Catania as Phd student, specific through a Scientific collaboration agreement between the Basin Authority of the Hydrographic District of Sicily [(AdB Sicilia)](https://www.regione.sicilia.it/istituzioni/regione/strutture-regionali/presidenza-regione/autorita-bacino-distretto-idrografico-sicilia/contatti-dipartimento-autorita-bacino-adb) and the Department of Civil Engineering and Architecture [(DICaR)](https://www.dicar.unict.it) of the University of Catania, for hydrological and hydraulic studies for the identification of river belts, for the identification of NWRM (Natural Water Retention Measures), and for the definition of lamination plans of the rivers.

### 7.1 How to cite

- Di Pietro, G., Stagnitti, M., Pennisi, V., Foti, E., and Musumeci, R. E.: Qgis RiverBanks tools suite for morphological river analysis, EGU General Assembly 2025, Vienna, Austria, 27 Apr–2 May 2025, EGU25-15570, [https://doi.org/10.5194/egusphere-egu25-15570](https://doi.org/10.5194/egusphere-egu25-15570), 2025.

see [CITATION.cff](CITATION.cff) for more details

Contributors:

- [Gianfranco Di Pietro](https://gianfrancodp.github.io), *PhD student at Università di Catania*
- Martina Stagnitti, *Researcer at Università di Catania*
- Valeria Pennisi, *Researcher at Università di Catania*
- [Rosaria Ester Musumeci](https://www.dicar.unict.it/faculty/rosaria.ester.musumeci), *Associate professor of Hydraulics - University of Catania*
- [Enrico Foti](https://www.dicar.unict.it/faculty/enrico.foti), *Full Professor of Hydraulics - University of Catania*
