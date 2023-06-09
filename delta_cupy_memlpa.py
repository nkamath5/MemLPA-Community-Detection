# -*- coding: utf-8 -*-
"""Demo3pm.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1i4O7cQwer4iEYSU0jKuaARDgKlBuOukr
"""
"""Make sure to:
1. Change input file name
2. Update the number of starting lines to ignore
3. Update the subtractor to ensure first node has index 0
4. Update the output csv file number
5. Troubleshooting #1: check matrix size given
"""

import numpy as np

# Importing 
import cupy as cp
from cupyx.scipy.sparse import csr_matrix
from scipy.sparse import lil_matrix
from tqdm import tqdm


def get_adj_matrix(filename, no_of_start_lines_to_ignore=0, subtractor=1):
  file1 = open(filename, 'r')
  row_idx, col_idx = [], []
  data = []
  indptr = [0]
  node = 1
  count = 0
  Lines = file1.readlines()
  print("Reading file for edge data..")
  for idx, line in enumerate(tqdm(Lines)):
    if idx >= no_of_start_lines_to_ignore:
      #print(line)
      u, v = line.split()
      if node != u:
        node = u
        indptr.append(count)
        count = 0
      row_idx.append(int(u)-subtractor)
      col_idx.append(int(v)-subtractor)
      #row_idx.append(int(v)-subtractor)  # for symmetricity of adjacency matrix
      #col_idx.append(int(u)-subtractor)  # for symmetricity of adjacency matrix
      #data.append(1)
      data.append(1) # for symmetricity of adjacency matrix
      count += 1
  data = cp.array(data, dtype=cp.float32)
  col = cp.array(col_idx, dtype=cp.int32)
  indptr = cp.array(indptr, dtype=cp.int32)
  row = cp.array(row_idx, dtype=cp.int32)
  print("Read. Returning..")
  return data, col, row, indptr

def adjust_for_neighborhood_overlap(row, col):
  nf_row, nf_col, nf_data = [],[],[]
  print("Applying adjustment for neighborhood overlaps..")
  for i in tqdm(cp.unique(row)): # size n, so O(n)
      ni = col[row == i]  # neighbors of i
      for j in ni:  # only checks those neighbors of i that are greater than i since, lower labelled neighbors are already covered
          if j > i:  # assumes so self loops, which is fine I guess # uncomment only for undirected
              nj = col[row == j]  # neighbors of j
              #print(ni, i)
              #print(nj, j)
              cardinality_intersection = 0
              if ni.shape[0] > 0 and nj.shape[0] >0:
                inter = cp.intersect1d(ni, nj, assume_unique=True)
                cardinality_intersection = inter.shape[0]
              n_overlap_fraction_ij = (cardinality_intersection+1) / ni.shape[0]  # +1 added to accomodate the case of no neghborhood overlap
              n_overlap_fraction_ji = (cardinality_intersection+1) / nj.shape[0] # uncomment only for undirected
              #print("(i) is", i, n_overlap_fraction_ij, "(j) is", j, n_overlap_fraction_ji)
              nf_row.append(int(i))
              nf_col.append(int(j))
              nf_data.append(n_overlap_fraction_ij)
              nf_row.append(int(j)) # uncomment only for undirected
              nf_col.append(int(i)) # uncomment only for undirected
              nf_data.append(n_overlap_fraction_ji) # uncomment only for undirected

  nf_data = cp.asarray(nf_data)
  nf_row = cp.asarray(nf_row)
  nf_col = cp.asarray(nf_col)
  nf_csr = csr_matrix((nf_data, (nf_row, nf_col)),(n_nodes,n_nodes), dtype = cp.float32)
  return nf_csr.data


data, col, row, _ = get_adj_matrix('com-amazon.ungraph.txt', no_of_start_lines_to_ignore=4, subtractor=1)
print("Returned")
#data, col, row, _ = get_adj_matrix('com-youtube.ungraph.txt', no_of_start_lines_to_ignore=4, subtractor=1)
#data, col, row, _ = get_adj_matrix('email-Eu-core.txt', 0, subtractor=0)
#data = adjust_for_neighborhood_overlap(row, col)

# arr = np.loadtxt("foo.csv", delimiter=",", dtype=np.float32)
# comment above code and add your numpy matrix to 'arr' variable

#size = 925876
size = (max(int(row.max()),int(col.max())) + 1)  # (from com-youtube should be 1157827)
# size = 1005
# add your size here 
print("Stated number of nodes= ", size)
current_labels = cp.arange(start=0, stop=size, dtype=cp.int32)

# Enter your number of edges
number_edges = data.shape[0]

# rows_input_file = cp.ndarray(number_edges, dtype=cp.int32)
# colm_input_file = cp.ndarray(number_edges, dtype=cp.int32)
# data_input_file = cp.ndarray(number_edges, dtype=cp.float32)
rows_input_file = row
colm_input_file = col
data_input_file = data

"""count = 0
for i,x in enumerate(arr):
  for j,z in enumerate(x):
    if z >0 :
      print(z)
      rows_input_file[count] = i
      colm_input_file[count] = j
      data_input_file[count] = z
      count = count + 1"""


