######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : 3D Agent 프로그램에서 사용되는 상수들의 집합 ##
######################################################

## Common ##
CMD_COMMON_ENTER = "\n"                                                                                     # Enter
CMD_COMMON_TAB = "\t"                                                                                       # Tab
CMD_COMMON_SLASH = "/"                                                                                      # Slash
CMD_COMMON_SPACE = " "                                                                                      # Space
CMD_COMMON_SPACE_DOUBLE = "  "                                                                              # Space x 2
CMD_COMMON_SPACE_FOUR = "    "                                                                              # Space x 4
CMD_COMMON_SPACE_SIX = "      "                                                                             # Space x 6
CMD_COMMON_SPACE_EIGHT = "        "                                                                         # Space x 8
CMD_COMMON_SPACE_TEN = "          "                                                                         # Space x 10
CMD_COMMON_SEMICOLON = ";"                                                                                  # Semicolon
CMD_COMMON_PARAM_INSERT = ":="                                                                              # Parameter insert
CMD_COMMON_DOUBLE_QUOTATION_MARKS = "\""                                                                    # Double quotation marks
CMD_COMMON_OPEN_LAUNCH = "<launch>"                                                                         # Tag : Launch
CMD_COMMON_CLOSE_LAUNCH = "</launch>"                                                                       # Tag : Launch closer
CMD_COMMON_ARG = "arg"                                                                                      # Tag : arg
CMD_COMMON_OPEN_ARG = "<arg"                                                                                # Tag : Argument
CMD_COMMON_OPEN_BRACKET_WITH_QUOTE = "\"$("                                                                 # Tag : Bracket With "
CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE = ")\""                                                                 # Tag : Bracket closer With "
CMD_COMMON_OPEN_BRACKET = "$("                                                                              # Tag : Bracket
CMD_COMMON_CLOSE_BRACKET = ")"                                                                              # Tag : Bracket closer
CMD_COMMON_OPEN_PARAM = "<param"                                                                            # Tag : Parameter
CMD_COMMON_CLOSE = ">"                                                                                      # Tag : Statement closer
CMD_COMMON_CLOSE_TAG = "/>"                                                                                 # Tag : Tag closer
CMD_COMMON_DEFAULT = "default="                                                                             # Value : default
CMD_COMMON_NAME = "name="                                                                                   # Attribute : name
CMD_COMMON_VALUE = "value="                                                                                 # Attribute : value
CMD_COMMON_OPEN_GROUP = "<group"                                                                            # Tag : Group
CMD_COMMON_CLOSE_GROUP = "</group>"                                                                         # Tag : Group closer
CMD_COMMON_NS = "ns="                                                                                       # Attribute : ns
CMD_COMMON_IF = "if="                                                                                       # Attribute : if    
CMD_COMMON_FILE = "file="                                                                                   # Attribute : File    
CMD_COMMON_OPEN_NODE = "<node"                                                                              # Tag : Node
CMD_COMMON_CLOSE_NODE = "</node>"                                                                           # Tag : Node closer
CMD_COMMON_PKG = "pkg="                                                                                     # Attribute : Package
CMD_COMMON_TYPE = "type="                                                                                   # Attribute : Type
CMD_COMMON_RESPAWN = "respawn="                                                                             # Attribute : Respawn
CMD_COMMON_OUTPUT = "output="                                                                               # Attribute : OutPut
CMD_COMMON_DOC = "doc="                                                                                     # Attribute : Documents
CMD_COMMON_DEFAULT_POS = "\"0.0\""                                                                          # Attribute : Default Position
CMD_COMMON_CLOSE_INCLUDE="</include>"                                                                       # Tag : Include Closer
CMD_COMMON_TRUE = "true"                                                                                    # Word : true
CMD_COMMON_FALSE = "false"                                                                                  # Word : false
CMD_COMMON_UNDERBAR = "_"                                                                                   # _
CMD_COMMON_X = "-x"
CMD_COMMON_Y = "-y"
CMD_COMMON_Z = "-z"
CMD_COMMON_MODEL = "-model"

