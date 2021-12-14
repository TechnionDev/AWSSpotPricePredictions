import subprocess as sp
import os

def main():
    files = os.listdir('./data')
    files.sort()
    files = [f for f in files if f.startswith('spot-advisor-data_') and f.endswith('.json')]
    print(f'num of files: {len(files)}')

    if len(files) < 2:
        print(f'Not enough files')
        exit(0)

    with open(os.path.join('data', files[-2]), 'r') as f:
        prev_content = f.read()

    with open(os.path.join('data', files[-1]), 'r') as f:
        curr_content = f.read()

    if prev_content == curr_content:
        print('Last two files are dup. Deleteing last one')
        os.remove(os.path.join('data', files[-1]))
    else:
        exit(0)


if __name__ == '__main__':
    for _ in range(30):
	    main()
