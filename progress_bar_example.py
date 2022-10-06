import bpy
import bmesh
import threading

class ModalTimerOperator(bpy.types.Operator):
    """Operator which runs itself from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"

    _timer = None
    
    total_cubes = 10_000
    cubes_created = 0
    updated=False
    end_early = False
    _th = None
    
    def create_cubes(self):
        while self.cubes_created < self.total_cubes:
            me = bpy.data.meshes.new("test")
            obj = bpy.data.objects.new("test", me)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bm.to_mesh(me)
            self.cubes_created += 1
            self.updated = True
            if self.end_early:
                print("Ending Early")
                return

    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type == 'ESC':
            self.end_early = True
            self.finish(context)
            return {'CANCELLED'}
        
        if self.updated:
            progress = self.cubes_created / self.total_cubes
            self.text.progress_bar = int(round(progress * 100, 2))
            self.updated = False
        
        if not self._th.is_alive():
            self.finish(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        self._th = threading.Thread(target=self.create_cubes, args=())
        
        self.text = context.space_data.text
        self.text.show_progress_bar = True
        self.text.progress_bar = 0
        self._th.start()
        return {'RUNNING_MODAL'}

    def finish(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.text.show_progress_bar = False
        print("FINISHED")


def header_draw_func(self, context):
    text = context.space_data.text
    if text.show_progress_bar:
        self.layout.prop(text, 'progress_bar')


def register():
    bpy.types.Text.progress_bar = bpy.props.IntProperty(
                                                subtype="PERCENTAGE",
                                                min=0,
                                                max=100
                                   )
    bpy.types.Text.show_progress_bar = bpy.props.BoolProperty()
    bpy.utils.register_class(ModalTimerOperator)
    bpy.types.TEXT_HT_header.append(header_draw_func)


def unregister():
    del bpy.types.Text.progress_bar
    del bpy.types.Text.show_progress_bar
    bpy.utils.unregister_class(ModalTimerOperator)
    bpy.types.TEXT_HT_header.remove(header_draw_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.modal_timer_operator() 
