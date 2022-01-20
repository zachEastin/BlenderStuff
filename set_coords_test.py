from typing import Tuple
import bpy,numpy as np
from bpy.types import Mesh, Object, GeometryNodeTree, NodesModifier, Attribute, GeometryNodeGroup
import timeit
from timeit import default_timer as dt

is_fields = bpy.data.version >= (3,0,0)

def set_py(me:Mesh, coords:np.ndarray) -> None:
    me.vertices.foreach_set("co",coords.flatten())

def ensure_geo_setter() -> Tuple[GeometryNodeTree,str]:
    """Ensure a Geometry NodeTree named 'Set Coords' exists

    Returns
    -------
    GeometryNodeTree
        The correct node tree
    """
    ng = bpy.data.node_groups.get("Set Coords")
    if ng:
        return (ng, ng.inputs[-1].identifier)
    
    # Create and Setup
    ng = bpy.data.node_groups.new("Set Coords", "GeometryNodeTree")
    
    nodes = ng.nodes
    links = ng.links

    inp_node = nodes.get('Group Input')
    if not inp_node:
        inp_node = nodes.new('NodeGroupInput')
    out_node = nodes.get('Group Output')
    if not out_node:
        out_node = nodes.new('NodeGroupOutput')
    
    if is_fields:
        set_pos_node = nodes.new('GeometryNodeSetPosition')
        # From Group Input to Set Position - Geometry
        ng.inputs.new("NodeSocketGeometry", "Geometry")
        links.new(
            inp_node.outputs['Geometry'],
            set_pos_node.inputs['Geometry']
        )
        # From Group Input to Set Position - Offset
        ng.inputs.new("NodeSocketString", "Offset")
        links.new(
            inp_node.outputs['Offset'],
            set_pos_node.inputs['Offset']
        )
        # From Set Position to Group Output - Geometry
        ng.outputs.new("NodeSocketGeometry", "Geometry")
        links.new(
            set_pos_node.outputs['Geometry'],
            out_node.inputs['Geometry']
        )
    else:
        set_pos_node = nodes.new('GeometryNodeAttributeMix')
        # From Group Input to Set Position - Geometry
        ng.inputs.new("NodeSocketGeometry","Geometry")
        links.new(
            inp_node.outputs['Geometry'],
            set_pos_node.inputs['Geometry']
        )
        # From Group Input to Set Position - B
        ng.inputs.new("NodeSocketString", "B")
        links.new(
            inp_node.outputs["B"],
            set_pos_node.inputs['B']
        )
        # From Set Position to Group Output - Geometry
        ng.outputs.new("NodeSocketGeometry", "Geometry")
        links.new(
            set_pos_node.outputs['Geometry'],
            out_node.inputs['Geometry']
        )

        # Factor - NodeSocketFloatFactor
        set_pos_node.inputs[2].default_value = 0.0
        # A - NodeSocketString
        set_pos_node.inputs[3].default_value = 'position'
        # Result - NodeSocketString
        set_pos_node.inputs[11].default_value = 'position'

    return (ng, ng.inputs[-1].identifier)
def set_geo_nodes(obj:'Object', coords:np.ndarray) -> None:
    # Ensure Geo NodeTree Exists
    ng, attr_id = ensure_geo_setter()

    # Add Geo Nodes Modifier
    mod: NodesModifier = obj.modifiers.new('Coords Setter', 'NODES')
    bpy.data.node_groups.remove(mod.node_group)
    mod.node_group = ng

    # Set Attribute in PY
    attr:Attribute = obj.data.attributes.new('setter_coords','FLOAT_VECTOR','POINT')
    attr.data.foreach_set('vector', coords.flatten())

    # Set Attribute in Geo Nodes
    if is_fields:
        mod[f'{attr_id}_use_attribute'] = 1
        attr_id = f'{attr_id}_attribute_name'
    mod[attr_id] = 'setter_coords'

    # Apply Geo Nodes Modifier
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    mesh_to_remove = obj.data
    mesh_name = mesh_to_remove.name
    obj.data = me
    bpy.data.meshes.remove(mesh_to_remove)
    me.name = mesh_name


def set_geo_nodes_timed(obj: 'Object', coords: np.ndarray) -> None:
    # ng_time = 0.0
    # py_set = 0.0
    st = dt()
    # Ensure Geo NodeTree Exists
    ng, attr_id = ensure_geo_setter()
    print("Get NG:",dt()-st)

    # Add Geo Nodes Modifier
    st = dt()
    mod: NodesModifier = obj.modifiers.new('Coords Setter', 'NODES')
    bpy.data.node_groups.remove(mod.node_group)
    mod.node_group = ng
    print("Add Mod:", dt()-st)

    # Set Attribute in PY
    st = dt()
    attr: Attribute = obj.data.attributes.new(
        'setter_coords', 'FLOAT_VECTOR', 'POINT')
    attr.data.foreach_set('vector', coords.flatten())
    print("Set attr:", dt()-st)

    # Set Attribute in Geo Nodes
    if is_fields:
        mod[f'{attr_id}_use_attribute'] = 1
        attr_id = f'{attr_id}_attribute_name'
    mod[attr_id] = 'setter_coords'

    # Apply Geo Nodes Modifier
    st = dt()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    mesh_to_remove = obj.data
    mesh_name = mesh_to_remove.name
    obj.data = me
    bpy.data.meshes.remove(mesh_to_remove)
    me.name = mesh_name
    print("Apply Mod:", dt()-st)


