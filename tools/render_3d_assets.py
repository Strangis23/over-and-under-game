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
    # Use EEVEE or CYCLES; EEVEE is fast and crisp
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderSettings') and 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items else 'BLENDER_EEVEE'

def add_camera(loc=(0, -5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.5):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    cam = bpy.context.active_object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho_scale
    bpy.context.scene.camera = cam
    return cam

def add_lights():
    # Key light
    bpy.ops.object.light_add(type='SUN', location=(3, -4, 5))
    sun = bpy.context.active_object
    sun.data.energy = 4.0
    sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(-30))

    # Rim light
    bpy.ops.object.light_add(type='POINT', location=(-3, 2, 3))
    rim = bpy.context.active_object
    rim.data.energy = 80.0
    rim.data.color = (0.5, 0.8, 1.0)

def create_metallic_mat(name, color, roughness=0.2, metallic=0.9, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emission:
            # Godot / Blender 4+ emission inputs
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emission
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emission
    return mat

def render_trophy():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0.4), rot=(math.radians(90), 0, 0), ortho_scale=3.8)
    add_lights()

    gold_mat = create_metallic_mat("Gold", (1.0, 0.82, 0.15, 1.0), roughness=0.18, metallic=0.95)
    base_mat = create_metallic_mat("Base", (0.1, 0.1, 0.15, 1.0), roughness=0.4, metallic=0.8)

    # Base cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.4, location=(0, 0, -1.2))
    base = bpy.context.active_object
    base.data.materials.append(base_mat)

    # Stem cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.9, location=(0, 0, -0.6))
    stem = bpy.context.active_object
    stem.data.materials.append(gold_mat)

    # Cup bowl (cone tapered)
    bpy.ops.mesh.primitive_cone_add(radius1=0.9, radius2=0.3, depth=1.3, location=(0, 0, 0.4))
    cup = bpy.context.active_object
    cup.data.materials.append(gold_mat)

    # Handles (torus on sides)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.85, minor_radius=0.1, location=(0, 0, 0.5), rotation=(0, math.radians(90), 0))
    handles = bpy.context.active_object
    handles.scale = (0.2, 0.8, 1.0)
    handles.data.materials.append(gold_mat)

    # Star on cup
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.22, location=(0, -0.7, 0.6))
    star = bpy.context.active_object
    star.data.materials.append(create_metallic_mat("StarGlow", (1.0, 1.0, 0.5, 1.0), roughness=0.1, metallic=0.5, emission=(1.0, 0.9, 0.2, 1.0), emission_strength=2.0))

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "trophy.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered trophy.png")

def render_flame():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0.2), rot=(math.radians(90), 0, 0), ortho_scale=3.5)
    add_lights()

    flame_mat = create_metallic_mat("Flame", (1.0, 0.35, 0.05, 1.0), roughness=0.3, metallic=0.2, emission=(1.0, 0.4, 0.0, 1.0), emission_strength=2.5)
    inner_mat = create_metallic_mat("FlameInner", (1.0, 0.85, 0.1, 1.0), roughness=0.2, metallic=0.1, emission=(1.0, 0.9, 0.2, 1.0), emission_strength=4.0)

    # Outer teardrop flame
    bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0.05, depth=1.8, location=(0, 0, 0.2))
    flame = bpy.context.active_object
    flame.rotation_euler = (0, 0, math.radians(-10))
    flame.data.materials.append(flame_mat)

    # Secondary flame lick
    bpy.ops.mesh.primitive_cone_add(radius1=0.5, radius2=0.02, depth=1.3, location=(-0.4, 0.1, -0.1))
    lick1 = bpy.context.active_object
    lick1.rotation_euler = (0, 0, math.radians(25))
    lick1.data.materials.append(flame_mat)

    # Core inner hot flame
    bpy.ops.mesh.primitive_cone_add(radius1=0.45, radius2=0.03, depth=1.0, location=(0, -0.1, -0.1))
    core = bpy.context.active_object
    core.data.materials.append(inner_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "flame.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered flame.png")

def render_vs_badge():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.2)
    add_lights()

    # Outer hexagonal shield/badge
    badge_mat = create_metallic_mat("Badge", (0.15, 0.18, 0.28, 1.0), roughness=0.2, metallic=0.95)
    rim_mat = create_metallic_mat("Rim", (1.0, 0.25, 0.45, 1.0), roughness=0.15, metallic=0.85, emission=(1.0, 0.2, 0.4, 1.0), emission_strength=1.8)

    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.3, depth=0.3, location=(0, 0, 0))
    badge = bpy.context.active_object
    badge.rotation_euler = (math.radians(90), 0, 0)
    badge.data.materials.append(badge_mat)

    bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.12, location=(0, -0.1, 0), rotation=(math.radians(90), 0, 0))
    rim = bpy.context.active_object
    rim.data.materials.append(rim_mat)

    # 3D Text "VS"
    bpy.ops.object.text_add(location=(-0.62, -0.3, -0.38))
    txt = bpy.context.active_object
    txt.data.body = "VS"
    txt.data.size = 1.0
    txt.data.extrude = 0.25
    txt.data.bevel_depth = 0.04
    txt.rotation_euler = (math.radians(90), 0, 0)
    txt_mat = create_metallic_mat("VsText", (1.0, 0.95, 0.9, 1.0), roughness=0.1, metallic=0.9, emission=(1.0, 0.9, 0.8, 1.0), emission_strength=1.5)
    txt.data.materials.append(txt_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "vs_badge.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered vs_badge.png")

def render_swipe_arrows():
    # Left arrow
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.2)
    add_lights()

    cyan_mat = create_metallic_mat("CyanGlow", (0.1, 0.85, 1.0, 1.0), roughness=0.2, metallic=0.5, emission=(0.1, 0.85, 1.0, 1.0), emission_strength=3.0)

    # Arrow head (cone pointing left)
    bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0.0, depth=1.0, location=(-0.5, 0, 0))
    head = bpy.context.active_object
    head.rotation_euler = (0, math.radians(90), 0)
    head.data.materials.append(cyan_mat)

    # Arrow shaft (cube)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.4, 0, 0))
    shaft = bpy.context.active_object
    shaft.scale = (0.9, 0.25, 0.5)
    shaft.data.materials.append(cyan_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "swipe_left.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered swipe_left.png")

    # Right arrow
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.2)
    add_lights()

    purple_mat = create_metallic_mat("PurpleGlow", (0.9, 0.2, 1.0, 1.0), roughness=0.2, metallic=0.5, emission=(0.9, 0.2, 1.0, 1.0), emission_strength=3.0)

    bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0.0, depth=1.0, location=(0.5, 0, 0))
    head = bpy.context.active_object
    head.rotation_euler = (0, math.radians(-90), 0)
    head.data.materials.append(purple_mat)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.4, 0, 0))
    shaft = bpy.context.active_object
    shaft.scale = (0.9, 0.25, 0.5)
    shaft.data.materials.append(purple_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "swipe_right.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered swipe_right.png")

if __name__ == "__main__":
    render_trophy()
    render_flame()
    render_vs_badge()
    render_swipe_arrows()
    print("All 3D assets successfully rendered!")
