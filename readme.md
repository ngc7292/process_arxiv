# Process arxiv

In this project, we will parse arxiv latex file, restruct it(recomplie \newcommand and \input and so on) and extract figure/table or other information tag for training.

we use pylatexenc to parse the latex file.

### TODO

- [x] Parse latex using pylatexenc
- [x] reconstruct latex file
- [x] extract target function
- [ ] Parse figure or other information 
- [ ] extract information
- [ ] format to internlmxcomposer training format.

### Usage


```
cd process_code
python process.py
```
