import sys

from fixtures.test_directory import test_directory

sys.modules['waflib.extras.wurf'] = ""
sys.modules['waflib.extras.wurf.wurf_registry'] = __import__('wurf_registry')

#print(sys.modules)
#exit(0)
