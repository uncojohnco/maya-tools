"""This module contains utilities for interacting with the maya DAG.

Functionality should try to be limited to using om2 only, querying with cmds is allowed with
no performance issues.
"""

import itertools
import logging
import pprint


import maya.cmds as mc
from maya.api import OpenMaya as om2

from ..dg import dg_utils


logger = logging.getLogger(__name__)
_pf = pprint.PrettyPrinter(indent=4).pformat

try:
    from typing import Callable, Dict, Generator, Iterable, List, Union
except:
    pass


# iterators
def idag(root=None, getter='currentItem', filter_type=om2.MFn.kInvalid):
    # type: (om2.MObject, str, om2.MFn) -> Generator[Union[om2.MDagPath, om2.MObject]]
    """Iterate over the maya DAG.

    Examples:
        >>> # iterate on all meshes (MObjects) under one transform
        >>> # from AL.dept.assets.om2utils.dg import dg_utils
        >>> root = dg_utils.as_mObject('|my|transform|node')
        >>> for mobj in idag(root, filter_type=om2.MFn.kMesh):
        ...     print(mobj)

        >>> # iterate on all full paths (strings) for shapes on the scene (mesh, nurbsCurves, etc.)
        >>> for path in idag(getter='fullPathName', filter_type=om2.MFn.kShape):
        ...     print(path)

    Args:
        root (Optional[MObject]): Root of the DAG iteration, if None is given, the world will be used.
        getter (str): Name of the accessor to retrieve on each iteration ('currentItem', 'getPath', etc).
                      Defaults to 'currentItem'.
        filterType: Filters the iterator to a specific type node. Defaults to om2.MFn.kInvalid (access all DAG).

    Yields:
        object: the current requested object on the DAG iteration (defaults to an MObject).
    """
    traversal_type = om2.MItDag.kDepthFirst
    mit = om2.MItDag()
    mit.reset(root or mit.root(), traversal_type, filter_type)

    accessor = getattr(mit, getter)

    while not mit.isDone():
        yield accessor()
        mit.next()


def itransforms_under_root(root=None, **kwargs):
    # type: (om2.MObject, Dict) -> Generator[om2.MObject]
    """Convenience wrapper function to iterate over all transforms under `root` in the DAG.

    Args:
        root (Optional): Root node in the DAG to iterate transforms from. If None is given, all transforms in the
                         scene are yielded. Defaults to None.
        **kwargs: Extra variable keyword arguments to pass on to the iterDAG function object (see help(iterDAG)).

    Yields:
        object: Next transform in the DAG (defaults to an MObject)

    """
    return idag(root, filter_type=om2.MFn.kTransform, **kwargs)


def itransformed_local_pivots(transforms):
    # type: (Iterable[om2.MObject]) -> Generator[Union[om2.MDagPath, om2.MObject]]
    """Iterate over the transforms that have non-zeroed local pivots (user modified pivots, frozen transforms, etc).

    Args:
        transforms (iterable): Iterable containing the transforms to iterate in.

    Yields:
        MObject: Next transform with non zero values on its local pivots.

    Examples:
        >>> # On an empty scene, create three cubes. Move the second and the third. Freeze transforms on the third one.
        >>> transforms = itransforms()  # TODO: This is incorrect...
        >>> identityTtransforms = iter_identity_transforms(transforms)
        >>> frozenTransforms = itransformed_local_pivots(identityTtransforms)
        >>> from maya.api.OpenMaya om2 import MFnDagNode
        >>> [MFnDagNode(t).fullPathName() for t in frozenTransforms]
        [u'|pCube3']

    """
    mdag = om2.MFnDagNode()

    mobj_path = lambda mobj:  mdag.setObject(mobj).fullPathName()
    local_space = lambda mobj: any(mc.xform(mobj_path, piv=True, q=True))

    for transform in itertools.ifilter(local_space, transforms):
        yield transform


def _itransforms_of_identity(transforms, filter_func):
    # type: (Iterable[om2.MObject], Callable) -> Generator[om2.MObject]

    mtrans = om2.MFnTransform()
    identity = lambda mobj: mtrans.setObject(mobj).transformationMatrix().isEquivalent(om2.MMatrix.kIdentity)

    return (t for t in filter_func(identity, transforms))


def itransforms_of_non_identity(transforms):
    # type: (Iterable[om2.MObject]) -> Generator[om2.MObject]
    """Iterate over the transforms that have any transformation values (object matrix is not identity).

    Args:
        transforms (iterable): Iterable containing the transforms to iterate in.

    Yields:
        MObject: Next transform with transformation values.

    Example:
        >>> # On an empty scene, create three cubes. Move the second and the third. Freeze transforms on the third one.
        >>> transforms = itransforms()  # TODO: This is incorrect...
        >>> from maya.api.OpenMaya om2 import MFnDagNode
        >>> [MFnDagNode(t).fullPathName() for t in itransforms_of_non_identity(transforms)]
        [u'|persp', u'|top', u'|front', u'|side', u'|pCube2']
    """
    for transform in _itransforms_of_identity(transforms, itertools.ifilterfalse):
        yield transform


def itransforms_of_identity(transforms):
    # type: (Iterable[om2.MObject]) -> Generator[om2.MObject]
    """Iterate over the transforms with an identity matrix (no transformation values).

    Args:
        transforms (iterable): Iterable containing the transforms to iterate in.

    Yields:
        MObject: Next transform with no transformation values.

    Example:
        >>> # On an empty scene, create three cubes. Move the second and the third. Freeze transforms on the third one.
        >>> transforms = itransforms()
        >>> from maya.api.OpenMaya om2 import MFnDagNode
        >>> [MFnDagNode(t).fullPathName() for t in _itransforms_of_identity(transforms)]
        [u'|pCube1', u'|pCube3']
    """
    for transform in _itransforms_of_identity(transforms, itertools.ifilter):
        yield transform


