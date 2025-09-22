import requests
import pandas as pd
from io import StringIO

def get_csv_from_cloud( url: str ) -> pd.DataFrame:

    # add /download
    url_answers = url + "/download"

    # press "Ergebnisse -> ... -> Tabellendokument neu exportieren"
    response = requests.get( url_answers )

    if response.status_code == 200:
        # Read CSV into pandas DataFrame
        csv_data = StringIO( response.content.decode( 'utf-8' ) )
        df = pd.read_csv( csv_data )
        print( df.head( ) )
    else:
        print( "Failed to download CSV: ", response.status_code )

if __name__ == "__main__":

    # example: download csv from TU Cloud
    # link from "Freigeben -> Link teilen"
    url = "https://cloud.tu-ilmenau.de/s/naKyLMGp5cYfGoN"
    get_csv_from_cloud( url )

