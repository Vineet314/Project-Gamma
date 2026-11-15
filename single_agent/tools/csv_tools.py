from langchain.tools import tool
import pandas as pd
df = pd.read_csv(r'C:\Users\Vineet\Desktop\trial\sales.csv')


@tool
def list_columns() -> list[str]:
    """
    Return the names of all columns in the fraud dataframe.
    """
    return df.columns.tolist()
