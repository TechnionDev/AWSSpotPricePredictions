import json
import pickle

ZONE = 'AvailabilityZone'
ITYPE = 'InstanceType'
OS = 'ProductDescription'
PRICE = 'SpotPrice'
TIMESTAMP = 'Timestamp'
ITEMS = 'SpotPriceHistory'
EXTRACT_KEYS = [PRICE, TIMESTAMP]
FILENAME = 'SpotPriceHistory.json'


def main():
    entries = []
    with open(FILENAME, mode='r') as fp:
        data = json.load(fp)
    


    with open('almost_three_months.csv', mode='w') as outf:
        outf.write(f'Region,instanceType,major,minor,OS,Price,date\n')
        count = 0
        acount = 0
        bcount = 0
        dcount = 0

        # for zone in data:
        #         if zone == 'Modified':
        #             continue

        #         for mtype in data[zone]:
        #             for os_type in data[zone][mtype]:
        #                 data[zone][mtype][os_type].sort(key=lambda x: x[PRICE])

        for zone in data:
            if zone == 'Modified':
                continue

            for mtype in data[zone]:
                for os_type in data[zone][mtype]:
                    parts = mtype.split(".")
                    if len(data[zone][mtype][os_type]) < 50:
                        acount += 1
                        continue

                    count += 1
                    strings = {}
                    for entry in data[zone][mtype][os_type]:
                        bcount += 1
                        s = f'{zone},{mtype},{parts[0]},{parts[1]},{os_type},{entry[PRICE]},{entry[TIMESTAMP][:15]}0:00+00:00\n'
                        if s in strings:
                            dcount += 1
                            print(f"Duplicate: {s}")
                            continue

                        strings[s] = True
                        outf.write(s)
                        # entries.append(f'{zone},{mtype},{parts[0]},{parts[1]},,{os_type},{entry[PRICE]},{entry[TIMESTAMP]}')


    print(f'Machines: {count}. Skipped: {acount}. Entries: {bcount}. Dups: {dcount}')

if __name__ == '__main__':
    main()
