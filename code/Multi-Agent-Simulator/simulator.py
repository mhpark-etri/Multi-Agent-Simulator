########################################################
## Teslasystem Co.,Ltd.                               ##
## 제작 : 박태순                                       ## 
## 설명 : 시뮬레이터에서 사용 될 데이터가 정의된 스크립트 ##
## 시뮬레이터 구조체 형태 ################################
## Simulator                                          ##
#### └ World                                         ##
#### └ Robot [n]                                   ####
####     └ Id                                      ####
####     └ Name                                    ####
####     └ Type                                    ####
####     └ Position                                ####
####     └ Option                                  ####
########################################################

from enum import Enum
from dataclasses import dataclass

## CONST : Robot Thumb path & name ##
CONST_LOCOBOT_PATH = "Resources/thumbnail/icon_thumb_robot_locobot.png"
CONST_LOCOBOT_NAME = "LoCoBot"
CONST_TURTLEBOT3_BURGER_PATH = "Resources/thumbnail/icon_thumb_robot_turtlebot_burger.png"
CONST_TURTLEBOT3_BUTGER_NAME = "Turtlebot3 - Burger"
CONST_TURTLEBOT3_WAFFLE_PATH = "Resources/thumbnail/icon_thumb_robot_turtlebot_waffle.png"
CONST_TURTLEBOT3_WAFFLE_NAME = "Turtlebot3 - Waffle"
CONST_JETBOT_PATH = ""
CONST_JETBOT_NAME = "Jetbot"
CONST_INTERBOTIX_PATH = "Resources/thumbnail/icon_thumb_robot_interbotix_wx250s.png"
CONST_INTERBOTIX_NAME = "Locobot - wx250s"
CONST_UNI_PATH = "Resources/thumbnail/icon_thumb_robot_uni.png"
CONST_UNI_NAME = "UNI050_BASE"

# extention
CONST_EXTENTION_WORLD = ".world"
CONST_EXTENTION_MODEL = ".model"

## ENUM : World type : main category ##
class ENUM_WORLD_CATEGORY_MAIN(Enum):
    HOUSE_CAFE = "HouseCafe"
    OFFICE = "Office"
    HOSPITAL = "Hospital"
    WAREHOUSE = "Warehouse"
    FACTORY = "Factory"
    BOOKSTORE = "Bookstore"
    OTHERS = "Others"
    CUSTOM = "Custom"
    NONE = "None"

## ENUM : World type : sub category ##
# 주석 처리된 맵들은 현재 동작하지 않는 맵
class ENUM_WORLD_CATEGORY_SUB(Enum):
    CAFE = "cafe"
    SMALL_HOUSE = "small_house"
    # HOUSE = "house"
    OFFICE_CPR = "office_cpr"
    OFFICE_CPR_CONSTRUCTION = "office_cpr_construction"
    # OFFICE_ENV_LARGE = "office_env_large"
    OFFICE_SMALL = "office_small"
    OFFICE = "office"
    # OFFCE_EARTHQUAKE = "office_earthquake"
    HOSPITAL = "hospital"
    HOSPITAL_2_FLOORS = "hospital_2_floors"
    HOISPITAL_3_FLOORS = "hospital_3_floors"
    FETCHIT_CHALLENGE_ARENA_MONTREAL2019 = "fetchit_challenge_arena_montreal2019"
    FETCHIT_CHALLENGE_ARENA_MONTREAL2019_HIGHTLIGHTS = "fetchit_challenge_arena_montreal2019_highlights"
    FETCHIT_CHALLENGE_ARENA_MONTREAL2019_ONLYLIGHTS = "fetchit_challenge_arena_montreal2019_onlylights"
    FETCHIT_CHALLENGE_ASSEMBLY = "fetchit_challenge_assembly"
    FETCHIT_CHALLENGE_ATREZZO = "fetchit_challenge_atrezzo"
    FETCHIT_CHALLENGE_SIMPLE = "fetchit_challenge_simple"
    FETCHIT_CHALLENGE_SIMPLE_HIGHLIGHTS = "fetchit_challenge_simple_highlights"
    FETCHIT_CHALLENGE_TESTS = "fetchit_challenge_tests"
    FETCHIT_CHALLENGE_TESTS_LOWLIGHTS = "fetchit_challenge_tests_lowlights"
    WAREHOUSE = "warehouse"
    INVENTORY = "inventory"
    CYBERZOO = "cyberzoo"
    CYBERZOO2019_ORANGE_POLES = "cyberzoo2019_orange_poles"
    CYBERZOO2019_ORANGE_POLES_PANELS = "cyberzoo2019_orange_poles_panels"
    CYBERZOO2019_RALPHTHESIS2020 = "cyberzoo2019_ralphthesis2020"
    CYBERZOO_4_PANELS = "cyberzoo_4_panels"
    CYBERZOO_ORANGE_POLES = "cyberzoo_orange_poles"
    CYBERZOO_PANEL = "cyberzoo_panel"
    POWERPLANT = "powerplant"
    WORKSHOP_EXAMPLE = "workshop_example"
    FACTORY = "factory"
    # BOOKSTORE = "bookstore"
    ORSF_ELVATOR = "osrf_elevator"
    WILLOWGARAGE = "willowgarage"
    TESTZONE = "testzone"
    # DYNAMIC_WORLD = "dynamic_world"
    # EXPERIMENT_ROOM = "experiment_room"
    # RANDOM_WORLD = "random_world"
    DISTRIBUTION_CENTER = "distribution_center"
    COLLABORATION = "collaboration"
    NONE = "None"