## World ##  
## "World는 옵션등이 반고정 형태이고 또한 현재 옵션을 사용하기 않기 때문에 전체 문장을 입력해 놓고 상황에 따라 사용한다" ##
CMD_WORLD_COMMENT_START = "<!-- #### World #### -->"
CMD_WORLD_COMMENT_END = "<!-- #### World End #### -->"
CMD_WORLD_INCLUDE_OPEN = "<include file=\"$(find gazebo_ros)/launch/empty_world.launch\">"
CMD_WORLD_ARG_WORLDNAME_WAREHOUSE = "<arg name=\"world_name\" value=\"$(find aws_robomaker_small_warehouse_world)/worlds/no_roof_small_warehouse.world\"/>"
CMD_WORLD_ARG_WORLDNAME_HOSPITAL = "<arg name=\"world_name\" value=\"$(find aws_robomaker_hospital_world)/worlds/hospital.world\"/>"
CMD_WORLD_ARG_WORLDNAME_SMALLHOUSE = "<arg name=\"world_name\" value=\"$(find aws_robomaker_small_house_world)/worlds/small_house.world\"/>"
CMD_WORLD_ARG_WORLDNAME_BOOKSTORE = "<arg name=\"world_name\" value=\"$(find aws_robomaker_bookstore_world)/worlds/bookstore.world\"/>"
CMD_WORLD_ARG_WORLDNAME_ARG_LEFT  = "<arg name=\"world_name\" value=\""
CMD_WORLD_ARG_WORLDNAME_ARG_RIGHT  = ".world\"/>"
CMD_WORLD_ARG_PAUSED = "<arg name=\"paused\" value=\"false\"/>"
CMD_WORLD_ARG_USE_SIM_TIME = "<arg name=\"use_sim_time\" value=\"true\"/>"
CMD_WORLD_ARG_GUI = "<arg name=\"gui\" value=\"true\"/>"
CMD_WORLD_ARG_HEADLESS = "<arg name=\"headless\" value=\"false\"/>"
CMD_WORLD_ARG_DEBUG = "<arg name=\"debug\" value=\"false\"/>"
CMD_WORLD_INCLUDE_CLOSE = "</include>"

