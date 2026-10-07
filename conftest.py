"""pytest 根配置。

除了放共享 fixture，它的存在本身还有一个作用：pytest 会把 ``conftest.py``
所在目录加入 ``sys.path``，从而让 ``tests/`` 下的用例可以直接
``import env`` / ``import common``，不需要把仓库安装成包。
"""
