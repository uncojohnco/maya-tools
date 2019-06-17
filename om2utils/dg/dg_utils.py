from maya.api import OpenMaya as om2

try:
    from typing import Iterable, Union
except:
    pass


def as_mObject(obj, getter='getDependNode'):
    # type: (Union[str, om2.MDagPath, om2.MObject], atr) -> Union[om2.MDagPath, om2.MObject]
    """Cast a maya node | attribute | component as an maya.api.OpenMaya object.

    Args:
        obj: Full path name or maya object to query.
        getter: Accessor to retrieve the object from maya. Defaults to 'getDependNode'.
    Returns:
        object: The maya object retrieved by the getter.
    Examples:
        >>> import maya.cmds as mc
        >>> transformName, shapeName = mc.polyCube()
        >>> transformPath = as_mObject(transformName, 'getDagPath')
        >>> transformPath.numberOfShapesDirectlyBelow()
        1
        >>> from maya.api import OpenMaya as om2
        >>> transform = om2.MFnTransform(as_mObject(transformName))
        >>> transform.transformationMatrix()
        om2.MMatrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))

    """
    msel = om2.MSelectionList()
    msel.add(obj)

    mobj = getattr(msel, getter)(0)

    return mobj


def get_shortname(obj):
    # type: (Union[str, om2.MDagPath, om2.MObject]) -> str
    """Returns the shortest name of an object in the maya graph 
    (e.g. no namespace & last element of the path).

    """
    valid_types = [str, om2.MDagPath, om2.MObject]

    if isinstance(obj, basestring):
        fullpath = obj

    elif isinstance(obj, om2.MDagPath):
        fullpath = obj.fullPathName()

    elif obj.hasFn(om2.MFn.kDependencyNode):
        fullpath = om2.MFnDependencyNode(obj).name()

    else:  # obj is not of a valid type.
        msg = ('Provided object is invalid, object type is "{}".'
               ' Valid types are: {}'.format(type(obj), valid_types))
        raise ValueError(msg)

    return om2.MNamespace.stripNamespaceFromName(fullpath).split('|')[-1]


def get_fullpath(mobj):
    # type: (om2.MObject) -> str

    valid_types = [om2.MObject, om2.MDagPath]

    if isinstance(mobj, om2.MDagPath):
        if mobj.hasFn(om2.MFn.kDagNode):
            return mobj.fullPathName()

    elif isinstance(mobj, om2.MObject):
        if mobj.hasFn(om2.MFn.kDagNode):
            return om2.MDagPath.getAPathTo(mobj).fullPathName()

    elif mobj.hasFn(om2.MFn.kDependencyNode):
        return om2.MFnDependencyNode(mobj).name()

    else:  # mobj is not of a valid type.
        msg = ('Provided object is invalid, object type is "{}".'
               ' Valid types are: {}'.format(type(mobj), valid_types))
        raise ValueError(msg)
