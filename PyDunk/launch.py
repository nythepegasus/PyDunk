# configuration and launch file for nuitka compilation

# Make executable standalone
# nuitka-project-if: {OS} in ("Windows", "Linux", "Darwin", "FreeBSD"):
#    nuitka-project: --mode=onefile
#    nuitka-project: --output-dir=build
#    nuitka-project: --onefile-tempdir-spec="{CACHE_DIR}/PyDunk"
# nuitka-project-else:
#    nuitka-project: --output-dir=build
#    nuitka-project: --mode=standalone

# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --output-filename=PyDunk-windows-x86_64.exe
#    nuitka-project: --include-module=jinxed.terminfo.vtwin10
#    nuitka-project: --include-module=jinxed.terminfo.ansicon
#    nuitka-project: --include-module=jinxed.terminfo.xterm
#    nuitka-project: --include-module=jinxed.terminfo.xterm_256color
#    nuitka-project: --user-package-configuration-file=sidejitserver-nuitka-package.config.yml
# nuitka-project-if: {OS} == "Linux":
#    nuitka-project: --output-filename=PyDunk-linux-x86_64.bin
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --output-filename=PyDunk-mac-arm64.bin

# nuitka-project: --report=build/compilation-report.xml

from PyDunk import cli

if __name__ == '__main__':
    cli()
