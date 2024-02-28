import sys

sys.path.append("/fs-computility/llm/shared/feizhaoye/code/utils/pylatexenc")

import pylatexenc
from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexnodes import nodes as latexnodes_nodes
from pylatexenc.latexnodes import parsers as latexnodes_parsers
from pylatexenc import _util,macrospec,latexwalker


default_node_type_dict = {
    "document": [latexnodes_nodes.LatexEnvironmentNode, "document", "environmentname"],
    "figure": [latexnodes_nodes.LatexEnvironmentNode, "figure", "environmentname"],
    "newcommand": [latexnodes_nodes.LatexMacroNode, "newcommand", "macroname"],
    "table": [latexnodes_nodes.LatexEnvironmentNode, "table", "environmentname"]
}

def find_all_target(nodelist, target, node_type = None, attr_name=None):
    targetnode_list = []
    
    if node_type is None or attr_name is None:
        if target not in default_node_type_dict.keys():
            raise NotImplementedError("must give `target`, `node_type` and `attr_name`")
        node_type, target, attr_name = default_node_type_dict[target]
    
    for node in nodelist:
        try:
            if isinstance(node, node_type) and getattr(node, attr_name) == target:
                targetnode_list.append(node)
            elif hasattr(node, "nodelist"):
                targetnode_list.extend(find_all_target(node.nodelist, target, node_type=node_type, attr_name=attr_name))
        except Exception as e:
            print(node)
            print(e)
            raise e
    return targetnode_list

def find_node(node, target_name):

    targetnode_list = []
    
    all_attr = node.__dir__()
    nodename_attr = ""
    for attr in all_attr:
        if attr.endswith("name"):
            nodename_attr = attr
            break
    if nodename_attr != "":
        if getattr(node, nodename_attr) == target_name:
            targetnode_list.append(node.latex_verbatim())
        if hasattr(node, "nodelist"):
            for sub_node in node.nodelist:
                targetnode_list.extend(find_node(sub_node, target_name))
    return targetnode_list

def strip_single(latex_code, delimiters):
    if latex_code == "":return latex_code
    if latex_code[0] is delimiters[0] and latex_code[-1] is delimiters[1]:
        return latex_code[1:-1]
    else:
        return latex_code
    

def parse_newcommand(newcommand_node):
    # newcommand_latex = newcommand_node.latex_verbatim()
    arg_list = newcommand_node.nodeargd.argnlist
    assert len(arg_list) == 5, arg_list
    # print(arg_list[1].delimiters)
    command_name = strip_single(arg_list[1].latex_verbatim(), arg_list[1].delimiters).lstrip("\\")
    if arg_list[2] is None:
        numargs = None
    else:
        numargs = strip_single(arg_list[2].latex_verbatim(), arg_list[2].delimiters)
    if arg_list[3] is None:
        default_fpar = None
    else:
        default_fpar = strip_single(arg_list[3].latex_verbatim(), arg_list[3].delimiters)
    command_str = strip_single(arg_list[4].latex_verbatim(), arg_list[4].delimiters)
    return command_name, numargs, default_fpar, command_str
    

def get_new_context_db(newcommand_list):
    from pylatexenc import latexwalker, macrospec
    from pylatexenc.macrospec import std_macro

    lw_context_db = latexwalker.get_default_latex_context_db()
    lw_context_db.add_context_category(
        'newcommand',
        prepend=True,
        macros=[
            std_macro(new_command[0], True, int(new_command[1])) if new_command[1] is not None and isdigit(new_command[1]) else macrospec.MacroSpec(new_command[0], True, 0) for new_command in newcommand_list 
        ],
        environments=[],
        specials=[],
    )
    return lw_context_db


from pylatexenc.latexnodes import *
from pylatexenc.latexnodes._exctypes import *
from pylatexenc.latexnodes.nodes import *
    
