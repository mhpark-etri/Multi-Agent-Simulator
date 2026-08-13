[🇰🇷 한국어](README.md) | **🇺🇸 English**

# Multi-Agent-Simulator v1.9
  <img src="https://github.com/user-attachments/assets/d64baddb-d154-4b10-8420-6c84a019a44e" width="70%" />

- Copyright (C) 2024-2026 ETRI. Licensed under the Apache License, Version 2.0 (see LICENSE). Third-party components and their licenses are listed in NOTICE.
- This software is a 3D simulator for learning multi-agents in virtual environments.
- You can download worlds or models at the following sites. After that, you should move them to the "worlds" or "models" directory.
  - https://github.com/gazebosim/gazebo-classic/tree/gazebo11/worlds
  - https://github.com/leonhartyao/gazebo_models_worlds_collection
  - https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps
  - https://github.com/osrf/gazebo_models
  - https://docs.px4.io/main/en/sim_gazebo_gz/worlds
  - https://github.com/PX4/PX4-SITL_gazebo-classic/tree/main/worlds
  - https://automaticaddison.com/useful-world-files-for-gazebo-and-ros-2-simulations/
  - https://data.nvision2.eecs.yorku.ca/3DGEMS/
  - https://github.com/eliabntt/gazebo_resources
- Any questions about our use of licensed work can be sent to dongoh@etri.re.kr

