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

def add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.2):
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
    rim.data.color = (0.7, 0.9, 1.0)

def create_mat(name, color, roughness=0.15, metallic=0.7, emission=None, emission_strength=1.0):
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

def render_heart(is_empty=False):
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.0)
    add_lights()

    if is_empty:
        heart_mat = create_mat("EmptyHeart", (0.2, 0.22, 0.28, 1.0), roughness=0.5, metallic=0.3)
    else:
        heart_mat = create_mat("RubyHeart", (1.0, 0.1, 0.25, 1.0), roughness=0.12, metallic=0.4,
                               emission=(1.0, 0.05, 0.2, 1.0), emission_strength=2.2)

    # Left lobe
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=24, radius=0.65, location=(-0.38, 0, 0.22))
    s1 = bpy.context.active_object
    s1.scale = (1.0, 0.6, 1.0)
    s1.data.materials.append(heart_mat)

    # Right lobe
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=24, radius=0.65, location=(0.38, 0, 0.22))
    s2 = bpy.context.active_object
    s2.scale = (1.0, 0.6, 1.0)
    s2.data.materials.append(heart_mat)

    # Bottom tip (inverted cone)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.88, radius2=0.08, depth=1.45, location=(0, 0, -0.4))
    cone = bpy.context.active_object
    cone.rotation_euler = (0, 0, math.radians(180))
    cone.scale = (1.0, 0.6, 1.0)
    cone.data.materials.append(heart_mat)

    # Center fill
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=24, radius=0.72, location=(0, 0, 0.05))
    s3 = bpy.context.active_object
    s3.scale = (1.0, 0.6, 1.0)
    s3.data.materials.append(heart_mat)

    filename = "heart_empty.png" if is_empty else "heart.png"
    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, filename)
    bpy.ops.render.render(write_still=True)
    print("Rendered " + filename)

def render_play_icon():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.0)
    add_lights()

    play_mat = create_mat("PlayGreen", (0.1, 0.9, 0.45, 1.0), roughness=0.1, metallic=0.6,
                          emission=(0.1, 0.85, 0.4, 1.0), emission_strength=2.5)

    # Triangular prism pointing right
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=1.1, depth=0.45, location=(0.1, 0, 0))
    tri = bpy.context.active_object
    tri.rotation_euler = (math.radians(90), 0, math.radians(90))
    tri.data.materials.append(play_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "play_icon.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered play_icon.png")

def render_filter_icon():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.2)
    add_lights()

    filter_mat = create_mat("FilterCyan", (0.15, 0.75, 1.0, 1.0), roughness=0.15, metallic=0.7,
                            emission=(0.1, 0.65, 0.95, 1.0), emission_strength=2.2)

    # Top funnel (cone pointing down)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.2, radius2=0.35, depth=1.1, location=(0, 0, 0.35))
    funnel = bpy.context.active_object
    funnel.data.materials.append(filter_mat)

    # Bottom spout (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.35, depth=0.85, location=(0, 0, -0.6))
    spout = bpy.context.active_object
    spout.data.materials.append(filter_mat)

    # Top rim (torus)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.1, location=(0, 0, 0.9))
    rim = bpy.context.active_object
    rim.data.materials.append(filter_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "filter_icon.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered filter_icon.png")

def render_infinity_icon():
    clear_scene()
    setup_render((256, 256))
    add_camera(loc=(0, -4.5, 0), rot=(math.radians(90), 0, 0), ortho_scale=3.4)
    add_lights()

    gold_mat = create_mat("InfinityGold", (1.0, 0.75, 0.2, 1.0), roughness=0.15, metallic=0.85,
                          emission=(1.0, 0.7, 0.15, 1.0), emission_strength=2.0)

    # Left loop
    bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.2, location=(-0.58, 0, 0), rotation=(math.radians(90), 0, 0))
    loop1 = bpy.context.active_object
    loop1.data.materials.append(gold_mat)

    # Right loop
    bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.2, location=(0.58, 0, 0), rotation=(math.radians(90), 0, 0))
    loop2 = bpy.context.active_object
    loop2.data.materials.append(gold_mat)

    bpy.context.scene.render.filepath = os.path.join(OUTPUT_DIR, "infinity.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered infinity.png")

if __name__ == "__main__":
    render_heart(is_empty=False)
    render_heart(is_empty=True)
    render_play_icon()
    render_filter_icon()
    render_infinity_icon()
    print("Mobile UI 3D icons render completed successfully!")
