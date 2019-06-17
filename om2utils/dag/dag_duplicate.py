import logging
import pprint


import maya.cmds as mc
from maya.api import OpenMaya as om2

from ..dg import dg_utils


logger = logging.getLogger(__name__)
_pf = pprint.PrettyPrinter(indent=4).pformat


class HierarchyDuplicator(object):

    def __init__(self, source_path):

        self._source_path = source_path
        self._destination_path = None
        self._replace = True
        self._new_name = None

        self._result_mobj = None

    def _setup(self):
        # type: () -> (om2.MFnDagNode, om2.MObject, str)

        dest_path = self._destination_path

        if mc.objExists(dest_path) and self._replace:
            mc.delete(dest_path)
            logger.info('Deleted existing node at path: "{}".'.format(dest_path))

    def _duplicate(self, *args, **kwargs):

        duplicate_path = mc.duplicate(self._source_mobj, *args, **kwargs)[0]
        self._result_mobj = dg_utils.as_mObject(duplicate_path)
        return self._result_mobj

    def duplicate(self):

        self._setup()
        self._duplicate()

        if self._new_name:
            self.rename(self._new_name)

    def duplicate_under_same_parent(self):

        parent = self._source_dagpath.parent

        self.duplicate()
        return self._parent_under(parent)

    def _parent_under(self, parent_path):
        # type: (str) -> None

        parent = dg_utils.as_mObject(parent_path)

        md = om2.MDagModifier()

        if self._src_is_valid_mobject_handle():
            md.reparentNode(self._source_mobj, parent)
            md.doIt()

        else:
            raise

    def rename(self, name):

        root = self._result_mobj.object()
        md = om2.MDagModifier()

        if self._src_is_valid_mobject_handle():
            md.renameNode(root, name)
            md.doIt()

        else:
            raise

    def _src_is_valid_mobject_handle(self):
        handle = self.source_mobjhandle
        return bool(handle.isValid() and handle.isAlive())

    @property
    def source_path(self):
        return self._source_path

    @property
    def source_mobjhandle(self):
        # type: () -> om2.MObjectHandle
        return om2.MObjectHandle(dg_utils.as_mObject(self._source_path))

    @property
    def _source_mobj(self):
        # type: () -> om2.MObject
        assert self._src_is_valid_mobject_handle()
        return self.source_mobjhandle.object()

    @property
    def _source_dagpath(self,):
        # type: () -> om2.MDagPath
        return dg_utils.as_mObject(self._source_mobj, 'getDagPath')

    @property
    def destination_path(self):
        return self._destination_path

    @destination_path.setter
    def destination_path(self, value):
        self._destination_path = value
