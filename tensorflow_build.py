#! /usr/bin/python3

import os
from os import path
import argparse
import subprocess

min_tf_version = '1.11'
max_tf_version = '1.15'


def version_to_int(version):
    segments = version.split('.')
    for seg in segments:
        if not seg.isdigit():
            return None

    str = ''.join(['{0}'.format(s) for s in segments])
    return int(str)


def git_clone(version):
    version_tf = 'r' + version
    git_repo_path = 'git://github.com/tensorflow/tensorflow.git'
    # git_repo_path = 'git@github.com:tensorflow/tensorflow.git'
    dir_name = 'tf_' + 'r' + version

    # check exist directory $dir_name
    if path.exists("./" + dir_name):
        os.system("rm -rf ./" + dir_name)

    command = 'git clone -b ' + version_tf + ' ' + git_repo_path + ' ' + dir_name
    subprocess.run([command], shell=True, check=True)
    return dir_name


def check_bazel_version(path, version):
    int_version = version_to_int(version)

    min_bzl_version_str = ''
    max_bzl_version_str = ''

    with open('./' + path + '/configure.py') as tf_conf_file:

        for line in tf_conf_file:

            def __find_version(str):
                seg = str.split('=')
                l_pos = seg[1].find('\'')
                r_pos = seg[1].rfind('\'')
                return seg[1][l_pos+1:r_pos]

            if int_version > version_to_int('1.14'):
                if '_TF_MIN_BAZEL_VERSION' in line:
                    min_bzl_version_str = line
                if '_TF_MAX_BAZEL_VERSION' in line:
                    max_bzl_version_str = line

                return (__find_version(min_bzl_version_str), __find_version(max_bzl_version_str))

            else:
                if 'check_bazel_version' in line:
                    min_bzl_version_str = line

                    l_brace_ind = min_bzl_version_str.find('(')
                    r_brace_ind = min_bzl_version_str.find(')')
                    min_bzl_version_str = min_bzl_version_str[l_brace_ind+1:r_brace_ind]

                    if int_version <= version_to_int('1.12'):
                        return (min_bzl_version_str, min_bzl_version_str)
                    else:
                        segments = min_bzl_version_str.split(',')
                        return (segments[0], segments[1])


        # print(min_bzl_version_str)
        # print(max_bzl_version_str)


def get_bazel(version):
    # https://github.com/bazelbuild/bazel/releases/download/0.29.1/bazel-0.29.1-installer-linux-x86_64.sh
    bazel_url = 'https://github.com/bazelbuild/bazel/releases/download/{0}/bazel-{0}-installer-linux-x86_64.sh'.format(version)
    command = 'wget -P bazel_{} '.format(version) + bazel_url
    subprocess.run([command], shell=True, check=True)


def main():
    version = '1.12'
    destination = '/usr/lib/'
    suffix = ''

    parser = argparse.ArgumentParser(description='tensorflow 1.xx build and install')
    parser.add_argument("--t", default='1.12', help='tensorflow version')
    parser.add_argument("--i", default='', help='destination directory')
    parser.add_argument("--s", default='', help='destination directory')

    args = parser.parse_args()
    version = args.t
    destination = args.i
    suffix = args.s

    min_v = version_to_int(min_tf_version)
    max_v = version_to_int(max_tf_version)

    if min_v < version_to_int(version) > max_v:
        return "Version TF {0} out of range min {1} or max {2} TF version".format(version, min_tf_version,
                                                                                  max_tf_version)

    tf_path = git_clone(version)

    # for debug
    # tf_path = 'tf_' + 'r' + version
    check_bazel_version(tf_path, version)


main()