## World - Person ##
CMD_WORLD_PERSON_ACTOR = "actor"
CMD_WORLD_PERSON_ACTOR_PLUGIN = "plugin"
CMD_WORLD_PERSON_ACTOR_ARG_NAME_OPEN_LEFT = "<actor name=\""
CMD_WORLD_PERSON_ACTOR_ARG_NAME_OPEN_RIGHT = "\">"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_OPEN = "<pose>"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT = "0 1 1.25 0 0 0"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_T_X = "0"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_T_Y = "0"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_T_Z = "1.25"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_R_X = "0"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_R_Y = "0"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_R_Z = "0"
CMD_WORLD_PERSON_ACTOR_ARG_POSE_CLOSE = "</pose>"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_OPEN = "<skin>"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_CLOSE = "</skin>"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_OPEN = "<filename>"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_WALK = "file://media/models/walk.dae"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_CLOSE = "</filename>"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_SCALE_OPEN = "<scale>"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_SCALE_DEFAULT = "1.0"
CMD_WORLD_PERSON_ACTOR_ARG_SKIN_SCALE_CLOSE = "</scale>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_OPEN_DEFAULT = "<animation name=\"walking\">"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_FILENAME_OPEN = "<filename>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_FILENAME_DEFAULT = "file://media/models/walk.dae"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_FILENAME_CLOSE = "</filename>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_SCALE_OPEN = "<scale>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_SCALE_DEFAULT = "1.000000"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_SCALE_CLOSE = "</scale>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_INTERPOLATE_X_OPEN = "<interpolate_x>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_INTERPOLATE_X_CLOSE = "</interpolate_x>"
CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_CLOSE = "</animation>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OPEN_LEFT = "<plugin name=\""
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OPEN_RIGHT = "\" filename=\"libActorPlugin.so\">"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_OPEN = "<target>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_DEFAULT = "0 -5 1.2138"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_CLOSE = "</target>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_WEIGHT_OPEN = "<target_weight>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_WEIGHT_DEFAULT = "1.15"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_WEIGHT_CLOSE = "</target_weight>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OBSTACLE_WEIGHT_OPEN = "<obstacle_weight>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OBSTACLE_WEIGHT_DEFAULT = "1.8"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OBSTACLE_WEIGHT_CLOSE = "</obstacle_weight>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_ANIMATION_FACTOR_OPEN = "<animation_factor>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_ANIMATION_FACTOR_DEFAULT = "5.1"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_ANIMATION_FACTOR_CLOSE = "</animation_factor>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_OPEN = "<ignore_obstacles>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_MODEL_OPEN = "<model>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_MODEL_DEFAULT = "ground_plane"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_MODEL_CLOSE = "</model>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_CLOSE = "</ignore_obstacles>"
CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_CLOSE = "</plugin>"
CMD_WORLD_PERSON_ACTOR_ARG_NAME_CLOSE = "</actor>"
CMD_WORLD_PERSON_ACTOR_EFFECT_SWATER = "<effect id=\"sweater-green-effect\">"
CMD_WORLD_PERSON_ACTOR_EFFECT_JEAN= "<effect id=\"jeans-blue-effect\">"
CMD_WORLD_PERSON_ACTOR_EFFECT_EMISSION= "<emission>"
CMD_WORLD_PERSON_ACTIR_EFFECT_EMISSION_COLOR_OPEN_LEFT = "<color sid=\"emission\">"
CMD_WORLD_PERSON_ACTOR_EFFECT_AMBIENT= "<ambient>"
CMD_WORLD_PERSON_ACTIR_EFFECT_AMBIENT_COLOR_OPEN_LEFT = "<color sid=\"ambient\">"
CMD_WORLD_PERSON_ACTOR_EFFECT_DIFFUSE= "<diffuse>"
CMD_WORLD_PERSON_ACTIR_EFFECT_DIFFUSE_COLOR_OPEN_LEFT = "<color sid=\"diffuse\">"
CMD_WORLD_PERSON_ACTOR_EFFECT_SPECULAR= "<specular>"
CMD_WORLD_PERSON_ACTIR_EFFECT_SPECULAR_COLOR_OPEN_LEFT = "<color sid=\"specular\">"
CMD_WORLD_PERSON_ACTIR_EFFECT_COLOR_CLOSE = "</color>"

## Locobot ##
CMD_LOCOBOT_COMMENT_START = "<!-- #### Locobot #### -->"
CMD_LOCOBOT_COMMENT_END = "<!-- #### Locobot End #### -->"
CMD_LOCOBOT_DEFAULT_NAME_LOCOBOT = "locobot"
CMD_LOCOBOT_NODE_PKG_TF = "<node pkg=\"tf\" type=\"static_transform_publisher\" name=\"cam_transform\" args=\"0 0 0 0 0 0 /camera_link /camera_color_optical_frame 100\" />"
CMD_LOCOBOT_MODEL = "locobot_"
# "Group 옵션들은 반고정 상태 이므로 모델명이 필요하지 않는 구문둘은 통으로 고정 하여 사용한다" ##
CMD_LOCOBOT_PARAM_NAME_ROBOT_DESCRIPTION = "<param name=\"/robot_description\" textfile=\"$(find locobot_description)/urdf/locobot_lite_description.urdf\"/>"
CMD_LOCOBOT_INCLUDE_FILE = "<include file=\"$(find locobot_lite_moveit_config)/launch/planning_context.launch\">"
CMD_LOCOBOT_ARG_LOAD_ROBOT = "<arg name=\"load_robot_description\" value=\"true\"/>"
CMD_LOCOBOT_OPEN_GROUP_NODE_NAME_SPAWN_URDF = "<node name=\"spawn_urdf\" pkg=\"gazebo_ros\" type=\"spawn_model\" args=\"-param /robot_description -urdf"
CMD_LOCOBOT_OPEN_GROUP_MODEL = "-model"
CMD_LOCOBOT_CLOSE_GROUP_NODE_NAME_SPAWN_URDF = "\" />"
CMD_LOCOBOT_POSITION_Z_DEFAULT = "0.05"
CMD_LOCOBOT_INCLUDE_GAZEBO_CONTROLE = "<include file=\"$(find locobot_gazebo)/launch/gazebo_locobot_control.launch\"/>"
CMD_LOCOBOT_NODE_NAME_LOCOBOT_GAZEBO = "<node name=\"locobot_gazebo\" pkg=\"locobot_gazebo\" type=\"locobot_gazebo\" respawn=\"true\" output=\"screen\"/>"
CMD_LOCOBOT_NODE_NAME_PYROBOT_MOVEIT = "<node name=\"pyrobot_moveit\" pkg=\"pyrobot_bridge\" type=\"moveit_bridge.py\"/>"
CMD_LOCOBOT_INCLUDE_LOCOBOT_LITE_MOVEIT = "<include file=\"$(find locobot_lite_moveit_config)/launch/demo.launch\"/>"

