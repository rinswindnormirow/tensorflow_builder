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

                if max_bzl_version_str != '' and min_bzl_version_str != '':
                    return (__find_version(min_bzl_version_str), __find_version(max_bzl_version_str))

            else:
                if 'check_bazel_version' in line:
                    min_bzl_version_str = line

                    l_brace_ind = min_bzl_version_str.find('(')
                    r_brace_ind = min_bzl_version_str.find(')')
                    min_bzl_version_str = min_bzl_version_str[l_brace_ind+1:r_brace_ind]

                    if not min_bzl_version_str[1].isdigit():
                        continue

                    if int_version <= version_to_int('1.12'):
                        return (min_bzl_version_str, min_bzl_version_str)
                    else:
                        segments = min_bzl_version_str.split(',')
                        return (segments[0], segments[1])

    return None


        # print(min_bzl_version_str)
        # print(max_bzl_version_str)


def get_bazel(version):
    # https://github.com/bazelbuild/bazel/releases/download/0.29.1/bazel-0.29.1-installer-linux-x86_64.sh
    bazel_url = 'https://github.com/bazelbuild/bazel/releases/download/{0}/bazel-{0}-installer-linux-x86_64.sh'.format(version)
    bazel_dir = 'bazel_{}'.format(version)

    os.system('rm -rf ./' + bazel_dir)

    command = 'wget -P' + ' ' + bazel_dir + ' ' + bazel_url
    subprocess.run([command], shell=True, check=True)

    current_dir = os.getcwd()

    # os.system('cd ./{}'.format(bazel_dir))
    os.system('chmod +x ./{0}/bazel-{1}-installer-linux-x86_64.sh'.format(bazel_dir, version))
    os.system('mkdir ./{0}/bin'.format(bazel_dir))
    # os.system('mkdir ./{0}/bin/bazel'.format(bazel_dir))
    os.system('mkdir ./{0}/lib/'.format(bazel_dir))
    os.system('mkdir ./{0}/lib/bazel'.format(bazel_dir))

    bzl_install_command = './{1}/bazel-{0}-installer-linux-x86_64.sh --prefix={2}/{1}'.format(version, bazel_dir, current_dir)
    subprocess.run([bzl_install_command], shell=True, check=True)
    return current_dir + '/{}'.format(bazel_dir) + '/bin'


def tf_configure(tf_path, python_location, python_library_location, apache_ignite_support, XLAJIT, opencl, rocm, cuda, cuda_version,
                 cuda_location):

    command = tf_path + '/configure'

    configure_proc = subprocess.Popen([command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    # poll check if child process has terminated
    while configure_proc.poll() is None:
        line = configure_proc.stdout.readline()
        print(line)
        if 'location of python' in line:
            configure_proc.stdin.write(python_location + '\\n')
        elif 'Python library path' in line:
            pass
        pass


def main():

    parser = argparse.ArgumentParser(description='tensorflow 1.xx build and install')
    parser.add_argument("--t", default='1.12', help='tensorflow version')
    parser.add_argument("--i", default='/usr/lib/', help='destination directory')
    parser.add_argument("--s", default='', help='destination directory')

    parser.add_argument("--python-location", default='/usr/bin/python', help='python interpreter location')
    parser.add_argument("--python-library-location", default='\\n', help='python library path (empty == default)')
    parser.add_argument("--apache-ignite-support", default='n')
    parser.add_argument("--XLA-JIT", default='n')
    parser.add_argument("--opencl-sycl", default='n')
    parser.add_argument("--rocm", default='n')
    parser.add_argument("--CUDA", default='y')
    parser.add_argument("--CUDA-VERSION", default='')
    parser.add_argument("--CUDA-toolkit-location", default='')

    args = parser.parse_args()
    version = args.t
    destination = args.i
    suffix = args.s

    python_location = args.python_location
    python_library_location = args.python_library_location
    apache_ignite_support = args.apache_ignite_support
    XLA_JIT = args.XLA_JIT
    opencl_sycl = args.opencl_sycl
    rocm = args.rocm
    CUDA = args.CUDA
    CUDA_VERSION = args.CUDA_VERSION
    CUDA_toolkit_location = args.CUDA_toolkit_location

    min_v = version_to_int(min_tf_version)
    max_v = version_to_int(max_tf_version)

    if min_v < version_to_int(version) > max_v:
        return "Version TF {0} out of range min {1} or max {2} TF version".format(version, min_tf_version,
                                                                                  max_tf_version)

    # tf_path = git_clone(version)

    # for debug
    tf_path = 'tf_' + 'r' + version
    bzl_version = check_bazel_version(tf_path, version)
    print("---- detected bazel version: {} ----".format(bzl_version[0]))
    bzl_path = get_bazel(bzl_version[0])
    print(bzl_path)

    tf_configure(tf_path, python_location, python_library_location, apache_ignite_support,
                 XLA_JIT, opencl_sycl, rocm, CUDA, CUDA_VERSION, CUDA_toolkit_location);

main()
