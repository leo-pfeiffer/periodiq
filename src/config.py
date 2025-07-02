import os
from dotenv import dotenv_values

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
CONFIG = dotenv_values(ROOT_DIR + '/.env', verbose=True)
