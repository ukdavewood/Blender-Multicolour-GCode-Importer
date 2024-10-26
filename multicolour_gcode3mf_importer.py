import bpy
import os
import math

from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

from datetime import time
from time import process_time

from zipfile import ZipFile
import io


bl_info = {
    "name": "Multicolour GCode3mf Importer",
    "author": "David Wood, based on earlier work by Kevin Nunley",
    "version": (1, 0, 1),
    "blender": (2, 90, 0),
    "location": "File > Import",
    "description": "Import Multicolour GCode.3mf files and visualize them as 3D models",
    "warning": "",
    "doc_url": "https://github.com/ukdavewood/Blender-Multicolour-GCode-Importer",
    "category": "Import-Export",
}


def arcPoints(command,i,j,fromX,fromY,toX,toY,Z,point_data):
    #  derived from arc-breaker - see https://github.com/constant-flow/arc-breaker/blob/main/index.html
    rad = math.sqrt(i*i+j*j)
    cX = fromX+i
    cY = fromY+j
    startAngle = math.atan2(fromY-cY, fromX - cX)
    endAngle = math.atan2(toY-cY,toX-cX)
    aX = fromX - cX
    aY = fromY - cY
    bX = toX - cX
    bY = toY - cY

    ccwAngle = math.atan2(aX * bY - aY * bX, aX * bX + aY * bY)
    if ccwAngle < 0:
        ccwAngle += math.pi * 2
    
    totalDeltaAngle = ccwAngle
    if command == 'G2':
        totalDeltaAngle = totalDeltaAngle - math.pi * 2

    bowLen = abs(totalDeltaAngle) * rad
    requiredSegments = int(abs(rad * rad * totalDeltaAngle/math.pi * 20) )
    print('segments',requiredSegments,rad)
    if requiredSegments < 5:
        requiredSegments = 5
    if requiredSegments > 100:
        requiredSegments = 100

    deltaAngle = totalDeltaAngle / requiredSegments



    for i in range(1,requiredSegments):
        angle = startAngle + i * deltaAngle
        segX = cX + math.cos(angle) * rad
        segY = cY + math.sin(angle) * rad    
        point = [segX, segY, Z]   
        point_data.append(point)
        # print(segX,segY,)


