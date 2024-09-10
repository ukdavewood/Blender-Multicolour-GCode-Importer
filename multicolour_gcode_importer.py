import bpy
import os

from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

from datetime import time
from time import process_time


bl_info = {
    "name": "Multicolour GCode Importer",
    "author": "David Wood, based on earlier work by Kevin Nunley",
    "version": (1, 0, 0),
    "blender": (2, 90, 0),
    "location": "File > Import",
    "description": "Import Multicolour GCode files and visualize them as 3D models",
    "warning": "",
    "doc_url": "https://github.com/kmnunley/Blender-GCode-Importer",
    "category": "Import-Export",
}

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
    bpy.ops.transform.rotate(value=3.14159, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False, alt_navigation=True)
    bpy.ops.transform.resize(value=(0.01, 0.01, 0.01), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False, alt_navigation=True)
    bpy.ops.transform.translate(value=(0, 0, 0.00999773), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False, alt_navigation=True)
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
        coord = [None, None, None, None]
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
            print(colours)
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
        if command == "G1" or command == "G0":
            coord = get_params(params)
            if len(coord) == 5:
                rate = coord[4]

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

            if e <= max_e:

                # if len(point_data) > 0:
                #     time_for_last_move = 

                if len(point_data) >= 2:

                    entry_count += 1

                    if "Layer"+str(layer)+"T"+str(tool_id) in bpy.data.objects:
                        prev_curve_object = bpy.data.objects["Layer"+str(layer)+"T"+str(tool_id)]

                        curve_data = bpy.data.objects["Layer"+str(layer)+"T"+str(tool_id)].data
                        curve_spline = curve_data.splines.new('BEZIER')

                        if point_data[0][0] == point_data[1][0] and point_data[0][1] == point_data[1][1] and point_data[0][1] == -3 and e == -2:
                                print("possible flushing",line_no,layer,tool_id,e,max_e,flush_amount,point_data)



                                
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

                    else:
 
                        # print("point_data:",point_data)
                        # Dump the curve data to a new curve object
                        # Create a new curve object
                        curve_data = bpy.data.curves.new("Layer"+str(layer)+"_"+str(entry_count), type='CURVE')
                        curve_data.dimensions = '3D'
                        curve_data.resolution_u = 1

                        # Create a curve spline and add the toolhead position as a control point
                        curve_spline = curve_data.splines.new('BEZIER')

                        if point_data[0][0] == point_data[1][0] and point_data[0][1] == point_data[1][1] and point_data[0][1] == -3 and e == -2:
                                print("possible flushingB",line_no,layer,tool_id,e,max_e,flush_amount,point_data)



                                
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

                        # Create a new object to hold the curve data
                        # prev_curve_object = None
                        # if "Layer"+str(layer)+"T"+str(tool_id) in bpy.data.objects:
                        #     prev_curve_object = bpy.data.objects["Layer"+str(layer)+"T"+str(tool_id)]
                        
                        curve_object = bpy.data.objects.new("Layer"+str(layer)+"T"+str(tool_id), curve_data)
                        curve_object.data.bevel_depth = radius
                        curve_object.data.materials.append(current_mat)

                                                # Link the object to the scene and the collection
                        bpy.context.collection.objects.link(curve_object)
                        collection.objects.link(curve_object)

                        # if prev_curve_object is None or True:
                            #curve_object.location = (0, 0, 0)
                        
                        
                        curve_object.scale = (0.0,0.0,0.0)
                        
                        curve_object.keyframe_insert(data_path="scale", frame=0)
                        
                    
                        
                        curve_object.keyframe_insert(data_path="scale", frame=frame-1)
                        # frame += 1
                          
                        curve_object.scale = (scale,scale,scale)
                        
                        curve_object.keyframe_insert(data_path="scale", frame=frame)

                        toolhead.location.x =  point_data[0][0]*scale
                        toolhead.location.y =  point_data[0][1]*scale
                        toolhead.location.z =  point_data[0][2]*scale+0.00999773
                        toolhead.keyframe_insert(data_path="location", frame=frame)




                    # else:
                    #     bpy.ops.object.select_all(action="DESELECT")
                    #     curve_object.scale = (0.01,0.01,0.01)
                    #     curve_object.select_set(True)
                    #     prev_curve_object.select_set(True)
                    #     bpy.context.view_layer.objects.active = prev_curve_object
                    #     bpy.ops.object.join()

                
                
                point_data = []
                point_data.append(toolhead_pos)

            if e > max_e:
            # if e >= max_e:
                # Update the toolhead position and add the point to the curve data
                point_data.append(toolhead_pos)
                max_e = e
            
            # else:
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
                    #curve_object.location = (0, 0, 0)
                    
                    
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
                print("Flush amount",line_no,flush_amount,point_data)
                e = coord[3]
                max_e = e

    bpy.data.scenes["Scene"].frame_end = frame+1
    print("run time:",process_time() - start)



def import_gcode(filepath):
    # Load the gcode file
    gcode_file = open(filepath, "r")
    gcode_lines = gcode_file.readlines()

    # Create the geometry
    create_paths(gcode_lines)

# Define the operator class
class ImportGCodeOperator(Operator, ImportHelper):
    bl_idname = "import_multicolour_gcode.operator"
    bl_label = "Import Mulitcolour GCode"

    filter_glob: StringProperty(
        default="*.gcode",
        options={'HIDDEN'},
    )

    def execute(self, context):

        filename, extension = os.path.splitext(self.filepath)

        import_gcode(self.filepath)
        return {'FINISHED'}

@bpy.app.handlers.persistent
def register():
    # Register the operator
    bpy.utils.register_class(ImportGCodeOperator)

    # Add the operator to the File > Import menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

@bpy.app.handlers.persistent
def unregister():
    # Remove the operator from the File > Import menu
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)

    # Unregister the operator
    bpy.utils.unregister_class(ImportGCodeOperator)

def menu_func(self, context):
    self.layout.operator(ImportGCodeOperator.bl_idname, text="MultiColour GCode (.gcode)")

if __name__ == "__main__":
    register() 
    
    
    
  