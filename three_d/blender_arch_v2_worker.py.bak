"""
Parametric Multi-Scale & Multi-Style Procedural 3D Architecture Builder & Renderer.
Phase 3 of AI Architectural Floor Plan Pipeline.

Supports all 27 architectural styles:
Spanish Revival, Mid-Century Modern, Georgian, Tudor Revival, Greek Revival,
Victorian, Colonial, Saltbox, French Provincial, Prairie School, Modern,
Contemporary, Craftsman, Bungalow, Cottage, Ranch, Mediterranean Revival,
Gothic Revival, Art Deco, International Style, Farmhouse, Cabin, Chalet,
Mediterranean, Cape Cod, American Foursquare, Split-Level.

Usage (headless):
  blender.exe --background --python blender_arch_v2_worker.py -- <input_plan.json> <output.blend> <output_perspective.png>
"""

import sys, os, json, math

try:
    import bpy
    import bmesh
    from mathutils import Vector, Euler, Matrix
except ImportError:
    sys.exit("Must be run inside Blender's Python environment.")


# ---- UTILITIES --------------------------------------------------------------

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)


def get_or_make_collection(name, parent=None):
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        if parent is None:
            bpy.context.scene.collection.children.link(col)
        else:
            parent.children.link(col)
    return col


def link_to_col(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def make_pbr_mat(name, base_color, roughness=0.6, metallic=0.0,
                 transmission=0.0, ior=1.45):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf   = nodes.new("ShaderNodeBsdfPrincipled")
    output.location = (300, 0)
    bsdf.location   = (0, 0)
    bsdf.inputs["Base Color"].default_value  = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value   = roughness
    bsdf.inputs["Metallic"].default_value    = metallic
    bsdf.inputs["IOR"].default_value         = ior
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    mat.use_backface_culling = False
    return mat


def box_mesh(name, col, lx, ly, lz, sx, sy, sz, mat=None, rotation_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lx, ly, lz))
    obj = bpy.context.active_object
    obj.name  = name
    obj.scale = (max(0.01, sx), max(0.01, sy), max(0.01, sz))
    if rotation_z:
        obj.rotation_euler = Euler((0, 0, rotation_z), 'XYZ')
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    link_to_col(obj, col)
    return obj


def cylinder_mesh(name, col, lx, ly, lz, r, depth, mat=None, rot_x=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=(lx, ly, lz))
    obj = bpy.context.active_object
    obj.name = name
    if rot_x:
        obj.rotation_euler = Euler((rot_x, 0, 0), 'XYZ')
        bpy.ops.object.transform_apply(rotation=True)
    if mat:
        obj.data.materials.append(mat)
    link_to_col(obj, col)
    return obj


def create_hipped_roof(name, col, cx, cy, cz, width, depth, height, overhang, mat=None):
    """Creates a 4-sided pitched hipped roof with eaves."""
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    link_to_col(obj, col)

    hw = width / 2.0 + overhang
    hd = depth / 2.0 + overhang
    ridge_len = max(0.2, (depth - width) * 0.7) if depth > width else max(0.2, (width - depth) * 0.7)

    bm = bmesh.new()
    # Bottom 4 eave vertices
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new(( hw, -hd, 0))
    v2 = bm.verts.new(( hw,  hd, 0))
    v3 = bm.verts.new((-hw,  hd, 0))

    if depth >= width:
        hr = ridge_len / 2.0
        v_r1 = bm.verts.new((0, -hr, height))
        v_r2 = bm.verts.new((0,  hr, height))
        bm.faces.new((v0, v1, v_r1))
        bm.faces.new((v1, v2, v_r2, v_r1))
        bm.faces.new((v2, v3, v_r2))
        bm.faces.new((v3, v0, v_r1, v_r2))
    else:
        hr = ridge_len / 2.0
        v_r1 = bm.verts.new((-hr, 0, height))
        v_r2 = bm.verts.new(( hr, 0, height))
        bm.faces.new((v0, v1, v_r2, v_r1))
        bm.faces.new((v1, v2, v_r2))
        bm.faces.new((v2, v3, v_r1, v_r2))
        bm.faces.new((v3, v0, v_r1))

    # Bottom ceiling face
    bm.faces.new((v3, v2, v1, v0))

    bm.to_mesh(mesh)
    bm.free()
    obj.location = (cx, cy, cz)
    if mat:
        obj.data.materials.append(mat)
    return obj


def create_gable_roof(name, col, cx, cy, cz, width, depth, height, overhang, mat=None, axis="Y"):
    """Creates a 2-sided pitched gable roof."""
    mesh = bpy.data.meshes.new(name + "_GableMesh")
    obj = bpy.data.objects.new(name, mesh)
    link_to_col(obj, col)

    hw = width / 2.0 + overhang
    hd = depth / 2.0 + overhang

    bm = bmesh.new()
    if axis == "Y":
        # Ridge runs along Y axis
        v0 = bm.verts.new((-hw, -hd, 0))
        v1 = bm.verts.new(( hw, -hd, 0))
        v2 = bm.verts.new(( hw,  hd, 0))
        v3 = bm.verts.new((-hw,  hd, 0))
        vr1 = bm.verts.new((0, -hd, height))
        vr2 = bm.verts.new((0,  hd, height))

        bm.faces.new((v0, vr1, v1))          # Front gable end
        bm.faces.new((v1, vr1, vr2, v2))     # Right slope
        bm.faces.new((v2, vr2, v3))          # Rear gable end
        bm.faces.new((v3, vr2, vr1, v0))     # Left slope
        bm.faces.new((v3, v2, v1, v0))       # Bottom
    else:
        # Ridge runs along X axis
        v0 = bm.verts.new((-hw, -hd, 0))
        v1 = bm.verts.new(( hw, -hd, 0))
        v2 = bm.verts.new(( hw,  hd, 0))
        v3 = bm.verts.new((-hw,  hd, 0))
        vr1 = bm.verts.new((-hw, 0, height))
        vr2 = bm.verts.new(( hw, 0, height))

        bm.faces.new((v0, v1, vr2, vr1))     # Front slope
        bm.faces.new((v1, v2, vr2))          # Right gable end
        bm.faces.new((v2, v3, vr1, vr2))     # Rear slope
        bm.faces.new((v3, v0, vr1))          # Left gable end
        bm.faces.new((v3, v2, v1, v0))       # Bottom

    bm.to_mesh(mesh)
    bm.free()
    obj.location = (cx, cy, cz)
