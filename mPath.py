#*******************************************************************************
# content = Generates a motion path from keyframed animation.
#
# version      = 0.0.1
# date         = 2023-03-31
# how to       => 
#
# dependencies = Maya
#
# author = Grae Revell <grae.revell@gmail.com>
#*******************************************************************************

from pymel.core import *
import maya.cmds as cmds

#*******************************************************************************
# VARIABLES

ROOT = 'Anim_to_Path'

#*******************************************************************************
# CLASS

class MotionObj:
    def __init__(self):
        self.start_frame = ''
        self.end_frame = ''
        self.selected_obj = ''
        self.curve_pts = []
        self.mp_curve = ''
        self.arc_len_dim = ''
        self.total_arc_len = ''
        self.motion_path = ''
        self.key_times = []
        self.arc_len_values = []

#*******************************************************************************
# COLLECT

    def get_scene_data(self):
        print('|get_scene_data|')
        self.start_frame = int(cmds.playbackOptions(min=True,q=True))
        self.end_frame = int(cmds.playbackOptions(max=True,q=True))
        self.selected_obj = cmds.ls(selection=True)[0]

#*******************************************************************************
# PROCESS
    def create_hierarchy(self):
        """ Creates initial folder structre
        
        Returns:
            None
        """

        if not cmds.objExists(ROOT):
            cmds.group(empty=True, name=ROOT)


    def spline_curve(self, curve, attr):
        cmds.selectKey(curve, time=(None, None), attribute=attr)
        cmds.keyTangent(curve, itt="spline", ott="spline", e=True)


    def create_curve(self):
        print('|create_curve|')
        snapshot = cmds.snapshot(self.selected_obj, constructionHistory=True, startTime=self.start_frame, endTime=self.end_frame, increment=1)
        cmds.select(snapshot)
        pointGrp = cmds.listRelatives( children=True, type='transform')
        cmds.spaceLocator( n='tempLocator')
        for point in pointGrp:
            cmds.xform( point, cp=True)
            cmds.pointConstraint( point, 'tempLocator' )
            self.curve_pts.append( cmds.xform('tempLocator', q=True, t=True, ws=True ) )
            cmds.delete(cmds.listRelatives( children=True ) )
        cmds.delete( 'tempLocator' )
        cmds.delete(snapshot)


    def create_pm_motion_path(self):
        print('|create_motion_path|')
        self.mp_curve = cmds.curve( p = self.curve_pts, name='mp_curve')
        cmds.parent( self.mp_curve, ROOT)
        cmds.rename('curveShape1', 'mp_curveShape')
        parametric_mp_obj = cmds.polyCube(name='parametric_mp_obj')
        cmds.parent( parametric_mp_obj, ROOT)
        motion_path_pm = cmds.pathAnimation( parametric_mp_obj, stu=self.start_frame, etu=self.end_frame, c=self.mp_curve )
        self.spline_curve(motion_path_pm, 'u')
        # Subtract 1 from the motion path U value and add 1 to the last U value.
        cmds.keyframe(motion_path_pm, edit=True, relative=True, valueChange=-1, index=(0,0))
        cmds.keyframe(motion_path_pm, edit=True, relative=True, valueChange=1, index=(1,1))


    def create_arc_length_dim(self):
        print('|create_arc_length_dim|')
        self.arc_len_dim = pm.arcLengthDimension(self.mp_curve + '.u[' + str(len(self.curve_pts)-3) + ']')
        self.total_arc_len = cmds.getAttr(self.arc_len_dim + '.arcLength')
        cmds.setKeyframe(self.arc_len_dim +'.upv', time=(self.start_frame, self.end_frame))
        self.spline_curve(self.arc_len_dim +'.upv', 'u')
        cmds.keyframe(self.arc_len_dim +'.upv', edit=True, absolute=True, valueChange=-1, index=(0,0))
        cmds.keyframe(self.arc_len_dim +'.upv', edit=True, relative=True, valueChange=1, index=(1,1))
        cmds.bakeResults(self.arc_len_dim + '.upv', t=(self.start_frame, self.end_frame), sb=1)


    def create_motion_path(self):
        mp_obj = cmds.polyCube(name='mp_obj')
        cmds.parent( mp_obj, ROOT)
        self.motion_path = cmds.pathAnimation(mp_obj, stu=self.start_frame, etu=self.end_frame, c=self.mp_curve, fractionMode=True)
        self.spline_curve(self.motion_path, 'u')
        anim_curve = cmds.listConnections(self.arc_len_dim + '.upv', type='animCurve')[0]
        self.key_times = cmds.keyframe(anim_curve, query=True, timeChange=True)     
        for time in self.key_times:
            arc_len_value = cmds.getAttr(self.arc_len_dim + '.arcLength', time=time) / self.total_arc_len
            #self.arc_len_values.append(arc_len_value)
            cmds.setKeyframe(self.motion_path, time=time, at='u', value=arc_len_value)


#*******************************************************************************
# RUN

motion_obj = MotionObj()
motion_obj.get_scene_data()
motion_obj.create_hierarchy()
motion_obj.create_curve()
motion_obj.create_pm_motion_path()
motion_obj.create_arc_length_dim()
motion_obj.create_motion_path()

