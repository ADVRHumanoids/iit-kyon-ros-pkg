import subprocess

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    RegisterEventHandler,
    Shutdown,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):

    # kyon configuration parameters
    arms = LaunchConfiguration('arms').perform(context)
    legs = LaunchConfiguration('legs').perform(context)
    sensors = LaunchConfiguration('sensors').perform(context)
    payload = LaunchConfiguration('payload').perform(context)
    dagana = LaunchConfiguration('dagana').perform(context)
    feet = LaunchConfiguration('feet').perform(context)
    wheels = LaunchConfiguration('wheels').perform(context)
    steering_wheels = LaunchConfiguration('steering_wheels').perform(context)
    varta = LaunchConfiguration('varta').perform(context)
    ft_sensors = LaunchConfiguration('ft_sensors').perform(context)
    velodyne = LaunchConfiguration('velodyne').perform(context)

    world = LaunchConfiguration('world').perform(context)
    simopt = LaunchConfiguration('simopt').perform(context)
    sites = LaunchConfiguration('sites').perform(context)
    sdf = LaunchConfiguration('sdf').perform(context)
    ctrlcfg = LaunchConfiguration('ctrlcfg').perform(context)

    urdf_command = [
        'xacro',
        PathJoinSubstitution(
            [FindPackageShare('kyon_urdf'), 'urdf', 'kyon_robot.urdf.xacro']
        ).perform(context),
        'floating_joint:=true',
        f'upper_body:={arms}',
        f'legs:={legs}',
        f'sensors:={sensors}',
        f'payload:={payload}',
        f'varta:={varta}',
        f'dagana:={dagana}',
        f'feet:={feet}',
        f'wheels:={wheels}',
        f'steering_wheels:={steering_wheels}',
        f'ft_sensors:={ft_sensors}',
        f'velodyne:={velodyne}',
    ]

    srdf_command = [
        'xacro',
        PathJoinSubstitution(
            [FindPackageShare('kyon_srdf'), 'srdf', 'kyon.srdf.xacro']
        ).perform(context),
        'floating_joint:=true',
        f'upper_body:={arms}',
        f'legs:={legs}',
        f'sensors:={sensors}',
        f'payload:={payload}',
        f'dagana:={dagana}',
        f'feet:={feet}',
        f'wheels:={wheels}',
        f'steering_wheels:={steering_wheels}',
        f'ft_sensors:={ft_sensors}',
        f'velodyne:={velodyne}',
    ]

    urdf_string = subprocess.check_output(urdf_command).decode('utf-8')
    srdf_string = subprocess.check_output(srdf_command).decode('utf-8')

    urdf_command_str = ' '.join(urdf_command)

    robot_description_publisher = Node(
        package='xbot2_ros',
        executable='robot_description_publisher',
        name='robot_description_publisher',
        output='screen',
        parameters=[
            {'robot_description': urdf_string},
            {'robot_description_semantic': srdf_string},
        ],
    )

    simulator = Node(
        package='kyon_mujoco',
        executable='simulator_wrapper.bash',
        name='kyon_mujoco',
        output='screen',
        arguments=[
            '--name', 'kyon',
            '--urdf-command', urdf_command_str,
            '--world', world,
            '--simopt', simopt,
            '--ctrlcfg', ctrlcfg,
            '--sites', sites,
            '--sdf', sdf,
        ],
    )

    def on_simulator_exit(event, context):
        if event.returncode != 0:
            import os
            print(
                f'[kyon_mujoco] Simulator exited with code {event.returncode}, shutting down.',
                flush=True,
            )
            os._exit(event.returncode)
        return [Shutdown(reason='simulator exited')]

    exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=simulator,
            on_exit=on_simulator_exit,
        )
    )

    return [robot_description_publisher, simulator, exit_handler]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_mujoco'), 'config', 'world_pyramids.xml']
            ),
        ),
        DeclareLaunchArgument(
            'simopt',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_mujoco'), 'config', 'options.xml']
            ),
        ),
        DeclareLaunchArgument(
            'sites',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_mujoco'), 'config', 'sites.xml']
            ),
        ),
        DeclareLaunchArgument(
            'sdf',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_mujoco'), 'config', 'sdf.yaml']
            ),
        ),
        DeclareLaunchArgument(
            'ctrlcfg',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_mujoco'), 'config', 'kyon.yaml']
            ),
        ),
        DeclareLaunchArgument(
            'urdf',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_urdf'), 'urdf', 'kyon.urdf.xacro']
            ),
        ),
        DeclareLaunchArgument(
            'srdf',
            default_value=PathJoinSubstitution(
                [FindPackageShare('kyon_srdf'), 'srdf', 'kyon.srdf.xacro']
            ),
        ),
        # kyon configuration parameters
        DeclareLaunchArgument('arms',            default_value='false'),
        DeclareLaunchArgument('legs',            default_value='true'),
        DeclareLaunchArgument('sensors',         default_value='false'),
        DeclareLaunchArgument('payload',         default_value='false'),
        DeclareLaunchArgument('dagana',          default_value='false'),
        DeclareLaunchArgument('feet',            default_value='true'),
        DeclareLaunchArgument('wheels',          default_value='false'),
        DeclareLaunchArgument('steering_wheels', default_value='false'),
        DeclareLaunchArgument('varta',           default_value='true'),
        DeclareLaunchArgument('ft_sensors',      default_value='true'),
        DeclareLaunchArgument('velodyne',        default_value='false'),

        OpaqueFunction(function=launch_setup),
    ])