def create_cone_roof(name, col, cx, cy, cz, radius, height, mat=None, segments=16):
    """Creates a conical turret spire roof (Victorian / Queen Anne)."""
    mesh = bpy.data.meshes.new(name + "_ConeMesh")
    obj = bpy.data.objects.new(name, mesh)
    link_to_col(obj, col)
    bm = bmesh.new()
    tip = bm.verts.new((0, 0, height))
    base_verts = []
    for i in range(segments):
        th = 2.0 * math.pi * i / segments
        x = radius * math.cos(th)
        y = radius * math.sin(th)
        base_verts.append(bm.verts.new((x, y, 0)))
    for i in range(segments):
        v1 = base_verts[i]
        v2 = base_verts[(i + 1) % segments]
        bm.faces.new((v1, v2, tip))
    bm.faces.new(reversed(base_verts))
    bm.to_mesh(mesh)
    bm.free()
    obj.location = (cx, cy, cz)
    if mat:
        obj.data.materials.append(mat)
    return obj


def create_saltbox_roof(name, col, cx, cy, cz, width, depth, height, overhang, mat=None):
    """Creates an authentic asymmetrical Saltbox roof with short front pitch and long rear catslide pitch."""
    mesh = bpy.data.meshes.new(name + "_SaltboxMesh")
    obj = bpy.data.objects.new(name, mesh)
    link_to_col(obj, col)
    hw = width / 2.0 + overhang
    hd = depth / 2.0 + overhang
    bm = bmesh.new()
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new(( hw, -hd, 0))
    v2 = bm.verts.new(( hw,  hd, -height * 0.40))
    v3 = bm.verts.new((-hw,  hd, -height * 0.40))
    ridge_y = -hd * 0.30
    vr1 = bm.verts.new((-hw, ridge_y, height))
    vr2 = bm.verts.new(( hw, ridge_y, height))
    bm.faces.new((v0, v1, vr2, vr1))      # Short steep front slope
    bm.faces.new((vr1, vr2, v2, v3))      # Long sloping rear catslide
    bm.faces.new((v0, vr1, v3))           # Left gable wall
    bm.faces.new((v1, v2, vr2))           # Right gable wall
    bm.to_mesh(mesh)
    bm.free()
    obj.location = (cx, cy, cz)
    if mat:
        obj.data.materials.append(mat)
    return obj


# ---- MAIN BUILDER -----------------------------------------------------------

