"""Run comprehensive GUI workflow validation"""
import sys
sys.path.insert(0, '.')

# Import the test
from tests.test_gui_workflow_composite import test_gui_composite_workflow

if __name__ == "__main__":
    success = test_gui_composite_workflow()
    sys.exit(0 if success else 1)
