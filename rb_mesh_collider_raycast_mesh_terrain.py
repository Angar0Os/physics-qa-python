import harfang as hg

hg.AddAssetsFolder("assets_compiled")

# Initialisation des entrées et de la fenêtre
hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit("Physics Test", res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)

pipeline = hg.CreateForwardPipeline()
res = hg.PipelineResources()

# Débogage physique
vtx_line_layout = hg.VertexLayoutPosFloatColorUInt8()
line_shader = hg.LoadProgramFromAssets("shaders/pos_rgb")

# Chargement de la scène
scene = hg.Scene()
hg.LoadSceneFromAssets("island_chain/island_chain.scn", scene, res, hg.GetForwardPipelineInfo())

cam_mat = hg.TransformationMat4(hg.Vec3(10, 2, -2) * 2000.0, hg.Vec3(hg.Deg(25), hg.Deg(-65), 0))
cam = hg.CreateCamera(scene, cam_mat, 10.0, 40000)
view_matrix = hg.InverseFast(cam_mat)
c = cam.GetCamera()
projection_matrix = hg.ComputePerspectiveProjectionMatrix(
    c.GetZNear(), c.GetZFar(), hg.FovToZoomFactor(c.GetFov()), hg.Vec2(res_x / res_y, 1)
)

scene.SetCurrentCamera(cam)

# Physique de la scène
physics = hg.SceneBullet3Physics()
physics.SceneCreatePhysicsFromAssets(scene)
physics_step = hg.time_from_sec_f(1 / 60)
dt_frame_step = hg.time_from_sec_f(1 / 60)

clocks = hg.SceneClocks()

# Description
hg.SetLogLevel(hg.LL_Normal)
print(
    ">>> Description:\n>>> Create a mesh collider with a rotating terrain collider from its .physics_bullet file "
    "and test the collisions with raycasts.\n>>> The 'Island chain' 3D model (65k triangles, 30x12Km) is a courtesy of World Machine."
)

island_node = scene.GetNode("island_chain")
mesh_col = scene.CreateCollision()
mesh_col.SetType(hg.CT_Mesh)
mesh_col.SetCollisionResource("island_chain/island_chain.physics_bullet")
mesh_col.SetMass(0)
island_node.SetCollision(0, mesh_col)

# Création d'un corps rigide
rb = scene.CreateRigidBody()
rb.SetType(hg.RBT_Static)
island_node.SetRigidBody(rb)
physics.NodeCreatePhysicsFromAssets(island_node)

# Boucle principale
keyboard = hg.Keyboard()
mouse = hg.Mouse()
cam_pos = cam.GetTransform().GetPos()
cam_rot = cam.GetTransform().GetRot()
vtx = hg.Vertices(vtx_line_layout, 2)
vid_scene_opaque = 0
frame_count = 0

while not keyboard.Down(hg.K_Escape) and hg.IsWindowOpen(win):
    keyboard.Update()
    mouse.Update()

    dt = hg.TickClock()

    s = 2000 if keyboard.Down(hg.K_LShift) else 200
    hg.FpsController(keyboard, mouse, cam_pos, cam_rot, s, dt)

    cam.GetTransform().SetPos(cam_pos)
    cam.GetTransform().SetRot(cam_rot)

    xz_spread = 300.0

    for i in range(-60, 61):
        for o in range(-15, 16):
            start_pos = hg.Vec3(i * xz_spread, 1000.0, o * xz_spread)
            end_pos = hg.Vec3(i * xz_spread, -100.0, o * xz_spread)
            raycast_out = physics.RaycastFirstHit(scene, start_pos, end_pos)

            vtx.Clear()
            if raycast_out.node.IsValid():
                vtx.Begin(0).SetPos(start_pos).SetColor0(hg.Color.Yellow).End()
                vtx.Begin(1).SetPos(raycast_out.P).SetColor0(hg.Color.Yellow).End()
            else:
                vtx.Begin(0).SetPos((start_pos + end_pos) * 0.5).SetColor0(hg.Color.Red).End()
                vtx.Begin(1).SetPos(end_pos).SetColor0(hg.Color.Red).End()

            hg.DrawLines(vid_scene_opaque, vtx, line_shader)

    view_id = 0
    hg.SceneUpdateSystems(scene, clocks, dt_frame_step, physics, physics_step, 3)
    view_id, pass_id = hg.SubmitSceneToPipeline(view_id, scene, hg.IntRect(0, 0, res_x, res_y), True, pipeline, res)
    vid_scene_opaque = hg.GetSceneForwardPipelinePassViewId(pass_id, hg.SFPP_Opaque)

    frame_count += 1

    hg.Frame()
    hg.UpdateWindow(win)

scene.Clear()
scene.GarbageCollect()

hg.RenderShutdown()
hg.DestroyWindow(win)

hg.WindowSystemShutdown()
hg.InputShutdown()
