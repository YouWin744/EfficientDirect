import os
import csv
import networkx as nx

input_dir = "csv_downloads"
output_file = "graph.csv"
data_list = []

def process_matrix(matrix, filename):
    if not matrix:
        return None
    
    num_nodes = len(matrix)
    if num_nodes == 0:
        return None

    try:
        degree = sum(matrix[0])
    except:
        return None

    for row in matrix:
        if len(row) != num_nodes:
            return None
        if sum(row) != degree:
            return None

    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if matrix[i][j] == 1:
                G.add_edge(i, j)

    if nx.is_connected(G):
        diameter = nx.diameter(G)
    else:
        diameter = "Inf"

    clean_name = filename.replace(".am.csv", "")
    return [clean_name, num_nodes, degree, diameter]

if os.path.exists(input_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(input_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()

                blocks = content.strip().split('\n\n')
                sub_index = 0
                
                for block in blocks:
                    block = block.strip()
                    if not block:
                        continue

                    lines = block.split('\n')
                    reader = csv.reader(lines)
                    matrix = []
                    for row in reader:
                        if row:
                            cleaned = [int(x) for x in row if x.strip() != '']
                            if cleaned:
                                matrix.append(cleaned)

                    res = process_matrix(matrix, filename)
                    if res:
                        if len(blocks) > 1:
                            res[0] = f"{res[0]}_{sub_index+1}"
                        data_list.append(res)
                        sub_index += 1
            except:
                pass

data_list.sort(key=lambda x: (x[1], x[0]))

with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['filename', 'nodes', 'degree', 'diameter'])
    writer.writerows(data_list)