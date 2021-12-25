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
PAGE_LIMIT = 200
measurements = None

# If running in different threads, the clients must operate over different regions as to block racing


def get_info_using_client(region_name):
    global measurements
    client = boto3.client('ec2', region_name=region_name)
    logging.info(f'Client for region {region_name} initialized')

    # filters = [{'Name': 'instance-type', 'Values': ['g4ad.2xlarge']},
    #            {'Name': 'availability-zone', 'Values': ['us-west-2a']},
    #            {'Name': 'product-description', 'Values': ['Linux/UNIX']}]

    h = client.describe_spot_price_history()  # Filters=filters

    for i in range(PAGE_LIMIT):
        if i%10 == 0:
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
                measurements[entry[ZONE]][entry[ITYPE]
                                          ][entry[OS]] += [extracted]

        h = client.describe_spot_price_history(NextToken=h['NextToken'])
    else:
        logging.warning(
            f'WARNING: Region {region_name} has more than {PAGE_LIMIT} pages')

    logging.info(f'Done fetching for region {region_name}')


def main():
    global measurements

    logging.info(f"Execution started")

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
    with ThreadPool(processes=10) as pool:
        pool.map(get_info_using_client, region_names)
        # pool.join()

    if orig_measurements == measurements:
        logging.warning(
            f"WARNING: No new information since {measurements['Modified']}")
    else:
        measurements['Modified'] = str(datetime.now())

    try:
        with open(FILENAME, mode='w') as fp:
            json.dump(measurements, fp)
    except:
        os.remove(FILENAME)
        raise

    logging.info('DONE')


if __name__ == '__main__':
    main()
