import bpy
import math
import os

OUTPUT_DIR = os.path.abspath("assets/icons")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def setup_render(resolution=(256, 256)):
    scene = bpy.context.scene
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderSettings') and 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items else 'BLENDER_EEVEE'

def add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.0):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    cam = bpy.context.active_object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho_scale
    bpy.context.scene.camera = cam
    return cam

def add_lights():
    bpy.ops.object.light_add(type='SUN', location=(3, -4, 5))
    sun = bpy.context.active_object
    sun.data.energy = 4.5
    sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(-30))

    bpy.ops.object.light_add(type='POINT', location=(-3, 2, 3))
    rim = bpy.context.active_object
    rim.data.energy = 90.0
    rim.data.color = (1.0, 0.9, 0.8)

def create_mat(name, color, roughness=0.35, metallic=0.05, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emission:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emission
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emission
    return mat

def render_basketball(is_empty=False):
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.2, 0), rot=(math.radians(90), 0, 0), ortho_scale=2.7)
    add_lights()

    if is_empty:
        ball_mat = create_mat("GhostBall", (0.22, 0.25, 0.32, 0.6), roughness=0.6, metallic=0.2)
        seam_mat = create_mat("GhostSeam", (0.12, 0.14, 0.18, 0.6), roughness=0.8, metallic=0.1)
    else:
        # Classic NBA pebbler orange with slight sheen
        ball_mat = create_mat("NBABall", (0.95, 0.38, 0.08, 1.0), roughness=0.32, metallic=0.08,
                              emission=(0.95, 0.35, 0.08, 1.0), emission_strength=0.6)
        seam_mat = create_mat("Seams", (0.1, 0.08, 0.08, 1.0), roughness=0.5, metallic=0.2)

    # Main sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=1.0, location=(0, 0, 0))
    ball = bpy.context.active_object
    ball.data.materials.append(ball_mat)

    # Basketball black seam ribs (tori around sphere)
    # 1. Equator seam
    bpy.ops.mesh.primitive_torus_add(major_radius=1.005, minor_radius=0.028, location=(0, 0, 0), rotation=(0, 0, 0))
    s1 = bpy.context.active_object
    s1.data.materials.append(seam_mat)

    # 2. Vertical longitudinal seam
    bpy.ops.mesh.primitive_torus_add(major_radius=1.005, minor_radius=0.028, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
    s2 = bpy.context.active_object
    s2.data.materials.append(seam_mat)

    # 3. Diagonal curved seams
    bpy.ops.mesh.primitive_torus_add(major_radius=1.005, minor_radius=0.025, location=(0, 0, 0), rotation=(0, math.radians(45), math.radians(45)))
    s3 = bpy.context.active_object
    s3.data.materials.append(seam_mat)

    bpy.ops.mesh.primitive_torus_add(major_radius=1.005, minor_radius=0.025, location=(0, 0, 0), rotation=(0, math.radians(-45), math.radians(-45)))
    s4 = bpy.context.active_object
    s4.data.materials.append(seam_mat)

    filename = "basketball_empty.png" if is_empty else "basketball.png"
    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, filename)
    bpy.ops.render.render(write_still=True)
    print("Rendered " + filename)

def render_basketball_hoop():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0.2), rot=(math.radians(85), 0, 0), ortho_scale=3.2)
    add_lights()

    rim_mat = create_mat("OrangeRim", (1.0, 0.28, 0.05, 1.0), roughness=0.2, metallic=0.8,
                         emission=(1.0, 0.25, 0.05, 1.0), emission_strength=1.5)
    net_mat = create_mat("WhiteNet", (0.95, 0.95, 0.95, 0.9), roughness=0.4, metallic=0.1)
    board_mat = create_mat("Backboard", (0.2, 0.3, 0.45, 0.8), roughness=0.1, metallic=0.9)

    # Backboard
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.6, 0.5))
    bb = bpy.context.active_object
    bb.scale = (1.5, 0.08, 1.0)
    bb.data.materials.append(board_mat)

    # Orange rim (torus)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.07, location=(0, 0, 0.1), rotation=(0, 0, 0))
    rim = bpy.context.active_object
    rim.data.materials.append(rim_mat)

    # Net (tapered cylinder/cone)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.68, radius2=0.38, depth=0.9, location=(0, 0, -0.4))
    net = bpy.context.active_object
    net.data.materials.append(net_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "basketball_hoop.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered basketball_hoop.png")

if __name__ == "__main__":
    render_basketball(is_empty=False)
    render_basketball(is_empty=True)
    render_basketball_hoop()
    print("Basketball 3D assets render complete!")
