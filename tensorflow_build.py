#! /usr/bin/python3

import os
from os import path
import argparse
import subprocess

def git_clone(version):
    version_tf = 'r' + version
    git_repo_path = 'https://github.com/tensorflow/tensorflow'
    dir_name = 'tf_' + 'r' + version

    # check exist directory $dir_name

    if path.exists("./" + dir_name):
        os.system("rm -rf ./" + dir_name)


    command = 'git clone -b ' + version_tf + ' ' + git_repo_path + ' ' + dir_name
    # stream = os.system(command)
    # subprocess.run(["ls", "-l", "/dev/null"], capture_output=True)
    subprocess.run([command], shell=True, check=True)

def check_bazel_version(path):
    pass

def get_bazel(url, version):
    pass

def main():
    version = '1.12'
    destination = '/usr/lib/'
    suffics = ''

    parser = argparse.ArgumentParser(description='tensorflow 1.xx build and install')
    parser.add_argument("--t", default='1.12', help='tensorflow version')
    parser.add_argument("--i", default='', help='destination directory')
    parser.add_argument("--s", default='', help='destination directory')

    args = parser.parse_args()
    version = args.t
    destination = args.i
    suffics = args.s

    git_clone(version)

main()
