#!/usr/bin/env python3

import time
import numpy as np
import argparse
import os

import rospy

os.environ['XBOT_VERBOSE'] = '2'
from xbot_interface import xbot_interface as xb
from cartesian_interface.pyci_all import *

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--action', choices=('park', 'unpark'))
parser.add_argument('-d', '--dance', action='store_true')
args = parser.parse_args()

# -d only valid for unpark
if args.dance and args.action != 'unpark':
    raise ValueError('Dance only valid for unpark action')


class Parking:

    ikpb = """

solver_options:
    regularization: 1e-2
    back_end: osqp
    
stack:
    - [postural, base, contact_1, contact_2, contact_3, contact_4]

constraints: [vlim]

vlim:
    type: VelocityLimits

contact_1:
    type: Cartesian
    distal_link: contact_1
    base_link: world
    indices: [0, 1, 2]
    
contact_2:
    type: Cartesian
    distal_link: contact_2
    base_link: world
    indices: [0, 1, 2]
    
contact_3:
    type: Cartesian
    distal_link: contact_3
    base_link: world
    indices: [0, 1, 2]
    
contact_4:
    type: Cartesian
    distal_link: contact_4
    base_link: world
    indices: [0, 1, 2]

postural:
    type: Postural
    lambda: 0.1
    weight: 0.01

base:
    type: Cartesian
    distal_link: base_link
    lambda: 0.1
    weight: 0.0
"""


    def __init__(self):
        # create robot
        self.cfg = get_xbot_config(prefix='xbotcore/')
        self.robot = xb.RobotInterface(self.cfg)

        self.joints = sum([[f'hip_roll_{i+1}', f'hip_pitch_{i+1}', f'knee_pitch_{i+1}'] for i in range(4)], [])
        self.robot.setControlMode(xb.ControlMode.Idle())
        self.robot.setControlMode({j: xb.ControlMode.Position() for j in self.joints})
        self.idx = np.array([self.robot.getDofIndex(j) for j in self.joints])
        self.qidx = self.idx


    def move(self, action):

        qname = {
            'park': 'parked',
            'unpark': 'home'
        }[action]

        robot = self.robot
        joints = self.joints
        qidx = self.qidx

        while not robot.sense(update_references=True):
            time.sleep(0.1)

        model = xb.ModelInterface(self.cfg)
        model.setJointPosition(robot.eigenToMap(robot.getPositionReference()))
        model.update()

        dt = 0.01
        ci = pyci.CartesianInterface.MakeInstance(solver='OpenSot', problem=Parking.ikpb, model=model, dt=dt)
        rsc = pyci.RosServerClass(ci)
        postural = ci.getTask('Postural')

        t = 0.0
        trj_time = 5.0

        q0 = model.getJointPosition()[qidx+6]
        qf = model.getRobotState(qname)[qidx+6]

        def solve_and_move():
            nonlocal t
            ci.update(t, dt)
            model.setJointPosition(model.getJointPosition() + model.getJointVelocity() * dt)
            model.update()
            rsc.run()
            
            # set reference to robot and move
            robot.setPositionReference(model.getJointPositionMap())
            robot.move()
            
            # update time and sync loop
            t += dt
            time.sleep(dt)

        while t < trj_time:

            # compute trajectory for postural task
            tau = t / trj_time
            alpha = 6 * tau**5 - 15 * tau**4 + 10 * tau**3
            q = (1-alpha) * q0 + alpha * qf

            # set reference and solve
            postural.setReferencePosture({joints[i]: q[i] for i in range(len(joints))})
            solve_and_move()

        if not args.dance or action != 'unpark':
            return
        
        # dance
        base = ci.getTask('base_link')
        base.setWeight(np.eye(6) * 100.0)
        th = np.pi / 4

        T0 = base.getPoseReference()[0]
        T1 = T0.copy()
        T1.quaternion = [0, 0, np.sin(th/2), np.cos(th/2)]
        base.setPoseTarget(T1, 1.0)

        t0 = t
        while t < t0 + 1.0:
            solve_and_move()
            if base.getTaskState() == pyci.State.Online:
                print('done')
                break

        T1.quaternion = [0, 0, -np.sin(th/2), np.cos(th/2)]
        base.setPoseTarget(T1, 1.0)

        t0 = t
        while t < t0 + 1.0:
            solve_and_move()
            if base.getTaskState() == pyci.State.Online:
                print('done')
                break

        base.setPoseTarget(T0, 1.0)

        t0 = t
        while t < t0 + 1.0:
            solve_and_move()
            if base.getTaskState() == pyci.State.Online:
                print('done')
                break



# init ros
rospy.init_node('parking')

# create parking object
parking = Parking()

# move
if args.action:
    parking.move(args.action)

print('Done')
