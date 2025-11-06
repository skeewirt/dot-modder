import os, shutil

def atomic_replace(src: str, dst: str):
    tmp = dst + ".tmpswap"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)
