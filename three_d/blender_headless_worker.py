"""
Standalone Headless Blender 5.1 Procedural Architecture Builder.
Executed inside Blender's embedded Python interpreter:
blender.exe --background --python blender_headless_worker.py -- <input_plan.json> <output_blend> <output_png>
"""

import sys
import os
import json
import math

try:
    import bpy
    import bmesh
    from mathutils import Vector, Euler
except ImportError:
    pass  # Allow importing outside Blender for unit tests / inspection


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for col in bpy.data.collections:
        bpy.data.collections.remove(col)


def create_materials():
    mats = {}
    
    # Wall material (Matte white/sand plaster)
    mat_wall = bpy.data.materials.new(name="Mat_Wall")
    bsdf = mat_wall.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.90, 0.86, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
    mats["wall"] = mat_wall

    # Floor wood material
    mat_floor = bpy.data.materials.new(name="Mat_Floor")
    bsdf = mat_floor.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.65, 0.45, 0.28, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.40
    mats["floor"] = mat_floor

    # Glass material
    mat_glass = bpy.data.materials.new(name="Mat_Glass")
    bsdf = mat_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.90
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = 0.90
    mats["glass"] = mat_glass

    return mats


def build_3d_architecture(plan_data, output_blend, output_png):
    clear_scene()
    mats = create_materials()

    main_col = bpy.data.collections.new("ArchitecturalModel")
    bpy.context.scene.collection.children.link(main_col)

    wall_height = float(plan_data.get("metadata", {}).get("wall_height_m", 2.80))
    walls = plan_data.get("walls", [])
    openings = plan_data.get("openings", [])
    rooms = plan_data.get("rooms", [])

    # 1. Build Floor Slabs for each room
    for r in rooms:
        pts = r["polygon"]
        if len(pts) < 3:
            continue
        lvl = int(r.get("level_index", 0))
        base_z = lvl * (wall_height + 0.20)

        mesh = bpy.data.meshes.new(f"Floor_{r['room_id']}")
        bm = bmesh.new()
        v_list = []
        for pt in pts[:-1]:  # Exclude repeated end
            v_list.append(bm.verts.new((pt[0], pt[1], base_z)))
        bm.verts.ensure_lookup_table()
        if len(v_list) >= 3:
            try:
                face = bm.faces.new(v_list)
                # Extrude downwards by 0.15m for floor slab thickness
                bmesh.ops.extrude_face_region(bm, geom=[face])
                for v in bm.verts:
                    if abs(v.co.z - base_z) < 0.01:
                        v.co.z = base_z - 0.15
            except Exception:
                pass
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Obj_Floor_{r['room_id']}", mesh)
        obj.data.materials.append(mats["floor"])
        main_col.objects.link(obj)

    # 2. Build Walls
    wall_objs = []
    for w in walls:
        p1, p2 = w["centerline"]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx**2 + dy**2)
        if length < 0.01:
            continue
        thick = float(w.get("thickness_m", 0.20))
        angle = math.atan2(dy, dx)
        mid_x = (p1[0] + p2[0]) / 2.0
        mid_y = (p1[1] + p2[1]) / 2.0
        lvl = int(w.get("level_index", 0))
        base_z = lvl * (wall_height + 0.20)

        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(mid_x, mid_y, base_z + wall_height / 2.0),
            scale=(length, thick, wall_height),
            rotation=(0.0, 0.0, angle)
        )
        wall_obj = bpy.context.active_object
        wall_obj.name = f"Obj_{w['wall_id']}"
        wall_obj.data.materials.append(mats["wall"])
        # Move to main collection
        for col in wall_obj.users_collection:
            col.objects.unlink(wall_obj)
        main_col.objects.link(wall_obj)
        wall_objs.append(wall_obj)

    # 3. Apply Boolean Void Cutters for Doors and Windows
    for op in openings:
        op_type = op.get("opening_type", "door")
        pos = op["position"]
        width = float(op.get("width_m", 0.90))
        sill = float(op.get("sill_height_m", 0.0))
        h = float(op.get("height_m", 2.10)) if op_type == "door" else 1.20
        lvl = int(op.get("level_index", 0))
        base_z = lvl * (wall_height + 0.20)

        # Cutter box
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(pos[0], pos[1], base_z + sill + h / 2.0),
            scale=(width * 1.05, 0.60, h)
        )
        cutter = bpy.context.active_object
        cutter.name = f"Cutter_{op['opening_id']}"

        # Find intersecting walls and apply boolean difference
        for w_obj in wall_objs:
            # Check 3D distance
            dist_xy = math.sqrt((w_obj.location.x - pos[0])**2 + (w_obj.location.y - pos[1])**2)
            dist_z = abs(w_obj.location.z - (base_z + wall_height / 2.0))
            max_reach = max(w_obj.scale.x, w_obj.scale.y) / 2.0 + 1.0
            if dist_xy <= max_reach and dist_z < 0.5:
                mod = w_obj.modifiers.new(name=f"Bool_{op['opening_id']}", type='BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = cutter
                bpy.context.view_layer.objects.active = w_obj
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception:
                    pass

        # Delete cutter object
        bpy.data.objects.remove(cutter, do_unlink=True)

    # 4. Setup Lighting and Camera
    # Compute bounding center
    min_x, max_x = 0.0, 10.0
    min_y, max_y = 0.0, 10.0
    max_lvl = max([int(r.get("level_index", 0)) for r in rooms]) if rooms else 0
    total_height = (max_lvl + 1) * (wall_height + 0.20)

    if rooms:
        all_xs = [pt[0] for r in rooms for pt in r["polygon"]]
        all_ys = [pt[1] for r in rooms for pt in r["polygon"]]
        min_x, max_x = min(all_xs), max(all_xs)
        min_y, max_y = min(all_ys), max(all_ys)

    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_z = total_height / 2.0
    span = max(max_x - min_x, max_y - min_y, 10.0)

    # Sunlight
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    light_data.energy = 4.0
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    light_obj.location = (center_x - span, center_y - span, total_height + span)
    light_obj.rotation_euler = Euler((math.radians(50), math.radians(15), math.radians(-45)), 'XYZ')
    main_col.objects.link(light_obj)

    # Isometric Camera
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_data.type = 'PERSP'
    cam_data.lens = 32
    cam_obj = bpy.data.objects.new(name="Camera", object_data=cam_data)
    cam_obj.location = (center_x - span * 1.3, center_y - span * 1.5, total_height + span * 0.85)
    
    # Point camera at center
    dx = center_x - cam_obj.location.x
    dy = center_y - cam_obj.location.y
    dz = center_z - cam_obj.location.z
    dist_xy = math.sqrt(dx**2 + dy**2)
    pitch = math.atan2(dist_xy, -dz)
    yaw = math.atan2(dy, dx) - math.pi / 2.0
    cam_obj.rotation_euler = Euler((pitch, 0.0, yaw), 'XYZ')
    main_col.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # 5. Render Settings
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.render.resolution_x = 960
    bpy.context.scene.render.resolution_y = 720
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.filepath = output_png

    # Render image
    bpy.ops.render.render(write_still=True)

    # Save .blend
    os.makedirs(os.path.dirname(os.path.abspath(output_blend)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    print(f"[SUCCESS] Exported 3D model to {output_blend} and render to {output_png}")


if __name__ == "__main__":
    args = sys.argv
    if "--" in args:
        user_args = args[args.index("--") + 1:]
        if len(user_args) >= 3:
            plan_file, blend_path, png_path = user_args[0], user_args[1], user_args[2]
            with open(plan_file, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            build_3d_architecture(p_data, blend_path, png_path)
