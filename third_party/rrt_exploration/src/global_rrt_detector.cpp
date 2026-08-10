#include "ros/ros.h"
#include "std_msgs/String.h"
#include <sstream>
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include "stdint.h"
#include "functions.h"
#include "mtrand.h"


#include "nav_msgs/OccupancyGrid.h"
#include "geometry_msgs/PointStamped.h"
#include "std_msgs/Header.h"
#include "nav_msgs/MapMetaData.h"
#include "geometry_msgs/Point.h"
#include "geometry_msgs/PolygonStamped.h"
#include "visualization_msgs/Marker.h"
#include <tf/transform_listener.h>



// global variables
nav_msgs::OccupancyGrid mapData;
geometry_msgs::PointStamped clickedpoint;
geometry_msgs::PointStamped exploration_goal;
visualization_msgs::Marker points,line;
float xdim,ydim,resolution,Xstartx,Xstarty,init_map_x,init_map_y;
bool g_boundary_ready = false;
float g_box_min_x = 0.f, g_box_max_x = 0.f, g_box_min_y = 0.f, g_box_max_y = 0.f;
float g_seed_x = 0.f, g_seed_y = 0.f;

rdm r; // for genrating random numbers



//Subscribers callback functions---------------------------------------
void mapCallBack(const nav_msgs::OccupancyGrid::ConstPtr& msg)
{
mapData=*msg;
}


 
void rvizCallBack(const geometry_msgs::PointStamped::ConstPtr& msg)
{ 

geometry_msgs::Point p;  
p.x=msg->point.x;
p.y=msg->point.y;
p.z=msg->point.z;

points.points.push_back(p);

}

void boundaryCallBack(const geometry_msgs::PolygonStamped::ConstPtr& msg)
{
  if (msg->polygon.points.size() < 3) {
    return;
  }
  float minx = 1e9f, maxx = -1e9f, miny = 1e9f, maxy = -1e9f;
  for (size_t i = 0; i < msg->polygon.points.size(); ++i) {
    const geometry_msgs::Point32& p = msg->polygon.points[i];
    minx = std::min(minx, p.x);
    maxx = std::max(maxx, p.x);
    miny = std::min(miny, p.y);
    maxy = std::max(maxy, p.y);
  }
  if (maxx <= minx || maxy <= miny) {
    return;
  }
  g_box_min_x = minx;
  g_box_max_x = maxx;
  g_box_min_y = miny;
  g_box_max_y = maxy;
  g_seed_x = 0.5f * (minx + maxx);
  g_seed_y = 0.5f * (miny + maxy);
  g_boundary_ready = true;
}




