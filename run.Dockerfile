# ARM_DEVICE_ID can be found with 'ls /dev/serial/by-id' or by looking at the station config.

# docker run --rm -it --network=host -v /home/pi28/code/aloha:/root/interbotix_ws/src/aloha --privileged run_aloha /bin/bash

# FROM ubuntu:20.04
FROM ros:noetic-robot@sha256:0e12e4db836e78c74c4b04c6d16f185d9a18d2b13cf5580747efa075eb6dc6e0
SHELL ["/bin/bash", "-c"]

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

RUN cd /root/interbotix_ws/src && git clone git@github.com:Physical-Intelligence/aloha.git
RUN cd /root/interbotix_ws && source /opt/ros/noetic/setup.sh && source /root/interbotix_ws/devel/setup.sh && catkin_make

## Copies over this robot config
RUN cp /root/interbotix_ws/src/aloha/uvdev_configs/99-fixed-interbotix-udev.rules /etc/udev/rules.d/99-fixed-interbotix-udev.rules
RUN sudo service udev restart && sudo udevadm control --reload && sudo udevadm trigger