> [!NOTE]
> These worlds and models carry different licenses depending on the source. Before downloading
> or redistributing them, $\textsf{\color{red}{be sure to read Worlds, models and their licenses}}$.
> → [Go to that section](#worlds-models-and-their-licenses)

---
# Runtime environment
- Ubuntu 20.04
- Docker v24.0.7 or later

---
# Installation
### 1. Download the project
- Clone with Git, or download the whole project as a Zip archive.

### 2. Build the Docker image
- Open a terminal in the folder that contains the `Dockerfile` and run:
```
sudo docker build --no-cache -t img_mas .
```
- `img_mas` is just the image name; choose any name you like.
- Takes about 15-20 minutes.

### 3. Create the Docker container
- Open a terminal and run:
```
sudo docker run -it --gpus all --net=host --privileged \
--ipc=host --shm-size=2g \
-e DISPLAY=$DISPLAY \
-e XDG_RUNTIME_DIR=/tmp/runtime-root \
-e QT_X11_NO_MITSHM=1 \
-e NVIDIA_VISIBLE_DEVICES=all \
-e NVIDIA_DRIVER_CAPABILITIES=all \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v $HOME/.Xauthority:/root/.Xauthority:ro \
-v /mnt/Shared:/mnt \
--name ct_mas img_mas
```
- `ct_mas` is just the container name; choose any name you like.
- You enter the container once it has been created.

### 4. Install required packages
- Start the container created above and run the commands below in order.
```
cd
cd tesla
source init.sh
```

> **Which steps do I actually need?** (when using the Docker image)
>
> | Section | Content | Action |
> |---|---|---|
> | 4.1 | Interbotix installation | **Required** (answer `y` at the prompts) |
> | 4.2 | Build JnP 0.2.1 | **Required** |
> | 4.2.1 | JnP 0.8.1 | Not needed — already built by the image and `init.sh` |
> | 4.2.2 | Exploration stack | Not needed — already built by the image and `init.sh` |
> | 4.2.3 | YOLO | Optional — only for the Find Object task |
> | 4.3 / 4.4 | Ai-Bot / Stretch2 | Only if you use those robots |

### 4.1 Interbotix installation
- While the required packages are installed, the Interbotix installer appears. Answer `y` to each prompt.
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/871c7299-c07c-4e2d-8f92-1d1770b40e7d" width="50%" />
<br>
<br>
- When the installation finishes, enter `y` to exit the container.
<br>
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/f10a5d3e-70e4-4585-b752-0a818a33cc12" width="50%" />
<br><br>

### 4.2 JnP installation (required)
- Re-enter the container from an Ubuntu terminal (`ct_mas` is the container name used above).
```
sudo docker start -i ct_mas
```
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/641dd3a6-f908-4120-be77-02f07c291f39" width="50%" />
<br>
<br>
- Inside the container, build JnP with the commands below.

```
cd /root/catkin_ws_jnp
catkin_make
chmod +x /root/catkin_ws_jnp/src/jnp/scripts/jnp_agent.py
```
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/e07af797-ef12-4767-a422-4c191fd1f04e" width="50%" />
<br><br>

### 4.2.1 JnP 0.8.1 (v1.9 collaboration tasks) — reference only, no action needed

> The image and `init.sh` already build this. **You can skip it.**
> Read on only to rebuild after editing the source, or to set things up without the image.

- The v1.9 collaboration tasks run on JnP **0.8.1**.
  - Relay / Multi-Goal Move / Collision Avoidance / Distributed Search-Mapping / Distributed Search-Find Object
- To rebuild from source, run:

```
mkdir -p /root/catkin_ws_jnp081/src
ln -s /opt/ros/noetic/share/catkin/cmake/toplevel.cmake /root/catkin_ws_jnp081/src/CMakeLists.txt
ln -s /root/tesla/jnp/jnp_0.8.1 /root/catkin_ws_jnp081/src/jnp
cd /root/catkin_ws_jnp081 && catkin_make
```

### 4.2.2 Exploration stack (third_party) — reference only, no action needed

> The image and `init.sh` already build this. **You can skip it.**
> Read on only to rebuild after editing the source, or to set things up without the image.

**What it uses**

- Distributed Search (Mapping / Find Object) needs **frontier detection** and **map merging**.
- Both packages ship with this repository under `third_party/`.
- Each keeps its own upstream license → `NOTICE`, `third_party/README.md`

| Package | License | Role | apt package instead? |
| --- | --- | --- | --- |
| `rrt_exploration` | MIT (**modified**) | frontier detection and filtering | **No** — multi-robot parameters such as `~use_global_merged_map` were added |
| `map_merge` | BSD-3-Clause (upstream **2.1.5**, unmodified) | multi-robot map merging | **No** — the apt build (2.1.4) misaligns the merged map |

**Rebuilding inside the image**

- The sources are already copied to `/root/catkin_ws_explo/src/` and **built**.
- After editing them, run only:

```
cd /root/catkin_ws_explo
catkin_make -DCMAKE_BUILD_TYPE=Release
source /root/catkin_ws_explo/devel/setup.bash
```

**Setting it up without the image** (from a repository cloned on the host)
```
mkdir -p /root/catkin_ws_explo/src
cp -a <repository>/third_party/rrt_exploration /root/catkin_ws_explo/src/
cp -a <repository>/third_party/map_merge       /root/catkin_ws_explo/src/
sudo apt-get install -y python3-sklearn ros-noetic-slam-toolbox \
     ros-noetic-dwa-local-planner ros-noetic-global-planner ros-noetic-topic-tools
cd /root/catkin_ws_explo && catkin_make -DCMAKE_BUILD_TYPE=Release
echo "source /root/catkin_ws_explo/devel/setup.bash" >> /root/.bashrc
```

### 4.2.3 Object detection (YOLO) — optional (only for that task)
- Only the **Distributed Search-Find Object** task uses Ultralytics YOLOv8 for perception.
- Ultralytics and its pre-trained weights are **AGPL-3.0**, so they are **not included**
  in this Apache-2.0 repository or in the Docker image. Install them yourself inside the
  container if you want that task (every other task works without them).
```
pip3 install torch==2.4.1+cpu torchvision==0.19.1+cpu \
     --index-url https://download.pytorch.org/whl/cpu
pip3 install ultralytics                       # AGPL-3.0
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"   # download the weights
mv yolov8n.pt /root/yolov8n.pt
```
- After installing, pick **Distributed Search: Find Object** in the GUI's
  Behavior (Action) panel. Detections are shown in yellow above the map in RViz,
  and a popup shows the YOLO result (bounding box and confidence) at the moment of detection.

### 4.3 Ai-Bot installation
- Build Ai-Bot with the commands below.
```
cd /root/catkin_ws_ai_bot/
catkin_make
```
<img src="https://github.com/user-attachments/assets/66ad2411-201c-402f-ab46-c3c6c2e2a293" width="50%" />
<br><br>

### 4.4 Hello_Robot Stretch2 installation
- Create the workspace and copy the tutorial package.
```
cd
mkdir -p ~/catkin_ws_stretch2/src
cd ~/catkin_ws_stretch2
git clone https://github.com/hello-robot/stretch_tutorials.git
```
<img src="https://github.com/user-attachments/assets/55508fb9-d1de-4f0f-9d5d-b420cdcaf9c7" width="50%" />
<br><br>

- Initial build
```
catkin_make -DCATKIN_ENABLE_TESTING=OFF
```
<img src="https://github.com/user-attachments/assets/8cc461bf-375a-4a06-b191-8faa81bedf8b" width="50%" />
<br><br>

- Install the Realsense camera package (it may already be installed).
```
apt-get install ros-noetic-realsense2-camera
```
<img src="https://github.com/user-attachments/assets/b8cc655d-e96d-42dc-bf99-3595b9ff82b4" width="50%" />
<br><br>

- Clone the Stretch and Gazebo packages.
```
cd ~/catkin_ws_stretch2/src
git clone https://github.com/hello-robot/stretch_ros
git clone -b melodic-devel https://github.com/pal-robotics/realsense_gazebo_plugin
git clone https://github.com/hello-robot/stretch_tutorials.git
```
<img src="https://github.com/user-attachments/assets/2a02e079-9bb2-47dc-ae6c-e1a457d014a3" width="50%" />
<br><br>

- Install dependencies and build every package.
```
cd ~/catkin_ws_stretch2
rosdep install --from-paths src --ignore-src -r -y
catkin_make -DCATKIN_ENABLE_TESTING=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5
```
<img src="https://github.com/user-attachments/assets/c6d20058-19f3-45be-a686-f9b9df911ce4" width="50%" />
<br><br>

---
# Usage
### Running the program
  - Open a terminal, start the container, then run the commands below in order.
```
cd
cd tesla
cd code
cd Multi-Agent-Simulator
python3 main.py
```

<details>
  <summary>What to do if a display error occurs.</summary>
    <img src="https://github.com/etri-clara2/Multi-Agent-Simulator/assets/147698192/20c1c527-a696-42d7-85f6-caea933150bc" width="70%" />

  - If you see a display-related error like the one above, open an **Ubuntu terminal (not the Docker terminal)** and run:
```
  xhost +
```
  - Then run the program again.
</details>
<br>

### How to use the program
<img src="https://github.com/user-attachments/assets/00242774-51e8-4c2f-a77e-76ed0ae89952" width="70%" />

### 1. Select a world
   - Choose the virtual environment to run from the World panel.
### 2. Add robots
   - Press Add in the Robot panel to create agents.
### 3. Start
   - Press the Start button at the bottom right to run the virtual environment.

### 4. Collaboration tasks (v1.9)
   - Pick a task under **Collaboration Tasks** in the Behavior (Action) panel and press Start.
   - Available tasks: Relay / Multi-Goal Move / Collision Avoidance /
     Distributed Search-Mapping / Distributed Search-Find Object.
   - Choose `JnP 0.8.1` in the **Execution** combo box: the agents then form a
     coalition and carry out the task together.
   - **Nav Settings** button: set navigation parameters per task (speed, inflation
     radius, planner, and so on). Only the values you save apply to that task;
     everything else falls back to the global settings and then to the defaults.
   - **JnP Monitor**: shows the coalition and the task tree in real time
     (maximize from the title bar, or press F11 for full screen).

### Notes
  - A model file (.pkl) is required to run the Image-to-Image environment-enhancement feature.


# License
- The code in this repository is licensed under the **Apache License 2.0** (`LICENSE`).
- Third-party components (TurtleBot3, Interbotix, rrt_exploration, map_merge, Gazebo
  models) and their licenses are listed in **`NOTICE`**.
- Packages under `third_party/` keep their own upstream licenses (MIT / BSD-3-Clause);
  the modifications made here are described in `third_party/README.md`.
- **YOLO (Ultralytics)** is AGPL-3.0 and is not included in this repository or image.
  If you enable the Find Object task, AGPL-3.0 applies to that component.


---
# Worlds, models and their licenses

> Read this section **before downloading, using or redistributing** any world or model.
> It separates what is bundled in this repository from what is not, and flags what cannot be stated with confidence.

## What this repository ships

| Item | Origin | License |
| --- | --- | --- |
| `ros/navi/worlds/no_roof_small_warehouse.world` + `models/aws_robomaker_warehouse_*` (14) | [AWS RoboMaker Small Warehouse](https://github.com/aws-robotics/aws-robomaker-small-warehouse-world) | **MIT-0** — full text in `licenses/aws-robomaker-small-warehouse-world-MIT-0.txt` |
| the other three worlds in `ros/navi/worlds/` | authored in this repository (ETRI) | Apache-2.0 |
| `third_party/rrt_exploration` | [hasauino/rrt_exploration](https://github.com/hasauino/rrt_exploration) | MIT (modified) |
| `third_party/map_merge` | [hrnr/m-explore](https://github.com/hrnr/m-explore) | BSD-3-Clause |

See `NOTICE` for the details.

## AWS RoboMaker worlds (optional — not bundled)

The `Hospital › hospital` and `HouseCafe › small_house` entries in the World panel need a world file to
work. You can supply them from AWS RoboMaker. All three are **MIT-0 (MIT No Attribution)**, so they are
free to use and redistribute. They are not bundled here because of their size (about 230 MB in total).

| World | Repository | models size |
| --- | --- | --- |
| hospital | https://github.com/aws-robotics/aws-robomaker-hospital-world | 76 MB |
| small house | https://github.com/aws-robotics/aws-robomaker-small-house-world | 105 MB |
| bookstore | https://github.com/aws-robotics/aws-robomaker-bookstore-world | 48 MB |

There is no need to build them as ROS packages — just put the files where Gazebo already looks.
All three repositories have `archive` as their default branch and keep the files on `ros1`, so
**`-b ros1` is required** — cloning the default branch gets you only a README.

```bash
# example: hospital — change the repository name for the other two
git clone --depth 1 -b ros1 \
  https://github.com/aws-robotics/aws-robomaker-hospital-world.git /tmp/aws_hospital

cp -r /tmp/aws_hospital/models/*        ~/.gazebo/models/             # 3D models
cp    /tmp/aws_hospital/worlds/*.world  /usr/share/gazebo-11/worlds/  # world files
```

- To survive a container rebuild, copy into this repository's `models/` and `worlds/` instead — `init.sh` installs them to the same places.
- `bookstore` has no entry in the World panel, and adding one takes a code change: the panel is built from the world catalog assembled in `InitWorld()` in `code/Multi-Agent-Simulator/main.py`, not from the enum. Uncomment `BOOKSTORE` in `ENUM_WORLD_CATEGORY_SUB` (`simulator.py`) **and** append a matching `World_Sub` (with a thumbnail) to the catalog in `main.py`.
- For `Hospital › hospital_2_floors` / `hospital_3_floors` you must rename the files: AWS ships them as `hospital_two_floors.world` / `hospital_three_floors.world`.
- The collaboration tasks (Relay, Multi-Goal Move, Collision Avoidance, Distributed Search) do not use these worlds, so everything works without them.

## Caveats when downloading from public collections

These are the sites listed at the top of this README. **A collection's license is not necessarily the license of the individual files inside it.**

- [leonhartyao/gazebo_models_worlds_collection](https://github.com/leonhartyao/gazebo_models_worlds_collection) is a **collection assembled from several projects**. Its repository-root LICENSE is GPL-3.0, but the files inside come from the upstreams its own readme names in the `Source` section — 3DGEMS, RotorS, TU Delft, ARTI-Robots, Clearpath Robotics and Fetch Robotics — and **each original work follows its own upstream license** (Fetch and Clearpath declare BSD, RotorS declares ASL 2.0, TU Delft is GPL-3.0). That the collection root is GPL-3.0 is a different claim from the individual files having been relicensed under GPL, so check the upstream terms before redistributing. **The origin of each World-panel entry is shown by the `World Info` button in the GUI.**
- [mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps](https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps) re-hosts the AWS worlds. However **it ships no license file at all** (checked all 8 archives / 2,696 entries: zero `LICENSE`, `COPYING` or `NOTICE`). MIT-0 requires no attribution, so this is not a violation in itself — but **if you need the license on record, download from the AWS repositories.**
- In that same collection, `office` is labelled `AWS Office` but no public AWS repository could be found for it (zero hits across the 43 aws-robotics repositories and a GitHub search), and `factory` is merely labelled `Custom Factory`, which is not evidence that the collection maintainer holds its copyright. **The original author and the license of these two cannot be stated.**
- The two PX4 links target different Gazebo generations. [PX4-gazebo-models](https://github.com/PX4/PX4-gazebo-models) is BSD-3-Clause but ships **`.sdf` worlds for the new Gazebo (gz)**, which do not load in Gazebo Classic as-is. For Classic use the 19 `.world` files in [PX4-SITL_gazebo-classic](https://github.com/PX4/PX4-SITL_gazebo-classic/tree/main/worlds); that repository ships no `LICENSE` file, its `package.xml` declares BSD and its source headers carry Apache-2.0 — **confirm before redistributing.**
- The repository-level LICENSE of [osrf/gazebo_models](https://github.com/osrf/gazebo_models) is **CC BY 3.0**. Upstream acknowledges that the provenance of some individual models is not fully documented, so verify per model before redistributing any of them.
- The remaining sites (automaticaddison, 3DGEMS, eliabntt/gazebo_resources) **have not been license-checked.** This repository does not bundle anything from them.
