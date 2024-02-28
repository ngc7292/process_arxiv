from ast import arg
from fileinput import filename
import sys
import os
file_path = os.path.dirname(__file__)
sys.path.append(os.path.join(file_path, "utils"))

import pylatexenc
from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexnodes import nodes as latexnodes_nodes
from pylatexenc.latexnodes import parsers as latexnodes_parsers
from pylatexenc import _util,macrospec,latexwalker


default_node_type_dict = {
    "document": [latexnodes_nodes.LatexEnvironmentNode, "document", "environmentname"],
    "figure": [latexnodes_nodes.LatexEnvironmentNode, "figure", "environmentname"],
    "figure*": [latexnodes_nodes.LatexEnvironmentNode, "figure*", "environmentname"],
    "newcommand": [latexnodes_nodes.LatexMacroNode, "newcommand", "macroname"],
    "table": [latexnodes_nodes.LatexEnvironmentNode, "table", "environmentname"],
    "subfigure": [latexnodes_nodes.LatexEnvironmentNode, "subfigure", "environmentname"],
    "subtable": [latexnodes_nodes.LatexEnvironmentNode, "subtable", "environmentname"],
    
    "label": [latexnodes_nodes.LatexMacroNode, "label", "macroname"],
    "caption": [latexnodes_nodes.LatexMacroNode, "caption", "macroname"],
}

default_multinode_type_dict = {
    "_realfigure": [
        [latexnodes_nodes.LatexMacroNode, "includegraphics", "macroname"], 
        [latexnodes_nodes.LatexMacroNode, "epsfig", "macroname"], 
    ],
}

def rfind_multi_all_target(nodelist, target):
    targetnode_list = []
    
    assert target in default_multinode_type_dict.keys(), NotImplementedError

    attr_list = default_multinode_type_dict[target]
    for node in nodelist:
        try:
            for node_type, target_name, attr_name in attr_list:
                if isinstance(node, node_type) and getattr(node, attr_name) == target_name:
                    targetnode_list.append(node)
                    break
            if isinstance(node, latexnodes_nodes.LatexEnvironmentNode) and getattr(node, "environmentname") not in ["subfigure", "subtable"]: # get subfigure or subtable exit
                targetnode_list.extend(rfind_multi_all_target(node.nodelist, target))
            elif isinstance(node, latexnodes_nodes.LatexGroupNode):
                targetnode_list.extend(rfind_multi_all_target(node.nodelist, target))
        except Exception as e:
            print(node)
            print(e)
            print(target)
            raise e
    return targetnode_list

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
        except Exception as e:
            print(node)
            print(e)
            raise e
    return targetnode_list

def rfind_all_target(nodelist, target, node_type = None, attr_name=None):
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
                targetnode_list.extend(rfind_all_target(node.nodelist, target, node_type=node_type, attr_name=attr_name))
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
            std_macro(new_command[0], True, int(new_command[1])) if new_command[1] is not None and new_command[1].isdigit() else macrospec.MacroSpec(new_command[0], True, 0) for new_command in newcommand_list 
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
    
    

def extract_figure_information_from_envnode(node: latexnodes_nodes.LatexEnvironmentNode):
    assert node.environmentname in ["figure", "figure*", "subfigure"]
    all_file_path_nodes = rfind_multi_all_target(node.nodelist, "_realfigure")
    label_nodes = find_all_target(node.nodelist, "label")
    caption_nodes = find_all_target(node.nodelist, "caption")
    
    file_paths = []
    if all_file_path_nodes != []:
        
        for file_path_node in all_file_path_nodes:
            if file_path_node.macroname == "includegraphics":
                argn = file_path_node.nodeargd.argnlist[1]
                
                file_path = strip_single(argn.latex_verbatim(), argn.delimiters)
                file_paths.append(file_path)
            elif file_path_node.macroname == 'epsfig':
                argn = file_path_node.nodeargd.argnlist[1]
                file_path = strip_single(argn.latex_verbatim(), argn.delimiters)
                real_path = ""
                if "," in file_path and file_path_node.macroname == 'epsfig':
                    for s in file_path.split(","):
                        key, value = s.split("=")
                        if key == "file":
                            real_path = value
                if real_path == "":
                    print(file_path_node)
                    raise NotImplementedError
                file_paths.append(real_path)
    
    labels = []
    if label_nodes != []:
        for label_node in label_nodes:
            for argn in label_node.nodeargd.argnlist:
                if argn is None: continue
                label = argn.latex_verbatim() # not think multi label
                labels.append(strip_single(label, argn.delimiters))
                break
            
    captions = [] # only one caption
    if caption_nodes != []:
        caption_node = caption_nodes[0]

        for argn in caption_node.nodeargd.argnlist:
            if argn is None: continue
            caption = argn.latex_verbatim() # not think multi label
            captions.append(strip_single(caption, argn.delimiters))
            break
            
    return {
        "file_paths": file_paths,
        "labels": labels,
        "caption": captions[0]
    }
    
def get_all_information_from_figurenode(node: latexnodes_nodes.LatexEnvironmentNode):
    """
    1. find subfigure
    2. extract figure information
    
    convert node(figure, table, etc.) to list:
    {
        labels: xxx,
        caption: xxx,
        origin_latex: xxx,
        figures:[{
            file_paths: xxx,
            labels: xxx
            caption: xxx
            }]
    }
    
    maybe:
    
    label 1 -> figure 1, figure 2 (figure's label)
    label 2 -> figure 1, figure 2 (figure's label)
    label 3 -> figure 1 (subfigure's label)
    
    """
    subsetnode_list = [node] # may be not subset
    subsetnode_list.extend(rfind_all_target(node.nodelist, "subfigure"))
    
    res = extract_figure_information_from_envnode(node)
    res["origin_latex"] = node.latex_verbatim()
    res['figures'] = []
    
    for subsetnode in subsetnode_list:
        res['figures'].append(extract_figure_information_from_envnode(subsetnode))
    return res

def get_all_figure(latex_data):
    all_figure_list = []
    w = LatexWalker(latex_data)   
    parser = latexnodes_parsers.LatexGeneralNodesParser()
    res = w.parse_content(parser)

    all_target = rfind_all_target(res[0], "figure")
    all_target.extend(rfind_all_target(res[0], "figure*"))
    for i in all_target:
        a = get_all_information_from_figurenode(i)
        all_figure_list.append(a)
    return all_figure_list

def reconstruct_latex(origin_latex):
    w = LatexWalker(origin_latex)   
    parser = latexnodes_parsers.LatexGeneralNodesParser()

    res = w.parse_content(parser)

    all_newcommand = [parse_newcommand(newcommand) for newcommand in rfind_all_target(res[0], "newcommand")]
    new_db = get_new_context_db(all_newcommand)
    new_w = LatexWalker(origin_latex, latex_context=new_db)
    nodelist, pos, length = new_w.get_latex_nodes()

    nodelist = rfind_all_target(nodelist, "document")

    return Node2latex(all_newcommand).nodelist_to_latex(nodelist)