import math
import rospy
import numpy as np
import modern_robotics as mr
from interbotix_xs_msgs.msg import *
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
import interbotix_common_modules.angle_manipulation as ang
import interbotix_xs_modules.mr_descriptions as mrd
from interbotix_xs_modules.core import InterbotixRobotXSCore
from interbotix_xs_modules.gripper import InterbotixGripperXSInterface

### @brief Standalone Module to control an Interbotix Arm and Gripper
### @param robot_model - Interbotix Arm model (ex. 'wx200' or 'vx300s')
### @param group_name - joint group name that contains the 'arm' joints as defined in the 'motor_config' yaml file; typically, this is 'arm'
### @param gripper_name - name of the gripper joint as defined in the 'motor_config' yaml file; typically, this is 'gripper'
### @param robot_name - defaults to value given to 'robot_model'; this can be customized if controlling two of the same arms from one computer (like 'arm1/wx200' and 'arm2/wx200')
### @param moving_time - time [s] it should take for all joints in the arm to complete one move
### @param accel_time - time [s] it should take for all joints in the arm to accelerate/decelerate to/from max speed
### @param use_gripper - True if the gripper module should be initialized; otherwise, it won't be.
### @param gripper_pressure - fraction from 0 - 1 where '0' means the gripper operates at 'gripper_pressure_lower_limit' and '1' means the gripper operates at 'gripper_pressure_upper_limit'
### @param gripper_pressure_lower_limit - lowest 'effort' that should be applied to the gripper if gripper_pressure is set to 0; it should be high enough to open/close the gripper (~150 PWM or ~400 mA current)
### @param gripper_pressure_upper_limit - largest 'effort' that should be applied to the gripper if gripper_pressure is set to 1; it should be low enough that the motor doesn't 'overload' when gripping an object for a few seconds (~350 PWM or ~900 mA)
### @param init_node - set to True if the InterbotixRobotXSCore class should initialize the ROS node - this is the most Pythonic approach; to incorporate a robot into an existing ROS node though, set to False
class InterbotixManipulatorXS(object):
    def __init__(self, robot_model, group_name="arm", gripper_name="gripper", robot_name=None, moving_time=2.0, accel_time=0.3, gripper_pressure=0.5, gripper_pressure_lower_limit=150, gripper_pressure_upper_limit=350, init_node=True):
        self.dxl = InterbotixRobotXSCore(robot_model, robot_name, init_node)
        self.arm = InterbotixArmXSInterface(self.dxl, robot_model, group_name, moving_time, accel_time)
        if gripper_name is not None:
            self.gripper = InterbotixGripperXSInterface(self.dxl, gripper_name, gripper_pressure, gripper_pressure_lower_limit, gripper_pressure_upper_limit)

