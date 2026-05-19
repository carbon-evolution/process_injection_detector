from setuptools import setup, find_packages

setup(
    name="process-injection-detector",
    version="0.1.0",
    description="A Windows-based security tool that monitors and detects process injection techniques",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/process-injection-detector",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "pywin32>=302",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Security",
    ],
    entry_points={
        "console_scripts": [
            "process-injection-detector=process_injection_detector:main",
        ],
    },
) 