## Turtlebot3 - common ##
CMD_TURTLEBOT3_DEFAULT_NAME = "tb3_"
CMD_TURTLEBOT3_GAZEBO = "turtlebot3_gazebo"

## Turtlebot3 - burger ##
CMD_TURTLEBOT3_BURGER_COMMENT_START = "<!-- #### Turtlebot3 - Burger #### -->"
CMD_TURTLEBOT3_BURGER_COMMENT_END = "<!-- #### Turtlebot3 - Burger End #### -->"
CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X = "_x_pos"
CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y = "_y_pos"
CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z = "_z_pos"
CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW = "_yaw"
CMD_TURTLEBOT3_MODEL_BURGER = "burger"                                                                      # Value : Burger

## Turtlebot3 - waffle ##
CMD_TURTLEBOT3_WAFFLE_COMMENT_START = "<!-- #### Turtlebot3 - Waffle #### -->"
CMD_TURTLEBOT3_WAFFLE_COMMENT_END = "<!-- #### Turtlebot3 - Waffle End #### -->"
CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_X = "_x_pos"
CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Y = "_y_pos"
CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Z = "_z_pos"
CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_YAW = "_yaw"
CMD_TURTLEBOT3_MODEL_WAFFLE = "waffle"                                                                      # Value : Waffle (default)
CMD_TURTLEBOT3_MODEL_WAFFLE_PI = "waffle_pi"                                                                # Value : Waffle_PI

## Turtlebot3 - common
CMD_TURTLEBOT3_MODEL = "\"model\""                                                                          # Value : Model
# "Group 옵션들은 반고정 상태 이므로 모델명이 필요하지 않는 구문둘은 통으로 고정 하여 사용한다(아래를 보면 TF_PRFIX 등 통 고정이 아닌 문장들이 몇몇 있다)" ##
CMD_TURTLEBOT3_OPEN_GROUP_PARAM_NAME_ROBOT_DESCRIPTION = "<param name=\"robot_description\" command=\"$(find xacro)/xacro --inorder $(find turtlebot3_description)/urdf/turtlebot3_"
CMD_TURTLEBOT3_CLOSE_GROUP_PARAM_NAME_ROBOT_DESCRIPTION = ".urdf.xacro\" />"
CMD_TURTLEBOT3_GROUP_NODE_PKG_ROBOT_STATE_PUBLISHER = "<node pkg=\"robot_state_publisher\" type=\"robot_state_publisher\" name=\"robot_state_publisher\" output=\"screen\">"
CMD_TURTLEBOT3_GROUP_PARAM_NAME_PUBLISH_FREQUENCY = "<param name=\"publish_frequency\" type=\"double\" value=\"50.0\" />"
CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX = "<param name=\"tf_prefix\" value="
CMD_TURTLEBOT3_OPEN_GROUP_NODE_NAME_SPAWN_URDF = "<node name=\"spawn_urdf\" pkg=\"gazebo_ros\" type=\"spawn_model\" "
CMD_TURTLEBOT3_CLOSE_GROUP_NODE_NAME_SPAWN_URDF = " -param robot_description\" />"

## Jetbot
CMD_JETBOT_DEFAULT_NAME = "jetbot_"

