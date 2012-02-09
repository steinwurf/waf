#! /usr/bin/env python
# encoding: utf-8

import os

from waflib.Configure import conf
from waflib import Context
from waflib import Utils

try:
    import _winreg
except:
    try:
        import winreg as _winreg
    except:
        _winreg = None

def find_in_winreg():
    """
    Look in the windows reg database for traces
    of the msysgit installer
    """

    reg_value = reg_type = None

    try:
        reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                  'SOFTWARE\\Wow6432node\\Microsoft'
                                  '\\Windows\\CurrentVersion\\'
                                  'Uninstall\\Git_is1')

        (reg_value, reg_type) = _winreg.QueryValueEx(reg_key,
                                                     'InstallLocation')

        
    except WindowsError as e:
     
        try:
            reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                      'SOFTWARE\\Microsoft'
                                      '\\Windows\\CurrentVersion\\'
                                      'Uninstall\\Git_is1')

            (reg_value, reg_type) = _winreg.QueryValueEx(reg_key,
                                                         'InstallLocation')
            
        except WindowsError:
            pass

    if reg_type == _winreg.REG_SZ:
        return str(reg_value)
    else:
        return ''

        
            

def find_git_win32(conf):
    """
    Attempt to find the git binary on windows
    """
    path = find_in_winreg()

    if path:
        path_list = [path, os.path.join(path, 'bin')]
        conf.find_program('git', path_list = path_list)
    else:
        conf.find_program('git')


def options(opt):
    pass


def configure(conf):

    if Utils.is_win32:
        find_git_win32(conf)
    else:
        conf.find_program('git')


    
@conf
def git_cmd_msg(self, cmd, **kw):
    """
    Runs a git command and writes the result
    to users 
    """

    self.start_msg('Running git %s ' % ' '.join(cmd))

    try:
        
        o = self.git_cmd_and_log(cmd, **kw)
        self.end_msg('ok')

    except Exception as e:

        self.end_msg('failed', 'YELLOW')
        self.fatal(e.stderr)

    return o

    
@conf
def git_cmd_and_log(self, cmd, **kw):
    """
    Runs a git command
    """

    cmd = Utils.to_list(cmd)
    cmd = [self.env['GIT']] + cmd
    
    return self.cmd_and_log(cmd, **kw)
    

@conf
def git_tags(self, repo_dir):
    """
    Runs git tag -l and retuns the tags
    """

    o = self.git_cmd_and_log('tag -l', cwd = repo_dir)
    tags = o.split('\n')
    return [t for t in tags if t != '']


@conf
def git_current_tag(self, repo_dir):
    """
    Runs git describe --tags and retuns the tags
    If exactly on a tag it will return that
    otherwise it will return <tag>-<n>-g<shortened sha-1>,
    where <n> is number of commits since <tag>
    """

    o = self.git_cmd_and_log('describe --tags', cwd = repo_dir)
    return o.strip()

@conf
def git_checkout(self, repo_dir, branch):
    """
    Runs git checkout in the working dir
    """
    self.git_cmd_and_log('checkout %s' % branch, cwd = repo_dir)


@conf
def git_pull(self, repo_dir):
    """
    Runs git pull in the working dir
    """
    self.git_cmd_and_log('pull', cwd = repo_dir)

@conf
def git_branch(self, repo_dir):
    """
    Runs git status in the working dir
    """
    o = self.git_cmd_and_log('branch', cwd = repo_dir)

    branch = o.split('\n')
    branch = [b for b in branch if b != '']

    current = ''
    others = []

    for b in branch:
        if b.startswith('*'):
            current = b[1:].strip()
        else:
            others.append(b)

    if current == '':
        self.fatal('Failed to locate current branch')

    return current, others

@conf
def git_has_submodules(self, repo_dir):
    """
    Returns true if the repository contains the .gitmodules file
    """
    return os.path.isfile(os.path.join(repo_dir, '.gitmodules'))

@conf
def git_submodule_init(self, repo_dir):
    """
    Runs git submodule init in the repo_dir
    """
    self.git_cmd_and_log('submodule init', cwd = repo_dir)

@conf
def git_submodule_update(self, repo_dir):
    """
    Runs git submodule init in the repo_dir
    """
    self.git_cmd_and_log('submodule update', cwd = repo_dir)


@conf
def git_clone(self, repo_url, **kw):
    """
    Clone a repository
    """
    cmd = ['clone']

    local = kw.get('local', False)
    if local:
        cmd.append('-l')
        del kw['local']

    cmd.append(repo_url)

    destdir = kw.get('destdir', '')
    if destdir:
        cmd.append(destdir)
        del kw['destdir']

    self.git_cmd_msg(cmd, **kw)



@conf
def repository_clone(self, repo_dir, repo_url):
    """
    Ensures that a repository is cloned and exists
    """
    if not os.path.isdir(repo_dir):
        self.to_log("repository dir %s not found" % repo_dir)

        self.git_clone(repo_url, destdir = repo_dir)
            
    self.git_pull(repo_dir)


@conf
def repository_check(self, repo_dir, **kw):
    """
    This function is used to check the status of a repository
    """
    if 'branch' in kw:
        (current, others) = self.git_branch(repo_dir)

        self.to_log("check branch %r => current %r, other %r" %
                    (repo_dir, current, others))

        if current != kw['branch']:
            self.fatal('Unexpected branch %s was %s expected %s' %
                       repo_dir, current,  kw['branch']) 

    if 'tag' in kw:
        tag = self.current_tag(repo_dir)

        if tag != kw['tag']:
            self.fatal('Unexpected tag %s was %s' % (tag, kw['tag']))

        
@conf
def local_clone_tag(self, from_repo_dir, to_repo_dir, tag):
    """
    Performs a local clone of a repository and checkout
    a specific tag
    """

    tags = self.git_tags(from_repo_dir)

    if not tag in tags:
        self.fatal('Trying to clone non existing tag %s -> %s, tag %s' %
                   (from_repo_dir, to_repo_dir, tag))

    if os.path.isdir(to_repo_dir):
        self.to_log('repository dir %s already found' % to_repo_dir)

        to_repo_tag = self.git_current_tag(to_repo_dir)

        if to_repo_tag != tag:
            self.fatal('repository %s on wrong tag %s expected %s' %
                       (to_repo_dir, to_repo_tag, tag))

    else:
        if Utils.is_win32:
            # git on windows currently does not support local clones
            self.git_clone(from_repo_dir, destdir = to_repo_dir)
        else:
            self.git_clone(from_repo_dir, destdir=to_repo_dir, local=True)
            
        self.git_checkout(to_repo_dir, tag)



    
