# ARM_DEVICE_ID can be found with 'ls /dev/serial/by-id' or by looking at the station config.

# docker build . -t run_aloha -f ./run.Dockerfile
# docker run --rm -it --network=host -v /etc:/etc -v /dev:/dev -v /var:/var -v /usr:/usr -v .:/home/aloha --privileged --device=/dev/dri/renderD128 -v /dev/dri:/dev/dri --device=/dev/snd run_aloha /bin/bash


# # 
# SUBSYSTEM=="tty", ATTRS{serial}=="FT88YWED", ENV{ID_MM_DEVICE_IGNORE}="1", ATTR{device/latency_timer}="1", SYMLINK+="ttyDXL_master_right"
# SUBSYSTEM=="tty", ATTRS{serial}=="FT8J0X80", ENV{ID_MM_DEVICE_IGNORE}="1", ATTR{device/latency_timer}="1", SYMLINK+="ttyDXL_master_left"
# SUBSYSTEM=="tty", ATTRS{serial}=="FT88YQRC", ENV{ID_MM_DEVICE_IGNORE}="1", ATTR{device/latency_timer}="1", SYMLINK+="ttyDXL_puppet_right"
# SUBSYSTEM=="tty", ATTRS{serial}=="FT88YXQH", ENV{ID_MM_DEVICE_IGNORE}="1", ATTR{device/latency_timer}="1", SYMLINK+="ttyDXL_puppet_left"
# SUBSYSTEM=="video4linux", ATTRS{serial}=="130523070912", ATTR{index}=="0", ATTRS{idProduct}=="0b5b", ATTR{device/latency_timer}="1", SYMLINK+="CAM_RIGHT_WRIST"
# SUBSYSTEM=="video4linux", ATTRS{serial}=="133323070799", ATTR{index}=="0", ATTRS{idProduct}=="0b5b", ATTR{device/latency_timer}="1", SYMLINK+="CAM_LEFT_WRIST"
# SUBSYSTEM=="video4linux", ATTRS{serial}=="128223070599", ATTR{index}=="0", ATTRS{idProduct}=="0b5b", ATTR{device/latency_timer}="1", SYMLINK+="CAM_LOW"
# SUBSYSTEM=="video4linux", ATTRS{serial}=="133323070708", ATTR{index}=="0", ATTRS{idProduct}=="0b5b", ATTR{device/latency_timer}="1", SYMLINK+="CAM_HIGH"

# docker run --rm -it --network=host -v .:/home/aloha --privileged run_aloha /bin/bash

# FROM ubuntu:20.04
FROM ros:noetic-robot@sha256:0e12e4db836e78c74c4b04c6d16f185d9a18d2b13cf5580747efa075eb6dc6e0
SHELL ["/bin/bash", "-c"]

RUN source /root/.bashrc

# FROM osrf/ros:noetic-desktop-full@sha256:cae9db690397b203c7d000149b17f88f3896a8240bd92a005176460cc73dfe28

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ## TODO: potentially install the next 3 later.
    ros-noetic-usb-cam \
    ros-noetic-cv-bridge \
    curl \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    whiptail \ 
    git

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends keyboard-configuration


ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /root
RUN curl 'https://raw.githubusercontent.com/Interbotix/interbotix_ros_manipulators/main/interbotix_ros_xsarms/install/amd64/xsarm_amd64_install.sh' > xsarm_amd64_install.sh 
RUN  chmod +x xsarm_amd64_install.sh 
RUN export DEBIAN_FRONTEND=noninteractive && export TZ='America/Los_Angeles' && ./xsarm_amd64_install.sh -d noetic -n

RUN cd /root/interbotix_ws/src && git clone https://github.com/tonyzhaozh/aloha
RUN cd /root/interbotix_ws && source /opt/ros/noetic/setup.sh && source /root/interbotix_ws/devel/setup.sh && catkin_make

RUN sudo service udev restart && sudo udevadm control --reload && sudo udevadm trigger
# # FINALLY GOT THESE TO WORK
# RUN rm /etc/ros/rosdep/sources.list.d/20-default.list
# RUN rosdep init
# RUN rosdep update --include-eol-distros


# RUN /bin/bash -c 'source /opt/ros/noetic/setup.bash'



