import logging


import maya.cmds as mc
from maya.api import OpenMaya as om2

from . import dg


logger = logging.getLogger(__name__)


# Safer if you used om2.MObjectHandle to store your MObject ...
class UVActions(object):

    def __init__(self, mobj):
        # type: (om2.MObject) ->None
        self._MObject = mobj

    def uvset_copy(self, src_uvset, dest_uvset, createNewMap=False):
        # type: (str, str, bool) -> None
        mc.polyCopyUV(self.fullpath, createNewMap=createNewMap, ch=False,
                        uvSetNameInput=src_uvset, uvSetName=dest_uvset)
        logger.info('Copied uv set "{}" to "{}"...'.format(src_uvset, dest_uvset))

    def uvset_current_switch(self, uvset):
        mc.polyUVSet(self.fullpath, currentUVSet=True, uvSet=uvset)

    def uvset_exists(self, uvset):
        # type: (str) -> bool
        is_uvset = uvset in self.uvsets
        return is_uvset

    def uvset_delete(self, uvset):
        # type: (str) -> None

        if self.uvset_exists(uvset):
            self.uvset_current_switch(self.uvset_default)
            mc.polyUVSet(self.fullpath, delete=True, uvSet=uvset)
            msg = 'Removed uv set "{}" from mesh "{}".'

        else:
            msg = 'Removal of uv set "{}" from mesh "{}" skipped - doesnt exist.'

        logger.info(msg.format(uvset, self.fullpath))

    # --- Properties -----------------------------------------------------------

    @property
    def uvsets(self):
        # type: () -> typing.Iterable(str)
        indices = mc.polyUVSet(self.fullpath, query=True, allUVSetsIndices=True)

        uvsets = []
        for ii in indices:
            node_attr = "{}.uvSet[{}].uvSetName".format(self.fullpath, ii)
            uvsets.append(mc.getAttr(node_attr))

        return uvsets

    @property
    def uvset_default(self):
        """Return the assumed Maya "default UV set" for this mesh."""
        if len(self.uvsets):
            return self.uvsets[0]

        else:
            raise RuntimeError('No UV sets could be found on "{}"'.format(self.fullpath))

    @property
    def uvs(self):
        return get_mesh_uvs(self.fullpath)

    @property
    def fullpath(self):
        return dg.getFullpath(self._MObject)


def get_mesh_uvs(fullpath):
    uvs = mc.polyEvaluate(fullpath, uv=True)
    return '{}.map[0:{}]'.format(fullpath, uvs)