def create_paths(gcode_lines):
    # Initialize the toolhead position and extruder temperature
    toolhead_pos = (0, 0, 0)

    start = process_time()

    # Create an empty collection to store the paths
    collection = bpy.data.collections.new("Paths")
    
    current_mat = bpy.data.materials.new(name="Green")
    current_mat.use_nodes = True
    
    bsdf = current_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs[0].default_value = (0,1,0,1)
    #current_mat.diffuse_color = (0,1,0,1)

    bpy.ops.mesh.primitive_cone_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.transform.rotate(value=3.14159, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.transform.resize(value=(0.01, 0.01, 0.01), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.transform.translate(value=(0, 0, 0.00999773), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    toolhead= bpy.context.active_object

    headpos = (0,0,0)


    materials = []
    
    absolute_coord = True
    absolute_extrude = False

    x = 0
    y = 0
    z = 0
    e = 0
    max_e = 0
    point_data = []

    def get_params(params):
        coord = [None, None, None, None, None, None, None]
        for param in params:
            try:
                if param[0] == "X":
                    coord[0] = float(param[1:])
                elif param[0] == "Y":
                    coord[1] = float(param[1:])
                elif param[0] == "Z":
                    coord[2] = float(param[1:])
                elif param[0] == "E":
                    coord[3] = float(param[1:])
                elif param[0] == "F":
                    coord[4] = float(param[1:])
                elif param[0] == "I":
                    coord[5] = float(param[1:])
                elif param[0] == "J":
                    coord[6] = float(param[1:])
            except:
                pass
        return tuple(coord)
    
    tool_id = 0
    
    frame = 0
    rate = 1

    time = 0
    prev_time = 0

    layer = 0
    prev_layer = 0
    entry_count = 0
    max_entry = 20
    detailed_start = 1
    detailed_end  = 2

    scale = 0.01
    radius = 0.2

    max_M73_R = 0
    last_remaining = 0

    prev_tool_id = -1


    line_no = 0

    flush_amount = 0


    # Iterate through the gcode instructions
    for line in gcode_lines:
        line_no += 1
        
                
        if line.startswith("; filament_colour = "):
            colours = line[20:].split(';')
            #print(colours)
            for colour in colours:

                material = bpy.data.materials.new(name=colour)
                material.use_nodes = True
    
                bsdf = material.node_tree.nodes["Principled BSDF"]
                colour_val = (int(colour[1:3], 16)/256, int(colour[3:5], 16)/256, int(colour[5:7], 16)/256, 1 )
                bsdf.inputs[0].default_value =  colour_val
                print(colour_val)
                
                materials.append(material)
            continue
        
        if line.strip().startswith('T'):
            # print(line)
            tool = int(line.strip().split(';')[0][1:])
  
            if tool+1 <= len(materials):
                current_mat = materials[tool]
                tool_id = tool
            
            continue
        
        # Skip comments
        
        if line[0] == ";":
            continue

            
        #FFFFFF;#118002;#C00D1E;#FD8008;#808080;#000000;#00358E;#B39B84;#8BD5EE;#032343")

        # Split the line into words
        words = line.split()
        if not words:
            continue

        # Extract the command and parameters
        command = words[0]
        params = words[1:]
        
        

        # Handle the movement command
        if command == "G1" or command == "G0" or command == "G2" or command == "G3":
            coord = get_params(params)
            if len(coord) >= 5:
                rate = coord[4]

            centre_pos = None
            prev_pos = None

            if coord[5] is not None and coord[6] is not None:
                    centre_pos = [toolhead_pos[0]+coord[5],toolhead_pos[1]+coord[6],toolhead_pos[2]]
                    prev_pos = toolhead_pos

            if absolute_coord:
                toolhead_pos = (
                    toolhead_pos[0] if coord[0] is None else coord[0],
                    toolhead_pos[1] if coord[1] is None else coord[1],
                    toolhead_pos[2] if coord[2] is None else coord[2]
                )
            else:
                
                toolhead_pos =  (
                    toolhead_pos[0] if coord[0] is None else coord[0]+ toolhead_pos[0],
                    toolhead_pos[1] if coord[1] is None else coord[1]+ toolhead_pos[1],
                    toolhead_pos[2] if coord[2] is None else coord[2]+ toolhead_pos[2]
                )
              
            if coord[3] is not None:
                if absolute_extrude:
                    e = coord[3]
                else:
                    e = e + coord[3]

            if e <= max_e:   #  retracted

                if len(point_data) >= 2:  # if extrusion already happened

                    entry_count += 1

                    if "Layer"+str(layer)+"T"+str(tool_id) in bpy.data.objects:  #  Curve on this layer for this colour already exists
                        prev_curve_object = bpy.data.objects["Layer"+str(layer)+"T"+str(tool_id)]

                        curve_data = bpy.data.objects["Layer"+str(layer)+"T"+str(tool_id)].data
                        curve_spline = curve_data.splines.new('BEZIER')

                        if point_data[0][0] == point_data[1][0] and point_data[0][1] == point_data[1][1] and point_data[0][1] == -3 and e == -2:
                                #print("possible flushing",line_no,layer,tool_id,e,max_e,flush_amount,point_data)

                                curve_spline.bezier_points[0].co = (tool_id*10, 350, point[2])
                                curve_spline.bezier_points.add(1)
                                curve_spline.bezier_points[-1].co = (tool_id*10, 350+flush_amount, point[2])
                                
                        else:

                            for index, point in enumerate(point_data):
                                if index == 0:

                                        curve_spline.bezier_points[0].co = point
                                else:
                                    curve_spline.bezier_points.add(1)
                                    curve_spline.bezier_points[-1].co = point

                    else:  # If Curve doesn't exist for tool on layer
 
                        curve_data = bpy.data.curves.new("Layer"+str(layer)+"_"+str(entry_count), type='CURVE')
                        curve_data.dimensions = '3D'
                        curve_data.resolution_u = 1

                        # Create a curve spline and add the toolhead position as a control point
                        curve_spline = curve_data.splines.new('BEZIER')

                        if point_data[0][0] == point_data[1][0] and point_data[0][1] == point_data[1][1] and point_data[0][1] == -3 and e == -2:
                                #print("possible flushingB",line_no,layer,tool_id,e,max_e,flush_amount,point_data)

                                curve_spline.bezier_points[0].co = (tool_id*10, 350, point[2])
                                curve_spline.bezier_points.add(1)
                                curve_spline.bezier_points[-1].co = (tool_id*10, 350+flush_amount, point[2])
                                
                        else:
                            for index, point in enumerate(point_data):
                                if index == 0:

                                    curve_spline.bezier_points[0].co = point
                                else:
                                    curve_spline.bezier_points.add(1)
                                    curve_spline.bezier_points[-1].co = point

                        curve_object = bpy.data.objects.new("Layer"+str(layer)+"T"+str(tool_id), curve_data)
                        curve_object.data.bevel_depth = radius
                        curve_object.data.materials.append(current_mat)

                        # Link the object to the scene and the collection
                        bpy.context.collection.objects.link(curve_object)
                        collection.objects.link(curve_object)

                        curve_object.scale = (0.0,0.0,0.0)
                        
                        curve_object.keyframe_insert(data_path="scale", frame=0)
                              
                        curve_object.keyframe_insert(data_path="scale", frame=frame-1)
                          
                        curve_object.scale = (scale,scale,scale)
                        
                        curve_object.keyframe_insert(data_path="scale", frame=frame)

                        toolhead.location.x =  point_data[0][0]*scale
                        toolhead.location.y =  point_data[0][1]*scale
                        toolhead.location.z =  point_data[0][2]*scale+0.00999773
                        toolhead.keyframe_insert(data_path="location", frame=frame)
                                
                point_data = []
                point_data.append(toolhead_pos)

            if e > max_e:

                # Update the toolhead position and add the point to the curve data
                if centre_pos is not None:
                    arcPoints(command,coord[5],coord[6],prev_pos[0],prev_pos[1],toolhead_pos[0],toolhead_pos[1],toolhead_pos[2],point_data)

                    #point_data.append(centre_pos)

                point_data.append(toolhead_pos)
                max_e = e
            
                # Check if there are enough points to create a curve
                if len(point_data) >= 2 and layer >= detailed_start and layer  < detailed_end and entry_count < max_entry:

                    entry_count += 1
                    # print("point_data:",point_data)
                    # Dump the curve data to a new curve object
                    # Create a new curve object
                    curve_data = bpy.data.curves.new("Layer"+str(layer)+"D", type='CURVE')
                    curve_data.dimensions = '3D'
                    curve_data.resolution_u = 1

                    # Create a curve spline and add the toolhead position as a control point
                    curve_spline = curve_data.splines.new('BEZIER')
                    for index, point in enumerate(point_data):
                        if index == 0:

                            curve_spline.bezier_points[0].co = point
                        else:
                            curve_spline.bezier_points.add(1)
                            curve_spline.bezier_points[-1].co = point
                            # curve_spline.bezier_points[-1].tilt = 180

                    # Create a new object to hold the curve data
                    curve_object = bpy.data.objects.new("Layer"+str(layer)+"D", curve_data)
                    curve_object.data.bevel_depth = radius
                    curve_object.data.materials.append(current_mat)

                    curve_object.scale = (0.0,0.0,0.0)
                    
                    curve_object.keyframe_insert(data_path="scale", frame=0)
                    
                    curve_object.keyframe_insert(data_path="scale", frame=frame)
                    frame += 1
                    
                    curve_object.scale = (scale,scale,scale)
                    
                    curve_object.keyframe_insert(data_path="scale", frame=frame)

                    toolhead.location.x =  toolhead_pos[0]*scale
                    toolhead.location.y =  toolhead_pos[1]*scale
                    toolhead.location.z =  toolhead_pos[2]*scale+0.00999773
                    toolhead.keyframe_insert(data_path="location", frame=frame)

   
                    # Link the object to the scene and the collection
                    bpy.context.collection.objects.link(curve_object)
                    collection.objects.link(curve_object)
                
                # Reset the point data
                    point_data = []
                    point_data.append(toolhead_pos)

        # Handle mode commands

        elif command == "M82":
            absolute_extrude = True

        elif command == "M73":
            for param in params:
                if param[0] == "R":
                    Remaining = int(param[1:])
                    if Remaining > max_M73_R:
                        max_M73_R = Remaining

                    if Remaining != last_remaining:
                        if "Geometry Nodes" in bpy.data.node_groups and "Integer" in  bpy.data.node_groups["Geometry Nodes"].nodes:
                            bpy.data.node_groups["Geometry Nodes"].nodes["Integer"].integer = max_M73_R - Remaining

                            bpy.data.node_groups["Geometry Nodes"].nodes["Integer"].keyframe_insert(data_path="integer", frame=frame)



   


                        last_remaining = Remaining




            
        elif command == "M991":
            layer += 1
            frame += 1

        elif command == "M83":
            absolute_extrude = False

        elif command == "G90":
            absolute_coord = True
            absolute_extrude = True

        elif command == "G91":
            absolute_coord = False
            absolute_extrude = False

        elif command == "G92":
            coord = get_params(params)

            toolhead_pos = (
                toolhead_pos[0] if coord[0] is None else coord[0],
                toolhead_pos[1] if coord[1] is None else coord[1],
                toolhead_pos[2] if coord[2] is None else coord[2]
            )

            if coord[3] is not None:
                flush_amount = max_e
                #print("Flush amount",line_no,flush_amount,point_data)
                e = coord[3]
                max_e = e

    bpy.data.scenes["Scene"].frame_end = frame+1
    print("run time:",process_time() - start)



def import_gcode3mf(f):

    gcode_lines = f.readlines()

    # Create the geometry
    create_paths(gcode_lines)

# Define the operator class
class ImportGCodeOperator(Operator, ImportHelper):
    bl_idname = "import_multicolour_gcode3mf.operator"
    bl_label = "Import Mulitcolour GCode 3mf"

    filter_glob: StringProperty(
        default="*.gcode.3mf",
        options={'HIDDEN'},
    )

    def execute(self, context):

        filename, extension = os.path.splitext(self.filepath)

        with ZipFile(self.filepath, "r") as f3mf:
            
            plate_list = ""

            for name in f3mf.namelist():
                #print(name)
              
                if name.endswith(".gcode"):
                    if plate_list != "":
                        plate_list = plate_list + ','
                    #print(name)
                    number = name.split('_')[1].split('.')[0]
                    if len(number) == 1:
                        number = '0'+ number 
                    plate_list = plate_list + number

                    
                    # with io.TextIOWrapper(f3mf.open(name), encoding="utf-8") as f:

                    #     import_gcode3mf(f)
            
            if plate_list != "":
                    list = plate_list.split(',')
                    list.sort()
                    plate_list = ",".join(list)
                    max_plate =  int(list[-1])
                    bpy.ops.wm.myop('INVOKE_DEFAULT',plate_list=plate_list,plate_max = max_plate,file = self.filepath)
                    self.report({'INFO'},"XXX")
            else:
                    self.report({'ERROR'},"no plates found")

        return {'FINISHED'}
    


class WM_OT_myOp(bpy.types.Operator):
    """Create Timelapse from gcode.3mf"""
    bl_label = "gcode.3mf import options"
    bl_idname = "wm.myop"
    
    file : bpy.props.StringProperty(name= "File", default= "")
    
    plate_list : bpy.props.StringProperty(name= "Plates", default= "")

    plate_max: bpy.props.IntProperty(name= "Max:", default= 1,options = {'HIDDEN'})
    plate : bpy.props.IntProperty(name= "Plate:", default= 1, min=1, max=50)
    
    
    
    def execute(self, context):
        
        s = self.plate
        m = self.plate_max
        
        if s > m:
            self.report({'ERROR'},"plate mumber out of range")
            bpy.ops.wm.myop('INVOKE_DEFAULT',plate_list=self.plate_list,plate_max = self.plate_max, plate=self.plate,file = self.file)
            return {'FINISHED'}
        else:

            name = "Metadata/plate_" + str(self.plate) + '.gcode'
            print(name)        

            with ZipFile(self.file, "r") as f3mf:
                
                        
                with io.TextIOWrapper(f3mf.open(name), encoding="utf-8") as f:

                    import_gcode3mf(f)
                
                
            return {'FINISHED'}
        
    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self)
 
 
 

@bpy.app.handlers.persistent
def register():
    # Register the operator
    bpy.utils.register_class(ImportGCodeOperator)

    # Add the operator to the File > Import menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

    bpy.utils.register_class(WM_OT_myOp)

@bpy.app.handlers.persistent
def unregister():
    # Remove the operator from the File > Import menu
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)

    # Unregister the operator
    bpy.utils.unregister_class(ImportGCodeOperator)

    bpy.utils.unregister_class(WM_OT_myOp)

def menu_func(self, context):
    self.layout.operator(ImportGCodeOperator.bl_idname, text="MultiColour V1 (.gcode.3mf)")

if __name__ == "__main__":
    register() 
    
    
    
  