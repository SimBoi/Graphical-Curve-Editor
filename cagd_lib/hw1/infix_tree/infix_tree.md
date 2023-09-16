

Producing Shared Library
========================
<p>
    <code> cd infix_tree</code> <br>
    <code> gcc -fPIC -shared -o expr2tree.so expr2tree.c</code> <br>
will produce the <code>expr2tree.so</code> file.
</p>

Then you must move the file to the project root and copy it to ``dist`` folder if an executable shoulf be built.