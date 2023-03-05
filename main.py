import pandas as pd
import numpy as np
import argparse


def find_slcsp(zips_file: str, plans_file: str) -> pd.DataFrame:
    """ Calculate the SLCSP of all available zipcodes in rate area

        Args:
            zips_file (str): Filename of the zips.csv (geographical information)
            plans_file (str): Filename of the plams.csv (health plans information)

        Returns:
            DataFrame with zipcode and SLCSP rate columns
    """

    zips_df = pd.read_csv(zips_file)
    plans_df = pd.read_csv(plans_file)

    # Combine rate area as state + rate_area, and drop state column
    zips_df['rate_area'] = zips_df['state'] + ' ' + zips_df['rate_area'].astype(str)
    zips_df.drop('state', axis=1, inplace=True)

    plans_df['rate_area'] = plans_df['state'] + ' ' + plans_df['rate_area'].astype(str)
    plans_df.drop('state', axis=1, inplace=True)

    # Join plans.csv and zips.csv on rate_area
    zip_plans_df = pd.merge(zips_df, plans_df, on='rate_area')

    # Filter metal_level = Silver
    silver_rates_df = zip_plans_df[zip_plans_df['metal_level'] == 'Silver']
    # Drop unnecessary columns to reduce computation
    silver_rates_df = silver_rates_df.drop(['name', 'plan_id', 'metal_level', 'county_code'], axis=1)

    # Check if zipcode has more than one rate area
    # If yes, set rate as blank
    # If no, check if there is more than one unique rate in the zipcode
        # If there is only one, leave blank
        # If no, set second lowest rate
    silver_rates_df.drop_duplicates(subset=['zipcode', 'rate_area', 'rate'], inplace=True)
    silver_rates_df['unique_area_count'] = silver_rates_df.groupby('zipcode')['rate_area'].transform('nunique')
    silver_rates_df['unique_rate_count'] = silver_rates_df.groupby('zipcode')['rate'].transform('nunique')
    # print(silver_rates_df)

    # Where rate = nan
    no_lowest_df = silver_rates_df[(silver_rates_df['unique_area_count'] > 1) | 
                                   (silver_rates_df['unique_rate_count'] == 1)]
    no_lowest_df = no_lowest_df.drop_duplicates(subset=['zipcode']).drop(['rate_area'], axis=1)
    no_lowest_df['rate'] = np.nan

    # Where rate = slcsp
    second_lowest_df = silver_rates_df[(silver_rates_df['unique_area_count'] == 1) & 
                                       (silver_rates_df['unique_rate_count'] > 1)].groupby('zipcode')['rate'].nsmallest(2)
    second_lowest_df = second_lowest_df.reset_index().drop('level_1', 1).drop_duplicates(subset=['zipcode'], keep='last')
    second_lowest_df = pd.concat([second_lowest_df, no_lowest_df])
    second_lowest_df.drop(['unique_area_count', 'unique_rate_count'], axis=1, inplace=True)
    # print(second_lowest_df)

    return second_lowest_df


def output_slcsp(args: dict):
    """ Print the SLCSP for each zipcode

        Args:
            args (dict): Parser dictionary values containing CSV filenames 

    """
    
    second_lowest_data = find_slcsp(args['z'], args['p'])
    slcsp_df = pd.read_csv(args['slcsp_file']).drop('rate', axis=1)

    slcsp = pd.merge(slcsp_df, second_lowest_data, on='zipcode', how='left')
    
    # Output the SLCSP for the required zips
    print(slcsp.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Program to find the second lowest cost silver plan (SLCSP) of given zipcodes.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('slcsp_file', 
                        help='SLCSP CSV filename which contains zip codes which required the SLCSP')
    parser.add_argument('-z', '-zips', 
                        help='CSV filename with geographical information',
                        default='zips.csv')
    parser.add_argument('-p', '-plans', 
                        help='CSV filename with health plans information',
                        default='plans.csv')
    
    args = parser.parse_args()
    config = vars(args)
    # print(config)

    slcsp_filename = config

    # If file found, call output_slcsp
    output_slcsp(slcsp_filename)