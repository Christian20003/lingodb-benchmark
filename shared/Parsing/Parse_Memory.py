def parse_memory_metrics(results: dict, file_name: str) -> dict:
    '''
    This function parses the output of the memory benchmark into the provided results dictionary.
    The output data will be read from a generated file. The resulting dictionary will contain the
    heap, stack and total memory at the time of highest consumption.

    :param results: The dictionary containing all benchmark results.
    :param file_name: The name of the file with the raw data from valgrind.

    :return: The updated dictionary.
    '''

    heap = []
    stack = []
    # Extract all values
    with open(file_name, 'r') as file:
        line = file.readline()
        while line:
            try:
                index = line.find('=')
                if 'mem_heap_B' in line:
                    heap.append(int(line[index + 1:]))
                if 'mem_heap_extra_B' in line:
                    heap[len(heap) - 1] += int(line[index + 1:])
                if 'mem_stacks_B' in line:
                    stack.append(int(line[index + 1:]))
            except ValueError:
                pass
            line = file.readline()
    # Identify max values
    results['memory'] = {}
    results['memory']['heap'] = 0
    results['memory']['stack'] = 0
    results['memory']['total'] = 0
    index = 0
    while index < len(heap):
        if heap[index] + stack[index] > results['memory']['total']:
            results['memory']['heap'] = heap[index]
            results['memory']['stack'] = stack[index]
            results['memory']['total'] = heap[index] + stack[index]
        index += 1
    return results