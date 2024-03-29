# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Fix ColorSpace",
    "author": "ChatGPT / Blender Bob / True-VFX",
    "blender": (2, 80, 0),
    "description": "Changes the color space of image nodes based on specific image names.",
    "category": "Material",
}

import bpy
from bpy.types import Image, Operator, Panel, ShaderNodeTree

KEYWORDS = (
    'glossiness', 'normalbump', 'specular', 'opacity', 'sss', 'subsurface', 'metallic',
    'metalness', 'metal', 'mtl', 'specularity', 'spec', 'spc', 'roughness', 'rough', 'rgh',
    'gloss', 'glossy', 'normal', 'nor', 'nrm', 'nrml', 'norm', 'bump', 'bmp', 'displacement',
    'displace', 'disp', 'dsp', 'height', 'heightmap', 'transmission', 'transparency', 'alpha', 'ao ambient', 'occlusion'
)


class FixColorSpaceBase:
    bl_options = {'REGISTER', 'UNDO'}

    # Must replace these with the color space names you want to use
    color_space:str
    non_color_space:str

    def execute(self, context):
        for image in bpy.data.images:
            has_keyword = False
            for keyword in KEYWORDS:
                if keyword in image.name.lower():
                    image.colorspace_settings.name = self.non_color_space
                    has_keyword = True
                    break
                if not has_keyword:
                    image.colorspace_settings.name = self.color_space
        return {'FINISHED'}


class FixColorSpace_OT_Filmic(FixColorSpaceBase, Operator):
    bl_idname = "scene.apply_filmic_colorspace"
    bl_label = "Filmic"

    color_space = 'sRGB'
    non_color_space = 'Raw'

class FixColorSpace_OT_ACES(FixColorSpaceBase, Operator):
    bl_idname = "scene.apply_aces_colorspace"
    bl_label = "ACES"

    color_space = 'Utility - Raw'
    non_color_space = 'Utility - sRGB - Texture'

class FixColorSpace_OT_ACEScg(FixColorSpaceBase, Operator):
    bl_idname = "scene.apply_acescg_colorspace"
    bl_label = "ACEScg"

    color_space = 'Utility - Raw'
    non_color_space = 'Utility - sRGB - Texture'


class FixColorSpace_PT_Panel(Panel):
    bl_label = "Fix Colorspace"
    bl_idname = "FixColorSpace_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        layout.operator("scene.apply_filmic_colorspace", text="To Filmic")
        layout.operator("scene.apply_aces_colorspace", text="To ACES")
        layout.operator("scene.apply_acescg_colorspace", text="To ACEScg")

classes = (
    FixColorSpace_OT_Filmic,
    FixColorSpace_OT_ACES,
    FixColorSpace_OT_ACEScg,
    FixColorSpace_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# Only needed if running from text editor. Remove if installing as an addon.
if __name__ == "__main__":
    register()
