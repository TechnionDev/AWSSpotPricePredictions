import pickle
import json
import _pickle as cPickle
import bz2

def decompress_pickle(file):
	data = bz2.BZ2File(file, 'rb')
	data = cPickle.load(data)
	return data


filename = input('Enter filename to decompress (without .json.pbz2 ext): ')

data = decompress_pickle(filename+'.json.pbz2')

with open(filename + '.json', 'w') as f:
	json.dump(data, f)

print(f'Saved to {filename}.json')
