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
import streamlit as st
from streamlit.logger import get_logger
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import duckdb
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

con=duckdb.connect('alberogenealogico.db')
data = con.sql('''SELECT * FROM LINKS_TO_REGISTRY''').df()
con.close()


with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

        authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
        )
        authenticator.login()

if st.session_state["authentication_status"]:
        authenticator.logout()
        
        st.write(f'Welcome *{st.session_state["name"]}*')
        st.write("# Le nostre ricerche! ")
        st.markdown(
                    """
        Qui puoi vedere i Cognomi che abbiamo giá cercato. 
        I filtri li trovi sull sinistra        
        """)
        
        Type=sorted(list(data.Tipologia.unique()))
        Year=sorted(list(data.Anno.unique()))
        Commune=sorted(list(data.Comune.unique()))
        with st.sidebar:                
                Tipologia = st.multiselect('Tipologia',Type)
                Anno = st.multiselect('Anno',Year)
                Comune = st.multiselect('Comune',Commune)
        if len(Tipologia)<1:
                Type_filt=Type
        else:
                Type_filt=Tipologia
        if len(Anno)<1:
                Year_filt=Year
        else:
                Year_filt=Anno
        if len(Comune)<1:
                Commune_filt=Commune
        else:
                Commune_filt=Comune

        filtered_df=data[(data['Anno'].isin(Year_filt))&(data['Comune'].isin(Commune_filt))&(data['Tipologia'].isin(Type_filt))]
        st.dataframe(filtered_df,
                     column_config={"Link": st.column_config.LinkColumn("Link al documento")},)

elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
       st.warning('Please enter your username and password')