class IMeshs(object):

    @staticmethod
    def iter(root=None, **kwargs):
        # type: (om2.MObject, Dict) -> Generator[om2.MObject]
        """Convenience wrapper function to iterate over all meshs under `root` in the DAG.
    
        Args:
            root (Optional): Root node in the DAG to iterate transforms from. If None is given, all transforms in the
                             scene are yielded. Defaults to None.
            **kwargs: Extra variable keyword arguments to pass on to the iterDAG function object (see help(iterDAG)).
    
        Yields:
            object: Next transform in the DAG (defaults to an MObject)
    
        """
        return idag(root, filter_type=om2.MFn.kMesh, **kwargs)

    @staticmethod
    def mesh_parents(node_name):
        # type: (str) -> Generator[om2.MObject]

        root = dg_utils.as_mObject(node_name)
        shape_paths = idag(root, getter='getPath', filter_type=om2.MFn.kShape)
        transform_paths = (path.pop().node() for path in shape_paths)

        return transform_paths


class IDag(object):

    _omTypeMap = {getattr(om2.MFn, n): n for n in dir(om2.MFn)}

    _omTypeInts = [i for i in _omTypeMap.iterkeys()]
    _omTypeStrs = [n for n in _omTypeMap.iteritems()]
    _omTypeIntToType = lambda i: IDag._omTypeMap[i]

    def __init__(self, root=None, *args, **kwargs):
        # type: (Union[str, om2.MObject , om2.MFn], List, Dict) -> None

        self._root = dg_utils.as_mObject(root)
        self._getter = 'currentItem'
        self._traversal_type = om2.MItDag.kDepthFirst
        self._traversal_depth_max = 0  # Traverse trees till exhausted.
        self._yield_only_at_depth = 0  # Yield nodes at specified depth
        self._filter_types = [om2.MFn.kInvalid]

    def doIt(self):

        mit = om2.MItDag()

        root = self._root or mit.root()
        traversal_type = self._traversal_type
        limit = self._traversal_depth_max

        if self._yield_only_at_depth:
            traversal_type = om2.MItDag.kBreadthFirst
            limit = self._yield_only_at_depth + 1

        if len(self._filter_types) == 1:
            mit.reset(root, traversal_type, self._filter_types[0])

        else:
            mItr = om2.MIteratorType()
            mItr.filterList = self._filter_types
            mit.reset(mItr, root, traversal_type)

        accessor = getattr(mit, self._getter)

        # logger.debug('root: "{}"'.format(dg_utils.get_fullpath(root)))
        # logger.debug('IDag.doIt() - locals()\n{}'.format(_pf(locals())))

        while not mit.isDone():
            logger.debug('@depth: {}, {}'.format(mit.depth(), mit.fullPathName()))

            # Handle if traversal of tree has depth limit.
            if limit and mit.depth() >= limit:
                logger.debug('Traversal depth limit ({}) reached for "{}"'
                             .format(limit - 1, dg_utils.get_fullpath(self._root)))
                break

            # Handle if yielding node at a specified depth.
            if self._yield_only_at_depth and mit.depth() < self._yield_only_at_depth:
                mit.next()
                continue

            # Finally yield the node.
            yield accessor()
            mit.next()

    @property
    def root(self):
        # type: () -> Union[str, om2.MObject , om2.MFn]
        return self._root

    @root.setter
    def root(self, value):
        # type: (Union[om2.MItDag.kDepthFirst, om2.MItDag.kBreadthFirst]) -> None
        self._root = dg_utils.as_mObject(value)

    @property
    def getter(self):
        # type: () -> Union['currentItem', 'getPath', 'fullPathName', 'getAllPaths',  'partialPathName']
        return self._getter

    @getter.setter
    def getter(self, value):
        # type: (Union['currentItem', 'getPath', 'fullPathName', 'getAllPaths', 'partialPathName']) -> None
        self._getter = value

    @property
    def filter_types(self):
        # type: () -> (Iterable[om2.MFn])
        return self._filter_types

    @filter_types.setter
    def filter_types(self, values):
        # type: (Iterable[om2.MFn]) -> None
        assert isinstance(values, list)
        msg = 'Provided "filter_types" are invalid, "{}"'.format(values)
        assert all(lambda v: v in IDag._omTypeInts for v in values), msg

        self._filter_types = values

    @property
    def traversal_type(self):
        # type: () -> Union[om2.MItDag.kDepthFirst, om2.MItDag.kBreadthFirst]
        return self._traversal_type

    @traversal_type.setter
    def traversal_type(self, value):
        # type: (Union[om2.MItDag.kDepthFirst, om2.MItDag.kBreadthFirst]) -> None
        self._traversal_type = value

    @property
    def traversal_depth_max(self):
        # type: () -> int
        return self._traversal_depth_max

    @traversal_depth_max.setter
    def traversal_depth_max(self, value):
        # type: (int) -> None
        self._traversal_depth_max = value

    @property
    def yield_only_at_depth(self):
        # type: () -> int
        return self._yield_only_at_depth

    @yield_only_at_depth.setter
    def yield_only_at_depth(self, value):
        # type: (int) -> None
        self._yield_only_at_depth = value
