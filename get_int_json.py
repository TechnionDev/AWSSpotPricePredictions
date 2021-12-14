import subprocess as sp
import os

def main():
    files = os.listdir('./data')
    files.sort()
    files = [f for f in files if f.startswith('spot-advisor-data_') and f.endswith('.json')]
    print(f'files: {files}')

    if len(files) < 2:
        return

    with open(os.path.join('data', files[-2]), 'r') as f:
        prev_content = f.read()

    with open(os.path.join('data', files[-1]), 'r') as f:
        curr_content = f.read()

    if prev_content == curr_content:
        os.remove(os.path.join('data', files[-1]))


if __name__ == '__main__':
    main()