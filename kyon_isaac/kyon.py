import omni.isaac.lab.sim as sim_utils
from omni.isaac.lab.actuators import ActuatorNetLSTMCfg, DCMotorCfg, ImplicitActuatorCfg
from omni.isaac.lab.assets.articulation import ArticulationCfg
from omni.isaac.lab.sensors import RayCasterCfg
from omni.isaac.lab.utils.assets import ISAACLAB_NUCLEUS_DIR

from .velodyne import VELODYNE_VLP_16_RAYCASTER_CFG

##
# Configuration - Actuators.
##

KYON_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path="/root/IsaacLab/iit-kyon-ros-pkg/kyon_urdf/urdf/kyon.usd",
        activate_contact_sensors=False,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False, solver_position_iteration_count=4, solver_velocity_iteration_count=0
        ),
        # collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=0.02, rest_offset=0.0),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.75),
        joint_pos={
            "hip_roll_.*": 0.0,
            "hip_pitch_1": 0.7,
            "hip_pitch_2": -0.7,
            "hip_pitch_3": 0.7,
            "hip_pitch_4": -0.7,
            "knee_pitch_1": -1.4,
            "knee_pitch_2": 1.4,
            "knee_pitch_3": 1.4,
            "knee_pitch_4": -1.4,
            "shoulder_pitch_1": 1.7,   
            "shoulder_pitch_2": -1.7,
            "elbow_pitch_1": -2.5,   
            "elbow_pitch_2": 2.5,        
            "wrist_pitch_1": 0.75,
            "wrist_pitch_2": -0.75,
            "shoulder_yaw_1": 0.0,    
            "shoulder_yaw_2": 0.0, 
            "wrist_yaw_1": 0.0,     
            "wrist_yaw_2": 0.0,
            "dagana_1_clamp_joint": 0.0,
            "dagana_2_clamp_joint": 0.0,
        },
    ),
    actuators={"all": DCMotorCfg(
            joint_names_expr=[".*"],
            saturation_effort=120.0,
            effort_limit=80.0,
            velocity_limit=7.5,
            stiffness={".*": 500.0},
            damping={".*": 10.0},
            friction=0.0,
        ),
    }
)