# RUN mkdir -p /home/aloha/interbotix_ws/src
# # WORKDIR /home/aloha/interbotix_ws
# # RUN catkin_make   ## NOT SURE ABOUT THIS

# # shopt -s extglob



# cd /home/aloha/interbotix_ws/src

# git clone -b noetic https://github.com/Interbotix/interbotix_ros_core.git
#     git clone -b noetic https://github.com/Interbotix/interbotix_ros_manipulators.git
#     git clone -b noetic https://github.com/Interbotix/interbotix_ros_toolboxes.git

#     rm                                                                                              \
#     interbotix_ros_core/interbotix_ros_xseries/CATKIN_IGNORE                                      \
#     interbotix_ros_manipulators/interbotix_ros_xsarms/CATKIN_IGNORE                               \
#     interbotix_ros_toolboxes/interbotix_xs_toolbox/CATKIN_IGNORE                                  \
#     interbotix_ros_toolboxes/interbotix_common_toolbox/interbotix_moveit_interface/CATKIN_IGNORE

#     rm                                                                                            \
#     interbotix_ros_manipulators/interbotix_ros_xsarms/interbotix_xsarm_perception/CATKIN_IGNORE \
#     interbotix_ros_toolboxes/interbotix_perception_toolbox/CATKIN_IGNORE




#     cd interbotix_ros_core/interbotix_ros_xseries/interbotix_xs_sdk
#     sudo cp 99-interbotix-udev.rules /etc/udev/rules.d/


# ## ADDED THIS (then prints out Starting version 249.11-0ubuntu3.12)
#     /lib/systemd/systemd-udevd --daemon 

#     udevadm control --reload-rules && udevadm trigger
#     cd /home/aloha/interbotix_ws

#     rosdep install --from-paths src --ignore-src -r -y



# ### WAS MISSINNG RVIZ ON CATKIN MAKE, so tried this
# apt-get install librviz-dev rviz





    # catkin_make

    # RUN /bin/bash -c 'source /home/aloha/interbotix_ws/devel/setup.bash' 












    



####################### EVERYTHING BELOW THIS MIGHT NOT BE NEEDED ##########################

# # Chelsea: removed catkin bc already installed, also removed python3-rosdep2
# RUN apt-get install -y  git g++ python3-pip apt-file
# RUN apt-file update
# RUN ln -s /usr/bin/python3 /usr/bin/python

# apt-get install -y  git g++ python3-pip apt-file 
# apt-file update

# ln -s /usr/bin/python3 /usr/bin/python


# python3 -m pip install modern_robotics







# https://github.com/Interbotix/interbotix_ros_manipulators.git


# WORKDIR /home/aloha/interbotix_ws/src
# git clone -b noetic https://github.com/Interbotix/interbotix_ros_core.git
# git clone -b noetic https://github.com/Interbotix/interbotix_ros_manipulators.git
# git clone -b noetic https://github.com/Interbotix/interbotix_ros_toolboxes.git
# rm interbotix_ros_core/interbotix_ros_xseries/CATKIN_IGNORE    
# rm interbotix_ros_manipulators/interbotix_ros_xsarms/CATKIN_IGNORE       
# rm interbotix_ros_toolboxes/interbotix_xs_toolbox/CATKIN_IGNORE         
# rm interbotix_ros_toolboxes/interbotix_common_toolbox/interbotix_moveit_interface/CATKIN_IGNORE
# cd interbotix_ros_core/interbotix_ros_xseries/interbotix_xs_sdk

# cp 99-interbotix-udev.rules /etc/udev/rules.d/ 

# apt-get install udev

## NOTE: I added the first part from the internet, and not sure if it messes things up. (but it made an error disappear)
# /lib/systemd/systemd-udevd --daemon && udevadm control --reload-rules
# udevadm trigger

# WORKDIR /home/aloha/interbotix_ws
# RUN rosdep install --from-paths src --ignore-src -r -y









# # Chelsea: I don't know if all of these are needed. I removed libgazebo9-dev
# RUN apt install -y joint-state-publisher librobot-state-publisher-dev python3-roslaunch librviz-dev rviz ros-std-msgs libactionlib-msgs-dev libtrajectory-msgs-dev ros-trajectory-msgs ros-actionlib-msgs libdynamic-reconfigure-config-init-mutex-dev ros-shape-msgs libshape-msgs-dev ros-sensor-msgs libfcl-dev librandom-numbers-dev librandom-numbers0d libassimp-dev libboost-python-dev librviz4d python3-trajectory-msgs xvfb strace