## Interbotix
# Arguments#
CMD_INTERBOTIX_COMMENT_ARGUMENTS_START = "<!-- #### Interbotix Arguments #### -->"
CMD_INTERBOTIX_COMMENT_ARGUMENTS_END = "<!-- #### Interbotix Arguments End #### -->"
CMD_INTERBOTIX_COMMENT_START = "<!-- #### Interbotix #### -->"
CMD_INTERBOTIX_COMMENT_END = "<!-- #### Interbotix End #### -->"
CMD_INTERBOTIX_ROBOT_MODEL = "robot_model"
CMD_INTERBOTIX_ROBOT_MODEL_LOCOBOT_WX250S = "locobot_wx250s"
CMD_INTERBOTIX_ROBOT_NAME = "locobot"
CMD_INTERBOTIX_ROBOT_NAME_DEFAULT = "locobot_"
CMD_INTERBOTIX_ARM_MODEL = "arm_model"
CMD_INTERBOTIX_ARM_MODEL_VALUE = "default=\"$(eval 'mobile_' + arg('robot_model').split('_')[1])\"/>"
CMD_INTERBOTIX_SHOW_LIDAR = "show_lidar"
CMD_INTERBOTIX_SHOW_GRIPPER_BAR = "show_gripper_bar"
CMD_INTERBOTIX_SHOW_GRIPPER_FINGERS = "show_gripper_fingers"
CMD_INTERBOTIX_EXTERNAL_URDF_LOC = "external_urdf_loc"
CMD_INTERBOTIX_USE_RVIZ = "use_rviz"
CMD_INTERBOTIX_RVIZ_FRAME = "rviz_frame"
CMD_INTERBOTIX_RVIZ_FRAME_VALUE_OPEN = "default=\"$(arg "
CMD_INTERBOTIX_RVIZ_FRAME_VALUE_CLOSE = ")/base_footprint"
CMD_INTERBOTIX_USE_POSITION_CONTROLLERS = "use_position_controllers"
CMD_INTERBOTIX_USE_TRAJECTORY_CONTROLLERS = "use_trajectory_controllers"
CMD_INTERBOTIX_DOF = "dof"
CMD_INTERBOTIX_DOF_VALUE_DEFAULT = "5"
CMD_INTERBOTIX_ENV_GAZEBO_RESOURCE_PATH = "<env name=\"GAZEBO_RESOURCE_PATH\"              value=\"$(find interbotix_xslocobot_gazebo)\"/>"
CMD_INTERBOTIX_ROSPARAM_FILE_LOCOBOT_GAZEBO_CONTROLLERS_OPEN = "<rosparam file=\"$(find interbotix_xslocobot_gazebo)/config/locobot_gazebo_controllers.yaml\" command=\"load\" ns=\""
CMD_INTERBOTIX_ROSPARAM_FILE_LOCOBOT_GAZEBO_CONTROLLERS_CLOSE = "\"/>"
# Param and nodes...
CMD_INTERBOTIX_GROUP_ROBOT_MODEL = "<group if=\"$(eval robot_model != 'locobot_base')\">"
CMD_INTERBOTIX_GROUP_USE_TRAJECTORY_CONTROLLERS = "<group if=\"$(arg use_trajectory_controllers)\">"
CMD_INTERBOTIX_ROSPARAM_FILE_TRAJECTORY_CONTROLLERS_OPEN = "<rosparam file=\"$(find interbotix_xslocobot_gazebo)/config/trajectory_controllers/$(arg arm_model)_trajectory_controllers.yaml\" command=\"load\" ns=\""
CMD_INTERBOTIX_ROSPARAM_FILE_TRAJECTORY_CONTROLLERS_CLOSE = "\"/>"
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_OPEN = "<node\n        name=\"controller_spawner\"\n        pkg=\"controller_manager\"\n        type=\"controller_manager\"\n        respawn=\"false\"\n        output=\"screen\"\n        ns=\""
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_CLOSE = "\"\n        args=\"spawn arm_controller gripper_controller pan_controller tilt_controller joint_state_controller\"/>"
CMD_INTERBOTIX_GROUP_USE_POSITION_CONTROLLERS = "<group if=\"$(arg use_position_controllers)\">"
CMD_INTERBOTIX_ROSPARAM_POSITION_CONTROLLERS_OPEN = "<rosparam file=\"$(find interbotix_xslocobot_gazebo)/config/position_controllers/$(arg arm_model)_position_controllers.yaml\" command=\"load\" ns=\""
CMD_INTERBOTIX_ROSPARAM_POSITION_CONTROLLERS_CLOSE = "\"/>"
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_4_OPEN = "<node if=\"$(eval dof == 4)\"\n        name=\"controller_spawner\"\n        pkg=\"controller_manager\"\n        type=\"controller_manager\"\n        respawn=\"false\"\n        output=\"screen\"\n        ns=\""
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_4_CLOSE = "\"\n        args=\"spawn joint_state_controller waist_controller shoulder_controller\n                    elbow_controller wrist_angle_controller left_finger_controller\n                    right_finger_controller pan_controller tilt_controller\"/>"
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_5_OPEN = "<node if=\"$(eval dof == 5)\"\n        name=\"controller_spawner\"\n        pkg=\"controller_manager\"\n        type=\"controller_manager\"\n        respawn=\"false\"\n        output=\"screen\"\n        ns=\""
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_5_CLOSE = "\"\n        args=\"spawn joint_state_controller waist_controller shoulder_controller\n                    elbow_controller wrist_angle_controller wrist_rotate_controller\n                    left_finger_controller right_finger_controller pan_controller\n                    tilt_controller\"/>"
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_6_OPEN = "<node if=\"$(eval dof == 6)\"\n        name=\"controller_spawner\"\n        pkg=\"controller_manager\"\n        type=\"controller_manager\"\n        respawn=\"false\"\n        output=\"screen\"\n        ns=\""
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_6_CLOSE = "\"\n        args=\"spawn joint_state_controller waist_controller shoulder_controller\n                    elbow_controller forearm_roll_controller wrist_angle_controller\n                    wrist_rotate_controller left_finger_controller right_finger_controller\n                    pan_controller tilt_controller\"/>"
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_UNLSESS_LOCOBOT_BASE_OPEN = "<node unless=\"$(eval robot_model != 'locobot_base')\"\n    name=\"controller_spawner\"\n    pkg=\"controller_manager\"\n    type=\"controller_manager\"\n    respawn=\"false\"\n    output=\"screen\"\n    ns=\""
CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_UNLSESS_LOCOBOT_BASE_CLOSE = "\"\n    args=\"spawn pan_controller tilt_controller joint_state_controller\"/>"
CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_OPEN = "<include file=\"$(find interbotix_xslocobot_descriptions)/launch/xslocobot_description.launch\">\n    <arg name=\"robot_model\"                       value=\"$(arg robot_model)\"/>\n    <arg name=\"robot_name\"                        value=\""
CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_MIDDLE = "\"/>\n    <arg name=\"show_lidar\"                        value=\"$(arg show_lidar)\"/>\n    <arg name=\"show_gripper_bar\"                  value=\"$(arg show_gripper_bar)\"/>\n    <arg name=\"show_gripper_fingers\"              value=\"$(arg show_gripper_fingers)\"/>\n    <arg name=\"external_urdf_loc\"                 value=\"$(arg external_urdf_loc)\"/>\n    <arg name=\"use_rviz\"                          value=\"$(arg use_rviz)\"/>\n    <arg name=\"rviz_frame\"                        value=\""
CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_CLOSE = "\"/>\n  </include>"
CMD_INTERBOTIX_NODE_URDF_SPAWNER_OPEN = "<node\n    name=\"urdf_spawner\"\n    pkg=\"gazebo_ros\"\n    type=\"spawn_model\"\n    respawn=\"false\"\n    output=\"screen\"\n    ns=\""
CMD_INTERBOTIX_NODE_URDF_SPAWNER_MIDDLE = "\"\n\t  args=\"-urdf -model "
CMD_INTERBOTIX_NODE_URDF_SPAWNER_CLOSE = " -param robot_description\"/>"