def build_architecture(plan_data, output_blend, output_png):
    clear_scene()

    # Collections
    root_col  = get_or_make_collection("ArchitecturalModel")
    col_site  = get_or_make_collection("Site",             root_col)
    col_slab  = get_or_make_collection("Slabs",            root_col)
    col_walls = get_or_make_collection("Walls",            root_col)
    col_glaz  = get_or_make_collection("Openings_Glazing", root_col)
    col_roof  = get_or_make_collection("Roof_System",      root_col)
    col_fac   = get_or_make_collection("Facade_Accents",   root_col)
    col_cam   = get_or_make_collection("Cameras_Lights",   root_col)

    meta  = plan_data.get("metadata", {})
    prov  = meta.get("provenance", {})

    # Detect Plan Bounds
    boundary = plan_data.get("boundary", [])
    if boundary and len(boundary) >= 3:
        xs = [pt[0] for pt in boundary]
        ys = [pt[1] for pt in boundary]
        W = max(xs) - min(xs)
        D = max(ys) - min(ys)
    else:
        W = float(prov.get("width_m", 10.67))
        D = float(prov.get("depth_m", 19.81))

    H_GF = float(meta.get("wall_height_m", 3.00))
    floors_count = int(meta.get("floor_count", 2))
    H_1F = H_GF if floors_count > 1 else 0.0

    PLINTH = 0.45
    SLAB_T = 0.20
    PAR_H  = 1.00
    PAR_T  = 0.23
    COP_H  = 0.08
    ext_T  = 0.23

    # Detect Architectural Style Parameters
    style_slug = prov.get("architectural_style", prov.get("style", "Modern")).lower()
    is_spanish = any(k in style_slug for k in ["spanish", "mediterranean", "mission", "tuscan"])
    is_greek = any(k in style_slug for k in ["greek", "neoclassical", "temple"])
    is_victorian = any(k in style_slug for k in ["victorian", "queen anne", "gothic revival"])
    is_tudor = any(k in style_slug for k in ["tudor", "gothic"]) and not is_victorian
    is_georgian = any(k in style_slug for k in ["georgian", "colonial", "foursquare"]) and not is_greek
    is_saltbox = any(k in style_slug for k in ["saltbox", "cape cod"])
    is_french = any(k in style_slug for k in ["french", "chateau", "provincial"])
    is_prairie = any(k in style_slug for k in ["prairie", "wright"])
    is_craftsman = any(k in style_slug for k in ["craftsman", "bungalow", "cottage"]) and not is_prairie
    is_farmhouse = any(k in style_slug for k in ["farmhouse", "ranch"])
    is_chalet = any(k in style_slug for k in ["chalet", "cabin", "alpine"])
    is_art_deco = any(k in style_slug for k in ["art deco", "deco", "streamline"])
    is_mid_century = any(k in style_slug for k in ["mid-century", "mid century", "mcm"])
    is_split_level = any(k in style_slug for k in ["split level", "split-level", "tri-level"])

    # PBR Materials customized by Architectural Style
    if is_spanish:
        m_wall = make_pbr_mat("M_SpanishStucco", (0.93, 0.89, 0.82), roughness=0.82)
        m_roof = make_pbr_mat("M_TerracottaTile", (0.76, 0.28, 0.14), roughness=0.55)
        m_accent = make_pbr_mat("M_TerracottaTrim", (0.68, 0.26, 0.15), roughness=0.65)
        m_metal = make_pbr_mat("M_WroughtIron", (0.10, 0.08, 0.06), roughness=0.35, metallic=0.85)
        m_wood = make_pbr_mat("M_DarkWoodLintel", (0.28, 0.18, 0.12), roughness=0.60)
        roof_style = "terracotta"
    elif is_greek:
        m_wall = make_pbr_mat("M_GreekWhiteStone", (0.96, 0.95, 0.94), roughness=0.45)
        m_roof = make_pbr_mat("M_GreekSlateTile", (0.28, 0.30, 0.32), roughness=0.60)
        m_accent = make_pbr_mat("M_GreekPedimentMarble", (0.92, 0.91, 0.89), roughness=0.40)
        m_metal = make_pbr_mat("M_BronzeHardware", (0.35, 0.28, 0.18), roughness=0.35, metallic=0.80)
        m_wood = make_pbr_mat("M_ClassicalDoorWood", (0.25, 0.14, 0.08), roughness=0.50)
        roof_style = "greek_pediment"
    elif is_victorian:
        m_wall = make_pbr_mat("M_VictorianClapboard", (0.86, 0.82, 0.74), roughness=0.70)
        m_roof = make_pbr_mat("M_VictorianSlateSpire", (0.18, 0.20, 0.24), roughness=0.55)
        m_accent = make_pbr_mat("M_GingerbreadTrim", (0.95, 0.93, 0.88), roughness=0.40)
        m_metal = make_pbr_mat("M_OrnamentalCrestIron", (0.08, 0.08, 0.08), roughness=0.30, metallic=0.85)
        m_wood = make_pbr_mat("M_CarvedSpindleWood", (0.40, 0.25, 0.16), roughness=0.60)
        roof_style = "victorian_turret"
    elif is_tudor:
        m_wall = make_pbr_mat("M_TudorPlaster", (0.92, 0.90, 0.84), roughness=0.80)
        m_roof = make_pbr_mat("M_SlateShingle", (0.20, 0.21, 0.23), roughness=0.60)
        m_accent = make_pbr_mat("M_HalfTimberOak", (0.22, 0.14, 0.09), roughness=0.70)
        m_metal = make_pbr_mat("M_BlackIron", (0.08, 0.08, 0.08), roughness=0.30, metallic=0.90)
        m_wood = make_pbr_mat("M_DarkOakBeams", (0.20, 0.13, 0.08), roughness=0.65)
        roof_style = "steep_gable"
    elif is_saltbox:
        m_wall = make_pbr_mat("M_SaltboxClapboard", (0.84, 0.82, 0.78), roughness=0.75)
        m_roof = make_pbr_mat("M_WeatheredShingle", (0.22, 0.23, 0.25), roughness=0.65)
        m_accent = make_pbr_mat("M_BrickCentralChimney", (0.60, 0.24, 0.18), roughness=0.85)
        m_metal = make_pbr_mat("M_BlackHinges", (0.10, 0.10, 0.10), roughness=0.35, metallic=0.80)
        m_wood = make_pbr_mat("M_PineCornerBoards", (0.90, 0.88, 0.85), roughness=0.50)
        roof_style = "saltbox_catslide"
    elif is_french:
        m_wall = make_pbr_mat("M_FrenchStoneQuoins", (0.90, 0.88, 0.84), roughness=0.60)
        m_roof = make_pbr_mat("M_FrenchMansardSlate", (0.20, 0.22, 0.26), roughness=0.50)
        m_accent = make_pbr_mat("M_CarvedLimestoneQuoin", (0.94, 0.93, 0.90), roughness=0.55)
        m_metal = make_pbr_mat("M_FrenchWroughtIron", (0.12, 0.10, 0.10), roughness=0.30, metallic=0.85)
        m_wood = make_pbr_mat("M_FrenchCasementWood", (0.92, 0.92, 0.90), roughness=0.45)
        roof_style = "french_mansard"
    elif is_prairie:
        m_wall = make_pbr_mat("M_PrairieRomanBrick", (0.72, 0.44, 0.32), roughness=0.80)
        m_roof = make_pbr_mat("M_PrairieFlatShingle", (0.24, 0.22, 0.20), roughness=0.60)
        m_accent = make_pbr_mat("M_CantileverFascia", (0.35, 0.25, 0.18), roughness=0.65)
        m_metal = make_pbr_mat("M_BronzeSash", (0.22, 0.18, 0.14), roughness=0.35, metallic=0.75)
        m_wood = make_pbr_mat("M_OakBands", (0.45, 0.30, 0.18), roughness=0.55)
        roof_style = "low_pitch_overhang"
    elif is_georgian:
        m_wall = make_pbr_mat("M_FacingBrick", (0.64, 0.25, 0.18), roughness=0.85)
        m_roof = make_pbr_mat("M_GeorgianSlate", (0.24, 0.26, 0.28), roughness=0.60)
        m_accent = make_pbr_mat("M_WhiteQuoinStone", (0.94, 0.93, 0.90), roughness=0.50)
        m_metal = make_pbr_mat("M_BlackSashMetal", (0.10, 0.10, 0.10), roughness=0.30, metallic=0.80)
        m_wood = make_pbr_mat("M_WhiteTrim", (0.96, 0.96, 0.95), roughness=0.40)
        roof_style = "hipped"
    elif is_craftsman:
        m_wall = make_pbr_mat("M_CraftsmanSiding", (0.74, 0.68, 0.58), roughness=0.80)
        m_roof = make_pbr_mat("M_ArchitecturalShingle", (0.28, 0.26, 0.24), roughness=0.70)
        m_accent = make_pbr_mat("M_RiverStonePier", (0.48, 0.44, 0.40), roughness=0.90)
        m_metal = make_pbr_mat("M_DarkBronze", (0.20, 0.16, 0.12), roughness=0.40, metallic=0.75)
        m_wood = make_pbr_mat("M_CedarTrim", (0.45, 0.30, 0.18), roughness=0.55)
        roof_style = "low_pitch_overhang"
    elif is_farmhouse:
        m_wall = make_pbr_mat("M_BoardAndBatten", (0.96, 0.96, 0.95), roughness=0.70)
        m_roof = make_pbr_mat("M_BlackMetalSeam", (0.12, 0.13, 0.14), roughness=0.35, metallic=0.65)
        m_accent = make_pbr_mat("M_CharcoalAccent", (0.20, 0.22, 0.24), roughness=0.50)
        m_metal = make_pbr_mat("M_BlackSteel", (0.08, 0.08, 0.08), roughness=0.25, metallic=0.85)
        m_wood = make_pbr_mat("M_NaturalCedarPosts", (0.55, 0.38, 0.22), roughness=0.75)
        roof_style = "metal_gable"
    elif is_chalet:
        m_wall = make_pbr_mat("M_TimberLogWood", (0.52, 0.36, 0.22), roughness=0.85)
        m_roof = make_pbr_mat("M_ChaletHeavyGable", (0.25, 0.22, 0.18), roughness=0.70)
        m_accent = make_pbr_mat("M_RusticFieldstoneBase", (0.45, 0.42, 0.38), roughness=0.90)
        m_metal = make_pbr_mat("M_WroughtIronHardware", (0.12, 0.10, 0.08), roughness=0.40, metallic=0.80)
        m_wood = make_pbr_mat("M_CarvedAlpineBalcony", (0.60, 0.42, 0.26), roughness=0.65)
        roof_style = "low_pitch_overhang"
    elif is_art_deco:
        m_wall = make_pbr_mat("M_LimestoneDeco", (0.92, 0.91, 0.88), roughness=0.55)
        m_roof = make_pbr_mat("M_FlatDecoParapet", (0.18, 0.20, 0.22), roughness=0.50)
        m_accent = make_pbr_mat("M_BrassGeometric", (0.72, 0.58, 0.32), roughness=0.30, metallic=0.75)
        m_metal = make_pbr_mat("M_BrassGold", (0.68, 0.54, 0.28), roughness=0.25, metallic=0.80)
        m_wood = make_pbr_mat("M_PolishedWalnut", (0.35, 0.20, 0.12), roughness=0.35)
        roof_style = "stepped_parapet"
    elif is_mid_century:
        m_wall = make_pbr_mat("M_MCMFieldstone", (0.88, 0.86, 0.82), roughness=0.75)
        m_roof = make_pbr_mat("M_MCMFlatCantilever", (0.15, 0.16, 0.18), roughness=0.50)
        m_accent = make_pbr_mat("M_StackedFieldstone", (0.42, 0.35, 0.28), roughness=0.85)
        m_metal = make_pbr_mat("M_SlenderBlackSteel", (0.08, 0.08, 0.09), roughness=0.25, metallic=0.90)
        m_wood = make_pbr_mat("M_TeakPostBeam", (0.50, 0.32, 0.18), roughness=0.50)
        roof_style = "modern_flat"
    elif is_split_level:
        m_wall = make_pbr_mat("M_SplitLevelSiding", (0.85, 0.83, 0.80), roughness=0.75)
        m_roof = make_pbr_mat("M_SplitLevelShingle", (0.22, 0.24, 0.26), roughness=0.60)
        m_accent = make_pbr_mat("M_LowerLevelBrick", (0.50, 0.32, 0.22), roughness=0.80)
        m_metal = make_pbr_mat("M_SplitLevelBronze", (0.15, 0.14, 0.12), roughness=0.35, metallic=0.70)
        m_wood = make_pbr_mat("M_SplitLevelTrim", (0.90, 0.88, 0.85), roughness=0.45)
        roof_style = "low_pitch_overhang"
    else: # Modern / Contemporary / International Style
        m_wall = make_pbr_mat("M_ModernStucco", (0.94, 0.94, 0.94), roughness=0.60)
        m_roof = make_pbr_mat("M_FlatRoof", (0.15, 0.16, 0.18), roughness=0.50)
        m_accent = make_pbr_mat("M_CharcoalPanel", (0.18, 0.20, 0.22), roughness=0.40, metallic=0.30)
        m_metal = make_pbr_mat("M_DarkMetal", (0.06, 0.065, 0.07), roughness=0.25, metallic=0.90)
        m_wood = make_pbr_mat("M_OakLouvres", (0.58, 0.36, 0.18), roughness=0.50)
        roof_style = "modern_flat"

    m_concrete = make_pbr_mat("M_Concrete", (0.72, 0.71, 0.70), roughness=0.85)
    m_glass    = make_pbr_mat("M_TintedGlass", (0.82, 0.92, 0.96), roughness=0.04, transmission=0.90, ior=1.52)
    m_grass    = make_pbr_mat("M_GrassLawn", (0.14, 0.44, 0.12), roughness=0.95)
    m_paver    = make_pbr_mat("M_PaverDriveway", (0.35, 0.34, 0.33), roughness=0.88)
    m_balus    = make_pbr_mat("M_Balustrade", (0.85, 0.94, 0.98), roughness=0.02, transmission=0.80, ior=1.52)
    m_water    = make_pbr_mat("M_Water", (0.20, 0.62, 0.82), roughness=0.05, metallic=0.30)

    # Elevation Z coordinates
    Z_PLINTH   = PLINTH
    Z_1F_slab  = Z_PLINTH + H_GF
    Z_1F_walls = Z_1F_slab + SLAB_T
    Z_RF_slab  = Z_1F_walls + H_1F
    par_base   = Z_RF_slab + SLAB_T

    # 1. Site Ground & Landscaping (Front Lawn + Driveway + Side Setbacks)
    site_w = W + 6.0
    site_d = D + 8.0
    box_mesh("SITE_Grass_Ground", col_site, W/2, D/2 - 2.0, -0.12, site_w, site_d, 0.24, m_grass)

    # Driveway / Car Porch Paving (Left bay leading from front gate to porch)
    porch_w = min(4.5, W * 0.45)
    porch_d = min(5.5, D * 0.32)
    box_mesh("SITE_Paver_Driveway", col_site, porch_w/2 + 0.3, porch_d/2, 0.02, porch_w, porch_d + 2.0, 0.04, m_paver)

    # Pedestrian Walkway to Front Entrance
    walk_w = 1.20
    walk_x = porch_w + 1.2
    box_mesh("SITE_Walkway", col_site, walk_x, porch_d * 0.4, 0.025, walk_w, porch_d * 0.8, 0.04, m_concrete)

    # Front Boundary Wall with Gate Piers
    wall_h = 1.60
    box_mesh("SITE_Boundary_Front_L", col_site, 0.4, -1.8, wall_h/2, 0.8, 0.23, wall_h, m_wall)
    box_mesh("SITE_Boundary_Front_R", col_site, W - 0.4, -1.8, wall_h/2, 0.8, 0.23, wall_h, m_wall)
    box_mesh("SITE_Gate_Pier_L", col_site, 0.15, -1.8, (wall_h + 0.3)/2, 0.45, 0.45, wall_h + 0.3, m_accent)
    box_mesh("SITE_Gate_Pier_R", col_site, porch_w + 0.6, -1.8, (wall_h + 0.3)/2, 0.45, 0.45, wall_h + 0.3, m_accent)

    # 2. Plinth & Ground Floor Slab
    box_mesh("Plinth", col_slab, W/2, D/2, Z_PLINTH/2, W, D, Z_PLINTH, m_concrete)
    box_mesh("Slab_GF", col_slab, W/2, D/2, Z_PLINTH - 0.05, W, D, 0.15, m_concrete)

    # 3. Ground Floor Walls
    box_mesh("GF_Wall_Left",  col_walls, ext_T/2, D/2, Z_PLINTH + H_GF/2, ext_T, D, H_GF, m_wall)
    box_mesh("GF_Wall_Right", col_walls, W - ext_T/2, D/2, Z_PLINTH + H_GF/2, ext_T, D, H_GF, m_wall)
    box_mesh("GF_Wall_Rear",  col_walls, W/2, D - ext_T/2, Z_PLINTH + H_GF/2, W, ext_T, H_GF, m_wall)

    # Front Facade Ground Wall (Right bay living/drawing room)
    front_r_w = max(2.5, W - porch_w - 0.3)
    front_r_cx = porch_w + 0.3 + front_r_w / 2.0
    box_mesh("GF_Wall_FrontRight", col_walls, front_r_cx, ext_T/2, Z_PLINTH + H_GF/2, front_r_w, ext_T, H_GF, m_wall)

    # Porch Columns / Arches matching Style
    if is_spanish:
        # Authentic Spanish Arched Arcade for Porch
        col_w = 0.40
        box_mesh("GF_SpanishArcade_Col1", col_fac, 0.30, ext_T/2, Z_PLINTH + H_GF/2, col_w, col_w, H_GF, m_wall)
        box_mesh("GF_SpanishArcade_Col2", col_fac, porch_w - 0.20, ext_T/2, Z_PLINTH + H_GF/2, col_w, col_w, H_GF, m_wall)
        # Arch spandrel lintel
        box_mesh("GF_SpanishArcade_Arch", col_fac, porch_w/2, ext_T/2, Z_PLINTH + H_GF - 0.40, porch_w, ext_T * 1.2, 0.80, m_accent)
    elif is_greek or is_georgian:
        # Classical Fluted Portico Columns
        cylinder_mesh("GF_ColPortico_L", col_fac, porch_w * 0.3, ext_T/2, Z_PLINTH + H_GF/2, 0.18, H_GF, m_accent)
        cylinder_mesh("GF_ColPortico_R", col_fac, porch_w * 0.8, ext_T/2, Z_PLINTH + H_GF/2, 0.18, H_GF, m_accent)
    elif is_craftsman or is_prairie:
        # Tapered square columns on heavy stone piers
        box_mesh("GF_CraftsmanPier_L", col_fac, 0.35, ext_T/2, Z_PLINTH + 0.50, 0.55, 0.55, 1.00, m_accent)
        box_mesh("GF_CraftsmanCol_L",  col_fac, 0.35, ext_T/2, Z_PLINTH + 1.0 + (H_GF-1.0)/2, 0.32, 0.32, H_GF - 1.0, m_wood)
        box_mesh("GF_CraftsmanPier_R", col_fac, porch_w - 0.30, ext_T/2, Z_PLINTH + 0.50, 0.55, 0.55, 1.00, m_accent)
        box_mesh("GF_CraftsmanCol_R",  col_fac, porch_w - 0.30, ext_T/2, Z_PLINTH + 1.0 + (H_GF-1.0)/2, 0.32, 0.32, H_GF - 1.0, m_wood)
    elif is_farmhouse or is_chalet:
        # Square timber posts
        box_mesh("GF_FarmhousePost_L", col_fac, 0.25, ext_T/2, Z_PLINTH + H_GF/2, 0.22, 0.22, H_GF, m_wood)
        box_mesh("GF_FarmhousePost_R", col_fac, porch_w - 0.25, ext_T/2, Z_PLINTH + H_GF/2, 0.22, 0.22, H_GF, m_wood)
    elif is_mid_century:
        # Slender black steel posts
        cylinder_mesh("GF_MCM_Post_L", col_fac, 0.30, ext_T/2, Z_PLINTH + H_GF/2, 0.08, H_GF, m_metal)
        cylinder_mesh("GF_MCM_Post_R", col_fac, porch_w - 0.20, ext_T/2, Z_PLINTH + H_GF/2, 0.08, H_GF, m_metal)
    else:
        # Modern / Contemporary Sleek Piers
        box_mesh("GF_PorchCol_1", col_fac, 0.30, ext_T/2, Z_PLINTH + H_GF/2, 0.30, 0.30, H_GF, m_accent)
        box_mesh("GF_PorchCol_2", col_fac, porch_w - 0.20, ext_T/2, Z_PLINTH + H_GF/2, 0.30, 0.30, H_GF, m_accent)

    # Ground Floor Glazing / Windows
    gl_h = H_GF - 0.60
    gl_w = min(3.5, front_r_w * 0.70)
    box_mesh("GL_GF_Drawing", col_glaz, front_r_cx, ext_T * 0.5, Z_PLINTH + 0.20 + gl_h/2,
             gl_w, 0.06, gl_h, m_glass)
    # Mullions & transom
    box_mesh("GL_Transom_GF", col_glaz, front_r_cx, ext_T * 0.5, Z_PLINTH + H_GF * 0.65,
             gl_w + 0.10, 0.08, 0.06, m_metal)

    # 4. Upper Floor Structure (Level 1)
    if floors_count > 1:
        # First floor slab
        box_mesh("Slab_1F", col_slab, W/2, D/2, Z_1F_slab + SLAB_T/2, W, D, SLAB_T, m_concrete)

        # Cantilevered front terrace / balcony slab over porch
        bal_w = porch_w + 0.4
        box_mesh("Slab_Balcony", col_slab, bal_w/2, porch_d/2, Z_1F_slab + SLAB_T/2, bal_w, porch_d, SLAB_T, m_concrete)

        # First floor walls
        box_mesh("FF_Wall_Left",  col_walls, ext_T/2, D/2, Z_1F_walls + H_1F/2, ext_T, D, H_1F, m_wall)
        box_mesh("FF_Wall_Right", col_walls, W - ext_T/2, D/2, Z_1F_walls + H_1F/2, ext_T, D, H_1F, m_wall)
        box_mesh("FF_Wall_Rear",  col_walls, W/2, D - ext_T/2, Z_1F_walls + H_1F/2, W, ext_T, H_1F, m_wall)

        # First floor front master suite wall
        ff_r_w = W - bal_w
        ff_r_cx = bal_w + ff_r_w/2.0
        box_mesh("FF_Wall_FrontRight", col_walls, ff_r_cx, ext_T/2, Z_1F_walls + H_1F/2, ff_r_w, ext_T, H_1F, m_wall)

        # FF Suite Glazing
        ff_gl_w = min(3.2, ff_r_w * 0.70)
        box_mesh("GL_FF_MasterSuite", col_glaz, ff_r_cx, ext_T * 0.5, Z_1F_walls + 0.20 + gl_h/2,
                 ff_gl_w, 0.06, gl_h, m_glass)

        # Balcony Balustrade matching Style
        bal_z = Z_1F_walls + 0.50
        if is_spanish or is_french:
            # Wrought iron curved grill balustrade
            box_mesh("BAL_Front_Iron", col_fac, bal_w/2, 0.10, bal_z, bal_w, 0.06, 1.00, m_metal)
            box_mesh("BAL_Side_Iron",  col_fac, bal_w - 0.05, porch_d/2, bal_z, 0.06, porch_d, 1.00, m_metal)
        elif is_craftsman or is_farmhouse or is_chalet or is_victorian:
            # Timber spindle baluster railing
            box_mesh("BAL_Front_Wood", col_fac, bal_w/2, 0.10, bal_z, bal_w, 0.08, 1.00, m_wood)
            box_mesh("BAL_Side_Wood",  col_fac, bal_w - 0.05, porch_d/2, bal_z, 0.08, porch_d, 1.00, m_wood)
        else:
            # Frameless glass balustrade with metallic handrail
            box_mesh("BAL_Front_Glass", col_fac, bal_w/2, 0.10, bal_z, bal_w, 0.03, 1.05, m_balus)
            box_mesh("BAL_Side_Glass",  col_fac, bal_w - 0.05, porch_d/2, bal_z, 0.03, porch_d, 1.05, m_balus)
            box_mesh("BAL_Handrail_F",  col_fac, bal_w/2, 0.10, Z_1F_walls + 1.08, bal_w + 0.05, 0.05, 0.04, m_metal)

        # Accent elements (Oak louvres for Modern, Stone cladding for Mid-Century, Half-timber for Tudor)
        if is_tudor:
            # Decorative half-timber beams on first floor facade
            box_mesh("TUDOR_Beam_Horiz", col_fac, ff_r_cx, ext_T/2 - 0.02, Z_1F_walls + H_1F * 0.5, ff_r_w, 0.05, 0.15, m_accent)
            for bx in [ff_r_cx - 1.2, ff_r_cx, ff_r_cx + 1.2]:
                box_mesh(f"TUDOR_Beam_Vert_{int(bx*10)}", col_fac, bx, ext_T/2 - 0.02, Z_1F_walls + H_1F/2, 0.12, 0.05, H_1F, m_accent)
        elif is_greek:
            # Classical Frieze and Entablature Band
            box_mesh("GREEK_Entablature", col_fac, W/2, ext_T/2 - 0.04, Z_1F_walls + H_1F - 0.20, W + 0.20, ext_T + 0.10, 0.40, m_accent)
        elif is_victorian:
            # Victorian Queen Anne Turret on front corner
            turret_r = 1.30
            cylinder_mesh("VICTORIAN_Turret_1F", col_fac, bal_w + turret_r, ext_T * 0.6, Z_1F_walls + H_1F/2, turret_r, H_1F, m_accent)
        elif not is_spanish and not is_georgian and not is_saltbox:
            # Vertical louvre accent screen
            lou_h = 1.00
            for lx in [bal_w + 0.35, bal_w + 0.65, bal_w + 0.95]:
                box_mesh(f"ACC_Louvre_{int(lx*10)}", col_fac, lx, ext_T/2 - 0.03, Z_1F_walls + H_1F - lou_h/2, 0.06, 0.10, lou_h, m_wood)

    # 5. Roof System procedural modeling based on Architectural Style
    roof_z_base = par_base

    if roof_style == "terracotta":
        # Spanish / Mediterranean low-pitch terracotta hipped roof
        roof_h = max(1.4, min(2.5, W * 0.22))
        create_hipped_roof("ROOF_Spanish_Terracotta", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.55, mat=m_roof)
        # Ridge caps & hip tile accents
        box_mesh("ROOF_Spanish_Ridge", col_roof, W/2, D/2, roof_z_base + roof_h + 0.05, 0.25, max(1.0, D * 0.4), 0.12, m_accent)
        # Timber rafter tails under eaves
        for rx in range(1, int(W), 2):
            box_mesh(f"ROOF_Rafter_{rx}", col_roof, rx, 0.10, roof_z_base - 0.10, 0.10, 0.50, 0.10, m_wood)

    elif roof_style == "greek_pediment":
        # Greek Revival Monumental Classical Pediment Gable
        roof_h = max(2.0, W * 0.32)
        create_gable_roof("ROOF_Greek_Pediment", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.35, mat=m_roof, axis="Y")
        # Triangular Pediment Tympanum Facade Block
        box_mesh("ROOF_Greek_Tympanum", col_roof, W/2, 0.10, roof_z_base + roof_h * 0.35, W * 0.85, 0.15, roof_h * 0.70, m_accent)

    elif roof_style == "victorian_turret":
        # Victorian Multi-faceted Gable + Conical Spire Turret
        roof_h = max(2.6, W * 0.42)
        create_gable_roof("ROOF_Victorian_Gable", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.45, mat=m_roof, axis="Y")
        # Conical Turret Spire
        turret_r = 1.45
        create_cone_roof("ROOF_Victorian_ConicalSpire", col_roof, bal_w + turret_r, 0.10, roof_z_base, turret_r, roof_h * 1.35, mat=m_roof)

    elif roof_style == "saltbox_catslide":
        # Saltbox Asymmetrical Long Rear Catslide Roof
        roof_h = max(2.4, W * 0.38)
        create_saltbox_roof("ROOF_Saltbox_Catslide", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.40, mat=m_roof)
        # Central Massive Chimney
        box_mesh("ROOF_Saltbox_Chimney", col_roof, W/2, D * 0.35, roof_z_base + roof_h * 0.8, 0.90, 0.90, roof_h * 1.3, m_accent)

    elif roof_style == "french_mansard":
        # French Provincial High-Pitched Steep Hip / Mansard Roof
        roof_h = max(2.6, W * 0.40)
        create_hipped_roof("ROOF_French_Mansard", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.30, mat=m_roof)
        # Arched Wall Dormers piercing eaves
        for dx in [W * 0.30, W * 0.70]:
            box_mesh(f"ROOF_FrenchDormer_{int(dx*10)}", col_roof, dx, 0.20, roof_z_base + roof_h * 0.40, 1.20, 1.40, 1.50, m_accent)

    elif roof_style == "steep_gable":
        # Tudor / Gothic steep cross-gable slate roof
        roof_h = max(2.8, W * 0.45)
        create_gable_roof("ROOF_Tudor_Gable", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.40, mat=m_roof, axis="Y")
        # Prominent brick exterior chimney
        box_mesh("ROOF_Tudor_Chimney", col_roof, W - 0.60, D * 0.40, roof_z_base + roof_h * 0.7, 0.85, 0.85, roof_h * 1.2, m_accent)

    elif roof_style == "hipped":
        # Georgian / Colonial classical 32° hipped slate roof with white dentil cornice
        roof_h = max(1.8, W * 0.30)
        create_hipped_roof("ROOF_Georgian_Hipped", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.35, mat=m_roof)
        # Dentil Cornice Band
        box_mesh("ROOF_Dentil_Cornice", col_roof, W/2, D/2, roof_z_base - 0.05, W + 0.30, D + 0.30, 0.18, m_accent)

    elif roof_style == "low_pitch_overhang":
        # Craftsman / Prairie low-pitch roof with deep cantilevered overhangs
        roof_h = max(1.1, W * 0.16)
        create_hipped_roof("ROOF_Craftsman_LowPitch", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.85, mat=m_roof)
        # Deep horizontal fascia band
        box_mesh("ROOF_Craftsman_Fascia", col_roof, W/2, D/2, roof_z_base - 0.02, W + 1.75, D + 1.75, 0.14, m_wood)

    elif roof_style == "metal_gable":
        # Farmhouse standing seam metal gable roof
        roof_h = max(2.2, W * 0.35)
        create_gable_roof("ROOF_Farmhouse_Metal", col_roof, W/2, D/2, roof_z_base, W, D, roof_h, overhang=0.45, mat=m_roof, axis="Y")

    elif roof_style == "stepped_parapet":
        # Art Deco Stepped Ziggurat parapet levels
        box_mesh("ROOF_Deco_Step1", col_roof, W/2, D/2, roof_z_base + 0.40, W, D, 0.80, m_wall)
        box_mesh("ROOF_Deco_Step2", col_roof, W/2, D/2, roof_z_base + 0.90, W - 0.8, D - 0.8, 0.60, m_accent)
        box_mesh("ROOF_Deco_Step3", col_roof, W/2, D/2, roof_z_base + 1.30, W - 1.6, D - 1.6, 0.40, m_metal)

    else:
        # Modern Flat Roof with Parapet, Stair Tower (Mumty) & Cantilever Canopy
        box_mesh("ROOF_Parapet_L", col_roof, PAR_T/2, D/2, roof_z_base + PAR_H/2, PAR_T, D, PAR_H, m_wall)
        box_mesh("ROOF_Parapet_R", col_roof, W - PAR_T/2, D/2, roof_z_base + PAR_H/2, PAR_T, D, PAR_H, m_wall)
        box_mesh("ROOF_Parapet_F", col_roof, W/2, PAR_T/2, roof_z_base + PAR_H/2, W, PAR_T, PAR_H, m_accent)
        box_mesh("ROOF_Parapet_B", col_roof, W/2, D - PAR_T/2, roof_z_base + PAR_H/2, W, PAR_T, PAR_H, m_wall)

        # Stair Tower (Mumty)
        mt_w = min(2.5, W * 0.30)
        mt_d = min(3.8, D * 0.25)
        mt_h = 2.40
        box_mesh("ROOF_Mumty", col_roof, mt_w/2 + 0.5, mt_d/2 + 3.0, roof_z_base + mt_h/2, mt_w, mt_d, mt_h, m_wall)
        box_mesh("ROOF_Mumty_Slab", col_roof, mt_w/2 + 0.5, mt_d/2 + 3.0, roof_z_base + mt_h + 0.08, mt_w + 0.4, mt_d + 0.4, 0.16, m_concrete)

    # 6. Dynamic Camera Framing scaled to Plot Dimensions (W, D)
    cam_data = bpy.data.cameras.new("Camera_Persp")
    cam_data.type     = 'PERSP'
    cam_data.lens     = 28
    cam_data.clip_end = 500.0
    cam_obj = bpy.data.objects.new("Camera_Persp", cam_data)

    # Calculate optimal diagonal human-eye viewpoint based on W and D
    cam_dist = max(14.0, math.hypot(W, D) * 0.75)
    cam_x = -cam_dist * 0.60
    cam_y = -cam_dist * 0.85
    cam_z = 2.40 # Human eye elevation
    cam_obj.location = (cam_x, cam_y, cam_z)

    target_x = W * 0.45
    target_y = D * 0.25
    target_z = (Z_RF_slab + 1.5) * 0.50

    dx = target_x - cam_x
    dy = target_y - cam_y
    dz = target_z - cam_z
    dist_xy = math.sqrt(dx**2 + dy**2)
    pitch = math.atan2(dz, dist_xy)
    yaw   = math.atan2(dy, dx) - math.pi/2
    cam_obj.rotation_euler = Euler((math.pi/2 - pitch, 0.0, yaw), 'XYZ')
    link_to_col(cam_obj, col_cam)
    bpy.context.scene.camera = cam_obj

    # 7. Lighting (Sun + Sky Dome)
    sun_data = bpy.data.lights.new("Sun_Warm", 'SUN')
    sun_data.energy = 5.0
    sun_data.color  = (1.0, 0.95, 0.85)
    sun_data.angle  = math.radians(0.5)
    sun_obj = bpy.data.objects.new("Sun_Warm", sun_data)
    sun_obj.location = (W*0.5 - 20, -20, 25)
    sun_obj.rotation_euler = Euler((math.radians(40), 0.0, math.radians(-35)), 'XYZ')
    link_to_col(sun_obj, col_cam)

    sky_data = bpy.data.lights.new("Sky_Fill", 'AREA')
    sky_data.energy = 1.8
    sky_data.color  = (0.78, 0.88, 1.0)
    sky_data.size   = max(20.0, max(W, D) * 1.5)
    sky_obj = bpy.data.objects.new("Sky_Fill", sky_data)
    sky_obj.location = (W/2, D/2, -2)
    sky_obj.rotation_euler = Euler((math.pi, 0, 0), 'XYZ')
    link_to_col(sky_obj, col_cam)

    # World Environment
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    world = bpy.context.scene.world
    if not world.node_tree:
        world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()
    bg_n  = wn.new("ShaderNodeBackground")
    sky_n = wn.new("ShaderNodeTexSky")
    out_n = wn.new("ShaderNodeOutputWorld")
    sky_n.sky_type      = 'HOSEK_WILKIE'
    sky_n.sun_elevation = math.radians(35)
    sky_n.sun_rotation  = math.radians(225)
    bg_n.inputs["Strength"].default_value = 1.20
    wl.new(sky_n.outputs["Color"], bg_n.inputs["Color"])
    wl.new(bg_n.outputs["Background"], out_n.inputs["Surface"])

    # 8. Render Engine Settings
    scene = bpy.context.scene
    scene.render.engine             = 'CYCLES'
    scene.cycles.device             = 'CPU'
    scene.cycles.samples            = int(os.environ.get("CYCLES_SAMPLES", "32"))
    scene.cycles.use_denoising      = True
    scene.render.resolution_x       = 2560
    scene.render.resolution_y       = 1440
    scene.render.resolution_percentage = int(os.environ.get("RENDER_RES_PCT", "100"))
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode  = 'RGBA'
    scene.render.film_transparent   = False

    abs_png = os.path.abspath(output_png)
    scene.render.filepath = abs_png

    bpy.ops.render.render(write_still=True)
    print(f"[RENDER] Saved -> {abs_png}")

    abs_blend = os.path.abspath(output_blend)
    os.makedirs(os.path.dirname(abs_blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=abs_blend)
    print(f"[BLEND]  Saved -> {abs_blend}")

    # Export WebGL-ready GLB asset
    abs_glb = os.path.splitext(abs_blend)[0] + ".glb"
    try:
        bpy.ops.export_scene.gltf(filepath=abs_glb, export_format='GLB', export_apply=True)
        print(f"[GLB]    Saved -> {abs_glb}")
    except Exception as e:
        print(f"[GLB WARNING] Export failed: {e}")


# ---- ENTRY POINT ------------------------------------------------------------
if __name__ == "__main__":
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if len(args) >= 3:
            plan_json, blend_out, png_out = args[0], args[1], args[2]
            with open(plan_json, "r", encoding="utf-8") as fh:
                plan = json.load(fh)
            build_architecture(plan, blend_out, png_out)
        else:
            print("Args: <plan.json> <out.blend> <out.png>")
            sys.exit(1)
    else:
        print("Run inside Blender via --background --python blender_arch_v2_worker.py -- ...")