int main(int argc, char **argv)
{

  unsigned long init[4] = {0x123, 0x234, 0x345, 0x456}, length = 7;
  MTRand_int32 irand(init, length); // 32-bit int generator
// this is an example of initializing by an array
// you may use MTRand(seed) with any 32bit integer
// as a seed for a simpler initialization
  MTRand drand; // double in [0, 1) generator, already init

// generate the same numbers as in the original C test program
  ros::init(argc, argv, "global_rrt_frontier_detector");
  ros::NodeHandle nh;
  
  // fetching all parameters
  float eta,init_map_x,init_map_y,range;
  std::string map_topic,base_frame_topic;
  
  std::string ns;
  ns=ros::this_node::getName();

  ros::param::param<float>(ns+"/eta", eta, 0.5);
  ros::param::param<std::string>(ns+"/map_topic", map_topic, "/robot_1/map");
  bool use_exploration_boundary = true;
  std::string boundary_topic = "/exploration_boundary";
  ros::param::param<bool>(ns+"/use_exploration_boundary", use_exploration_boundary, true);
  ros::param::param<std::string>(ns+"/boundary_topic", boundary_topic, boundary_topic);
  std::string map_frame_id = "map";
  ros::param::param<std::string>(ns+"/map_frame", map_frame_id, map_frame_id);
//---------------------------------------------------------------
ros::Subscriber sub= nh.subscribe(map_topic, 100 ,mapCallBack);
ros::Subscriber rviz_sub;
ros::Subscriber boundary_sub;
if (use_exploration_boundary) {
  boundary_sub = nh.subscribe(boundary_topic, 10, boundaryCallBack);
  ROS_INFO(
      "global_rrt_detector: sampling from %s only (do NOT use /clicked_point for RRT)",
      boundary_topic.c_str());
} else {
  rviz_sub = nh.subscribe("/clicked_point", 100, rvizCallBack);
}	

ros::Publisher targetspub = nh.advertise<geometry_msgs::PointStamped>("/detected_points", 10);
ros::Publisher pub = nh.advertise<visualization_msgs::Marker>(ns+"_shapes", 10);

ros::Rate rate(100); 
 
 
// wait until map is received.
// ★ header.seq<1 조건 제거(2026-07-22): ROS1 의 첫 발행 메시지는 seq=0 이라, SLAM 이 지도를
//   한 번만 발행한 상태(로봇 정지 등)면 지도를 '받고도' 영원히 대기했다 — latched 재전달도
//   원본 seq=0 그대로라 재시작해도 못 벗어나는 영구 교착(실측: stretch_0 seq=0 vs 동작하던
//   로봇들 seq>=6). data.size() 만으로 수신 판정이 옳다.
while (ros::ok() && mapData.data.size()<1)  {  ros::spinOnce();  ros::Duration(0.1).sleep();}



//visualizations  points and lines..
points.header.frame_id=mapData.header.frame_id;
line.header.frame_id=mapData.header.frame_id;
points.header.stamp=ros::Time(0);
line.header.stamp=ros::Time(0);
	
points.ns=line.ns = "markers";
points.id = 0;
line.id =1;


points.type = points.POINTS;
line.type=line.LINE_LIST;

//Set the marker action.  Options are ADD, DELETE, and new in ROS Indigo: 3 (DELETEALL)
points.action =points.ADD;
line.action = line.ADD;
points.pose.orientation.w =1.0;
line.pose.orientation.w = 1.0;
line.scale.x =  0.12;
line.scale.y= 0.12;
points.scale.x=0.3; 
points.scale.y=0.3; 

line.color.r =9.0/255.0;
line.color.g= 91.0/255.0;
line.color.b =236.0/255.0;
points.color.r = 255.0/255.0;
points.color.g = 0.0/255.0;
points.color.b = 0.0/255.0;
points.color.a=1.0;
line.color.a = 1.0;
points.lifetime = ros::Duration(1.0);
line.lifetime = ros::Duration(1.0);

geometry_msgs::Point p;  


if (use_exploration_boundary) {
  ROS_INFO("global_rrt_detector: waiting for exploration boundary or 5 RViz clicks...");
  while (ros::ok() && !g_boundary_ready && points.points.size() < 5) {
    ros::spinOnce();
    if (points.points.size() > 0) {
      points.header.stamp = ros::Time::now();
      pub.publish(points);
    }
    ros::Duration(0.1).sleep();
  }
} else {
  while (points.points.size() < 5) {
    ros::spinOnce();
    if (points.points.size() > 0) {
      points.header.stamp = ros::Time::now();
      pub.publish(points);
    }
    ros::Duration(0.1).sleep();
  }
}

std::vector< std::vector<float>  > V;
std::vector<float> xnew;

if (g_boundary_ready) {
  init_map_x = g_box_max_x - g_box_min_x;
  init_map_y = g_box_max_y - g_box_min_y;
  const float map_min_x = mapData.info.origin.position.x;
  const float map_min_y = mapData.info.origin.position.y;
  const float map_max_x =
      map_min_x + mapData.info.width * mapData.info.resolution;
  const float map_max_y =
      map_min_y + mapData.info.height * mapData.info.resolution;
  const float sx = std::max(map_min_x, g_box_min_x);
  const float ex = std::min(map_max_x, g_box_max_x);
  const float sy = std::max(map_min_y, g_box_min_y);
  const float ey = std::min(map_max_y, g_box_max_y);
  if (ex > sx && ey > sy) {
    Xstartx = 0.5f * (sx + ex);
    Xstarty = 0.5f * (sy + ey);
    // ★ 샘플링 박스도 map∩boundary(+여유)로 좁힌다.
    //   박스는 아래에서 Xstart ± init_map*0.5 로 만들어지는데, init_map 을 '경계 전체'로
    //   두면 지도가 작을 때(예: 지도 5x8m vs 경계 26x18m) 샘플의 90% 이상이 지도 밖으로
    //   나가 버려져 트리가 자라지 못하고 /detected_points 가 전혀 안 나온다(로봇이 안 움직임).
    //   지도가 커지면 sx..ex 도 커지므로 박스가 자동으로 따라 커진다(탐사 진행에 문제 없음).
    const float sample_margin = 2.0f;   // 지도 가장자리 너머로 조금 더 뻗을 여유(m)
    init_map_x = std::min((ex - sx) + 2.0f * sample_margin,
                          g_box_max_x - g_box_min_x);
    init_map_y = std::min((ey - sy) + 2.0f * sample_margin,
                          g_box_max_y - g_box_min_y);
    ROS_INFO(
        "global_rrt_detector: RRT seed at map∩boundary center (%.2f, %.2f) "
        "[map %.2f,%.2f-%.2f,%.2f boundary %.2f,%.2f-%.2f,%.2f] "
        "sampling %.1fx%.1fm (map∩boundary+%.0fm)",
        Xstartx, Xstarty, map_min_x, map_min_y, map_max_x, map_max_y,
        g_box_min_x, g_box_min_y, g_box_max_x, g_box_max_y,
        init_map_x, init_map_y, sample_margin);
  } else {
    Xstartx = g_seed_x;
    Xstarty = g_seed_y;
    ROS_WARN(
        "global_rrt_detector: boundary does not overlap /map — RRT seed at "
        "boundary center (%.2f, %.2f); draw boundary around merged map",
        Xstartx, Xstarty);
  }
  xnew.push_back(Xstartx);
  xnew.push_back(Xstarty);
  V.push_back(xnew);
  ROS_INFO("global_rrt_detector: sampling box from boundary [%.2f,%.2f]-[%.2f,%.2f]",
           g_box_min_x, g_box_min_y, g_box_max_x, g_box_max_y);
} else {
  std::vector<float> temp1;
  temp1.push_back(points.points[0].x);
  temp1.push_back(points.points[0].y);

  std::vector<float> temp2;
  temp2.push_back(points.points[2].x);
  temp2.push_back(points.points[0].y);

  init_map_x = Norm(temp1, temp2);
  temp1.clear();
  temp2.clear();

  temp1.push_back(points.points[0].x);
  temp1.push_back(points.points[0].y);

  temp2.push_back(points.points[0].x);
  temp2.push_back(points.points[2].y);

  init_map_y = Norm(temp1, temp2);
  temp1.clear();
  temp2.clear();

  Xstartx = (points.points[0].x + points.points[2].x) * .5;
  Xstarty = (points.points[0].y + points.points[2].y) * .5;

  geometry_msgs::Point trans;
  trans = points.points[4];
  xnew.push_back(trans.x);
  xnew.push_back(trans.y);
  V.push_back(xnew);
  ROS_INFO("global_rrt_detector: sampling box from 5 RViz clicks");
}

points.points.clear();







std::vector<float> frontiers;
int i=0;
float xr,yr;
std::vector<float> x_rand,x_nearest,x_new;

const size_t kMaxLinePoints = 120;
// const size_t kMaxTreeNodes = 200;  // V cap disabled: keep global tree nodes
int loop_count = 0;

// Main loop
while (ros::ok()){
loop_count++;
ros::spinOnce();

// Sample only inside published map (intersected with user click box)
float map_min_x = mapData.info.origin.position.x;
float map_min_y = mapData.info.origin.position.y;
float map_max_x = map_min_x + mapData.info.width * mapData.info.resolution;
float map_max_y = map_min_y + mapData.info.height * mapData.info.resolution;
float box_min_x, box_max_x, box_min_y, box_max_y;
if (g_boundary_ready) {
  box_min_x = g_box_min_x;
  box_max_x = g_box_max_x;
  box_min_y = g_box_min_y;
  box_max_y = g_box_max_y;
} else {
  box_min_x = Xstartx - init_map_x * 0.5f;
  box_max_x = Xstartx + init_map_x * 0.5f;
  box_min_y = Xstarty - init_map_y * 0.5f;
  box_max_y = Xstarty + init_map_y * 0.5f;
}
float sx = std::max(map_min_x, box_min_x);
float ex = std::min(map_max_x, box_max_x);
float sy = std::max(map_min_y, box_min_y);
float ey = std::min(map_max_y, box_max_y);
if (ex <= sx || ey <= sy) {
  ROS_WARN_THROTTLE(
      15.0,
      "global_rrt_detector: sampling box does not overlap /map — "
      "draw the 4-point boundary around robots AND merged map (not only old map tile)");
  rate.sleep();
  continue;
}

x_rand.clear();
xr = sx + drand() * (ex - sx);
yr = sy + drand() * (ey - sy);

x_rand.push_back( xr ); x_rand.push_back( yr );


// Nearest
x_nearest=Nearest(V,x_rand);

// Steer

x_new=Steer(x_nearest,x_rand,eta);


// ObstacleFree    1:free     -1:unkown (frontier region)      0:obstacle
char   checking=ObstacleFree(x_nearest,x_new,mapData);

	  if (checking==-1){
          	exploration_goal.header.stamp=ros::Time(0);
          	exploration_goal.header.frame_id=map_frame_id;
          	exploration_goal.point.x=x_new[0];
          	exploration_goal.point.y=x_new[1];
          	exploration_goal.point.z=0.0;
          	p.x=x_new[0]; 
			p.y=x_new[1]; 
			p.z=0.0;
          	points.points.push_back(p);
          	points.header.stamp=ros::Time::now();
          	pub.publish(points);
          	targetspub.publish(exploration_goal);
		  	points.points.clear();
		  	// Prevent RViz LINE_LIST from growing without bound (looks like RRT fills unknown space)
		  	line.points.clear();
        	
        	}
	  	
	  
	  else if (checking==1){
	 	V.push_back(x_new);
	 	
	 	p.x=x_new[0]; 
		p.y=x_new[1]; 
		p.z=0.0;
	 	line.points.push_back(p);
	 	p.x=x_nearest[0]; 
		p.y=x_nearest[1]; 
		p.z=0.0;
	 	line.points.push_back(p);
	 	// Cap RViz LINE_LIST size (else unknown area fills with stale blue segments)
	 	if (line.points.size() > kMaxLinePoints) {
	 	  line.points.clear();
	 	}
	 	// Keep V growing; only line is cleared for RViz (see frontier / caps above).
	 	// if (V.size() > kMaxTreeNodes) {
	 	//   std::vector<float> root = V[0];
	 	//   V.clear();
	 	//   V.push_back(root);
	 	//   line.points.clear();
	 	// }

	        }

if (loop_count % 300 == 0) {
  visualization_msgs::Marker del;
  del.header = line.header;
  del.ns = line.ns;
  del.action = visualization_msgs::Marker::DELETEALL;
  pub.publish(del);
  line.points.clear();
}

if (line.points.size() >= 2)
{
line.header.stamp=ros::Time::now();
line.header.frame_id=mapData.header.frame_id;
line.action = visualization_msgs::Marker::ADD;
pub.publish(line);
}

rate.sleep();
  }return 0;}
