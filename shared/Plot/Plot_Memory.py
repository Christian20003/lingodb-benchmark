import matplotlib.pyplot as plt

MEMORY_FILE_NAMES = {
    'y_heap': 'Heap.pdf',
    'y_stack': 'Stack.pdf',
    'y_total_memory': 'TotalMemory.pdf'
}

def plot_memory_multiple(data: dict, x_label: str) -> None:
    '''
    This function generates for each result attribute according to memory a single plot stored 
    in a seperate file (One plot for heap, stack and total).

    :param data: The dictionary containing all pre-processed data.
    :param x_label: The label for the x-axis.
    '''
    
    colors = ['r', 'b', 'g', 'c']
    styles = ['-', ':', '--', '-']
    for y_key, file_value in MEMORY_FILE_NAMES.items():
        plt.clf()
        style_index = 0
        for type_key, value in data.items():
            # plot the data
            plt.plot(value['x_values'], value[y_key], linestyle=styles[style_index], color=colors[style_index], marker='o', label=f'Type: {type_key}')
            style_index += 1
        plt.legend(loc='lower left', bbox_to_anchor=(0, 1, 1, 0.2))
        plt.ylim(bottom=0)
        plt.xlabel(x_label)
        if y_key == 'y_stack':
            plt.ylabel('Used memory in KB')
        else:
            plt.ylabel('Used memory in MB')
        plt.xscale('log')
        plt.savefig(file_value)