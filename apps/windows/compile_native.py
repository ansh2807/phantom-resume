"""Optional native compilation of core logic (hardening, not encryption)."""
from pathlib import Path
import os
from setuptools import setup, Extension
from Cython.Build import cythonize

root = Path(__file__).resolve().parent
destination = Path(os.environ['PHANTOM_NATIVE_BUILD'])
sources = [p for p in (root/'core').rglob('*.py') if p.name != '__init__.py'] + [root/'desktop'/'engine.py']
extensions = [Extension('.'.join(p.relative_to(root).with_suffix('').parts), [str(p)], extra_link_args=['-static-libgcc']) for p in sources]
setup(name='phantomresume-native-core',
      ext_modules=cythonize(extensions, build_dir=str(destination/'generated'), compiler_directives={'language_level':3, 'binding':True, 'embedsignature':False}, annotate=False),
      script_args=['build_ext', '--compiler=mingw32', '--build-lib='+str(destination/'modules'), '--build-temp='+str(destination/'objects')])
