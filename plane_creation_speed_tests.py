import bpy
import bmesh
from bpy.types import GeometryNodeGroup, Object, Mesh, NodesModifier
import numpy as np
import timeit

print(" STARTING ".center(60, "-"))


def bmesh_op(x: int, y: int):
    """Generate a grid object using bmesh ops"""
    me: Mesh = bpy.context.object.data

    bm = bmesh.new()
    bmesh.ops.create_grid(
        bm,
        x_segments=x,
        y_segments=y,
        size=2.0
    )
    bm.to_mesh(me)
    me.update()


def bpy_py(x: int, y: int):
    """Generate a grid object using mesh ops"""
    def from_mydata(mesh: Mesh, vertices: np.ndarray, faces: np.ndarray, faces_len:int) -> None:
        """Like Blender's mesh.from_pydata but optimized for numpy and grid creation

        Parameters
        ----------
        mesh : Mesh
        vertices : np.ndarray
            1D numpy array of vertex coordinates. Length of list should be x*y*3
        faces : np.ndarray
            1D numpy array of each face's vertex indices. Length should be (y-1)*(x-1)*4
        faces_len : int
            The number of faces
        """
        mesh.clear_geometry()

        face_lengths = np.full(faces_len, 4)  # Assume we have 4 verts per face

        vertices_len = int(len(vertices)/3)

        mesh.vertices.add(vertices_len)
        mesh.loops.add(len(faces))
        mesh.polygons.add(faces_len)

        mesh.vertices.foreach_set("co", vertices)

        vertex_indices = faces.copy()
        # Can assume each face has only 4 verts
        loop_starts = np.arange(faces_len)*4

        mesh.polygons.foreach_set("loop_total", face_lengths)
        mesh.polygons.foreach_set("loop_start", loop_starts)
        mesh.polygons.foreach_set("vertices", vertex_indices)

        if faces_len:
            mesh.update(
                calc_edges=True
            )

    me: Mesh = bpy.context.object.data

    # VERTS
    verts = np.zeros([y, x, 3], dtype=float)
    xc = np.linspace(0, 1, x)
    yc = np.linspace(0, 1, y)
    xv, yv = np.meshgrid(xc, yc)
    verts[:, :, 0] = xv
    verts[:, :, 1] = yv

    # FACES
    a = np.arange(x-1, dtype=int)
    b = a + 1
    c = a + x
    d = c + 1
    faces = np.empty([y-1, x-1, 4], dtype=int)
    faces[:, :, 0] = a
    faces[:, :, 1] = b
    faces[:, :, 2] = d
    faces[:, :, 3] = c
    # print("Faces Pre:\n",faces)

    fc = np.arange(faces.shape[0])
    # Make array of same shape with numbers to add
    # array([1,2,3]) becomes array([1,1,1],[2,2,2],[3,3,3]) or whatever the shape of faces is
    broad_fc = np.broadcast_to(fc, faces.T.shape).T
    # print("broad_fc:\n",broad_fc)
    # print(f"broad_fc*{x}:\n",broad_fc*x)
    faces += broad_fc*x
    faces.resize([(y-1)*(x-1), 4])

    from_mydata(
        me,    # mesh
        verts.flatten(),  # verts
        faces.flatten(),  # faces
        len(faces),
    )

    me.update()


def geo_node(x: int, y: int):
    """Generate a grid object using geometry nodes"""
    def create_plane_gen_nodes(obj) -> GeometryNodeGroup:
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

    obj: Object = bpy.context.object

    mod: NodesModifier = obj.modifiers.new('Plane Generator', 'NODES')

    # Creat Plane with Geo Nodes
    ng = bpy.data.node_groups.get('Plane Generator')
    if not ng:
        ng = create_plane_gen_nodes(obj)
    mod.node_group = ng
    ng.nodes['Grid'].inputs['Vertices X'].default_value = x
    ng.nodes['Grid'].inputs['Vertices Y'].default_value = y

    # Apply Modifier
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    obj.data = mesh

    # Reset Node Group to not cause slow downs when assigning to a new object
    ng.nodes['Grid'].inputs['Vertices X'].default_value = 3
    ng.nodes['Grid'].inputs['Vertices Y'].default_value = 3


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


def bpy_ops_time(x, y, repeat, number):
    """Time bpy ops grid creation"""
    SETUP_CODE = "import bpy"
    TEST_CODE = f'bpy.ops.mesh.primitive_grid_add(x_subdivisions={x},y_subdivisions={y},);bpy.data.objects.remove(bpy.data.objects["Grid"])'

    mytimeit("BPY OPS", SETUP_CODE, TEST_CODE, repeat, number)


def bmesh_ops_time(x, y, repeat, number):
    """Time bmesh ops grid creation"""
    SETUP_CODE = '''
import bpy, bmesh
from __main__ import bmesh_op'''
    TEST_CODE = f'bmesh_op({x},{y})'

    mytimeit("BMESH OPS", SETUP_CODE, TEST_CODE, repeat, number)


def bpy_py_time(x, y, repeat, number):
    """Time bpy mesh ops grid creation"""
    SETUP_CODE = '''
import bpy
from __main__ import bpy_py'''
    TEST_CODE = f'bpy_py({x},{y})'

    mytimeit("FROM NumPYDATA", SETUP_CODE, TEST_CODE, repeat, number)


def geo_node_time(x, y, repeat, number):
    """Time geo nodes grid creation"""
    SETUP_CODE = '''
import bpy
from __main__ import geo_node'''
    TEST_CODE = f'geo_node({x},{y})'

    mytimeit("GEO NODE", SETUP_CODE, TEST_CODE, repeat, number)


if __name__ == "__main__":
    # Change These
    x = 100
    y = 100
    runs = 3
    loops = 100
    
    C = bpy.context
    obj = C.object

    bpy_ops_time(x, y, runs, loops)
    
    C.view_layer.objects.active = obj
    bmesh_ops_time(x, y, runs, loops)
    
    C.view_layer.objects.active = obj
    bpy_py_time(x, y, runs, loops)
    
    C.view_layer.objects.active = obj
    geo_node_time(x, y, runs, loops)