## uni
CMD_UNI_MODEL_NAME = "uni_base" 
CMD_UNI_DEFAULT_NAME = "uni"
CMD_UNI_COMMENT_START = "<!-- #### UNI050_BASE #### -->"
CMD_UNI_COMMENT_END = "<!-- #### UNI050_BASE End #### -->"
CMD_UNI_DEFAULT_NAME_POSITION_X = "_x_pos"
CMD_UNI_DEFAULT_NAME_POSITION_Y = "_y_pos"
CMD_UNI_DEFAULT_NAME_POSITION_Z = "_z_pos"
CMD_UNI_PARAM_NAME_ROBOT_DESCRIPTION = "<param name=\"robot_description\" command=\"$(find xacro)/xacro --inorder $(find uni_description)/urdf/uni_base.urdf.xacro\" />"
CMD_UNI_NODE_PKG_ROBOT_STATE_PUBLISHER = "<node name=\"robot_state_publisher\" pkg=\"robot_state_publisher\" type=\"robot_state_publisher\" />"
CMD_UNI_NODE_PKG_SPAWN_MODEL_OPEN = "<node pkg=\"gazebo_ros\" type=\"spawn_model\" name=\"spawn_urdf\" args=\"-urdf"
CMD_UNI_NODE_PKG_SPAWN_MODEL_CLOSE = "-param robot_description\" />"

