import harfang as hg

def create_physic_cube_ex(scene, size, mtx, model_ref, materials, rb_type=hg.RBT_Dynamic, mass=0):
    node = hg.CreateObject(scene, mtx, model_ref, materials)
    node.SetName("Physic Cube")
    rb = scene.CreateRigidBody()
    rb.SetType(rb_type)
    node.SetRigidBody(rb)
    col = scene.CreateCollision()
    col.SetType(hg.CT_Cube)
    col.SetSize(size)
    col.SetMass(mass)
    node.SetCollision(0, col)
    return node, rb

def create_physic_sphere_ex(scene, radius, mtx, model_ref, materials, rb_type=hg.RBT_Dynamic, mass=0):
    node = hg.CreateObject(scene, mtx, model_ref, materials)
    node.SetName("Physic Sphere")
    rb = scene.CreateRigidBody()
    rb.SetType(rb_type)
    node.SetRigidBody(rb)
    col = scene.CreateCollision()
    col.SetType(hg.CT_Sphere)
    col.SetRadius(radius)
    col.SetMass(mass)
    node.SetCollision(0, col)
    return node, rb

hg.AddAssetsFolder('assets_compiled')

hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit('Physics Test', res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)

pipeline = hg.CreateForwardPipeline(2048)
res = hg.PipelineResources()

vtx_line_layout = hg.VertexLayoutPosFloatColorUInt8()
line_shader = hg.LoadProgramFromAssets("shaders/pos_rgb")

pbr_shader = hg.LoadPipelineProgramRefFromAssets('core/shader/pbr.hps', res, hg.GetForwardPipelineInfo())
mat_grey = hg.CreateMaterial(pbr_shader, 'uBaseOpacityColor', hg.Vec4(1, 1, 1), 'uOcclusionRoughnessMetalnessColor', hg.Vec4(1, 0.5, 0.05))

vtx_layout = hg.VertexLayoutPosFloatNormUInt8()

sphere_radius = 0.8
sphere_ref = res.AddModel('sphere', hg.CreateSphereModel(vtx_layout, sphere_radius, 8, 8))

ground_size = hg.Vec3(30, 1, 30)
ground_ref = res.AddModel('ground', hg.CreateCubeModel(vtx_layout, ground_size.x, ground_size.y, ground_size.z))

scene = hg.Scene()

cam_mat = hg.TransformationMat4(hg.Vec3(-10, 13, -25), hg.Vec3(hg.Deg(35), hg.Deg(15), 0))
cam = hg.CreateCamera(scene, cam_mat, 0.01, 1000)
view_matrix = hg.InverseFast(cam_mat)
c = cam.GetCamera()
projection_matrix = hg.ComputePerspectiveProjectionMatrix(c.GetZNear(), c.GetZFar(), hg.FovToZoomFactor(c.GetFov()), hg.Vec2(res_x / res_y, 1))

scene.SetCurrentCamera(cam)

lgt = hg.CreateLinearLight(scene, hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(hg.Deg(30), hg.Deg(-30), 0)), hg.Color(1, 1, 1), hg.Color(1, 1, 1), 10, hg.LST_Map, 0.00075, hg.Vec4(10, 20, 30, 50))

sphere_list = []
for i in range(1, 12):
    sphere_node, sphere_rb = create_physic_sphere_ex(scene, sphere_radius, hg.TranslationMat4(hg.Vec3(-14, 0.8, -14 + 2 * i)), sphere_ref, [mat_grey], hg.RBT_Dynamic, 15.0)
    rolling_friction = 1 - ((i - 1) / 10.0)
    print(f"rolling_friction = {rolling_friction}")
    sphere_rb.SetRollingFriction(rolling_friction)
    sphere_list.append(sphere_node)

floor, rb_floor = create_physic_cube_ex(scene, ground_size, hg.TranslationMat4(hg.Vec3(-2, -0.5, 0)), ground_ref, [mat_grey], hg.RBT_Static, 0)
rb_floor.SetRollingFriction(0)

physics = hg.SceneBullet3Physics()
physics.SceneCreatePhysicsFromAssets(scene)
physics_step = hg.time_from_sec_f(1 / 60)
dt_frame_step = hg.time_from_sec_f(1 / 60)

clocks = hg.SceneClocks()

hg.SetLogLevel(hg.LL_Normal)
print(">>> Description:\n>>> Apply a constant force on N spheres having a rolling friction factor from 0.0 (far) to 1.0 (near).")

keyboard = hg.Keyboard()

while not keyboard.Down(hg.K_Escape) and hg.IsWindowOpen(win):
    keyboard.Update()

    for sphere in sphere_list:
        physics.NodeAddForce(sphere, hg.Vec3(50, 0, 0))

    view_id = 0
    hg.SceneUpdateSystems(scene, clocks, dt_frame_step, physics, physics_step, 3)
    view_id, pass_id = hg.SubmitSceneToPipeline(view_id, scene, hg.IntRect(0, 0, res_x, res_y), True, pipeline, res)

    hg.SetViewClear(view_id, 0, 0, 1.0, 0)
    hg.SetViewRect(view_id, 0, 0, res_x, res_y)
    hg.SetViewTransform(view_id, view_matrix, projection_matrix)
    rs = hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled)
    physics.RenderCollision(view_id, vtx_line_layout, line_shader, rs, 0)

    hg.Frame()
    hg.UpdateWindow(win)

scene.Clear()
scene.GarbageCollect()

hg.RenderShutdown()
hg.DestroyWindow(win)

hg.WindowSystemShutdown()
hg.InputShutdown()