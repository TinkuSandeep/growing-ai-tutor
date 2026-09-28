[build-system]  
requires = ["setuptools>=69", "wheel"]  
build-backend = "setuptools.build_meta"  
  
[project]  
name = "wellsfargo_1tcoo_batch_transformation"  
version = "1.4.0"  
description = "OCP-ready stored-procedure-driven AutoSys AEWS ingestion, summary refresh and stream refresh"  
requires-python = ">=3.10"  
dependencies = [  
    "python-dotenv>=1.0,<2",  
    "PyYAML>=6.0,<7",  
    "requests>=2.31,<3",  
    "tzdata>=2024.1",  
    "pyodbc>=5.1,<6",  
]  
  
[project.optional-dependencies]  
dev = [  
    "build>=1.2,<2",  
    "pytest>=8,<9",  
    "pytest-cov>=5,<6",  
    "pylint>=3,<4",  
]  
  
[project.scripts]  
autosys-phase1 = "autosys_phase1.source_check:main"  
batch-dashboard-summary = "autosys_phase1.summary_refresh:main"  
batch-dashboard-stream = "autosys_phase1.stream_refresh:main"  
  
[tool.setuptools]  
package-dir = {"" = "src"}  
  
[tool.setuptools.packages.find]  
where = ["src"]  
  
[tool.pytest.ini_options]  
pythonpath = ["src"]  
testpaths = ["tests"]  
addopts = "-q"  