###############################
############# ROS #############
###############################
## Common
CMD_ROS_SLAM_COMMENT_START = "<!-- #### ROS : Slam #### -->"
CMD_ROS_SLAM_COMMENT_END = "<!-- #### ROS : Slam End #### -->"
CMD_ROS_NAVIGATION_COMMENT_START = "<!-- #### ROS : Navigation #### -->"
CMD_ROS_NAVIGATION_COMMENT_END = "<!-- #### ROS : Navigation End #### -->"
CMD_ROS_NAVIGATION_COMMONET_RVIZ_START = "<!-- #### RViz : Navigation #### -->"
CMD_ROS_NAVIGATION_COMMONET_RVIZ_END = "<!-- #### RViz : Navigation End #### -->"
CMD_ROS_COMMON_EXPORT = "export"
CMD_ROS_COMMON_ROSRUN = "rosrun"
CMD_ROS_COMMON_ROSLAUNCH = "roslaunch"
CMD_ROS_COMMON_ROS_NAMESPACE = "ROS_NAMESPACE="
CMD_ROS_COMMON_CMD_VEL = "cmd_vel"
CMD_ROS_COMMON_NODE_NAME = "__name"
CMD_ROS_JNP = "jnp"
CMD_ROS_JNP_JNP_AGENT = "jnp_agent.py"
CMD_ROS_JNP_JNP_AGENT_NS = "__ns:="
CMD_ROS_JNP_JNP_AGENT_NS_DEFAULT = "etri"
CMD_ROS_JNP_JNP_AGENT_NAME = "__name:="

## Locobot
CMD_ROS_LOCOBOT_SAMPLE_LOAD_PYROBOT_ENV = "load_pyrobot_env"
CMD_ROS_LOCOBOT_SAMPLE_CD_CONTROL_NODES = "cd ~/low_cost_ws/src/pyrobot/robots/LoCoBot/locobot_control/nodes"
CMD_ROS_LOCOBOT_SAMPLE_TELEOP_EXCUTE_SERVER = "python robot_teleop_server.py"
CMD_ROS_LOCOBOT_SAMPLE_TELEOP_EXCUTE_CLIENT = "python keyboard_teleop_client.py"
CMD_ROS_LOCOBOT_TELEOP_TWIST_KEYBOARD_PKG = "teleop_twist_keyboard"
CMD_ROS_LOCOBOT_TELEOP_TWIST_KEYBOARD_PY = "teleop_twist_keyboard.py"

## Turtlebot3
CMD_ROS_TURTLEBOT3_MODEL = "TURTLEBOT3_MODEL="
CMD_ROS_TURTLEBOT3_TELEOP = "turtlebot3_teleop"
CMD_ROS_TURTLEBOT3_TELEOP_KEY = "turtlebot3_teleop_key"

