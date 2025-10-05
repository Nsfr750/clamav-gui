from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="clamav-gui",
    version="1.0.0",
    author="Nsfr750",
    author_email="nsfr750@yandex.com",
    description="A PySide6 GUI for ClamAV Antivirus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nsfr750/clamav-gui",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.8',
    install_requires=[
        'PySide6>=6.5.0',
        'python-dotenv>=1.0.0',
        'pywin32>=306; sys_platform == "win32"',
    ],
    entry_points={
        'console_scripts': [
            'clamav-gui=clamav_gui.__main__:main',
        ],
    },
    include_package_data=True,
)
