########################################################
## Teslasystem Co.,Ltd.                               ##
## 제작 : 박태순                                       ## 
## 설명 : 시뮬레이터에서 사용 될 데이터가 정의된 스크립트 ##
## 시뮬레이터 구조체 형태 ################################
## Simulator                                          ##
#### └ World                                         ##
#### └ Robot [n]                                   ####
####     └ Id                                      ####
####     └ RosNamespace                            ####
####     └ Type                                    ####
####     └ Position                                ####
####     └ Option                                  ####
########################################################

from enum import Enum

## CONST : Robot Thumb path & name ##
CONST_LOCOBOT_PATH = ":/thumbnail/Resources/thumbnail/icon_thumb_robot_locobot.png"
CONST_LOCOBOT_NAME = "LoCoBot"
CONST_TURTLEBOT3_BURGER_PATH = ":/thumbnail/Resources/thumbnail/icon_thumb_robot_turtlebot_burger.png"
CONST_TURTLEBOT3_BUTGER_NAME = "Turtlebot3 - Burger"
CONST_TURTLEBOT3_WAFFLE_PATH = ":/thumbnail/Resources/thumbnail/icon_thumb_robot_turtlebot_waffle.png"
CONST_TURTLEBOT3_WAFFLE_NAME = "Turtlebot3 - Waffle"
CONST_JETBOT_PATH = ""
CONST_JETBOT_NAME = "Jetbot"

## ENUM : World Type ##
class ENUM_WORLD(Enum):
    WAREHOUSE = 0                           ## Type : Warehouse
    HOSPITAL = 1                            ## Type : Hospital 
    SMALLHOUSE = 2                          ## Type : Small House
    BOOK_STORE = 3                          ## Type : Book Store

## ENUM : Robot Type ##  
class ENUM_ROBOT_TYPE(Enum):
    LOCOBOT = 0                             ## Type : Locobot
    TURTLEBOT3_BURGER = 1                   ## Type : Turtlebot3 Burger    
    TURTLEBOT3_WAFFLE = 2                   ## Type : Turtlebot3 Waffle
    JETBOT = 3                              ## Type : Jetbot

## ENUM : ROS Type ##
class ENUM_ROS_TYPE(Enum):
    NONE = 0                                ## Type : None
    SLAM = 1                                ## Type : Slam
    NAVIGATION = 2                          ## Type : Navigation

## ENUM : ROS Slam Method Type ##
class ENUM_ROS_SLAM_METHOD(Enum):
    GMAPPING = 0                            ## Type : Gmapping

## Class : Thumbnail list
class Thumb:
    thumbPath = ""
    thumbName = ""

## Class : Launch world
class World:
    type = ENUM_WORLD.WAREHOUSE             ## World : EnumType                 
    filePath = ""                           ## World : World File Path

## Class : Simulator option
class Option:
    ## Common
    camera = False                          ## Option : Use Camera
    arm = False                             ## Option : Locobot - Use Arm
    base = False                            ## Option : Locobot - Use base

## Class : Robot
class Robot:
    id = 0                                  ## Robot : ID
    rosNamespace = ""                       ## Robot : ROS Namespace
    type = ENUM_ROBOT_TYPE.LOCOBOT          ## Robot : Robot type
    startX = 0                              ## Robot : Start Posotion X (Default 0)
    startY = 0                              ## Robot : Start Position Y (Default 0)
    startZ = 0                              ## Robot : Start Position Z (Default 0, Fixed...)
    option = Option()                       ## Option : Robot options..

## Class : ROS

## Class : Simulator
class Simulator:
    worldType = ENUM_WORLD.WAREHOUSE      ## 사용할 월드
    robots = []                           ## 사용할 로봇들
    ros = ENUM_ROS_TYPE.NONE              ## 사용할 ROS
    def __init__(self):
        self.worldType = ENUM_WORLD.WAREHOUSE
        self.robots = []
        self.ros = ENUM_ROS_TYPE.NONE