# # xacro
# WORKDIR /home/aloha/interbotix_ws
# RUN git clone https://github.com/ros/xacro.git
# WORKDIR /home/aloha/interbotix_ws/xacro
# RUN cmake . && make && make install
# RUN pip3 install .

# # ros_control
# WORKDIR /home/aloha/interbotix_ws
# RUN git clone https://github.com/ros-controls/ros_control.git
# WORKDIR /home/aloha/interbotix_ws/ros_control/hardware_interface
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_control/controller_interface
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_control/controller_manager_msgs
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_control/controller_manager
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_control/transmission_interface
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_control/joint_limits_interface
# RUN cmake . && make && make install


# # ros_controllers
# WORKDIR /home/aloha/interbotix_ws
# RUN git clone https://github.com/ros-controls/ros_controllers.git

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/effort_controllers
# RUN git clone https://github.com/ros-controls/control_msgs.git
# WORKDIR /root/interbotix_ws/ros_controllers/effort_controllers/control_msgs/control_msgs
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/effort_controllers
# RUN git clone https://github.com/ros-controls/control_toolbox.git

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/effort_controllers/control_toolbox
# RUN git clone https://github.com/ros-controls/realtime_tools.git
# WORKDIR /root/interbotix_ws/ros_controllers/effort_controllers/control_toolbox/realtime_tools
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/effort_controllers/control_toolbox
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/forward_command_controller
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/effort_controllers
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/joint_state_controller
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/ros_controllers/joint_trajectory_controller
# RUN cmake . && make && make install


# # dynamixel
# WORKDIR /home/aloha/interbotix_ws
# RUN git clone https://github.com/ROBOTIS-GIT/dynamixel-workbench.git

# WORKDIR /home/aloha/interbotix_ws/dynamixel-workbench/dynamixel_workbench_toolbox
# RUN git clone https://github.com/ROBOTIS-GIT/DynamixelSDK.git
# WORKDIR /home/aloha/interbotix_ws/dynamixel-workbench/dynamixel_workbench_toolbox/DynamixelSDK/ros
# RUN cmake . && make && make install

# WORKDIR /home/aloha/interbotix_ws/dynamixel-workbench/dynamixel_workbench_toolbox
# RUN cmake . && make && make install

# # move deps away
# WORKDIR /home/aloha/interbotix_ws/deps
# RUN  ../ros_controllers/ ../xacro/ ../ros_control/ ../dynamixel-workbench/  ./
# # mv  ../gazebo_ros_pkgs/ ../rqt_plot/ ../roslint/ ../moveit/


# WORKDIR /home/aloha/interbotix_ws
# RUN catkin_make

# RUN /bin/bash -c 'source /home/aloha/interbotix_ws/devel/setup.bash' 
# # >> /root/.bashrc

# RUN ln -s /home/aloha/interbotix_ws/deps/xacro /home/aloha/interbotix_ws/src/
# RUN ln -s /usr/local/bin/xacro /root/interbotix_ws/src/xacro/
# RUN ln -s /home/aloha/interbotix_ws/deps/dynamixel-workbench/dynamixel_workbench_toolbox/DynamixelSDK/ros/devel/lib/libdynamixel_sdk.so /usr/lib






# Following instructions here: https://docs.trossenrobotics.com/interbotix_xsarms_docs/ros_interface/ros1/software_setup.html

# curl 'https://raw.githubusercontent.com/Interbotix/interbotix_ros_manipulators/main/interbotix_ros_xsarms/install/amd64/xsarm_amd64_install.sh' > xsarm_amd64_install.sh
# chmod +x xsarm_amd64_install.sh
# ./xsarm_amd64_install.sh -d noetic


# The above doesn't work. This seems promising:
# https://github.com/Lukorr/interbotix-ros/blob/master/Dockerfile



# RUN /bin/bash -c 'source /opt/ros/noetic/setup.bash && \
#         cd $ARM_ROOT && \
#         catkin_make -DYPYTHON_EXECUABLE=/usr/bin/python3'
