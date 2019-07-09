
bl_info = {
    "name": "Optimuscan importer",
    "author": "IK3D/Issa",
    "version": (0, 2),
    "blender": (2, 80, 0),
    "location": "File > Import > Optimuscan",
    "description": "Import scan with scale texture (.obj)",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
    }


import bpy, os
import tempfile


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty


from bpy.utils import register_class
from bpy.utils import unregister_class


from bpy.types import Operator


def set_mat(data):
    """Setup material acording to scene render engine"""
    mat = data["model"][2] 

    
    #CYCLES
    if bpy.context.scene.render.engine in ['CYCLES','BLENDER_EEVEE']:
        mat.use_nodes = True
        
        for N in mat.node_tree.nodes: mat.node_tree.nodes.remove(N);

        nodeMat = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        nodeOut = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        
        mat.node_tree.links.new(nodeMat.outputs[0],nodeOut.inputs[0])
        nodeOut.location = (600,0)

        albedo = data.get("albedo", None)
        if albedo:
            nodeAlbedo = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
            nodeAlbedo.label = "Albedo"
            nodeAlbedo.location = (-500,-150*0)
            nodeAlbedo.image = data["albedo"][2]
            
            oclusion = data.get("oclusion", None)
            if oclusion:
                AO = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
                AO.label = "AO"
                AO.location = (-500, 250)
                AO.image = data["oclusion"][2]

                mul = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
                mul.location = (-200, 150)
                mul.blend_type = 'MULTIPLY'
                mul.inputs[0].default_value = 0.150
                
                mat.node_tree.links.new(AO.outputs[0],mul.inputs[2])
                mat.node_tree.links.new(nodeAlbedo.outputs[0],mul.inputs[1])
                mat.node_tree.links.new(mul.outputs[0],nodeMat.inputs[0])
            else:
                mat.node_tree.links.new(nodeAlbedo.outputs[0],nodeMat.inputs[0])

        roughness = data.get("roughness", None)
        if roughness:
            nodeRoughness = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
            nodeRoughness.label = "Roughness"
            nodeRoughness.location = (-500,-150*2)
            nodeRoughness.image = data["roughness"][2]
            nodeRoughness.image.colorspace_settings.name = 'Non-Color'
            mat.node_tree.links.new(nodeRoughness.outputs[0],nodeMat.inputs[7])

        normal = data.get("normal", None)
        if normal:
            mapNor = mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
            mapNor.location = (-200,-150*4)
            mapNor.inputs[0].default_value = 0.5


            nodeNormal = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
            nodeNormal.label = "Normal"
            nodeNormal.location = (-500,-150*4)
            nodeNormal.image = data["normal"][2]
            nodeNormal.image.colorspace_settings.name = 'Non-Color'

            mat.node_tree.links.new(nodeNormal.outputs[0],mapNor.inputs[1])
            mat.node_tree.links.new(mapNor.outputs[0],nodeMat.inputs[19])

        height = data.get("height", None)
        if height:
            nodeHeight = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
            nodeDisplace = mat.node_tree.nodes.new(type="ShaderNodeDisplacement")
            nodeHeight.label = "Height"
            nodeHeight.location = (-500,-150*5)
            nodeDisplace.location = (-200,-150*5)
            nodeHeight.image = data["height"][2]
            nodeHeight.image.colorspace_settings.name = 'Non-Color'
            mat.node_tree.links.new(nodeHeight.outputs[0],nodeDisplace.inputs[1])
            mat.node_tree.links.new(nodeDisplace.outputs[0],nodeOut.inputs[2])

    


def bImage(fullPath, check = False):
    return bpy.data.images.load(fullPath, check_existing=check)

def getFolderData(userPath):
    """ returne {stDdata:[Name, fullPath, blenderImage ], ...}"""
    folderPath = os.path.split(userPath)[0]
    filenames = next(os.walk( folderPath))[2]

    folderData = {}

    
    base = "" #analyse folder
    for filename in filenames:
        name, ext = os.path.splitext(filename)
        fullPath  = os.path.join(folderPath, filename)
        base = os.path.split(fullPath)[0]

        if not ext.lower() in [".jpg", ".png", ".tga", ".exr", ".tif", ".obj"]:
            continue
        if ext.lower() == ".obj":
            folderData["model"] = [name+ext, fullPath, None]
            continue
        if ("albedo" in name.lower() or "diffu" in name.lower()) and (not "original" in name.lower()):
            folderData["albedo"] = [name+ext, fullPath, bImage(fullPath)]
            continue


        if ("normal" in name.lower()):
            folderData["normal"] = [name+ext, fullPath, bImage(fullPath)]
            continue
        if ("height" in name.lower() or "displ" in name.lower()):
            folderData["height"] = [name+ext, fullPath, bImage(fullPath)]
            continue
        if ("roughnes" in name.lower()):
            folderData["roughness"] = [name+ext, fullPath, bImage(fullPath)]
            continue
        if ("_ao" in name.lower()):
            folderData["oclusion"] = [name+ext, fullPath, bImage(fullPath)]
            continue

    return folderData


def resize_then_pack(userPath, width):
    """resize then pack image to blender"""
    tempDir = tempfile.gettempdir()
    images = getFolderData(userPath)
    if len(images) > 1:
        for key, img in images.items(): 
            
            if key == "model":
                continue

            name, ext = os.path.splitext(img[0])
            resizedImgName = "%s_%i%s"%(name,width,ext)
            tmpImgPath = os.path.join(tempDir, resizedImgName)

            x, y = img[2].size
            if x > width > 0:
                
                img[2].scale(width, width)
                img[2].save_render(tmpImgPath)
                #remove original img to blender
                bpy.data.images.remove(img[2], do_unlink=True)
                #load resized img
                img[2] = bImage(tmpImgPath, True)
                images[key] = img
            
            # pack image to blender
            img[2].pack() 
            if os.path.isfile(tmpImgPath):
                os.remove(tmpImgPath)
        
    return images
 



def read_folder_data(context, filepath, width):

    #{[dataName, fullPath, blenderImage/modelMaterial ], ...}
    data = resize_then_pack(filepath, width)
    
    #importer model
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.obj(filepath=data["model"][1])
    context.view_layer.objects.active = context.selected_objects[0]

    mat = None
    if context.active_object.material_slots:
        if context.active_object.material_slots[0].material:
            mat = context.active_object.material_slots[0].material
        else:
            #add the material to the object
            mat = bpy.data.materials.new(name=os.path.splitext(data["model"][0])[0]) 
            activeObject.data.materials.append(mat) 
    
    data["model"][2] = mat
    set_mat(data) if not mat == None else None


    return {'FINISHED'}





class ImportOptimuScan(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_optimuscan.obj_data"  # important since its how bpy.ops.import_optimuscan.obj_data is constructed
    bl_label = "Import Optimuscan"

    # ImportHelper mixin class uses this
    filename_ext = ".obj"

    filter_glob: StringProperty(
            default="*.obj",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    width: IntProperty(
            name="Texture width",
            description="Resize texture width, 0 mean full resolution",
            default=1024,
            )


    def execute(self, context):
        return read_folder_data(context, self.filepath, self.width)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportOptimuScan.bl_idname, text="Optimuscan (.obj)")


def register():
    bpy.utils.register_class(ImportOptimuScan)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportOptimuScan)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.import_test.some_data('INVOKE_DEFAULT')
