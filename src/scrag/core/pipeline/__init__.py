"""Pipeline stage interface and base implementations."""

from .stages import PipelineStage, StageContext, StageResult

# Import PipelineRunner from the parallel pipeline.py file
import importlib.util
import sys
from pathlib import Path

# Get the pipeline.py file that's a sibling to this package
pipeline_file = Path(__file__).parent / "../pipeline.py"
pipeline_file = pipeline_file.resolve()

spec = importlib.util.spec_from_file_location("pipeline_runner_module", pipeline_file)
pipeline_runner_module = importlib.util.module_from_spec(spec)
sys.modules["pipeline_runner_module"] = pipeline_runner_module
spec.loader.exec_module(pipeline_runner_module)

PipelineRunner = pipeline_runner_module.PipelineRunner

__all__ = [
    "PipelineStage",
    "StageContext", 
    "StageResult",
    "PipelineRunner",
]