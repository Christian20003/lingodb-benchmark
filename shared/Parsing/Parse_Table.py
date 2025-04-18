import numpy as np
import re

def parse_table_output(output: str, total_columns: int, start: int, stop: int) -> np.ndarray:
    '''
    This function parses the table output of the database into a numpy array. This function
    only works if all columns are numeric values. Each row will be an element in the numpy array.

    :param output: The output string from the database executable.
    :param total_columns: The number of output columns. 
    :param start: The first column which should be extracted (Start with 0).
    :param stop: The last column which should be extracted (Start with 0).

    :return: A numpy array containing all extracted values.
    '''
    
    output = output.decode('utf-8')
    end = output.index('{')
    # Extract all numbers from the output table
    database_result = re.findall(r'-?\d+\.\d+e[+-]?\d+|-?\d+\.\d+|-?\d+', output[:end])
    data = []
    for index in range(0, len(database_result), total_columns):
        if index + stop < len(database_result):
            row = []
            for entry in range(start, stop + 1):
                row.append(float(database_result[index + entry]))
            if len(row) == 1:
                data.append(row[0])
            else:
                data.append(row)
    result = np.array(data, dtype=float)
    return result