class Node2latex():
    def __init__(self, new_command_list) -> None:
        self.newcommand_para_dict = {i[0]: i for i in new_command_list}

    def process_newcommand_func(self, node):
        command_name = node.macroname
        command_name, numargs, default_fpar, command_str = self.newcommand_para_dict[command_name]
        if numargs is None: return command_str
        args_list = []
        nodeargd = node.nodeargd
        for argt, argn in zip(nodeargd.argspec, nodeargd.argnlist):
            if argn is None: continue
            args_list.append(strip_single(self.nodelist_to_latex([argn]), ["{", "}"]))
        for i in range(int(numargs)):
            replace_tag = f"#{str(i+1)}"
            command_str = command_str.replace(replace_tag, args_list[i])
        
        return command_str
        

    
    def add_args(self, nodeargd):
        if nodeargd is None or nodeargd.argspec is None or nodeargd.argnlist is None:
            return ''
        argslatex = ''
        for argt, argn in zip(nodeargd.argspec, nodeargd.argnlist):
            if argt == '*':
                if argn is not None:
                    argslatex += self.nodelist_to_latex([argn])
            elif argt == '[':
                if argn is not None:
                    # the node is a group node with '[' delimiter char anyway
                    argslatex += self.nodelist_to_latex([argn])
            elif argt == '{':
                # either a group node with '{' delimiter char, or single node argument
                argslatex += self.nodelist_to_latex([argn])
            else:
                raise ValueError("Unknown argument type: {!r}".format(argt))
        return argslatex
        
    
    def nodelist_to_latex(self, nodelist):

        # It's NOT recommended to use this function.  You should use
        # node.latex_verbatim() instead.

        # Here, we don't use latex_verbatim() and continue to provide (an updated
        # version of) the old code, because we want to be compatible with code that
        # used this function on custom instantiated nodes without setting the
        # parsing_state.
        
        # using this function, we can reconstruct all latex code and also 


        latex = ''
        for n in nodelist:
            if n is None:
                continue
            if n.isNodeType(LatexCharsNode):
                latex += n.chars
                continue

            if n.isNodeType(LatexMacroNode):
                if n.macroname in self.newcommand_para_dict.keys():
                    latex += self.process_newcommand_func(n)
                else:
                    latex += r'\%s%s%s' %(n.macroname, n.macro_post_space, self.add_args(n.nodeargd))
                continue

            if n.isNodeType(LatexSpecialsNode):
                latex += r'%s%s' %(n.specials_chars, self.add_args(n.nodeargd))
                continue
            
            if n.isNodeType(LatexCommentNode):
                latex += '%'+n.comment+n.comment_post_space
                continue
            
            if n.isNodeType(LatexGroupNode):
                latex += n.delimiters[0] + self.nodelist_to_latex(n.nodelist) + n.delimiters[1]
                continue
            
            if n.isNodeType(LatexEnvironmentNode):
                latex += r'\begin{%s}%s' %(n.envname, self.add_args(n.nodeargd))
                latex += self.nodelist_to_latex(n.nodelist)
                latex += r'\end{%s}' %(n.envname)
                continue
            
            if n.isNodeType(LatexMathNode):
                latex += n.delimiters[0] + self.nodelist_to_latex(n.nodelist) + n.delimiters[1]
                continue
            
            latex += "<[UNKNOWN LATEX NODE: \'%s\']>"%(n.nodeType().__name__)

        return latex


if __name__ == '__main__':
        
    dir_path = "/fs-computility/llm/shared/feizhaoye/datasets/origin_data/arxiv/test-2023-05-30"
    import os
    import json
    import logging
    logger = logging.getLogger("pylatexenc")
    # logger.setLevel(logging.DEBUG)
    # logging.basicConfig(level=logging.DEBUG)
    all_data = []

    for i,j,k in os.walk(dir_path):
        if j != []:continue
        for file_name in k:
            file_path = os.path.join(i, file_name)
            if file_path.endswith(".json"):
                with open(file_path, "r") as fp:
                    all_data.append(json.loads(fp.read()))

    for i in range(1):
        print("="*10)
        w = LatexWalker(all_data[i]['content'])   
        parser = latexnodes_parsers.LatexGeneralNodesParser()

        res = w.parse_content(latexnodes_parsers.LatexGeneralNodesParser())

        all_newcommand = [parse_newcommand(newcommand) for newcommand in find_all_target(res[0], "newcommand")]
        print(all_newcommand)
        new_db = get_new_context_db(all_newcommand)
        new_w = LatexWalker(all_data[i]['content'], latex_context=new_db)
        nodelist, pos, length = new_w.get_latex_nodes()
        
        nodelist = find_all_target(nodelist, "document")
        print(len(nodelist))
        reconstruct_latex = Node2latex(all_newcommand).nodelist_to_latex(nodelist)
        
        w = LatexWalker(reconstruct_latex)   
        parser = latexnodes_parsers.LatexGeneralNodesParser()
        nodelist, pos, length = w.get_latex_nodes()
        all_figure = find_all_target(nodelist, "figure")
        for i in all_figure:
            print(i.latex_verbatim())
            print(i)
    