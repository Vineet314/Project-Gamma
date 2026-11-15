import sys
from io import StringIO
from langchain_core.tools import tool
import pandas as pd
df = pd.read_csv(r'C:\Users\Vineet\Desktop\trial\sales.csv')

@tool
def execute_python_code(code: str) -> str:
    """
    Executes Python code dynamically and returns the standard output (stdout).
    Use this tool to run calculations, manipulate data, or test logic.
    Only use standard print() statements to see the results.
    
    Args:
        code (str): The valid Python code string to execute.
    """

    # Redirect stdout to capture print statements
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output

    try:
        # local namespace
        local_vars = {}
        exec(code, {'df':df}, local_vars)
        return redirected_output.getvalue() or "Code executed successfully with no output."
    
    except Exception as e:
        # Restore stdout and return the error message so the LLM can debug it
        return f"Error during execution: {type(e).__name__}: {e}"

    finally:
        sys.stdout = old_stdout
