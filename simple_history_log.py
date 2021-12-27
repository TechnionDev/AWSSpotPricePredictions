import threading
import time

import boto3
import json
import os
import copy
from datetime import datetime
from multiprocessing.pool import ThreadPool
import logging

logging.basicConfig(filename='spot_history_boto3.log',
                    encoding='utf-8', level=logging.INFO,
                    format='%(asctime)s p%(process)s %(filename)s:%(funcName)s:%(lineno)d %(levelname)s> %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

ZONE = 'AvailabilityZone'
ITYPE = 'InstanceType'
OS = 'ProductDescription'
PRICE = 'SpotPrice'
TIMESTAMP = 'Timestamp'
ITEMS = 'SpotPriceHistory'
EXTRACT_KEYS = [PRICE, TIMESTAMP]
FILENAME = 'SpotPriceHistory.json'
PAGE_LIMIT = 50000
measurements = None
threadLock = None
finished = 0


# If running in different threads, the clients must operate over different regions as to block racing


def get_info_using_client(region_name):
    global measurements, finished
    client = boto3.client('ec2', region_name=region_name)
    logging.info(f'Client for region {region_name} initialized')

    # filters = [{'Name': 'instance-type', 'Values': ['g4ad.2xlarge']},
    #            {'Name': 'availability-zone', 'Values': ['us-west-2a']},
    #            {'Name': 'product-description', 'Values': ['Linux/UNIX']}]

    if region_name not in measurements:
        measurements[region_name] = {}
    if 'next_token' in measurements[region_name] and measurements[region_name]['next_token'] is not None:
        h = client.describe_spot_price_history(NextToken=measurements[region_name]['next_token'])
    else:
        h = client.describe_spot_price_history()  # Filters=filters

    for i in range(PAGE_LIMIT):
        if i % 10 == 0:
            logging.info(f'Finished {i} pages from region {region_name}')
        if len(h[ITEMS]) == 0:
            logging.debug(f'No items in page: {i}. Early stopping ;-)')
            break

        for entry in h[ITEMS]:
            if entry[ZONE] not in measurements:
                measurements[entry[ZONE]] = {entry[ITYPE]: {entry[OS]: []}}
            elif entry[ITYPE] not in measurements[entry[ZONE]]:
                measurements[entry[ZONE]][entry[ITYPE]] = {entry[OS]: []}
            elif entry[OS] not in measurements[entry[ZONE]][entry[ITYPE]]:
                measurements[entry[ZONE]][entry[ITYPE]][entry[OS]] = []
            else:
                logging.debug(
                    f'Not the first one: {(entry[ZONE], entry[ITYPE], entry[OS])}')

            extracted = {k: str(entry[k]) for k in EXTRACT_KEYS}

            if len(measurements[entry[ZONE]][entry[ITYPE]][entry[OS]]) == 0 \
                    or measurements[entry[ZONE]][entry[ITYPE]][entry[OS]][-1][PRICE] != extracted[PRICE] \
                    and extracted not in measurements[entry[ZONE]][entry[ITYPE]][entry[OS]]:
                measurements[entry[ZONE]][entry[ITYPE]][entry[OS]] += [extracted]

        measurements[region_name]['next_token'] = h['NextToken']
        h = client.describe_spot_price_history(NextToken=h['NextToken'])
    else:
        logging.warning(
            f'WARNING: Region {region_name} has more than {PAGE_LIMIT} pages')

    logging.info(f'Done fetching for region {region_name}')
    finished += 1


def save_measurements(checkpoint=False):
    global measurements
    threadLock.acquire()
    logging.info(f'Saving measurements. Checkpoint: {checkpoint}')
    measurements['Modified'] = str(datetime.now())

    try:
        with open(FILENAME, mode='w') as fp:
            json.dump(measurements, fp)
    except:
        os.remove(FILENAME)
        threadLock.release()
        raise

    threadLock.release()


def main():
    global measurements, threadLock

    logging.info(f"Execution started")
    threadLock = threading.Lock()

    orig_measurements = None

    if os.path.isfile(FILENAME):
        with open(FILENAME, mode='r') as fp:
            measurements = json.load(fp)
            orig_measurements = copy.deepcopy(measurements)
    else:
        logging.warning(
            f'WARNING: File {FILENAME} does not exist in {os.path.abspath(os.path.curdir)}')
        measurements = {}

    client = boto3.client('ec2', region_name='us-west-2')

    regions = client.describe_regions()['Regions']

    region_names = [x['RegionName'] for x in regions]

    # Run threadpool
    with ThreadPool(processes=30) as pool:
        pool.map_async(get_info_using_client, region_names)
        while finished < len(region_names):
            if orig_measurements == measurements:
                logging.warning(
                    f"WARNING: No new information since {measurements['Modified']}")
            else:
                measurements['Modified'] = str(datetime.now())
                save_measurements(checkpoint=True)
            time.sleep(120)
        # pool.join()

    if orig_measurements == measurements:
        logging.warning(
            f"WARNING: No new information since {measurements['Modified']}")
    else:
        measurements['Modified'] = str(datetime.now())
        save_measurements(checkpoint=False)

    # try:
    #     with open(FILENAME, mode='w') as fp:
    #         json.dump(measurements, fp)
    # except:
    #     os.remove(FILENAME)
    #     raise

    logging.info('DONE')


if __name__ == '__main__':
    main()
