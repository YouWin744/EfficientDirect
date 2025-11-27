import cvxpy as cp

print("已安装的求解器:", cp.installed_solvers())

print(cp.settings.__file__)