def memlpa(current_labels, columns, size, row, data):
  
  flag = 1 # flag variable is used to exit the loop 
  iteration = 0 # iteration is important for history label

  mem_mat = csr_matrix((size, size), dtype=cp.float32) # sparse matrix to define the memory lpa, size is n X n 
  history = cp.random.rand(3,size) # history matrix to find termination cases, size is 3 X n

  history_adder = 0.00001


  while flag:     # we check initially of flag
   
    labels_from_columns = cp.zeros_like(columns) # setting an array to zero to absorb the new label values
    #print("Checker:::::::::::::::::::::::::::::::::::::::::::::")
    #print("Current Labels")
    #print(current_labels)

    #print("Columns")
    #print(columns)

    #print("labels from columns")
    #print(labels_from_columns)

    #print("Checker:::::::::::::::::::::::::::::::::::::::::::::")
    #trial_kernel((1,), (1024,), (current_labels, columns, labels_from_columns, len(row)))  #kernel call to get labels_from_columns     #TODO Change trial kernel for block size and number of threads
    #cp.cuda.Stream.null.synchronize()
    
    """for itr in range(len(columns)):
      labels_from_columns[itr] = current_labels[columns[itr]]"""
    labels_from_columns = cp.take(current_labels, columns)
      
    #cp.cuda.Stream.null.synchronize()
    #print("Labels from Columns")
    #print(labels_from_columns)

    #print("Rows")
    #print(row)
    #print("Rows Length")
    #print(len(row))

    #print("Data")
    #print(data)


    
    
    current_mem_mat = csr_matrix((data, (row, labels_from_columns)), shape=(size, size))  # create a new sparse matrix to store the current memory matrix 
    
    print("Current Value")
    #print(current_mem_mat.toarray())

    mem_mat = mem_mat + current_mem_mat # adding the current memory matrix to the cumaltive mem matrix
    #print(mem_mat.argmax(axis = 1))
    current_labels = mem_mat.argmax(axis = 1).reshape(-1) # extracting the max value of mem_mat to get the update labels
    #print("Immediate current labels")
    #print(current_labels)
    idx = iteration % 3 # 3 here is our chosen parameter
    history[idx] = current_labels # based on iteration number, store the current labels in the history matrix

    """print("Memory Value")
    #print(mem_mat.toarray())
    mem_matrix = mem_mat.toarray()
    #f'{a:.2f}'
    for z in mem_matrix:
      for j in z:
        print(f'{j:.5f}', end=" ")
      print()"""


    hist_data = cp.full((size), history_adder)
    hist_row = cp.arange(start=0, stop = size, dtype=cp.int32)
    hist_labels_column = current_labels
    history_mem_mat = csr_matrix((hist_data, (hist_row, hist_labels_column)), shape=(size, size))
    mem_mat = mem_mat + history_mem_mat
    #history_mem_matrix = history_mem_mat.toarray()

    

    
    

    # below logic checks if past 3 updates are the same, essentially checking for convergence
    if cp.array_equal(history[0], history[1]):
      if cp.array_equal(history[1], history[2]):
        flag = 0    # setting flag to 0 to exit while looping
        pass
    iteration = iteration + 1 # incrementing iteration count
    
    print("The Current Labels are:")
    print(current_labels)
    mapper = {}

    for i in tqdm(range(len(current_labels))):
        if int(current_labels[i]) in mapper:
            mapper[int(current_labels[i])].append(i)
        else:
            mapper[int(current_labels[i])] = [i]
    
    #label_bucket = label_2_list(current_labels)
    
    #print("Label bucket: ", label_bucket)
    
    out_filename = 'memlpa_com_amazon'+str(iteration)+'.csv'
    print("Making output file..:", out_filename)
    import csv
    #data = label_bucket
    
    with open(out_filename, mode='w') as file:
        writer = csv.writer(file)
        for k,v in mapper.items():
            writer.writerow(v)
    print(f"End of iteration {iteration} :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
    #a = input("Hey")
  return current_labels

print(current_labels)

print(data_input_file)

final_labels = memlpa(current_labels, colm_input_file, size, rows_input_file, data_input_file)

def label_2_list(new_labels):
  label = new_labels[0]
  label_bucket = []
  new_label = []
  new_label.append(0)
  visited = []
  for z in tqdm(range(len(new_labels))):
    new_label = []
    for x in (range(0, len(new_labels))):
      # get a label
      if new_labels[x] == z and x not in visited:
        new_label.append(x)
        visited.append(x)
      pass
    if len(new_label) > 0:
      label_bucket.append(new_label)

  return label_bucket

print("Final labels: ", final_labels)

mapper = {}

for i in tqdm(range(len(final_labels))):
    if int(final_labels[i]) in mapper:
        mapper[int(final_labels[i])].append(i)
    else:
        mapper[int(final_labels[i])] = [i]

#label_bucket = label_2_list(final_labels)

#print("Label bucket: ", label_bucket)

out_filename = 'memlpa_com_amazon.csv'
print("Making output file..:", out_filename)
import csv
#data = label_bucket

with open(out_filename, mode='w') as file:
    writer = csv.writer(file)
    for k,v in mapper.items():
        writer.writerow(v)
# Download the csv file generated
