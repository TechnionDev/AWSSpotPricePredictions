import pickle
import json
import _pickle as cPickle
import bz2
import os

def compressed_pickle(title, data):
	with bz2.BZ2File(title + '.json.pbz2', 'w') as f: 
		cPickle.dump(data, f)


filename = input('Enter filename to compress (without .json ext): ')

with open(filename + '.json', 'r') as f:
	data = json.load(f)

compressed_pickle(filename, data)

print(f'Saved to {filename}.json.pbz2')
