import logging
import pprint

from maya.api import OpenMaya as om2

from ..dag import dag_iter
from . import dg_utils


logger = logging.getLogger(__name__)
_pf = pprint.PrettyPrinter(indent=4).pformat

try:
    from typing import Iterable, Union
except:
    pass


# TODO: Implement behaviour to lookup the value type to infer the setter method.
def _set_plug_value(mobjs, plug_name, plug_value):
    # type: (Iterable[Union[str, om2.MDagPath, om2.MObject]], str, any) -> None

    dep_node = om2.MFnDependencyNode()

    for mobj in map(dg_utils.as_mObject, mobjs):

        node_plug = dep_node.setObject(mobj).findPlug(plug_name, False)
        try:
            node_plug.setBool(plug_value)

        except RuntimeError as err:
            node_plug_ = node_plug.name().split('|')[-1]
            msg = 'Could not set "{node_plug_}"\n Reason:\n{err}'
            logger.error(msg.format(**locals()))


def _set_visibility(mobjs, show_nodes=None):
    # type: (Iterable[om2.MObject], Iterable[str]) -> None

    attr_name = 'visibility'

    nodes_to_show = set(show_nodes or [])
    dep_node = om2.MFnDependencyNode()

    msg_ = []

    for mobj in mobjs:

        dep_node.setObject(mobj)
        node_plug = dep_node.findPlug(attr_name, False)
        node_sn = dg_utils.get_shortname(node_plug.name().split('.')[0])

        choice = bool(node_sn in nodes_to_show)
        # TODO: improve handling to be more explicit for values that can't be changed.
        try:
            node_plug.setBool(choice)

        except RuntimeError as err:
            node_plug_ = node_plug.name().split('|')[-1]
            err_msg = 'Could not set "{node_plug_}"\n Reason:\n{err}'
            logger.error(err_msg.format(**locals()))

        msg_.append('{v} : {p}.{a}'.format(
            p=om2.MDagPath.getAPathTo(mobj).fullPathName(),
            a=attr_name, v=choice)
        )

    print _pf(msg_)


def set_visibility_all_transforms(value):
    # type: (bool) -> None
    _set_plug_value(dag_iter.itransforms(), 'visibility', value)


def set_visibility_all_meshs(value):
    # type: (bool) -> None
    _set_plug_value(dag_iter.IMeshs.iter(), 'visibility', value)


# def set_visibility_by_fullpath(mobjs, show_nodes=None):
#     # type: (Iterable[om2.MObject], typing.Iterable[str]) -> None
#     """From the given `mobjs`, set visible only those whose shortname match any of the given `show_nodes`.
#
#     Args:
#         mobjs list[MObject]: DAG nodes to affect display on.
#         show_nodes list[str]: Short node names to set visibility to True. All other nodes will be set to hidden.
#
#     """
#     _set_visibility(mobjs, show_nodes)


def set_visibility_by_shortname(mobjs, show_nodes=None):
    # type: (Iterable[om2.MObject], Iterable[str]) -> None
    """From the given `mobjs`, set visible only those whose shortname match any of the given `show_nodes`.

    Args:
        mobjs list[MObject]: DAG nodes to affect display on.
        show_nodes list[str]: Short node names to set visibility to True. All other nodes will be set to hidden.

    """
    _set_visibility(mobjs, show_nodes)