### @brief Definition of the Interbotix Arm Module
### @param core - reference to the InterbotixRobotXSCore class containing the internal ROS plumbing that drives the Python API
### @param robot_model - Interbotix Arm model (ex. 'wx200' or 'vx300s')
### @param group_name - joint group name that contains the 'arm' joints as defined in the 'motor_config' yaml file; typically, this is 'arm'
### @param moving_time - time [s] it should take for all joints in the arm to complete one move
### @param accel_time - time [s] it should take for all joints in the arm to accelerate/decelerate to/from max speed
class InterbotixArmXSInterface(object):

    def __init__(self, core, robot_model, group_name, moving_time=2.0, accel_time=0.3):
        self.core = core
        self.group_info = self.core.srv_get_info("group", group_name)
        if (self.group_info.profile_type != "time"):
            rospy.logerr("Please set the group's 'profile type' to 'time'.")
        if (self.group_info.mode != "position"):
            rospy.logerr("Please set the group's 'operating mode' to 'position'.")
        self.robot_des = getattr(mrd, robot_model)
        self.initial_guesses = [[0.0] * self.group_info.num_joints for i in range(3)]
        self.initial_guesses[1][0] = np.deg2rad(-120)
        self.initial_guesses[2][0] = np.deg2rad(120)
        self.moving_time = None
        self.accel_time = None
        self.group_name = group_name
        self.joint_commands = []
        self.rev = 2 * math.pi
        for name in self.group_info.joint_names:
            self.joint_commands.append(self.core.joint_states.position[self.core.js_index_map[name]])
        self.T_sb = mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, self.joint_commands)
        self.set_trajectory_time(moving_time, accel_time)
        self.info_index_map = dict(zip(self.group_info.joint_names, range(self.group_info.num_joints)))
        print("Arm Group Name: %s\nMoving Time: %.2f seconds\nAcceleration Time: %.2f seconds\nDrive Mode: Time-Based-Profile" % (group_name, moving_time, accel_time))
        print("Initialized InterbotixArmXSInterface!\n")

    ### @brief Helper function to publish joint positions and block if necessary
    ### @param positions - desired joint positions
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    def publish_positions(self, positions, moving_time=None, accel_time=None, blocking=True):
        self.set_trajectory_time(moving_time, accel_time)
        self.joint_commands = list(positions)
        joint_commands = JointGroupCommand(self.group_name, self.joint_commands)
        self.core.pub_group.publish(joint_commands)
        if blocking:
            rospy.sleep(self.moving_time)
        self.T_sb = None # mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, self.joint_commands)

    ### @brief Helper function to command the 'Profile_Velocity' and 'Profile_Acceleration' motor registers
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    def set_trajectory_time(self, moving_time=None, accel_time=None):
        if (moving_time is not None and moving_time != self.moving_time):
            self.moving_time = moving_time
            self.core.srv_set_reg(cmd_type="group", name=self.group_name, reg="Profile_Velocity", value=int(moving_time * 1000))
        if (accel_time is not None and accel_time != self.accel_time):
            self.accel_time = accel_time
            self.core.srv_set_reg(cmd_type="group", name=self.group_name, reg="Profile_Acceleration", value=int(accel_time * 1000))

    ### @brief Helper function to check to make sure the desired arm group's joint positions are all within their respective joint limits
    ### @param positions - the positions [rad] to check
    ### @return <bool> - True if all positions are within limits; False otherwise
    def check_joint_limits(self, positions):
        theta_list = [int(elem * 1000)/1000.0 for elem in positions]
        speed_list = [abs(goal - current)/float(self.moving_time) for goal,current in zip(theta_list, self.joint_commands)]
        # check position and velocity limits
        for x in range(self.group_info.num_joints):
            if not (self.group_info.joint_lower_limits[x] <= theta_list[x] <= self.group_info.joint_upper_limits[x]):
                rospy.logwarn(
                    "Would exceed position limits on joint %s." % x
                )
                rospy.logwarn(
                    "Limits are [%f, %f], value was %f." %
                    (self.group_info.joint_lower_limits[x],
                    self.group_info.joint_upper_limits[x], theta_list[x])
                )
                return False
            if (speed_list[x] > self.group_info.joint_velocity_limits[x]):
                rospy.logwarn(
                    "Would exceed velocity limits on joint %s." % x
                )
                rospy.logwarn(
                    "Limit is %f, value was %f." %
                    (self.group_info.joint_velocity_limits[x], theta_list[x])
                )
                return False
        return True

    ### @brief Helper function to check to make sure a desired position for a given joint is within its limits
    ### @param joint_name - desired joint name
    ### @param position - desired joint position [rad]
    ### @return <bool> - True if within limits; False otherwise
    def check_single_joint_limit(self, joint_name, position):
        theta = int(position * 1000)/1000.0
        speed = abs(theta - self.joint_commands[self.info_index_map[joint_name]])/float(self.moving_time)
        ll = self.group_info.joint_lower_limits[self.info_index_map[joint_name]]
        ul = self.group_info.joint_upper_limits[self.info_index_map[joint_name]]
        vl = self.group_info.joint_velocity_limits[self.info_index_map[joint_name]]
        if not (ll <= theta <= ul):
            return False
        if speed > vl:
            return False
        return True

    ### @brief Command positions to the arm joints
    ### @param joint_positions - desired joint positions [rad]
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    ### @return <bool> - True if position was commanded; False if it wasn't due to being outside limits
    def set_joint_positions(self, joint_positions, moving_time=None, accel_time=None, blocking=True):
        if (self.check_joint_limits(joint_positions)):
            self.publish_positions(joint_positions, moving_time, accel_time, blocking)
            return True
        else:
            return False

    ### @brief Command the arm to go to its Home pose
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    def go_to_home_pose(self, moving_time=None, accel_time=None, blocking=True):
        self.publish_positions([0] * self.group_info.num_joints, moving_time, accel_time, blocking)

    ### @brief Command the arm to go to its Sleep pose
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    def go_to_sleep_pose(self, moving_time=None, accel_time=None, blocking=True):
        self.publish_positions(self.group_info.joint_sleep_positions, moving_time, accel_time, blocking)

    ### @brief Command a single joint to a desired position
    ### @param joint_name - name of the joint to control
    ### @param position - desired position [rad]
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    ### @details - Note that if a moving_time or accel_time is specified, the changes affect ALL the arm joints, not just the specified one
    def set_single_joint_position(self, joint_name, position, moving_time=None, accel_time=None, blocking=True):
        if not self.check_single_joint_limit(joint_name, position):
            return False
        self.set_trajectory_time(moving_time, accel_time)
        self.joint_commands[self.core.js_index_map[joint_name]] = position
        single_command = JointSingleCommand(joint_name, position)
        self.core.pub_single.publish(single_command)
        if blocking:
            rospy.sleep(self.moving_time)
        self.T_sb = mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, self.joint_commands)
        return True

    ### @brief Command a desired end-effector pose
    ### @param T_sd - 4x4 Transformation Matrix representing the transform from the /<robot_name>/base_link frame to the /<robot_name>/ee_gripper_link frame
    ### @param custom_guess - list of joint positions with which to seed the IK solver
    ### @param execute - if True, this moves the physical robot after planning; otherwise, only planning is done
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    ### @return theta_list - joint values needed to get the end-effector to the desired pose
    ### @return <bool> - True if a valid solution was found; False otherwise
    def set_ee_pose_matrix(self, T_sd, custom_guess=None, execute=True, moving_time=None, accel_time=None, blocking=True):
        if (custom_guess is None):
            initial_guesses = self.initial_guesses
        else:
            initial_guesses = [custom_guess]

        for guess in initial_guesses:
            theta_list, success = mr.IKinSpace(self.robot_des.Slist, self.robot_des.M, T_sd, guess, 0.001, 0.001)
            solution_found = True

            # Check to make sure a solution was found and that no joint limits were violated
            if success:
                for x in range(len(theta_list)):
                    if theta_list[x] <= -self.rev:
                        theta_list[x] %= -self.rev
                    elif theta_list[x] >= self.rev:
                        theta_list[x] %= self.rev

                    if round(theta_list[x],3) < round(self.group_info.joint_lower_limits[x],3):
                        theta_list[x] += self.rev
                    elif round(theta_list[x],3) > round(self.group_info.joint_upper_limits[x],3):
                        theta_list[x] -= self.rev
                solution_found = self.check_joint_limits(theta_list)
            else:
                solution_found = False

            if solution_found:
                if execute:
                    self.publish_positions(theta_list, moving_time, accel_time, blocking)
                    self.T_sb = T_sd
                return theta_list, True

        rospy.logwarn("No valid pose could be found. Returned theta_list variable may be nonsense.")
        return theta_list, False

    ### @brief Command a desired end-effector pose w.r.t. the Space frame
    ### @param x - linear position along the X-axis of the Space frame [m]
    ### @param y - linear position along the Y-axis of the Space frame [m]
    ### @param z - linear position along the Z-axis of the Space frame [m]
    ### @param roll - angular position around the X-axis of the Space frame [rad]
    ### @param pitch - angular position around the Y-axis of the Space frame [rad]
    ### @param yaw - angular position around the Z-axis of the Space frame [rad]
    ### @param custom_guess - list of joint positions with which to seed the IK solver
    ### @param execute - if True, this moves the physical robot after planning; otherwise, only planning is done
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    ### @return theta_list - joint values needed to get the end-effector to the desired pose
    ### @return <bool> - True if a valid solution was found; False otherwise
    ### @details - Do not set 'yaw' if using an arm with fewer than 6dof
    def set_ee_pose_components(self, x=0, y=0, z=0, roll=0, pitch=0, yaw=None, custom_guess=None, execute=True, moving_time=None, accel_time=None, blocking=True):
        if (self.group_info.num_joints < 6 or (self.group_info.num_joints >= 6 and yaw is None)):
            yaw = math.atan2(y,x)
        T_sd = np.identity(4)
        T_sd[:3,:3] = ang.eulerAnglesToRotationMatrix([roll, pitch, yaw])
        T_sd[:3, 3] = [x, y, z]
        return self.set_ee_pose_matrix(T_sd, custom_guess, execute, moving_time, accel_time, blocking)

    ### @brief Command a desired end-effector displacement that will follow a straight line path (when in 'position' control mode)
    ### @param x - linear displacement along the X-axis w.r.t. T_sy [m]
    ### @param y - linear displacement along the Y-axis w.r.t. T_sy [m]
    ### @param z - linear displacement along the Z-axis w.r.t. T_sy [m]
    ### @param roll - angular displacement around the X-axis w.r.t. T_sy [rad]
    ### @param pitch - angular displacement around the Y-axis w.r.t. T_sy [rad]
    ### @param yaw - angular displacement around the Z-axis w.r.t. T_sy [rad]
    ### @param moving_time - duration in seconds that the robot should move
    ### @param wp_moving_time - duration in seconds that each waypoint in the trajectory should move
    ### @param wp_accel_time - duration in seconds that each waypoint in the trajectory should be accelerating/decelerating (must be equal to or less than half of wp_moving_time)
    ### @param wp_period - duration in seconds between each waypoint
    ### @return <bool> - True if a trajectory was successfully planned and executed; otherwise False
    ### @details - T_sy is a 4x4 transformation matrix representing the pose of a virtual frame w.r.t. /<robot_name>/base_link.
    ###            This virtual frame has the exact same x, y, z, roll, and pitch of /<robot_name>/base_link but contains the yaw
    ###            of the end-effector frame (/<robot_name>/ee_gripper_link).
    ###            Note that 'y' and 'yaw' must equal 0 if using arms with less than 6dof.
    def set_ee_cartesian_trajectory(self, x=0, y=0, z=0, roll=0, pitch=0, yaw=0, moving_time=None, wp_moving_time=0.2, wp_accel_time=0.1, wp_period=0.05):
        if self.group_info.num_joints < 6 and (y != 0 or yaw != 0):
            rospy.loginfo("Please leave the 'y' and 'yaw' fields at '0' when working with arms that have less than 6dof.")
            return False
        rpy = ang.rotationMatrixToEulerAngles(self.T_sb[:3,:3])
        T_sy = np.identity(4)
        T_sy[:3,:3] = ang.eulerAnglesToRotationMatrix([0.0, 0.0, rpy[2]])
        T_yb = np.dot(mr.TransInv(T_sy), self.T_sb)
        rpy[2] = 0.0
        if (moving_time == None):
            moving_time = self.moving_time
        accel_time = self.accel_time
        N = int(moving_time / wp_period)
        inc = 1.0 / float(N)
        joint_traj = JointTrajectory()
        joint_positions = list(self.joint_commands)
        for i in range(N+1):
            joint_traj_point = JointTrajectoryPoint()
            joint_traj_point.positions = joint_positions
            joint_traj_point.time_from_start = rospy.Duration.from_sec(i * wp_period)
            joint_traj.points.append(joint_traj_point)
            if (i == N):
                break
            T_yb[:3,3] += [inc * x, inc * y, inc * z]
            rpy[0] += inc * roll
            rpy[1] += inc * pitch
            rpy[2] += inc * yaw
            T_yb[:3,:3] = ang.eulerAnglesToRotationMatrix(rpy)
            T_sd = np.dot(T_sy, T_yb)
            theta_list, success = self.set_ee_pose_matrix(T_sd, joint_positions, False, blocking=False)
            if success:
                joint_positions = theta_list
            else:
                rospy.loginfo("%.1f%% of trajectory successfully planned. Trajectory will not be executed." % (i/float(N) * 100))
                break

        if success:
            self.set_trajectory_time(wp_moving_time, wp_accel_time)
            joint_traj.joint_names = self.group_info.joint_names
            current_positions = []
            with self.core.js_mutex:
                for name in joint_traj.joint_names:
                    current_positions.append(self.core.joint_states.position[self.core.js_index_map[name]])
            joint_traj.points[0].positions = current_positions
            joint_traj.header.stamp = rospy.Time.now()
            self.core.pub_traj.publish(JointTrajectoryCommand("group", self.group_name, joint_traj))
            rospy.sleep(moving_time + wp_moving_time)
            self.T_sb = T_sd
            self.joint_commands = joint_positions
            self.set_trajectory_time(moving_time, accel_time)

        return success

    ### @brief Command displacements to the end effector's position w.r.t. the Space frame
    ### @param dx - linear displacement along the X-axis of the Space frame [m]
    ### @param dy - linear displacement along the Y-axis of the Space frame [m]
    ### @param dz - linear displacement along the Z-axis of the Space frame [m]
    ### @param custom_guess - list of joint positions with which to seed the IK solver
    ### @param execute - if True, this moves the physical robot after planning; otherwise, only planning is done
    ### @param moving_time - duration in seconds that the robot should move
    ### @param accel_time - duration in seconds that that robot should spend accelerating/decelerating (must be less than or equal to half the moving_time)
    ### @param blocking - whether the function should wait to return control to the user until the robot finishes moving
    ### @return theta_list - joint values needed to get the end-effector to the desired pose
    ### @return <bool> - True if a valid solution was found; False otherwise
    ### @details - Do not set 'yaw' if using an arm with fewer than 6dof
    def set_relative_ee_position_wrt_to_base_frame(self, *, dx=0, dy=0, dz=0, custom_guess=None, execute=True, moving_time=None, accel_time=None, blocking=True):
        return self.set_ee_pose_components(
            x=self.T_sb[0, 3] + dx,
            y=self.T_sb[1, 3] + dy,
            z=self.T_sb[2, 3] + dz,
            custom_guess=custom_guess,
            execute=execute,
            moving_time=moving_time,
            accel_time=accel_time,
            blocking=blocking,
        )

    ### @brief Get the latest commanded joint positions
    ### @return - list of latest commanded joint positions [rad]
    def get_joint_commands(self):
        return list(self.joint_commands)

    ### @brief Get the latest commanded position for a given joint
    ### @param joint_name - joint for which to get the position
    ### @return - desired position [rad]
    def get_single_joint_command(self, joint_name):
        return self.joint_commands[self.info_index_map[joint_name]]

    ### @brief Get the latest commanded end-effector pose w.r.t the Space frame
    ### @return <4x4 matrix> - Transformation matrix
    def get_ee_pose_command(self):
        return np.array(self.T_sb)

    ### @brief Get the actual end-effector pose w.r.t the Space frame
    ### @return <4x4 matrix> - Transformation matrix
    def get_ee_pose(self):
        joint_states = [self.core.joint_states.position[self.core.js_index_map[name]] for name in self.group_info.joint_names]
        T_sb = mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, joint_states)
        return T_sb

    ### @brief Resets self.joint_commands to be the actual positions seen by the encoders
    ### @details - should be used whenever joints are torqued off, right after torquing them on again
    def capture_joint_positions(self):
        self.joint_commands = []
        for name in self.group_info.joint_names:
            self.joint_commands.append(self.core.joint_states.position[self.core.js_index_map[name]])
        self.T_sb = mr.FKinSpace(self.robot_des.M, self.robot_des.Slist, self.joint_commands)