from langchain.tools import tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq
import os
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from dotenv import load_dotenv


load_dotenv()

# Initialize LLM
llm =ChatGroq(
    api_key=os.getenv("visual_groq"),
    model="moonshotai/kimi-k2-instruct-0905",
    temperature=0.1,
)

# Directory for saving charts
CHARTS_DIR = os.path.join(os.getcwd(), "output", "visualizations")
os.makedirs(CHARTS_DIR, exist_ok=True)

@tool
def execute_visualization(
    code: str,
    chart_title: str
) -> str:
    """Execute Python code to create a visualization using Seaborn.
    
    The code should:
    - Import necessary libraries (seaborn, pandas, matplotlib.pyplot)
    - Create a visualization using Seaborn
    - Save the plot with plt.savefig(filename) using the provided 'filename' variable.
    
    Args:
        code: Complete Python code as a string to execute
        chart_title: Title/name for the chart (used for filename)
    """
    try:
        # Sanitize filename
        safe_title = "".join(c for c in chart_title if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
        filename = os.path.join(CHARTS_DIR, f"{safe_title}_chart.png")
        
        # Create execution namespace with necessary imports and the filename variable
        namespace = {
            'plt': plt,
            'sns': sns,
            'pd': pd,
            'np': np,
            'filename': filename,
        }
        
        # Clean current figure to avoid overlapping plots
        plt.clf()
        
        # Execute the user's code
        exec(code, namespace)
        
        # Robustness Middleware: Check if file was saved. If not, try to save the current figure.
        if not os.path.exists(filename):
            print(f"File not found at {filename}, attempting to save current figure...")
            if plt.get_fignums():
                plt.savefig(filename, dpi=300, bbox_inches='tight')
            else:
                return f"Error: Code executed but no file was saved and no active plot found. Code must generate a plot."
        
        plt.close('all')
        
        return f"Chart created successfully and saved to {filename}"
    
    except Exception as e:
        return f"Error executing visualization code: {str(e)}"


@tool
def generate_visualization_code(
    data_description: str,
    chart_type: str
) -> str:
    """Generate Seaborn code template for a specific chart type.
    
    Args:
        data_description: Description of the data (e.g., "Sales by month")
        chart_type: Type of chart (bar, line, scatter, heatmap, violin, box, pie)
    
    Returns:
        Template code as a string. Note: The code assumes a variable `filename` is available in the environment for saving.
    """
    
    templates = {
        "bar": """import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# Create DataFrame
# REPLACE THIS DATA with user's data
data = pd.DataFrame({
    'Category': ['A', 'B', 'C'],
    'Value': [10, 20, 15]
})

# Create bar plot
plt.figure(figsize=(10, 6))
sns.barplot(data=data, x='Category', y='Value', palette='viridis')
plt.title('{title}')
plt.xlabel('Category')
plt.ylabel('Value')
plt.tight_layout()
# 'filename' variable is provided by the execution environment
plt.savefig(filename, dpi=300, bbox_inches='tight')""",

        "line": """import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# Create DataFrame
data = pd.DataFrame({
    'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
    'Sales': [100, 150, 120, 200]
})

# Create line plot
plt.figure(figsize=(10, 6))
sns.lineplot(data=data, x='Month', y='Sales', marker='o', linewidth=2)
plt.title('{title}')
plt.xlabel('Month')
plt.ylabel('Sales')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(filename, dpi=300, bbox_inches='tight')""",

        "scatter": """import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# Create DataFrame
data = pd.DataFrame({
    'X': [1, 2, 3, 4, 5],
    'Y': [2, 4, 5, 4, 6],
    'Category': ['A', 'A', 'B', 'B', 'C']
})

# Create scatter plot
plt.figure(figsize=(10, 6))
sns.scatterplot(data=data, x='X', y='Y', hue='Category', s=100, palette='Set2')
plt.title('{title}')
plt.xlabel('X Axis')
plt.ylabel('Y Axis')
plt.legend(title='Category')
plt.tight_layout()
plt.savefig(filename, dpi=300, bbox_inches='tight')""",
        
        "pie": """import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# Create DataFrame
data = pd.DataFrame({
    'Category': ['A', 'B', 'C', 'D'],
    'Value': [15, 30, 45, 10]
})

# Seaborn doesn't have a direct pie chart, using matplotlib with seaborn style
plt.figure(figsize=(10, 8))
colors = sns.color_palette('pastel')[0:4]
plt.pie(data['Value'], labels=data['Category'], colors=colors, autopct='%.0f%%')
plt.title('{title}')
plt.tight_layout()
plt.savefig(filename, dpi=300, bbox_inches='tight')"""
    }
    
    template = templates.get(chart_type.lower(), templates["bar"])
    return template.replace('{title}', data_description)

def get_visualization_agent():
    tools = [execute_visualization, generate_visualization_code]
    
    system_prompt = """You are a Data Visualization Expert Agent. 
    When users ask you to create charts:
    1. First use `generate_visualization_code` to get the right template for the chart type.
    2. Adapt the template code to match the user's data exactly. 
       - IMPORTANT: The execution environment provides a `filename` variable. 
       - YOU MUST USE `plt.savefig(filename, dpi=300, bbox_inches='tight')` to save your work.
       - DO NOT use `plt.show()`.
    3. Use `execute_visualization` to run the code creation tool.
    4. Verify the output says "Chart created successfully".
    5. Return the full path of the saved image file provided by the tool output.
    """
    
    return create_agent(llm, tools=tools, system_prompt=system_prompt)
