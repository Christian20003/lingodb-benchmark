import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/Benchmark')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/Csv')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/Parsing')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/Plot')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/Types')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/Helper')))

from Config import CONFIG
from Point import Point
from Plot import plot_results
from typing import List, Tuple
from Csv import init_csv_file, write_to_csv
from Parse_Args import parse_args
from Parse_Memory import parse_memory_metrics
from Parse_Time import parse_time_metrics
from Parse_Table import parse_table_output
from Execute import time_benchmark, memory_benchmark
from Format import print_warning, print_information, print_success, print_title
from Helper import remove_files, execute_sql, generate_csv, tfloat_switch
from duck_db import duck_db_benchmark
from sklearn.cluster import KMeans
import numpy as np
import random

def main():
    args = parse_args('Kmeans')
    types = CONFIG['types']
    iterations = CONFIG['iterations']
    init_csv_file(['Size', 'correctResult', 'lingoDBResult'])
    # Iterate over all cluser benchmarks
    for key, value in CONFIG.items():
        if 'cluster' not in key:
            continue
        print_title(f'### START BENCHMARKING KMEANS WITH {value["number"]} POINTS ###')
        points = generate_points(value["number"], value["x_upper_bound"], value["y_upper_bound"], value["x_lower_bound"], value["y_lower_bound"])
        cluster = generate_points(value["cluster"], value["x_upper_bound"], value["y_upper_bound"], value["x_lower_bound"], value["y_lower_bound"])
        time, memory = duck_db_benchmark(cluster, points, args['statement'], value['number'])
        # Iterate over all specified types
        for type in types:
            table_names = ['points', 'clusters_0']
            print_information(f'Execute benchmark with type: {type}')
            print_information(f'Create Point-table with {len(points)} entries and Cluster-table with {len(cluster)} entries.')
            if type == 'tfloat':
                dummy_tables = ['pointsdummy', 'clusterdummy']
                create_tables(table_names, type, args)
                create_tables(dummy_tables, 'float', args)
                insert_points(cluster, dummy_tables[1], './cluster.csv', args)
                insert_points(points, dummy_tables[0], './points.csv', args)
                tfloat_switch(table_names[1], dummy_tables[1], args)
                tfloat_switch(table_names[0], dummy_tables[0], args)
            else:
                create_tables(table_names, type, args)
                insert_points(cluster, table_names[1], './cluster.csv', args)
                insert_points(points, table_names[0], './points.csv', args)
            output = time_benchmark(args)
            results = parse_time_metrics(output)
            results['duckdbt'] = time
            results['duckdbm'] = memory
            clusters = parse_table_output(output, 4, 2, 3)
            file = memory_benchmark(args, f'{type}{value["number"]}')
            results = parse_memory_metrics(results, file)
            eval = evaluate_accuray(points, cluster, clusters, iterations, type)
            write_to_csv(results, 'KMeans', type, [value['number'], eval[0], eval[1]])
        print('\n')
    plot_results('Number of points')

def generate_points(number: int, x_upper: int, y_upper: int, x_lower: int, y_lower: int) -> List[Point]:
    '''
    This function generates a specified number of random points.

    :param number: The number of points.
    :param x_upper: The maximum value for x.
    :param y_upper: The maximum value for y.
    :param x_lower: The minimum value for x.
    :param y_lower: The minimum value for y.

    :return: A list of point objects.
    '''

    result = []
    for value in range(number):
        x = "{:.4f}".format(random.uniform(x_lower, x_upper))
        y = "{:.4f}".format(random.uniform(y_lower, y_upper))
        result.append(Point(value, x, y))
    return result

def create_tables(table_names: List[str], type: str, paths: dict) -> None:
    '''
    This function creates tables which can be inserted with values.

    :param table_names: The name of the tables.
    :param type: The current datatype.
    :param paths: A dictionary with paths to all necessary executables and directories.

    :raise RuntimeError: If the tables could not be generated.
    '''
    
    # Remove tables from previous tests
    files = []
    for name in table_names:
        files.append(f'{name}.arrow')
        files.append(f'{name}.arrow.sample')
        files.append(f'{name}.metadata.json')
    remove_files(files, paths['storage'])


    # Define all statements to create tables with the help of LingoDB
    statements = ['SET persist=1;\n']
    for name in table_names:
        statements.append(f'CREATE TABLE {name}(id int, x {type}, y {type});\n')
    execute_sql(statements, paths['exe'], paths['storage'])

def insert_points(points: List[Point], table_name: str, csv_file: str, paths: dict) -> None:
    '''
    This function inserts all given points into a table.

    :param points: A list of points which should be inserted.
    :param table_name: The name of table in which the points should be inserted.
    :param csv_file: The file where the data is stored.
    :param paths: A dictionary with paths to all necessary executables and directories.

    :raise RuntimeError: If the data could not be inserted.
    '''

    print_information(f'Inserting {len(points)} of points (This can take a while)', tabs=1)
    data = [[point.id, point.x, point.y] for point in points]
    generate_csv(csv_file, ['id', 'x', 'y'], data)
    statements = ['SET persist=1;\n']
    copy = f"copy {table_name} from '{csv_file}' delimiter ',' HEADER;\n"
    statements.append(copy)
    execute_sql(statements, paths['exe'], paths['storage'])    

def evaluate_accuray(points: List[Point], cluster: List[Point], result: np.ndarray, iterations: int, type: str) -> Tuple[str, str]:
    '''
    This function evaluates the precision of the database output with the KMeans algorithm of 'Sklearn'.

    :param points: The list of randomly generated points.
    :param cluster: The list of randomly generated cluster centers.
    :param result: A numpy array containing the clusters from the database execution.
    :param iterations: The number of iterations of the KMeans algorithm.
    :param type: The datatype of the current running benchmark.

    :returns: Two strings containing the correct result from numpy and the database result.
    '''

    # Prepare and execute Kmeans from sklearn
    points = Point.points_to_numpy(points)
    cluster = Point.points_to_numpy(cluster)
    kmeans = KMeans(n_clusters=cluster.shape[0], init=cluster, n_init=1, max_iter=iterations)
    kmeans.fit(points)
    centers = kmeans.cluster_centers_
    correct = np.array_str(centers)
    calculation = np.array_str(result)
    # Find the nearest pairs and print the solution of comparison.
    for idx, center in enumerate(centers):
        distance = np.linalg.norm(result - center, axis=1)
        if len(distance) == 0:
            break
        closest_index = np.argmin(distance)
        closest = result[closest_index]

        value = f'{distance[closest_index]:.2f}'
        print_information(f'Cluster {idx + 1}', True, 1)
        print_information(f'Lingo-DB with {type}: {closest}', tabs=2)
        print_information(f'Sklearn with float: {center}', tabs=2)
        if value.startswith('0.00'):
            print_success(f'Distance: {distance[closest_index]:.2f}', tabs=2)
        else:
            print_warning(f'Distance: {distance[closest_index]:.2f}', tabs=2)

        result = np.delete(result, closest_index, axis=0)
    return correct, calculation


if __name__ == "__main__":
    main()
