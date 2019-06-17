import logging
from functools import partial

from ..dg import dg_utils

from maya.api import OpenMaya as om2

logger = logging.getLogger(__name__)


def create_parent_above(mobj, name=None):
    # type: (om2.MObject, str) ->  om2.MObject
    """Creates a transform node between a maya DAG node 'mobj' and its current parent.

    New parent will have 'mobj' values and 'mobj' transformations will be reset to identity.

    Args:
        mobj (om2.MObject): Transform that will be moved under a new parent.
        name (Optional[str]): Name of the new parent node (Transform).

    """
    mtrans = om2.MFnTransform(mobj)
    identity_matrix = mtrans.transformationMatrix()

    parent = mtrans.getPath().pop().node()
    mdag_mod = om2.MDagModifier()

    node = parent if parent.hasFn(om2.MFn.kTransform) else om2.MObject.kNullObj
    new_parent = mtrans.create(node)

    mdag_mod.reparentNode(mobj, new_parent)

    if name:
        mdag_mod.renameNode(new_parent, name)
    mdag_mod.doIt()

    scalePivot = mtrans.scalePivot(om2.MSpace.kTransform)
    rotatePivot = mtrans.rotatePivot(om2.MSpace.kTransform)

    setScalePivot = partial(mtrans.setScalePivot, scalePivot,
                            om2.MSpace.kTransform, True)
    setRotatePivot = partial(mtrans.setRotatePivot, rotatePivot,
                             om2.MSpace.kTransform, True)

    mtrans.setTransformation(om2.MTransformationMatrix(identity_matrix))
    setScalePivot()
    setRotatePivot()

    mtrans.setObject(mobj)
    mtrans.setTransformation(om2.MTransformationMatrix())
    setScalePivot()
    setRotatePivot()

    return new_parent


def create_node_at_path(path):
    # type: (str) -> om2.MObject

    from AL.maya import cmds

    # mtrans = om2.MFnTransform(om2.MObject.kNullObj)
    # new_parent = mtrans.createNode(name=nn, parent='|'.join(path_steps))

    path_steps = ['']
    last_node = ''

    for ii, nn in enumerate(path.split('|')[:]):

        if ii == 0:
            continue

        if not cmds.objExists('|'.join(path_steps + [nn])):
            last_node = cmds.createNode('transform', name=nn,
                                        parent='|'.join(path_steps))
        path_steps.append(nn)

    return dg_utils.as_mObject(last_node)
