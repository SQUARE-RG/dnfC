
import packaging.version

#查看支持的所有压缩格式


def get_all_supported_compressors():
    """
    获取所有支持的压缩格式

    Returns:
        所有支持的压缩格式列表
    """

    compressors = []

    for entry_point in packaging.iter_entry_points('packaging.compressors'):
        compressors.append(entry_point.name)

    return compressors

import os
import zipfile
import rarfile
import tarfile
import gzip
import bz2
# import xz
import winrar
#以上代码可以解压缩以下格式的压缩文件:
#
#.zip
#.rar
#.tar
#.gz
#.bz2
#.xz
def remove_file_extension(file_name):
    base = os.path.basename(file_name)
    file_name_without_extension = os.path.splitext(base)[0]
    return file_name_without_extension
def decompress(source_file, target_dir):
    """
    解压缩文件

    Args:
        source_file: 源压缩文件路径
        target_dir: 目标文件夹路径
    """

    # 检查目标文件夹是否存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # 获取源文件名称
    filename = os.path.basename(source_file)

    # 判断压缩格式
    if zipfile.is_zipfile(source_file):
        with zipfile.ZipFile(source_file, "r") as z:
            z.extractall(target_dir)
    elif rarfile.is_rarfile(source_file):
        with rarfile.RarFile(source_file, "r") as r:
            r.extractall(target_dir)
    elif tarfile.is_tarfile(source_file):
        with tarfile.open(source_file, "r") as t:
            t.extractall(target_dir)
    elif filename.endswith('.gz'):
        with gzip.open(source_file, "rb") as g:
            with open(os.path.join(target_dir, filename), "wb") as f:
                f.write(g.read())
    elif source_file.endswith(".bz2"):
        with bz2.BZ2File(source_file, "rb") as b:
            with open(os.path.join(target_dir, filename), "wb") as f:
                f.write(b.read())
    # elif xz.is_xz(source_file):
    #     with xz.open(source_file, "rb") as x:
    #         with open(os.path.join(target_dir, filename), "wb") as f:
    #             f.write(x.read())
    else:
        return "Unsupported archive format"
    # with winrar.RARFile(source_file) as rar:
    #     z.extractall(target_dir)



# 使用示例
# source_file = "/path/to/source.zip"
# target_dir = "/path/to/target"
#
# decompress(source_file, target_dir)

# import os

# import libarchive.read
# import libarchive.extract

# def extract_rpm(rpm_file, extract_dir):
#     # with libarchive.read.file_reader(rpm_file) as  archive:
#     #     for entry in archive:
#     #         target_path = os.path.join(extract_dir, entry.path)
#     #         libarchive.extract.mentions(entry,target_path)
#     #         print(f"Extracting: {target_path}")
#     with libarchive.file_reader(rpm_file) as archive:
#         for entry in archive:
#             # libarchive.extract.extract_entries(entry,extract_dir)

#             extract_path = os.path.join(extract_dir, entry.path)
#             os.makedirs(os.path.dirname(extract_path), exist_ok=True)
#             with libarchive.file_writer(extract_path,'zip') as ext:
#                 for block in entry.get_blocks():
#                     ext.write(block)
#             print(f"Extracting: {extract_path}")


# extract_rpm("/home/jiliqiang/RPM/rpm/kaffeine-2.0.18-10.fc39.x86_64.rpm", "/home/jiliqiang/RPM/rpm/affeine-2.0.18-10.fc39.x86_64")