## Slam
CMD_ROS_SLAM_TURTLEBOT3_SLAM = "turtlebot3_slam"
CMD_ROS_SLAM_TURTLEBOT3_SLAM_LAUNCH = "turtlebot3_slam.launch"
CMD_ROS_SLAM_TURTLEBOT3_GMAPPING_LAUNCH = "turtlebot3_gmapping.launch"
CMD_ROS_SLAM_TURTLEBOT3_SET_BASE_FRAME = "set_base_frame"
CMD_ROS_SLAM_TURTLEBOT3_BASE_FOORPRINT = "base_footprint"
CMD_ROS_SLAM_TURTLEBOT3_SET_ODOM_FRAME = "set_odom_frame"
CMD_ROS_SLAM_TURTLEBOT3_ODOM = "odom"
CMD_ROS_SLAM_TURTLEBOT3_SET_MAP_FRAME = "set_map_frame"
CMD_ROS_SLAM_TURTLEBOT3_MAP = "map"
CMD_ROS_SLAM_TURTLEBOT3_MULTI_MAP_MERGE_LAUNCH = "multi_map_merge.launch"
CMD_ROS_SLAM_TURTLEBOT3_RVIZ_FULL = "rosrun rviz rviz -d `rospack find turtlebot3_gazebo`/rviz/multi_turtlebot3_slam.rviz"

CMD_ROS_SLAM_METHOD = "slam_methods"
CMD_ROS_SLAM_METHOD_GMAPPING = "gmapping"
CMD_ROS_SLAM_MAP_SERVER = "map_server"
CMD_ROS_SLAM_MAP_SAVER = "map_saver"
CMD_ROS_SLAM_MAP_OPTION_FILE_PATH = "-f"

## Navigation
CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION = "turtlebot3_navigation"
CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_LAUNCH = "turtlebot3_navigation.launch"
CMD_ROS_NAVIGATION_MAP_FILE = "map_file"
CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_MPA_DEFAULT = "$(find turtlebot3_navigation)/maps/map.yaml"
CMD_ROS_NAVIGATION_TURTLEBOT3_INCLUDE_ONE_ROBOT_LAUNCH = "<include file=\"$(find turtlebot3_navigation)/launch/turtlebot3_navigation_with_gazebo_ns4_one_robot.launch\">"
CMD_ROS_NAVIGATION_ROBOT_NAME = "robot_name"
CMD_ROS_NAVIGATION_X_POS = "x_pos"
CMD_ROS_NAVIGATION_Y_POS = "y_pos"
CMD_ROS_NAVIGATION_Z_POS = "z_pos"
CMD_ROS_NAVIGATION_MOVE_FORWARD_ONLY = "move_forward_only"
CMD_ROS_NAVIGATION_MULTI_ROBOT_NAME = "multi_robot_name"
CMD_ROS_NAVIGATION_OPEN_RVIZ = "open_rviz"
CMD_ROS_NAVIGATION_RVIZ_PKG = "<node pkg=\"rviz\" type=\"rviz\" name=\"rviz\" required=\"true\" args=\"-d $(find turtlebot3_navigation)/rviz/turtlebot3_navigation_together.rviz\"/>"

###############################
############# ETC #############
###############################
CMD_EXCUTE_CMD_OPEN = "gnome-terminal -- bash -c \""
CMD_EXCUTE_CMD_CLOSE = ";bash\""
CMD__COMMON_CMD_OPEN_NO_SHOW = "\'"
CMD__COMMON_CMD_CLOSE_NO_SHOW = ">/dev/null 2>&1\'"
CMD_CLOSER_GZSERVER = "killall gzserver"

## System Setting
SETTING_COMPANY = "ETRI"
SETTING_APP = "ROSSimulator"
MAP_FOLDER_NAME = "Maps"
SETTING_PATH_SLAM_SAVED_MAP_PATH = "Saved_Slam_Map_Path"
SETTING_PATH_NAVIGATION_SAVED_MAP_PATH = "Saved_Navigation_Map_Path"
SETTING_DB_ID = "ID"
CONST_SETTING_DB_ID = "tesla"
SETTING_DB_PW = "PW"
CONST_SETTING_DB_PW = "test"
CONST_SETTING_DB_DEFAULT_HOST = "localhost"
CONST_SETTING_DB_DEFAULT_NAME = "test_db"
SETTING_PATH_DQN_WEIGHT = "Saved_DQN_Weight_Path"