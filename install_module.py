from sys import executable as exe
import subprocess

def install_module(module_name:str, target:str=None):
  """Download and install a python library or update.
  Parameters
  ----------
  module_name : str
    The name of the module to install
  target : str, None (Optional)
    The target file path to install the module. If None will use the '--user' command
  """
  args = [exe, '-m', 'ensurepip', '--user', '--upgrade', '--default-pip']
  if subprocess.call(args=args):
      return

  args = [exe, '-m', 'pip', 'install', f'-t={target}' if target else '--user', '--upgrade', module_name]
  if subprocess.call(args=args):
      return