def create_plane(x: int, y: int) -> Object:
    """Generate a grid object using geometry nodes
    Returns the created object"""
    def create_plane_gen_nodes() -> GeometryNodeGroup:
        """Create a geometry node group designed just to create grids"""
        ng = bpy.data.node_groups.new('Plane Generator', 'GeometryNodeTree')
        nodes = ng.nodes
        links = ng.links

        grid_node = nodes.new("GeometryNodeMeshGrid")
        out_node = nodes.new("NodeGroupOutput")

        ng.outputs.new("NodeSocketGeometry", "Geometry")

        links.new(out_node.inputs["Geometry"],
                  grid_node.outputs[0])
        return ng

    me: Mesh = bpy.data.meshes.new('deleteme')
    obj: Object = bpy.data.objects.new('deleteme',me)
    bpy.context.collection.objects.link(obj)

    mod: NodesModifier = obj.modifiers.new('Plane Generator', 'NODES')
    bpy.data.node_groups.remove(mod.node_group)

    # Create Plane with Geo Nodes
    ng = bpy.data.node_groups.get('Plane Generator')
    if not ng:
        ng = create_plane_gen_nodes()
    mod.node_group = ng
    ng.nodes['Grid'].inputs['Vertices X'].default_value = x
    ng.nodes['Grid'].inputs['Vertices Y'].default_value = y

    ng.interface_update(bpy.context)

    # Apply Modifier
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    mesh_to_remove = obj.data
    mesh_name = mesh_to_remove.name
    obj.data = me
    bpy.data.meshes.remove(mesh_to_remove)
    me.name = mesh_name

    # Reset Node Group to not cause slow downs when assigning to a new object
    ng.nodes['Grid'].inputs['Vertices X'].default_value = 3
    ng.nodes['Grid'].inputs['Vertices Y'].default_value = 3

    return obj


def mytimeit(title, SETUP_CODE, TEST_CODE, repeat, number):
    # timeit.repeat statement
    times = timeit.repeat(setup=SETUP_CODE,
                          stmt=TEST_CODE,
                          repeat=repeat,
                          number=number)

    # Print out Results
    avg = sum(times)/len(times)
    error_range = max(times) - avg
    print(
        f'{title}: {round(avg,2)} s ± {round(error_range,3)} s per loop')
    print(f'    (mean ± std. dev. of {repeat} runs, {number} loops each)')
    print(f'    (Min:{min(times)} | Max:{max(times)})')


def bpy_py_time(me_name:str, x:int, y:int, repeat, number):
    """Time bpy mesh ops vertex coordinate setting"""
    SETUP_CODE = f'''
import bpy, numpy as np
from __main__ import set_py
is_fields = bpy.data.version >= (3,0,0)
coords = np.random.random({x*y*3})
me = bpy.data.meshes.get('{me_name}')'''
    TEST_CODE = 'set_py(me, coords)'

    mytimeit("FROM FOREACH_SET", SETUP_CODE, TEST_CODE, repeat, number)


def geo_node_time(obj_name:str, x:int, y:int, repeat, number):
    """Time geo nodes vertex coordinate setting"""
    SETUP_CODE = f'''
import bpy, numpy as np
from __main__ import set_geo_nodes
is_fields = bpy.data.version >= (3,0,0)
coords = np.random.random({x*y*3})
obj = bpy.data.objects.get('{obj_name}')'''
    TEST_CODE = f'set_geo_nodes(obj, coords)'

    mytimeit("GEO NODE", SETUP_CODE, TEST_CODE, repeat, number)


if __name__ == "__main__":
    # Change These
    x = 100
    y = 100
    runs = 3
    loops = 100

    obj = create_plane(x, y)

    print()
    print(" STARTING ".center(60, "-"))
    print("NUM OF VERTS:",len(obj.data.vertices))

    bpy_py_time(obj.data.name, x, y, runs, loops)

    geo_node_time(obj.name, x, y, runs, loops)

    print()
    print(" Single Geo Nodes Detailed Timings:".rjust(60,'-'))
    coords = np.random.random(x*y*3)
    st = dt()
    set_geo_nodes_timed(obj, coords)
    print(" Total Timings:".rjust(30, '-'), dt()-st)

    bpy.data.meshes.remove(obj.data)

    print(" FINISHED ".center(60, "-"))
    print()
