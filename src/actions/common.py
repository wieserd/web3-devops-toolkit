import os

def get_contracts_dir(params=None):
    """
    Returns the absolute path to the contracts directory.
    Uses params['contracts_dir'] if provided, otherwise defaults to '<project_root>/contracts'.
    """
    if params and isinstance(params, dict) and params.get('contracts_dir'):
        return os.path.abspath(params['contracts_dir'])
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(project_root, 'contracts')

def clean_env(env):
    """
    Remove pytest-specific and other volatile environment variables.
    """
    keys_to_remove = [
        k for k in env if k.startswith('PYTEST_') or k.startswith('TERM_') or k.startswith('SHLVL') or
        k.startswith('OLDPWD') or k.startswith('PWD') or k.startswith('_') or k.startswith('CONDA_') or
        k.startswith('HOMEBREW_') or k.startswith('INFOPATH') or k.startswith('DISPLAY') or
        k.startswith('npm_') or k.startswith('XPC_') or k.startswith('__CF_') or k.startswith('SSH_') or
        k.startswith('LOGNAME') or k.startswith('USER') or k.startswith('TMPDIR') or k.startswith('SHELL') or
        k.startswith('INIT_CWD') or k.startswith('NODE') or k.startswith('COLOR') or k.startswith('LANG') or
        k.startswith('EDITOR') or k.startswith('__CFBundleIdentifier') or
        k.startswith('OBJC_DISABLE_INITIALIZE_FORK_SAFETY') or k.startswith('__PYVENV_LAUNCHER__') or
        k.startswith('__VIRTUAL_ENV__') or k.startswith('VIRTUAL_ENV')
    ]
    for key in keys_to_remove:
        env.pop(key, None)
    return env
