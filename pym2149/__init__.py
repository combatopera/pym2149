import pyximport, numpy as np

# Note -O3 is apparently the default:
pyximport.install(setup_args = {'include_dirs': np.get_include()}, inplace = True)