## ENUM : World Type ##
class ENUM_WORLD(Enum):
    GAZEBO_DEFAULT = 0                      ## Type : Gazebo Default World
    WAREHOUSE = 1                           ## Type : AWS Warehouse
    HOSPITAL = 2                            ## Type : AWS Hospital 
    SMALLHOUSE = 3                          ## Type : AWS Small House
    BOOK_STORE = 4                          ## Type : AWS Book Store

## ENUM : Robot Type ##  
class ENUM_ROBOT_TYPE(Enum):
    LOCOBOT = 0                             ## Type : Locobot
    TURTLEBOT3_BURGER = 1                   ## Type : Turtlebot3 Burger    
    TURTLEBOT3_WAFFLE = 2                   ## Type : Turtlebot3 Waffle
    JETBOT = 3                              ## Type : Jetbot
    INTERBOTIX = 4                          ## Type : Interbotix
    UNI050_BASE = 5                         ## Type : UNI050_BASE

## ENUM : ROS Type ##
class ENUM_ROS_TYPE(Enum):
    NONE = 0                                ## Type : None
    SLAM = 1                                ## Type : Slam
    NAVIGATION = 2                          ## Type : Navigation

## ENUM : ROS Slam Method Type ##
class ENUM_ROS_NAVIGATION_SLAM_METHOD(Enum):
    GMAPPING = 0                            ## Type : Gmapping

## ENUM : ROS Collaboration Task ##
class ENUM_ROS_COLLABORATION_TASK_TYPE(Enum):
    NONE = "None"
    RELAY = "Relay"
    MOVE = "다목적 이동"
    AVOIDANCE = "충돌회피"
    SEARCH_FIND = "분산 탐색(물건 찾기)"
    SEARCH_MAKE_MAP = "분산 탐색(지도 제작)"

## Class : Thumbnail list
class Thumb:
    thumbPath = ""
    thumbName = ""

## Class : Launch world
class World:
    categoryMain = ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE              ## WorldTypeMain
    arrCategorySubs = []                                            ## WorldTypeSubs

    def __init__(self):
        self.categoryMain = ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE
        self.arrCategorySubs = []

class World_Sub:
    categorySub = ENUM_WORLD_CATEGORY_SUB.CAFE                      ## WorldTypeSub
    thumbPath = ""                                                  ## Thumbnail image path
    robotStartXYZ = []                                              ## Starting point robot xyz : ex(x1,y1,z1, x2,y2,z2 ...... xn,yn,zn)
    extention = ""                                                  ## File extention.. ex(.world or .model)

    def __init__(self):
        self.categorySub = ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE
        self.thumbPath = ""
        self.robotStartXYZ = []

## Class : Simulator option
class Option:
    ## Common
    camera = False                          ## Option : Use Camera
    arm = False                             ## Option : Locobot - Use Arm
    base = False                            ## Option : Locobot - Use base

## Class : Robot
class Robot:
    id = 0                                  ## Robot : ID
    name = ""                               ## Robot : Model name
    type = ENUM_ROBOT_TYPE.LOCOBOT          ## Robot : Robot type
    startX = 0                              ## Robot : Start Posotion X (Default 0)
    startY = 0                              ## Robot : Start Position Y (Default 0)
    startZ = 0                              ## Robot : Start Position Z (Default 0, Fixed...)
    option = Option()                       ## Robot : Robot options..
    moveToX = 0                             ## Robot : Collaboration Task Goal Position X (Default 0)
    moveToY = 0                             ## Robot : Collaboration Task Goal Position Y (Default 0)
    moveToZ = 0                             ## Robot : Collaboration Task Goal Position Z (Default 0, Fixed...)

## DataClass : ROS Collaboration task
@dataclass
class ROSCollaborationTask :
    type : ENUM_ROS_COLLABORATION_TASK_TYPE
    thumbPath : str

## Class : Worlds
## Class : Simulator
class Simulator:
    worldType = ENUM_WORLD.GAZEBO_DEFAULT                       ## 구버전 월드, 남겨둔 이유는 AWS 시리즈는 특수한 방법으로 빌드를 하여야 하기 때문에 트리거를 남겨둠(AWS사용시 사용하던 코드로 현재는 GAZEBO_DEFAULT만 사용)
    worldFileType = ""                                          ## 월드 파일의 확장자 (.world or .model)
    categoryMain = ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE          ## 현재 선택된 World의 상위 카테고리
    categorySub = ENUM_WORLD_CATEGORY_SUB.CAFE                  ## 현재 선택된 World의 하위 카테고리
    robots = []                                                 ## 사용할 로봇들
    ros = ENUM_ROS_TYPE.NONE                                    ## 사용할 ROS 타입
    ros_collaboration = ENUM_ROS_COLLABORATION_TASK_TYPE.NONE   ## 사용할 ROS Collaboration 타입
    ros_navigation_map_path = ""                                ## 사용할 ROS Collaboration 에서 쓸 네비게이션 맵 파일 경로
    launchFileName = ""                                         ## 현재 실행중인 launchFile의 이름
    addedLunchFileNumber = 0                                    ## 실행 이후 추가된 launchFile의 번호
    def __init__(self):
        self.worldType = ENUM_WORLD.GAZEBO_DEFAULT
        self.worldFileType = ".world"
        self.categoryMain = ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE
        self.categorySub = ENUM_WORLD_CATEGORY_SUB.CAFE 
        self.robots = []
        self.ros = ENUM_ROS_TYPE.NONE
