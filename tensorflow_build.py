#! /usr/bin/python3

import os
from os import path
import argparse
import subprocess

import shutil
from shutil import which
from functools import partial

min_tf_version = '1.11'
max_tf_version = '1.15'


def version_to_int(version):
    segments = version.split('.')
    for seg in segments:
        if not seg.isdigit():
            return None

    str = ''.join(['{0}'.format(s) for s in segments])
    return int(str)


def git_clone(version, no_download=False):
    version_tf = 'r' + version
    git_repo_path = 'git://github.com/tensorflow/tensorflow.git'
    # git_repo_path = 'git@github.com:tensorflow/tensorflow.git'
    dir_name = 'tf_' + 'r' + version

    if no_download == False:
        # check exist directory $dir_name
        if path.exists("./" + dir_name):
            os.system("rm -rf ./" + dir_name)

        command = 'git clone -b ' + version_tf + ' ' + git_repo_path + ' ' + dir_name
        subprocess.run([command], shell=True, check=True)
    else:
        if not path.exists("./" + dir_name) or not path.exists('./' + dir_name + '/.git'):
            command = 'git clone -b ' + version_tf + ' ' + git_repo_path + ' ' + dir_name
            subprocess.run([command], shell=True, check=True)



def check_true_tf_version(tf_dir):
    true_version = ''
    if path.exists(tf_dir + '/RELEASE.md'):
        with open(tf_dir + '/RELEASE.md') as rls:
            for line in rls:
                if '# Release' in line or '# release' in line:
                    seg = line.split(' ')
                    for s in seg:
                        if s[0].isdigit():
                            true_ = s
                            break
                    break
    else:
        print('can\'t detect true tf version')
        return -1

    for h in true_:
        if h.isdigit() or h == '.':
            true_version += h

    return true_version


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


def get_bazel(version, no_download=False):
    # https://github.com/bazelbuild/bazel/releases/download/0.29.1/bazel-0.29.1-installer-linux-x86_64.sh

    # version = version[version.find('\'') + 1: version.rfind('\'')]

    bazel_url = 'https://github.com/bazelbuild/bazel/releases/download/{0}/bazel-{0}-installer-linux-x86_64.sh'.format(version)
    bazel_dir = 'bazel_{}'.format(version)



    command = 'wget -P' + ' ' + bazel_dir + ' ' + bazel_url

    try:
        if no_download:
            if not path.exists('./' + bazel_dir + '/bazel-{0}-installer-linux-x86_64.sh'.format(version)):
                subprocess.run([command], shell=True, check=True)
        else:
            os.system('rm -rf ./' + bazel_dir)
            os.system('rm -rf ./bazel/bin')
            subprocess.run([command], shell=True, check=True)
    except subprocess.CalledProcessError:
        os.system('rm -rf ./' + bazel_dir)
        os.system('rm -rf ./bazel/bin')
        return -1

    current_dir = os.getcwd()

    os.system('chmod +x ./{0}/bazel-{1}-installer-linux-x86_64.sh'.format(bazel_dir, version))        #
    os.system('mkdir ./{0}/bin'.format(bazel_dir))                                                    # ${BAZEL_DIR}/bin
    os.system('mkdir ./{0}/lib/'.format(bazel_dir))                                                   # ${BAZEL_DIR}/lib
    os.system('mkdir ./{0}/lib/bazel'.format(bazel_dir))                                              # ${BAZEL_DIR}/lib/bazel

    os.system('mkdir ./bazel')
    os.system('mkdir ./bazel/bin')

    # bzl_install_command = './{1}/bazel-{0}-installer-linux-x86_64.sh --prefix={2}/{1}'.format(version, bazel_dir, current_dir)
    bzl_install_command = './{1}/bazel-{0}-installer-linux-x86_64.sh --prefix={2}/{1}'.format(version, bazel_dir,
                                                                                              current_dir)
    subprocess.run([bzl_install_command], shell=True, check=True)

    # add path to the bazel to $PATH
    old_path = os.environ['PATH']
    # new_path = old_path + ':' + current_dir + '/' + bazel_dir + '/bin'
    new_path = old_path + ':' + current_dir + '/bazel/bin'

    os.environ['PATH'] = new_path
    print(os.environ['PATH'])
    print(which('bazel'))


    os.system('ln -s {1}/{0}/lib/bazel/bin/bazel {1}/bazel/bin/'.format(bazel_dir, current_dir))

    return current_dir + '/{}'.format(bazel_dir) + '/bin'


