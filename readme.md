# Process arxiv

In this project, we will parse arxiv latex file, restruct it(recomplie \newcommand and \input and so on) and extract figure/table or other information tag for training.

we use pylatexenc to parse the latex file.

### TODO

- [x] Parse latex using pylatexenc
- [x] reconstruct latex file
- [x] extract target function
- [x] Parse figure or other information 
- [ ] extract information
- [ ] format to internlmxcomposer training format.

### Usage


```
from gettext import find
import sys
import os
file_path = os.path.dirname(__file__)
print(file_path)
sys.path.append(os.path.join(file_path, "utils"))

import pylatexenc
from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexnodes import nodes as latexnodes_nodes
from pylatexenc.latexnodes import parsers as latexnodes_parsers
from pylatexenc import _util,macrospec,latexwalker

from process import (
    reconstruct_latex, get_all_figure)

file_path = "./example/a.tex"


with open(file_path, "r") as fp:
    latex_data = fp.read()
    
reconstruct_latex_data = reconstruct_latex(latex_data)

all_figure = get_all_figure(reconstruct_latex_data)

print(all_figure)
```
