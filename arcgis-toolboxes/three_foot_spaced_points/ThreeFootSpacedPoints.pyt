import arcpy
import os
import math

class Toolbox(object):
    def __init__(self):
        """Define the toolbox with its label and alias, and list the tools it contains."""
        self.label = "3-foot Spaced Points"
        self.alias = "3-foot Spaced Points"
        self.tools = [GeneratePoints]

class GeneratePoints(object):
    def __init__(self):
        """Define the tool with its label and description."""
        self.label = "Generate Points at 3-Foot Intervals"
        self.description = ("Creates a line from user‑defined pairs of points based on their OBJECTIDs and "
                            "generates points along each line at 3‑foot intervals. Generated points that are "
                            "within 2 feet of either endpoint are omitted.")

    #Define paramater definitions
    def getParameterInfo(self):
        """Define parameter definitions."""
        # Parameter 0: Input points feature class.
        param0 = arcpy.Parameter(
            displayName="Input Feature Class",
            name="input_points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 1: Output line feature class.
        param1 = arcpy.Parameter(
            displayName="Output Line Feature Class",
            name="output_lines",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        # Parameter 2: Output points feature class.
        param2 = arcpy.Parameter(
            displayName="Output Points Feature Class",
            name="output_points",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        # Parameter 3: Pairs of OBJECTIDs as a text string.
        param3 = arcpy.Parameter(
            displayName="Pairs of OBJECTIDs",
            name="pairs",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        # Expected format: "1,2;3,4;5,6;7,8;..."
        param3.filter.type = "String"
        param3.value = "1,2;3,4"  # Example default.

        # --- NEW Parameter 4: Center point OBJECTID for circle mode ---
        param4 = arcpy.Parameter(
            displayName="Circle Center Point OBJECTID",
            name="circle_center_oid",
            datatype="GPLong",
            parameterType="Optional",   # Optional — only used for circle mode
            direction="Input")

        # also new, object ID of point in the circle"
        param5 = arcpy.Parameter(
            displayName="Circle Edge Reference Point OBJECTID",
            name="circle_edge_oid",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input")

        return [param0, param1, param2, param3, param4, param5]

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify parameter values and properties before internal validation is performed."""
        return

    def updateMessages(self, parameters):
        # Warn if neither pairs nor circle parameters are provided
        pairs_empty = not parameters[3].valueAsText or parameters[3].valueAsText.strip() == ""
        circle_oid_empty = not parameters[4].valueAsText
        circle_radius_empty = not parameters[5].valueAsText

        if pairs_empty and (circle_oid_empty or circle_radius_empty):
            parameters[3].setWarningMessage(
                "Enter pairs in the format: OBJECTID1,OBJECTID2;OBJECTID3,OBJECTID4; ..."
                " OR provide a Circle Center OBJECTID and Radius.")

        # Warn if only one of the two circle params is filled
        if not circle_oid_empty and circle_radius_empty:
            parameters[5].setWarningMessage("Please also enter an edge reference point OBJECTID for the circle.")
        if circle_oid_empty and not circle_radius_empty:
            parameters[4].setWarningMessage("Please also enter a center point OBJECTID for the circle.")

        return


    def execute(self, parameters, messages):
        """The source code of the tool."""
        #input layer's path
        inputPoints = parameters[0].valueAsText
        #output lines layer's path, user can pick name
        outputLines = parameters[1].valueAsText

        #output lines layer's path, user can pick name
        outputPoints = parameters[2].valueAsText

        #User's inputted points
        pairs_text = parameters[3].valueAsText
        
        # object ID of the center of the circle
        circle_center_oid = parameters[4].value          # integer or None
        
        # object ID of the edge point of the circle
        circle_edge_oid  = parameters[5].value          # float or None

        #Let us plot on new feature layers.
        arcpy.env.overwriteOutput = True

        # Define spacing (3 feet) and minimum distance (2 feet).
        spacing = .9144
        min_distance_threshold = .6096

        # Get the spatial reference from the input feature class.
        spatial_ref = arcpy.Describe(inputPoints).spatialReference

        # Create output feature classes.
        out_lines_path = os.path.dirname(outputLines)
        out_lines_name = os.path.basename(outputLines)
        arcpy.CreateFeatureclass_management(out_lines_path, out_lines_name, "POLYLINE", spatial_reference=spatial_ref)

        out_points_path = os.path.dirname(outputPoints)
        out_points_name = os.path.basename(outputPoints)
        arcpy.CreateFeatureclass_management(out_points_path, out_points_name, "POINT", spatial_reference=spatial_ref)


        # Optionally add a "PairID" field to both outputs.
        for fc in [outputLines, outputPoints]:
            if len(arcpy.ListFields(fc, "PairID")) == 0:
                arcpy.AddField_management(fc, "PairID", "LONG")

        # Build a lookup dictionary for input points by OBJECTID.
        # Use .firstPoint to ensure we have an arcpy.Point object (with X and Y properties).
        feature_dict = {}
        with arcpy.da.SearchCursor(inputPoints, ["OID@", "SHAPE@"]) as cursor:
            for row in cursor:
                oid = row[0]
                feature_dict[oid] = row[1].firstPoint

        # Helper function: create a line from a list of points.
        def generate_line_from_points(point_list):
            array = arcpy.Array(point_list)#organizing points into an arcpy array
            return arcpy.Polyline(array)#making lines from the points

        # Helper function: compute Euclidean distance between two arcpy.Point objects.
        def distance(pt1, pt2):
            return math.hypot(pt1.X - pt2.X, pt1.Y - pt2.Y)#distance between points using pythagorean theorem

        # Helper function: generate points along a line at the specified spacing.
        # It converts the returned geometry to a Point object using .firstPoint.
        def generate_points_along_line(line, spacing, pt1, pt2, min_threshold):
            pts_along = []
            total_length = line.length
            distance_along = 0.0
            while distance_along <= total_length:
                # Get the point geometry from the line at certain distance.
                pt_geom = line.positionAlongLine(distance_along)
                # Convert it to an arcpy.Point.
                pt = pt_geom.firstPoint
                # Check if this generated point is sufficiently distant from both endpoints.
                if distance(pt, pt1) >= min_threshold and distance(pt, pt2) >= min_threshold:
                    pts_along.append(pt_geom)  # Keep the geometry for output.
                distance_along += spacing
            return pts_along
        
        def generate_points_on_circle(center_pt, radius_m, spacing_m):
            """
            Places points around a circle so that the arc length between
            consecutive points equals spacing_m (3 feet).

            The angle step between points (in radians) is:
                angle_step = arc_length / radius = spacing_m / radius_m

            We walk from 0 to 2π, placing a point at each angle step.
            The last point is intentionally skipped if it would land on top
            of the first (i.e., we stop just before completing the full loop).
            """
            pts = []
            angle_step = spacing_m / radius_m   # radians between each point

            # Number of evenly spaced points that fit around the full circle
            num_points = int(2 * math.pi / angle_step)

            for i in range(num_points):
                angle = i * angle_step
                x = center_pt.X + radius_m * math.cos(angle)
                y = center_pt.Y + radius_m * math.sin(angle)
                pt = arcpy.Point(x, y)
                pts.append(arcpy.PointGeometry(pt, spatial_ref))

            return pts

        generated_point_rows = []
        pair_id = 1

        with arcpy.da.InsertCursor(outputLines, ["SHAPE@", "PairID"]) as lineCursor:

            # Only run pair logic if pairs were provided
            if pairs_text and pairs_text.strip():
                pair_list = []
                for pair in pairs_text.split(";"):
                    parts = pair.split(",")
                    if len(parts) == 2:
                        try:
                            oid1 = int(parts[0].strip())
                            oid2 = int(parts[1].strip())
                            pair_list.append((oid1, oid2))
                        except Exception as e:
                            arcpy.AddError("Error parsing pair '{}': {}".format(pair, e))
                    else:
                        arcpy.AddError("Invalid pair format: '{}'. Use 'OBJECTID1,OBJECTID2'.".format(pair))

                for oid1, oid2 in pair_list:
                    if oid1 not in feature_dict or oid2 not in feature_dict:
                        arcpy.AddWarning("Skipping pair {} and {}: OBJECTID not found.".format(oid1, oid2))
                        continue
                    pt1 = feature_dict[oid1]
                    pt2 = feature_dict[oid2]
                    line = generate_line_from_points([pt1, pt2])
                    lineCursor.insertRow([line, pair_id])
                    pts = generate_points_along_line(line, spacing, pt1, pt2, min_distance_threshold)
                    for pt_geom in pts:
                        generated_point_rows.append((pt_geom, pair_id))
                    pair_id += 1

            # ── NEW: Circle logic ─────────────────────────────────────────────
            circle_edge_oid = parameters[5].value

            if circle_center_oid is not None and circle_edge_oid is not None:

                if circle_center_oid not in feature_dict:
                    arcpy.AddError("Circle center OBJECTID {} not found.".format(circle_center_oid))
                elif circle_edge_oid not in feature_dict:
                    arcpy.AddError("Circle edge OBJECTID {} not found.".format(circle_edge_oid))
                else:
                    center_pt = feature_dict[circle_center_oid]
                    edge_pt = feature_dict[circle_edge_oid]

                    # Radius is just the straight-line distance between the two points
                    radius_m = math.hypot(edge_pt.X - center_pt.X, edge_pt.Y - center_pt.Y)

                    # Everything below stays exactly the same as before
                    circle_pts = generate_points_on_circle(center_pt, radius_m, spacing)

                    raw_points = [arcpy.Point(pg.firstPoint.X, pg.firstPoint.Y) for pg in circle_pts]
                    raw_points.append(raw_points[0])
                    circle_line = arcpy.Polyline(arcpy.Array(raw_points), spatial_ref)
                    lineCursor.insertRow([circle_line, pair_id])

                    for pt_geom in circle_pts:
                        generated_point_rows.append((pt_geom, pair_id))

                    pair_id += 1

        # Insert all generated points (lines + circle combined)
        with arcpy.da.InsertCursor(outputPoints, ["SHAPE@", "PairID"]) as pointCursor:
            for row in generated_point_rows:
                pointCursor.insertRow(row)

        return