def tf_configure(tf_path, python_location, python_library_location, apache_ignite_support, XLAJIT, opencl, rocm, cuda, cuda_version,
                 cuda_location, TensorRT, clang, mpi, opt_flag, android_wpc, jemalloc, google_cloud, hadoop_file_system,
                 amazon_aws_platform, kafka):

    def __stdin_write(child, str2write):
        child.stdout.flush()
        child.stdin.write(str2write + '\n')
        child.stdin.flush()

    print(tf_path)
    os.chdir('./' + tf_path)

    # command = './' + tf_path + '/configure'
    # os.system('chmod +x ' + command)
    print(os.getcwd())

    command = './configure.py'
    os.system('chmod +x ' + command)

    configure_proc = subprocess.Popen(['/usr/bin/python3', command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

    # poll check if child process has terminated
    while configure_proc.poll() is None:

        configure_proc.stdout.flush()
        configure_proc.stdin.flush()

        line = ''
        for c in iter(partial(configure_proc.stdout.read, 1), ''):
            if c == '\n' or c == ':':
                break
            line += c

        print(line)
        if 'location of python' in line:
            __stdin_write(configure_proc, python_location)
        elif 'desired Python library path' in line:
            __stdin_write(configure_proc, python_library_location)
        elif 'XLA JIT support? [Y/n]' in line or 'XLA JIT support?' in line:
            __stdin_write(configure_proc, XLAJIT)
        elif 'Apache Ignite Support' in line:
            __stdin_write(configure_proc, apache_ignite_support)
        elif 'OpenCL SYCL support? [y/N]' in line:
            __stdin_write(configure_proc, opencl)
        elif 'ROCm support? [y/N]' in line:
            __stdin_write(configure_proc, rocm)
        elif 'CUDA support? [y/N]' in line:
            __stdin_write(configure_proc, cuda)
        elif 'Do you wish to build TensorFlow with TensorRT support? [y/N]' in line:
            __stdin_write(configure_proc, TensorRT)
        elif 'fresh release of clang? (Experimental) [y/N]' in line:
            __stdin_write(configure_proc, clang)
        elif 'TensorFlow with MPI support? [y/N]' in line:
            __stdin_write(configure_proc, mpi)
        elif 'specify optimization flags' in line:
            __stdin_write(configure_proc, opt_flag)
        elif 'Android builds? [y/N]' in line:
            __stdin_write(configure_proc, android_wpc)
        elif 'Do you wish to build TensorFlow with jemalloc as malloc support? [Y/n]' in line:
            __stdin_write(configure_proc, jemalloc)
        elif 'Do you wish to build TensorFlow with Google Cloud Platform support? [Y/n]' in line:
            __stdin_write(configure_proc, google_cloud)
        elif 'Do you wish to build TensorFlow with Hadoop File System support? [Y/n]' in line:
            __stdin_write(configure_proc, hadoop_file_system)
        elif 'Do you wish to build TensorFlow with Amazon AWS Platform support? [Y/n]' in line:
            __stdin_write(configure_proc, amazon_aws_platform)
        elif 'Do you wish to build TensorFlow with Apache Kafka Platform support? [Y/n]' in line:
            __stdin_write(configure_proc, kafka)
        elif '[Y/n]' in line or '[y/N]' in line or '[y/n]' in line or '[Y/N]' in line:
            __stdin_write(configure_proc, 'n')

    os.chdir('..')


def tf_build(tf_dir):
    bazel = which('bazel')
    command = '{0} build --config=opt //tensorflow:libtensorflow_cc.so'.format(bazel)

    os.chdir('./' + tf_dir)

    subprocess.run([command], shell=True, check=True)
    os.chdir('..')


def __parser(wps, markers):
    res_string = ''
    n = 0
    lbo = False  # last but one
    for line in wps:
        # if markers[n] in line:
        b = 0
        if n == len(markers):
            break
        while line[b:].find(markers[n]) != -1:
            p = line.find(markers[n])

            if n < len(markers) - 2:
                n += 1
            else:
                if n == len(markers) - 2:
                    # res_string += line[p:]
                    line = line[p:]
                    lbo = True
                    n += 1
                    continue
                else:
                    # res_string += line[:p]
                    line = line[:p]
                    n += 1
                    break
                    # lbo = False

            b = p
        else:
            if lbo == True:
                res_string += line

    seg = res_string.split('\n')
    urls = []
    for s in seg:
        b = s.find('https')
        if b != -1:
            e = s[b:].rfind('\"')
            urls.append(s[b:b+e])
    return urls



def eigen_download_and_build(tf_dir, no_download=False):

    # detect eigen version urls
    with open('./' + tf_dir + '/tensorflow/workspace.bzl') as wps:
        urls = __parser(wps, ["eigen_archive", 'urls', '[', ']'])

    url = urls[0]

    command = 'wget -P ./eigen ' + url

    # download eigen
    if path.exists("./eigen") and no_download == False:
        os.system("rm -rf ./eigen")

    if not no_download or not path.exists("./eigen"):
        subprocess.run([command], shell=True, check=True)

    # extract tarball
    tarball = url[url.rfind('/') + 1:]
    os.chdir('./eigen')
    command = 'tar -xvf ' + tarball + ' --strip-components=1'
    subprocess.run([command], shell=True, check=True)

    # cmake
    os.system('mkdir ./build')
    os.chdir('./build')

    subprocess.run('cmake ..', shell=True, check=True)

    os.chdir('..')
    os.chdir('..')


def eigen_install(prefix):

    os.chdir('./eigen/build')

    # make install
    install_prefix = '/usr/local/include/eigen3_' + prefix
    if prefix != '':
        cmake = 'cmake . -DINCLUDE_INSTALL_DIR=' + install_prefix
        subprocess.run(cmake, shell=True, check=True)

    subprocess.run('make install', check=True, shell=True)

    os.chdir('..')
    os.chdir('..')


def protobuf_download_and_build(tf_dir, no_download=False):
    with open('./' + tf_dir + '/tensorflow/workspace.bzl') as wps:
        urls = __parser(wps, ["PROTOBUF_URLS", '[', ']'])

    url = urls[0]

    try:
        # download eigen
        if path.exists("./protobuf") and not no_download:
            os.system("rm -rf ./protobuf")

        if not no_download or not path.exists("./protobuf"):
            command = 'wget -P ./protobuf ' + url
            subprocess.run([command], shell=True, check=True)

        # extract tarball
        tarball = url[url.rfind('/') + 1:]
        os.chdir('./protobuf')
        command = 'tar -xvf ' + tarball + ' --strip-components=1'
        subprocess.run([command], shell=True, check=True)

        # autogen
        subprocess.run('./autogen.sh', shell=True, check=True)
        # configure
        subprocess.run('./configure', shell=True, check=True)
        # make
        subprocess.run('make', shell=True, check=True)
        # print('check')
        # subprocess.run('make check', shell=True, check=True)


    except subprocess.CalledProcessError:
        os.chdir('..')

    os.chdir('..')
    # os.chdir('..')


def protobuf_install():
    os.chdir('./protobuf')
    try:
        # make install
        subprocess.run('make install', shell=True, check=True)
    except subprocess.CalledProcessError:
        os.chdir('..')

    os.chdir('..')


def install_tensorflow(tf_path, version, install_prefix='/usr/local'):
    print('install tensorflow')
    old_dir = os.getcwd()
    base_bin_dir = './' + tf_path + '/bazel-bin/tensorflow'
    # os.chdir(base_bin_dir)

    # шаблон для libtensorflow_framework.so и для libtensorflow_cc.so:
    # libtensorflow_framework.so
    # libtensorflow_framework.so.${VERSION}.1
    # libtensorflow_cc.so
    # libtensorflow_cc.so.${VERSION}.1


    # install binary files

    base_install_binary_dir = install_prefix  + '/lib'

    try:

        print(base_bin_dir + '/libtensorflow_cc.so.{0}.0.1'.format(version))
        if path.exists(base_bin_dir + '/libtensorflow_cc.so') and not path.islink(base_bin_dir + '/libtensorflow_cc.so'):
            print('path {0} exists and is\'nt symbol link'.format(base_bin_dir + '/libtensorflow_cc.so'))
            shutil.copy(base_bin_dir + '/libtensorflow_cc.so'.format(version),
                        base_install_binary_dir + '/libtensorflow_cc.so.{0}.1'.format(version))

        elif path.exists(base_bin_dir + '/libtensorflow_cc.so.{0}.1'.format(version)) or path.exists(base_bin_dir + '/libtensorflow_cc.so.{0}.0.1'.format(version)):
            print('copy {0} to {1}'.format(base_bin_dir + '/libtensorflow_cc.so.{0}.1'.format(version), base_install_binary_dir + '/libtensorflow_cc.so.{0}.1'.format(version)))
            # копируем libtensorflow_cc.so.${VERSION}.1
            shutil.copy(base_bin_dir + '/libtensorflow_cc.so.{0}.1'.format(version), base_install_binary_dir + '/libtensorflow_cc.so.{0}.1'.format(version))
        else:
            print('nothing to copy')
            return -1

        if path.exists(base_bin_dir + '/libtensorflow_framework.so') and not path.islink(base_bin_dir + '/libtensorflow_framework.so'):
            print('path {0} exists and is\'nt symbol link'.format(base_bin_dir + '/libtensorflow_framework.so'))
            shutil.copy(base_bin_dir + '/libtensorflow_framework.so',
                        base_install_binary_dir + '/libtensorflow_framework.so.{0}.1'.format(version))
        elif path.exists(base_bin_dir + '/libtensorflow_framework.so.{0}.1'.format(version)):
            shutil.copy(base_bin_dir + '/libtensorflow_framework.so.{0}.1'.format(version),
                        base_install_binary_dir + '/libtensorflow_framework.so.{0}.1'.format(version))
        else:
            return -1

    except PermissionError as e:
        print('{0} - {1}'.format(e.filename, e.strerror))
        return -1

    # создадим копии старых библиотек и удалим их
    if path.exists(base_install_binary_dir + '/libtensorflow_cc.so'):

        shutil.copy(base_install_binary_dir + '/libtensorflow_cc.so',
                    base_install_binary_dir + '/libtensorflow_cc.so.old.1')

        # shutil.move(base_install_binary_dir + '/libtensorflow_cc.so', '/dev/null')
        os.remove(base_install_binary_dir + '/libtensorflow_cc.so')


    if  path.exists(base_install_binary_dir + '/libtensorflow_framework.so'):
        shutil.copy(base_install_binary_dir + '/libtensorflow_framework.so',
                    base_install_binary_dir + '/libtensorflow_framework.so.old.1')

        os.remove(base_install_binary_dir + '/libtensorflow_framework.so')

        # shutil.move(base_install_binary_dir + '/libtensorflow_framework.so', '/dev/null')

    # создадим симводически ссылки
    os.system('ln -s ' + base_install_binary_dir + '/libtensorflow_framework.so.{0}.1'.format(version) + ' ' + base_install_binary_dir + '/libtensorflow_framework.so')
    os.system('ln -s ' + base_install_binary_dir + '/libtensorflow_cc.so.{0}.1'.format(
        version) + ' ' + base_install_binary_dir + '/libtensorflow_cc.so')

    # install source files

    base_install_source_dir = install_prefix + '/include/google/tensorflow'
    if path.exists(base_install_source_dir):
        # надо сохранить старую версию исходников
        try:
            shutil.move(base_install_source_dir, base_install_source_dir + '_old')
        except shutil.Error:
            pass

    # os.mkdir(base_install_source_dir)
    base_source_dir = './' + tf_path

    def has_not(pattern):
        def _ignore(path, names):
            ignored_names = []
            for name in names:
                if not pattern in name and not os.path.isdir(path + '/' + name):
                    ignored_names.append(name)
            return set(ignored_names)

        return _ignore


    def copytree(src, dst, symlinks=False, ignore=None):

        if not path.exists(dst):
            os.makedirs(dst)

        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                copytree(s, d, symlinks=symlinks, ignore=ignore)
            else:
                ignored_names = set()
                if ignore is not None:
                    ignored_names = ignore(src, [item])

                if not item in ignored_names:
                    shutil.copy2(s, d)


    copy_list = [
        (base_source_dir + '/tensorflow', base_install_source_dir + '/tensorflow', has_not('.h')),
        (base_source_dir + '/third_party', base_install_source_dir + '/third_party', None),
        # (base_source_dir + '/bazel-genfiles/tensorflow/core/framework', base_install_source_dir + '/tensorflow/core/framework', has_not('.h')),
        # (base_source_dir + '/bazel-genfiles/tensorflow/core/kernels', base_install_source_dir + '/tensorflow/core/kernels', has_not('.h')),
        # (base_source_dir + '/bazel-genfiles/tensorflow/core/lib/core', base_install_source_dir + '/tensorflow/core/lib/core', has_not('.h')),
        # (base_source_dir + '/bazel-genfiles/tensorflow/core/protobuf', base_install_source_dir + '/tensorflow/core/protobuf', has_not('.h')),
        # (base_source_dir + '/bazel-genfiles/tensorflow/core/util', base_install_source_dir + '/tensorflow/core/util', has_not('.h')),
        # (base_source_dir + '/bazel-genfiles/tensorflow/cc/ops', base_install_source_dir + '/tensorflow/cc/ops', has_not('.h'))
        (base_source_dir + '/bazel-genfiles/tensorflow/core/', base_install_source_dir + '/tensorflow/core/', has_not('.h')),
        (base_source_dir + '/bazel-genfiles/tensorflow/cc/', base_install_source_dir + '/tensorflow/cc/', has_not('.h'))
                 ]

    for src_dst in copy_list:
        try:
            copytree(src_dst[0], src_dst[1], ignore=src_dst[2])
        except FileExistsError:
            print('already exist ' + src_dst[1])
            continue



    # os.chdir(old_dir)


def main():

    # print(os.getenv("PATH"))
    # print(which('bazel'))

    parser = argparse.ArgumentParser(description='tensorflow 1.xx build and install')
    parser.add_argument("-t", default='1.12', help='tensorflow version')
    # parser.add_argument("-i", default='/usr/lib/', help='destination directory')
    parser.add_argument("--install-prefix", default='/usr/local', help='prefix')
    parser.add_argument("--no-install", action='store_true', default=False, help='download and build but no install')
    parser.add_argument("--only-install", action='store_true', default=False)
    parser.add_argument('--no-download', action='store_true', default=False, help='no download if exist')

    parser.add_argument("--python-location", default='/usr/bin/python', help='python interpreter location')
    parser.add_argument("--python-library-location", default='\\n', help='python library path (empty == default)')
    parser.add_argument("--apache-ignite-support", default='n')
    parser.add_argument("--XLA-JIT", default='n')
    parser.add_argument("--opencl-sycl", default='n')
    parser.add_argument("--rocm", default='n')
    parser.add_argument("--CUDA", default='y')
    parser.add_argument("--CUDA-VERSION", default='')
    parser.add_argument("--CUDA-toolkit-location", default='')
    parser.add_argument("--TensorRT-support", default='n')
    parser.add_argument("--download-clang", default='n')
    parser.add_argument("--MPI-support", default='n')
    parser.add_argument("--opt-flag", default='-Wno-sign-compare')
    parser.add_argument("--android-workspace", default='n')
    parser.add_argument("--jemalloc", default='n')
    parser.add_argument("--google-cloud", default='n')
    parser.add_argument("--hadoop-file-system", default='n')
    parser.add_argument("--amazon-aws-platform", default='n')
    parser.add_argument("--apache-kafka", default='n')

    args = parser.parse_args()
    version = args.t
    # destination = args.i
    prefix = args.install_prefix
    no_install = args.no_install
    no_download = args.no_download
    only_install = args.only_install

    python_location = args.python_location
    python_library_location = args.python_library_location
    apache_ignite_support = args.apache_ignite_support
    XLA_JIT = args.XLA_JIT
    opencl_sycl = args.opencl_sycl
    rocm = args.rocm
    CUDA = args.CUDA
    CUDA_VERSION = args.CUDA_VERSION
    CUDA_toolkit_location = args.CUDA_toolkit_location
    TensorRT = args.TensorRT_support
    clang = args.download_clang
    mpi = args.MPI_support
    opt_flag = args.opt_flag
    android_wpc = args.android_workspace
    jemalloc = args.jemalloc
    google_cloud = args.google_cloud
    hadoop_file_system = args.hadoop_file_system
    amazon = args.amazon_aws_platform
    kafka = args.apache_kafka

    min_v = version_to_int(min_tf_version)
    max_v = version_to_int(max_tf_version)

    if min_v < version_to_int(version) > max_v:
        return "Version TF {0} out of range min {1} or max {2} TF version".format(version, min_tf_version,
                                                                                  max_tf_version)

    tf_path = 'tf_' + 'r' + version

    if not only_install:
        git_clone(version, no_download)
        true_tf_version = check_true_tf_version(tf_path)

        # for debug
        # tf_path = 'tf_' + 'r' + version

        bzl_version = check_bazel_version(tf_path, true_tf_version)
        print("---- detected bazel version: {} ----".format(bzl_version[0]))
        bzl_path = get_bazel(bzl_version[0], no_download)
        print(bzl_path)

        tf_configure(tf_path, python_location, python_library_location, apache_ignite_support,
                     XLA_JIT, opencl_sycl, rocm, CUDA, CUDA_VERSION, CUDA_toolkit_location,
                     TensorRT, clang, mpi, opt_flag, android_wpc, jemalloc, google_cloud,
                     hadoop_file_system, amazon, kafka)

        tf_build(tf_path)

        eigen_download_and_build(tf_path, no_download)
        protobuf_download_and_build(tf_path, no_download)



    if not no_install or only_install:
        install_tensorflow(tf_path, true_tf_version, prefix)
        # eigen_install(prefix)
        # protobuf_install()


main()
