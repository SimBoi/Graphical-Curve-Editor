
Setup
=====

From Pycharm
------------

1. git clone directory  
2. open directory as pycharm project
3. pycharm will suggest environment.yml as new conda env
4. open terminal and activate environment:
<br> <code>conda env activate cagd_hw</code>
5. pip install opengl:
<br> <code>pip install .\PyOpenGL-3.1.6-cp310-cp310-win_amd64.whl</code>
<br> <code>pip install .\PyOpenGL_accelerate-3.1.6-cp310-cp310-win_amd64.whl</code>


From Terminal
-------------

cd into project root:
<br> <code>cd [project root]</code>

Create environment:
<br> <code>conda env create -f environment.yml</code>

Activate environment:
<br> <code>conda env activate cagd_hw</code>

Pip install opengl:
<br> <code>pip install .\PyOpenGL-3.1.6-cp310-cp310-win_amd64.whl</code>
<br> <code>pip install .\PyOpenGL_accelerate-3.1.6-cp310-cp310-win_amd64.whl</code>


Run Main (beyond here is outdated but can help)
========
To ensure things are working properly, run main script:
<br> <code>python main.py </code>

Executable
==========
Run the ``build.py`` script and make sure ``exprtree.so`` is in the same folder as the executable.

Our .dat File
=============
Our .dat file can be found under ``FrenetData`` folder with the name ``mustafa_hamza.dat``: ``FrenetData\mustafa_hamza.dat`` 