# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import duckdb
import pandas as pd

def duck_run_query(db_name
                   ,query
                   ,read_only=True
                   ,attach=[]):
    '''
    wrapper function to run query on DuckDB
    
    param
    -db_name: str Name of the FileDB
    -query: str SQL string
    -folder: str Name of the folder where the FileDB is stored
    -read_only: True or False 
    -attach: list of paths
    
    
    
    '''
    path='{1}.db'.format(db_name)
    
    Dcon = duckdb.connect(path,read_only)          
    #attach databases if specified in the parameters
    if len(attach)>0:        
        for path in attach:
            if '/' in path:
                Dcon.sql(''' ATTACH '{0}' '''.format(path))
            else:
                Dcon.sql(''' ATTACH '/domino/datasets/local/DB/{0}.db' '''.format(path))
                
    try:
        try:
            #print('before running query')
            out=Dcon.sql(query).df()
            #print('after query')
            Dcon.close()            
            return(out)
        except Exception as e:
            Dcon.close()
            if 'NoneType' in str(e):
                None
            else:
                d = {'e': [e],'db':[db_name],'query':[query],'id':[1]}
                df = pd.DataFrame(data=d)
                print(e)
                return(df)
    except Exception as e:
        Dcon.close()
        d = {'e': [e],'db':[db_name],'query':[query],'id':[2]}
        df = pd.DataFrame(data=d)
        print(e)
        return(df)  