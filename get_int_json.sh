set -e

cd ~/pgit/AWSSpotPricePredictions/
curl https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json --output data/spot-advisor-data_$(date +"%Y-%m-%d-%H%M").json
python3 get_int_json.py
echo Ran on $(date +"%Y-%m-%d-%H%M")
